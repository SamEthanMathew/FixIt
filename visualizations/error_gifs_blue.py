"""Error-type GIFs, monochrome edition: all 2048 object points in blue,
16 interacting points in red. One sample per error type across different
fridge models, plus a functional one."""
import os, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

DATA = "/home/sammathew/Code/FixIt/data/fridge/shapes"
OUT = "/tmp/claude-1003/-home-sammathew-Code-FixIt/145f1fde-347d-47c8-9823-75201e8414c0/scratchpad"
BLUE, IPT = "#2a78d6", "#e34948"
INK, SEC = "#0b0b0b", "#52514e"

SAMPLES = [
    ("train_before", "12055+7_malfunctional",  "fridge 12055 — scale error (single door)",
     "GT fix: scale +z 1.98 — the moving door is shrunk to ~51% height", "7_error_scale.gif"),
    ("train_before", "10944+9_malfunctional",  "fridge 10944 — translate error (single door)",
     "GT fix: translate +z 0.30 — the moving door is shifted down 0.30", "7_error_translate.gif"),
    ("train_before", "10144+13_malfunctional", "fridge 10144 — rotate error",
     "GT fix: rotate part1 -y 0.47 (door tilted ~27°)",     "7_error_rotate.gif"),
    ("train_before", "10068+5_functional",     "fridge 10068 — no error",
     "functional — doors close cleanly",                    "7_no_error.gif"),
]

def make_gif(split, sample, title, sub, fname):
    frames = np.stack([np.load(f"{DATA}/{split}/{sample}/new/{t}.npy") for t in range(10)])
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
        obj, ip = frames[t, 16:], frames[t, :16]
        ax.scatter(obj[:, 0], obj[:, 1], obj[:, 2], c=BLUE, s=2.6, linewidths=0, depthshade=False)
        ax.scatter(ip[:, 0], ip[:, 1], ip[:, 2], c=IPT, s=26, linewidths=0, depthshade=False)
        ax.set_xlim(mid[0]-r, mid[0]+r); ax.set_ylim(mid[1]-r, mid[1]+r); ax.set_zlim(mid[2]-r, mid[2]+r)
        ax.set_box_aspect((1, 1, 1))
        ax.set_axis_off()
        ax.set_title(f"{title}\n{sub}", fontsize=11, color=INK, pad=2)
        ax.text2D(0.5, 0.02, f"frame {t+1}/10", transform=ax.transAxes,
                  ha="center", fontsize=10, color=SEC)

    seq = list(range(10)) + [9, 9, 9]
    anim = FuncAnimation(fig, draw, frames=seq)
    anim.save(os.path.join(OUT, fname), writer=PillowWriter(fps=2.5))
    plt.close(fig)
    print("saved", fname)

for s in SAMPLES:
    make_gif(*s)

# QA sheet
fig, axes = plt.subplots(4, 4, figsize=(12, 13), facecolor="#fcfcfb",
                         subplot_kw={"projection": "3d"})
for row, (split, sample, title, sub, _) in enumerate(SAMPLES):
    frames = np.stack([np.load(f"{DATA}/{split}/{sample}/new/{t}.npy") for t in range(10)])
    allp = frames.reshape(-1, 3)
    mid = (allp.max(0) + allp.min(0)) / 2
    r = (allp.max(0) - allp.min(0)).max() / 2 * 1.02
    for col, t in enumerate([0, 3, 6, 9]):
        ax = axes[row][col]
        ax.set_facecolor("#fcfcfb"); ax.set_proj_type("ortho"); ax.view_init(elev=35.264, azim=-45)
        obj, ip = frames[t, 16:], frames[t, :16]
        ax.scatter(obj[:, 0], obj[:, 1], obj[:, 2], c=BLUE, s=1.6, linewidths=0, depthshade=False)
        ax.scatter(ip[:, 0], ip[:, 1], ip[:, 2], c=IPT, s=14, linewidths=0, depthshade=False)
        ax.set_xlim(mid[0]-r, mid[0]+r); ax.set_ylim(mid[1]-r, mid[1]+r); ax.set_zlim(mid[2]-r, mid[2]+r)
        ax.set_box_aspect((1, 1, 1)); ax.set_axis_off()
        if col == 0:
            ax.text2D(-0.05, 0.5, title.split('— ')[1], transform=ax.transAxes, rotation=90,
                      va="center", fontsize=11, color=INK, fontweight="bold")
        if row == 0:
            ax.set_title(f"frame {t+1}", fontsize=11, color=SEC)
fig.suptitle("QA sheet — monochrome error GIFs: 12055 scale · 10944 translate · 10144 rotate · 10068 functional",
             fontsize=13, color=INK)
fig.tight_layout(rect=(0.01, 0, 1, 0.97))
fig.savefig(os.path.join(OUT, "qa_error_sheet_blue.png"), dpi=110, facecolor="#fcfcfb")
print("saved qa_error_sheet_blue.png")
