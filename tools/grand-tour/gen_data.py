import json, os
gates = json.load(open('gates.json'))['gates']
zone = [ g for g in gates if not g.get('fromCircuit') ]
labels = { 'lab': 'Labo', 'cookie': 'Cookie', 'projects': 'Projets', 'career': 'Carrière', 'social': 'Social', 'behindTheScene': 'Coulisses', 'altar': 'Autel', 'achievements': 'Succès', 'landing': 'Accueil', 'toilet': 'Toilettes', 'bowling': 'Bowling', 'timeMachine': 'Machine à remonter le temps' }
lines = [ f"    {{ name: '{g['name']}', label: '{labels[g['name']]}', x: {g['x']}, z: {g['z']}, rotation: {g['rot']}, halfWidth: {g['w']} }}," for g in zone ]
src = """/**
 * Grand tour : après les 8 portes du circuit, une porte par zone de l'île, puis arrivée sur la ligne de départ.
 * Positions calculées sur une carte praticable de l'île (sol, eau, obstacles) relevée dans le moteur physique,
 * avec au moins 4 à 6 m dégagés autour de chaque porte.
 * rotation : même convention que les portes du circuit (le segment de la porte est perpendiculaire au sens de la course)
 * halfWidth : demi-largeur de la porte
 */
export const grandTourGates = [
""" + "\n".join(lines) + """
]

// Pendant le Grand tour : on ne renvoie au dernier checkpoint que dans l'eau profonde
export const grandTourOutOfBoundsY = -1.0
"""
open(os.environ.get('FOLIO_SRC', '../../../folio-2025') + '/sources/data/grandTour.js', 'w').write(src)
print('données écrites :', len(zone), 'portes de zone')
