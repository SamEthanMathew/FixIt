#!/usr/bin/env python
"""
The Text-FixIt evaluation contract.

    A repair SUCCEEDS iff the repaired part matches the original part's state within a
    tolerance tau, AND the repaired door still physically closes, AND no two parts of the
    fridge interpenetrate more than the healthy fridge already does.

    Generation guarantees every corruption displaces the part by MORE than tau (with margin),
    so every instance is unambiguously broken and unambiguously fixable.

tau is relative to the part (geom.TAU_FRAC * door bbox diagonal, ~20 mm on a typical 800 mm
door), so one constant works across large/small and 1-door/3-door fridges.

WHY THESE METHODS -- what was tried on this data and what happened:

  per-vertex displacement, exact correspondence  ADOPTED. Meshes are never edited (a fix only
      changes URDF transform attributes), so candidate and healthy doors have identical vertices
      in identical order. Exact, dense, always defined; an 0.080 m commanded shift measures 80.0 mm.
  Chamfer / Hausdorff                            REJECTED. Under-measures in-plane shifts -- a flat
      door slid within its own plane maps onto its own surface, scoring genuine breaks 0.66-0.80.
  6-DoF link pose distance                       Reported alongside for interpretability only
      (mm + deg); does not capture scale.
  volumetric IoU                                 Deferred: expensive, resolution-sensitive, and adds
      no signal the correspondence metric lacks.
  kinematic CLOSING sweep                        ADOPTED as the physical gate. Detects 28% of breaks
      (rotate 40% / translate 29% / scale 15%) -- those pushed INTO the body.
  kinematic OPENING sweep                        FALSIFIED. A displaced door swings into free space
      and never collides; broken variants scored identically to healthy.
  part-collision, all-pair, relative-to-healthy  ADOPTED as a third gate. At closed pose, deepest
      interpenetration over ALL distinct part pairs, compared to the same fridge's healthy baseline
      (relative because 7/43 healthy fridges self-overlap up to 57 mm at rest). Catches door<->door
      and door<->body overlaps; overlaps the closing gate for single-door breaks but generalises to
      multi-part corruptions and gives an interpretable failure ("door_1_right <-> body").
  dynamic motored rollout                        Deferred: needs force/friction tuning, non-deterministic.
  seal-gap (getClosestPoints door<->frame)       BUILT AND REJECTED. Measured door<->body closest
      distance at closed pose, hoping to catch doors pulled AWAY from the frame that closing misses.
      It fired on only 1% of instances and added nothing over closing (23% vs 22% combined). Reason:
      the hinge is never moved, so the door's hinge edge always stays near the frame -> closest
      distance stays ~0 no matter how the door is shifted/scaled.

CONCLUSION on physical coverage: no cheap kinematic test detects more than ~22% of these corruptions,
because most breaks (in-plane offsets, overhang scaling) leave a door that still swings and still nearly
touches the frame. Geometry (deviation vs tau) is therefore the always-defined workhorse; the closing
gate adds a hard physical guarantee only on the ~22% `physics_verified` subset where the door jams shut.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import geom                                  # noqa: E402
from close_eval import evaluate_closing      # noqa: E402
from part_collision import evaluate_part_collision   # noqa: E402


def evaluate_repair(candidate_urdf, healthy_urdf, joint_name, link_name, client=None):
    """Evaluate a candidate repair against the contract.

    Returns geometry (deviation/tau/within_tol), physics (closes), part-collision (collides), and
    PASS = within_tol AND closes AND not collides.
    """
    g = geom.geometric_score(candidate_urdf, healthy_urdf, joint_name, link_name, client=client)
    closes = evaluate_closing(candidate_urdf, joint_name, client=client)
    pc = evaluate_part_collision(candidate_urdf, healthy_urdf, client=client)
    out = {
        "deviation_mm": round(g["deviation_mm"], 3),
        "tau_mm": round(g["tau_mm"], 3),
        "within_tol": g["within_tol"],
        "score": round(g["score"], 4),
        "closes": closes["closes"],
        "closed_angle_deg": round(closes["closed_angle_deg"], 1),
        "collides": pc["collides"],
        "collision_excess_mm": pc["excess_mm"],
        "collision_pair": pc["worst_pair_names"],
    }
    out["PASS"] = bool(out["within_tol"] and out["closes"] and not out["collides"])
    return out


if __name__ == "__main__":
    import argparse
    import json

    ap = argparse.ArgumentParser(description="Evaluate a candidate repair against the contract.")
    ap.add_argument("candidate_urdf")
    ap.add_argument("joint")
    ap.add_argument("link")
    ap.add_argument("--healthy", default=None,
                    help="healthy reference URDF (default: mobility.urdf beside the candidate)")
    args = ap.parse_args()
    healthy = args.healthy or os.path.join(os.path.dirname(args.candidate_urdf), "mobility.urdf")
    print(json.dumps(evaluate_repair(args.candidate_urdf, healthy, args.joint, args.link), indent=2))
