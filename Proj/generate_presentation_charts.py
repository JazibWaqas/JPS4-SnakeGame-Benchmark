"""
Generates all dark-themed presentation charts.
Usage: python generate_presentation_charts.py
Writes PNG files to Proj/presentation_charts/
"""

import glob, json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
import numpy as np

# ── paths ──────────────────────────────────────────────────────────────────
PROJ     = os.path.dirname(os.path.abspath(__file__))
OUT_DIR  = os.path.join(PROJ, "presentation_charts")
os.makedirs(OUT_DIR, exist_ok=True)

summaries = sorted(glob.glob(os.path.join(PROJ, "results", "extended_summary_*.json")))
if not summaries:
    raise FileNotFoundError("No extended_summary_*.json found in results/")
with open(summaries[-1], encoding="utf-8") as f:
    data = json.load(f)
results = data["results"]

# ── palette ─────────────────────────────────────────────────────────────────
BG       = "#1e2130"
AX_BG    = "#252a3d"
C_DIJ    = "#e05c5c"
C_AST    = "#f5a623"
C_JPS    = "#3ecf8e"
C_WHITE  = "#ffffff"
C_GREY   = "#8892a4"
C_GRID   = "#353c55"

COLORS  = {"dijkstra": C_DIJ,  "astar": C_AST,  "jps4": C_JPS}
LABELS  = {"dijkstra": "Dijkstra", "astar": "A*", "jps4": "JPS4"}
MARKERS = {"dijkstra": "o",    "astar": "s",    "jps4": "D"}
MODES   = ["dijkstra", "astar", "jps4"]


def dark_base(figsize):
    plt.rcParams.update({
        "font.family": "sans-serif",
        "text.color":  C_WHITE,
        "axes.labelcolor": C_WHITE,
        "xtick.color": C_WHITE,
        "ytick.color": C_WHITE,
    })
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(AX_BG)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(C_GRID)
    ax.spines["bottom"].set_color(C_GRID)
    ax.tick_params(colors=C_WHITE, which="both")
    ax.grid(True, color=C_GRID, linestyle="--", linewidth=0.7, alpha=0.8)
    return fig, ax


