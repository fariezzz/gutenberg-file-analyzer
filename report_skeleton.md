# Laporan Ujian Tengah Semester (UTS)
## Komputasi Paralel dan Terdistribusi

**Tema:** Hybrid Computing for Real-World Simulation and Data Processing  
**Topik Proyek:** Parallel File Analyzer (Project Gutenberg Text Corpus)  
**Program Studi:** Informatika, Fakultas Teknik, Universitas Siliwangi  

---

### Identitas Mahasiswa
- **Nama:** Muhammad Fariez Riziq Ilham
- **NPM:** 247006111146
- **Kelas:** E
- **Dosen Pengampu:** Ir. Randi Rizal, Ph.D.
- **Slogan Proyek:** *“Think Parallel. Work Distributed. Create Hybrid Innovation”.*

---

## Bagian A — Konsep & Desain Arsitektur (Bobot 20%)

### 1. Diagram Arsitektur Hybrid Computing

Berikut adalah alur arsitektur sistem *Parallel File Analyzer* yang memadukan paradigma *Task/Thread Parallelism* untuk fase I/O dan *Process Pool* untuk fase CPU-bound:

![Diagram Arsitektur Hybrid Computing](arsitektur_hybrid.png)

```mermaid
flowchart TD
    subgraph Storage [Penyimpanan Lokal]
        DS[(1.460 Berkas Teks Gutenberg<br/>data_wc_real/*.txt)]
        MF[manifest.csv<br/>Indeks Deterministik Seed NIM]
    end

    subgraph PhaseIO [Fase 1: I/O & Pembersihan Teks (Thread Pool)]
        MF --> TP[ThreadPoolExecutor<br/>4 Worker Threads]
        DS --> TP
        TP -->|Thread 1| T1[Baca & Bersihkan Teks Header/Footer]
        TP -->|Thread 2| T2[Baca & Bersihkan Teks Header/Footer]
        TP -->|Thread 3| T3[Baca & Bersihkan Teks Header/Footer]
        TP -->|Thread 4| T4[Baca & Bersihkan Teks Header/Footer]
    end

    subgraph Batching [Adaptive Batch Partitioning]
        T1 & T2 & T3 & T4 --> BPart[Pengelompokan Batch Teks Bersih<br/>Batch Size = 15-25 Dokumen/Tugas]
    end

    subgraph PhaseCPU [Fase 2: Analisis Linguistik CPU-Bound (Process Pool)]
        BPart --> PP[ProcessPoolExecutor<br/>3 Worker Processes]
        PP -->|Batch Data| W1[Process Worker 1 (Core 1)<br/>Tokenisasi Regex, Vokal, Angka, Word Counter]
        PP -->|Batch Data| W2[Process Worker 2 (Core 2)<br/>Tokenisasi Regex, Vokal, Angka, Word Counter]
        PP -->|Batch Data| W3[Process Worker 3 (Core 3)<br/>Tokenisasi Regex, Vokal, Angka, Word Counter]
    end

    subgraph PhaseReduce [Fase 3: Agregasi & Validasi (Main Process)]
        W1 & W2 & W3 -->|Ringkasan Statistik Numerik & Counter| Reducer[Reducer / Aggregator Utama]
        Reducer --> OutTerminal[Output Terminal Terformat<br/>Speedup, Efisiensi, Throughput]
        Reducer --> OutJSON[results.json & results.csv]
        Reducer --> OutDash[Dashboard Web Chart.js]
    end

    subgraph OptionalMPI [Komputasi Terdistribusi Multi-Node (Opsional)]
        MPIBlock[MPI / Message Passing Interface<br/>(Ditandai: Tidak Digunakan / Single-Node Workstation)]
    end
```

### 2. Penjelasan Desain Alur dan Pembagian Beban

