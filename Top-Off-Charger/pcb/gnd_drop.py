"""Ground-pour voltage drop on the Top Off Charger board (design doc section 7.3).

Finite differences on the rasterised GND copper of a KiCad board file. +1 A goes
in at TB2's GND pad (pack -) and out at TB1's GND pad (PSU -V, held at 0 V); each
is found by reference and net, so a layout that renumbers or moves them still
solves. The potential of every GND pad per amp is printed in milliohms, followed
by the two figures section 7.3 uses:

  R_shared    V(TB2 GND) - V(U2 pin 2): the pour resistance the charge current
              shares with the INA228's ground reference, so VBUS reads high by
              R_shared x I
  whole pour  V(TB2 GND) - V(TB1 GND)

The model includes the zone fills as saved in the board file (refill the zones in
KiCad before saving), the GND tracks, the through-hole GND pads (both layers, each
pad one node) and the GND vias (ideal, or F/B pairs joined by --barrel-mohm). It
leaves out the modules, socket contacts, solder joints and temperature.

usage:
  python gnd_drop.py ["Top Off Charger- Oct 2026.kicad_pcb"] [--h 0.1]
                     [--barrel-mohm 0] [--t-um 35]
  python gnd_drop.py --self-test

--self-test solves a uniform 20 x 100 mm strip against its exact resistance, and
checks that a pour cut in two, and a board with no TB2, are refused rather than
solved.
"""

import argparse
import math
import re
import sys
import time
from pathlib import Path as FsPath

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from matplotlib.path import Path
from scipy.sparse.csgraph import connected_components

RHO = 1.724e-8  # ohm.m, annealed copper at 20 C
DEFAULT_BOARD = FsPath(__file__).with_name("Top Off Charger- Oct 2026.kicad_pcb")
LAY = {"F.Cu": 0, "B.Cu": 1}


class NotConnected(Exception):
    """The source and sink pads are not joined by GND copper."""


