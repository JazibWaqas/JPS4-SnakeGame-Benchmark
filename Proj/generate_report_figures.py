"""
Generate high-quality figures for the progress report.
Run: python generate_report_figures.py
"""
import os, sys

_CODE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "Snake Game Code")
if _CODE not in sys.path:
    sys.path.insert(0, _CODE)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

FIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "report", "figures")
os.makedirs(FIG_DIR, exist_ok=True)

# ── Data from benchmark (run_preliminary_benchmark.py, seed=42, 24 trials) ──
densities   = [0.15, 0.28, 0.40]
dens_labels = [r"$\rho=0.15$", r"$\rho=0.28$", r"$\rho=0.40$"]

data = {
    "Dijkstra": {"exp": [2062.2, 1659.2, 915.0],  "ms": [7.067, 4.955, 2.729]},
    "A*":       {"exp": [1019.7,  629.0,  513.2],  "ms": [3.741, 2.112, 1.701]},
    "JPS4":     {"exp": [ 488.4,  969.8,  681.6],  "ms": [4.432, 6.216, 3.132]},
}

COLORS = {"Dijkstra": "#e05c5c", "A*": "#4d94e0", "JPS4": "#2ca02c"}
MARKERS = {"Dijkstra": "o", "A*": "s", "JPS4": "D"}

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "lines.linewidth": 1.8,
    "lines.markersize": 6,
    "figure.dpi": 150,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.linestyle": "--",
    "grid.alpha": 0.4,
})

# ── Figure 1: Side-by-side expansions + time line charts ──────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 2.9))

for alg, d in data.items():
    ax1.plot(dens_labels, d["exp"], marker=MARKERS[alg], color=COLORS[alg], label=alg)
    ax2.plot(dens_labels, d["ms"],  marker=MARKERS[alg], color=COLORS[alg], label=alg)

ax1.set_title("(a) Mean Node Expansions")
ax1.set_xlabel("Obstacle density")
ax1.set_ylabel("Heap pops (mean)")
ax1.legend(framealpha=0.7)

ax2.set_title("(b) Mean Wall-Clock Time")
ax2.set_xlabel("Obstacle density")
ax2.set_ylabel("Time (ms, mean)")
ax2.legend(framealpha=0.7)

fig.tight_layout(pad=1.2)
out = os.path.join(FIG_DIR, "results_combined.pdf")
fig.savefig(out, bbox_inches="tight")
fig.savefig(out.replace(".pdf", ".png"), bbox_inches="tight", dpi=200)
plt.close(fig)
print(f"Saved combined figure: {out}")

# ── Figure 2: Reduction ratio vs Dijkstra (expansions) ───────────────────────
fig2, ax = plt.subplots(figsize=(3.5, 2.6))
dij_exp = data["Dijkstra"]["exp"]
for alg in ["A*", "JPS4"]:
    ratios = [data[alg]["exp"][i] / dij_exp[i] * 100 for i in range(len(densities))]
    ax.plot(dens_labels, ratios, marker=MARKERS[alg], color=COLORS[alg], label=alg)

ax.axhline(100, color=COLORS["Dijkstra"], linestyle="--", linewidth=1.2, label="Dijkstra (100%)")
ax.set_title("Expansions Relative to Dijkstra (%)")
ax.set_xlabel("Obstacle density")
ax.set_ylabel("% of Dijkstra expansions")
ax.legend(framealpha=0.7)
ax.set_ylim(0, 130)

fig2.tight_layout(pad=1.2)
out2 = os.path.join(FIG_DIR, "expansion_ratio.pdf")
fig2.savefig(out2, bbox_inches="tight")
fig2.savefig(out2.replace(".pdf", ".png"), bbox_inches="tight", dpi=200)
plt.close(fig2)
print(f"Saved ratio figure: {out2}")

# ── Figure 3: Path illustration schematic ─────────────────────────────────────
# Simple grid tile illustration showing the JPS "jump" concept
fig3, ax3 = plt.subplots(figsize=(3.0, 2.4))
ax3.set_xlim(0, 9); ax3.set_ylim(0, 7)
ax3.set_aspect("equal")
ax3.axis("off")
ax3.set_title("JPS4: Pruning vs A* Expansion", fontsize=9, pad=4)

# Draw grid
for x in range(9):
    for y in range(7):
        rect = plt.Rectangle((x, y), 1, 1, fill=False, edgecolor="#cccccc", lw=0.4)
        ax3.add_patch(rect)

# Obstacles
obstacles = [(2,3),(2,4),(5,1),(5,2),(5,3),(7,5)]
for (ox, oy) in obstacles:
    ax3.add_patch(plt.Rectangle((ox, oy), 1, 1, color="#555555"))

# A* explored cells (many)
astar_cells = [(1,2),(1,3),(1,4),(2,2),(3,2),(3,3),(3,4),(3,5),(4,1),(4,2),(4,3),(4,4),(4,5),(4,6)]
for (cx, cy) in astar_cells:
    ax3.add_patch(plt.Rectangle((cx, cy), 1, 1, color="#4d94e0", alpha=0.25))

# JPS jump points (just a few)
jps_pts = [(1,2),(3,3),(6,3),(8,4)]
for (jx, jy) in jps_pts:
    ax3.add_patch(plt.Rectangle((jx, jy), 1, 1, color="#2ca02c", alpha=0.5))
    ax3.plot(jx+0.5, jy+0.5, "D", color="#2ca02c", markersize=5, zorder=5)

# Start / Goal
ax3.add_patch(plt.Rectangle((0,2),1,1,color="#e05c5c",alpha=0.8))
ax3.text(0.5,2.5,"S", ha="center", va="center", color="white", fontsize=8, fontweight="bold")
ax3.add_patch(plt.Rectangle((8,4),1,1,color="#e0a020",alpha=0.8))
ax3.text(8.5,4.5,"G", ha="center", va="center", color="white", fontsize=8, fontweight="bold")

# Arrow path
ax3.annotate("", xy=(8.5,4.5), xytext=(0.5,2.5),
    arrowprops=dict(arrowstyle="->", color="#2ca02c", lw=1.5,
                    connectionstyle="arc3,rad=-0.1"))

blue_patch = mpatches.Patch(color="#4d94e0", alpha=0.5, label="A* explored")
green_patch = mpatches.Patch(color="#2ca02c", alpha=0.6, label="JPS jump pts")
ax3.legend(handles=[blue_patch, green_patch], loc="lower right", fontsize=7, framealpha=0.8)

fig3.tight_layout()
out3 = os.path.join(FIG_DIR, "jps_concept.png")
fig3.savefig(out3, bbox_inches="tight", dpi=200)
plt.close(fig3)
print(f"Saved concept figure: {out3}")

print("All figures saved to:", FIG_DIR)
