# Parallel File Analyzer: Hybrid Computing for Real-World Data Processing

> **Ujian Tengah Semester (UTS) — Ganjil 2026/2027**  
> **Mata Kuliah:** Komputasi Paralel dan Terdistribusi (3 SKS)  
> **Dosen Pengampu:** Ir. Randi Rizal, Ph.D.  
> **Program Studi:** Informatika, Fakultas Teknik, Universitas Siliwangi  
> **Mahasiswa:** Muhammad Fariez Riziq Ilham (NIM: **247006111146**)  
> **Slogan Proyek:** *“Think Parallel. Work Distributed. Create Hybrid Innovation”.*

---

## 1. Deskripsi Proyek

Proyek ini merupakan implementasi sistem komputasi paralel hibrida (*hybrid computing*) untuk menganalisis korpus teks berskala besar dari Project Gutenberg secara efisien. Sistem memadukan dua paradigma paralelisme:
1. **Task / Thread Parallelism (`concurrent.futures.ThreadPoolExecutor`)**: Menangani pekerjaan *I/O-bound*, yaitu membaca berkas teks dari media penyimpanan dan membersihkan header/footer lisensi Gutenberg tanpa terhalang *Global Interpreter Lock* (GIL) Python.
2. **Process Pool (`concurrent.futures.ProcessPoolExecutor`)**: Menangani komputasi berat *CPU-bound*, yaitu tokenisasi regex kata, kalimat, simbol, penghitungan vokal, angka, dan agregasi frekuensi kata (*word frequency counter*) pada proses-proses independen yang berjalan di atas core fisik prosesor terpisah.

---

## 2. Parameter Berdasarkan NIM (NIM: 247006111146)

Berdasarkan rumus penentuan parameter pada naskah soal UTS:
- **Seed Acak Global**: `random.seed(247006111146)`
- **Jumlah Thread ($T$)**:
  $$\text{Dua digit terakhir NIM mod } 4 + 2 = (46 \bmod 4) + 2 = 2 + 2 = \mathbf{4\text{ Thread}}$$
- **Jumlah Proses ($P$)**:
  $$\text{Dua digit tengah NIM mod } 3 + 2 = (61 \bmod 3) + 2 = 1 + 2 = \mathbf{3\text{ Proses}}$$
- **Jumlah Data File ($N$)**:
  $$\text{Tiga digit terakhir NIM} \times 10 = 146 \times 10 = \mathbf{1.460\text{ File Teks}}$$

Seluruh konstanta ini dideklarasikan terpusat di `config.py` agar tidak ada angka ajaib (*magic numbers*) yang tersebar.

---

## 3. Struktur Repositori

```text
file_analyzer/
├── .gitignore                # Aturan pengecualian cache, dataset besar, dan draft
├── README.md                 # Dokumentasi komprehensif proyek
├── config.py                 # Parameter terpusat (NAMA, NIM, SEED, THREADS, PROCESSES, DATA_COUNT, PATH)
├── analyzer.py               # Modul inti komputasi Serial dan Hybrid + validasi integritas
├── benchmark.py              # Runner benchmark 10 konfigurasi x 3 repetisi + warm-up & drift check
├── make_charts.py            # Generator 5 grafik analisis beresolusi tinggi (300 DPI)
├── render_diagram.py         # Skrip perender diagram arsitektur sistem (matplotlib)
├── serve.py                  # Server web HTTP lokal untuk visualisasi dashboard (port 8000)
├── manifest.csv              # Indeks urutan 1.460 file Gutenberg deterministik (seed NIM)
├── pg_catalog.csv            # Salinan katalog buku teks Project Gutenberg
├── arsitektur_hybrid.png     # Gambar diagram arsitektur sistem (300 DPI)
├── arsitektur_hybrid.svg     # Berkas grafik vektor diagram arsitektur
├── data_wc_real/             # Direktori dataset 1.460 berkas teks Project Gutenberg (~538 MB)
├── results/
│   ├── results.csv           # Tabel ringkasan 10 konfigurasi pengujian
│   ├── results.json          # Data mentah lengkap, spesifikasi mesin, baselines, korpus, dan validation
│   └── charts/               # Berkas grafik analisis kinerja (300 DPI)
│       ├── chart_1_time_vs_threads.png
│       ├── chart_2_time_vs_processes.png
│       ├── chart_3_speedup_vs_configs.png
│       ├── chart_4_efficiency_vs_configs.png
│       └── chart_5_phase_breakdown_stacked.png
├── dashboard/                # Antarmuka web visualisasi mandiri (offline)
│   ├── index.html            # Markup antarmuka bertema profiler teknis ilmiah
│   ├── style.css             # Desain antarmuka (Dark & Light mode, high-contrast)
│   ├── app.js                # Logika interaktif Chart.js, sortir tabel, dan ekspor CSV client-side
│   └── chart.min.js          # Pustaka Chart.js v4.5.1 lokal (tanpa CDN eksternal)
└── docs/
    └── misc/                 # Berkas arsip draft laporan internal dan log sesi
```