def parse(src):
    stack = [[]]
    for m in re.finditer(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', src):
        t = m.group(0)
        if t == "(":
            stack.append([])
        elif t == ")":
            x = stack.pop()
            stack[-1].append(x)
        else:
            stack[-1].append(t[1:-1] if t.startswith('"') else t)
    return stack[0][0]


def kids(n, name):
    return [c for c in n if isinstance(c, list) and c and c[0] == name]


def kid(n, name):
    k = kids(n, name)
    return k[0] if k else None


def netname(n):
    # KiCad 10 writes (net "GND"); older files write (net 3 "GND")
    k = kid(n, "net")
    return (k[2] if len(k) > 2 else k[1]) if k else ""


def xf(at, x, y):
    ax, ay = float(at[1]), float(at[2])
    th = math.radians(float(at[3]) if len(at) > 3 else 0)
    return (
        ax + x * math.cos(th) + y * math.sin(th),
        ay - x * math.sin(th) + y * math.cos(th),
    )


def solve(board_text, h, r_barrel=0.0, t_cu=35e-6):
    """Return (pads, src, snk, info): pads maps label -> ohm per amp above the sink."""
    rs = RHO / t_cu  # ohm per square
    T = parse(board_text)

    edge = next(g for g in kids(T, "gr_rect") if kid(g, "layer")[1] == "Edge.Cuts")
    X0, Y0 = float(kid(edge, "start")[1]), float(kid(edge, "start")[2])
    X1, Y1 = float(kid(edge, "end")[1]), float(kid(edge, "end")[2])
    NX, NY = round((X1 - X0) / h), round((Y1 - Y0) / h)
    xc = X0 + (np.arange(NX) + 0.5) * h
    yc = Y0 + (np.arange(NY) + 0.5) * h
    XX, YY = np.meshgrid(xc, yc)  # [NY, NX]
    cu = np.zeros((2, NY, NX), bool)

    def win(x0, x1, y0, y1):
        i0, i1 = max(0, int((x0 - X0) / h) - 1), min(NX, int((x1 - X0) / h) + 2)
        j0, j1 = max(0, int((y0 - Y0) / h) - 1), min(NY, int((y1 - Y0) / h) + 2)
        return slice(j0, j1), slice(i0, i1)

    # 1. zone fills
    for z in kids(T, "zone"):
        if (kid(z, "net_name") or kid(z, "net") or [None, ""])[1] != "GND":
            continue
        for fp in kids(z, "filled_polygon"):
            P = np.array(
                [(float(q[1]), float(q[2])) for q in kids(kid(fp, "pts"), "xy")]
            )
            sj, si = win(P[:, 0].min(), P[:, 0].max(), P[:, 1].min(), P[:, 1].max())
            pts = np.column_stack([XX[sj, si].ravel(), YY[sj, si].ravel()])
            inside = Path(P).contains_points(pts).reshape(XX[sj, si].shape)
            cu[LAY[kid(fp, "layer")[1]], sj, si] |= inside

    # 2. GND tracks
    for s in kids(T, "segment"):
        if netname(s) != "GND":
            continue
        a = np.array([float(v) for v in kid(s, "start")[1:3]])
        b = np.array([float(v) for v in kid(s, "end")[1:3]])
        w = float(kid(s, "width")[1])
        L = LAY[kid(s, "layer")[1]]
        sj, si = win(
            min(a[0], b[0]) - w,
            max(a[0], b[0]) + w,
            min(a[1], b[1]) - w,
            max(a[1], b[1]) + w,
        )
        px, py = XX[sj, si] - a[0], YY[sj, si] - a[1]
        d = b - a
        dd = max(d @ d, 1e-12)
        t = np.clip((px * d[0] + py * d[1]) / dd, 0, 1)
        cu[L, sj, si] |= (px - t * d[0]) ** 2 + (py - t * d[1]) ** 2 <= (w / 2) ** 2

    def shape_mask(x, y, sx, sy, kind):
        sj, si = win(x - sx, x + sx, y - sy, y + sy)
        dx, dy = XX[sj, si] - x, YY[sj, si] - y
        if kind == "circle" or (kind == "oval" and abs(sx - sy) < 1e-6):
            m = dx**2 + dy**2 <= (sx / 2) ** 2
        elif kind == "oval":
            r = min(sx, sy) / 2
            ex, ey = max(0, sx / 2 - r), max(0, sy / 2 - r)
            m = (
                np.maximum(abs(dx) - ex, 0) ** 2 + np.maximum(abs(dy) - ey, 0) ** 2
            ) <= r**2
        else:  # rect / roundrect, 0/90/180/270 only
            m = (abs(dx) <= sx / 2) & (abs(dy) <= sy / 2)
        return sj, si, m

    # 3. GND THT pads (both layers) -> supernodes; vias -> supernodes (ideal) or F/B pair + barrel
    groups = []  # (label, [(layer, sj, si, mask)], is_pad)
    for fp in kids(T, "footprint"):
        at = kid(fp, "at")
        ref = {p[1]: p[2] for p in kids(fp, "property")}.get("Reference")
        for p in kids(fp, "pad"):
            if netname(p) != "GND":
                continue
            pa = kid(p, "at")
            x, y = xf(at, float(pa[1]), float(pa[2]))
            sz = kid(p, "size")
            sx, sy = float(sz[1]), float(sz[2])
            rot = (float(pa[3]) if len(pa) > 3 else 0) % 180
            if abs(rot - 90) < 1:
                sx, sy = sy, sx
            sj, si, m = shape_mask(x, y, sx, sy, p[3])
            groups.append(
                (
                    f"{ref}.{p[1]}@({x:.2f},{y:.2f})",
                    [(0, sj, si, m), (1, sj, si, m)],
                    True,
                )
            )
            cu[0, sj, si] |= m
            cu[1, sj, si] |= m
    for v in kids(T, "via"):
        if netname(v) != "GND":
            continue
        x, y = float(kid(v, "at")[1]), float(kid(v, "at")[2])
        d = float(kid(v, "size")[1])
        sj, si, m = shape_mask(x, y, d, d, "circle")
        cu[0, sj, si] |= m
        cu[1, sj, si] |= m
        if r_barrel == 0:
            groups.append((f"via@({x},{y})", [(0, sj, si, m), (1, sj, si, m)], False))
        else:
            groups.append((f"viaF@({x},{y})", [(0, sj, si, m)], False))
            groups.append((f"viaB@({x},{y})", [(1, sj, si, m)], False))

    # node numbering: every copper cell its own node, then supernode cells collapsed.
    # A later group takes the cells it shares with an earlier one. A pad that loses every
    # cell that way is moved to the end and the numbering redone, so it keeps a node.
    # R13, 2026-10-08: there was one pass. From the owner's 2026-10-07 19:09 save on,
    # TB2-2's enlarged pad covered the net tie's GND pad, which came first in the file, so
    # TB2-2 took every cell of it; remap gave -1 and the tie read V[-1], another node's
    # voltage: a Kelvin residual of 0.24-0.26 mohm where the solve gives 0.0000.
    N = NY * NX
    cid = np.flatnonzero(cu.ravel())
    for _pass in range(2):
        node = np.full(2 * N, -1, np.int64)
        node[cid] = np.arange(cid.size)
        nxt = cid.size
        gnode = {}
        for lab, parts, _ in groups:
            for L, sj, si, m in parts:
                idx = (
                    L * N
                    + np.add.outer(
                        np.arange(sj.start, sj.stop) * NX, np.arange(si.start, si.stop)
                    )
                )[m]
                node[idx] = nxt
            gnode[lab] = nxt
            nxt += 1
        own = np.bincount(node[node >= cid.size] - cid.size, minlength=len(groups))
        gone = [i for i, g in enumerate(groups) if g[2] and own[i] == 0]
        if not gone:
            break
        groups = [g for i, g in enumerate(groups) if i not in gone] + [
            groups[i] for i in gone
        ]

    rows, cols = [], []
    c3 = cu.reshape(2, NY, NX)
    n3 = node.reshape(2, NY, NX)
    for L in (0, 1):
        for a, b in (
            ((slice(None), slice(0, -1)), (slice(None), slice(1, None))),
            ((slice(0, -1), slice(None)), (slice(1, None), slice(None))),
        ):
            ok = c3[L][a] & c3[L][b]
            u, w = n3[L][a][ok], n3[L][b][ok]
            k = u != w
            rows.append(u[k])
            cols.append(w[k])
    u = np.concatenate(rows)
    w = np.concatenate(cols)
    g = np.full(u.size, 1.0 / rs)
    if r_barrel:
        for lab in list(gnode):
            if lab.startswith("viaF"):
                u = np.append(u, gnode[lab])
                w = np.append(w, gnode["viaB" + lab[4:]])
                g = np.append(g, 1.0 / r_barrel)
    # Laplacian over used nodes
    used = np.unique(np.concatenate([u, w]))
    remap = -np.ones(nxt, np.int64)
    remap[used] = np.arange(used.size)
    u, w = remap[u], remap[w]
    M = used.size
    A = sp.coo_matrix(
        (
            np.concatenate([-g, -g, g, g]),
            (np.concatenate([u, w, u, w]), np.concatenate([w, u, u, w])),
        ),
        (M, M),
    ).tocsr()

    pads = {lab: remap[gnode[lab]] for lab, _, isp in groups if isp}
    # a pad with no node in the network would read V[-1], another node's voltage (R8)
    lost = [lab for lab, n in pads.items() if n < 0]
    if lost:
        raise ValueError(f"pads missing from the solved network: {lost}")
    # the GND pad of each terminal block, by reference and net, not by pad number or
    # position: TB2 (pack -) is the source, TB1 (PSU -V) the sink.
    # R13, 2026-10-06: this took pad 2 of each block and called the upper one the
    # source; the 2026-10-06 layout moved TB1's GND to pad 1 and it raised
    # "expected two terminal-block GND pads, found ['TB2.2@(16.79,24.50)']".
    tb = {r: [k for k in pads if k.startswith(r + ".")] for r in ("TB2", "TB1")}
    if any(len(v) != 1 for v in tb.values()):
        raise ValueError(f"expected one GND pad on each of TB2 and TB1, found {tb}")
    src, snk = tb["TB2"][0], tb["TB1"][0]
    ncomp, comp = connected_components(A, directed=False)
    if comp[pads[src]] != comp[pads[snk]]:
        raise NotConnected(
            f"{src} and {snk} are not joined by GND copper ({ncomp} components)"
        )
    keep = np.flatnonzero(comp == comp[pads[snk]])
    red = [i for i in range(keep.size) if keep[i] != pads[snk]]
    Ar = A[keep][:, keep][red][:, red].tocsc()
    rhs = np.zeros(len(red))
    r_of = {keep[i]: j for j, i in enumerate(red)}
    rhs[r_of[pads[src]]] = 1.0
    t0 = time.time()
    V = spla.spsolve(Ar, rhs)
    dt = time.time() - t0
    Vn = np.zeros(M)
    Vn[keep[red]] = V
    info = (
        f"h={h} mm  t={t_cu * 1e6:.0f} um  Rs={rs * 1e3:.4f} mohm/sq  barrel={r_barrel * 1e3:.2f} mohm  "
        f"cells F={cu[0].sum()} B={cu[1].sum()}  unknowns={len(red)}  components={ncomp}  solve {dt:.1f}s"
    )
    islands = {lab for lab in pads if comp[pads[lab]] != comp[pads[snk]]}
    return (
        {lab: (None if lab in islands else Vn[pads[lab]]) for lab in pads},
        src,
        snk,
        info,
    )


STRIP = """(kicad_pcb (gr_rect (start 0 0) (end 20 100) (layer "Edge.Cuts"))
 (footprint "t" (at 10 10) (property "Reference" "TB2") (pad "2" thru_hole rect (at 0 0) (size 20 1)
  (drill 0.5) (layers "*.Cu") (net "GND")))
 (footprint "t" (at 10 90) (property "Reference" "TB1") (pad "2" thru_hole rect (at 0 0) (size 20 1)
  (drill 0.5) (layers "*.Cu") (net "GND")))
 (zone (net "GND") (layer "B.Cu") {fills}))"""
FILL = '(filled_polygon (layer "B.Cu") (pts (xy 0 {y0}) (xy 20 {y0}) (xy 20 {y1}) (xy 0 {y1})))'


def self_test():
    # direction 1: a uniform strip; 79 mm between the pads' inner edges, 20 mm wide
    exact = RHO / 35e-6 * 79 / 20
    pads, src, _snk, _ = solve(STRIP.format(fills=FILL.format(y0=0, y1=100)), 0.1)
    got = pads[src]
    err = (got - exact) / exact
    print(
        f"strip: {got * 1e3:.4f} mohm vs {exact * 1e3:.4f} mohm exact ({err * 100:+.2f}%)"
    )
    ok = abs(err) < 0.005
    # direction 2: the same strip cut in two must be refused, not solved
    cut = FILL.format(y0=0, y1=49.9) + " " + FILL.format(y0=50.1, y1=100)
    try:
        solve(STRIP.format(fills=cut), 0.1)
        print("cut pour: SOLVED - the connectivity check did not fire")
        ok = False
    except NotConnected as e:
        print(f"cut pour: refused ({e})")
    # direction 3: a board with no TB2 GND pad must be refused, not guessed at
    no_tb2 = STRIP.replace('"TB2"', '"TB1"', 1).format(fills=FILL.format(y0=0, y1=100))
    try:
        solve(no_tb2, 0.1)
        print("no TB2: SOLVED - the pad selection did not fire")
        ok = False
    except ValueError as e:
        print(f"no TB2: refused ({e})")
    # direction 4: a small pad inside TB2's pad, listed before it, keeps a node of its
    # own and reads TB2's voltage, since no current leaves it (the 2026-10-08 R13 case)
    tie = (
        '(footprint "t" (at 10 10.2) (property "Reference" "NT1") (pad "1" smd rect'
        ' (at 0 0) (size 0.4 0.4) (layers "F.Cu") (net "GND")))\n (footprint "t" (at 10 10)'
    )
    board = STRIP.replace('(footprint "t" (at 10 10)', tie, 1)
    pads, src, _snk, _ = solve(board.format(fills=FILL.format(y0=0, y1=100)), 0.1)
    nt = [k for k in pads if k.startswith("NT1.")]
    if len(nt) == 1 and abs(pads[nt[0]] - pads[src]) < 1e-9:
        print(f"pad inside TB2: reads TB2 ({pads[nt[0]] * 1e3:.4f} mohm)")
    else:
        got = {k: pads[k] for k in nt}
        print(f"pad inside TB2: WRONG {got} vs {pads[src]}")
        ok = False
    # direction 5: two pads on the same copper cannot both keep a node; refuse, not guess
    pad = (
        ' (footprint "t" (at 10 50) (property "Reference" "X{n}") (pad "1" smd rect'
        ' (at 0 0) (size 0.4 0.4) (layers "F.Cu") (net "GND")))\n'
    )
    twin = pad.replace("{n}", "1") + pad.replace("{n}", "2") + " (zone"
    board = STRIP.replace(" (zone", twin, 1)
    try:
        solve(board.format(fills=FILL.format(y0=0, y1=100)), 0.1)
        print("coincident pads: SOLVED - the missing-pad check did not fire")
        ok = False
    except ValueError as e:
        if "missing from the solved network" not in str(e):
            raise
        print(f"coincident pads: refused ({e})")
    print("SELF-TEST PASSED" if ok else "SELF-TEST FAILED")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("board", nargs="?", default=str(DEFAULT_BOARD))
    ap.add_argument("--h", type=float, default=0.1, help="cell size, mm (default 0.1)")
    ap.add_argument(
        "--barrel-mohm",
        type=float,
        default=0.0,
        help="via barrel, mohm (default 0 = ideal)",
    )
    ap.add_argument(
        "--t-um",
        type=float,
        default=35.0,
        help="copper thickness, um (default 35 = 1 oz)",
    )
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    text = FsPath(a.board).read_text(encoding="utf-8")
    pads, src, snk, info = solve(text, a.h, a.barrel_mohm * 1e-3, a.t_um * 1e-6)
    print(info)
    print(f"source {src}  sink {snk}")
    for lab in sorted(pads, key=lambda k: -(pads[k] or 0)):
        v = pads[lab]
        print(
            f"  {lab:34} "
            + ("  (ISLAND - not connected)" if v is None else f"{v * 1e3:8.4f} mohm")
        )
    u2 = [k for k in pads if k.startswith("U2.2@")]
    if u2:
        print(
            f"R_shared   V({src}) - V({u2[0]}) = {(pads[src] - pads[u2[0]]) * 1e3:.4f} mohm"
        )
    print(f"whole pour V({src}) - V({snk}) = {pads[src] * 1e3:.4f} mohm")
    return 0


if __name__ == "__main__":
    sys.exit(main())
