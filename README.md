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

1. **Task / Thread Parallelism (`concurrent.futures.ThreadPoolExecutor`)**:  
   Menangani pekerjaan *I/O-bound*, yaitu membaca berkas teks dari disk lokal dan membersihkan header/footer lisensi Gutenberg. Multi-threading pada tahap ini sangat efektif karena *Global Interpreter Lock* (GIL) Python secara otomatis dilepas selama operasi I/O tingkat sistem operasi.
2. **Process Pool (`concurrent.futures.ProcessPoolExecutor`)**:  
   Menangani komputasi berat *CPU-bound*, yaitu tokenisasi regex kata, penghitungan kalimat, simbol, vokal, angka, serta agregasi frekuensi kata (*word frequency counter*). Multi-processing memotong batas GIL dengan mendistribusikan beban ke proses-proses independen yang berjalan di atas core fisik prosesor terpisah.

---

## 2. Parameter Berdasarkan NIM (NIM: 247006111146)

Seluruh parameter komputasi diturunkan secara unik dan deterministik dari NIM mahasiswa sesuai formula naskah soal UTS:

- **Seed Acak Global**: `random.seed(247006111146)`
- **Jumlah Thread ($T$)**:
  $$\text{Dua digit terakhir NIM mod } 4 + 2 = (46 \bmod 4) + 2 = 2 + 2 = \mathbf{4\text{ Thread}}$$
- **Jumlah Proses ($P$)**:
  $$\text{Dua digit tengah NIM mod } 3 + 2 = (61 \bmod 3) + 2 = 1 + 2 = \mathbf{3\text{ Proses}}$$
- **Jumlah Data File ($N$)**:
  $$\text{Tiga digit terakhir NIM} \times 10 = 146 \times 10 = \mathbf{1.460\text{ File Teks}}$$

Seluruh konstanta dideklarasikan terpusat di `config.py` sebagai sumber tunggal konfigurasi sistem.

---

## 3. Struktur Repositori

```text
file_analyzer/
├── .gitignore                # Aturan pengabaian cache, dataset besar, dan berkas draft
├── README.md                 # Dokumentasi komprehensif proyek
├── config.py                 # Parameter terpusat (NAMA, NIM, SEED, THREADS, PROCESSES, DATA_COUNT, PATHS)
├── analyzer.py               # Modul inti komputasi Serial dan Hybrid + validasi integritas
├── benchmark.py              # Runner benchmark 10 konfigurasi x 3 repetisi + warm-up & drift check
├── make_charts.py            # Generator 5 grafik analisis kinerja resolusi tinggi (300 DPI)
├── render_diagram.py         # Skrip perender diagram arsitektur sistem (output: arsitektur_hybrid.png)
├── serve.py                  # Server web HTTP lokal untuk menyajikan dashboard visualisasi (port 8000)
├── manifest.csv              # Indeks urutan 1.460 file Gutenberg deterministik (seed NIM)
├── pg_catalog.csv            # Salinan katalog buku teks Project Gutenberg
├── data_wc_real/             # Direktori dataset 1.460 berkas teks Project Gutenberg (~538 MiB)
├── results/
│   ├── results.csv           # Tabel ringkasan 10 konfigurasi pengujian
│   ├── results.json          # Data mentah lengkap, spesifikasi mesin, baselines, korpus, dan validasi
│   └── charts/               # Berkas gambar grafik analisis hasil benchmark (300 DPI)
│       ├── chart_1_time_vs_threads.png
│       ├── chart_2_time_vs_processes.png
│       ├── chart_3_speedup_vs_configs.png
│       ├── chart_4_efficiency_vs_configs.png
│       └── chart_5_phase_breakdown_stacked.png
├── dashboard/                # Antarmuka web visualisasi mandiri (offline tanpa CDN eksternal)
│   ├── index.html            # Markup antarmuka bertema profiler teknis ilmiah
│   ├── style.css             # Desain antarmuka (Dark & Light mode, palet kontras tinggi)
│   ├── app.js                # Logika interaktif Chart.js, sortir tabel, dan ekspor CSV client-side
│   └── chart.min.js          # Pustaka Chart.js v4.5.1 lokal
└── docs/
    └── misc/                 # Berkas arsip draft laporan internal dan skrip utilitas pendukung
```

---

## 4. Prasyarat & Instalasi

Proyek ini dibangun di atas Python 3 (diuji pada Python 3.11.9 Windows / WSL). Sistem hanya memerlukan pustaka standar Python ditambah dua pustaka analisis/grafik:

```bash
pip install matplotlib psutil
```

*(Opsional) Jika ingin menjalankan skrip pendukung pembuatan dokumen laporan Word di folder `docs/misc/`:*
```bash
pip install python-docx
```

---

## 5. Urutan Menjalankan Program

Jalankan perintah berikut secara berurutan di terminal (PowerShell, Command Prompt, atau terminal WSL):

### Langkah 1: Persiapan Dataset (Sudah Terunduh Lengkap)
Dataset sebanyak 1.460 buku teks telah tersedia lengkap di folder `data_wc_real/` dengan indeks deterministik pada `manifest.csv`. Jika ingin memeriksa integritas atau mengunduh ulang di lingkungan baru:
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
# Menjalankan konfigurasi kustom
python analyzer.py --threads 4 --procs 3 --data 1460 --mode hybrid

# Menjalankan mode serial baseline murni
python analyzer.py --mode serial --data 1460

