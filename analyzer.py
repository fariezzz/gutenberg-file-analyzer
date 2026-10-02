"""
Modul Inti Parallel File Analyzer (Hybrid Computing)
Proyek UTS Komputasi Paralel dan Terdistribusi
Teknik Informatika - Universitas Siliwangi

Definisi Metrik:
1. Speedup     = T_serial / T_hybrid
   (Perbandingan waktu eksekusi sekuensial murni terhadap waktu eksekusi hybrid
   pada jumlah dataset file yang sama persis).
2. Efisiensi   = (Speedup / Jumlah Proses) x 100%
   (Mengukur utilisasi relatif core prosesor dalam mengeksekusi komputasi paralel).
3. Throughput  = Jumlah File / Waktu Total (file/detik)
   (Mengukur laju pemrosesan data per satuan waktu).

Keputusan Desain Arsitektur & IPC (Inter-Process Communication):
1. Pemisahan Tahap I/O dan CPU:
   - Tahap I/O ditangani oleh ThreadPoolExecutor (I/O-bound: pembacaan disk & pembersihan Gutenberg).
     Pemanfaatan multi-threading pada tahap ini sangat efektif karena GIL (Global Interpreter Lock)
     dilepas saat proses pembacaan file dari disk ke memori (OS-level I/O).
   - Tahap CPU ditangani oleh ProcessPoolExecutor (CPU-bound: regex tokenisasi, ekstraksi statistik, frekuensi kata).
     Multi-processing mengatasi batasan GIL dengan menjalankan worker pada proses independen
     dengan alokasi core CPU masing-masing.
2. Pengiriman Batch Objek (Batching):
   - Yang dikirim ke worker ProcessPool adalah batch teks bersih (bukan path file). Hal ini
     menjamin disk I/O 100% selesai di fase ThreadPool dan tidak ada I/O berulang pada worker CPU.
   - Batching (mengelompokkan sejumlah teks per pekerjaan) mereduksi overhead pickling / IPC round-trip.
     Jika 1460 file dikirim satu per satu, overhead serialize/deserialize objek Python lewat socket/pipe
     akan mendominasi waktu eksekusi. Dengan batching terukur, overhead serialisasi dapat diminimalisir.
3. Struktur Reducer:
   - Worker hanya mengembalikan ringkasan statistik numerik, durasi eksekusi worker, dan Counter kata.
     Teks mentah tidak dikembalikan ke proses utama untuk menghemat bandwidth memori dan waktu unpickling.
"""

import os
import sys
import time
import re
import csv
import json
import math
import argparse
from datetime import datetime
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

import config

# Pre-compiled Regex untuk performa maksimal pada fase CPU-bound
RE_START_MARKER = re.compile(r"\*\*\*\s*START OF[^\r\n]*", re.IGNORECASE)
RE_END_MARKER = re.compile(r"\*\*\*\s*END OF", re.IGNORECASE)
RE_WORD = re.compile(r"\b[a-zA-Z]+\b")
RE_SENTENCE = re.compile(r"[.!?]+(?:\s+|$)")
RE_SYMBOL = re.compile(r"[^a-zA-Z0-9\s]")

VOWEL_CHARS = "aeiouAEIOU"
DIGIT_CHARS = "0123456789"


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


def read_and_clean_file(file_path: str):
    """
    Tugas I/O-bound:
    Membaca file dengan encoding utf-8 dan errors='ignore',
    kemudian membersihkan penanda Gutenberg.
    Mengembalikan tuple: (filename, cleaned_text, raw_byte_size).
    """
    filename = os.path.basename(file_path)
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            raw_text = f.read()
        raw_bytes = len(raw_text.encode("utf-8", errors="ignore"))
        cleaned_text = clean_gutenberg_text(raw_text)
        return (filename, cleaned_text, raw_bytes)
    except Exception:
        return (filename, "", 0)


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


