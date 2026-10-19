"""
Membuat laporan HTML (index.html) dari studi kasus simulasi PM2.5 paralel.
Semua gambar disisipkan langsung ke dalam HTML (base64), jadi index.html
bisa dibuka dengan double-click tanpa server.
"""
import base64
import io
import multiprocessing as mp
from datetime import date

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from simulasi_pm25 import (
    buat_skenario, jalankan_serial, jalankan_paralel,
    JUMLAH_SKENARIO, UKURAN_GRID, LANGKAH_WAKTU,
)


def gambar_ke_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=140, bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()


def kategori_risiko(nilai, batas_sedang, batas_tinggi):
    if nilai >= batas_tinggi:
        return "Tinggi"
    if nilai >= batas_sedang:
        return "Sedang"
    return "Rendah"


def main():
    skenario = buat_skenario(JUMLAH_SKENARIO)
    inti = mp.cpu_count()

    # --- Modeling: jalankan simulasi serial lalu paralel ---
    hasil_serial, t_serial = jalankan_serial(skenario)
    daftar_proses = sorted({1, 2, 4, inti})
    waktu = {p: jalankan_paralel(skenario, p)[1] for p in daftar_proses}

    tabel = pd.DataFrame([h for h, _ in hasil_serial])
    batas_sedang = tabel["pm25_maks"].quantile(0.5)
    batas_tinggi = tabel["pm25_maks"].quantile(0.75)
    tabel["risiko"] = tabel["pm25_maks"].apply(
        lambda v: kategori_risiko(v, batas_sedang, batas_tinggi))
    tabel_urut = tabel.sort_values("pm25_maks", ascending=False)

    # --- Grafik: peta skenario terburuk ---
    idx = int(tabel["pm25_maks"].idxmax())
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(hasil_serial[idx][1], cmap="inferno")
    fig.colorbar(im, label="PM2.5 (satuan relatif)")
    ax.set_title(f"Skenario terburuk (ID {idx})")
    img_peta = gambar_ke_base64(fig)

    # --- Grafik: speedup ---
    fig, ax = plt.subplots(figsize=(6, 4))
    p = list(waktu.keys())
    ax.plot(p, [t_serial / waktu[x] for x in p], marker="o", label="Hasil uji")
    ax.plot(p, p, "--", label="Ideal")
    ax.set_xlabel("Jumlah proses")
    ax.set_ylabel("Speedup (x)")
    ax.legend()
    img_speedup = gambar_ke_base64(fig)

    # --- Grafik: distribusi PM2.5 maksimum ---
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(tabel["id"], tabel["pm25_maks"], color="#c2410c")
    ax.axhline(batas_tinggi, color="k", ls="--", lw=1, label="Batas risiko tinggi")
    ax.set_xlabel("ID skenario")
    ax.set_ylabel("PM2.5 maksimum")
    ax.legend()
    img_dist = gambar_ke_base64(fig)

    p_terbaik = max(waktu, key=lambda x: t_serial / waktu[x])
    speedup_terbaik = t_serial / waktu[p_terbaik]

    baris = "\n".join(
        f"<tr><td>{r.id}</td><td>{r.pm25_maks:.1f}</td><td>{r.pm25_rata2:.2f}</td>"
        f"<td>{r.sel_di_atas_ambang}</td>"
        f"<td><span class='badge {r.risiko.lower()}'>{r.risiko}</span></td></tr>"
        for r in tabel_urut.head(10).itertuples())

    jumlah_tinggi = int((tabel["risiko"] == "Tinggi").sum())

    html = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Studi Kasus HPC: Simulasi PM2.5 Paralel</title>
