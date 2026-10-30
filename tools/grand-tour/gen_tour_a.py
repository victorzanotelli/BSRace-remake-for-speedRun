# Tracé A : 8 portes du circuit (avec barrières), sortie après la porte 7, 11 zones, retour par le circuit, arrivée sur la porte 0
import json, math, re, sys
import os
SRC = os.environ.get('FOLIO_SRC', os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../folio-2025')) + '/sources/data/grandTour.js'
# positions des portes de zone : relevées sur la carte praticable de l'île (version 1.3.0)
pos = {'lab': {'label': 'Labo', 'x': 14.5, 'z': 22.5, 'w': 5.2},
    'cookie': {'label': 'Cookie', 'x': 3.5, 'z': 33.5, 'w': 5.4},
    'projects': {'label': 'Projets', 'x': 28.5, 'z': 18.5, 'w': 5.2},
    'career': {'label': 'Carrière', 'x': 25.5, 'z': -0.5, 'w': 6.0},
    'social': {'label': 'Social', 'x': 33.5, 'z': -27.5, 'w': 5.0},
    'behindTheScene': {'label': 'Coulisses', 'x': 47.5, 'z': -15.5, 'w': 5.0},
    'altar': {'label': 'Autel', 'x': 66.3, 'z': -27.9, 'w': 4.0},
    'achievements': {'label': 'Succès', 'x': 68.5, 'z': 3.5, 'w': 5.0},
    'landing': {'label': 'Accueil', 'x': 43.5, 'z': 48.5, 'w': 5.2},
    'toilet': {'label': 'Toilettes', 'x': 63.0, 'z': 64.0, 'w': 4.0},
    'bowling': {'label': 'Bowling', 'x': 1.5, 'z': 68.5, 'w': 5.2},
    'timeMachine': {'label': 'Machine à remonter le temps', 'x': -45.5, 'z': -76.5, 'w': 4.0}}
# tracé A : la porte Succès est au sud du bâtiment (on arrive par le sud)
pos['achievements'].update(x=69.5, z=19.5, w=5.0)
# Toilettes : porte un peu plus au nord, on la traverse vers le nord-est sans descendre vers la cabane
pos['toilet'].update(x=62.0, z=61.5, w=4.0)
order = [ 'bowling', 'landing', 'toilet', 'achievements', 'altar', 'behindTheScene', 'social', 'career', 'projects', 'lab', 'cookie' ]
gaps = [ dict(name='exit', x=-25.0, z=66.5, radius=6.0), dict(name='entry', x=-4.6, z=35.5, radius=6.0) ]
# sens de passage : tangente du trajet (path_a.json) si disponible, sinon direction précédente → suivante
tang = json.load(open('tangents_a.json')) if len(sys.argv) > 1 and sys.argv[1] == 'tangents' else {}
pts = [ (gaps[0]['x'], gaps[0]['z']) ] + [ (pos[n]['x'], pos[n]['z']) for n in order ] + [ (gaps[1]['x'], gaps[1]['z']) ]
lines = []
for i, n in enumerate(order):
    if n in tang: dx, dz = tang[n]
    else:
        a, b = pts[i], pts[i + 2]; dx, dz = b[0] - a[0], b[1] - a[1]
    rot = math.atan2(-dx, -dz)   # sens de course = (-sin(rot), -cos(rot))
    p = pos[n]
    lines.append(f"    {{ name: '{n}', label: '{p['label']}', x: {p['x']}, z: {p['z']}, rotation: {rot:.4f}, halfWidth: {p['w']} }},")
src = """/**
 * Grand tour (tracé A) : un tour complet du circuit avec ses barrières (portes 0 à 7),
 * sortie par une ouverture juste après la porte 7, une porte par zone de l'île,
 * retour sur le circuit par une seconde ouverture, arrivée sur la ligne de départ (porte 0).
 * Positions calculées sur une carte praticable de l'île (sol, eau, obstacles) relevée dans le moteur physique.
 * rotation : même convention que les portes du circuit (le segment de la porte est perpendiculaire au sens de la course)
 * halfWidth : demi-largeur de la porte
 */
export const grandTourGates = [
""" + "\n".join(lines) + """
]

// Ouvertures dans les barrières du circuit (les triangles des barrières à moins de radius mètres sont retirés)
export const grandTourRailGaps = [
""" + "\n".join(f"    {{ name: '{g['name']}', x: {g['x']}, z: {g['z']}, radius: {g['radius']} }}," for g in gaps) + """
]

// Pendant le Grand tour : on ne renvoie au dernier checkpoint que dans l'eau profonde
export const grandTourOutOfBoundsY = -1.0
"""
open(SRC, 'w').write(src)
print(src)
