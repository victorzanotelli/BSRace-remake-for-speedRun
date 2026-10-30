import json, sys, numpy as np
from PIL import Image, ImageDraw, ImageFont
d = json.load(open('map.json'))
N, half = d['N'], d['half']
G = np.array(d['ground']).reshape(N, N); T = np.array(d['top']).reshape(N, N); K = np.array(d['kind']).reshape(N, N)
LOW = np.array(d.get('low', [99] * (N * N))).reshape(N, N)
RES = d.get('res', 1)
S = max(1, int(round(4 * RES)))
img = Image.new('RGB', (N * S, N * S))
px = img.load()
gy, gx = np.gradient(G); gy, gx = gy / RES, gx / RES
slope = np.hypot(gx, gy)
for z in range(N):
    for x in range(N):
        g = G[z, x]
        if g < 0: col = (40, 80, 160) if g > -1.5 else (20, 40, 110)
        else:
            v = int(min(255, 90 + g * 12)); col = (v // 2, v, v // 2)
            if slope[z, x] > 0.6: col = (120, 110, 70)
        h = T[z, x] - g if T[z, x] > -50 else 0
        if LOW[z, x] - max(g, 0) > 2.2: h = 0
        if K[z, x] == 1 and h > 0.35: col = (200, 50, 50) if h > 1.2 else (230, 140, 60)
        if K[z, x] == 2 and h > 0.2: col = (240, 220, 60)
        for dz in range(S):
            for dx in range(S): px[x * S + dx, z * S + dz] = col
dr = ImageDraw.Draw(img)
tow = lambda x, z: ((x + half) / RES * S, (z + half) / RES * S)
for name, (x, z) in d['zones'].items():
    X, Z = tow(x, z); dr.ellipse([X - 5, Z - 5, X + 5, Z + 5], outline='white', width=2); dr.text((X + 7, Z - 7), name, fill='white')
extra = json.load(open(sys.argv[1])) if len(sys.argv) > 1 else None
if extra:
    pts = extra['gates']
    for i, gt in enumerate(pts):
        x, z, rot, w = gt['x'], gt['z'], gt.get('rot', 0), gt.get('w', 5)
        import math
        # segment de la porte (comme le jeu : ±w le long de x, tourné de -rot)
        ax, az = x - w * math.cos(-rot), z - w * math.sin(-rot)
        bx, bz = x + w * math.cos(-rot), z + w * math.sin(-rot)
        dr.line([tow(ax, az), tow(bx, bz)], fill=(50, 255, 193), width=4)
        X, Z = tow(x, z); dr.text((X + 6, Z + 4), str(i), fill=(50, 255, 193))
    if 'path' in extra:
        dr.line([tow(x, z) for x, z in extra['path']], fill=(255, 255, 255), width=1)
for i in range(-96, 97, 16):
    X, _ = tow(i, 0); dr.line([X, 0, X, 6], fill='white'); dr.text((X + 2, 8), str(i), fill='white')
    _, Z = tow(0, i); dr.line([0, Z, 6, Z], fill='white'); dr.text((8, Z + 2), str(i), fill='white')
img.save(sys.argv[2] if len(sys.argv) > 2 else 'map.png')
print('ok')
