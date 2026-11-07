# Grand tour, étape 2 : piste de l'île bordée de barrières
# - entrée : map-a.json (île aplanie, relevée en course), barrières du circuit (avec ouvertures)
# - trajet A* entre les points de passage (portes), lissé (Chaikin), rééchantillonné tous les mètres
# - barrières : décalage de ±W/2 de part et d'autre de la ligne centrale, boucles intérieures retirées
# - sortie : track_b.json (ligne centrale, portes recalées, barrières), contrôles, image
import json, math, heapq, sys, os
import numpy as np
from collections import deque

W = float(os.environ.get('TRACK_WIDTH', 12))          # largeur de la piste
HALF_W = W / 2
d = json.load(open('map-a.json')); N, half, RES = d['N'], d['half'], d['res']
G = np.array(d['ground']).reshape(N, N); T = np.array(d['top']).reshape(N, N); K = np.array(d['kind']).reshape(N, N)
H = np.where(T > -50, T - np.maximum(G, 0), 0)
obst = ((K == 1) & (H > 0.35)) | ((K == 2) & (H > 0.2))
toc = lambda x, z: (int(math.floor((z + half) / RES)), int(math.floor((x + half) / RES)))
tow = lambda zi, xi: ((xi + 0.5) * RES - half, (zi + 0.5) * RES - half)

# barrières du circuit (relevé avec les ouvertures)
RAIL = np.zeros((N, N), bool)
for ax, az, bx, bz in d['segs']:
    n = int(math.hypot(bx - ax, bz - az) / (RES / 3)) + 1
    for i in range(n + 1):
        zz, xx = toc(ax + (bx - ax) * i / n, az + (bz - az) * i / n)
        if 0 <= zz < N and 0 <= xx < N: RAIL[zz, xx] = True

def distance_field(mask):
    dist = np.full((N, N), 1e9); q = deque()
    for z, x in zip(*np.nonzero(mask)): dist[z, x] = 0; q.append((z, x))
    while q:
        z, x = q.popleft()
        for dz in (-1, 0, 1):
            for dx in (-1, 0, 1):
                nz, nx = z + dz, x + dx
                if 0 <= nz < N and 0 <= nx < N and dist[nz, nx] > dist[z, x] + math.hypot(dz, dx):
                    dist[nz, nx] = dist[z, x] + math.hypot(dz, dx); q.append((nz, nx))
    return dist * RES
rdist = distance_field(RAIL)
odist = distance_field(obst)
DEEP = -0.9

src = open(os.environ.get('FOLIO_SRC', os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../folio-2025')) + '/sources/data/grandTour.js').read()
import re
gaps = { m[0]: (float(m[1]), float(m[2])) for m in re.findall(r"name: '(exit|entry)', x: ([-\d.]+), z: ([-\d.]+)", src) }

# points de passage : (nom, x, z) — None = point d'appui sans porte
WAYPOINTS = json.load(open(sys.argv[1] if len(sys.argv) > 1 else 'waypoints_b.json'))

def near_gap(x, z, r):
    return any(math.hypot(x - gx, z - gz) < r for gx, gz in gaps.values())

def cost(zi, xi):
    x, z = tow(zi, xi)
    g = G[zi, xi]
    if g < DEEP: return None
    if odist[zi, xi] < HALF_W + 0.5: return None
    if rdist[zi, xi] < HALF_W + 1.0 and not near_gap(x, z, 10): return None
    c = 1.0
    if g < -0.05: c += float(os.environ.get("WATER_COST", 4))
    if rdist[zi, xi] < HALF_W + 5: c += (HALF_W + 5 - rdist[zi, xi]) * 0.5
    return c

def astar(a, b):
    sz, sx = toc(*a); gz, gx = toc(*b)
    openq = [ (0, sz, sx) ]; came = {}; gs = { (sz, sx): 0 }
    while openq:
        _, z, x = heapq.heappop(openq)
        if (z, x) == (gz, gx): break
        for dz in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if not dz and not dx: continue
                nz, nx = z + dz, x + dx
                if not (0 <= nz < N and 0 <= nx < N): continue
                c = cost(nz, nx)
                if c is None:
                    # départ et arrivée de tronçon : on tolère (points imposés)
                    if min(math.hypot(nz - gz, nx - gx), math.hypot(nz - sz, nx - sx)) * RES < 4: c = 3
                    else: continue
                ng = gs[(z, x)] + math.hypot(dz, dx) * RES * c
                if ng < gs.get((nz, nx), 1e18):
                    gs[(nz, nx)] = ng; came[(nz, nx)] = (z, x)
                    heapq.heappush(openq, (ng + math.hypot(nz - gz, nx - gx) * RES, nz, nx))
    if (gz, gx) not in came: return None
    path = [ (gz, gx) ]
    while path[-1] != (sz, sx): path.append(came[path[-1]])
    return [ tow(z, x) for z, x in reversed(path) ]

def los(p, q):
    n = int(math.dist(p, q) / (RES / 2)) + 1
    for i in range(1, n):
        x = p[0] + (q[0] - p[0]) * i / n; z = p[1] + (q[1] - p[1]) * i / n
        zi, xi = toc(x, z)
        if cost(zi, xi) is None and not near_gap(x, z, 8): return False
    return True

def simplify(path):
    out = [ path[0] ]; i = 0
    while i < len(path) - 1:
        j = len(path) - 1
        while j > i + 1 and not los(path[i], path[j]): j -= 1
        out.append(path[j]); i = j
    return out

# 1. trajet brut porte à porte
pts = []; marks = []
for (na, xa, za), (nb, xb, zb) in zip(WAYPOINTS, WAYPOINTS[1:]):
    p = astar((xa, za), (xb, zb))
    if p is None: print('PAS DE CHEMIN', na, '→', nb); sys.exit(1)
    s = simplify(p)
    pts += s if not pts else s[1:]
    marks.append((nb, len(pts) - 1))

# 2. lissage (Chaikin), extrémités fixes (centres des ouvertures)
def chaikin(p, it):
    for _ in range(it):
        q = [ p[0] ]
        for a, b in zip(p, p[1:]):
            q.append((0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]))
            q.append((0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]))
        q.append(p[-1]); p = q
    return p
