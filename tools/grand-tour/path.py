# Trajet praticable porte par porte (A* sur la grille de l'île), lissé
import json, math, heapq, numpy as np
from collections import deque
d = json.load(open('map.json')); N, half = d['N'], d['half']; RES = d.get('res', 1)
G = np.array(d['ground']).reshape(N, N); T = np.array(d['top']).reshape(N, N); K = np.array(d['kind']).reshape(N, N)
H = np.where(T > -50, T - G, 0)
LOW = np.array(d.get('low', [99] * (N * N))).reshape(N, N)
H = np.where(LOW - np.maximum(G, 0) > 2.2, 0, H)  # obstacle en hauteur : la voiture passe dessous
obst = ((K == 1) & (H > 0.35)) | ((K == 2) & (H > 0.2))
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
WATER_OK = [ (66.3, -27.9), (-54.5, -67.4), (55.0, 58.0) ]   # Autel, Machine à remonter le temps, bras d'eau Accueil → Toilettes
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
    if dist[z, x] < 2.2 or ddist[z, x] < 2.2: return None          # trop près d'un obstacle
    c = 1.0
    g = G[z, x]
    if g < -0.05:
        wx, wz = tow(z, x)
        if not any(math.hypot(wx - ax, wz - az) < 16 for ax, az in WATER_OK): return None
        c += 3 + 6 * min(1.5, -g)  # eau : lent
    if dist[z, x] < 5: c += (5 - dist[z, x]) * 1.5
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
    return True
def smooth(path):
    out = [ path[0] ]; i = 0
    while i < len(path) - 1:
        j = len(path) - 1
        while j > i + 1 and not line_ok(path[i], path[j]): j -= 1
        out.append(path[j]); i = j
    return out
gates = json.load(open('gates.json'))['gates']
start = (-9.23, 5.74)
seq = [ start ] + [ (g['x'], g['z']) for g in gates ] + [ (gates[0]['x'], gates[0]['z']) ]
full = []; legs = []; gate_idx = []
for a, b in zip(seq, seq[1:]):
    p = astar(a, b)
    if p is None: print('PAS DE CHEMIN', a, '→', b); legs.append(None); continue
    s = smooth(p); legs.append(len(s))
    full += s if not full else s[1:]
    gate_idx.append(len(full) - 1)
L = sum(math.dist(full[i], full[i + 1]) for i in range(len(full) - 1))
print(f"{len(full)} points, longueur du trajet {L:.0f} u ; tronçons {legs}")
clear = np.minimum(dist, ddist)
json.dump({ 'gates': gates, 'gateIdx': gate_idx, 'path': [ [ round(x, 2), round(z, 2) ] for x, z in full ], 'res': RES, 'half': half, 'N': N, 'clear': [ round(float(min(v, 20)), 1) for v in clear.flatten() ] }, open('path.json', 'w'))