1. **Peran ThreadPoolExecutor (Fase I/O-Bound)**:
   Membaca 1.460 berkas teks dari disk lokal NVMe dan melakukan pembersihan boilerplate Gutenberg (*header* `*** START OF` dan *footer* `*** END OF`). Multi-threading sangat optimal pada fase ini karena *Global Interpreter Lock* (GIL) Python dilepas secara otomatis oleh runtime saat proses transfer I/O dari filesystem ke buffer memori sistem operasi.
2. **Peran ProcessPoolExecutor (Fase CPU-Bound)**:
   Melakukan parsing linguistik intensif (tokenisasi regex kata `\b[a-zA-Z]+\b`, kalimat, simbol, karakter vokal, angka, dan `Counter` frekuensi kata). Karena komputasi ini murni CPU-bound, penggunaan proses terpisah mutlak diperlukan agar tugas dapat dieksekusi secara konkuren pada core fisik prosesor yang berbeda tanpa hambatan GIL.
3. **Strategi Batching & Reduksi Overhead IPC**:
   Data yang dikirimkan ke worker proses adalah *batch teks bersih* (bukan path file), sehingga worker CPU tidak lagi melakukan I/O disk berulang. Dokumen dikelompokkan ke dalam batch adaptif (15–25 dokumen per tugas) guna menekan frekuensi serialisasi *pickle* antar proses melalui OS pipe/socket.
4. **Catatan MPI**:
   MPI (*Message Passing Interface*) ditandai tidak digunakan karena pengujian dilakukan pada lingkungan mesin tunggal (*single-node workstation* 6 core fisik / 12 core logis). Kombinasi Threading + Process Pool telah merepresentasikan paradigma *hybrid computing* secara utuh dan efisien.

---

## Bagian B — Implementasi Kode (Bobot 40%)

### 1. Perhitungan Parameter Pribadi Berdasarkan NIM

- **NIM:** `247006111146`
- **Seed Global:** `247006111146` (digunakan pada pengacakan dataset Gutenberg)
- **Jumlah Thread:**
  $$\text{Dua digit terakhir NIM mod } 4 + 2 = (46 \bmod 4) + 2 = 2 + 2 = \mathbf{4\text{ Thread}}$$
- **Jumlah Proses:**
  $$\text{Dua digit tengah NIM mod } 3 + 2 = (61 \bmod 3) + 2 = 1 + 2 = \mathbf{3\text{ Proses}}$$
- **Jumlah Data:**
  $$\text{Tiga digit terakhir NIM} \times 10 = 146 \times 10 = \mathbf{1.460\text{ File Teks}}$$

### 2. Cuplikan Kode Sumber Inti (Verbatim Source Code)

#### a. Konfigurasi Terpusat (`config.py`)
```python
NAMA = "Muhammad Fariez Riziq Ilham"
NIM = "247006111146"
SEED = 247006111146

# Perhitungan Parameter Sesuai Ketentuan Soal UTS:
# - Dua digit terakhir NIM = 46 -> 46 mod 4 + 2 = 2 + 2 = 4
THREADS = (46 % 4) + 2

# - Dua digit tengah NIM = 61 -> 61 mod 3 + 2 = 1 + 2 = 3
PROCESSES = (61 % 3) + 2

# - Tiga digit terakhir NIM = 146 -> 146 x 10 = 1460
DATA_COUNT = 146 * 10
```

#### b. Pembersihan Teks Gutenberg (`analyzer.py`)
```python
def clean_gutenberg_text(raw_text: str) -> str:
    """
    Membersihkan boilerplate / header dan footer Project Gutenberg.
    Membuang semua teks sebelum penanda '*** START OF' dan sesudah '*** END OF'.
    Jika penanda tidak ditemukan, memakai teks utuh apa adanya.
    """
    text = raw_text
    start_match = RE_START_MARKER.search(text)
    if start_match:
        text = text[start_match.end():]
        
    end_match = RE_END_MARKER.search(text)
    if end_match:
        text = text[:end_match.start()]
        
    return text.strip()
```

