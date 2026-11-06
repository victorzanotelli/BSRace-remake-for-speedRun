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
for ax, az, bx, bz in d['segs']: dr.line([ tw(ax, az), tw(bx, bz) ], fill=(225, 40, 40, 255), width=2)
poly = [ tw(*p) for p in t['left'] ] + [ tw(*p) for p in reversed(t['right']) ]
dr.polygon(poly, fill=(60, 50, 60, 120))
for side in ('left', 'right'): dr.line([ tw(*p) for p in t[side] ], fill=(255, 140, 0, 255), width=3)
dr.line([ tw(*p) for p in t['center'] ], fill=(255, 230, 0, 160), width=1)
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 13)
for g in t['gates']:
    x, z, rot, w = g['x'], g['z'], g['rotation'], t['width'] / 2
    dr.line([ tw(x - w * math.cos(-rot), z - w * math.sin(-rot)), tw(x + w * math.cos(-rot), z + w * math.sin(-rot)) ], fill=(50, 255, 193, 255), width=4)
    X, Z = tw(x, z); dr.text((X + 8, Z - 8), g['name'], fill='white', font=F, stroke_width=3, stroke_fill=(20, 20, 20))
img.save(sys.argv[1] if len(sys.argv) > 1 else 'track_b.png'); print('ok')
