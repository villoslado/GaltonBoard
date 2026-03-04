import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.gridspec import GridSpec
from scipy.stats import binom

# ── Configuration ──────────────────────────────────────────────────────────────
NUM_BALLS       = 1000
NUM_ROWS        = 12
BALLS_PER_FRAME = 2
INTERVAL_MS     = 45
BALL_RADIUS     = 0.18
TRAIL_LENGTH    = 8
# ──────────────────────────────────────────────────────────────────────────────

plt.rcParams.update({
    "font.family":      "monospace",
    "axes.labelcolor":  "#888",
    "xtick.color":      "#666",
    "ytick.color":      "#666",
    "text.color":       "#ddd",
})

BG         = "#0d0d0d"
PANEL_BG   = "#111111"
PEG_COLOR  = "#e0e0e0"
PEG_GLOW   = "#ffffff"
BALL_COLOR = "#4fc3f7"
BALL_EDGE  = "#ffffff"
BAR_FACE   = "#1a3a4a"
BAR_EDGE   = "#4fc3f7"
CURVE_COL  = "#ff6b6b"
GRID_COL   = "#1e1e1e"
TEXT_COL   = "#cccccc"

# ── Simulate all ball paths ────────────────────────────────────────────────────
rng     = np.random.default_rng(42)
choices = rng.integers(0, 2, size=(NUM_BALLS, NUM_ROWS))
bins    = choices.sum(axis=1)

def make_path(choice_row, ball_idx):
    """
    Ball starts at top-center, deflects left/right at each peg,
    tracking its absolute x position correctly at every row.
    """
    x = 0.0
    xs = [x]
    ys = [1.5]

    for r in range(NUM_ROWS):
        peg_y = -r
        # drop straight down to peg level
        xs.append(x)
        ys.append(peg_y)
        # deflect left or right
        dx = -0.5 if choice_row[r] == 0 else 0.5
        x += dx
        # short nudge after deflection
        xs.append(x)
        ys.append(peg_y - 0.3)

    # drop into final bin
    xs.append(x)
    ys.append(-NUM_ROWS - 0.5)
    return np.array(xs), np.array(ys)

all_paths = []
for i in range(NUM_BALLS):
    xs, ys = make_path(choices[i], i)
    all_paths.append((xs, ys))

PATH_LEN = len(all_paths[0][0])

# ── Peg positions ──────────────────────────────────────────────────────────────
peg_xs, peg_ys = [], []
for row in range(NUM_ROWS):
    for col in range(row + 1):
        peg_xs.append(col - row / 2)
        peg_ys.append(-row)
peg_xs = np.array(peg_xs)
peg_ys = np.array(peg_ys)

# ── Figure layout ──────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(9, 11), facecolor=BG)
gs  = GridSpec(2, 1, figure=fig, height_ratios=[2.2, 1], hspace=0.08)

ax_board = fig.add_subplot(gs[0])
ax_hist  = fig.add_subplot(gs[1])

for ax in (ax_board, ax_hist):
    ax.set_facecolor(PANEL_BG)
    for spine in ax.spines.values():
        spine.set_edgecolor("#2a2a2a")

# Board
ax_board.set_xlim(-NUM_ROWS / 2 - 1.2, NUM_ROWS / 2 + 1.2)
ax_board.set_ylim(-NUM_ROWS - 1.2, 2.2)
ax_board.set_aspect("equal")
ax_board.axis("off")

for y in range(-NUM_ROWS, 1):
    ax_board.axhline(y, color=GRID_COL, lw=0.4, zorder=0)

ax_board.text(
    0, 2.0, "GALTON BOARD  ·  n = 1000  ·  rows = 12",
    ha="center", va="top", fontsize=9,
    color="#555", fontfamily="monospace"
)

ax_board.scatter(
    peg_xs, peg_ys, s=55, color=PEG_COLOR, zorder=4,
    edgecolors=PEG_GLOW, linewidths=0.6
)

num_bins  = NUM_ROWS + 1
bin_edges = np.arange(num_bins) - NUM_ROWS / 2
for bx in bin_edges:
    ax_board.axvline(bx - 0.5, ymin=0.01, ymax=0.065,
                     color="#2a2a2a", lw=1, zorder=2)

