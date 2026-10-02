"""
Modul Benchmark Komparatif (Tahap 2)
Proyek UTS Komputasi Paralel dan Terdistribusi
Menjalankan 10 konfigurasi pengujian dengan 3 pengulangan (cold & warm runs),
mengukur speedup, efisiensi, throughput, dan load balancing antar worker.
Dilengkapi warm-up CPU, stability check per-konfigurasi, dan drift check akhir.
"""

import os
import sys
import time
import json
import csv
import platform
import argparse
import statistics
import subprocess
from datetime import datetime

import psutil

import config
import analyzer

# Daftar 10 konfigurasi sesuai ketentuan UTS
BENCHMARK_CONFIGS = [
    {"id": 1,  "threads": 1, "procs": 1, "data": 1460, "desc": "1T / 1P, 1460 file (Serial Baseline)"},
    {"id": 2,  "threads": 4, "procs": 1, "data": 1460, "desc": "4T / 1P, 1460 file"},
    {"id": 3,  "threads": 1, "procs": 3, "data": 1460, "desc": "1T / 3P, 1460 file"},
    {"id": 4,  "threads": 2, "procs": 3, "data": 1460, "desc": "2T / 3P, 1460 file"},
    {"id": 5,  "threads": 4, "procs": 3, "data": 1460, "desc": "4T / 3P, 1460 file (Konfigurasi NIM)"},
    {"id": 6,  "threads": 8, "procs": 3, "data": 1460, "desc": "8T / 3P, 1460 file"},
    {"id": 7,  "threads": 4, "procs": 2, "data": 1460, "desc": "4T / 2P, 1460 file"},
    {"id": 8,  "threads": 4, "procs": 6, "data": 1460, "desc": "4T / 6P, 1460 file"},
    {"id": 9,  "threads": 4, "procs": 3, "data": 500,  "desc": "4T / 3P, 500 file"},
    {"id": 10, "threads": 4, "procs": 3, "data": 1000, "desc": "4T / 3P, 1000 file"},
]


def get_current_cpu_freq():
    """Membaca frekuensi CPU saat ini dalam MHz untuk deteksi throttling."""
    try:
        f = psutil.cpu_freq()
        return round(f.current, 1) if f and f.current else None
    except Exception:
        return None


def get_machine_specs() -> dict:
    """
    Mendeteksi spesifikasi mesin secara mendalam:
    Model CPU, core fisik & logis, RAM, OS, versi Python, dan jenis penyimpanan (disk).
    """
    cpu_model = platform.processor() or "Unknown CPU"
    disk_model = "Storage Drive"

    # Deteksi nama prosesor yang lebih akurat via PowerShell di lingkungan Windows
    try:
        ps_cmd = 'powershell.exe -NoProfile -Command "(Get-CimInstance Win32_Processor).Name"'
        out = subprocess.check_output(ps_cmd, shell=True, stderr=subprocess.DEVNULL)
        res = out.decode("utf-8", errors="ignore").strip()
        if res:
            cpu_model = res
    except Exception:
        pass

    # Deteksi jenis media penyimpanan
    try:
        disk_cmd = 'powershell.exe -NoProfile -Command "Get-PhysicalDisk | Select-Object -Property FriendlyName, MediaType, BusType | Format-Table -HideTableHeaders"'
        out_disk = subprocess.check_output(disk_cmd, shell=True, stderr=subprocess.DEVNULL)
        d_res = out_disk.decode("utf-8", errors="ignore").strip()
        if d_res:
            disk_model = " ".join(d_res.split())
    except Exception:
        pass

    # Deteksi OS akurat (Windows 11 tetap dilaporkan sebagai versi NT 10.0 oleh platform.system/release)
    os_name = f"{platform.system()} {platform.release()} ({platform.platform()})"
    try:
        os_cmd = 'powershell.exe -NoProfile -Command "(Get-CimInstance Win32_OperatingSystem).Caption"'
        out_os = subprocess.check_output(os_cmd, shell=True, stderr=subprocess.DEVNULL)
        os_res = out_os.decode("utf-8", errors="ignore").strip()
        if os_res:
            build = getattr(sys, "getwindowsversion", lambda: None)()
            build_str = f" (Build {build.build})" if build else ""
            os_name = f"{os_res}{build_str}"
    except Exception:
        try:
            build_num = int(platform.version().split(".")[-1])
            if platform.system() == "Windows" and build_num >= 22000:
                os_name = f"Microsoft Windows 11 (Build {build_num})"
        except Exception:
            pass

    logical_cores = psutil.cpu_count(logical=True) or 1
    physical_cores = psutil.cpu_count(logical=False) or 1
    ram_gb = round(psutil.virtual_memory().total / (1024 ** 3), 2)

    return {
        "cpu_model": cpu_model,
        "physical_cores": physical_cores,
        "logical_cores": logical_cores,
        "ram_gb": ram_gb,
        "os": os_name,
        "python_version": sys.version.split()[0],
        "disk_type": disk_model,
    }


