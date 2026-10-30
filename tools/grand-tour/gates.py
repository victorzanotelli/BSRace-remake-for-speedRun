import json, math, numpy as np
from collections import deque
d = json.load(open('map.json')); N, half = d['N'], d['half']; RES = d.get('res', 1)
G = np.array(d['ground']).reshape(N, N); T = np.array(d['top']).reshape(N, N); K = np.array(d['kind']).reshape(N, N)
H = np.where(T > -50, T - G, 0)
LOW = np.array(d.get('low', [99] * (N * N))).reshape(N, N)
H = np.where(LOW - np.maximum(G, 0) > 2.2, 0, H)  # obstacle en hauteur : la voiture passe dessous
blocked = ((K == 1) & (H > 0.35)) | ((K == 2) & (H > 0.2)) | (G < -0.05)
# distance au plus proche obstacle / eau (BFS 8-connexe)
dist = np.full((N, N), 1e9); q = deque()
for z in range(N):
    for x in range(N):
        if blocked[z, x]: dist[z, x] = 0; q.append((z, x))
while q:
    z, x = q.popleft()
    for dz in (-1, 0, 1):
        for dx in (-1, 0, 1):
            nz, nx = z + dz, x + dx
            if 0 <= nz < N and 0 <= nx < N and dist[nz, nx] > dist[z, x] + math.hypot(dz, dx):
                dist[nz, nx] = dist[z, x] + math.hypot(dz, dx); q.append((nz, nx))
dist = dist * RES
cell = lambda x, z: (int(math.floor((z + half) / RES)), int(math.floor((x + half) / RES)))
def place(cx, cz, clearance=6.0, rmax=20, avoid=()):
    best = None
    for z in range(N):
        for x in range(N):
            wx, wz = (x + 0.5) * RES - half, (z + 0.5) * RES - half
            r = math.hypot(wx - cx, wz - cz)
            if any(math.hypot(wx - ax, wz - az) < 10 for ax, az in avoid): continue
            if r <= rmax and dist[z, x] >= clearance and (best is None or r < best[0]): best = (r, wx, wz)
    return best
circuit = [ (-11.25, -0.47, 0.0), (37.06, -47.82, -math.pi / 2), (39.70, -80.26, math.pi / 2), (-15.45, -47.16, math.pi), (-61.81, -27.47, math.pi / 2), (-38.17, -66.28, -math.pi), (-60.84, 15.98, math.pi / 2), (-56.05, 70.52, -math.pi / 2) ]
order = [ 'lab', 'cookie', 'projects', 'career', 'social', 'behindTheScene', 'altar', 'achievements', 'landing', 'toilet', 'bowling', 'timeMachine' ]
gates = [ dict(x=x, z=z, rot=r, w=5, name=f'circuit {i}', fromCircuit=True) for i, (x, z, r) in enumerate(circuit) ]
MANUAL = { 'altar': (66.3, -27.9, 4.0), 'toilet': (63.0, 64.0, 4.0) }
for name in order:
    cx, cz = d['zones'][name]
    if name in MANUAL:
        x, z, w = MANUAL[name]
        gates.append(dict(x=x, z=z, w=w, name=name, offset=round(math.hypot(x - cx, z - cz), 1), clearance=w + 0.5, manual=True))
        continue
    p = place(cx, cz, clearance=(4.5 if name == 'timeMachine' else 6.0), avoid=[ (g['x'], g['z']) for g in gates ])
    if not p: print('AUCUNE place pour', name); continue
    r, x, z = p
    gates.append(dict(x=round(x, 2), z=round(z, 2), w=5, name=name, offset=round(r, 1), clearance=round(float(dist[cell(x, z)]), 1)))
# orientation des portes de zone : perpendiculaire à la direction (précédente → suivante)
seq = gates + [ gates[0] ]
for i, g in enumerate(gates):
    if g.get('fromCircuit'): continue
    prev, nxt = seq[i - 1], seq[i + 1]
    dx, dz = nxt['x'] - prev['x'], nxt['z'] - prev['z']
    g['rot'] = round(math.atan2(-dx, -dz), 4)
    if not g.get('manual'): g['w'] = round(min(6.0, max(4.0, g['clearance'] - 1.0)), 1)
L = sum(math.dist((seq[i]['x'], seq[i]['z']), (seq[i + 1]['x'], seq[i + 1]['z'])) for i in range(len(seq) - 1))
for i, g in enumerate(gates): print(f"{i:2d} {g['name']:15s} ({g['x']:7.2f}, {g['z']:7.2f}) rot {g['rot']:6.2f} demi-largeur {g['w']}" + (f"  (à {g['offset']} m du centre, dégagement {g['clearance']})" if 'offset' in g else ''))
print(f"longueur à vol d'oiseau : {L:.0f} u (circuit seul ~484)")
json.dump({ 'gates': gates }, open('gates.json', 'w'), indent=1)