#### c. Worker Analisis CPU-Bound (`analyzer.py`)
```python
def analyze_batch_worker(batch_items):
    """
    Worker function CPU-bound untuk ProcessPool:
    Menerima batch teks bersih, melakukan tokenisasi regex, ekstraksi statistik,
    dan penghitungan frekuensi kata.
    Mencatat PID dan durasi kerja worker untuk analisis load imbalance.
    """
    worker_pid = os.getpid()
    t_start = time.perf_counter()

    batch_chars = 0
    batch_vowels = 0
    batch_digits = 0
    batch_symbols = 0
    batch_sentences = 0
    batch_words = 0
    batch_bytes = 0
    word_counter = Counter()

    for filename, cleaned_text, raw_bytes in batch_items:
        batch_bytes += raw_bytes
        batch_chars += len(cleaned_text)
        batch_vowels += sum(cleaned_text.count(v) for v in VOWEL_CHARS)
        batch_digits += sum(cleaned_text.count(d) for d in DIGIT_CHARS)
        batch_symbols += len(RE_SYMBOL.findall(cleaned_text))
        batch_sentences += len(RE_SENTENCE.findall(cleaned_text))

        words = RE_WORD.findall(cleaned_text.lower())
        batch_words += len(words)
        word_counter.update(words)

    t_end = time.perf_counter()
    worker_duration = t_end - t_start

    return {
        "pid": worker_pid,
        "worker_time": worker_duration,
        "file_count": len(batch_items),
        "total_bytes": batch_bytes,
        "char_count": batch_chars,
        "vowel_count": batch_vowels,
        "digit_count": batch_digits,
        "symbol_count": batch_symbols,
        "sentence_count": batch_sentences,
        "word_count": batch_words,
        "word_counter": word_counter,
    }
```

#### d. Eksekusi Pipeline Hybrid (`analyzer.py`)
```python
def run_hybrid(file_paths: list, n_threads: int, n_procs: int) -> dict:
    t_pipeline_start = time.perf_counter()

    # Fase 1: I/O Paralel (ThreadPoolExecutor)
    t_io_start = time.perf_counter()
    if n_threads > 1:
        with ThreadPoolExecutor(max_workers=n_threads) as thread_pool:
            io_results = list(thread_pool.map(read_and_clean_file, file_paths))
    else:
        io_results = [read_and_clean_file(fp) for fp in file_paths]
    t_io = time.perf_counter() - t_io_start

    # Pengelompokan Batch Adaptif untuk Meminimalkan Overhead IPC / Pickle
    total_items = len(io_results)
    batch_size = max(1, min(25, math.ceil(total_items / (n_procs * 4))))
    batches = [io_results[i:i + batch_size] for i in range(0, total_items, batch_size)]

    # Fase 2: CPU Paralel (ProcessPoolExecutor)
    t_cpu_start = time.perf_counter()
    if n_procs > 1:
        with ProcessPoolExecutor(max_workers=n_procs) as proc_pool:
            batch_outputs = list(proc_pool.map(analyze_batch_worker, batches))
    else:
        with ProcessPoolExecutor(max_workers=1) as proc_pool:
            batch_outputs = list(proc_pool.map(analyze_batch_worker, batches))
    t_cpu = time.perf_counter() - t_cpu_start

    # Fase 3: Reducer (Penggabungan di Proses Utama)
    t_reduce_start = time.perf_counter()
    agg_chars = agg_vowels = agg_digits = agg_symbols = agg_sentences = agg_words = agg_bytes = 0
    global_counter = Counter()
    worker_map = {}

    for item in batch_outputs:
        agg_chars += item["char_count"]
        agg_vowels += item["vowel_count"]
        agg_digits += item["digit_count"]
        agg_symbols += item["symbol_count"]
        agg_sentences += item["sentence_count"]
        agg_words += item["word_count"]
        agg_bytes += item["total_bytes"]
        global_counter.update(item["word_counter"])

        pid = item["pid"]
        if pid not in worker_map:
            worker_map[pid] = {"pid": pid, "file_count": 0, "total_bytes": 0, "worker_time": 0.0, "batch_count": 0}
        worker_map[pid]["file_count"] += item["file_count"]
        worker_map[pid]["total_bytes"] += item["total_bytes"]
        worker_map[pid]["worker_time"] += item["worker_time"]
        worker_map[pid]["batch_count"] += 1

    top_20 = global_counter.most_common(20)
    top_10 = top_20[:10]
    t_reduce = time.perf_counter() - t_reduce_start
    t_total = time.perf_counter() - t_pipeline_start
    ...
```

