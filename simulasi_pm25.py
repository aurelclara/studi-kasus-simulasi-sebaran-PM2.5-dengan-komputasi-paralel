"""
Studi Kasus: Simulasi Sebaran PM2.5 dengan Komputasi Paralel
Terinspirasi materi "Global Infrastructure to Address Local Challenge with HPC"
(prakiraan kualitas udara PM2.5 pada superkomputer).

Ide HPC yang didemonstrasikan: banyak skenario simulasi yang independen
dapat dijalankan bersamaan di beberapa inti CPU (parallel), sehingga
waktu total lebih singkat dibanding dijalankan satu per satu (serial).
"""
import time
import multiprocessing as mp

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # supaya bisa menyimpan gambar tanpa jendela
import matplotlib.pyplot as plt

UKURAN_GRID = 150      # grid 150 x 150 sel (representasi peta wilayah)
LANGKAH_WAKTU = 400    # jumlah langkah simulasi
JUMLAH_SKENARIO = 24   # banyaknya skenario yang disimulasikan


def buat_skenario(jumlah, seed=42):
    """Membuat skenario acak: posisi sumber asap, arah/kecepatan angin, difusi."""
    acak = np.random.default_rng(seed)
    skenario = []
    for i in range(jumlah):
        skenario.append({
            "id": i,
            "sumber_x": int(acak.integers(30, UKURAN_GRID - 30)),
            "sumber_y": int(acak.integers(30, UKURAN_GRID - 30)),
            "angin_x": float(acak.uniform(-0.2, 0.2)),
            "angin_y": float(acak.uniform(-0.2, 0.2)),
            "difusi": float(acak.uniform(0.05, 0.2)),
        })
    return skenario


def simulasi_satu_skenario(s):
    """Simulasi penyebaran PM2.5 (difusi + adveksi angin + peluruhan)."""
    g = np.zeros((UKURAN_GRID, UKURAN_GRID))
    for _ in range(LANGKAH_WAKTU):
        g[s["sumber_y"], s["sumber_x"]] += 100.0  # emisi tetap dari sumber
        difusi = (np.roll(g, 1, 0) + np.roll(g, -1, 0)
                  + np.roll(g, 1, 1) + np.roll(g, -1, 1) - 4 * g)
        adveksi = (s["angin_x"] * (g - np.roll(g, np.sign(s["angin_x"]).astype(int), 1))
                   + s["angin_y"] * (g - np.roll(g, np.sign(s["angin_y"]).astype(int), 0)))
        g = g + s["difusi"] * difusi - adveksi
        g *= 0.999  # peluruhan alami
    hasil = {
        "id": s["id"],
        "pm25_maks": float(g.max()),
        "pm25_rata2": float(g.mean()),
        "sel_di_atas_ambang": int((g > 5.0).sum()),
    }
    return hasil, g


def jalankan_serial(skenario):
    mulai = time.perf_counter()
    hasil = [simulasi_satu_skenario(s) for s in skenario]
    return hasil, time.perf_counter() - mulai


def jalankan_paralel(skenario, jumlah_proses):
    mulai = time.perf_counter()
    with mp.Pool(processes=jumlah_proses) as kolam:
        hasil = kolam.map(simulasi_satu_skenario, skenario)
    return hasil, time.perf_counter() - mulai


def main():
    skenario = buat_skenario(JUMLAH_SKENARIO)
    inti = mp.cpu_count()
    print(f"Jumlah inti CPU terdeteksi: {inti}")

    hasil_serial, t_serial = jalankan_serial(skenario)
    print(f"Serial   : {t_serial:.2f} detik")

    daftar_proses = sorted({1, 2, 4, inti})
    waktu = {}
    for p in daftar_proses:
        _, t = jalankan_paralel(skenario, p)
        waktu[p] = t
        print(f"Paralel ({p} proses): {t:.2f} detik | speedup {t_serial / t:.2f}x")

    # Simpan tabel hasil
    tabel = pd.DataFrame([h for h, _ in hasil_serial])
    tabel.to_csv("hasil_simulasi.csv", index=False)

    # Grafik 1: peta sebaran skenario terburuk
    idx = int(tabel["pm25_maks"].idxmax())
    plt.figure(figsize=(6, 5))
    plt.imshow(hasil_serial[idx][1], cmap="inferno")
    plt.colorbar(label="Konsentrasi PM2.5 (satuan relatif)")
    plt.title(f"Sebaran PM2.5 skenario terburuk (ID {idx})")
    plt.tight_layout()
    plt.savefig("peta_sebaran.png", dpi=150)
    plt.close()

    # Grafik 2: speedup
    plt.figure(figsize=(6, 4))
    plt.plot(list(waktu.keys()), [t_serial / t for t in waktu.values()], marker="o", label="Hasil uji")
    plt.plot(list(waktu.keys()), list(waktu.keys()), "--", label="Ideal")
    plt.xlabel("Jumlah proses")
    plt.ylabel("Speedup (x)")
    plt.title("Speedup komputasi paralel")
    plt.legend()
    plt.tight_layout()
    plt.savefig("grafik_speedup.png", dpi=150)
    plt.close()
    print("Selesai. File hasil_simulasi.csv, peta_sebaran.png, grafik_speedup.png dibuat.")


if __name__ == "__main__":
    main()
