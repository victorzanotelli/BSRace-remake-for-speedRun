# Trajet du pilote automatique sur le tracé B : partie circuit de path.json (tracé A), puis ligne centrale de l'île
import json, math, numpy as np, re, os
from collections import deque
old = json.load(open('path-a-circuit.json'))
t = json.load(open('track_b.json'))
d = json.load(open('map-a.json')); N, half, RES = d['N'], d['half'], d['res']
src = open(os.environ.get('FOLIO_SRC', os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../folio-2025')) + '/sources/data/grandTour.js').read()
gx, gz = [ (float(m[0]), float(m[1])) for m in re.findall(r"name: 'exit', x: ([-\d.]+), z: ([-\d.]+)", src) ][0]
P = old['path']; gi = old['gateIdx']
# jusqu'à la porte 7, puis jusqu'au point le plus proche de l'ouverture de sortie
k = min(range(gi[7], gi[8]), key=lambda i: math.dist(P[i], (gx, gz)))
path = P[:k] + t['center']
gate_idx = gi[:8] + [ k + g['i'] for g in t['gates'] ]
finish = (-11.25, -0.47); last = t['center'][-1]
steps = int(math.dist(last, finish))
for i in range(1, steps + 1): path.append([ last[0] + (finish[0] - last[0]) * i / steps, last[1] + (finish[1] - last[1]) * i / steps ])
gate_idx.append(len(path) - 1)
# dégagement (vitesse limitée près des barrières et des obstacles)
walls = np.zeros((N, N), bool)
toc = lambda x, z: (int(math.floor((z + half) / RES)), int(math.floor((x + half) / RES)))
lines = [ (s[0], s[1], s[2], s[3]) for s in d['segs'] ]
for line in t['left'], t['right']:
    for a, b in zip(line, line[1:]): lines.append((a[0], a[1], b[0], b[1]))
for ax, az, bx, bz in lines:
    n = int(math.hypot(bx - ax, bz - az) / (RES / 3)) + 1
    for i in range(n + 1):
        zz, xx = toc(ax + (bx - ax) * i / n, az + (bz - az) * i / n)
        if 0 <= zz < N and 0 <= xx < N: walls[zz, xx] = True
T = np.array(d['top']).reshape(N, N); G = np.array(d['ground']).reshape(N, N); K = np.array(d['kind']).reshape(N, N)
H = np.where(T > -50, T - np.maximum(G, 0), 0)
walls |= ((K == 1) & (H > 0.35)) | ((K == 2) & (H > 0.2))
dist = np.full((N, N), 1e9); q = deque()
for z, x in zip(*np.nonzero(walls)): dist[z, x] = 0; q.append((z, x))
while q:
    z, x = q.popleft()
    for dz in (-1, 0, 1):
        for dx in (-1, 0, 1):
            nz, nx = z + dz, x + dx
            if 0 <= nz < N and 0 <= nx < N and dist[nz, nx] > dist[z, x] + math.hypot(dz, dx):
                dist[nz, nx] = dist[z, x] + math.hypot(dz, dx); q.append((nz, nx))
dist *= RES
json.dump({ 'gateIdx': gate_idx, 'path': [ [ round(x, 2), round(z, 2) ] for x, z in path ], 'res': RES, 'half': half, 'N': N, 'clear': [ round(float(min(v, 20)), 1) for v in dist.flatten() ] }, open('path.json', 'w'))
print(len(path), 'points ; portes', gate_idx)