def save(fig, name):
    path = os.path.join(OUT_DIR, name + ".png")
    fig.savefig(path, dpi=220, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print("saved:", path)


def extract(grid_key, metric):
    d = results[grid_key]
    dens = d["densities"]
    series = {m: [d["per_density"][str(r)][m][metric] for r in dens] for m in MODES}
    return dens, series


# ── CHART 1: Expansions vs Density — 100x100 (main trend slide) ──────────
dens100, exp100 = extract("100x100", "exp_mean")
xlabels = [f"{int(d*100)}%" for d in dens100]

fig, ax = dark_base((11, 6))
lw = 2.8
ms = 8
for m in MODES:
    ax.plot(xlabels, exp100[m], marker=MARKERS[m], color=COLORS[m],
            label=LABELS[m], linewidth=lw, markersize=ms, zorder=3)

# annotate gap at 10%
ax.annotate("", xy=(0, exp100["jps4"][0]), xytext=(0, exp100["dijkstra"][0]),
            arrowprops=dict(arrowstyle="<->", color=C_WHITE, lw=1.2))
ax.text(0.12, (exp100["jps4"][0] + exp100["dijkstra"][0]) / 2,
        "73% fewer\nexpansions", color=C_WHITE, fontsize=9, va="center")

ax.set_xlabel("Obstacle Density", fontsize=13, labelpad=8)
ax.set_ylabel("Avg Node Expansions  (30 trials)", fontsize=13, labelpad=8)
ax.set_title("Node Expansions vs Obstacle Density  [100×100 Grid]",
             fontsize=15, fontweight="bold", color=C_WHITE, pad=14)
ax.legend(fontsize=12, framealpha=0.15, labelcolor=C_WHITE,
          facecolor=AX_BG, edgecolor=C_GRID)
ax.tick_params(labelsize=11)
fig.tight_layout(pad=1.5)
save(fig, "slide_trend_100x100")


# ── CHART 2: Expansions vs Density — 50x50 ───────────────────────────────
dens50, exp50 = extract("50x50", "exp_mean")
xlabels50 = [f"{int(d*100)}%" for d in dens50]

fig, ax = dark_base((11, 6))
for m in MODES:
    ax.plot(xlabels50, exp50[m], marker=MARKERS[m], color=COLORS[m],
            label=LABELS[m], linewidth=lw, markersize=ms, zorder=3)

ax.set_xlabel("Obstacle Density", fontsize=13, labelpad=8)
ax.set_ylabel("Avg Node Expansions  (30 trials)", fontsize=13, labelpad=8)
ax.set_title("Node Expansions vs Obstacle Density  [50×50 Grid]",
             fontsize=15, fontweight="bold", color=C_WHITE, pad=14)
ax.legend(fontsize=12, framealpha=0.15, labelcolor=C_WHITE,
          facecolor=AX_BG, edgecolor=C_GRID)
ax.tick_params(labelsize=11)
fig.tight_layout(pad=1.5)
save(fig, "slide_trend_50x50")


# ── CHART 3: Side-by-side both grids ─────────────────────────────────────
plt.rcParams.update({"font.family": "sans-serif", "text.color": C_WHITE,
                     "axes.labelcolor": C_WHITE, "xtick.color": C_WHITE, "ytick.color": C_WHITE})
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
fig.patch.set_facecolor(BG)

for ax, xlbls, exp, title in [
    (ax1, xlabels50,  exp50,  "50×50 Grid"),
    (ax2, xlabels,    exp100, "100×100 Grid"),
]:
    ax.set_facecolor(AX_BG)
    ax.spines["top"].set_visible(False);  ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(C_GRID);  ax.spines["bottom"].set_color(C_GRID)
    ax.grid(True, color=C_GRID, linestyle="--", linewidth=0.7, alpha=0.8)
    ax.tick_params(colors=C_WHITE, labelsize=11)
    for m in MODES:
        ax.plot(xlbls, exp[m], marker=MARKERS[m], color=COLORS[m],
                label=LABELS[m], linewidth=lw, markersize=ms, zorder=3)
    ax.set_xlabel("Obstacle Density", fontsize=12, labelpad=8)
    ax.set_ylabel("Avg Node Expansions", fontsize=12, labelpad=8)
    ax.set_title(title, fontsize=14, fontweight="bold", color=C_WHITE, pad=10)
    ax.legend(fontsize=11, framealpha=0.15, labelcolor=C_WHITE,
              facecolor=AX_BG, edgecolor=C_GRID)

fig.suptitle("Node Expansions vs Obstacle Density — Both Grid Sizes",
             fontsize=16, fontweight="bold", color=C_WHITE, y=1.02)
fig.tight_layout(pad=1.5)
save(fig, "slide_both_grids")


# ── CHART 4: JPS4 advantage (% saved vs Dijkstra) ────────────────────────
fig, ax = dark_base((11, 6))

pct_saved_100 = [(exp100["dijkstra"][i] - exp100["jps4"][i]) / exp100["dijkstra"][i] * 100
                 for i in range(len(dens100))]
pct_saved_50  = [(exp50["dijkstra"][i]  - exp50["jps4"][i])  / exp50["dijkstra"][i]  * 100
                 for i in range(len(dens50))]

ax.plot(xlabels,   pct_saved_100, marker="D", color=C_JPS, linewidth=lw,
        markersize=ms, label="100×100 grid", linestyle="-")
ax.plot(xlabels50, pct_saved_50,  marker="D", color="#5de8c8", linewidth=lw,
        markersize=ms, label="50×50 grid",   linestyle="--")

ax.axhline(50, color=C_GREY, linestyle=":", linewidth=1.2)
ax.text(6.1, 51.5, "50% savings line", color=C_GREY, fontsize=9)

ax.set_ylim(0, 100)
ax.set_xlabel("Obstacle Density", fontsize=13, labelpad=8)
ax.set_ylabel("Node Expansions Saved vs Dijkstra (%)", fontsize=13, labelpad=8)
ax.set_title("JPS4 Efficiency Advantage Over Dijkstra",
             fontsize=15, fontweight="bold", color=C_WHITE, pad=14)
ax.legend(fontsize=12, framealpha=0.15, labelcolor=C_WHITE,
          facecolor=AX_BG, edgecolor=C_GRID)
ax.tick_params(labelsize=11)

# annotate open vs dense
ax.annotate("73% saved\n(open map)", xy=(0, pct_saved_100[0]),
            xytext=(0.4, pct_saved_100[0] - 10),
            color=C_JPS, fontsize=10, fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=C_JPS))
