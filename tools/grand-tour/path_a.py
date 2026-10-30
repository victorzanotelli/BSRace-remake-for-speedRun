# Trajet praticable porte par porte (A* sur la grille de l'île), lissé
import json, math, os, heapq, numpy as np
from collections import deque
d = json.load(open('map-a.json')); N, half = d['N'], d['half']; RES = d.get('res', 1)
G = np.array(d['ground']).reshape(N, N); T = np.array(d['top']).reshape(N, N); K = np.array(d['kind']).reshape(N, N)
H = np.where(T > -50, T - G, 0)
LOW = np.array(d.get('low', [99] * (N * N))).reshape(N, N)
H = np.where(LOW - np.maximum(G, 0) > 2.2, 0, H)  # obstacle en hauteur : la voiture passe dessous
obst = ((K == 1) & (H > 0.35)) | ((K == 2) & (H > 0.2))
# barrières du circuit (avec les ouvertures du Grand tour) : segments au sol
RAIL = np.zeros((N, N), bool)
for ax, az, bx, bz in d['segs']:
    n = int(math.hypot(bx - ax, bz - az) / (RES / 3)) + 1
    for i in range(n + 1):
        x = ax + (bx - ax) * i / n; z = az + (bz - az) * i / n
        zz, xx = int(math.floor((z + half) / RES)), int(math.floor((x + half) / RES))
        if 0 <= zz < N and 0 <= xx < N: RAIL[zz, xx] = True
# distance aux barrières (à part : on les longe de plus loin)
rdist = np.full((N, N), 1e9); q = deque()
for z, x in zip(*np.nonzero(RAIL)): rdist[z, x] = 0; q.append((z, x))
while q:
    z, x = q.popleft()
    for dz in (-1, 0, 1):
        for dx in (-1, 0, 1):
            nz, nx = z + dz, x + dx
            if 0 <= nz < N and 0 <= nx < N and rdist[nz, nx] > rdist[z, x] + math.hypot(dz, dx):
                rdist[nz, nx] = rdist[z, x] + math.hypot(dz, dx); q.append((nz, nx))
rdist = rdist * RES
# route du circuit (dalles) : on y tolère de passer plus près des obstacles fixes (chicane de 4 m)
cg = json.load(open('circuit-geom.json'))['cols']
ONROAD = np.zeros((N, N), bool)
xs = (np.arange(N) + 0.5) * RES - half
XX, ZZ = np.meshgrid(xs, xs)
for c in cg:
    t, r, h = c['t'], c['r'], c['h']; ang = 2 * math.atan2(r['y'], r['w'])
    dx_, dz_ = XX - t['x'], ZZ - t['z']
    lx = dx_ * math.cos(ang) - dz_ * math.sin(ang); lz = dx_ * math.sin(ang) + dz_ * math.cos(ang)
    ONROAD |= (abs(lx) < h['x']) & (abs(lz) < h['z'])
dyn = (K == 2) & (H > 0.2)
# distance aux obstacles
dist = np.full((N, N), 1e9); q = deque()
for z, x in zip(*np.nonzero(obst)): dist[z, x] = 0; q.append((z, x))
while q:
    z, x = q.popleft()
    for dz in (-1, 0, 1):
        for dx in (-1, 0, 1):
            nz, nx = z + dz, x + dx
            if 0 <= nz < N and 0 <= nx < N and dist[nz, nx] > dist[z, x] + math.hypot(dz, dx):
                dist[nz, nx] = dist[z, x] + math.hypot(dz, dx); q.append((nz, nx))
dist = dist * RES
WATER_OK = [ (66.3, -27.9), (55.0, 58.0) ]   # Autel, bras d'eau Accueil → Toilettes
# distance aux objets mobiles (on les pousse, mieux vaut les éviter largement)
ddist = np.full((N, N), 1e9); q = deque()
for z, x in zip(*np.nonzero(dyn)): ddist[z, x] = 0; q.append((z, x))
while q:
    z, x = q.popleft()
    for dz in (-1, 0, 1):
        for dx in (-1, 0, 1):
            nz, nx = z + dz, x + dx
            if 0 <= nz < N and 0 <= nx < N and ddist[nz, nx] > ddist[z, x] + math.hypot(dz, dx):
                ddist[nz, nx] = ddist[z, x] + math.hypot(dz, dx); q.append((nz, nx))
ddist = ddist * RES
def cost(z, x):
    if rdist[z, x] < 2.4 or ddist[z, x] < 2.2: return None          # trop près d'une barrière ou d'un objet mobile
    if dist[z, x] < (1.6 if ONROAD[z, x] else 2.0): return None     # trop près d'un obstacle fixe
    c = 1.0
    g = G[z, x]
    if g < -0.05:
        wx, wz = tow(z, x)
        if not any(math.hypot(wx - ax, wz - az) < 16 for ax, az in WATER_OK): return None
        c += 3 + 6 * min(1.5, -g)  # eau : lent
    if dist[z, x] < 5: c += (5 - dist[z, x]) * 1.5
    if rdist[z, x] < 4: c += (4 - rdist[z, x]) * 1.5
    if ddist[z, x] < 6: c += (6 - ddist[z, x]) * 1.5
    return c
