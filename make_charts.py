"""
Modul Pembuatan Grafik Benchmark (Tahap 3)
Proyek UTS Komputasi Paralel dan Terdistribusi
Menghasilkan 5 grafik PNG beresolusi tinggi (300 DPI) untuk laporan UTS:
1. Waktu vs Jumlah Thread (Proses tetap = 3, Data = 1460)
2. Waktu vs Jumlah Process (Thread tetap = 4, Data = 1460)
3. Speedup vs Konfigurasi (Diagram Batang dengan label nilai)
4. Efisiensi per Konfigurasi (dengan garis referensi ideal 100%)
5. Waktu per Fase (Stacked Bar: I/O Baca, CPU Analisis, Reduce)
"""

import os
import sys
import json
import matplotlib

# Gunakan backend non-GUI untuk kestabilan rendering
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import config


def load_results():
    """Memuat data benchmark dari results/results.json."""
    if not os.path.exists(config.RESULTS_JSON):
        raise FileNotFoundError(
            f"File hasil benchmark tidak ditemukan di: {config.RESULTS_JSON}. "
            f"Jalankan benchmark.py terlebih dahulu."
        )
    with open(config.RESULTS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def apply_chart_style():
    """Mengatur gaya visual grafik agar bersih, profesional, dan mudah dibaca."""
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica", "sans-serif"]
    plt.rcParams["axes.edgecolor"] = "#cccccc"
    plt.rcParams["axes.linewidth"] = 0.8
    plt.rcParams["grid.color"] = "#e5e7eb"
    plt.rcParams["grid.linestyle"] = "--"
    plt.rcParams["grid.alpha"] = 0.7


def chart_1_time_vs_threads(configs, output_dir):
    """
    Grafik 1: Waktu vs Jumlah Thread (Proses tetap = 3, Data = 1460).
    Konfigurasi yang diuji: 1T/3P, 2T/3P, 4T/3P (NIM), 8T/3P.
    """
    selected = [c for c in configs if c["procs"] == 3 and c["data"] == 1460]
    selected.sort(key=lambda x: x["threads"])

    threads = [c["threads"] for c in selected]
    times = [c["mean"] for c in selected]
    stds = [c.get("std", 0.0) for c in selected]

    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
    ax.errorbar(
        threads,
        times,
        yerr=stds,
        fmt="o-",
        color="#2563eb",
        ecolor="#93c5fd",
        elinewidth=2,
        capsize=5,
        linewidth=2.5,
        markersize=8,
        label="Waktu Eksekusi Nyata",
    )

    # Sorot konfigurasi NIM (4 Thread)
    nim_idx = threads.index(4)
    ax.plot(
        threads[nim_idx],
        times[nim_idx],
        "o",
        color="#dc2626",
        markersize=12,
        label="Konfigurasi NIM (4 Thread)",
        zorder=5,
    )

    for t, tm in zip(threads, times):
        ax.annotate(
            f"{tm:.2f} s",
            (t, tm),
            textcoords="offset points",
            xytext=(0, 10),
            ha="center",
            fontsize=10,
            fontweight="bold",
            color="#1e293b",
        )

    ax.set_title(
        "Pengaruh Jumlah Thread terhadap Waktu Eksekusi\n(Proses Tetap = 3, Data = 1.460 File)",
        fontsize=13,
        fontweight="bold",
        pad=15,
    )
    ax.set_xlabel("Jumlah Thread (I/O-bound Phase)", fontsize=11, labelpad=10)
    ax.set_ylabel("Waktu Eksekusi Rata-rata (detik)", fontsize=11, labelpad=10)
    ax.set_xticks(threads)
    ax.set_ylim(min(times) - 3, max(times) + 3)
    ax.legend(frameon=True, facecolor="white", edgecolor="#cbd5e1", loc="upper right")
    plt.tight_layout()

    out_path = os.path.join(output_dir, "chart_1_time_vs_threads.png")
    fig.savefig(out_path)
    plt.close(fig)
    print(f"[OK] Disimpan: {out_path}")


def chart_2_time_vs_processes(configs, output_dir):
    """
    Grafik 2: Waktu vs Jumlah Process (Thread tetap = 4, Data = 1460).
    Konfigurasi yang diuji: 4T/1P, 4T/2P, 4T/3P (NIM), 4T/6P.
    """
    selected = [c for c in configs if c["threads"] == 4 and c["data"] == 1460]
    selected.sort(key=lambda x: x["procs"])

    procs = [c["procs"] for c in selected]
    times = [c["mean"] for c in selected]
    stds = [c.get("std", 0.0) for c in selected]

    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
    ax.errorbar(
        procs,
        times,
        yerr=stds,
        fmt="s-",
        color="#059669",
        ecolor="#a7f3d0",
        elinewidth=2,
        capsize=5,
        linewidth=2.5,
        markersize=8,
        label="Waktu Eksekusi Nyata",
    )

    # Sorot konfigurasi NIM (3 Process)
    nim_idx = procs.index(3)
    ax.plot(
        procs[nim_idx],
        times[nim_idx],
        "s",
        color="#dc2626",
        markersize=12,
        label="Konfigurasi NIM (3 Proses)",
        zorder=5,
    )

    for p, tm in zip(procs, times):
        ax.annotate(
            f"{tm:.2f} s",
            (p, tm),
            textcoords="offset points",
            xytext=(0, 10),
            ha="center",
            fontsize=10,
            fontweight="bold",
            color="#1e293b",
        )

    ax.set_title(
        "Pengaruh Jumlah Process terhadap Waktu Eksekusi\n(Thread Tetap = 4, Data = 1.460 File)",
        fontsize=13,
        fontweight="bold",
        pad=15,
    )
    ax.set_xlabel("Jumlah Process (CPU-bound Phase)", fontsize=11, labelpad=10)
    ax.set_ylabel("Waktu Eksekusi Rata-rata (detik)", fontsize=11, labelpad=10)
    ax.set_xticks(procs)
    ax.set_ylim(min(times) - 5, max(times) + 7)
    ax.legend(frameon=True, facecolor="white", edgecolor="#cbd5e1", loc="upper right")
    plt.tight_layout()

    out_path = os.path.join(output_dir, "chart_2_time_vs_processes.png")
    fig.savefig(out_path)
    plt.close(fig)
    print(f"[OK] Disimpan: {out_path}")


def chart_3_speedup_vs_configs(configs, output_dir):
    """
    Grafik 3: Speedup vs Konfigurasi (Diagram Batang dengan label konfigurasi).
    """
    labels = []
    speedups = []
    colors = []

    for c in configs:
        lbl = f"C{c['id']}: {c['threads']}T/{c['procs']}P"
        if c["data"] != 1460:
            lbl += f"\n({c['data']}f)"
        labels.append(lbl)
        speedups.append(c["speedup"])

        # Warna khusus untuk NIM (C5) dan Baseline (C1)
        if c["id"] == 5:
            colors.append("#d97706")  # Amber emas untuk konfigurasi NIM
        elif c["id"] == 1:
            colors.append("#94a3b8")  # Slate abu-abu untuk serial baseline
        elif c["id"] == 8:
            colors.append("#059669")  # Hijau untuk speedup tertinggi
        else:
            colors.append("#3b82f6")  # Biru standar

    fig, ax = plt.subplots(figsize=(11, 5.5), dpi=300)
    bars = ax.bar(labels, speedups, color=colors, width=0.65, edgecolor="#1e293b", linewidth=0.5)

    # Tambahkan garis horizontal referensi baseline = 1.0
    ax.axhline(1.0, color="#64748b", linestyle="--", linewidth=1.2, alpha=0.8, label="Baseline Serial (1.0x)")

    for bar, sp in zip(bars, speedups):
        yval = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            yval + 0.08,
            f"{sp:.2f}x",
            ha="center",
            va="bottom",
            fontsize=9.5,
            fontweight="bold",
            color="#0f172a",
        )

    ax.set_title(
        "Perbandingan Speedup Relatif terhadap Baseline per Konfigurasi",
        fontsize=13,
        fontweight="bold",
        pad=15,
    )
    ax.set_xlabel("Konfigurasi Eksperimen (Thread / Process / Data)", fontsize=11, labelpad=10)
    ax.set_ylabel("Speedup (kali lebih cepat)", fontsize=11, labelpad=10)
    ax.set_ylim(0, max(speedups) + 0.6)

    # Custom legend untuk penanda warna
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#d97706", edgecolor="#1e293b", label="Konfigurasi NIM (4T / 3P, 1460)"),
        Patch(facecolor="#059669", edgecolor="#1e293b", label="Speedup Tertinggi (4T / 6P, 1460)"),
        Patch(facecolor="#3b82f6", edgecolor="#1e293b", label="Konfigurasi Hybrid Lainnya"),
        Patch(facecolor="#94a3b8", edgecolor="#1e293b", label="Serial Baseline (1T / 1P)"),
    ]
    ax.legend(handles=legend_elements, frameon=True, facecolor="white", edgecolor="#cbd5e1", loc="upper left")
    plt.tight_layout()

    out_path = os.path.join(output_dir, "chart_3_speedup_vs_configs.png")
    fig.savefig(out_path)
    plt.close(fig)
    print(f"[OK] Disimpan: {out_path}")