ax.annotate("51% saved\n(dense map)", xy=(6, pct_saved_100[-1]),
            xytext=(4.8, pct_saved_100[-1] - 12),
            color=C_JPS, fontsize=10, fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=C_JPS))

fig.tight_layout(pad=1.5)
save(fig, "slide_jps4_advantage")


# ── CHART 5: Dark-theme JPS4 concept schematic ───────────────────────────
plt.rcParams.update({"text.color": C_WHITE})
fig, ax = plt.subplots(figsize=(9, 6))
fig.patch.set_facecolor(BG)
ax.set_facecolor(AX_BG)
ax.set_xlim(0, 12); ax.set_ylim(0, 8)
ax.set_aspect("equal"); ax.axis("off")
ax.set_title("How JPS4 Works: Jump Points vs Full Expansion",
             fontsize=13, fontweight="bold", color=C_WHITE, pad=12)

# draw grid
for x in range(12):
    for y in range(8):
        ax.add_patch(plt.Rectangle((x, y), 1, 1, fill=False,
                                   edgecolor=C_GRID, lw=0.5))

# obstacles
for ox, oy in [(3,4),(3,5),(3,6),(7,1),(7,2),(7,3),(7,4),(10,5),(10,6)]:
    ax.add_patch(plt.Rectangle((ox, oy), 1, 1, color="#444c6a"))

# A* explored cells (blue tint)
astar_cells = [(1,2),(1,3),(1,4),(2,2),(2,3),(2,4),(2,5),
               (4,2),(4,3),(4,4),(4,5),(5,2),(5,3),(5,4),(5,5),(5,6),
               (6,3),(6,4),(6,5),(6,6),(8,4),(8,5),(9,4),(9,5),(9,6)]
for cx, cy in astar_cells:
    ax.add_patch(plt.Rectangle((cx, cy), 1, 1, color="#4d94e0", alpha=0.22))

# JPS4 jump points (green diamonds)
jump_points = [(1, 2), (4, 2), (6, 3), (8, 4), (11, 5)]
for jx, jy in jump_points:
    ax.add_patch(plt.Rectangle((jx, jy), 1, 1, color=C_JPS, alpha=0.35))
    ax.plot(jx + 0.5, jy + 0.5, "D", color=C_JPS, markersize=9, zorder=5)

# path arrows between jump points
path = jump_points
for i in range(len(path) - 1):
    x0, y0 = path[i][0] + 0.5, path[i][1] + 0.5
    x1, y1 = path[i+1][0] + 0.5, path[i+1][1] + 0.5
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle="-|>", color=C_JPS, lw=2.0,
                                connectionstyle="arc3,rad=0.0"))

# Start and Goal
ax.add_patch(plt.Rectangle((0, 2), 1, 1, color=C_DIJ, alpha=0.9))
ax.text(0.5, 2.5, "S", ha="center", va="center",
        color="white", fontsize=11, fontweight="bold")
ax.add_patch(plt.Rectangle((11, 5), 1, 1, color=C_AST, alpha=0.9))
ax.text(11.5, 5.5, "G", ha="center", va="center",
        color="white", fontsize=11, fontweight="bold")

# labels
ax.text(2.5, 7.5, "A* explores all these cells", color="#4d94e0",
        fontsize=9.5, ha="center", style="italic")
ax.text(6.5, 0.3, "JPS4 only stops at jump points — skips everything in between",
        color=C_JPS, fontsize=9.5, ha="center", style="italic")

# legend
legend_handles = [
    mpatches.Patch(color="#4d94e0", alpha=0.5, label="A* explored cells"),
    mpatches.Patch(color=C_JPS,    alpha=0.5, label="JPS4 jump points only"),
    mpatches.Patch(color="#444c6a",            label="Obstacles"),
]
ax.legend(handles=legend_handles, loc="upper right", fontsize=9,
          framealpha=0.3, labelcolor=C_WHITE, facecolor=AX_BG, edgecolor=C_GRID)

fig.tight_layout(pad=1.0)
save(fig, "slide_jps4_concept")


print(f"\nAll charts written to: {OUT_DIR}")
print("Files:")
for f in sorted(os.listdir(OUT_DIR)):
    print(" ", f)
