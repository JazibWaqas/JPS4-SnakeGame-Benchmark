# generate all figures for the final report using real benchmark data
# run: python generate_final_figures.py

import json
import os
import glob

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

_PROJ = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(_PROJ, "report", "figures")
os.makedirs(FIG_DIR, exist_ok=True)

# load the latest extended summary
summaries = sorted(glob.glob(os.path.join(_PROJ, "results", "extended_summary_*.json")))
if not summaries:
    raise FileNotFoundError("No extended_summary_*.json found. Run run_extended_benchmark.py first.")
summary_path = summaries[-1]
print("Using:", summary_path)
with open(summary_path, encoding="utf-8") as f:
    data = json.load(f)

results = data["results"]  # keys: "50x50", "100x100"

COLORS = {"dijkstra": "#e05c5c", "astar": "#4d94e0", "jps4": "#2ca02c"}
LABELS = {"dijkstra": "Dijkstra", "astar": "A*", "jps4": "JPS4"}
MARKERS = {"dijkstra": "o", "astar": "s", "jps4": "D"}
MODES = ["dijkstra", "astar", "jps4"]

plt.rcParams["font.family"] = "serif"
plt.rcParams["font.size"] = 9
plt.rcParams["axes.grid"] = True
plt.rcParams["grid.linestyle"] = "--"
plt.rcParams["grid.alpha"] = 0.4


def extract_series(grid_key, metric):
    d = results[grid_key]
    densities = d["densities"]
    series = {}
    for m in MODES:
        series[m] = [d["per_density"][str(rho)][m][metric] for rho in densities]
    return densities, series


# ------------------------------------------------------------------ #
# Fig 1: expansions + time for 50x50 (combined 2-panel)
# ------------------------------------------------------------------ #
densities_50, exp_50 = extract_series("50x50", "exp_mean")
_,            time_50 = extract_series("50x50", "time_mean")
dens_labels = [f"{d:.2f}" for d in densities_50]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 2.9))
for m in MODES:
    ax1.plot(dens_labels, exp_50[m],  marker=MARKERS[m], color=COLORS[m], label=LABELS[m])
    ax2.plot(dens_labels, time_50[m], marker=MARKERS[m], color=COLORS[m], label=LABELS[m])

ax1.set_title("(a) Mean Node Expansions  [50x50]")
ax1.set_xlabel("Obstacle density")
ax1.set_ylabel("Heap pops (mean, 30 trials)")
ax1.legend()

ax2.set_title("(b) Mean Search Time  [50x50]")
ax2.set_xlabel("Obstacle density")
ax2.set_ylabel("Wall-clock time (ms, mean)")
ax2.legend()

fig.tight_layout(pad=1.2)
out = os.path.join(FIG_DIR, "results_50x50.pdf")
fig.savefig(out, bbox_inches="tight")
fig.savefig(out.replace(".pdf", ".png"), bbox_inches="tight", dpi=200)
plt.close(fig)
print("saved:", out)

# ------------------------------------------------------------------ #
# Fig 2: expansions + time for 100x100 (combined 2-panel)
# ------------------------------------------------------------------ #
densities_100, exp_100 = extract_series("100x100", "exp_mean")
_,              time_100 = extract_series("100x100", "time_mean")
dens_labels_100 = [f"{d:.2f}" for d in densities_100]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 2.9))
for m in MODES:
    ax1.plot(dens_labels_100, exp_100[m],  marker=MARKERS[m], color=COLORS[m], label=LABELS[m])
    ax2.plot(dens_labels_100, time_100[m], marker=MARKERS[m], color=COLORS[m], label=LABELS[m])

ax1.set_title("(a) Mean Node Expansions  [100x100]")
ax1.set_xlabel("Obstacle density")
ax1.set_ylabel("Heap pops (mean, 30 trials)")
ax1.legend()

ax2.set_title("(b) Mean Search Time  [100x100]")
ax2.set_xlabel("Obstacle density")
ax2.set_ylabel("Wall-clock time (ms, mean)")
ax2.legend()

fig.tight_layout(pad=1.2)
out2 = os.path.join(FIG_DIR, "results_100x100.pdf")
fig.savefig(out2, bbox_inches="tight")
fig.savefig(out2.replace(".pdf", ".png"), bbox_inches="tight", dpi=200)
plt.close(fig)
print("saved:", out2)

# ------------------------------------------------------------------ #
# Fig 3: expansion ratio relative to Dijkstra, both grid sizes side by side
# ------------------------------------------------------------------ #
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 2.9))

