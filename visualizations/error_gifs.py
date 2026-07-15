"""Four GIFs of the same base fridge (10143): one variant per error type
(scale / translate / rotate) plus a functional one. Each animates the 10-frame
interaction video; parts colored as in the galleries, interacting points in red."""
import os, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.animation import FuncAnimation, PillowWriter

DATA = "/home/sammathew/Code/FixIt/data/fridge/shapes/train_before"
OUT = "/tmp/claude-1003/-home-sammathew-Code-FixIt/145f1fde-347d-47c8-9823-75201e8414c0/scratchpad"
BODY = "#b6b4ac"
SLOTS = ["#2a78d6", "#1baf7a", "#eda100", "#008300"]
IPT = "#e34948"  # interacting points
INK, SEC = "#0b0b0b", "#52514e"

SAMPLES = [
    ("10143+10_malfunctional", "scale error",     "GT fix: scale part2 -z 1.88 (door shrunk to ~53%)", "7_error_scale.gif"),
    ("10143+17_malfunctional", "translate error", "GT fix: translate part1 -x 0.25 (door offset)",      "7_error_translate.gif"),
    ("10143+6_malfunctional",  "rotate error",    "GT fix: rotate part2 +y 0.47 (door tilted ~27°)",    "7_error_rotate.gif"),
    ("10143+5_functional",     "no error",        "functional — door closes cleanly",                   "7_no_error.gif"),
]

# consistent part->color mapping taken from the functional variant's size ranks
ref_lab = np.load(f"{DATA}/10143+5_functional/label.npy")[:2048]
ids, counts = np.unique(ref_lab, return_counts=True)
order = ids[np.argsort(-counts)]
CMAP = {order[0]: BODY, **{pid: SLOTS[k % len(SLOTS)] for k, pid in enumerate(order[1:])}}

def load(sample):
    """Frames are independent FPS samples (no cross-frame point correspondence);
    label.npy labels frame 0 only. Propagate labels t -> t+1 via GT flow:
    label(p_{t+1,j}) = label of nearest (p_t + flow_t)."""
    from scipy.spatial import cKDTree
    frames = np.stack([np.load(f"{DATA}/{sample}/new/{t}.npy") for t in range(10)])
    flows = [np.load(f"{DATA}/{sample}/flow/{t}.npy") for t in range(9)]
    labs = [np.load(f"{DATA}/{sample}/label.npy")[:2048]]
    for t in range(9):
        moved = frames[t, :2048] + flows[t][:2048]
        _, nn = cKDTree(moved).query(frames[t + 1, :2048])
        labs.append(labs[t][nn])
    colors = [np.array([CMAP.get(l, SLOTS[0]) for l in lab], dtype=object) for lab in labs]
    return frames, colors

def make_gif(sample, err, sub, fname):
    frames, colors = load(sample)
    allp = frames.reshape(-1, 3)
    mid = (allp.max(0) + allp.min(0)) / 2
    r = (allp.max(0) - allp.min(0)).max() / 2 * 1.02

    fig = plt.figure(figsize=(5.4, 5.9), facecolor="#fcfcfb")
    ax = fig.add_subplot(111, projection="3d")

    def draw(t):
        ax.clear()
        ax.set_facecolor("#fcfcfb")
        ax.set_proj_type("ortho")
        ax.view_init(elev=35.264, azim=-45)
        obj, ip = frames[t, :2048], frames[t, 2048:]
        ax.scatter(obj[:, 0], obj[:, 1], obj[:, 2], c=list(colors[t]), s=2.6, linewidths=0, depthshade=False)
        ax.scatter(ip[:, 0], ip[:, 1], ip[:, 2], c=IPT, s=26, linewidths=0, depthshade=False)
        ax.set_xlim(mid[0]-r, mid[0]+r); ax.set_ylim(mid[1]-r, mid[1]+r); ax.set_zlim(mid[2]-r, mid[2]+r)
        ax.set_box_aspect((1, 1, 1))
        ax.set_axis_off()
        ax.set_title(f"fridge 10143 — {err}\n{sub}", fontsize=11, color=INK, pad=2)
        ax.text2D(0.5, 0.02, f"frame {t+1}/10", transform=ax.transAxes,
                  ha="center", fontsize=10, color=SEC)

    seq = list(range(10)) + [9, 9, 9]          # hold the final state
    anim = FuncAnimation(fig, draw, frames=seq)
    anim.save(os.path.join(OUT, fname), writer=PillowWriter(fps=2.5))
    plt.close(fig)
    print("saved", fname)

for s in SAMPLES:
    make_gif(*s)

# QA contact sheet: 4 samples x 4 key frames
fig, axes = plt.subplots(4, 4, figsize=(12, 13), facecolor="#fcfcfb",
                         subplot_kw={"projection": "3d"})
for row, (sample, err, sub, _) in enumerate(SAMPLES):
    frames, colors = load(sample)
    allp = frames.reshape(-1, 3)
    mid = (allp.max(0) + allp.min(0)) / 2
    r = (allp.max(0) - allp.min(0)).max() / 2 * 1.02
    for col, t in enumerate([0, 3, 6, 9]):
        ax = axes[row][col]
        ax.set_facecolor("#fcfcfb"); ax.set_proj_type("ortho"); ax.view_init(elev=35.264, azim=-45)
        obj, ip = frames[t, :2048], frames[t, 2048:]
        ax.scatter(obj[:, 0], obj[:, 1], obj[:, 2], c=list(colors[t]), s=1.6, linewidths=0, depthshade=False)
        ax.scatter(ip[:, 0], ip[:, 1], ip[:, 2], c=IPT, s=14, linewidths=0, depthshade=False)
        ax.set_xlim(mid[0]-r, mid[0]+r); ax.set_ylim(mid[1]-r, mid[1]+r); ax.set_zlim(mid[2]-r, mid[2]+r)
        ax.set_box_aspect((1, 1, 1)); ax.set_axis_off()
        if col == 0:
            ax.text2D(-0.05, 0.5, err, transform=ax.transAxes, rotation=90,
                      va="center", fontsize=11, color=INK, fontweight="bold")
        if row == 0:
            ax.set_title(f"frame {t+1}", fontsize=11, color=SEC)
fig.suptitle("QA sheet — fridge 10143, one variant per error type (rows), key frames (cols); red = interacting points",
             fontsize=13, color=INK)
fig.tight_layout(rect=(0.01, 0, 1, 0.97))
fig.savefig(os.path.join(OUT, "qa_error_sheet.png"), dpi=110, facecolor="#fcfcfb")
print("saved qa_error_sheet.png")
