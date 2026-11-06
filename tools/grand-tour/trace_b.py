# Image du tracé B (mode d'emploi) : île aplanie, circuit de base, piste de l'île, portes
import json, math, sys, numpy as np
from PIL import Image, ImageDraw, ImageFont
d = json.load(open('map-a.json')); N, half, RES = d['N'], d['half'], d['res']
t = json.load(open('track_b.json'))
G = np.array(d['ground']).reshape(N, N)
S = 2
img = Image.new('RGB', (N * S, N * S)); px = img.load()
for z in range(N):
    for x in range(N):
        g = G[z, x]
        col = ((70, 120, 190) if g > -0.9 else (45, 85, 150)) if g < -0.05 else (110, 165, 100)
        for a in range(S):
            for b in range(S): px[x * S + b, z * S + a] = col
dr = ImageDraw.Draw(img, 'RGBA')
tw = lambda x, z: ((x + half) / RES * S, (z + half) / RES * S)
poly = [ tw(*p) for p in t['roadLeft'] ] + [ tw(*p) for p in reversed(t['roadRight']) ]
dr.polygon(poly, fill=(56, 48, 57, 230))
for ax, az, bx, bz in d['segs']: dr.line([ tw(ax, az), tw(bx, bz) ], fill=(225, 40, 40, 255), width=3)
for side in ('left', 'right'): dr.line([ tw(*p) for p in t[side] ], fill=(225, 40, 40, 255), width=3)
F = lambda s: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', s)
LABELS = { 'bowling': 'Bowling', 'landing': 'Accueil', 'toilet': 'Toilettes', 'achievements': 'Succès', 'altar': 'Autel', 'behindTheScene': 'Coulisses', 'social': 'Social', 'career': 'Carrière', 'projects': 'Projets', 'lab': 'Labo', 'cookie': 'Cookie' }
for i, g in enumerate(d['gates'][:8]):
    X, Z = tw(g['x'], g['z']); dr.ellipse([ X - 11, Z - 11, X + 11, Z + 11 ], fill=(20, 20, 20, 235)); dr.text((X, Z), str(i), fill='white', font=F(12), anchor='mm')
for k, g in enumerate(t['gates']):
    x, z, rot, w = g['x'], g['z'], g['rotation'], t['width'] / 2
    dr.line([ tw(x - w * math.cos(-rot), z - w * math.sin(-rot)), tw(x + w * math.cos(-rot), z + w * math.sin(-rot)) ], fill=(50, 255, 193, 255), width=5)
    X, Z = tw(x, z); dr.text((X + 10, Z - 8), f'{8 + k} {LABELS[g["name"]]}', fill='white', font=F(13), stroke_width=3, stroke_fill=(20, 20, 20))
dr.rectangle([ 0, 0, N * S, 44 ], fill=(15, 15, 25, 215))
dr.text((10, 8), 'Grand tour (tracé B) : circuit 0 → 7, piste de l\'île (8 → 18), arrivée sur 0', fill='white', font=F(17))
img.save(sys.argv[1] if len(sys.argv) > 1 else 'trace_b.png'); print('ok')
