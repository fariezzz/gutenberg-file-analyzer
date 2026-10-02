"""
Script perbaikan perutean panah dan layout diagram arsitektur.
Memperbaiki:
1. Jalur panah Thread ke Batching menggunakan bus vertikal rapi (tidak memutar semrawut).
2. Spacing dan posisi judul Fase 3 agar tidak tertabrak panah diagonal Worker 1.
3. Posisi teks Adaptive Batch Partitioning yang terisolasi rapi di dalam batas kontainernya.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

def render_polished_diagram(output_path="arsitektur_hybrid.png"):
    fig = plt.figure(figsize=(14, 11), dpi=300)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor("#020617")
    ax.set_xlim(0, 1100)
    ax.set_ylim(840, 0)  # Invert Y so 0 is top
    ax.axis("off")

    # Grid background
    for x in range(0, 1100, 40):
        ax.axvline(x, color="#1e293b", linewidth=0.4, alpha=0.5)
    for y in range(0, 840, 40):
        ax.axhline(y, color="#1e293b", linewidth=0.4, alpha=0.5)

    # Title & Subtitle
    ax.plot(48, 38, "o", color="#38bdf8", markersize=8)
    ax.text(64, 40, "ARSITEKTUR HYBRID COMPUTING — PARALLEL FILE ANALYZER", 
            fontfamily="monospace", fontsize=14, fontweight="bold", color="#f8fafc", va="center")
    ax.text(64, 60, "Pemisahan Task-Parallel I/O (ThreadPool) dan CPU-Bound Analysis (ProcessPool) dengan Adaptive Batching", 
            fontfamily="monospace", fontsize=9.5, color="#94a3b8", va="center")

    # Helper: draw fancy box
    def draw_box(x, y, w, h, title, desc="", fill_color="#0f172a", border_color="#334155", title_color="#f1f5f9", rx=6):
        box = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={rx}",
                             linewidth=1.2, edgecolor=border_color, facecolor=fill_color, zorder=3)
        ax.add_patch(box)
        if title and desc:
            ax.text(x + 12, y + 18, title, fontfamily="monospace", fontsize=9.5, fontweight="bold", color=title_color, va="center", zorder=4)
            ax.text(x + 12, y + 36, desc, fontfamily="monospace", fontsize=8, color="#94a3b8", va="center", zorder=4)
        elif title:
            ax.text(x + 10, y + h/2, title, fontfamily="monospace", fontsize=8.5, fontweight="bold", color=title_color, va="center", zorder=4)

    # Helper: draw arrow
    def draw_arrow(x1, y1, x2, y2, color="#38bdf8", width=1.4):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=width, mutation_scale=11), zorder=2)

    # ================= REGIONS =================
    # Storage Region
    r_storage = FancyBboxPatch((40, 80), 265, 140, boxstyle="round,pad=0,rounding_size=8",
                               linewidth=1, edgecolor="#334155", linestyle="--", facecolor="#0f172a", alpha=0.6, zorder=1)
    ax.add_patch(r_storage)
    ax.text(55, 100, "PENYIMPANAN DATA LOKAL", fontfamily="monospace", fontsize=9.5, fontweight="bold", color="#94a3b8", zorder=2)

    # Phase 1: I/O Region
    r_io = FancyBboxPatch((325, 80), 735, 140, boxstyle="round,pad=0,rounding_size=8",
                          linewidth=1.2, edgecolor="#0e7490", facecolor="#083344", alpha=0.25, zorder=1)
    ax.add_patch(r_io)
    ax.text(340, 100, "FASE 1: I/O-BOUND READ & CLEANING (THREAD POOL)", fontfamily="monospace", fontsize=9.5, fontweight="bold", color="#22d3ee", zorder=2)
    # Badge GIL
    b_gil = FancyBboxPatch((900, 90), 145, 18, boxstyle="round,pad=0,rounding_size=3",
                           linewidth=0.8, edgecolor="#0891b2", facecolor="#083344", zorder=3)
    ax.add_patch(b_gil)
    ax.text(972, 99, "GIL RELEASED DURING I/O", fontfamily="monospace", fontsize=7.5, fontweight="bold", color="#38bdf8", ha="center", va="center", zorder=4)

    # Adaptive Batching Region (Spaced out nicely between Phase 1 and Phase 2)
    r_batch = FancyBboxPatch((340, 240), 420, 85, boxstyle="round,pad=0,rounding_size=8",
                             linewidth=1, edgecolor="#38bdf8", linestyle=":", facecolor="#0f172a", alpha=0.5, zorder=1)
    ax.add_patch(r_batch)
    ax.text(355, 258, "ADAPTIVE BATCH PARTITIONING", fontfamily="monospace", fontsize=9, fontweight="bold", color="#38bdf8", zorder=2)

    # Phase 2: CPU Region
    r_cpu = FancyBboxPatch((40, 335), 1020, 230, boxstyle="round,pad=0,rounding_size=8",
                           linewidth=1.2, edgecolor="#059669", facecolor="#064e3b", alpha=0.2, zorder=1)
    ax.add_patch(r_cpu)
    ax.text(55, 355, "FASE 2: CPU-BOUND STATISTICAL ANALYSIS (PROCESS POOL)", fontfamily="monospace", fontsize=9.5, fontweight="bold", color="#34d399", zorder=2)
    # Badge BYPASS GIL
    b_core = FancyBboxPatch((865, 345), 180, 18, boxstyle="round,pad=0,rounding_size=3",
                            linewidth=0.8, edgecolor="#10b981", facecolor="#064e3b", zorder=3)
    ax.add_patch(b_core)
    ax.text(955, 354, "BYPASS GIL (INDEPENDENT CORES)", fontfamily="monospace", fontsize=7.5, fontweight="bold", color="#6ee7b7", ha="center", va="center", zorder=4)

    # Phase 3: Reduce Region (Shifted down so title is never overlapped)
    r_red = FancyBboxPatch((40, 595), 1020, 195, boxstyle="round,pad=0,rounding_size=8",
                           linewidth=1.2, edgecolor="#7c3aed", facecolor="#4c1d95", alpha=0.2, zorder=1)
    ax.add_patch(r_red)
    ax.text(55, 615, "FASE 3: AGREGASI, VALIDASI & VISUALISASI (MAIN PROCESS)", fontfamily="monospace", fontsize=9.5, fontweight="bold", color="#a78bfa", zorder=2)

    # ================= COMPONENT CARDS =================
    # Storage Cards
    draw_box(55, 115, 235, 42, "1.460 File Teks Gutenberg", "data_wc_real/*.txt (Total: 537.91 MB)", fill_color="#0f172a", border_color="#475569")
    draw_box(55, 165, 235, 42, "manifest.csv (Urutan Deterministik)", "Seed NIM 247006111146 (Reproducible)", fill_color="#0f172a", border_color="#475569")

    # ThreadPool Card
    draw_box(340, 120, 140, 65, "ThreadPoolExecutor", "4 Worker Threads (NIM)", fill_color="#083344", border_color="#22d3ee", title_color="#22d3ee")

    # 4 Threads Cards
    for i in range(1, 5):
        draw_box(525, 78 + i*24, 340, 20, f"Thread-{i}: Read & Strip Boilerplate Header/Footer", fill_color="#083344", border_color="#0891b2", title_color="#bae6fd", rx=4)

    # Adaptive Batching Inner Card (Tinggikan agar muat deskripsi tanpa tertabrak panah keluar)
    # Card dari y=268 s.d. y=318 (h=50), teks di y=284 & y=302
    draw_box(355, 268, 390, 50, "Pengelompokan Batch Teks Bersih", "Batch Size = 15-25 File (Mereduksi Overhead IPC/Pickle)", fill_color="#082f49", border_color="#0284c7", title_color="#7dd3fc")

    # ProcessPool Card (Mulai di y=372)
    draw_box(460, 372, 180, 48, "ProcessPoolExecutor", "3 Worker Processes (NIM)", fill_color="#064e3b", border_color="#34d399", title_color="#34d399")

    # 3 Workers Cards
    def draw_worker(x, title):
        b = FancyBboxPatch((x, 435), 290, 112, boxstyle="round,pad=0,rounding_size=6",
                           linewidth=1.2, edgecolor="#10b981", facecolor="#0f172a", zorder=3)
        ax.add_patch(b)
        ax.text(x + 12, 455, title, fontfamily="monospace", fontsize=9.5, fontweight="bold", color="#f1f5f9", zorder=4)
        ax.text(x + 12, 477, "• Tokenisasi Regex Kata (\\b[a-zA-Z]+\\b)", fontfamily="monospace", fontsize=8, color="#cbd5e1", zorder=4)
        ax.text(x + 12, 497, "• Hitung Vokal, Angka, Simbol, Kalimat", fontfamily="monospace", fontsize=8, color="#cbd5e1", zorder=4)
        ax.text(x + 12, 517, "• Word Frequency: collections.Counter()", fontfamily="monospace", fontsize=8, color="#cbd5e1", zorder=4)
        ax.text(x + 12, 535, "• Catat Durasi & PID Beban Kerja", fontfamily="monospace", fontsize=8, color="#6ee7b7", zorder=4)

    draw_worker(60, "Worker Process 1 (Core Fisik 1)")
    draw_worker(405, "Worker Process 2 (Core Fisik 2)")
    draw_worker(750, "Worker Process 3 (Core Fisik 3)")

    # Reducer Card (Main Process)
    draw_box(410, 635, 280, 62, "Reducer / Aggregator Utama", "Merge Counter & Ringkasan Metrik (Validasi 100%)", fill_color="#2e1065", border_color="#a78bfa", title_color="#c084fc")

    # Output Cards
    draw_box(60, 725, 260, 46, "Output Terminal Terformat", "Speedup, Efisiensi, Throughput, Top-10 Kata", fill_color="#0f172a", border_color="#64748b")
    draw_box(420, 725, 260, 46, "results.json & results.csv", "10 Konfigurasi x 3 Repetisi Nyata", fill_color="#0f172a", border_color="#64748b")
    draw_box(780, 725, 260, 46, "Dashboard Visualisasi Web", "Chart.js Lokal (http://localhost:8000)", fill_color="#0f172a", border_color="#64748b")

    # Footer
    ax.text(40, 815, "Muhammad Fariez Riziq Ilham · NIM 247006111146 · Teknik Informatika Universitas Siliwangi",
            fontfamily="monospace", fontsize=9, color="#64748b", va="center")

    # ================= POLISHED ARROWS =================
    # 1. Storage to ThreadPool
    draw_arrow(290, 145, 338, 145, color="#22d3ee")

    # 2. ThreadPool to 4 Threads (Fan-out)
    for i in range(1, 5):
        draw_arrow(480, 145, 523, 78 + i*24 + 10, color="#22d3ee", width=1.1)

    # 3. Clean Thread Collection Bus into Batching
    # Vertical Collector Bus at x=885
    ax.plot([865, 885], [102, 102], color="#0ea5e9", lw=1.2, zorder=2)
    ax.plot([865, 885], [126, 126], color="#0ea5e9", lw=1.2, zorder=2)
    ax.plot([865, 885], [150, 150], color="#0ea5e9", lw=1.2, zorder=2)
    ax.plot([865, 885], [174, 174], color="#0ea5e9", lw=1.2, zorder=2)
    # Downward collector line into batch box (y=293 adalah garis tengah vertikal card batch)
    ax.plot([885, 885, 747], [102, 293, 293], color="#0ea5e9", lw=1.3, zorder=2)
    draw_arrow(760, 293, 747, 293, color="#0ea5e9", width=1.3)

    # 4. Batching to ProcessPoolExecutor (Mulai dari batas bawah box y=320 menuju puncak ProcessPool y=370)
    draw_arrow(550, 320, 550, 370, color="#34d399", width=1.5)

    # 5. ProcessPool to 3 Worker Processes (Fan-out)
    draw_arrow(460, 392, 205, 433, color="#34d399", width=1.2)
    draw_arrow(550, 416, 550, 433, color="#34d399", width=1.2)
    draw_arrow(640, 392, 895, 433, color="#34d399", width=1.2)

    # 6. Workers down to Reducer (Routing cleanly below title area)
    # Worker 1: down then right to left of Reducer
    ax.plot([205, 205, 408], [547, 655, 655], color="#a78bfa", lw=1.2, zorder=2)
    draw_arrow(390, 655, 408, 655, color="#a78bfa", width=1.2)

    # Worker 2: straight down
    draw_arrow(550, 547, 550, 633, color="#a78bfa", width=1.2)

    # Worker 3: down then left to right of Reducer
    ax.plot([895, 895, 692], [547, 655, 655], color="#a78bfa", lw=1.2, zorder=2)
    draw_arrow(710, 655, 692, 655, color="#a78bfa", width=1.2)

    # 7. Reducer to Outputs
    draw_arrow(430, 697, 190, 723, color="#94a3b8", width=1.2)
    draw_arrow(550, 697, 550, 723, color="#94a3b8", width=1.2)
    draw_arrow(670, 697, 910, 723, color="#94a3b8", width=1.2)

    plt.savefig(output_path, facecolor="#020617", edgecolor="none", bbox_inches="tight")
    plt.close()
    print(f"Diagram arsitektur rapi berhasil disimpan ke: {output_path}")

if __name__ == "__main__":
    render_polished_diagram("arsitektur_hybrid.png")
