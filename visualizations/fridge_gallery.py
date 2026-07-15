"""Gallery of the 43 distinct fridge base models (one functional variant each),
points colored by GT part instance: largest part (body) in neutral gray,
remaining parts in validated categorical slots."""
import os, sys, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

DATA = "/home/sammathew/Code/FixIt/data/fridge/shapes"
BODY = "#b6b4ac"                       # recessive context (muted, between gridline/muted ink)
SLOTS = ["#2a78d6", "#1baf7a", "#eda100", "#008300"]  # validated categorical, fixed order
INK, SEC = "#0b0b0b", "#52514e"

def reps():
    out = {}
    for split in ["train_before", "test_before"]:
        for d in sorted(os.listdir(f"{DATA}/{split}")):
            if d.endswith("_functional"):
                sid = d.split("+")[0]
                out.setdefault(sid, (split, d))
    return dict(sorted(out.items(), key=lambda kv: int(kv[0])))

def draw(ax, split, d):
    pts = np.load(f"{DATA}/{split}/{d}/new/0.npy")[:2048]
    lab = np.load(f"{DATA}/{split}/{d}/label.npy")[:2048]
    ids, counts = np.unique(lab, return_counts=True)
    order = ids[np.argsort(-counts)]           # body first, then parts by size
    colors = np.empty(len(pts), dtype=object)
    colors[lab == order[0]] = BODY
    for k, pid in enumerate(order[1:]):
        colors[lab == pid] = SLOTS[k % len(SLOTS)]
    ax.scatter(pts[:, 0], pts[:, 1], pts[:, 2], c=list(colors), s=2.0, linewidths=0, depthshade=False)
    # equal aspect
    ext = pts.max(0) - pts.min(0); mid = (pts.max(0) + pts.min(0)) / 2; r = ext.max() / 2
    ax.set_xlim(mid[0]-r, mid[0]+r); ax.set_ylim(mid[1]-r, mid[1]+r); ax.set_zlim(mid[2]-r, mid[2]+r)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=18, azim=-55)
    ax.set_axis_off()
    return len(ids)

def main(limit=None, out="fridge_probe.png", ncols=7):
    R = reps()
    items = list(R.items())[:limit] if limit else list(R.items())
    n = len(items)
    nrows = -(-n // ncols)
    fig = plt.figure(figsize=(ncols * 2.6, nrows * 2.9), facecolor="#fcfcfb")
    for i, (sid, (split, d)) in enumerate(items):
        ax = fig.add_subplot(nrows, ncols, i + 1, projection="3d")
        ax.set_facecolor("#fcfcfb")
        npart = draw(ax, split, d)
        tag = "test" if split.startswith("test") else "train"
        ax.set_title(f"{sid} · {npart} parts · {tag}",
                     fontsize=8, color=(INK if tag == "test" else SEC),
                     fontweight=("bold" if tag == "test" else "normal"), pad=0)
    handles = [Line2D([], [], marker="o", ls="", color=BODY, label="body (largest part)")] + [
        Line2D([], [], marker="o", ls="", color=c, label=f"part {i+1} (by size)")
        for i, c in enumerate(SLOTS)]
    fig.legend(handles=handles, loc="lower center", ncol=5, frameon=False, fontsize=9)
    fig.suptitle("FixIt fridges — the 43 distinct base models (one undistorted functional variant each, frame 0)",
                 fontsize=13, color=INK, y=0.995)
    fig.tight_layout(rect=(0, 0.02, 1, 0.985))
    fig.savefig(out, dpi=150, facecolor="#fcfcfb")
    print("saved", out, f"{n} panels")

if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    out = sys.argv[2] if len(sys.argv) > 2 else "fridge_probe.png"
    main(limit, out)
