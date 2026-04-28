# Generates all figures for the final report from real benchmark data.
# Usage: python benchmark/generate_figures.py
# Reads:  results/extended_summary_*.json  (latest file)
# Writes: report/figures/*.pdf and *.png

import glob
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

_PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG_DIR = os.path.join(_PROJ, "report", "figures")
os.makedirs(FIG_DIR, exist_ok=True)

summaries = sorted(glob.glob(os.path.join(_PROJ, "results", "extended_summary_*.json")))
if not summaries:
    raise FileNotFoundError("No extended_summary_*.json found. Run benchmark/run_benchmark.py first.")
summary_path = summaries[-1]
print("Using:", summary_path)
with open(summary_path, encoding="utf-8") as f:
    data = json.load(f)

results = data["results"]

COLORS  = {"dijkstra": "#e05c5c", "astar": "#4d94e0", "jps4": "#2ca02c"}
LABELS  = {"dijkstra": "Dijkstra", "astar": "A*", "jps4": "JPS4"}
MARKERS = {"dijkstra": "o", "astar": "s", "jps4": "D"}
MODES   = ["dijkstra", "astar", "jps4"]

plt.rcParams["font.family"] = "serif"
plt.rcParams["font.size"]   = 9
plt.rcParams["axes.grid"]   = True
plt.rcParams["grid.linestyle"] = "--"
plt.rcParams["grid.alpha"]  = 0.4


def extract_series(grid_key, metric):
    d = results[grid_key]
    densities = d["densities"]
    series = {m: [d["per_density"][str(rho)][m][metric] for rho in densities] for m in MODES}
    return densities, series


def save(fig, stem):
    pdf = os.path.join(FIG_DIR, stem + ".pdf")
    fig.savefig(pdf, bbox_inches="tight")
    fig.savefig(pdf.replace(".pdf", ".png"), bbox_inches="tight", dpi=200)
    plt.close(fig)
    print("saved:", pdf)


# --- Fig 1: expansions + time for 50x50 ---
densities_50, exp_50  = extract_series("50x50", "exp_mean")
_,             time_50 = extract_series("50x50", "time_mean")
lbl50 = [f"{d:.2f}" for d in densities_50]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 2.9))
for m in MODES:
    ax1.plot(lbl50, exp_50[m],  marker=MARKERS[m], color=COLORS[m], label=LABELS[m])
    ax2.plot(lbl50, time_50[m], marker=MARKERS[m], color=COLORS[m], label=LABELS[m])
ax1.set_title("(a) Mean Node Expansions  [50x50]")
ax1.set_xlabel("Obstacle density"); ax1.set_ylabel("Heap pops (mean, 30 trials)"); ax1.legend()
ax2.set_title("(b) Mean Search Time  [50x50]")
ax2.set_xlabel("Obstacle density"); ax2.set_ylabel("Wall-clock time (ms, mean)"); ax2.legend()
fig.tight_layout(pad=1.2)
save(fig, "results_50x50")

# --- Fig 2: expansions + time for 100x100 ---
densities_100, exp_100  = extract_series("100x100", "exp_mean")
_,              time_100 = extract_series("100x100", "time_mean")
lbl100 = [f"{d:.2f}" for d in densities_100]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 2.9))
for m in MODES:
    ax1.plot(lbl100, exp_100[m],  marker=MARKERS[m], color=COLORS[m], label=LABELS[m])
    ax2.plot(lbl100, time_100[m], marker=MARKERS[m], color=COLORS[m], label=LABELS[m])
ax1.set_title("(a) Mean Node Expansions  [100x100]")
ax1.set_xlabel("Obstacle density"); ax1.set_ylabel("Heap pops (mean, 30 trials)"); ax1.legend()
ax2.set_title("(b) Mean Search Time  [100x100]")
ax2.set_xlabel("Obstacle density"); ax2.set_ylabel("Wall-clock time (ms, mean)"); ax2.legend()
fig.tight_layout(pad=1.2)
save(fig, "results_100x100")

