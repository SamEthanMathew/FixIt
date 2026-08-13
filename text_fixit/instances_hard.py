#!/usr/bin/env python
"""
Generate the HARD benchmark: composite (multi-fault) instances + a matched single-fault control.

Why this exists (see docs/EXPERIMENT_2026-08-09_composite_faults.md): on the single-fault task the
strong models saturate, and they solve it in a MEDIAN OF ONE simulate -- the closed loop is barely
load-bearing. A composite break needs an ordered SEQUENCE of repairs, which makes planning, credit
assignment and feedback necessary rather than optional.

Two sets, both generated under the same hardening knobs (off-grid magnitudes, tau_frac 0.015,
part table with the fixable column hidden, harder renders -- the last two are runtime flags):

  composite (25) : exactly 3 sub-faults per instance, one translate + one rotate + one scale.
                     10 x composite_1door -- all 3 on a single door
                     15 x composite_2door -- the 3 split across two doors (2 + 1)
                   Sub-fault COUNT is held at 3 in both arms, so the only thing that differs is the
                   diagnosis/assignment burden -- a clean ablation.
  control   (25) : one sub-fault, same knobs. This is what separates "the knobs got harder" from
                   "composition got harder".

Every instance in a set uses a DISTINCT fridge base.

THE INVERTIBILITY ARGUMENT (the thing that keeps oracle at 100%):
each edit is exactly invertible given its pivot, and canonical.part_centroid / canonical.scale_pivot
are recomputable from the current geometry. So for a break applied as [c1, c2, c3],

    gt_fix_sequence = [inv(c3), inv(c2), inv(c1)]        # REVERSED, each inverted

Applied in that order, each inverse acts on exactly the state its forward op produced -- so the
centroid/pivot recomputed at that moment equals the one the break used, and the fix is expressible
in the agent's parameter-free action space with no hidden geometry. Asserted per instance below, not
assumed.

    FIXIT_TAU_FRAC=0.015 python text_fixit/instances_hard.py
"""
import argparse
import itertools
import json
import os
import random
import sys

import pybullet as p

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corruption as corr          # noqa: E402
import geom                        # noqa: E402
from close_eval import evaluate_closing        # noqa: E402
from evaluation import evaluate_repair_multi   # noqa: E402
from parts import corruptible_parts            # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets", "partnet_mobility")
IDS = os.path.join(HERE, "data", "fridge_ids.json")
CTYPES = ("translate", "rotate", "scale")

N_TWO_DOOR = 15
N_ONE_DOOR = 10
N_CONTROL = 25
TARGET_TAU_FRAC = 0.015


# --------------------------------------------------------------------------- shape inventory

def usable_doors(base, cid):
    """Doors of `base` that pass gate 3 (the HEALTHY door must actually close -- otherwise no repair,
    however perfect, can satisfy the contract). Returns [] if the shape is missing from disk."""
    urdf = os.path.join(ASSETS, base, "mobility.urdf")
    if not os.path.isfile(urdf):
        return []
    return [pt for pt in corruptible_parts(urdf)
            if evaluate_closing(urdf, pt["joint"], client=cid)["closes"]]


def inventory(cid):
    """{base: [usable door parts]} over every declared shape, plus the split lookup."""
    ids = json.load(open(IDS))
    split_of = {b: "train" for b in ids["train"]}
    split_of.update({b: "test" for b in ids["test"]})
    inv = {}
    for base in ids["train"] + ids["test"]:
        doors = usable_doors(base, cid)
        if doors:
            inv[base] = doors
    return inv, split_of


# --------------------------------------------------------------------------- composite build

def _apply_chain(healthy_urdf, specs, out_name):
    """Apply `specs` in order, healthy -> broken, returning the final URDF path.

    Intermediates are written next to the meshes (relative textured_objs/ paths must resolve) and
    removed as we go; only the last one survives.
    """
    cur, tmps = healthy_urdf, []
    for i, spec in enumerate(specs):
        name = out_name if i == len(specs) - 1 else f"_chain{i}_{out_name}"
        cur = corr.apply(cur, spec, name)
        if i < len(specs) - 1:
            tmps.append(cur)
    for t in tmps:
        if os.path.exists(t):
            os.remove(t)
    return cur