---

## 4. Prasyarat & Instalasi

Proyek ini hanya menggunakan pustaka standar Python 3 ditambah `psutil` dan `matplotlib`.
Pastikan dependensi berikut terpasang di lingkungan Python Anda:

```bash
pip install matplotlib psutil python-docx
```

---

## 5. Urutan Menjalankan Program

Jalankan perintah berikut secara berurutan di terminal (PowerShell, Command Prompt, atau terminal WSL):

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
Menjalankan 10 konfigurasi pengujian (masing-masing 3 repetisi dengan warm-up CPU otomatis dan perutean *single source of truth* baseline) ke `results/results.json` serta `results/results.csv`:
```bash
python benchmark.py --force
```
*Catatan: Skrip mendukung resumability. Jika terhenti, eksekusi akan melanjutkan konfigurasi yang belum selesai. Gunakan flag `--force` untuk menjalankan ulang seluruh benchmark dari awal.*

### Langkah 4: Membuat Grafik Analisis (Matplotlib 300 DPI)
Menghasilkan 5 grafik PNG berkualitas cetak di direktori `results/charts/`:
```bash
python make_charts.py
```

### Langkah 5: Menghasilkan Diagram Arsitektur
Menghasilkan diagram arsitektur teknis (`arsitektur_hybrid.png` 300 DPI dan `arsitektur_hybrid.svg`):
```bash
python render_diagram.py
```

### Langkah 6: Menjalankan Dashboard Visualisasi Web
Menjalankan web server lokal untuk melihat dashboard interaktif berbasis Chart.js:
```bash
python serve.py --port 8000
```
Buka browser pada alamat: **`http://localhost:8000`**

---

## 6. Ringkasan Hasil Eksperimen Utama (10 Konfigurasi Nyata)

Pengujian dilakukan pada prosesor **AMD Ryzen 5 5600H** (6 Core Fisik / 12 Core Logis, 15.4 GB RAM, Windows 11 64-bit):

| No | Jumlah Thread | Jumlah Process | Data/Task | Waktu (s) | Speedup | Efisiensi (%) | Keterangan |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | **1** | **1** | **1460** | **48.90** | **1.00x** | **100.00%** | **Baseline Serial Utama (1.460 File)** |
| 2 | 4 | 1 | 1460 | 45.17 | 1.08x | 108.00% | Efek thread I/O pada single worker |
| 3 | 1 | 3 | 1460 | 24.28 | 2.01x | 67.00% | Skalabilitas proses (P=3) |
| 4 | 2 | 3 | 1460 | 24.47 | 2.00x | 66.67% | Variasi thread pada P=3 |
| **5** | **4** | **3** | **1460** | **24.42** | **2.00x** | **66.67%** | **Konfigurasi Wajib NIM (Throughput 59.80 f/s)** |
| 6 | 8 | 3 | 1460 | 24.35 | 2.01x | 67.00% | Saturasi thread (kurva mendatar) |
| 7 | 4 | 2 | 1460 | 35.18 | 1.39x | 69.50% | Skalabilitas 2 proses |
| **8** | **4** | **6** | **1460** | **17.11** | **2.86x** | **47.67%** | **Konfigurasi Tercepat (Throughput 85.32 f/s)** |
| 9 | 4 | 3 | 500 | 8.30 | 1.92x | 64.00% | Dataset kecil (Baseline 500: 15.92 s) |
| 10 | 4 | 3 | 1000 | 17.12 | 1.97x | 65.67% | Dataset sedang (Baseline 1000: 33.80 s) |