def compute_file_size_histogram(file_paths: list) -> dict:
    """
    Menghitung distribusi histogram ukuran file dalam korpus Gutenberg.
    """
    bins = {
        "< 100 KB": 0,
        "100 KB - 250 KB": 0,
        "250 KB - 500 KB": 0,
        "500 KB - 1 MB": 0,
        "> 1 MB": 0,
    }
    for fp in file_paths:
        try:
            sz_kb = os.path.getsize(fp) / 1024
            if sz_kb < 100:
                bins["< 100 KB"] += 1
            elif sz_kb < 250:
                bins["100 KB - 250 KB"] += 1
            elif sz_kb < 500:
                bins["250 KB - 500 KB"] += 1
            elif sz_kb < 1024:
                bins["500 KB - 1 MB"] += 1
            else:
                bins["> 1 MB"] += 1
        except Exception:
            pass
    return bins


def save_results(data_structure: dict):
    """
    Menyimpan hasil benchmark ke file results.json dan results.csv.
    """
    # 1. Simpan ke results.json
    with open(config.RESULTS_JSON, "w", encoding="utf-8") as f:
        json.dump(data_structure, f, indent=2)

    # 2. Simpan ke results.csv (Sesuai format tabel di naskah soal UTS)
    with open(config.RESULTS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "No",
            "Jumlah Thread",
            "Jumlah Process",
            "Data/Task",
            "Waktu (s)",
            "Speedup",
            "Efisiensi (%)",
        ])
        for c in data_structure.get("configs", []):
            writer.writerow([
                c["id"],
                c["threads"],
                c["procs"],
                c["data"],
                f"{c['mean']:.2f}",
                f"{c['speedup']:.2f}",
                f"{c['efficiency']:.2f}",
            ])