def oracle_roundtrip(broken, healthy, faults, gt_seq, cid, tag="rt"):
    """Replay the GT sequence through the AGENT'S OWN PATH and score the result.

    Each spec is rendered as an action string, parsed back (which DROPS centroid/pivot and clamps
    the value), and re-injected with canonical params RECOMPUTED from the intermediate state -- byte
    for byte what env.py does for the oracle.

    This is the real "solvable in the agent's action space" test. Replaying the STORED specs only
    proves the break is mathematically invertible; it does NOT prove the inverse is expressible
    without privileged parameters, which is the property the whole action space rests on.
    """
    import action_parser
    from env import _inject_canonical
    from part_table import build_part_table

    _, id_map = build_part_table(broken)
    pid_of = {pt["link"]: pid for pid, pt in id_map.items()}
    cur, tmps = broken, []
    for i, f in enumerate(gt_seq):
        call = action_parser.format_call(f["spec"], pid_of[f["link"]])
        res = action_parser.parse(f"<act>COMMIT {call}</act>", id_map, multi=True)
        if not res["valid"]:
            return {"PASS": False, "deviation_mm": float("inf"), "parse_error": res["error"]}
        spec = _inject_canonical(res["actions"][0]["spec"], cur)
        nxt = corr.apply(cur, spec, f"_{tag}{i}_{os.path.basename(broken)}")
        if cur != broken:
            tmps.append(cur)
        cur = nxt
    ev = evaluate_repair_multi(cur, healthy, faults, client=cid)
    for t in tmps + [cur]:
        if os.path.exists(t) and t != broken:
            os.remove(t)
    return ev