def resample(p, step):
    cum = [ 0 ]
    for a, b in zip(p, p[1:]): cum.append(cum[-1] + math.dist(a, b))
    out = []; k = 0; t = 0
    while t <= cum[-1]:
        while k < len(p) - 2 and cum[k + 1] < t: k += 1
        seg = cum[k + 1] - cum[k] or 1; u = (t - cum[k]) / seg
        out.append((p[k][0] + (p[k + 1][0] - p[k][0]) * u, p[k][1] + (p[k + 1][1] - p[k][1]) * u)); t += step
    if math.dist(out[-1], p[-1]) > 0.2: out.append(p[-1])
    return out
# les ouvertures : on impose une sortie perpendiculaire à la barrière du circuit (points d'appui)
center = resample(chaikin(pts, int(os.environ.get('CHAIKIN', 5))), 1.0)

# 3. portes recalées sur la ligne centrale
def nearest(p):
    best = min(range(len(center)), key=lambda i: math.dist(center[i], p))
    return best
gates = []
for name, x, z in WAYPOINTS[1:-1]:
    if name.startswith('_'): continue
    i = nearest((x, z)); a = center[max(0, i - 2)]; b = center[min(len(center) - 1, i + 2)]
    dx, dz = b[0] - a[0], b[1] - a[1]
    gates.append({ 'name': name, 'x': round(center[i][0], 2), 'z': round(center[i][1], 2), 'rotation': round(math.atan2(-dx, -dz), 4), 'i': i, 'moved': round(math.dist(center[i], (x, z)), 1) })

# 4. barrières : décalages, boucles retirées
def offset(p, s):
    out = []
    for i in range(len(p)):
        a = p[max(0, i - 1)]; b = p[min(len(p) - 1, i + 1)]
        dx, dz = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dz) or 1
        nx, nz = -dz / L, dx / L
        out.append((p[i][0] + nx * s, p[i][1] + nz * s))
    return out
def seg_inter(p1, p2, p3, p4):
    d1x, d1z = p2[0] - p1[0], p2[1] - p1[1]; d2x, d2z = p4[0] - p3[0], p4[1] - p3[1]
    den = d1x * d2z - d1z * d2x
    if abs(den) < 1e-9: return None
    t = ((p3[0] - p1[0]) * d2z - (p3[1] - p1[1]) * d2x) / den
    u = ((p3[0] - p1[0]) * d1z - (p3[1] - p1[1]) * d1x) / den
    if 0 <= t <= 1 and 0 <= u <= 1: return (p1[0] + t * d1x, p1[1] + t * d1z)
    return None
def remove_loops(p, window=60):
    out = list(p); i = 0
    while i < len(out) - 1:
        cut = None
        for j in range(min(len(out) - 2, i + window), i + 1, -1):
            x = seg_inter(out[i], out[i + 1], out[j], out[j + 1])
            if x: cut = (j, x); break
        if cut:
            j, x = cut
            out = out[:i + 1] + [ x ] + out[j + 1:]
        i += 1
    return out
left = remove_loops(offset(center, HALF_W))
right = remove_loops(offset(center, -HALF_W))

# raccord aux barrières du circuit : on prolonge chaque bord jusqu'au bout de barrière coupé le plus proche
ends = []
for ax, az, bx, bz in d['segs']:
    for x, z in ((ax, az), (bx, bz)):
        for gx, gz in gaps.values():
            r = math.hypot(x - gx, z - gz)
            if 5.0 < r < 7.0: ends.append((x, z))