# ── Histogram ──────────────────────────────────────────────────────────────────
bin_counts = np.zeros(num_bins, dtype=int)

ax_hist.set_xlim(-NUM_ROWS / 2 - 1.2, NUM_ROWS / 2 + 1.2)
ax_hist.set_ylim(0, NUM_BALLS * 0.35)
ax_hist.set_xlabel("bin", fontsize=8, labelpad=6)
ax_hist.set_ylabel("count", fontsize=8, labelpad=6)
ax_hist.yaxis.grid(True, color=GRID_COL, lw=0.6)
ax_hist.set_axisbelow(True)

bars = ax_hist.bar(
    bin_edges, bin_counts,
    width=0.82, color=BAR_FACE,
    edgecolor=BAR_EDGE, linewidth=0.8
)

mu      = NUM_ROWS / 2
sigma   = np.sqrt(NUM_ROWS * 0.25)
x_curve = np.linspace(-NUM_ROWS / 2 - 1, NUM_ROWS / 2 + 1, 300)

curve_line, = ax_hist.plot([], [], color=CURVE_COL, lw=1.6,
                            linestyle="--", alpha=0.85, zorder=5)

counter = ax_board.text(
    NUM_ROWS / 2 + 1.1, 2.0, "0 / 1000",
    ha="right", va="top", fontsize=9,
    color=TEXT_COL, fontfamily="monospace"
)

active_scatter = ax_board.scatter(
    [], [], s=55,
    color=BALL_COLOR, edgecolors=BALL_EDGE,
    linewidths=0.6, zorder=6
)

trail_scatter = ax_board.scatter(
    [], [], s=18,
    color=BALL_COLOR, alpha=0.25, zorder=5
)

# ── Animation state ────────────────────────────────────────────────────────────
state = {
    "landed":    0,
    "in_flight": [],
    "frame":     0,
}

def update(_):
    state["frame"] += 1

    # Launch new balls
    for _ in range(BALLS_PER_FRAME):
        if state["landed"] + len(state["in_flight"]) < NUM_BALLS:
            next_idx = state["landed"] + len(state["in_flight"])
            state["in_flight"].append([next_idx, 0])

    # Advance in-flight balls
    still_flying = []
    for ball in state["in_flight"]:
        ball[1] += 1
        if ball[1] >= PATH_LEN:
            bin_counts[bins[ball[0]]] += 1
            state["landed"] += 1
        else:
            still_flying.append(ball)
    state["in_flight"] = still_flying

    # Gather positions
    ball_xs, ball_ys = [], []
    trail_xs, trail_ys = [], []
    for ball_idx, pf in state["in_flight"]:
        px, py = all_paths[ball_idx]
        ball_xs.append(px[pf])
        ball_ys.append(py[pf])
        for t in range(1, TRAIL_LENGTH):
            tp = pf - t
            if tp >= 0:
                trail_xs.append(px[tp])
                trail_ys.append(py[tp])

    if ball_xs:
        active_scatter.set_offsets(np.column_stack([ball_xs, ball_ys]))
    else:
        active_scatter.set_offsets(np.empty((0, 2)))

    if trail_xs:
        trail_scatter.set_offsets(np.column_stack([trail_xs, trail_ys]))
    else:
        trail_scatter.set_offsets(np.empty((0, 2)))

    # Update histogram bars
    for bar, count in zip(bars, bin_counts):
        bar.set_height(count)

    # Update normal curve
    total = state["landed"]
    if total > 10:
        pdf_vals = (
            (1 / (sigma * np.sqrt(2 * np.pi)))
            * np.exp(-0.5 * ((x_curve - mu) / sigma) ** 2)
        )
        curve_line.set_data(x_curve, pdf_vals * total)

    counter.set_text(f"{state['landed']} / {NUM_BALLS}")

    if state["landed"] >= NUM_BALLS and not state["in_flight"]:
        ani.event_source.stop()

    return active_scatter, trail_scatter, curve_line, counter, *bars

ani = animation.FuncAnimation(
    fig, update,
    frames=NUM_BALLS * 10,
    interval=INTERVAL_MS,
    blit=False
)

plt.tight_layout(pad=1.5)
plt.show()