toc = lambda x, z: (int(math.floor((z + half) / RES)), int(math.floor((x + half) / RES)))
tow = lambda z, x: ((x + 0.5) * RES - half, (z + 0.5) * RES - half)
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
                # près des portes (départ ou arrivée du tronçon), on tolère de passer à 1,2 m des obstacles fixes
                if c is None and min(math.hypot(nz - gz, nx - gx), math.hypot(nz - sz, nx - sx)) * RES < 5 and dist[nz, nx] >= 1.2 and rdist[nz, nx] >= 1.5:
                    c = 4.0
                if c is None and (nz, nx) != (gz, gx): continue
                ng = gs[(z, x)] + math.hypot(dz, dx) * RES * (c or 1)
                if ng < gs.get((nz, nx), 1e18):
                    gs[(nz, nx)] = ng; came[(nz, nx)] = (z, x)
                    heapq.heappush(openq, (ng + math.hypot(nz - gz, nx - gx) * RES, nz, nx))
    if (gz, gx) not in came: return None
    path = [ (gz, gx) ]
    while path[-1] != (sz, sx): path.append(came[path[-1]])
    return [ tow(z, x) for z, x in reversed(path) ]
def line_ok(p, q):
    n = int(math.dist(p, q) * 2 / RES) + 1
    for i in range(n + 1):
        x = p[0] + (q[0] - p[0]) * i / n; z = p[1] + (q[1] - p[1]) * i / n
        zz, xx = toc(x, z)
        if cost(zz, xx) is None or G[zz, xx] < -0.05 and G[toc(*p)] >= -0.05: return False
        # lissage : les raccourcis gardent de la marge (sinon ils frôlent les obstacles)
        if min(dist[zz, xx], ddist[zz, xx]) < 3.0 and min(math.dist((x, z), p), math.dist((x, z), q)) > 3: return False
    return True
def smooth(path):
    out = [ path[0] ]; i = 0
    while i < len(path) - 1:
        j = len(path) - 1
        while j > i + 1 and not line_ok(path[i], path[j]): j -= 1
        out.append(path[j]); i = j
    return out
gates = d['gates']
start = (d['start'][0], d['start'][2])
import re
gaps = [ (float(x), float(z)) for x, z in re.findall(r"name: '(?:exit|entry)', x: ([-\d.]+), z: ([-\d.]+)", open(os.environ.get('FOLIO_SRC', os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../folio-2025')) + '/sources/data/grandTour.js').read()) ]
# passages obligés : centre de l'ouverture de sortie (après la porte 7) et d'entrée (avant l'arrivée)
seq = [ (start, False) ] + [ ((g['x'], g['z']), True) for g in gates[:8] ] + [ (gaps[0], False) ] + [ ((g['x'], g['z']), True) for g in gates[8:] ] + [ (gaps[1], False), ((gates[0]['x'], gates[0]['z']), True) ]
full = []; legs = []; gate_idx = []
for (a, _), (b, isGate) in zip(seq, seq[1:]):
    p = astar(a, b)
    if p is None: print('PAS DE CHEMIN', a, '→', b); legs.append(None); continue
    s = smooth(p); legs.append(round(sum(math.dist(s[i], s[i + 1]) for i in range(len(s) - 1))))
    full += s if not full else s[1:]
    if isGate: gate_idx.append(len(full) - 1)
L = sum(math.dist(full[i], full[i + 1]) for i in range(len(full) - 1))
print(f"{len(full)} points, longueur du trajet {L:.0f} m ; tronçons {legs}")
# tangentes aux portes de zone (sens de course) pour orienter les portes
names = [ 'bowling', 'landing', 'toilet', 'achievements', 'altar', 'behindTheScene', 'social', 'career', 'projects', 'lab', 'cookie' ]
tang = {}
for k, n in enumerate(names):
    gi = gate_idx[8 + k]; a = full[max(0, gi - 1)]; b = full[min(len(full) - 1, gi + 1)]
    tang[n] = [ b[0] - a[0], b[1] - a[1] ]
json.dump(tang, open('tangents_a.json', 'w'))
clear = np.minimum(np.minimum(dist, ddist), rdist)
json.dump({ 'gates': [ { 'x': g['x'], 'z': g['z'], 'rot': g['rot'], 'w': g['w'] } for g in gates ], 'gateIdx': gate_idx, 'path': [ [ round(x, 2), round(z, 2) ] for x, z in full ], 'res': RES, 'half': half, 'N': N, 'clear': [ round(float(min(v, 20)), 1) for v in clear.flatten() ] }, open('path.json', 'w'))