<style>
:root {{ --bg:#faf9f7; --kartu:#fff; --teks:#1f2328; --muted:#6b7280; --garis:#e5e7eb; --aksen:#c2410c; }}
@media (prefers-color-scheme: dark) {{
  :root {{ --bg:#16181b; --kartu:#1f2227; --teks:#e6e6e6; --muted:#9ca3af; --garis:#2f343b; --aksen:#fb923c; }}
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--teks); font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif; line-height:1.6; }}
main {{ max-width:960px; margin:0 auto; padding:32px 20px 64px; }}
h1 {{ font-size:1.9rem; margin:0 0 4px; }}
h2 {{ font-size:1.25rem; margin:40px 0 12px; border-bottom:2px solid var(--aksen); padding-bottom:6px; }}
.sub {{ color:var(--muted); margin:0 0 24px; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:14px; }}
.kpi {{ background:var(--kartu); border:1px solid var(--garis); border-radius:12px; padding:16px; }}
.kpi .nilai {{ font-size:1.7rem; font-weight:700; color:var(--aksen); }}
.kpi .label {{ color:var(--muted); font-size:.85rem; }}
.kartu {{ background:var(--kartu); border:1px solid var(--garis); border-radius:12px; padding:18px; }}
.dua {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:14px; }}
img {{ max-width:100%; height:auto; border-radius:8px; }}
.tabel {{ overflow-x:auto; }}
table {{ width:100%; border-collapse:collapse; font-size:.92rem; }}
th,td {{ padding:8px 10px; border-bottom:1px solid var(--garis); text-align:left; }}
th {{ color:var(--muted); font-weight:600; }}
.badge {{ padding:2px 10px; border-radius:999px; font-size:.8rem; font-weight:600; }}
.badge.tinggi {{ background:#fee2e2; color:#991b1b; }}
.badge.sedang {{ background:#fef3c7; color:#92400e; }}
.badge.rendah {{ background:#dcfce7; color:#166534; }}
ul {{ padding-left:20px; }}
footer {{ margin-top:48px; color:var(--muted); font-size:.85rem; }}
</style>
</head>
<body>
<main>
<h1>Simulasi Sebaran PM2.5 dengan Komputasi Paralel</h1>
<p class="sub">Studi kasus CRISP-DM berdasarkan kuliah tamu <em>Global Infrastructure to Address Local Challenge with HPC</em> &middot; dibuat {date.today().strftime('%d-%m-%Y')}</p>

<div class="grid">
  <div class="kpi"><div class="nilai">{JUMLAH_SKENARIO}</div><div class="label">Skenario disimulasikan</div></div>
  <div class="kpi"><div class="nilai">{t_serial:.1f} dtk</div><div class="label">Waktu serial</div></div>
  <div class="kpi"><div class="nilai">{speedup_terbaik:.2f}x</div><div class="label"><em>Speedup</em> terbaik ({p_terbaik} proses)</div></div>
  <div class="kpi"><div class="nilai">{jumlah_tinggi}</div><div class="label">Skenario risiko tinggi</div></div>
</div>

<h2>1. <em>Business Understanding</em></h2>
<div class="kartu">
<p>Kabut asap akibat kebakaran hutan dan lahan adalah masalah lokal di Sumatra. Materi kuliah tamu menunjukkan bahwa <em>High Performance Computing</em> (HPC) dipakai untuk prakiraan kualitas udara PM2.5 pada superkomputer LANTA di Thailand. Prakiraan yang baik membutuhkan banyak skenario simulasi (posisi sumber asap, arah angin, laju difusi), sehingga waktu komputasi menjadi kendala.</p>
<p><strong>Tujuan:</strong> menunjukkan bahwa menjalankan skenario secara paralel mempercepat simulasi, lalu mengidentifikasi skenario dengan risiko PM2.5 tertinggi.</p>
</div>

<h2>2. <em>Data Understanding &amp; Preparation</em></h2>
<div class="kartu">
<p>Data berupa simulasi: <em>grid</em> {UKURAN_GRID}&times;{UKURAN_GRID} sel dengan {LANGKAH_WAKTU} langkah waktu per skenario. Setiap skenario memiliki satu sumber emisi tetap, kecepatan angin pada sumbu x dan y, serta koefisien difusi yang dibangkitkan acak dengan <code>seed</code> tetap agar hasilnya dapat direproduksi.</p>
</div>

<h2>3. <em>Modeling</em></h2>
<div class="kartu">
<p>Model sederhana menggabungkan tiga proses pada tiap langkah waktu: <em>difusi</em> (penyebaran ke sel tetangga), <em>adveksi</em> (terbawa angin), dan peluruhan alami. Karena tiap skenario independen, pekerjaan dibagi ke beberapa inti CPU memakai <code>multiprocessing.Pool</code>.</p>
</div>

<h2>4. <em>Evaluation</em></h2>
<div class="dua">
  <div class="kartu"><h3>Perbandingan waktu</h3><img src="data:image/png;base64,{img_speedup}" alt="Grafik speedup"></div>
  <div class="kartu"><h3>PM2.5 maksimum per skenario</h3><img src="data:image/png;base64,{img_dist}" alt="Distribusi PM2.5 maksimum"></div>
</div>
<div class="kartu" style="margin-top:14px">
<h3>Peta sebaran skenario terburuk</h3>
<img src="data:image/png;base64,{img_peta}" alt="Peta sebaran PM2.5" style="max-width:480px">
</div>
<div class="kartu tabel" style="margin-top:14px">
<h3>10 skenario dengan PM2.5 tertinggi</h3>
<table>
<tr><th>ID</th><th>PM2.5 maks</th><th>Rata-rata</th><th>Sel di atas ambang</th><th>Risiko</th></tr>
{baris}
</table>
</div>
<p class="sub" style="margin-top:12px">Komputer pengujian: {inti} inti CPU. Nilai <em>speedup</em> bergantung pada jumlah inti; pada 1 inti hasilnya mendekati 1x.</p>

<h2>5. <em>Deployment</em> / Rekomendasi</h2>
<div class="kartu">
<ul>
  <li>Pada sistem prakiraan nyata, jalankan ratusan skenario secara paralel agar hasil tersedia sebelum keputusan harus diambil.</li>
  <li>Prioritaskan pemantauan dan tindakan pencegahan pada area dengan kategori risiko <strong>Tinggi</strong>.</li>
  <li>Skalakan ke <em>cluster</em> atau superkomputer ketika jumlah skenario dan resolusi <em>grid</em> bertambah.</li>
  <li>Ganti model sederhana ini dengan data meteorologi dan model kualitas udara operasional.</li>
</ul>
</div>

<footer>Kuliah tamu: Worawan Diaz Carballo, Thammasat University. Data simulasi untuk keperluan pembelajaran, bukan prakiraan operasional.</footer>
</main>
</body>
</html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    tabel.drop(columns=["risiko"]).to_csv("hasil_simulasi.csv", index=False)
    print("index.html berhasil dibuat.")


if __name__ == "__main__":
    main()