def build_composite(base, doors, split, layout, seed, cid, types=None,
                    level_prefix="composite", seed_tag="composite", iid_tag="comp"):
    """One multi-fault instance: n sub-faults (one per entry of `types`) spread over 1 or 2 doors.

    layout: "1door" -> all n on one door; "2door" -> split across two, ceil(n/2) + floor(n/2).
    types:  the corruption types to compose, one sub-fault each. Defaults to all three (M4's
            composite set). M6 passes a PAIR, which is what makes the n=2 rung.
    level_prefix / seed_tag / iid_tag: keep each generated set in its own id and RNG namespace, so
            a new set never collides with or perturbs an existing one. The defaults reproduce M4's
            `instances_hard.jsonl` draw-for-draw.
    Returns the instance dict, or None if any gate fails.
    """
    rng = random.Random(f"{seed_tag}|{base}|{layout}|{seed}")
    healthy = os.path.join(ASSETS, base, "mobility.urdf")

    types = list(CTYPES if types is None else types)
    n = len(types)
    rng.shuffle(types)                       # application ORDER is randomised (order matters)
    if layout == "1door":
        chosen = [rng.choice(doors)] * n
    else:
        a, b = rng.sample(doors, 2)
        # the larger share lands on one door, the rest on the other; which door is seeded.
        # n=3 -> 2+1 (M4's assignment burden); n=2 -> 1+1 (M6, one fault per door).
        pair_first = rng.random() < 0.5
        k = (n + 1) // 2
        chosen = ([a] * k + [b] * (n - k)) if pair_first else ([a] * (n - k) + [b] * k)

    # SCALE MUST BE APPLIED FIRST on its part, for the agent's action space to be able to express
    # the inverse. Two reasons, both about corruption._edit_scale:
    #   1. It multiplies the <mesh scale>, which acts in the MESH frame, BEFORE the visual origin's
    #      rpy. Once a rotation has put a non-zero rpy on the part, scaling "axis 1" no longer scales
    #      along link-frame axis 1, and the pivot compensation stops fixing the link-frame edge.
    #   2. canonical.scale_pivot recomputes the pivot as "the bbox extreme nearer 0", which is only
    #      still the true pivot on unrotated geometry.
    # Scale first forward => its inverse is LAST in reverse, applied once every rotation has already
    # been undone, so the recomputed pivot equals the one the break used. (Empirically: with scale
    # first the recomputed pivot matches to 0.000000; with a rotation before it, it is off by ~0.07-
    # 0.13 m and the oracle cannot restore the part.) Stable, so the shuffle of the other two holds.
    pairs = sorted(zip(types, chosen), key=lambda tc: tc[0] != "scale")
    types, chosen = [t for t, _ in pairs], [c for _, c in pairs]

    # Sample each sub-fault against the state it will actually be applied to, so its
    # "individually >= 3*tau" guarantee is about ITS OWN displacement, not the cumulative one.
    specs, invs, cur = [], [], healthy
    stage_tmps = []
    for k, (ctype, part) in enumerate(zip(types, chosen)):
        spec, inv = corr.sample_corruption(cur, part, k, ctype, client=cid,
                                           continuous=True, base=base)
        if spec is None:
            for t in stage_tmps:
                if os.path.exists(t):
                    os.remove(t)
            return None
        specs.append(spec)
        invs.append(inv)
        nxt = corr.apply(cur, spec, f"_stage{k}_{base}_{seed_tag}_{layout}.urdf")
        if cur is not healthy:
            stage_tmps.append(cur)
        cur = nxt
    stage_tmps.append(cur)

    iid = f"{base}_{iid_tag}{layout}_{seed}"
    broken = _apply_chain(healthy, specs, f"_hard_{iid}.urdf")
    for t in stage_tmps:                                    # drop the sampling scratch files
        if os.path.exists(t) and os.path.abspath(t) != os.path.abspath(broken):
            os.remove(t)

    faults = [{"part_name": pt["name"], "link": pt["link"], "joint": pt["joint"], "spec": s}
              for pt, s in zip(chosen, specs)]
    # REVERSED inverses -- see the invertibility argument in the module docstring.
    gt_seq = [{"part_name": pt["name"], "link": pt["link"], "joint": pt["joint"], "spec": iv}
              for pt, iv in reversed(list(zip(chosen, invs)))]

    rec = _finish(iid, base, split, f"{level_prefix}_{layout}", faults, gt_seq, healthy, broken, cid)
    if rec is None and os.path.exists(broken):
        os.remove(broken)
    return rec


# --------------------------------------------------------------------------- M6: the n=2 rung

PAIRS = (("translate", "rotate"), ("translate", "scale"), ("rotate", "scale"))


def build_two_fault(inv, split_of, seed, per_pair, cid):
    """The M6 set: 2 sub-faults per instance, level-matched across the two arms.

      2fault_2door : one sub-fault on each of two doors
      2fault_1door : both sub-faults on one door

    Both arms need exactly TWO correct actions, so PASS is directly comparable between them -- which
    is what M4's n=3 H3 test could not claim (its 2door arm always contained a door carrying only one
    of the three faults). Each arm is stratified `per_pair` instances across the three type pairs,
    because M5 showed the two models are lopsided in OPPOSITE directions by fault type, so which two
    types compose may matter more than that there are two.

    Every base is used at most once across the whole set.
    """
    rng = random.Random(f"2fault|{seed}")
    two = sorted(b for b, d in inv.items() if len(d) >= 2)
    one = sorted(b for b, d in inv.items() if len(d) == 1)
    rng.shuffle(two)
    rng.shuffle(one)
    out, used, short = [], set(), []

    def fill(layout, pool, pair):
        got = 0
        for base in pool:
            if got >= per_pair:
                break
            if base in used:
                continue
            rec = build_composite(base, inv[base], split_of[base], layout, seed, cid,
                                  types=list(pair), level_prefix="2fault",
                                  seed_tag="2fault", iid_tag="2f")
            if rec:
                out.append(rec)
                used.add(base)
                got += 1
            else:
                print(f"  drop {layout} {base} {'+'.join(pair)} (gate)")
        if got < per_pair:
            short.append(f"{layout} {'+'.join(pair)}: {got}/{per_pair}")
        return got

    # two-door arm first -- only `two` can host it, and it is the scarce resource
    for pair in PAIRS:
        fill("2door", two, pair)
    # one-door arm from what is left, preferring single-door shapes so the scarce two-door
    # bases are not consumed by an arm that does not need them
    for pair in PAIRS:
        fill("1door", [b for b in one + two if b not in used], pair)

    if short:
        print("  UNDER-FILLED CELLS (recorded, not silently padded): " + "; ".join(short))
    return out