---

## 7. Definisi Metrik Komputasi Paralel

1. **Speedup ($S$)**:
   $$S = \frac{T_{\text{serial}}}{T_{\text{hybrid}}}$$
   Mengukur akselerasi komputasi hybrid relatif terhadap baseline serial murni pada ukuran dataset file yang sama persis.

2. **Efisiensi Komputasi ($E$)**:
   $$E = \frac{S}{P} \times 100\%$$
   Mengukur persentase utilisasi relatif core prosesor ($P$ = jumlah proses worker). Nilai cenderung menurun seiring bertambahnya proses sesuai Hukum Amdahl.

3. **Throughput ($TP$)**:
   $$TP = \frac{\text{Jumlah File}}{T_{\text{total}}} \quad (\text{file/detik})$$
   Mengukur laju penyelesaian berkas teks per satuan waktu.

---

## 8. Keputusan Desain & Rekayasa Sistem

1. **Pemisahan Tegas Tahap I/O dan CPU**:
   - `ThreadPoolExecutor` menangani pembacaan file dan pembersihan Gutenberg. Multi-threading sangat efektif untuk operasi I/O disk karena GIL dilepas selama transfer data dari disk ke buffer memori.
   - `ProcessPoolExecutor` menangani kalkulasi analitik teks (regex kata, vokal, angka, simbol, kalimat, frekuensi kata) untuk memotong batas GIL dengan mendistribusikan beban ke proses independen pada core CPU terpisah.
2. **Penerapan Batching Adaptif pada IPC (Inter-Process Communication)**:
   - Objek yang dikirim ke worker ProcessPool adalah batch teks bersih (`List[Tuple[str, str, int]]`), bukan path file. Hal ini menjamin tidak ada operasi I/O berulang pada worker CPU.
   - Mengelompokkan file menjadi batch adaptif ($15 \le \text{batch\_size} \le 25$) mereduksi *overhead* pickling/unpickling objek Python lewat socket/pipe IPC.
3. **Keadilan Pengukuran Baseline (*Fair Baseline*)**:
   - Jalur serial (`run_serial`) menjalankan fungsi worker `analyze_batch_worker` dan struktur pembagian batch yang sama persis dengan hybrid di proses utama (tanpa pool). Hal ini memastikan bahwa metrik speedup murni mencerminkan percepatan paralelisme hardware, bukan asimetri algoritma.
4. **Single Source of Truth Baseline**:
   - Baseline untuk setiap ukuran data diukur secara terpusat oleh `benchmark.py` dan disimpan di `results/results.json`. Modul `analyzer.py` membaca langsung dari sumber data tersebut untuk menghindari deviasi angka.
5. **Ketahanan terhadap Drift Mesin (*Robustness against Machine Drift*)**:
   - Dilengkapi warm-up komputasi CPU sebelum benchmark dimulai agar clock prosesor berada pada kondisi *steady state*.
   - Stability check otomatis: jika variasi repetisi $> 5\%$, konfigurasi otomatis diulang (maksimal 2 retry).
   - Drift check akhir menguji ulang baseline 500 file di akhir sesi untuk mendeteksi *thermal throttling*.
6. **Kompatibilitas Windows Multiprocessing**:
   - Sistem operasi Windows menggunakan metode `spawn` (bukan `fork`). Seluruh fungsi worker ditempatkan pada tingkat modul (*top-level*) dan seluruh skrip dilindungi oleh blok `if __name__ == "__main__":`.
