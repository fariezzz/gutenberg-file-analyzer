import os
import csv
import time
import random
import urllib.request
import urllib.error

# PARAMETER
NIM = 247006111146
TARGET = 146 * 10          # 3 digit terakhir NIM x 10 = 1460
MIN_BYTES = 10_000         # file lebih kecil dari ini dianggap gagal
DELAY = 0.7
TIMEOUT = 20
MAX_RETRY = 2

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data_wc_real")
CATALOG = os.path.join(BASE_DIR, "pg_catalog.csv")
MANIFEST = os.path.join(BASE_DIR, "manifest.csv")
CATALOG_URL = "https://www.gutenberg.org/cache/epub/feeds/pg_catalog.csv"

os.makedirs(DATA_DIR, exist_ok=True)
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) UTS-Komputasi-Paralel"}


def http_get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read()


def load_catalog():
    """Unduh katalog sekali saja, lalu pakai salinan lokal."""
    if not os.path.exists(CATALOG):
        print("Mengunduh katalog Gutenberg...")
        with open(CATALOG, "wb") as f:
            f.write(http_get(CATALOG_URL))
    ids = []
    with open(CATALOG, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("Type") == "Text" and row.get("Language") == "en":
                try:
                    ids.append(int(row["Text#"]))
                except (ValueError, KeyError):
                    pass
    return sorted(set(ids))


def download(gid, dest):
    url = f"https://www.gutenberg.org/cache/epub/{gid}/pg{gid}.txt"
    for attempt in range(1, MAX_RETRY + 1):
        try:
            content = http_get(url)
            if len(content) < MIN_BYTES:
                return False, "terlalu kecil"
            with open(dest, "wb") as f:
                f.write(content)
            return True, len(content)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return False, "404"
            time.sleep(2 * attempt)
        except Exception as e:
            if attempt == MAX_RETRY:
                return False, str(e)
            time.sleep(2 * attempt)
    return False, "gagal"


def main():
    all_ids = load_catalog()
    print(f"Katalog: {len(all_ids)} buku teks berbahasa Inggris")

    # Urutan kandidat ditentukan oleh seed NIM -> reproducible
    rng = random.Random(NIM)
    candidates = all_ids[:]
    rng.shuffle(candidates)

    selected = []      # (gid, filename)
    gagal = 0
    total_bytes = 0

    for gid in candidates:
        if len(selected) >= TARGET:
            break
        fname = f"pg{gid}.txt"
        dest = os.path.join(DATA_DIR, fname)

        if os.path.exists(dest) and os.path.getsize(dest) >= MIN_BYTES:
            selected.append((gid, fname))
            total_bytes += os.path.getsize(dest)
            continue

        ok, info = download(gid, dest)
        if ok:
            selected.append((gid, fname))
            total_bytes += info
            print(f"[{len(selected)}/{TARGET}] OK  {fname} ({info:,} bytes)")
            time.sleep(DELAY)
        else:
            gagal += 1
            print(f"      skip {gid}: {info}")
            time.sleep(0.2)

    with open(MANIFEST, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["no", "gutenberg_id", "filename"])
        for i, (gid, fname) in enumerate(selected, start=1):
            w.writerow([i, gid, fname])

    print(f"\nSelesai: {len(selected)}/{TARGET} file, ~{total_bytes/1e6:.0f} MB, "
          f"{gagal} ID dilewati")
    print(f"Folder   : {DATA_DIR}")
    print(f"Manifest : {MANIFEST}")
    if len(selected) < TARGET:
        print("Belum mencapai target. Jalankan ulang, script akan melanjutkan.")


if __name__ == "__main__":
    main()