# --- Fig 3: expansion ratio relative to Dijkstra, both grid sizes ---
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 2.9))
for ax, dens, exp, title in [
    (ax1, densities_50,  exp_50,  "50x50 grid"),
    (ax2, densities_100, exp_100, "100x100 grid"),
]:
    lbl = [f"{d:.2f}" for d in dens]
    dij = exp["dijkstra"]
    for m in ["astar", "jps4"]:
        ratios = [exp[m][i] / dij[i] * 100 for i in range(len(dens))]
        ax.plot(lbl, ratios, marker=MARKERS[m], color=COLORS[m], label=LABELS[m])
    ax.axhline(100, color=COLORS["dijkstra"], linestyle="--", linewidth=1.2, label="Dijkstra (100%)")
    ax.set_title(f"Expansions vs Dijkstra (%)  [{title}]")
    ax.set_xlabel("Obstacle density"); ax.set_ylabel("% of Dijkstra expansions")
    ax.legend(); ax.set_ylim(0, 115)
fig.tight_layout(pad=1.2)
save(fig, "expansion_ratio")

# --- Fig 4: JPS4 reduction over A*, both grid sizes ---
fig, ax = plt.subplots(figsize=(5.5, 3.0))
for grid_key, dens, exp, ls in [
    ("50x50",   densities_50,  exp_50,  "-"),
    ("100x100", densities_100, exp_100, "--"),
]:
    lbl = [f"{d:.2f}" for d in dens]
    speedup = [exp["astar"][i] / exp["jps4"][i] for i in range(len(dens))]
    ax.plot(lbl, speedup, marker="D", color=COLORS["jps4"], linestyle=ls,
            label=f"A* / JPS4 expansions  ({grid_key})")
ax.axhline(1.0, color="#999999", linestyle=":", linewidth=1.0, label="Parity")
ax.set_xlabel("Obstacle density")
ax.set_ylabel("A* expansions / JPS4 expansions")
ax.set_title("JPS4 Expansion Reduction Relative to A*")
ax.legend(fontsize=8)
fig.tight_layout(pad=1.2)
save(fig, "jps4_speedup")

# --- Fig 5: JPS4 concept schematic ---
fig3, ax3 = plt.subplots(figsize=(3.2, 2.6))
ax3.set_xlim(0, 9); ax3.set_ylim(0, 7)
ax3.set_aspect("equal"); ax3.axis("off")
ax3.set_title("JPS4: Pruning vs A* Expansion", fontsize=9, pad=4)
for x in range(9):
    for y in range(7):
        ax3.add_patch(plt.Rectangle((x, y), 1, 1, fill=False, edgecolor="#cccccc", lw=0.4))
for ox, oy in [(2, 3), (2, 4), (5, 1), (5, 2), (5, 3), (7, 5)]:
    ax3.add_patch(plt.Rectangle((ox, oy), 1, 1, color="#555555"))
for cx, cy in [(1,2),(1,3),(1,4),(2,2),(3,2),(3,3),(3,4),(3,5),(4,1),(4,2),(4,3),(4,4),(4,5),(4,6)]:
    ax3.add_patch(plt.Rectangle((cx, cy), 1, 1, color="#4d94e0", alpha=0.25))
for jx, jy in [(1, 2), (3, 3), (6, 3), (8, 4)]:
    ax3.add_patch(plt.Rectangle((jx, jy), 1, 1, color="#2ca02c", alpha=0.5))
    ax3.plot(jx + 0.5, jy + 0.5, "D", color="#2ca02c", markersize=5, zorder=5)
ax3.add_patch(plt.Rectangle((0, 2), 1, 1, color="#e05c5c", alpha=0.8))
ax3.text(0.5, 2.5, "S", ha="center", va="center", color="white", fontsize=8, fontweight="bold")
ax3.add_patch(plt.Rectangle((8, 4), 1, 1, color="#e0a020", alpha=0.8))
ax3.text(8.5, 4.5, "G", ha="center", va="center", color="white", fontsize=8, fontweight="bold")
ax3.annotate("", xy=(8.5, 4.5), xytext=(0.5, 2.5),
    arrowprops=dict(arrowstyle="->", color="#2ca02c", lw=1.5, connectionstyle="arc3,rad=-0.1"))
ax3.legend(handles=[
    mpatches.Patch(color="#4d94e0", alpha=0.5, label="A* explored"),
    mpatches.Patch(color="#2ca02c", alpha=0.6, label="JPS4 jump points"),
], loc="lower right", fontsize=7)
fig3.tight_layout()
save(fig3, "jps_concept")

print("\nAll figures written to:", FIG_DIR)
