# Simulasi Sebaran PM2.5 dengan Komputasi Paralel

Studi kasus **CRISP-DM** berdasarkan kuliah tamu *Global Infrastructure to Address Local Challenge with HPC* (Worawan Diaz Carballo, Thammasat University). Proyek ini menunjukkan bagaimana komputasi paralel mempercepat simulasi banyak skenario sebaran PM2.5, seperti contoh prakiraan kualitas udara pada superkomputer LANTA di Thailand.

🔗 **[Lihat laporan HTML (live)]([https://USERNAME.github.io/studi-kasus-hpc-pm25/](https://aurelclara.github.io/studi-kasus-simulasi-sebaran-PM2.5-dengan-komputasi-paralel/)**

## Kerangka CRISP-DM

| Tahap | Penjelasan |
| --- | --- |
| **Business Understanding** | Kabut asap adalah masalah lokal di Sumatra. Prakiraan membutuhkan banyak skenario simulasi sehingga waktu komputasi menjadi kendala. |
| **Data Understanding & Preparation** | Data simulasi: *grid* 150x150, 400 langkah waktu, 24 skenario acak (posisi sumber, angin, difusi) dengan `seed` tetap. |
| **Modeling** | Model difusi + adveksi + peluruhan pada *grid* 2D, dijalankan serial dan paralel (`multiprocessing.Pool`). |
| **Evaluation** | Membandingkan waktu serial vs paralel (*speedup*) dan mengelompokkan skenario berdasarkan risiko PM2.5. |
| **Deployment** | Laporan HTML berisi KPI, grafik, tabel, dan rekomendasi. |

## Struktur Proyek

```
studi-kasus-hpc-pm25/
├── simulasi_pm25.py      # Simulasi + perbandingan serial vs paralel (hasil di terminal)
├── generate_report.py    # Pembuat laporan HTML
├── index.html            # Laporan visual (buka di browser)
├── requirements.txt      # Dependensi
├── .gitignore
└── README.md
```

## Cara Menjalankan

```bash
git clone https://github.com/USERNAME/studi-kasus-hpc-pm25.git
cd studi-kasus-hpc-pm25

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python simulasi_pm25.py          # simulasi di terminal + gambar PNG
python generate_report.py        # membuat ulang index.html
```

## Laporan HTML

- **Membuka lokal:** double-click `index.html` (semua gambar sudah tertanam, tidak perlu server).
- **Lewat link:** aktifkan GitHub Pages di **Settings → Pages**, pilih branch `main` dan folder `/ (root)`.

## Catatan

Data adalah **simulasi** untuk pembelajaran, bukan prakiraan operasional. Nilai *speedup* bergantung pada jumlah inti CPU komputer yang dipakai.

## Lisensi
Kuliah tamu Informatics Practitioner Lecture Series 2026, Worawan Diaz Carballo, Thammasat University.

Proyek ini dibuat untuk keperluan pembelajaran.