# Menjalankan validasi ulang terhadap baseline
python analyzer.py --data 500 --validate
```

### Langkah 3: Menjalankan Benchmark 10 Konfigurasi
Menjalankan 10 konfigurasi pengujian (masing-masing 3 repetisi dengan warm-up CPU otomatis, stability check, dan perutean *single source of truth* baseline) ke `results/results.json` serta `results/results.csv`:
```bash
python benchmark.py --force
```
*Catatan: Skrip mendukung resumability. Jika terhenti, eksekusi akan melanjutkan konfigurasi yang belum selesai. Gunakan flag `--force` untuk menjalankan ulang seluruh benchmark dari awal.*

### Langkah 4: Membuat Grafik Analisis (Matplotlib 300 DPI)
Menghasilkan 5 grafik PNG beresolusi tinggi (300 DPI) di direktori `results/charts/`:
```bash
python make_charts.py
```

### Langkah 5: Menghasilkan Diagram Arsitektur (Opsional)
Menghasilkan diagram arsitektur teknis sistem (`arsitektur_hybrid.png` 300 DPI):
```bash
python render_diagram.py
```

### Langkah 6: Menjalankan Dashboard Visualisasi Web
Menjalankan server web HTTP lokal untuk menyajikan visualisasi data interaktif:
```bash
python serve.py --port 8000
```
Buka browser pada alamat: **`http://localhost:8000`**

---

## 6. Ringkasan Hasil Eksperimen Utama (10 Konfigurasi Nyata)

Seluruh pengujian dijalankan pada satu unit mesin (*single-node workstation*) dengan spesifikasi resmi:
- **Prosesor (CPU):** AMD Ryzen 5 5600H with Radeon Graphics (6 Core Fisik / 12 Core Logis)
- **Memori Utama (RAM):** 15.4 GB
- **Sistem Operasi:** Microsoft Windows 11 Home Single Language (Build 26100)
- **Runtime:** Python 3.11.9 (64-bit)
- **Penyimpanan:** INTEL SSDPEKNU512GZ NVMe SSD

### Tabel Hasil Pengujian 10 Konfigurasi (Rata-rata 3 Repetisi):

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

### Karakteristik Statistik Korpus Teks Gutenberg:
- **Jumlah Berkas:** 1.460 file teks
- **Ukuran Mentah Data:** 537,91 MiB (~564,04 MB)
- **Karakter Bersih:** 532.796.781 karakter
- **Total Kata Bersih:** 91.700.012 kata
- **Statistik Ekstraksi:** 153.472.926 vokal | 3.545.233 angka | 21.344.540 simbol | 4.729.834 kalimat
- **Top-5 Kata Terbanyak:**
  1. `"the"` : 6.174.819 kali
  2. `"of"` : 3.316.622 kali
  3. `"and"` : 2.937.917 kali
  4. `"to"` : 2.416.580 kali
  5. `"a"` : 1.925.853 kali

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
   Mengukur laju penyelesaian pemrosesan berkas teks per satuan waktu.

---

## 8. Keputusan Desain & Rekayasa Performa

1. **Pemisahan Tegas Tahap I/O dan CPU**:
   - `ThreadPoolExecutor` menangani pembacaan file dan pembersihan Gutenberg. Multi-threading efektif untuk I/O disk karena GIL dilepas selama pembacaan byte dari media penyimpanan ke RAM.
   - `ProcessPoolExecutor` menangani kalkulasi analitik teks (regex kata, vokal, angka, simbol, kalimat, frekuensi kata) untuk memotong batas GIL dengan mendistribusikan beban ke proses independen pada core CPU terpisah.
2. **Penerapan Batching Adaptif pada IPC (Inter-Process Communication)**:
   - Objek yang dikirim ke worker ProcessPool adalah batch teks bersih (`List[Tuple[str, str, int]]`), bukan path file. Hal ini menjamin tidak ada pembacaan disk berulang pada worker CPU.
   - Mengelompokkan file menjadi batch adaptif ($15 \le \text{batch\_size} \le 25$) mereduksi *overhead* pickling/unpickling objek Python lewat socket/pipe IPC.
3. **Keadilan Pengukuran Baseline (*Fair Baseline*)**:
   - Jalur serial (`run_serial`) menjalankan fungsi worker `analyze_batch_worker` dan struktur pembagian batch yang sama persis dengan hybrid di proses utama (tanpa pool). Hal ini memastikan bahwa metrik speedup murni mencerminkan percepatan paralelisme hardware, bukan asimetri algoritma atau perbedaan struktur data.
4. **Single Source of Truth Baseline**:
   - Baseline untuk setiap ukuran data diukur secara terpusat oleh `benchmark.py` dan disimpan di `results/results.json`. Modul `analyzer.py` membaca langsung dari sumber data tersebut untuk menghindari deviasi angka antar-komponen.
5. **Ketahanan terhadap Drift Mesin (*Robustness against Machine Drift*)**:
   - Dilengkapi warm-up komputasi CPU sebelum benchmark dimulai untuk membantu clock prosesor mencapai kondisi yang lebih stabil sebelum pengukuran.
   - Stability check otomatis: jika variasi repetisi $> 5\%$, konfigurasi otomatis diulang (maksimal 2 retry).
   - Drift check akhir menguji ulang baseline 500 file di akhir sesi untuk mendeteksi *thermal throttling* atau pergeseran clock dinamis.
6. **Kompatibilitas Windows Multiprocessing**:
   - Sistem operasi Windows menggunakan metode proses `spawn` (bukan `fork`). Seluruh fungsi worker ditempatkan pada tingkat modul (*top-level*) dan seluruh skrip dilindungi oleh blok `if __name__ == "__main__":`.
7. **Peniadaan Dependensi Eksternal pada Dashboard Web**:
   - Antarmuka visualisasi web dibuat menggunakan HTML, CSS modern, dan pustaka `chart.min.js` lokal (tanpa framework, tanpa Node.js/npm, dan tanpa dependensi CDN eksternal) sehingga dapat dijalankan secara instan dalam kondisi offline melalui `python serve.py`.
