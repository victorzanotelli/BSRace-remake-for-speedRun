# Image du tracé A (pour le mode d'emploi) : terrain, route, barrières avec ouvertures, portes, trajet du pilote automatique
import json, math, sys, re, os
from PIL import Image, ImageDraw, ImageFont
d = json.load(open('map-a.json')); N, half, RES = d['N'], d['half'], d['res']
cg = json.load(open('circuit-geom.json'))
p = json.load(open('path.json'))
S = 2
import numpy as np
G = np.array(d['ground']).reshape(N, N); T = np.array(d['top']).reshape(N, N); K = np.array(d['kind']).reshape(N, N)
img = Image.new('RGB', (N * S, N * S)); px = img.load()
for z in range(N):
    for x in range(N):
        g = G[z, x]
        col = ((70, 120, 190) if g > -1.5 else (45, 85, 150)) if g < -0.05 else (110, 165, 100)
        h = T[z, x] - g if T[z, x] > -50 else 0
        if K[z, x] == 1 and h > 0.35: col = (150, 110, 85)
        if K[z, x] == 2 and h > 0.2: col = (200, 185, 110)
        for a in range(S):
            for b in range(S): px[x * S + b, z * S + a] = col
dr = ImageDraw.Draw(img, 'RGBA')
tw = lambda x, z: ((x + half) / RES * S, (z + half) / RES * S)
for c in cg['cols']:
    t, r, h = c['t'], c['r'], c['h']; ang = 2 * math.atan2(r['y'], r['w']); pts = []
    for sx, sz in [ (-1, -1), (1, -1), (1, 1), (-1, 1) ]:
        lx, lz = sx * h['x'], sz * h['z']; pts.append(tw(t['x'] + lx * math.cos(ang) + lz * math.sin(ang), t['z'] - lx * math.sin(ang) + lz * math.cos(ang)))
    dr.polygon(pts, fill=(90, 90, 90, 90))
for ax, az, bx, bz in d['segs']: dr.line([ tw(ax, az), tw(bx, bz) ], fill=(225, 40, 40, 255), width=3)
dr.line([ tw(x, z) for x, z in p['path'] ], fill=(255, 210, 0, 255), width=3)
F = lambda s: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', s)
src = open(os.environ.get('FOLIO_SRC', os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../folio-2025')) + '/sources/data/grandTour.js').read()
for x, z in re.findall(r"name: '(?:exit|entry)', x: ([-\d.]+), z: ([-\d.]+)", src):
    X, Z = tw(float(x), float(z)); dr.ellipse([ X - 16, Z - 16, X + 16, Z + 16 ], outline=(255, 230, 0, 255), width=4)
for i, g in enumerate(d['gates']):
    x, z, rot, w = g['x'], g['z'], g['rot'], g['w']
    dr.line([ tw(x - w * math.cos(-rot), z - w * math.sin(-rot)), tw(x + w * math.cos(-rot), z + w * math.sin(-rot)) ], fill=(50, 255, 193, 255), width=5)
    X, Z = tw(x, z); lab = str(i) if i < 8 else str(i)
    dr.ellipse([ X - 11, Z - 11, X + 11, Z + 11 ], fill=(20, 20, 20, 235)); dr.text((X, Z), lab, fill='white', font=F(12), anchor='mm')
    if g.get('label'): dr.text((X + 14, Z - 8), g['label'], fill='white', font=F(13), stroke_width=3, stroke_fill=(20, 20, 20))
dr.rectangle([ 0, 0, N * S, 44 ], fill=(15, 15, 25, 215))
dr.text((10, 8), 'Grand tour (tracé A) : circuit 0 → 7, île (8 → 18), retour et arrivée sur 0', fill='white', font=F(17))
dr.rectangle([ 0, N * S - 30, N * S, N * S ], fill=(15, 15, 25, 200))
dr.text((10, N * S - 22), 'rouge : barrières · cercles jaunes : ouvertures · ligne jaune : trajet du pilote automatique (1:33.350)', fill='white', font=F(12))
img.save(sys.argv[1] if len(sys.argv) > 1 else 'trace-a.png'); print('ok')