def get_file_list(data_count: int) -> list:
    """
    Mengambil N file pertama secara deterministik berdasarkan urutan di manifest.csv.
    """
    if not os.path.exists(config.MANIFEST_PATH):
        raise FileNotFoundError(
            f"File manifest tidak ditemukan di: {config.MANIFEST_PATH}. "
            f"Jalankan skrip unduhan terlebih dahulu."
        )

    file_list = []
    with open(config.MANIFEST_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fname = row.get("filename")
            if not fname:
                continue
            full_path = os.path.join(config.DATA_DIR, fname)
            if os.path.exists(full_path):
                file_list.append(full_path)
            if len(file_list) >= data_count:
                break

    if len(file_list) < data_count:
        raise ValueError(
            f"Jumlah file pada direktori ({len(file_list)}) kurang dari data_count ({data_count})."
        )
    return file_list


def run_serial(file_paths: list) -> dict:
    """
    Eksekusi SERIAL murni (1 Thread, 1 Process, tanpa pool executor) sebagai baseline.
    Menjalankan alur baca -> analisis -> agregasi secara sekuensial.

    Desain komparasi adil (fair baseline):
    Serial menjalankan fungsi worker (analyze_batch_worker) dan struktur batching yang
    sama persis dengan worker hybrid, dieksekusi secara sekuensial di proses utama
    tanpa pool executor, kemudian diagregasikan (reducer) dengan logika yang sama.
    Dengan beban kerja dan struktur data yang identik, speedup murni mengukur
    efek paralelisme hardware, bukan asimetri algoritma atau struktur data.
    """
    t_pipeline_start = time.perf_counter()

    # Fase 1: I/O Pembacaan dan Pembersihan Sekuensial
    t_io_start = time.perf_counter()
    cleaned_items = [read_and_clean_file(fp) for fp in file_paths]
    t_io = time.perf_counter() - t_io_start

    # Pengelompokan Batch Adaptif (struktur batch identik dengan hybrid P=1)
    total_items = len(cleaned_items)
    batch_size = max(1, min(25, math.ceil(total_items / 4)))
    batches = [cleaned_items[i:i + batch_size] for i in range(0, total_items, batch_size)]

    # Fase 2: CPU Analisis Sekuensial (memanggil analyze_batch_worker yang sama persis)
    t_cpu_start = time.perf_counter()
    batch_outputs = [analyze_batch_worker(b) for b in batches]
    t_cpu = time.perf_counter() - t_cpu_start

    # Fase 3: Reducer Sekuensial (agregasi metrik & merge Counter)
    t_reduce_start = time.perf_counter()
    agg_chars = 0
    agg_vowels = 0
    agg_digits = 0
    agg_symbols = 0
    agg_sentences = 0
    agg_words = 0
    agg_bytes = 0
    global_counter = Counter()

    pid = os.getpid()
    total_worker_time = sum(item["worker_time"] for item in batch_outputs)

    for item in batch_outputs:
        agg_chars += item["char_count"]
        agg_vowels += item["vowel_count"]
        agg_digits += item["digit_count"]
        agg_symbols += item["symbol_count"]
        agg_sentences += item["sentence_count"]
        agg_words += item["word_count"]
        agg_bytes += item["total_bytes"]
        global_counter.update(item["word_counter"])

    top_20 = global_counter.most_common(20)
    top_10 = top_20[:10]
    t_reduce = time.perf_counter() - t_reduce_start

    t_total = time.perf_counter() - t_pipeline_start

    worker_stats = [
        {
            "pid": pid,
            "file_count": len(file_paths),
            "total_bytes": agg_bytes,
            "worker_time": round(total_worker_time, 4),
            "batch_count": len(batches),
        }
    ]

    return {
        "mode": "serial",
        "threads": 1,
        "processes": 1,
        "total_files": len(file_paths),
        "total_bytes": agg_bytes,
        "total_chars": agg_chars,
        "total_vowels": agg_vowels,
        "total_digits": agg_digits,
        "total_symbols": agg_symbols,
        "total_sentences": agg_sentences,
        "total_words": agg_words,
        "top_20_words": top_20,
        "top_10_words": top_10,
        "phase_times": {
            "io": round(t_io, 4),
            "cpu": round(t_cpu, 4),
            "reduce": round(t_reduce, 4),
            "total": round(t_total, 4),
        },
        "worker_stats": worker_stats,
        "throughput": round(len(file_paths) / t_total, 2) if t_total > 0 else 0,
    }


def run_hybrid(file_paths: list, n_threads: int, n_procs: int) -> dict:
    """
    Eksekusi HYBRID:
    - ThreadPoolExecutor(n_threads) untuk tahap I/O pembacaan & pembersihan file.
    - Pengelompokan teks bersih menjadi batch adaptif.
    - ProcessPoolExecutor(n_procs) untuk tahap CPU analisis teks paralel.
    - Reducer di proses utama untuk menggabungkan hasil dan menghitung statistik worker.
    """
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
    with ProcessPoolExecutor(max_workers=n_procs) as proc_pool:
        batch_outputs = list(proc_pool.map(analyze_batch_worker, batches))
    t_cpu = time.perf_counter() - t_cpu_start

    # Fase 3: Reducer (Penggabungan di Proses Utama)
    t_reduce_start = time.perf_counter()
    agg_chars = 0
    agg_vowels = 0
    agg_digits = 0
    agg_symbols = 0
    agg_sentences = 0
    agg_words = 0
    agg_bytes = 0
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

        # Pelacakan beban kerja per proses worker
        pid = item["pid"]
        if pid not in worker_map:
            worker_map[pid] = {
                "pid": pid,
                "file_count": 0,
                "total_bytes": 0,
                "worker_time": 0.0,
                "batch_count": 0,
            }
        worker_map[pid]["file_count"] += item["file_count"]
        worker_map[pid]["total_bytes"] += item["total_bytes"]
        worker_map[pid]["worker_time"] += item["worker_time"]
        worker_map[pid]["batch_count"] += 1

    top_20 = global_counter.most_common(20)
    top_10 = top_20[:10]
    t_reduce = time.perf_counter() - t_reduce_start

    t_total = time.perf_counter() - t_pipeline_start

    worker_stats = [
        {
            "pid": v["pid"],
            "file_count": v["file_count"],
            "total_bytes": v["total_bytes"],
            "worker_time": round(v["worker_time"], 4),
            "batch_count": v["batch_count"],
        }
        for v in sorted(worker_map.values(), key=lambda x: x["pid"])
    ]

    return {
        "mode": "hybrid",
        "threads": n_threads,
        "processes": n_procs,
        "total_files": len(file_paths),
        "total_bytes": agg_bytes,
        "total_chars": agg_chars,
        "total_vowels": agg_vowels,
        "total_digits": agg_digits,
        "total_symbols": agg_symbols,
        "total_sentences": agg_sentences,
        "total_words": agg_words,
        "top_20_words": top_20,
        "top_10_words": top_10,
        "phase_times": {
            "io": round(t_io, 4),
            "cpu": round(t_cpu, 4),
            "reduce": round(t_reduce, 4),
            "total": round(t_total, 4),
        },
        "worker_stats": worker_stats,
        "throughput": round(len(file_paths) / t_total, 2) if t_total > 0 else 0,
    }


def validate_results(serial_res: dict, hybrid_res: dict):
    """
    Validasi integritas hasil: Memastikan hasil agregat Serial dan Hybrid 100% identik.
    Memeriksa seluruh metrik hitungan numerik dan urutan top-20 kata beserta frekuensinya.
    """
    metrics = [
        "total_files",
        "total_bytes",
        "total_chars",
        "total_vowels",
        "total_digits",
        "total_symbols",
        "total_sentences",
        "total_words",
    ]
    mismatches = []
    for m in metrics:
        s_val = serial_res.get(m)
        h_val = hybrid_res.get(m)
        if s_val != h_val:
            mismatches.append(f"Ketidakcocokan pada {m}: Serial={s_val} vs Hybrid={h_val}")

    # Normalisasi format list/tuple untuk perbandingan yang konsisten (akibat serialisasi JSON)
    s_top20 = [tuple(item) for item in serial_res.get("top_20_words", [])]
    h_top20 = [tuple(item) for item in hybrid_res.get("top_20_words", [])]
    if s_top20 != h_top20:
        mismatches.append(
            f"Ketidakcocokan pada top_20_words:\n  Serial: {s_top20}\n  Hybrid: {h_top20}"
        )

    if mismatches:
        err_msg = "VALIDASI GAGAL! Perbedaan terdeteksi antara Serial dan Hybrid:\n" + "\n".join(mismatches)
        return False, err_msg
    return True, "VALID (Hasil serial dan hybrid 100% identik)"


def get_baseline_for_data(data_count: int, file_paths: list, force_recompute: bool = False):
    """
    Mengambil data baseline serial untuk jumlah file tertentu (Single Source of Truth).
    1. Membaca HANYA dari results/results.json pada key baselines[str(data_count)].
    2. Mengambil waktu modifikasi berkas (mtime) untuk transparansi reproduksibilitas.
    3. Jika results.json atau key tidak ditemukan (atau force_recompute=True),
       tampilkan pesan jelas dan ukur baseline serial secara langsung (1 run),
       lalu beri tanda '(baseline measured now)'.
    """
    if not force_recompute and os.path.exists(config.RESULTS_JSON):
        try:
            mtime_dt = datetime.fromtimestamp(os.path.getmtime(config.RESULTS_JSON))
            mtime_str = mtime_dt.strftime("%Y-%m-%d %H:%M:%S")
            with open(config.RESULTS_JSON, "r", encoding="utf-8") as f:
                saved = json.load(f)
            b = saved.get("baselines", {}).get(str(data_count))
            if b and "mean" in b and "top_20_words" in b:
                return b, False, mtime_str
        except Exception:
            pass

    print(f"[*] Catatan: Baseline untuk data={data_count} tidak ditemukan di results/results.json.")
    print(f"[*] Mengukur baseline serial sekarang...")
    serial_res = run_serial(file_paths)
    serial_res["mean"] = serial_res["phase_times"]["total"]
    return serial_res, True, None


def main():
    parser = argparse.ArgumentParser(
        description="Parallel File Analyzer (Hybrid Thread + Process Pool)"
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=config.THREADS,
        help=f"Jumlah worker thread untuk fase I/O (default: {config.THREADS})",
    )
    parser.add_argument(
        "--procs",
        type=int,
        default=config.PROCESSES,
        help=f"Jumlah worker proses untuk fase CPU (default: {config.PROCESSES})",
    )
    parser.add_argument(
        "--data",
        type=int,
        default=config.DATA_COUNT,
        help=f"Jumlah file teks yang dianalisis (default: {config.DATA_COUNT})",
    )
    parser.add_argument(
        "--mode",
        choices=["serial", "hybrid"],
        default="hybrid",
        help="Mode eksekusi: serial atau hybrid (default: hybrid)",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Paksa jalankan serial ulang dan validasi integritas terhadap hybrid",
    )

    args = parser.parse_args()

    # Dapatkan file teks deterministik sesuai manifest.csv
    file_paths = get_file_list(args.data)

    if args.mode == "serial":
        res = run_serial(file_paths)
        t_total = res["phase_times"]["total"]
        speedup = 1.00
        efficiency = 100.0
        val_status = "VALID (Baseline Serial)"
        baseline_source_note = ""
    else:
        # Mode Hybrid
        # Dapatkan baseline serial untuk penghitungan Speedup, Efisiensi, dan Validasi (Single source of truth)
        serial_baseline, measured_now, mtime_str = get_baseline_for_data(
            args.data, file_paths, force_recompute=args.validate
        )
        res = run_hybrid(file_paths, args.threads, args.procs)
        t_total = res["phase_times"]["total"]

        # Validasi integritas
        is_valid, val_msg = validate_results(serial_baseline, res)
        if not is_valid:
            print(val_msg, file=sys.stderr)
            sys.exit(1)
        val_status = "VALID (100% cocok dengan serial baseline)"
        if measured_now:
            val_status += " (baseline measured now)"

        t_serial = serial_baseline.get("mean")
        if t_serial is None:
            t_serial = serial_baseline.get("phase_times", {}).get("total", 0.0)
        speedup = t_serial / t_total if t_total > 0 else 0.0
        efficiency = (speedup / args.procs) * 100.0 if args.procs > 0 else 0.0
        if measured_now:
            baseline_source_note = f"\nBaseline Serial   : {t_serial:.2f} s (baseline measured now)"
        else:
            baseline_source_note = f"\nBaseline Serial   : {t_serial:.2f} s (dari results.json, diperbarui: {mtime_str})"

    throughput = res["throughput"]
    mb_processed = res["total_bytes"] / (1024 * 1024)
    mb_per_sec = mb_processed / t_total if t_total > 0 else 0.0

    # Output Terminal PERSIS sesuai format ketentuan soal UTS
    print(f"Hybrid Project by: {config.NAMA} ({config.NIM})")
    print(f"Threads: {args.threads} | Processes: {args.procs} | Data: {args.data}")
    print(f"Total Time: {t_total:.2f} s | Speedup: {speedup:.1f} | Efficiency: {efficiency:.1f}%")
    print()
    print(f"Throughput        : {throughput:.2f} file/detik ({mb_per_sec:.2f} MB/s)")
    print(f"Status Validasi   : {val_status}")
    if baseline_source_note:
        print(f"{baseline_source_note.strip()}")
    print()
    print("Contoh Hasil Analisis:")
    print(f"- Total File      : {res['total_files']:,} file")
    print(f"- Total Ukuran    : {mb_processed:.2f} MB")
    print(f"- Total Karakter  : {res['total_chars']:,}")
    print(f"- Total Kata      : {res['total_words']:,}")
    print(f"- Total Vokal     : {res['total_vowels']:,}")
    print(f"- Total Angka     : {res['total_digits']:,}")
    print(f"- Total Simbol    : {res['total_symbols']:,}")
    print(f"- Total Kalimat   : {res['total_sentences']:,}")
    print()
    print("Top-10 Kata Terbanyak:")
    for rank, (word, count) in enumerate(res["top_10_words"], start=1):
        print(f"  {rank:>2}. {word:<12} : {count:,} kemunculan")
    print()
    print("Fase Waktu (s):")
    print(
        f"  I/O (Baca)     : {res['phase_times']['io']:.4f} s "
        f"({(res['phase_times']['io']/t_total)*100:.1f}%)"
    )
    print(
        f"  CPU (Analisis) : {res['phase_times']['cpu']:.4f} s "
        f"({(res['phase_times']['cpu']/t_total)*100:.1f}%)"
    )
    print(
        f"  Reduce         : {res['phase_times']['reduce']:.4f} s "
        f"({(res['phase_times']['reduce']/t_total)*100:.1f}%)"
    )
    print()
    print("Beban per Worker (Process):")
    for ws in res["worker_stats"]:
        pct = (ws['worker_time'] / res['phase_times']['cpu']) * 100 if res['phase_times']['cpu'] > 0 else 0
        print(
            f"  PID {ws['pid']:<6} : {ws['file_count']:>4} file | "
            f"{ws['total_bytes']/(1024*1024):>6.2f} MB | "
            f"Waktu: {ws['worker_time']:>6.2f} s ({pct:>5.1f}%)"
        )
    print()
    print('"Think Parallel. Work Distributed. Create Hybrid Innovation".')


if __name__ == "__main__":
    main()
