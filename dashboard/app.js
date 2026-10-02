/**
 * app.js - Parallel File Analyzer Dashboard
 * Semua data bersumber dari /results.json
 */

document.addEventListener("DOMContentLoaded", () => {
  let benchmarkData = null;
  let chartInstances = {};
  let sortKey = "id";
  let sortAsc = true;

  initTheme();
  initChartDownloads();
  loadData();

  async function loadData() {
    const alert = document.getElementById("data-alert");
    try {
      const res = await fetch("/results.json");
      if (!res.ok) throw new Error(res.status);
      benchmarkData = await res.json();
      if (alert) alert.classList.add("hidden");
      render(benchmarkData);
    } catch (e) {
      console.warn("Gagal memuat results.json:", e);
      if (alert) alert.classList.remove("hidden");
    }
  }

  function render(data) {
    fillSummary(data);
    fillSpecs(data.machine);
    fillTable(data.configs);
    bindSort(data.configs);
    drawCharts(data);
    fillCorpusAndWorkers(data);
  }

  // -- ringkasan metrik --
  function fillSummary(data) {
    const cfg = (data.configs || []).find(c => c.id === 5) || {};
    const base = data.baselines && data.baselines["1460"] ? data.baselines["1460"] : {};

    setText("kpi-nim-threads", cfg.threads || 4);
    setText("kpi-nim-procs", cfg.procs || 3);
    setText("kpi-nim-data", (cfg.data || 1460).toLocaleString("id-ID"));
    setText("kpi-nim-time", cfg.mean ? cfg.mean.toFixed(2) + " s" : "—");
    setText("kpi-nim-baseline", base.mean ? "Baseline 1T/1P: " + base.mean.toFixed(2) + " s" : "—");
    setText("kpi-nim-speedup", cfg.speedup ? cfg.speedup.toFixed(2) + "x" : "—");
    setText("kpi-nim-efficiency", cfg.efficiency ? cfg.efficiency.toFixed(1) + "%" : "—");
    setText("kpi-throughput", cfg.throughput ? cfg.throughput.toFixed(1) + " file/s" : "—");

    const mbEl = document.getElementById("kpi-throughput-mb");
    if (mbEl && data.corpus && data.corpus.total_size_mb && cfg.mean) {
      mbEl.textContent = (data.corpus.total_size_mb / cfg.mean).toFixed(2) + " MB/s";
    }
  }

  // -- spesifikasi sistem --
  function fillSpecs(m) {
    if (!m) return;
    setText("spec-cpu", m.cpu_model || "—");
    setText("spec-cores", m.physical_cores + " fisik / " + m.logical_cores + " logis");
    setText("spec-ram", m.ram_gb + " GB");
    setText("spec-os", m.os || "—");
    setText("spec-python", "Python " + (m.python_version || "3.x"));
    setText("spec-disk", m.disk_type || "SSD NVMe");
  }

  // -- tabel hasil --
  function fillTable(configs) {
    const tbody = document.getElementById("benchmark-tbody");
    if (!tbody || !configs) return;
    tbody.innerHTML = "";

    // tercepat hanya dari konfigurasi 1460 file
    const c1460 = configs.filter(c => c.data === 1460);
    const fastest = c1460.length ? c1460.reduce((p, c) => c.mean < p.mean ? c : p, c1460[0]) : null;

    configs.forEach(c => {
      const tr = document.createElement("tr");
      if (c.id === 5) tr.className = "row-nim";
      else if (fastest && c.id === fastest.id) tr.className = "row-fastest";

      tr.innerHTML = `
        <td class="tc font-mono">${c.id}</td>
        <td>${c.desc || (c.threads + "T / " + c.procs + "P, " + c.data + " file")}</td>
        <td class="tc font-mono">${c.threads}</td>
        <td class="tc font-mono">${c.procs}</td>
        <td class="tc font-mono">${c.data}</td>
        <td class="tr font-mono"><strong>${c.mean.toFixed(2)}</strong></td>
        <td class="tr font-mono">${c.std ? c.std.toFixed(2) : "0.00"}</td>
        <td class="tr font-mono"><strong>${c.speedup.toFixed(2)}x</strong></td>
        <td class="tr font-mono">${c.efficiency.toFixed(1)}%</td>
        <td class="tr font-mono">${c.throughput ? c.throughput.toFixed(1) : "—"}</td>
      `;
      tbody.appendChild(tr);
    });
  }

  function bindSort(configs) {
    const ths = document.querySelectorAll("#benchmark-table th.sortable");
    ths.forEach(th => {
      th.addEventListener("click", () => {
        const key = th.dataset.key;
        if (sortKey === key) sortAsc = !sortAsc;
        else { sortKey = key; sortAsc = true; }

        configs.sort((a, b) => {
          let va = a[key], vb = b[key];
          if (typeof va === "string") { va = va.toLowerCase(); vb = vb.toLowerCase(); }
          return va < vb ? (sortAsc ? -1 : 1) : va > vb ? (sortAsc ? 1 : -1) : 0;
        });

        ths.forEach(h => {
          const base = h.textContent.replace(/[▲▼]/g, "").trim();
          h.textContent = h.dataset.key === key ? base + " " + (sortAsc ? "▲" : "▼") : base;
        });

        fillTable(configs);
      });
    });

    const csv = document.getElementById("btn-export-csv");
    if (csv) {
      csv.onclick = () => downloadCsv(configs);
    }
  }

  function downloadCsv(configs) {
    if (!configs || !configs.length) return;
    const headers = [
      "No",
      "Deskripsi",
      "Thread",
      "Process",
      "Data (File)",
      "Waktu (s)",
      "Std Dev (s)",
      "Speedup",
      "Efisiensi (%)",
      "Throughput (f/s)"
    ];
    const sorted = [...configs].sort((a, b) => a.id - b.id);
    const rows = sorted.map(c => [
      c.id,
      `"${(c.desc || "").replace(/"/g, '""')}"`,
      c.threads,
      c.procs,
      c.data,
      c.mean.toFixed(2),
      c.std ? c.std.toFixed(2) : "0.00",
      c.speedup.toFixed(2),
      c.efficiency.toFixed(1),
      c.throughput ? c.throughput.toFixed(1) : "0.0"
    ]);

    const csvContent = "\uFEFF" + [headers.join(","), ...rows.map(r => r.join(","))].join("\r\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "results.csv";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  // -- grafik --
  function drawCharts(data) {
    if (!window.Chart) return;
    const configs = data.configs || [];
    const dk = document.body.classList.contains("theme-dark");

    const C = {
      text: dk ? "#cbd5e1" : "#374151",
      grid: dk ? "rgba(255,255,255,0.07)" : "rgba(0,0,0,0.06)",
      accent: dk ? "#5ba0d0" : "#3178a5",
      green: dk ? "#4ead6a" : "#3a8a53",
      neutral: dk ? "#475569" : "#94a3b8",
      dim: dk ? "#334155" : "#cbd5e1",
      phaseIO: dk ? "#334155" : "#cbd5e1",
      phaseCPU: dk ? "#64748b" : "#8c959f",
      phaseReduce: dk ? "#94a3b8" : "#475569",
    };

    Chart.defaults.color = C.text;
    Chart.defaults.borderColor = C.grid;
    Chart.defaults.font.family = 'ui-monospace, "SFMono-Regular", Consolas, monospace';
    Chart.defaults.font.size = 11;

    chartProcesses(configs, C);
    chartThreads(configs, C);
    chartSpeedup(configs, C);
    chartEfficiency(configs, C);
    chartPhases(configs, C);
    chartColdWarm(configs, C);
    if (data.corpus && data.corpus.file_size_histogram)
      chartHistogram(data.corpus.file_size_histogram, C);
  }

  function chartProcesses(configs, C) {
    const ctx = document.getElementById("canvas-procs");
    if (!ctx) return;
    if (chartInstances.p) chartInstances.p.destroy();

    const sel = configs.filter(c => c.threads === 4 && c.data === 1460).sort((a,b) => a.procs - b.procs);
    const labels = sel.map(c => c.procs + "P");
    const times = sel.map(c => c.mean);
    const colors = sel.map(c => c.procs === 3 ? C.accent : c.procs === 6 ? C.green : C.neutral);
    const radii = sel.map(c => (c.procs === 3 || c.procs === 6) ? 6 : 4);

    chartInstances.p = new Chart(ctx, {
      type: "line",
      data: { labels, datasets: [{ label: "Waktu (s)", data: times, borderColor: C.neutral, backgroundColor: "rgba(148,163,184,0.06)", pointBackgroundColor: colors, pointBorderColor: "#fff", pointRadius: radii, pointHoverRadius: 8, borderWidth: 2, fill: true, tension: 0.15 }] },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { callbacks: { afterLabel: ctx => { const c = sel[ctx.dataIndex]; if (c.procs === 3) return "Konfigurasi NIM (4T/3P)"; if (c.procs === 6) return "Tercepat (4T/6P)"; return ""; } } } }, scales: { y: { beginAtZero: true, title: { display: true, text: "Waktu (detik)", color: C.text }, grid: { color: C.grid } }, x: { grid: { color: C.grid } } } }
    });
  }

  function chartThreads(configs, C) {
    const ctx = document.getElementById("canvas-threads");
    if (!ctx) return;
    if (chartInstances.t) chartInstances.t.destroy();

    const sel = configs.filter(c => c.procs === 3 && c.data === 1460).sort((a,b) => a.threads - b.threads);
    const labels = sel.map(c => c.threads + "T");
    const times = sel.map(c => c.mean);

    // catatan variasi waktu thread
    if (sel.length > 0) {
      const minC = sel.reduce((p,c) => c.mean < p.mean ? c : p, sel[0]);
      const maxC = sel.reduce((p,c) => c.mean > p.mean ? c : p, sel[0]);
      const diff = (((maxC.mean - minC.mean) / minC.mean) * 100).toFixed(1);
      const note = document.getElementById("threads-note");
      if (note) note.textContent = "Variasi " + diff + "% (" + minC.mean.toFixed(2) + " s pada " + minC.threads + "T vs " + maxC.mean.toFixed(2) + " s pada " + maxC.threads + "T)";
    }

    const colors = sel.map(c => c.threads === 4 ? C.accent : C.neutral);
    const radii = sel.map(c => c.threads === 4 ? 6 : 4);

    chartInstances.t = new Chart(ctx, {
      type: "line",
      data: { labels, datasets: [{ label: "Waktu (s)", data: times, borderColor: C.neutral, backgroundColor: "rgba(148,163,184,0.06)", pointBackgroundColor: colors, pointBorderColor: "#fff", pointRadius: radii, pointHoverRadius: 8, borderWidth: 2, fill: true, tension: 0.15 }] },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { callbacks: { afterLabel: ctx => sel[ctx.dataIndex].threads === 4 ? "Konfigurasi NIM" : "" } } }, scales: { y: { beginAtZero: true, title: { display: true, text: "Waktu (s)", color: C.text }, grid: { color: C.grid } }, x: { grid: { color: C.grid } } } }
    });
  }

  function chartSpeedup(configs, C) {
    const ctx = document.getElementById("canvas-speedup");
    if (!ctx) return;
    if (chartInstances.s) chartInstances.s.destroy();

    const c1460 = configs.filter(c => c.data === 1460);
    const fastest = c1460.length ? c1460.reduce((p,c) => c.mean < p.mean ? c : p, c1460[0]) : null;

    const labels = configs.map(c => cfgLabel(c));
    const speeds = configs.map(c => c.speedup);
    const bg = configs.map(c => { if (c.id === 5) return C.accent; if (fastest && c.id === fastest.id) return C.green; return C.neutral; });

    chartInstances.s = new Chart(ctx, {
      type: "bar",
      data: { labels, datasets: [{ label: "Speedup", data: speeds, backgroundColor: bg, borderRadius: 2, borderWidth: 0 }] },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { callbacks: { title: items => { const c = configs[items[0].dataIndex]; return "C" + c.id + ": " + c.threads + "T/" + c.procs + "P (" + c.data + " file)"; }, afterLabel: ctx => { const c = configs[ctx.dataIndex]; if (c.id === 5) return "Konfigurasi NIM"; if (fastest && c.id === fastest.id) return "Tercepat (1460 file)"; return ""; } } } }, scales: { y: { beginAtZero: true, title: { display: true, text: "Speedup (x)", color: C.text }, grid: { color: C.grid } }, x: { grid: { display: false } } } }
    });
  }

  function chartEfficiency(configs, C) {
    const ctx = document.getElementById("canvas-efficiency");
    if (!ctx) return;
    if (chartInstances.e) chartInstances.e.destroy();

    const c1460 = configs.filter(c => c.data === 1460);

    const labels = configs.map(c => cfgLabel(c));
    const eff = configs.map(c => c.efficiency);
    const bg = configs.map(c => c.id === 5 ? C.accent : C.neutral);

    chartInstances.e = new Chart(ctx, {
      type: "bar",
      data: { labels, datasets: [
        { label: "Efisiensi (%)", data: eff, backgroundColor: bg, borderRadius: 2, order: 2 },
        { label: "Ideal 100%", data: new Array(configs.length).fill(100), type: "line", borderColor: "#d45555", borderDash: [4,4], borderWidth: 1.5, pointRadius: 0, fill: false, order: 1 }
      ] },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: "top", labels: { boxWidth: 10, padding: 6 } }, tooltip: { callbacks: { title: items => { const c = configs[items[0].dataIndex]; return "C" + c.id + ": " + c.threads + "T/" + c.procs + "P"; } } } }, scales: { y: { beginAtZero: true, title: { display: true, text: "Efisiensi (%)", color: C.text }, grid: { color: C.grid } }, x: { grid: { display: false } } } }
    });
  }

  function chartPhases(configs, C) {
    const ctx = document.getElementById("canvas-phases");
    if (!ctx) return;
    if (chartInstances.ph) chartInstances.ph.destroy();

    const labels = configs.map(c => cfgLabel(c));
    const io = configs.map(c => c.avg_phase_times ? c.avg_phase_times.io : 0);
    const cpu = configs.map(c => c.avg_phase_times ? c.avg_phase_times.cpu : 0);
    const red = configs.map(c => c.avg_phase_times ? c.avg_phase_times.reduce : 0);

    chartInstances.ph = new Chart(ctx, {
      type: "bar",
      data: { labels, datasets: [
        { label: "I/O", data: io, backgroundColor: C.phaseIO },
        { label: "CPU", data: cpu, backgroundColor: C.phaseCPU },
        { label: "Reduce", data: red, backgroundColor: C.phaseReduce }
      ] },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: "top", labels: { boxWidth: 10, padding: 6 } } }, scales: { x: { stacked: true, grid: { display: false } }, y: { beginAtZero: true, stacked: true, title: { display: true, text: "Durasi (s)", color: C.text }, grid: { color: C.grid } } } }
    });
  }

  function chartColdWarm(configs, C) {
    const ctx = document.getElementById("canvas-cold-warm");
    if (!ctx) return;
    if (chartInstances.cw) chartInstances.cw.destroy();

    const labels = configs.map(c => cfgLabel(c));
    const cold = configs.map(c => c.cold || c.mean);
    const warm = configs.map(c => c.warm || c.mean);

    chartInstances.cw = new Chart(ctx, {
      type: "bar",
      data: { labels, datasets: [
        { label: "Cold (Run 1)", data: cold, backgroundColor: C.neutral, borderRadius: 2 },
        { label: "Warm (Run 2-3)", data: warm, backgroundColor: C.accent, borderRadius: 2 }
      ] },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: "top", labels: { boxWidth: 10, padding: 6 } } }, scales: { y: { beginAtZero: true, title: { display: true, text: "Durasi (s)", color: C.text }, grid: { color: C.grid } }, x: { grid: { display: false } } } }
    });
  }

  function chartHistogram(hist, C) {
    const ctx = document.getElementById("canvas-histogram");
    if (!ctx) return;
    if (chartInstances.h) chartInstances.h.destroy();

    chartInstances.h = new Chart(ctx, {
      type: "bar",
      data: { labels: Object.keys(hist), datasets: [{ label: "File", data: Object.values(hist), backgroundColor: C.neutral, borderRadius: 2 }] },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, title: { display: true, text: "Jumlah File", color: C.text }, grid: { color: C.grid } }, x: { grid: { display: false } } } }
    });
  }

  // -- korpus dan worker --
  function fillCorpusAndWorkers(data) {
    const el = document.getElementById("dataset-summary-text");
    if (el && data.corpus) {
      const c = data.corpus;
      el.textContent = c.total_files.toLocaleString("id-ID") + " file / " + c.total_size_mb.toFixed(2) + " MB / " + c.total_words.toLocaleString("id-ID") + " kata / " + c.total_chars.toLocaleString("id-ID") + " karakter";
    }

    // top-20 kata
    const wc = document.getElementById("top-words-container");
    if (wc && data.corpus && data.corpus.top_words_20) {
      wc.innerHTML = "";
      data.corpus.top_words_20.forEach((item, i) => {
        const row = document.createElement("div");
        row.className = "word-row font-mono";
        row.innerHTML = '<div><span class="word-rank">' + String(i+1).padStart(2,"0") + '.</span> <span class="word-term">' + item.word + '</span></div><span class="word-count-num">' + item.count.toLocaleString("id-ID") + '</span>';
        wc.appendChild(row);
      });
    }

    // worker load balance
    const wb = document.getElementById("worker-balance-container");
    const nimCfg = (data.configs || []).find(c => c.id === 5);
    if (wb && nimCfg && nimCfg.worker_stats) {
      wb.innerHTML = "";
      const total = nimCfg.worker_stats.reduce((a,w) => a + w.worker_time, 0);
      nimCfg.worker_stats.forEach((w, i) => {
        const tr = document.createElement("tr");
        const mb = (w.total_bytes / (1024*1024)).toFixed(2);
        const pct = total > 0 ? ((w.worker_time / total) * 100).toFixed(1) : "—";
        tr.innerHTML = '<td>Worker #' + (i+1) + '</td><td class="font-mono">' + w.pid + '</td><td class="tr font-mono">' + w.file_count + '</td><td class="tr font-mono">' + mb + '</td><td class="tr font-mono">' + w.worker_time.toFixed(2) + '</td><td class="tr font-mono">' + pct + '%</td>';
        wb.appendChild(tr);
      });
    }
  }

  // -- tema --
  function initTheme() {
    const btn = document.getElementById("theme-toggle");
    const saved = localStorage.getItem("dashboard-theme") || "dark";

    if (saved === "light") {
      document.body.classList.replace("theme-dark", "theme-light");
      toggleIcons(btn, true);
    }

    if (btn) btn.addEventListener("click", () => {
      const isDark = document.body.classList.contains("theme-dark");
      if (isDark) {
        document.body.classList.replace("theme-dark", "theme-light");
        localStorage.setItem("dashboard-theme", "light");
      } else {
        document.body.classList.replace("theme-light", "theme-dark");
        localStorage.setItem("dashboard-theme", "dark");
      }
      toggleIcons(btn, isDark);
      if (benchmarkData) drawCharts(benchmarkData);
    });
  }

  function toggleIcons(btn, showMoon) {
    if (!btn) return;
    const sun = btn.querySelector(".icon-sun");
    const moon = btn.querySelector(".icon-moon");
    if (sun) sun.classList.toggle("hidden", showMoon);
    if (moon) moon.classList.toggle("hidden", !showMoon);
  }

  // -- download grafik --
  function initChartDownloads() {
    document.querySelectorAll(".btn-dl").forEach(btn => {
      btn.addEventListener("click", () => {
        const canvas = document.getElementById(btn.dataset.target);
        if (!canvas) return;
        const a = document.createElement("a");
        a.download = btn.dataset.target + ".png";
        a.href = canvas.toDataURL("image/png");
        a.click();
      });
    });
  }

  function setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  }

  // label pendek untuk sumbu X grafik per-konfigurasi
  function cfgLabel(c) {
    return "C" + c.id + " \u00b7 " + c.threads + "T/" + c.procs + "P";
  }
});