---

## Bagian C — Hasil Eksperimen (Bobot 25%)

### 1. Spesifikasi Mesin Pengujian
- **Model CPU:** AMD Ryzen 5 5600H with Radeon Graphics
- **Jumlah Core:** 6 Core Fisik / 12 Core Logis
- **Memori RAM:** 15.4 GB
- **Sistem Operasi:** Windows 11 Home 64-bit (Build 26100)
- **Versi Python:** Python 3.11.9
- **Media Penyimpanan:** INTEL SSDPEKNU512GZ SSD NVMe

### 2. Tabel Hasil Eksperimen (10 Konfigurasi x 3 Repetisi)

| No | Jumlah Thread | Jumlah Process | Data/Task | Waktu (s) | Speedup | Efisiensi (%) |
|:--:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | 1 | 1 | 1460 | 69.79 | 1.00 | 100.00 |
| 2 | 4 | 1 | 1460 | 54.49 | 1.28 | 128.00 |
| 3 | 1 | 3 | 1460 | 27.49 | 2.54 | 84.67 |
| 4 | 2 | 3 | 1460 | 27.32 | 2.55 | 85.00 |
| 5 | **4** | **3** | **1460** | **27.24** | **2.56** | **85.33** |
| 6 | 8 | 3 | 1460 | 27.60 | 2.53 | 84.33 |
| 7 | 4 | 2 | 1460 | 38.54 | 1.81 | 90.50 |
| 8 | 4 | 6 | 1460 | 19.02 | 3.67 | 61.17 |
| 9 | 4 | 3 | 500 | 9.41 | 1.85 | 61.67 |
| 10 | 4 | 3 | 1000 | 19.03 | 1.94 | 64.67 |

*Catatan:*
- *Baris 1 adalah Baseline Serial untuk 1.460 file (69.79 s).*
- *Baris 5 adalah Konfigurasi Wajib NIM 247006111146 (4 Thread, 3 Process, 1.460 File).*
- *Baris 8 adalah Konfigurasi Tercepat pada dataset 1.460 file (4T / 6P, Speedup 3.67x).*
- *Baseline serial dihitung terpisah untuk setiap ukuran data: Baseline 500 file = 17.43 s, Baseline 1000 file = 36.96 s, Baseline 1460 file = 69.79 s.*

### 3. Tiga Grafik Wajib Sesuai Ketentuan Soal UTS

#### Grafik 1: Waktu vs Jumlah Thread (Proses Tetap = 3, Data = 1.460 File)
![Waktu vs Jumlah Thread](results/charts/chart_1_time_vs_threads.png)

#### Grafik 2: Waktu vs Jumlah Process (Thread Tetap = 4, Data = 1.460 File)
![Waktu vs Jumlah Process](results/charts/chart_2_time_vs_processes.png)

#### Grafik 3: Speedup vs Konfigurasi
![Speedup vs Konfigurasi](results/charts/chart_3_speedup_vs_configs.png)

---

## Bagian D — Analisis dan Kesimpulan (Bobot 15%)

> **Petunjuk Pengisian:** Bagian ini disediakan sebagai kerangka untuk diisi oleh mahasiswa berdasarkan data nyata pada tabel hasil, berkas `results/results.json`, serta grafik di atas.