def execute_config_with_stability(nthr: int, nprc: int, file_subset: list, repeats: int = 3, label: str = ""):
    """
    Menjalankan konfigurasi pengujian dengan:
    1. Pencatatan frekuensi CPU sebelum eksekusi.
    2. Stability check: bila variasi antar repetisi (max vs min) > 5%,
       otomatis jalankan ulang konfigurasi (maksimal 2 retry).
    3. Menyimpan run asli yang dibuang ke 'discarded_runs', memilih set
       paling konsisten, dan menandai 'unstable' bila variasi tetap > 5%.
    """
    attempts_data = []

    for attempt in range(3):  # 1 initial + max 2 retries
        freq_before = get_current_cpu_freq()
        if attempt > 0:
            last_diff = attempts_data[-1]["diff_ratio"] * 100
            print(f"  [Stabilitas] Variasi repetisi ({last_diff:.1f}%) > 5.0%. Menjalankan ulang konfigurasi (retry {attempt}/2)...")

        if freq_before:
            print(f"  [Info CPU] Frekuensi sebelum run: {freq_before} MHz")

        runs_total = []
        phase_io_list = []
        phase_cpu_list = []
        phase_red_list = []
        latest_res = None

        for r in range(1, repeats + 1):
            if nthr == 1 and nprc == 1:
                res = analyzer.run_serial(file_subset)
            else:
                res = analyzer.run_hybrid(file_subset, nthr, nprc)

            latest_res = res
            t_tot = res["phase_times"]["total"]
            runs_total.append(round(t_tot, 4))
            phase_io_list.append(res["phase_times"]["io"])
            phase_cpu_list.append(res["phase_times"]["cpu"])
            phase_red_list.append(res["phase_times"]["reduce"])

            kind = "Cold" if r == 1 else f"Warm-{r-1}"
            print(f"  - Ulangan {r} ({kind:<6}): Total={t_tot:.2f} s (I/O={res['phase_times']['io']:.2f}s, CPU={res['phase_times']['cpu']:.2f}s, Reduce={res['phase_times']['reduce']:.2f}s)")

        min_val = min(runs_total)
        max_val = max(runs_total)
        diff_ratio = (max_val - min_val) / min_val if min_val > 0 else 0.0

        attempts_data.append({
            "diff_ratio": diff_ratio,
            "runs": runs_total,
            "phase_io": phase_io_list,
            "phase_cpu": phase_cpu_list,
            "phase_red": phase_red_list,
            "latest_res": latest_res,
            "cpu_freq": freq_before,
        })

        if diff_ratio <= 0.05:
            break

    best = min(attempts_data, key=lambda x: x["diff_ratio"])
    discarded = [att["runs"] for att in attempts_data if att is not best]
    is_unstable = best["diff_ratio"] > 0.05
    if is_unstable and len(attempts_data) > 1:
        print(f"  [PERINGATAN] Variasi repetisi tetap > 5% ({best['diff_ratio']*100:.1f}%) setelah 2 retry. Ditandai 'unstable'.")

    return best, discarded, is_unstable


