#!/usr/bin/env python
"""
Quantisation grids for the repair action space.

The agent emits a magnitude for each action type; the environment SNAPS that magnitude onto a
discrete grid before applying it (mirroring the {value_grid}/{angle_grid}/{scale_grid} in the
prompt). Corruptions are also drawn ON these grids, so every break's exact inverse is itself an
on-grid action -- the task is solvable by exactly one quantised (type, part, axis, value).

Grid choices:
  TRANSLATE  linear, 0.01 m steps (metres). The signed displacement along one part axis.
  ROTATE     linear, 5 deg steps (degrees). The angle about the part's centroid.
  SCALE      LOG-spaced and RECIPROCAL-SYMMETRIC: f_k = exp(k * SCALE_LOG_STEP). This is what
             makes scale invertible on-grid -- if a corruption uses factor f_k = exp(k*d), its
             inverse is 1/f_k = exp(-k*d) = f_{-k}, which is another grid point. A linear scale
             grid would NOT contain the reciprocals and the inverse would be off-grid.
"""
import math

# ------------------------------------------------------------------ translate (metres)
TRANSLATE_STEP = 0.01
_TRANSLATE_MAX = 0.40
VALUE_GRID = [round(TRANSLATE_STEP * k, 4)
              for k in range(1, int(round(_TRANSLATE_MAX / TRANSLATE_STEP)) + 1)]

# ------------------------------------------------------------------ rotate (degrees)
ANGLE_STEP = 5.0
_ANGLE_MAX = 60.0
ANGLE_GRID = [ANGLE_STEP * k for k in range(1, int(round(_ANGLE_MAX / ANGLE_STEP)) + 1)]

# ------------------------------------------------------------------ scale (multiplier)
SCALE_LOG_STEP = 0.10             # ln-spacing between adjacent scale factors
_SCALE_K_MAX = 6                  # f in [exp(-0.6), exp(0.6)] ~ [0.549, 1.822]
SCALE_GRID = [math.exp(SCALE_LOG_STEP * k)
              for k in range(-_SCALE_K_MAX, _SCALE_K_MAX + 1) if k != 0]


def snap(value, grid):
    """Return the grid entry nearest to `value` (grids hold POSITIVE magnitudes; sign is
    preserved for the linear grids and reciprocals are separate entries for the scale grid)."""
    if not grid:
        return value
    if _is_scale_grid(grid):
        return min(grid, key=lambda g: abs(math.log(value) - math.log(g)))
    sign = -1.0 if value < 0 else 1.0
    mag = min(grid, key=lambda g: abs(abs(value) - g))
    return sign * mag


def clamp_to_grid(value, grid):
    """Snap, then clamp into the grid's representable range."""
    if not grid:
        return value
    snapped = snap(value, grid)
    lo, hi = min(grid), max(grid)
    if _is_scale_grid(grid):
        return min(max(snapped, lo), hi)
    sign = -1.0 if snapped < 0 else 1.0
    return sign * min(max(abs(snapped), lo), hi)


def on_grid(value, grid, rel_tol=1e-6):
    """Is `value` (or its magnitude) exactly a grid point?"""
    if _is_scale_grid(grid):
        return any(math.isclose(value, g, rel_tol=rel_tol) for g in grid)
    return any(math.isclose(abs(value), g, rel_tol=rel_tol) for g in grid)


def _is_scale_grid(grid):
    # The scale grid is the only one straddling 1.0 (it holds reciprocal pairs). TRANSLATE is all
    # < 1 (max 0.40) and ANGLE is all > 1 (min 5.0), so neither straddles.
    return any(g < 1.0 for g in grid) and any(g > 1.0 for g in grid)


def grid_for(ctype):
    return {"translate": VALUE_GRID, "rotate": ANGLE_GRID, "scale": SCALE_GRID}[ctype]


if __name__ == "__main__":
    print(f"VALUE_GRID  ({len(VALUE_GRID)}): {VALUE_GRID[:5]} ... {VALUE_GRID[-1]}")
    print(f"ANGLE_GRID  ({len(ANGLE_GRID)}): {ANGLE_GRID}")
    print(f"SCALE_GRID  ({len(SCALE_GRID)}):")
    for g in SCALE_GRID:
        print(f"    {g:.4f}   1/f={1.0/g:.4f}   1/f on-grid: {on_grid(1.0/g, SCALE_GRID)}")
    # reciprocal-symmetry assertion
    assert all(on_grid(1.0 / g, SCALE_GRID) for g in SCALE_GRID), "scale grid not reciprocal-symmetric"
    print("OK: scale grid is reciprocal-symmetric")
