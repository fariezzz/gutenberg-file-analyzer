"""
Konfigurasi Terpusat Proyek UTS Komputasi Paralel dan Terdistribusi
Tema: Hybrid Computing for Real-World Simulation and Data Processing
"""

import os
import random

# ==============================================================================
# IDENTITAS & PARAMETER MAHASISWA (NIM: 247006111146)
# ==============================================================================
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

# Inisialisasi seed acak global untuk reproduksibilitas
random.seed(SEED)

# ==============================================================================
# PATH DIREKTORI & FILE
# ==============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data_wc_real")
MANIFEST_PATH = os.path.join(BASE_DIR, "manifest.csv")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
CHARTS_DIR = os.path.join(RESULTS_DIR, "charts")
DASHBOARD_DIR = os.path.join(BASE_DIR, "dashboard")

BASELINES_FILE = os.path.join(RESULTS_DIR, "baselines.json")
RESULTS_CSV = os.path.join(RESULTS_DIR, "results.csv")
RESULTS_JSON = os.path.join(RESULTS_DIR, "results.json")

# Buat direktori output jika belum ada
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(CHARTS_DIR, exist_ok=True)
os.makedirs(DASHBOARD_DIR, exist_ok=True)
