"""
Server Web Visualisasi Dashboard Lokal (Tahap 4)
Proyek UTS Komputasi Paralel dan Terdistribusi
Melayani dashboard visualisasi berbasis Chart.js secara lokal tanpa dependensi eksternal.
Akses URL: http://localhost:8000
"""

import os
import sys
import json
import mimetypes
import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler

import config


class DashboardRequestHandler(BaseHTTPRequestHandler):
    """Handler HTTP untuk menyajikan berkas statis dashboard dan data hasil benchmark."""

    def log_message(self, format, *args):
        # Format log ringkas ke terminal
        sys.stdout.write(f"[{self.log_date_time_string()}] {args[0]} - {args[1]}\n")

    def end_headers(self):
        # Tambahkan header CORS dan no-cache untuk data dinamis
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def do_HEAD(self):
        self.do_GET(is_head=True)

    def do_GET(self, is_head=False):
        url_path = self.path.split("?")[0]

        # 1. Routing API Data Benchmark
        if url_path in ["/results.json", "/results/results.json", "/api/results"]:
            if not os.path.exists(config.RESULTS_JSON):
                self.send_response(404)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                err_payload = json.dumps({
                    "error": "results.json belum tersedia. Jalankan 'python benchmark.py' terlebih dahulu."
                })
                self.wfile.write(err_payload.encode("utf-8"))
                return

            try:
                with open(config.RESULTS_JSON, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                if not is_head:
                    self.wfile.write(content)
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                if not is_head:
                    self.wfile.write(str(e).encode("utf-8"))
            return

        # 2. Routing CSV Hasil Benchmark
        if url_path in ["/results.csv", "/results/results.csv"]:
            if not os.path.exists(config.RESULTS_CSV):
                self.send_response(404)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                if not is_head:
                    self.wfile.write("results.csv belum tersedia.".encode("utf-8"))
                return

            try:
                with open(config.RESULTS_CSV, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/csv; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                if not is_head:
                    self.wfile.write(content)
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                if not is_head:
                    self.wfile.write(str(e).encode("utf-8"))
            return

        # 3. Routing Grafik Gambar PNG Hasil Matplotlib
        if url_path.startswith("/charts/") or url_path.startswith("/results/charts/"):
            fname = os.path.basename(url_path)
            chart_file = os.path.join(config.CHARTS_DIR, fname)
            if os.path.exists(chart_file) and os.path.isfile(chart_file):
                with open(chart_file, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                if not is_head:
                    self.wfile.write(content)
                return

        # 3. Routing Berkas Statis Dashboard (index.html, style.css, app.js, chart.min.js)
        if url_path == "/" or url_path == "":
            rel_file = "index.html"
        else:
            rel_file = url_path.lstrip("/")

        target_file = os.path.join(config.DASHBOARD_DIR, rel_file)

        if not os.path.exists(target_file) or not os.path.isfile(target_file):
            self.send_response(404)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            if not is_head:
                self.wfile.write(f"Berkas '{rel_file}' tidak ditemukan.".encode("utf-8"))
            return

        mime_type, _ = mimetypes.guess_type(target_file)
        if not mime_type:
            mime_type = "application/octet-stream"

        try:
            with open(target_file, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", f"{mime_type}; charset=utf-8" if "text" in mime_type or "json" in mime_type or "javascript" in mime_type else mime_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            if not is_head:
                self.wfile.write(content)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            if not is_head:
                self.wfile.write(str(e).encode("utf-8"))


def run_server(port=8000):
    server_address = ("0.0.0.0", port)
    httpd = HTTPServer(server_address, DashboardRequestHandler)
    print("=" * 65)
    print("DASHBOARD VISUALISASI PARALLEL FILE ANALYZER")
    print("UTS Komputasi Paralel dan Terdistribusi")
    print(f"Mahasiswa : {config.NAMA} ({config.NIM})")
    print("=" * 65)
    print(f"Server aktif di : http://localhost:{port}")
    print(f"Folder Web      : {config.DASHBOARD_DIR}")
    print(f"Data Hasil      : {config.RESULTS_JSON}")
    print("Tekan Ctrl+C untuk menghentikan server.")
    print("=" * 65)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[Server dihentikan oleh pengguna]")
        httpd.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Jalankan Server Dashboard Visualisasi UTS")
    parser.add_argument("--port", type=int, default=8000, help="Port HTTP server (default: 8000)")
    args = parser.parse_args()
    run_server(args.port)