def run_benchmark(force: bool = False, repeats: int = 3):
    print("=" * 65)
    print(f"BENCHMARK KOMPUTASI HYBRID: {config.NAMA} ({config.NIM})")
    print("=" * 65)

    specs = get_machine_specs()
    print("Spesifikasi Mesin Pengujian:")
    print(f"  CPU         : {specs['cpu_model']}")
    print(f"  Core        : {specs['physical_cores']} Fisik | {specs['logical_cores']} Logis")
    print(f"  RAM         : {specs['ram_gb']} GB")
    print(f"  OS          : {specs['os']}")
    print(f"  Python      : {specs['python_version']}")
    print(f"  Storage     : {specs['disk_type']}")
    print("-" * 65)

    # 0. Warm-up CPU sebelum pengukuran (Hybrid 4T/3P pada 300 file)
    print("[*] Menjalankan warm-up CPU (Hybrid 4T/3P, 300 file) agar clock stabil...")
    warmup_files = analyzer.get_file_list(min(300, config.DATA_COUNT))
    analyzer.run_hybrid(warmup_files, n_threads=4, n_procs=3)
    print("[*] Warm-up selesai, CPU berada pada steady state.\n")

    # Muat struktur data jika sudah ada (dukungan resumability)
    if os.path.exists(config.RESULTS_JSON) and not force:
        try:
            with open(config.RESULTS_JSON, "r", encoding="utf-8") as f:
                saved_data = json.load(f)
            print("[*] Ditemukan data benchmark sebelumnya. Melanjutkan...")
        except Exception:
            saved_data = {}
    else:
        saved_data = {}

    meta = {
        "nama": config.NAMA,
        "nim": config.NIM,
        "seed": config.SEED,
        "params": {
            "threads": config.THREADS,
            "processes": config.PROCESSES,
            "data_count": config.DATA_COUNT,
        },
        "baseline_method": "serial, same code path as hybrid worker, mean of 3 runs",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "repeats": repeats,
    }

    baselines = saved_data.get("baselines", {})
    completed_configs = {c["id"]: c for c in saved_data.get("configs", [])}
    corpus_info = saved_data.get("corpus", {})
    validation_info = saved_data.get("validation", {})
    is_full_run = True

    # 1. Pastikan baseline serial untuk 500, 1000, dan 1460 file tersedia (3 repetisi tiap ukuran)
    needed_baseline_counts = [500, 1000, 1460]
    for count in needed_baseline_counts:
        key = str(count)
        if key not in baselines or force:
            print(f"\n[*] Mengukur baseline serial terpisah untuk {count} file ({repeats} repetisi)...")
            files = analyzer.get_file_list(count)
            best, discarded, is_unstable = execute_config_with_stability(
                nthr=1, nprc=1, file_subset=files, repeats=repeats, label=f"Baseline {count} file"
            )

            b_mean = round(statistics.mean(best["runs"]), 4)
            b_std = round(statistics.stdev(best["runs"]), 4) if len(best["runs"]) > 1 else 0.0
            avg_phases = {
                "io": round(statistics.mean(best["phase_io"]), 4),
                "cpu": round(statistics.mean(best["phase_cpu"]), 4),
                "reduce": round(statistics.mean(best["phase_red"]), 4),
                "total": b_mean,
            }
            baselines[key] = {
                "total_files": count,
                "data_count": count,
                "runs": best["runs"],
                "mean": b_mean,
                "std": b_std,
                "avg_phase_times": avg_phases,
                "total_bytes": best["latest_res"]["total_bytes"],
                "total_chars": best["latest_res"]["total_chars"],
                "total_words": best["latest_res"]["total_words"],
                "total_vowels": best["latest_res"]["total_vowels"],
                "total_digits": best["latest_res"]["total_digits"],
                "total_symbols": best["latest_res"]["total_symbols"],
                "total_sentences": best["latest_res"]["total_sentences"],
                "top_20_words": best["latest_res"]["top_20_words"],
                "worker_stats": best["latest_res"].get("worker_stats", []),
                "cpu_freq_mhz": best["cpu_freq"],
                "stability": "unstable" if is_unstable else "stable",
                "discarded_runs": discarded,
            }
            # Simpan sementara
            temp_struct = {
                "meta": meta,
                "machine": specs,
                "baselines": baselines,
                "configs": [completed_configs[i] for i in sorted(completed_configs.keys())],
                "corpus": corpus_info,
                "validation": validation_info,
            }
            save_results(temp_struct)
        else:
            is_full_run = False

    # 2. Ambil informasi korpus lengkap dari baseline 1460
    base_1460 = baselines["1460"]
    all_files_1460 = analyzer.get_file_list(1460)
    if not corpus_info or force:
        corpus_info = {
            "total_files": 1460,
            "total_bytes": base_1460["total_bytes"],
            "total_size_mb": round(base_1460["total_bytes"] / (1024 * 1024), 2),
            "total_chars": base_1460["total_chars"],
            "total_words": base_1460["total_words"],
            "total_vowels": base_1460["total_vowels"],
            "total_digits": base_1460["total_digits"],
            "total_symbols": base_1460["total_symbols"],
            "total_sentences": base_1460["total_sentences"],
            "top_words_20": [
                {"word": w, "count": c} for w, c in base_1460["top_20_words"]
            ],
            "file_size_histogram": compute_file_size_histogram(all_files_1460),
        }

    # Konfigurasi 1 adalah baseline serial 1460 file (1T / 1P)
    # SINGLE SOURCE OF TRUTH: Menggunakan angka yang SAMA PERSIS dengan base_1460 (tanpa pengukuran kedua)
    if 1 not in completed_configs or force:
        mean_1 = base_1460["mean"]
        std_1 = base_1460["std"]
        runs_1 = base_1460["runs"]
        cold_1 = runs_1[0]
        warm_1 = round(statistics.mean(runs_1[1:]), 4) if len(runs_1) > 1 else cold_1
        tp_1 = round(1460 / mean_1, 2)

        completed_configs[1] = {
            "id": 1,
            "threads": 1,
            "procs": 1,
            "data": 1460,
            "desc": BENCHMARK_CONFIGS[0]["desc"],
            "runs": runs_1,
            "mean": mean_1,
            "std": std_1,
            "cold": cold_1,
            "warm": warm_1,
            "speedup": 1.00,
            "efficiency": 100.00,
            "throughput": tp_1,
            "avg_phase_times": base_1460.get("avg_phase_times", {}),
            "worker_stats": base_1460.get("worker_stats", []),
            "cpu_freq_mhz": base_1460.get("cpu_freq_mhz"),
            "stability": base_1460.get("stability", "stable"),
            "discarded_runs": base_1460.get("discarded_runs", []),
        }
        validation_info["config_1"] = {
            "valid": True,
            "message": "VALID (100% cocok dengan serial baseline)",
        }
        temp_struct = {
            "meta": meta,
            "machine": specs,
            "baselines": baselines,
            "configs": [completed_configs[i] for i in sorted(completed_configs.keys())],
            "corpus": corpus_info,
            "validation": validation_info,
        }
        save_results(temp_struct)
        print(f"[Done] Konfigurasi  1: {BENCHMARK_CONFIGS[0]['desc']} -> Rata-rata: {mean_1:.2f} s | Speedup: 1.00x | Efisiensi: 100.00%")
    else:
        is_full_run = False

    # 3. Jalankan Konfigurasi Benchmark Lainnya
    print("-" * 65)
    print("Memulai Eksekusi Konfigurasi Benchmark:")
    print("-" * 65)

    for cfg in BENCHMARK_CONFIGS:
        cid = cfg["id"]
        if cid == 1:
            continue
        nthr = cfg["threads"]
        nprc = cfg["procs"]
        ndata = cfg["data"]
        cdesc = cfg["desc"]

        if cid in completed_configs and not force:
            c = completed_configs[cid]
            print(f"[Lewati] Konfigurasi {cid:2d}: {cdesc} -> Rata-rata: {c['mean']:.2f} s | Speedup: {c['speedup']:.2f}x")
            is_full_run = False
            continue

        if nthr > specs["logical_cores"] or nprc > specs["logical_cores"]:
            print(f"  [PERINGATAN] Konfigurasi {cid} berpotensi oversubscription: Thread={nthr}, Procs={nprc} > Core Logis={specs['logical_cores']}")

        print(f"\n[Run {cid:2d}/10] {cdesc}")
        file_subset = analyzer.get_file_list(ndata)

        best, discarded, is_unstable = execute_config_with_stability(
            nthr=nthr, nprc=nprc, file_subset=file_subset, repeats=repeats, label=f"Config {cid}"
        )

        mean_time = round(statistics.mean(best["runs"]), 4)
        std_time = round(statistics.stdev(best["runs"]), 4) if len(best["runs"]) > 1 else 0.0
        cold_time = best["runs"][0]
        warm_time = round(statistics.mean(best["runs"][1:]), 4) if len(best["runs"]) > 1 else cold_time

        base_time = baselines[str(ndata)]["mean"]
        if nthr == 1 and nprc == 1:
            speedup = 1.00
            efficiency = 100.00
        else:
            speedup = round(base_time / mean_time, 2) if mean_time > 0 else 0.0
            efficiency = round((speedup / nprc) * 100.0, 2) if nprc > 0 else 0.0

        throughput = round(ndata / mean_time, 2) if mean_time > 0 else 0.0

        avg_phases = {
            "io": round(statistics.mean(best["phase_io"]), 4),
            "cpu": round(statistics.mean(best["phase_cpu"]), 4),
            "reduce": round(statistics.mean(best["phase_red"]), 4),
            "total": mean_time,
        }

        # Validasi terhadap baseline korpus
        base_ref = baselines[str(ndata)]
        is_valid, v_msg = analyzer.validate_results(base_ref, best["latest_res"])
        validation_info[f"config_{cid}"] = {
            "valid": is_valid,
            "message": v_msg,
        }

        config_entry = {
            "id": cid,
            "threads": nthr,
            "procs": nprc,
            "data": ndata,
            "desc": cdesc,
            "runs": best["runs"],
            "mean": mean_time,
            "std": std_time,
            "cold": cold_time,
            "warm": warm_time,
            "speedup": speedup,
            "efficiency": efficiency,
            "throughput": throughput,
            "avg_phase_times": avg_phases,
            "worker_stats": best["latest_res"].get("worker_stats", []),
            "cpu_freq_mhz": best["cpu_freq"],
            "stability": "unstable" if is_unstable else "stable",
            "discarded_runs": discarded,
        }

        completed_configs[cid] = config_entry

        # Simpan progres terkini ke disk
        all_configs_sorted = [completed_configs[i] for i in sorted(completed_configs.keys())]
        full_data = {
            "meta": meta,
            "machine": specs,
            "baselines": baselines,
            "configs": all_configs_sorted,
            "corpus": corpus_info,
            "validation": validation_info,
        }
        save_results(full_data)

        print(f"  => Rata-rata: {mean_time:.2f} s | Speedup: {speedup:.2f}x | Efisiensi: {efficiency:.1f}% | Throughput: {throughput:.2f} f/s")

    # 4. Drift Check di akhir pengujian (hanya jika full run / bukan partial resume)
    if is_full_run:
        print("\n" + "=" * 65)
        print("[*] Melakukan drift check akhir (Baseline serial 500 file, 3 repetisi)...")
        files_500 = analyzer.get_file_list(500)
        end_runs = []
        for r in range(1, repeats + 1):
            t0 = time.perf_counter()
            analyzer.run_serial(files_500)
            dur = time.perf_counter() - t0
            end_runs.append(round(dur, 4))
        end_500_mean = round(statistics.mean(end_runs), 4)
        start_500_mean = baselines["500"]["mean"]
        drift_pct = round(((end_500_mean - start_500_mean) / start_500_mean) * 100, 2)

        meta["drift_check"] = {
            "start_mean": start_500_mean,
            "end_mean": end_500_mean,
            "drift_percent": drift_pct,
            "end_runs": end_runs,
        }
        all_configs_sorted = [completed_configs[i] for i in sorted(completed_configs.keys())]
        full_data = {
            "meta": meta,
            "machine": specs,
            "baselines": baselines,
            "configs": all_configs_sorted,
            "corpus": corpus_info,
            "validation": validation_info,
        }
        save_results(full_data)

        print(f"Drift check: start {start_500_mean:.2f} s vs end {end_500_mean:.2f} s ({drift_pct:+.1f}%)")
        if abs(drift_pct) > 5.0:
            print(f"[PERINGATAN] |drift| > 5% ({abs(drift_pct):.1f}%). Kondisi clock CPU / thermal throttling bergeser selama pengujian!")
        else:
            print("[✓] Kondisi mesin stabil selama pengujian (|drift| <= 5%).")

    print("\n" + "=" * 65)
    print("SEMUA BENCHMARK SELESAI DISIMPAN!")
    print(f"File Hasil: {config.RESULTS_CSV}")
    print(f"            {config.RESULTS_JSON}")
    print("=" * 65)


def main():
    parser = argparse.ArgumentParser(description="Jalankan Benchmark UTS Paralel")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Paksa eksekusi ulang seluruh benchmark dari awal",
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=3,
        help="Jumlah pengulangan tiap konfigurasi (default: 3)",
    )
    args = parser.parse_args()

    run_benchmark(force=args.force, repeats=args.repeats)


if __name__ == "__main__":
    main()
