# Grand tour (tracé B) : circuit de base + piste de l'île bordée de barrières → sources/data/grandTour.js
import json, math, os, re
SRC = os.environ.get('FOLIO_SRC', os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../folio-2025')) + '/sources/data/grandTour.js'
LABELS = { 'bowling': 'Bowling', 'landing': 'Accueil', 'toilet': 'Toilettes', 'achievements': 'Succès', 'altar': 'Autel', 'behindTheScene': 'Coulisses', 'social': 'Social', 'career': 'Carrière', 'projects': 'Projets', 'lab': 'Labo', 'cookie': 'Cookie' }
t = json.load(open('track_b.json'))
old = open(SRC).read()
gaps_block = re.search(r"export const grandTourRailGaps = \[[^\]]*\]", old).group(0)
pts = lambda arr: ', '.join(f'[{x:.2f}, {z:.2f}]' for x, z in arr)

# guidage : la ligne centrale de l'île, puis de l'ouverture d'entrée à la ligne d'arrivée (porte 0)
center = [ tuple(p) for p in t['center'] ]
finish = (-11.25, -0.47)
tail = [ center[-1] ]
steps = int(math.dist(center[-1], finish))
for i in range(1, steps + 1):
    tail.append((center[-1][0] + (finish[0] - center[-1][0]) * i / steps, center[-1][1] + (finish[1] - center[-1][1]) * i / steps))
guide = center + tail[1:]
leg_ends = [ 0 ] * 8 + [ g['i'] for g in t['gates'] ] + [ len(guide) - 1 ]

src = """/**
 * Grand tour (tracé B, depuis 1.5.0) : un tour complet du circuit avec ses barrières (portes 0 à 7),
 * sortie par une ouverture juste après la porte 7, puis une piste de l'île bordée de barrières
 * qui passe par une porte par zone, retour sur le circuit par une seconde ouverture, arrivée sur la porte 0.
 * Pendant la course, l'île est aplanie (World/Flatten.js). Données calculées par tools/grand-tour/track_b.py.
 * rotation : même convention que les portes du circuit ; halfWidth : demi-largeur de la porte
 */
export const grandTourGates = [
""" + "\n".join(f"    {{ name: '{g['name']}', label: '{LABELS[g['name']]}', x: {g['x']}, z: {g['z']}, rotation: {g['rotation']}, halfWidth: {t['width'] / 2} }}," for g in t['gates']) + """
]

// Ouvertures dans les barrières du circuit (les triangles des barrières à moins de radius mètres sont retirés)
""" + gaps_block + """

// Pendant le Grand tour : on ne renvoie au dernier checkpoint que dans l'eau profonde
export const grandTourOutOfBoundsY = -1.0

// Piste de l'île : bords de la route (left/right, même nombre de points) et barrières (polylignes)
export const grandTourIsland = {
    width: """ + str(t['width']) + """,
    roadLeft: [ """ + pts(t['roadLeft']) + """ ],
    roadRight: [ """ + pts(t['roadRight']) + """ ],
    kerbLeft: [ """ + pts(t['kerbLeft']) + """ ],
    kerbRight: [ """ + pts(t['kerbRight']) + """ ],
    barriers: [
        [ """ + pts(t['left']) + """ ],
        [ """ + pts(t['right']) + """ ]
    ]
}

// Guidage (flèche au sol, distance) : ligne centrale de l'île puis jusqu'à l'arrivée
// legEnds[k] = indice, dans points, de la porte visée quand k portes ont été franchies
export const grandTourGuide = {
    points: [ """ + pts(guide) + """ ],
    legEnds: [ """ + ', '.join(str(i) for i in leg_ends) + """ ]
}
"""
open(SRC, 'w').write(src)
print(len(t['gates']), 'portes ;', len(guide), 'points de guidage ; legEnds', leg_ends)
