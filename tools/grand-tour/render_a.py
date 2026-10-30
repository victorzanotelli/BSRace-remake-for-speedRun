import json, math, sys, numpy as np
from PIL import Image, ImageDraw
d = json.load(open('map-a.json')); N, half, RES = d['N'], d['half'], d['res']
G = np.array(d['ground']).reshape(N, N); T = np.array(d['top']).reshape(N, N); K = np.array(d['kind']).reshape(N, N); LOW = np.array(d['low']).reshape(N, N)
S = 2
img = Image.new('RGB', (N*S, N*S)); px = img.load()
for z in range(N):
    for x in range(N):
        g = G[z, x]
        col = ((70,120,190) if g > -1.5 else (45,85,150)) if g < -0.05 else (110,165,100)
        h = T[z, x] - g if T[z, x] > -50 else 0
        if LOW[z, x] - max(g, 0) > 2.2: h = 0
        if K[z, x] == 1 and h > 0.35: col = (150, 90, 70)
        if K[z, x] == 2 and h > 0.2: col = (210, 190, 90)
        for a in range(S):
            for b in range(S): px[x*S+b, z*S+a] = col
dr = ImageDraw.Draw(img)
tw = lambda x, z: ((x + half) / RES * S, (z + half) / RES * S)
for ax, az, bx, bz in d['segs']: dr.line([tw(ax, az), tw(bx, bz)], fill=(230, 40, 40), width=2)
p = json.load(open('path.json'))
dr.line([tw(x, z) for x, z in p['path']], fill=(255, 220, 0), width=2)
for i, g in enumerate(d['gates']):
    x, z, rot, w = g['x'], g['z'], g['rot'], g['w']
    a = tw(x - w * math.cos(-rot), z - w * math.sin(-rot)); b = tw(x + w * math.cos(-rot), z + w * math.sin(-rot))
    dr.line([a, b], fill=(50, 255, 193), width=4); X, Z = tw(x, z); dr.text((X + 5, Z + 3), str(i), fill='white')
    # sens
    dx, dz = -math.sin(rot), -math.cos(rot); dr.line([tw(x, z), tw(x + dx * 4, z + dz * 4)], fill=(255, 0, 255), width=2)
img.save(sys.argv[1] if len(sys.argv) > 1 else 'map-a.png'); print('ok')