def chart_4_efficiency_vs_configs(configs, output_dir):
    """
    Grafik 4: Efisiensi Komputasi per Konfigurasi dengan Garis Referensi Ideal 100%.
    """
    labels = []
    efficiencies = []
    colors = []

    for c in configs:
        lbl = f"C{c['id']}: {c['threads']}T/{c['procs']}P"
        if c["data"] != 1460:
            lbl += f"\n({c['data']}f)"
        labels.append(lbl)
        efficiencies.append(c["efficiency"])

        if c["id"] == 5:
            colors.append("#d97706")  # Amber untuk NIM
        elif c["id"] == 2:
            colors.append("#8b5cf6")  # Ungu untuk 4T/1P (efisiensi > 100% karena I/O concurrency)
        else:
            colors.append("#38bdf8")

    fig, ax = plt.subplots(figsize=(11, 5.5), dpi=300)
    bars = ax.bar(labels, efficiencies, color=colors, width=0.65, edgecolor="#1e293b", linewidth=0.5)

    # Garis ideal 100% efisiensi linear
    ax.axhline(100.0, color="#ef4444", linestyle="--", linewidth=1.5, alpha=0.9, label="Efisiensi Linear Ideal (100%)")

    for bar, eff in zip(bars, efficiencies):
        yval = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            yval + 2,
            f"{eff:.1f}%",
            ha="center",
            va="bottom",
            fontsize=9.5,
            fontweight="bold",
            color="#0f172a",
        )

    ax.set_title(
        "Efisiensi Komputasi Paralel per Konfigurasi\n[ Efisiensi = (Speedup / Jumlah Proses) x 100% ]",
        fontsize=13,
        fontweight="bold",
        pad=15,
    )
    ax.set_xlabel("Konfigurasi Eksperimen", fontsize=11, labelpad=10)
    ax.set_ylabel("Efisiensi (%)", fontsize=11, labelpad=10)
    ax.set_ylim(0, max(efficiencies) + 15)

    from matplotlib.patches import Patch
    legend_elements = [
        plt.Line2D([0], [0], color="#ef4444", linestyle="--", linewidth=1.5, label="Efisiensi Ideal (100%)"),
        Patch(facecolor="#d97706", edgecolor="#1e293b", label="Konfigurasi NIM"),
        Patch(facecolor="#8b5cf6", edgecolor="#1e293b", label="4T / 1P"),
        Patch(facecolor="#38bdf8", edgecolor="#1e293b", label="Konfigurasi Lainnya"),
    ]
    ax.legend(handles=legend_elements, frameon=True, facecolor="white", edgecolor="#cbd5e1", loc="upper right")
    plt.tight_layout()

    out_path = os.path.join(output_dir, "chart_4_efficiency_vs_configs.png")
    fig.savefig(out_path)
    plt.close(fig)
    print(f"[OK] Disimpan: {out_path}")