### 1. Perbedaan Performa Antar Konfigurasi
*Petunjuk data acuan:*
- Bandingkan **Konfigurasi 1 (1T/1P: 69.79s)** dengan **Konfigurasi 5 (4T/3P: 27.24s)**: Perpaduan 4 Thread dan 3 Proses berhasil memangkas waktu sebesar 61% dengan speedup 2.56x.
- Bandingkan pengaruh jumlah proses (C2: 54.49s -> C7: 38.54s -> C5: 27.24s -> C8: 19.02s). Terlihat tren penurunan waktu yang curam seiring bertambahnya core prosesor CPU.
- Bandingkan pengaruh jumlah thread pada 3 proses (C3: 27.49s, C4: 27.32s, C5: 27.24s, C6: 27.60s). Peningkatan dari 1 ke 4 thread memberikan efisiensi I/O, namun pada 8 thread (C6) waktu sedikit naik karena *context switching overhead*.
- Bandingkan skalabilitas ukuran data (C9: 500 file / 9.41s vs C10: 1000 file / 19.03s vs C5: 1460 file / 27.24s) yang menunjukkan throughput stabil (~53 file/detik).

*[Tuliskan analisis komparatif performa Anda di sini]*

---

### 2. Faktor yang Paling Memengaruhi Kecepatan Program (I/O, CPU, atau Komunikasi/IPC?)
*Petunjuk data acuan:*
- Periksa data rata-rata fase waktu (`avg_phase_times`) dan grafik *Stacked Breakdown* (`chart_5_phase_breakdown_stacked.png`).
- Pada Konfigurasi NIM (4T/3P, 1460 file):
  - **Fase I/O (ThreadPool):** ~3.43 s (~12.6% dari total waktu)
  - **Fase CPU (ProcessPool):** ~22.75 s (~83.5% dari total waktu)
  - **Fase Reduce (Agregasi):** ~1.06 s (~3.9% dari total waktu)
- Komputasi tokenisasi teks, regular expression, dan penghitungan frekuensi kata terbukti menjadi faktor paling dominan (>83%). Oleh karena itu, percepatan terbesar diperoleh dari penambahan proses worker CPU.

*[Tuliskan analisis faktor dominan Anda di sini]*

---

### 3. Analisis Bottleneck pada Kombinasi Thread + Process
*Petunjuk data acuan:*
- **Hukum Amdahl (*Serial Fraction*):** Fase reduksi (penggabungan Counter di proses utama) dan tahapan koleksi batch awal tidak dapat diparalelkan secara penuh, menjadi batas teoretis percepatan maksimum.
- **Overhead Serialisasi IPC (Pickle):** Proses transfer batch teks dan pengembalian Counter melalui OS socket/pipe menimbulkan beban serialisasi memori.
- **Load Imbalance Antar Worker:** Lihat data `worker_stats` pada `results.json` dan histogram ukuran file (`chart_histogram.png`). File Gutenberg memiliki rentang ukuran dari <100 KB hingga >1 MB, sehingga worker yang menerima file berukuran besar bekerja sedikit lebih lama dibanding worker lainnya.

*[Tuliskan analisis bottleneck Anda di sini]*

---

### 4. Kesimpulan Umum Eksperimen
*Petunjuk poin kesimpulan:*
- Ringkas efektivitas paradigma *Hybrid Computing* (Threading untuk I/O + Multiprocessing untuk CPU).
- Sebutkan capaian metrik konfigurasi pribadi NIM (Waktu 27.24 s, Speedup 2.56x, Efisiensi 85.33%, Throughput 53.60 file/detik).
- Nyatakan validitas hasil bahwa seluruh kalkulasi agregat korpus antara Serial dan Hybrid terbukti 100% konsisten/identik.

*[Tuliskan kesimpulan menyeluruh Anda di sini]*