def build_control(base, doors, split, seed, ctype, cid):
    """One single-fault instance under the same hardened knobs (the attribution control)."""
    rng = random.Random(f"control|{base}|{ctype}|{seed}")
    healthy = os.path.join(ASSETS, base, "mobility.urdf")
    part = rng.choice(doors)
    spec, inv = corr.sample_corruption(healthy, part, seed, ctype, client=cid,
                                       continuous=True, base=base)
    if spec is None:
        return None
    iid = f"{base}_ctrl_{ctype}_{seed}"
    broken = corr.apply(healthy, spec, f"_hard_{iid}.urdf")
    faults = [{"part_name": part["name"], "link": part["link"], "joint": part["joint"],
               "spec": spec}]
    gt_seq = [{"part_name": part["name"], "link": part["link"], "joint": part["joint"],
               "spec": inv}]
    rec = _finish(iid, base, split, "control_single", faults, gt_seq, healthy, broken, cid)
    if rec is None and os.path.exists(broken):
        os.remove(broken)
    return rec


def _finish(iid, base, split, level, faults, gt_seq, healthy, broken, cid):
    """Score the break, verify the GT sequence restores it, and assemble the record.

    Gates (the four from instances.py, generalised to multiple parts):
      1. every faulty part is displaced >= 3*tau by the composite break
      2. the GT sequence restores every faulty part to <= 0.1*tau
      3. (already applied upstream) the healthy door closes
      4. the GT-fixed object PASSes the full multi-part contract
    """
    rb = evaluate_repair_multi(broken, healthy, faults, client=cid)
    if rb["PASS"]:
        return None                                        # not actually broken
    if any(v["deviation_mm"] < corr.BROKEN_MARGIN * v["tau_mm"] for v in rb["per_part"].values()):
        return None                                        # gate 1: some part barely moved

    fixed = _apply_chain(broken, [f["spec"] for f in gt_seq], f"_gtfix_{iid}.urdf")
    rf = evaluate_repair_multi(fixed, healthy, faults, client=cid)
    os.remove(fixed)
    if rf["deviation_mm"] > 0.1 * rf["tau_mm"]:            # gate 2: not exactly reversible
        return None
    if not rf["PASS"]:                                      # gate 4: unsolvable
        return None

    # Gate 5 (composite only): NECESSITY. Dropping any single fix must leave >= 3*tau of residual
    # error, so all n sub-faults genuinely have to be repaired and the instance cannot be solved
    # with n-1 actions. This is the right framing for composed breaks -- measuring a sub-fault ALONE
    # against the healthy object is not, because a scale sampled onto an already-rotated door
    # displaces differently there.
    residuals = []
    if len(gt_seq) > 1:
        for drop in range(len(gt_seq)):
            partial = [f["spec"] for i, f in enumerate(gt_seq) if i != drop]
            cand = _apply_chain(broken, partial, f"_nec_{iid}_{drop}.urdf")
            rp = evaluate_repair_multi(cand, healthy, faults, client=cid)
            os.remove(cand)
            residuals.append(round(rp["deviation_mm"], 3))
            if rp["PASS"] or rp["deviation_mm"] < corr.BROKEN_MARGIN * rp["tau_mm"]:
                return None

    # Gate 6: ORACLE ROUND-TRIP. The fix must be reachable through the agent's own action language,
    # with canonical params RECOMPUTED rather than read from the stored spec. Gate 2 (above) only
    # proves mathematical invertibility; this proves the ceiling is actually attainable.
    ro = oracle_roundtrip(broken, healthy, faults, gt_seq, cid, tag=f"g6_{iid}_")
    if not ro["PASS"]:
        print(f"  drop {iid}: oracle round-trip failed "
              f"(deviation {ro['deviation_mm']:.2f} mm) - recomputed canonical params diverge")
        return None

    links = list(dict.fromkeys(f["link"] for f in faults))
    return {
        "id": iid,
        "base": base,
        "split": split,
        "level": level,
        "n_faults": len(faults),
        "faults": faults,
        "gt_fix_sequence": gt_seq,
        "faulty_links": links,
        "faulty_joints": list(dict.fromkeys(f["joint"] for f in faults)),
        "fault_types": [f["spec"]["type"] for f in faults],
        "broken_urdf": os.path.relpath(broken, HERE),
        "healthy_urdf": os.path.relpath(healthy, HERE),
        "tau_frac": geom.TAU_FRAC,
        "broken_margin": corr.BROKEN_MARGIN,
        "magnitude_ranges": {"translate": list(corr.TRANSLATE_RANGE),
                             "rotate_deg": list(corr.ROTATE_RANGE_DEG),
                             "scale": list(corr.SCALE_RANGE)},
        "tau_mm_per_part": {k: v["tau_mm"] for k, v in rb["per_part"].items()},
        "tau_mm": rb["tau_mm"],
        "broken_deviation_mm": rb["deviation_mm"],
        "broken_score": rb["score"],
        "broken_pass": rb["PASS"],
        "per_part_broken": rb["per_part"],
        "closes_broken": rb["closes"],
        "collides_broken": rb["collides"],
        "collision_excess_mm": rb["collision_excess_mm"],
        "collision_pair": rb["collision_pair"],
        "gt_fixed_deviation_mm": rf["deviation_mm"],
        "gt_fixed_pass": rf["PASS"],
        "leave_one_out_deviation_mm": residuals,   # gate 5: each >= 3*tau (see above)
        "oracle_roundtrip_deviation_mm": round(ro["deviation_mm"], 6),   # gate 6
        "oracle_roundtrip_pass": ro["PASS"],
        "physics_verified": (not rb["closes"]) or rb["collides"],
        # back-compat shim: evaluate.py / run_episode.py group by corruption["type"]
        "corruption": {"type": "composite" if len(faults) > 1 else faults[0]["spec"]["type"]},
        # legacy single-fault fields, so single-part tooling keeps working on the control set
        "link": links[0],
        "joint": faults[0]["joint"],
        "part_name": faults[0]["part_name"],
        "gt_fix": gt_seq[0]["spec"] if len(faults) == 1 else None,
    }


