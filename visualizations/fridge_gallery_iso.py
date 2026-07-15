"""Isometric gallery of the 43 distinct fridge base models: orthographic
projection at the true isometric angle, with recessive 3D axes/grid so
shape and relative size are comparable across panels."""
import os, sys, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import MultipleLocator

DATA = "/home/sammathew/Code/FixIt/data/fridge/shapes"
BODY = "#b6b4ac"
SLOTS = ["#2a78d6", "#1baf7a", "#eda100", "#008300"]  # validated categorical, fixed order
INK, SEC, MUT, GRID, BASE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
ISO_ELEV = 35.264  # atan(1/sqrt(2)) — true isometric
ISO_AZIM = -45

def reps():
    out = {}
    for split in ["train_before", "test_before"]:
        for d in sorted(os.listdir(f"{DATA}/{split}")):
            if d.endswith("_functional"):
                out.setdefault(d.split("+")[0], (split, d))
    return dict(sorted(out.items(), key=lambda kv: int(kv[0])))

def style_axes(ax):
    ax.set_proj_type("ortho")
    ax.view_init(elev=ISO_ELEV, azim=ISO_AZIM)
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.set_pane_color((1, 1, 1, 0))
        axis._axinfo["grid"].update(color=GRID, linewidth=0.4)
        axis.line.set_color(BASE)
        axis.line.set_linewidth(0.6)
        axis.set_major_locator(MultipleLocator(0.5))
    ax.tick_params(labelsize=4.5, colors=MUT, pad=-3)

def draw(ax, split, d):
    pts = np.load(f"{DATA}/{split}/{d}/new/0.npy")[:2048]
    lab = np.load(f"{DATA}/{split}/{d}/label.npy")[:2048]
    ids, counts = np.unique(lab, return_counts=True)
    order = ids[np.argsort(-counts)]
    colors = np.empty(len(pts), dtype=object)
    colors[lab == order[0]] = BODY
    for k, pid in enumerate(order[1:]):
        colors[lab == pid] = SLOTS[k % len(SLOTS)]
    ax.scatter(pts[:, 0], pts[:, 1], pts[:, 2], c=list(colors), s=2.2, linewidths=0, depthshade=False)
    ext = pts.max(0) - pts.min(0); mid = (pts.max(0) + pts.min(0)) / 2; r = ext.max() / 2 * 1.02
    ax.set_xlim(mid[0]-r, mid[0]+r); ax.set_ylim(mid[1]-r, mid[1]+r); ax.set_zlim(mid[2]-r, mid[2]+r)
    ax.set_box_aspect((1, 1, 1))
    style_axes(ax)
    return len(ids)

def main(out="all_fridges_iso.png", ncols=7):
    items = list(reps().items())
    nrows = -(-len(items) // ncols)
    fig = plt.figure(figsize=(ncols * 3.0, nrows * 3.2), facecolor="#fcfcfb")
    for i, (sid, (split, d)) in enumerate(items):
        ax = fig.add_subplot(nrows, ncols, i + 1, projection="3d")
        ax.set_facecolor("#fcfcfb")
        npart = draw(ax, split, d)
        tag = "test" if split.startswith("test") else "train"
        ax.set_title(f"{sid} · {npart} parts · {tag}",
                     fontsize=9, color=(INK if tag == "test" else SEC),
                     fontweight=("bold" if tag == "test" else "normal"), pad=0)
    handles = [Line2D([], [], marker="o", ls="", color=BODY, label="largest part")] + [
        Line2D([], [], marker="o", ls="", color=c, label=f"part {i+1} (by size)")
        for i, c in enumerate(SLOTS)]
    fig.legend(handles=handles, loc="lower center", ncol=5, frameon=False, fontsize=10)
    fig.suptitle("FixIt fridges — 43 base models, isometric view (orthographic, grid = 0.5 units)",
                 fontsize=14, color=INK, y=0.995)
    fig.tight_layout(rect=(0, 0.015, 1, 0.985))
    fig.savefig(out, dpi=150, facecolor="#fcfcfb")
    print("saved", out, f"{len(items)} panels")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "all_fridges_iso.png")
