# Parallel File Analyzer: Hybrid Computing for Real-World Data Processing

> **Ujian Tengah Semester (UTS) — Ganjil 2026/2027**  
> **Mata Kuliah:** Komputasi Paralel dan Terdistribusi (3 SKS)  
> **Dosen Pengampu:** Ir. Randi Rizal, Ph.D.  
> **Program Studi:** Informatika, Fakultas Teknik, Universitas Siliwangi  
> **Mahasiswa:** Muhammad Fariez Riziq Ilham (NPM: **247006111146**)  
> **Slogan:** *“Think Parallel. Work Distributed. Create Hybrid Innovation”.*

---

## 1. Deskripsi Proyek

Proyek ini merupakan implementasi sistem komputasi paralel hibrida (*hybrid computing*) untuk menganalisis korpus teks berskala besar dari Project Gutenberg secara efisien. Sistem menggabungkan dua paradigma paralelisme:
1. **Task / Thread Parallelism (`concurrent.futures.ThreadPoolExecutor`)**: Menangani pekerjaan *I/O-bound*, yaitu membaca berkas teks dari media penyimpanan dan membersihkan header/footer Gutenberg tanpa terhalang *Global Interpreter Lock* (GIL) Python.
2. **Process Pool (`concurrent.futures.ProcessPoolExecutor`)**: Menangani komputasi berat *CPU-bound*, yaitu tokenisasi regex kata, kalimat, simbol, penghitungan vokal, angka, dan agregasi frekuensi kata (*word frequency counter*) pada proses-proses independen yang berjalan di atas core fisik prosesor.

---

## 2. Parameter Mahasiswa (NIM: 247006111146)

Berdasarkan rumus penentuan parameter pada naskah soal UTS:
- **Seed Acak Global**: `random.seed(247006111146)`
- **Jumlah Thread ($T$)**:
  $$\text{Dua digit terakhir NIM mod } 4 + 2 = (46 \bmod 4) + 2 = 2 + 2 = \mathbf{4\text{ Thread}}$$
- **Jumlah Proses ($P$)**:
  $$\text{Dua digit tengah NIM mod } 3 + 2 = (61 \bmod 3) + 2 = 1 + 2 = \mathbf{3\text{ Proses}}$$
- **Jumlah Data File ($N$)**:
  $$\text{Tiga digit terakhir NIM} \times 10 = 146 \times 10 = \mathbf{1.460\text{ File Teks}}$$

Seluruh konstanta ini dideklarasikan terpusat di `config.py`.

---

## 3. Struktur Direktori

```text
file_analyzer/
├── config.py                 # Konfigurasi parameter NIM terpusat dan path direktori
├── download_data.py          # Skrip pengunduh dataset buku teks Project Gutenberg
├── analyzer.py               # Modul inti komputasi Serial dan Hybrid
├── benchmark.py              # Runner benchmark 10 konfigurasi x 3 repetisi
├── make_charts.py            # Generator 5 grafik PNG resolusi tinggi (300 DPI)
├── serve.py                  # Server web lokal visualisasi dashboard (port 8000)
├── manifest.csv              # Daftar urutan 1.460 file Gutenberg deterministik
├── pg_catalog.csv            # Salinan katalog buku teks Project Gutenberg
├── data_wc_real/             # Folder dataset 1.460 berkas teks Project Gutenberg
├── results/
│   ├── results.csv           # Tabel ringkasan 10 konfigurasi pengujian
│   ├── results.json          # Data mentah lengkap, spesifikasi mesin, dan korpus
│   ├── baselines.json        # Cache baseline serial (500, 1000, 1460 file)
│   └── charts/               # Grafik hasil matplotlib (300 DPI)
│       ├── chart_1_time_vs_threads.png
│       ├── chart_2_time_vs_processes.png
│       ├── chart_3_speedup_vs_configs.png
│       ├── chart_4_efficiency_vs_configs.png
│       └── chart_5_phase_breakdown_stacked.png
└── dashboard/                # Antarmuka web visualisasi Chart.js (offline)
    ├── index.html            # Markup dashboard responsif
    ├── style.css             # Desain antarmuka (Dark / Light mode)
    ├── app.js                # Logika interaktif dan rendering Chart.js
    └── chart.min.js          # Library Chart.js v4.5.1 lokal (tanpa CDN)
```

---

## 4. Prasyarat & Instalasi

Proyek ini hanya menggunakan pustaka standar Python 3 ditambah `psutil` dan `matplotlib`.
Pastikan dependensi berikut terpasang di lingkungan Python Windows Anda:

```bash
pip install matplotlib psutil
```