# --------------------------------------------------------------------------- driver

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--set", default="composite", choices=["composite", "2fault", "easy"],
                    help="composite = M4's n=3 set + its single-fault control; "
                         "2fault = M6's n=2 rung (level-matched arms, type-pair stratified)")
    ap.add_argument("--per-type", type=int, default=10,
                    help="easy: single-fault instances per corruption type (10 -> 30 total)")
    ap.add_argument("--out-easy", default=os.path.join(HERE, "data", "instances_easy.jsonl"))
    ap.add_argument("--per-pair", type=int, default=5,
                    help="2fault: instances per type pair per arm (5 -> 15 per arm, 30 total)")
    ap.add_argument("--out-composite", default=os.path.join(HERE, "data", "instances_hard.jsonl"))
    ap.add_argument("--out-control", default=os.path.join(HERE, "data", "instances_control.jsonl"))
    ap.add_argument("--out-2fault", default=os.path.join(HERE, "data", "instances_2fault.jsonl"))
    ap.add_argument("--difficulty-scale", type=float, default=None,
                    help="scale every corruption magnitude range toward identity (1.0 = unchanged, "
                         "0.35 = much smaller faults). Translate/rotate ranges are multiplied; the "
                         "scale range is contracted toward 1.0. This is the knob that actually sets "
                         "difficulty: landing inside tau when the fault is D*tau needs magnitude "
                         "accuracy of +/-1/D, and D is driven by the DRAW RANGE, not by "
                         "--broken-margin (which only sets a floor the draw usually clears already)")
    ap.add_argument("--broken-margin", type=float, default=None,
                    help="override corruption.BROKEN_MARGIN: every fault is grown until it displaces "
                         "the part by at least this many tau. LOWER = genuinely easier, because "
                         "landing inside tau when the fault is D*tau needs magnitude accuracy of "
                         "+/-1/D. Recorded per instance as broken_margin")
    ap.add_argument("--allow-default-tau", action="store_true",
                    help="permit generating at the default 0.025 (normally a hard error)")
    args = ap.parse_args()

    if args.difficulty_scale is not None:
        f = args.difficulty_scale
        corr.TRANSLATE_RANGE = tuple(v * f for v in corr.TRANSLATE_RANGE)
        corr.ROTATE_RANGE_DEG = tuple(v * f for v in corr.ROTATE_RANGE_DEG)
        corr.SCALE_RANGE = tuple(1.0 + (v - 1.0) * f for v in corr.SCALE_RANGE)
        print(f"difficulty-scale {f}: translate {corr.TRANSLATE_RANGE}, "
              f"rotate {corr.ROTATE_RANGE_DEG}, scale {corr.SCALE_RANGE}")

    if args.broken_margin is not None:
        corr.BROKEN_MARGIN = args.broken_margin
        print(f"BROKEN_MARGIN overridden to {corr.BROKEN_MARGIN}")

    if not args.allow_default_tau and abs(geom.TAU_FRAC - TARGET_TAU_FRAC) > 1e-12:
        raise SystemExit(f"TAU_FRAC is {geom.TAU_FRAC}, expected {TARGET_TAU_FRAC}. "
                         f"Run with FIXIT_TAU_FRAC={TARGET_TAU_FRAC}.")

    cid = p.connect(p.DIRECT)
    inv, split_of = inventory(cid)
    two = sorted(b for b, d in inv.items() if len(d) >= 2)
    one = sorted(b for b, d in inv.items() if len(d) == 1)
    print(f"shapes usable: {len(inv)}   >=2 doors: {len(two)}   1 door: {len(one)}")

    if args.set == "easy":
        # Single fault, type-balanced. The point of this set is the MARGIN and the draw range:
        # --broken-margin 1.2 --difficulty-scale 0.35 puts faults at ~1.6 tau, so a correction needs
        # magnitude accuracy of +/-60% rather than +/-22%. See M7 section 6.
        #
        # per_type may exceed the number of usable shapes (36), so bases are CYCLED with an
        # incrementing seed: build_control seeds on (base, ctype, seed) and ids are
        # {base}_ctrl_{ctype}_{seed}, so each pass over the pool yields genuinely different
        # corruptions on the same geometry. Instances sharing a base are CORRELATED -- the effective
        # n is below the nominal n -- which is why the count per base is reported below.
        rng = random.Random(args.seed)
        cpool = sorted(inv)
        rng.shuffle(cpool)
        rows, used = [], set()
        for ctype in CTYPES:
            got, k = 0, 0
            while got < args.per_type and k < len(cpool) * 6:
                base = cpool[k % len(cpool)]
                seed_i = args.seed + (k // len(cpool))
                k += 1
                # Prefer an UNUSED shape across the whole set, not just within this fault type.
                # Restarting each type at the head of the pool would hand every type the same first
                # N fridges, so a 30-instance set would rest on 10 shapes with everything correlated
                # in threes. Only reuse once the pool is genuinely exhausted.
                if base in used and len(used) < len(cpool):
                    continue
                rec = build_control(base, inv[base], split_of[base], seed_i, ctype, cid)
                if rec:
                    rows.append(rec)
                    used.add(base)
                    got += 1
                else:
                    print(f"  drop easy {base} {ctype} seed{seed_i} (gate)")
            if got < args.per_type:
                print(f"  UNDER-FILLED {ctype}: {got}/{args.per_type} (recorded, not padded)")
        p.disconnect(cid)
        _write_sets(((args.out_easy, rows, "easy"),), allow_base_reuse=True)
        return

    if args.set == "2fault":
        rows = build_two_fault(inv, split_of, args.seed, args.per_pair, cid)
        p.disconnect(cid)
        _write_sets(((args.out_2fault, rows, "2fault"),))
        return

    rng = random.Random(args.seed)
    rng.shuffle(two)
    rng.shuffle(one)

    composite, used = [], set()

    # two-door arm first: it is the scarce resource (only `two` can host it)
    for base in two:
        if len(composite) >= N_TWO_DOOR:
            break
        rec = build_composite(base, inv[base], split_of[base], "2door", args.seed, cid)
        if rec:
            composite.append(rec)
            used.add(base)
        else:
            print(f"  drop 2door {base} (gate)")

    # one-door arm from whatever is left, preferring single-door shapes so two-door shapes stay
    # available for the arm that needs them
    pool = [b for b in one + two if b not in used]
    n1 = 0
    for base in pool:
        if n1 >= N_ONE_DOOR:
            break
        rec = build_composite(base, inv[base], split_of[base], "1door", args.seed, cid)
        if rec:
            composite.append(rec)
            used.add(base)
            n1 += 1
        else:
            print(f"  drop 1door {base} (gate)")

    # control: 25 distinct bases, types round-robined so the mix stays balanced
    control = []
    cpool = sorted(inv)
    rng.shuffle(cpool)
    types = itertools.cycle(CTYPES)
    for base in cpool:
        if len(control) >= N_CONTROL:
            break
        rec = build_control(base, inv[base], split_of[base], args.seed, next(types), cid)
        if rec:
            control.append(rec)
        else:
            print(f"  drop control {base} (gate)")
    p.disconnect(cid)
    _write_sets(((args.out_composite, composite, "composite"),
                 (args.out_control, control, "control")))


def _write_sets(specs, allow_base_reuse=False):
    for path, rows, label in specs:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        bases = {r["base"] for r in rows}
        print(f"\n{label}: {len(rows)} instances, {len(bases)} distinct bases -> {path}")
        by_level = {}
        for r in rows:
            by_level[r["level"]] = by_level.get(r["level"], 0) + 1
        print(f"  levels: {by_level}")
        pairs = {}
        for r in rows:
            if len(r.get("fault_types", [])) > 1:
                k = "+".join(sorted(r["fault_types"]))
                pairs[k] = pairs.get(k, 0) + 1
        if pairs:
            print(f"  fault-type combinations: {pairs}")
        if rows:
            if not allow_base_reuse:
                assert len(bases) == len(rows), f"{label}: base reuse"
            else:
                from collections import Counter
                per = Counter(r["base"] for r in rows)
                print(f"  instances per base: min={min(per.values())} "
                      f"max={max(per.values())} (correlated; effective n < {len(rows)})")
            assert all(r["gt_fixed_pass"] for r in rows), f"{label}: an instance is unsolvable"
            assert not any(r["broken_pass"] for r in rows), f"{label}: an instance already passes"
            assert all(abs(r["tau_frac"] - geom.TAU_FRAC) < 1e-12 for r in rows)
            dev = [r["broken_deviation_mm"] / r["tau_mm"] for r in rows]
            print(f"  deviation/tau: min={min(dev):.1f}x max={max(dev):.1f}x  "
                  f"(floor {corr.BROKEN_MARGIN}x)")
            print(f"  gt_fixed deviation max: {max(r['gt_fixed_deviation_mm'] for r in rows):.4f}mm")
            print(f"  physics_verified: {sum(r['physics_verified'] for r in rows)}/{len(rows)}")
            print("  assertions OK: broken, solvable, distinct bases, tau matches")


if __name__ == "__main__":
    main()
