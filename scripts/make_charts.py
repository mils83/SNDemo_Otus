# -*- coding: utf-8 -*-
"""Строит графики для отчёта ДЗ №6 из reports/loadtest_results.csv."""
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CSV = os.path.join(ROOT, "reports", "loadtest_results.csv")
OUT = os.path.join(ROOT, "reports")

rows = []
with open(CSV, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        r["concurrency"] = int(r["concurrency"])
        rows.append(r)
rows.sort(key=lambda r: r["concurrency"])

phases = {}
for r in rows:
    phases.setdefault(r["phase"], {})[r["concurrency"]] = r

before, after = phases["before"], phases["after"]
concurrency = sorted({r["concurrency"] for r in rows})
X = range(len(concurrency))
W = 0.2
LABELS = [str(c) for c in concurrency]


def v(ph, c, key):
    return float(ph[c][key])


# --- 1/3. Latency до и после: avg, p50, p95, p99 ------------------------------
for phase in ("before", "after"):
    ph = phases[phase]
    fig, ax = plt.subplots(figsize=(8, 5))
    for i, (key, label) in enumerate([("avg_ms", "avg"), ("p50_ms", "p50"),
                                      ("p95_ms", "p95"), ("p99_ms", "p99")]):
        ys = [v(ph, c, key) for c in concurrency]
        bars = ax.bar([x + i * W for x in X], ys, width=W, label=f"{label}, мс")
        for b, y in zip(bars, ys):
            ax.text(b.get_x() + b.get_width() / 2, max(y, 0.5) * 1.05, f"{y:g}",
                    ha="center", va="bottom", fontsize=7)
    ax.set_yscale("symlog", linthresh=10)
    ax.set_xticks([x + 1.5 * W for x in X])
    ax.set_xticklabels(LABELS)
    ax.set_xlabel("Количество одновременных запросов")
    ax.set_ylabel("Задержка, мс (лог. шкала)")
    ax.set_title("Задержка /user/search ДО добавления индекса"
                 if phase == "before" else
                 "Задержка /user/search ПОСЛЕ добавления индекса")
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    p = os.path.join(OUT, f"latency_{phase}.png")
    fig.savefig(p, dpi=150)
    plt.close(fig)
    print("saved", p)

# --- 2/4. Throughput до и после -----------------------------------------------
for phase in ("before", "after"):
    ph = phases[phase]
    fig, ax = plt.subplots(figsize=(7, 5))
    ys = [v(ph, c, "rps") for c in concurrency]
    bars = ax.bar(X, ys, width=0.55, color="#3572A5")
    for b, y in zip(bars, ys):
        ax.text(b.get_x() + b.get_width() / 2, y * 1.01, f"{y:g}",
                ha="center", va="bottom", fontsize=9)
    ax.set_xticks(X)
    ax.set_xticklabels(LABELS)
    ax.set_xlabel("Количество одновременных запросов")
    ax.set_ylabel("Requests per second")
    ax.set_title("Пропускная способность /user/search до добавления индекса"
                 if phase == "before" else
                 "Пропускная способность /user/search после добавления индекса")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    p = os.path.join(OUT, f"throughput_{phase}.png")
    fig.savefig(p, dpi=150)
    plt.close(fig)
    print("saved", p)

# --- 5. Сравнение задержки avg и p95 до/после ----------------------------------
fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
for ax, (key, label) in zip(axes, [("avg_ms", "avg"), ("p95_ms", "p95")]):
    xb = [x * 3 for x in X]
    ya = [x * 3 + 0.8 for x in X]
    ys_b = [v(before, c, key) for c in concurrency]
    ys_a = [v(after, c, key) for c in concurrency]
    ax.bar(xb, ys_b, width=0.7, color="#C44E52", label="до")
    ax.bar(ya, ys_a, width=0.7, color="#4C72B0", label="после")
    for x, y in list(zip(xb, ys_b)) + list(zip(ya, ys_a)):
        ax.text(x, max(y, 0.5) * 1.04, f"{y:g}", ha="center", va="bottom", fontsize=8)
    ax.set_yscale("symlog", linthresh=10)
    ax.set_xticks([x + 0.4 for x in xb])
    ax.set_xticklabels(LABELS)
    ax.set_xlabel("Количество одновременных запросов")
    ax.set_ylabel(f"Задержка {label}, мс (лог. шкала)")
    ax.set_title(f"Задержка {label}: до vs после")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
p = os.path.join(OUT, "latency_compare.png")
fig.savefig(p, dpi=150)
plt.close(fig)
print("saved", p)

# --- 6. Сравнение RPS до/после --------------------------------------------------
fig, ax = plt.subplots(figsize=(7.5, 5))
xb = [2 * x for x in X]
xa = [2 * x + 0.85 for x in X]
ys_b = [v(before, c, "rps") for c in concurrency]
ys_a = [v(after, c, "rps") for c in concurrency]
ax.bar(xb, ys_b, width=0.8, color="#C44E52", label="до индекса")
ax.bar(xa, ys_a, width=0.8, color="#4C72B0", label="после индекса")
for x, y in list(zip(xb, ys_b)) + list(zip(xa, ys_a)):
    ax.text(x, y * 1.01, f"{y:g}", ha="center", va="bottom", fontsize=8)
ax.set_xticks([x + 0.42 for x in xb])
ax.set_xticklabels(LABELS)
ax.set_xlabel("Количество одновременных запросов")
ax.set_ylabel("Requests per second")
ax.set_title("Пропускная способность /user/search: до vs после")
ax.legend()
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
p = os.path.join(OUT, "throughput_compare.png")
fig.savefig(p, dpi=150)
plt.close(fig)
print("saved", p)