for ax, grid_key, dens, exp, title in [
    (ax1, "50x50",   densities_50,  exp_50,  "50x50 grid"),
    (ax2, "100x100", densities_100, exp_100, "100x100 grid"),
]:
    dens_lbl = [f"{d:.2f}" for d in dens]
    dij = exp["dijkstra"]
    for m in ["astar", "jps4"]:
        ratios = [exp[m][i] / dij[i] * 100 for i in range(len(dens))]
        ax.plot(dens_lbl, ratios, marker=MARKERS[m], color=COLORS[m], label=LABELS[m])
    ax.axhline(100, color=COLORS["dijkstra"], linestyle="--", linewidth=1.2, label="Dijkstra (100%)")
    ax.set_title(f"Expansions vs Dijkstra (%)  [{title}]")
    ax.set_xlabel("Obstacle density")
    ax.set_ylabel("% of Dijkstra expansions")
    ax.legend()
    ax.set_ylim(0, 115)

fig.tight_layout(pad=1.2)
out3 = os.path.join(FIG_DIR, "expansion_ratio.pdf")
fig.savefig(out3, bbox_inches="tight")
fig.savefig(out3.replace(".pdf", ".png"), bbox_inches="tight", dpi=200)
plt.close(fig)
print("saved:", out3)

# ------------------------------------------------------------------ #
# Fig 4: JPS4 speedup factor vs A* (expansions), both sizes
# ------------------------------------------------------------------ #
fig, ax = plt.subplots(figsize=(5.5, 3.0))
for grid_key, dens, exp, ls in [("50x50", densities_50, exp_50, "-"), ("100x100", densities_100, exp_100, "--")]:
    dens_lbl = [f"{d:.2f}" for d in dens]
    speedup = [exp["astar"][i] / exp["jps4"][i] for i in range(len(dens))]
    ax.plot(dens_lbl, speedup, marker="D", color=COLORS["jps4"], linestyle=ls,
            label=f"JPS4 / A* expansion ratio  ({grid_key})")

ax.axhline(1.0, color="#999999", linestyle=":", linewidth=1.0, label="Parity (JPS4 = A*)")
ax.set_xlabel("Obstacle density")
ax.set_ylabel("A* expansions / JPS4 expansions")
ax.set_title("JPS4 Expansion Reduction Relative to A*")
ax.legend(fontsize=8)
fig.tight_layout(pad=1.2)
out4 = os.path.join(FIG_DIR, "jps4_speedup.pdf")
fig.savefig(out4, bbox_inches="tight")
fig.savefig(out4.replace(".pdf", ".png"), bbox_inches="tight", dpi=200)
plt.close(fig)
print("saved:", out4)

# ------------------------------------------------------------------ #
# Fig 5: JPS4 concept schematic (kept from original, reprinted cleanly)
# ------------------------------------------------------------------ #
fig3, ax3 = plt.subplots(figsize=(3.2, 2.6))
ax3.set_xlim(0, 9)
ax3.set_ylim(0, 7)
ax3.set_aspect("equal")
ax3.axis("off")
ax3.set_title("JPS4: Pruning vs A* Expansion", fontsize=9, pad=4)

for x in range(9):
    for y in range(7):
        ax3.add_patch(plt.Rectangle((x, y), 1, 1, fill=False, edgecolor="#cccccc", lw=0.4))

for ox, oy in [(2, 3), (2, 4), (5, 1), (5, 2), (5, 3), (7, 5)]:
    ax3.add_patch(plt.Rectangle((ox, oy), 1, 1, color="#555555"))

for cx, cy in [(1, 2), (1, 3), (1, 4), (2, 2), (3, 2), (3, 3), (3, 4), (3, 5),
               (4, 1), (4, 2), (4, 3), (4, 4), (4, 5), (4, 6)]:
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

blue_patch = mpatches.Patch(color="#4d94e0", alpha=0.5, label="A* explored")
green_patch = mpatches.Patch(color="#2ca02c", alpha=0.6, label="JPS4 jump points")
ax3.legend(handles=[blue_patch, green_patch], loc="lower right", fontsize=7)

fig3.tight_layout()
out5 = os.path.join(FIG_DIR, "jps_concept.png")
fig3.savefig(out5, bbox_inches="tight", dpi=200)
plt.close(fig3)
print("saved:", out5)

print("\nAll figures written to:", FIG_DIR)