def chart_5_phase_breakdown_stacked(configs, output_dir):
    """
    Grafik 5: Waktu per Fase (Stacked: Baca I/O, Analisis CPU, Reduce).
    Menunjukkan secara transparan fase dominan pembentuk bottleneck.
    """
    labels = []
    io_times = []
    cpu_times = []
    reduce_times = []

    for c in configs:
        lbl = f"C{c['id']}: {c['threads']}T/{c['procs']}P"
        if c["data"] != 1460:
            lbl += f"\n({c['data']}f)"
        labels.append(lbl)

        phases = c.get("avg_phase_times", {})
        io_times.append(phases.get("io", 0.0))
        cpu_times.append(phases.get("cpu", 0.0))
        reduce_times.append(phases.get("reduce", 0.0))

    x = np.arange(len(labels))
    width = 0.65

    fig, ax = plt.subplots(figsize=(11, 5.5), dpi=300)

    # Stacked Bars: I/O (Bawah), CPU (Tengah), Reduce (Atas)
    ax.bar(x, io_times, width, label="Fase I/O (Baca & Bersihkan Teks)", color="#3b82f6", edgecolor="#1e293b", linewidth=0.5)
    ax.bar(x, cpu_times, width, bottom=io_times, label="Fase CPU (Analisis Token & Kata)", color="#f59e0b", edgecolor="#1e293b", linewidth=0.5)
    bottom_reduce = np.array(io_times) + np.array(cpu_times)
    ax.bar(x, reduce_times, width, bottom=bottom_reduce, label="Fase Reduce (Agregasi Data)", color="#10b981", edgecolor="#1e293b", linewidth=0.5)

    # Tambahkan total waktu di puncak setiap bar
    for idx, (tot_b, red_val) in enumerate(zip(bottom_reduce, reduce_times)):
        total_time = tot_b + red_val
        ax.text(
            idx,
            total_time + 1.2,
            f"{total_time:.1f}s",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
            color="#0f172a",
        )

    ax.set_title(
        "Dekomposisi Waktu Eksekusi per Fase (Stacked Breakdown)\n[ Analisis Beban I/O vs CPU vs Reducer ]",
        fontsize=13,
        fontweight="bold",
        pad=15,
    )
    ax.set_xlabel("Konfigurasi Eksperimen", fontsize=11, labelpad=10)
    ax.set_ylabel("Waktu Eksekusi (detik)", fontsize=11, labelpad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, max([b + r for b, r in zip(bottom_reduce, reduce_times)]) + 8)
    ax.legend(frameon=True, facecolor="white", edgecolor="#cbd5e1", loc="upper right")
    plt.tight_layout()

    out_path = os.path.join(output_dir, "chart_5_phase_breakdown_stacked.png")
    fig.savefig(out_path)
    plt.close(fig)
    print(f"[OK] Disimpan: {out_path}")


def main():
    print("=" * 60)
    print("MEMBUAT GRAFIK BENCHMARK HASIL EKSPERIMEN (300 DPI)")
    print("=" * 60)

    data = load_results()
    configs = data.get("configs", [])
    if not configs:
        print("[Error] Tidak ada konfigurasi ditemukan di results.json!", file=sys.stderr)
        sys.exit(1)

    os.makedirs(config.CHARTS_DIR, exist_ok=True)
    apply_chart_style()

    chart_1_time_vs_threads(configs, config.CHARTS_DIR)
    chart_2_time_vs_processes(configs, config.CHARTS_DIR)
    chart_3_speedup_vs_configs(configs, config.CHARTS_DIR)
    chart_4_efficiency_vs_configs(configs, config.CHARTS_DIR)
    chart_5_phase_breakdown_stacked(configs, config.CHARTS_DIR)

    print("=" * 60)
    print(f"Semua grafik PNG berhasil dibuat di: {config.CHARTS_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