---

## 5. Urutan Menjalankan Program

Jalankan perintah berikut secara berurutan di terminal:

### Langkah 1: Persiapan Dataset (Sudah Terunduh Lengkap)
Dataset sebanyak 1.460 buku teks telah tersedia di folder `data_wc_real/` dengan indeks pada `manifest.csv`. Jika ingin memeriksa integritas atau mengunduh ulang di lingkungan baru:
```bash
python download_data.py
```

### Langkah 2: Eksekusi File Analyzer (Modul Inti)
Menjalankan program analyzer utama dengan konfigurasi default NIM (4 Thread, 3 Proses, 1.460 File):
```bash
python analyzer.py
```
Opsi argumen CLI yang tersedia:
```bash
python analyzer.py --threads 4 --procs 3 --data 1460 --mode hybrid
python analyzer.py --mode serial --data 1460
python analyzer.py --data 500 --validate
```

### Langkah 3: Menjalankan Benchmark 10 Konfigurasi
Menjalankan 10 konfigurasi pengujian (masing-masing 3 kali pengulangan cold & warm) dan mencatat spesifikasi perangkat keras ke `results/results.json` serta `results/results.csv`:
```bash
python benchmark.py
```
*Catatan: Skrip mendukung resumability. Jika terhenti, eksekusi akan melanjutkan konfigurasi yang belum selesai tanpa mengulang dari awal. Gunakan `--force` untuk mengulang seluruh benchmark.*

### Langkah 4: Membuat Grafik Laporan (Matplotlib 300 DPI)
Menghasilkan 5 grafik PNG berkualitas cetak di direktori `results/charts/`:
```bash
python make_charts.py
```

### Langkah 5: Menjalankan Dashboard Visualisasi Web
Menjalankan web server lokal untuk melihat dashboard interaktif berbasis Chart.js:
```bash
python serve.py --port 8000
```
Buka browser pada alamat: **`http://localhost:8000`**

---

## 6. Definisi Metrik

1. **Speedup ($S$)**:
   $$S = \frac{T_{\text{serial}}}{T_{\text{hybrid}}}$$
   Mengukur seberapa kali lebih cepat eksekusi hybrid dibandingkan baseline serial murni pada ukuran dataset file yang sama persis.

2. **Efisiensi Komputasi ($E$)**:
   $$E = \frac{S}{P} \times 100\%$$
   Mengukur persentase utilisasi relatif core prosesor ($P$ = jumlah proses worker) dalam melakukan komputasi paralel.

3. **Throughput ($TP$)**:
   $$TP = \frac{\text{Jumlah File}}{T_{\text{total}}} \quad (\text{file/detik})$$
   Mengukur laju pemrosesan dokumen teks per satuan waktu.

---

## 7. Asumsi & Keputusan Desain

1. **Pemisahan Tegas Tahap I/O dan CPU**:
   - `ThreadPoolExecutor` menangani pembacaan file dan pembersihan Gutenberg. Threading sangat efektif untuk operasi I/O disk karena GIL dilepas selama transfer byte dari filesystem ke buffer memori.
   - `ProcessPoolExecutor` menangani kalkulasi analitik teks (regex tokenisasi, frekuensi kata, ekstraksi numerik) untuk memotong batas GIL dengan mendistribusikan beban ke proses independen pada core CPU terpisah.
2. **Penerapan Batching Adaptif pada IPC (Inter-Process Communication)**:
   - Objek yang dikirim ke worker ProcessPool adalah batch teks bersih (`List[Tuple[str, str, int]]`), bukan path file. Hal ini menjamin tidak ada operasi I/O berulang pada worker CPU.
   - Mengelompokkan file menjadi batch (15-25 file per task) mereduksi *overhead* pickling/unpickling objek Python lewat socket/pipe IPC. Mengirim 1.460 file satu per satu terbukti menimbulkan overhead komunikasi yang signifikan.
3. **Kompatibilitas Windows Multiprocessing**:
   - Sistem operasi Windows menggunakan metode `spawn` (bukan `fork`). Oleh karena itu, seluruh fungsi worker ditempatkan pada tingkat modul (*top-level*) dan seluruh skrip dibungkus dalam blok proteksi `if __name__ == "__main__":`.
4. **Alasan Tidak Digunakannya MPI**:
   - Berdasarkan petunjuk soal, MPI bersifat opsional dan ditujukan untuk arsitektur kluster multi-node terdistribusi. Eksperimen ini difokuskan secara optimal pada arsitektur hybrid Thread + Process Pool pada lingkungan single-node workstation (AMD Ryzen 5 5600H, 6 physical cores).