def attach(line):
    a = min(ends, key=lambda e: math.dist(e, line[0])); b = min(ends, key=lambda e: math.dist(e, line[-1]))
    return [ a ] + line + [ b ], math.dist(a, line[0]), math.dist(b, line[-1])
left, la, lb = attach(left); right, ra, rb = attach(right)

# 5. contrôles
problems = []
def check_against_rails(line, name):
    for i in range(1, len(line) - 2):
        p, q = line[i], line[i + 1]
        if near_gap(p[0], p[1], 9): continue
        for s in d['segs']:
            if max(s[0], s[2]) < min(p[0], q[0]) - 1 or min(s[0], s[2]) > max(p[0], q[0]) + 1: continue
            if max(s[1], s[3]) < min(p[1], q[1]) - 1 or min(s[1], s[3]) > max(p[1], q[1]) + 1: continue
            if seg_inter(p, q, (s[0], s[1]), (s[2], s[3])):
                problems.append(f'{name} croise une barrière du circuit vers ({p[0]:.0f}, {p[1]:.0f})'); return
check_against_rails(left, 'bord gauche'); check_against_rails(right, 'bord droit')
# deux bords qui se croisent, ou tronçons de piste qui se touchent (hors voisinage)
def crossings(a, b, name, local):
    for i in range(len(a) - 1):
        for j in range(len(b) - 1):
            if local and abs(i - j) < 40: continue
            if seg_inter(a[i], a[i + 1], b[j], b[j + 1]):
                problems.append(f'{name} vers ({a[i][0]:.0f}, {a[i][1]:.0f})'); return
crossings(left, right, 'les deux bords se croisent', False)
for i in range(0, len(center), 3):
    for j in range(i + 30, len(center), 3):
        if math.dist(center[i], center[j]) < W + 1:
            # sauf si on reste dans le même virage (distance le long du trajet faible)
            problems.append(f'deux passages de la piste trop proches : ({center[i][0]:.0f}, {center[i][1]:.0f}) et ({center[j][0]:.0f}, {center[j][1]:.0f})'); break
    else: continue
    break
deep = [ p for p in center if G[toc(*p)] < DEEP ]
if deep: problems.append(f'{len(deep)} m de ligne centrale en eau profonde, ex. ({deep[0][0]:.0f}, {deep[0][1]:.0f})')
water = sum(1 for p in center if G[toc(*p)] < -0.05)

L = len(center) - 1
print(f'piste de l\'île : {L} m, dont {water} m dans l\'eau peu profonde ; raccords {la:.1f}/{lb:.1f}/{ra:.1f}/{rb:.1f} m')
for g in gates: print(f"  {g['name']:15s} ({g['x']:6.1f}, {g['z']:6.1f}) déplacée de {g['moved']} m")
print('PROBLÈMES :' if problems else 'aucun problème', *problems, sep='\n  ')
# route : prolongée de 7 m dans le circuit à chaque bout (recouvre le raccord avec la route du circuit), sans vibreurs sur ces prolongements
EXT = 7
def extend(p):
    a, b = p[0], p[1]; L = math.dist(a, b) or 1
    head = [ (a[0] - (b[0] - a[0]) / L * k, a[1] - (b[1] - a[1]) / L * k) for k in range(EXT, 0, -1) ]
    a, b = p[-1], p[-2]; L = math.dist(a, b) or 1
    tail = [ (a[0] - (b[0] - a[0]) / L * k, a[1] - (b[1] - a[1]) / L * k) for k in range(1, EXT + 1) ]
    return head + p + tail
ext = extend(center)
roadL = offset(ext, HALF_W + 0.3); roadR = offset(ext, -HALF_W - 0.3)
kerbL = offset(ext, HALF_W - 1.2); kerbR = offset(ext, -HALF_W + 1.2)
for i in list(range(EXT)) + list(range(len(ext) - EXT, len(ext))): kerbL[i] = roadL[i]; kerbR[i] = roadR[i]
json.dump({ 'kerbLeft': [ [ round(x, 2), round(z, 2) ] for x, z in kerbL ], 'kerbRight': [ [ round(x, 2), round(z, 2) ] for x, z in kerbR ], 'roadLeft': [ [ round(x, 2), round(z, 2) ] for x, z in roadL ], 'roadRight': [ [ round(x, 2), round(z, 2) ] for x, z in roadR ], 'width': W, 'center': [ [ round(x, 2), round(z, 2) ] for x, z in center ], 'left': [ [ round(x, 2), round(z, 2) ] for x, z in left ], 'right': [ [ round(x, 2), round(z, 2) ] for x, z in right ], 'gates': gates, 'problems': problems }, open('track_b.json', 'w'))
