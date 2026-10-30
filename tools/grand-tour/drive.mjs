// Pilote automatique : suit le trajet calculé dans le vrai jeu (Grand tour), sans affichage
import { launch } from './runner.mjs'
import fs from 'node:fs'
const { path, gateIdx, clear, res: RES, half, N } = JSON.parse(fs.readFileSync('path.json'))
const opts = { look: Number(process.argv[2] || 7), gain: Number(process.argv[3] || 2.2), boostAngle: Number(process.argv[4] || 0.35) }
const { newGame, close, errors } = await launch({ root: process.env.FOLIO_DIST || new URL('../../../folio-2025/dist', import.meta.url).pathname })
const page = await newGame('tas&skip&course=tour')
const res = await page.evaluate(({ path, gateIdx, clear, res, half, N, opts }) =>
{
    const tas = window.tas, g = window.game, c = g.world.areas.circuit, v = g.physicalVehicle
    tas.startRace('tour')
    try {
    const movie = [], events = []
    let seg = 0, stuckFrames = 0, reverse = 0, lastReached = 0
    const total = c.checkpoints.count + 2
    for(let f = 0; f < 60 * 60 * 6; f++)
    {
        const px = v.position.x, pz = v.position.z
        // avance sur le trajet : point le plus proche dans une fenêtre
        const legEnd = gateIdx[Math.min(c.checkpoints.reachedCount, gateIdx.length - 1)]
        let best = seg, bestD = Infinity
        for(let i = seg; i < Math.min(legEnd, seg + 6); i++)
        {
            const [ ax, az ] = path[i], [ bx, bz ] = path[i + 1]
            const vx = bx - ax, vz = bz - az, l2 = vx * vx + vz * vz || 1
            const t = Math.max(0, Math.min(1, ((px - ax) * vx + (pz - az) * vz) / l2))
            const d = Math.hypot(ax + vx * t - px, az + vz * t - pz)
            if(d < bestD) { bestD = d; best = i }
        }
        seg = best
        // point visé : look mètres plus loin sur le trajet
        let remaining = opts.look, i = seg, tx = path[Math.min(seg + 1, path.length - 1)][0], tz = path[Math.min(seg + 1, path.length - 1)][1]
        let cx = px, cz = pz
        while(i < path.length - 1)
        {
            const [ bx, bz ] = path[i + 1]
            const d = Math.hypot(bx - cx, bz - cz)
            if(d >= remaining) { tx = cx + (bx - cx) * remaining / d; tz = cz + (bz - cz) * remaining / d; break }
            remaining -= d; cx = bx; cz = bz; i++; tx = bx; tz = bz
        }
        const gate = c.checkpoints.target
        const gateDistance = gate ? Math.hypot(gate.center.x - px, gate.center.y - pz) : Infinity
        if(gate && gateDistance < 10) { tx = gate.center.x; tz = gate.center.y }
        const heading = Math.atan2(v.forward.z, v.forward.x), want = Math.atan2(tz - pz, tx - px)
        let diff = want - heading
        while(diff > Math.PI) diff -= 2 * Math.PI
        while(diff < -Math.PI) diff += 2 * Math.PI
        const cl = (x, z) => { const ix = Math.floor((x + half) / res), iz = Math.floor((z + half) / res); return ix >= 0 && iz >= 0 && ix < N && iz < N ? clear[iz * N + ix] : 0 }
        const tight = Math.min(cl(tx, tz), cl(px, pz), cl((px + tx) / 2, (pz + tz) / 2))
        const maxSpeed = tight < 3.2 ? 7 : tight < 4.5 ? 12 : 30
        let input = { throttle: v.speed > maxSpeed ? 0 : 1, steer: Math.max(-1, Math.min(1, -diff * opts.gain)), boost: Math.abs(diff) < opts.boostAngle && gateDistance > 30 && v.speed < 28 && tight > 6, brake: v.speed > maxSpeed * 1.3, susp: null }
        if(Math.abs(diff) > 0.9 && v.speed > 9) input = { ...input, throttle: 0, brake: true, boost: false }
        // coincé : marche arrière quelques instants
        if(reverse > 0) { input = { throttle: -1, steer: Math.sign(diff) || 1, boost: false, brake: false, susp: null }; reverse-- }
        else if(f > 120 && v.speed < 1.0 && v.position.y > 0.6) { if(++stuckFrames > 90) { reverse = 60; stuckFrames = 0; events.push(`coincé à ${f} (${px.toFixed(0)}, ${pz.toFixed(0)})`) } }
        else stuckFrames = 0
        movie.push(input)
        tas.input = input
        tas.step()
        if(c.checkpoints.reachedCount !== lastReached)
        {
            seg = Math.max(seg, gateIdx[c.checkpoints.reachedCount - 1] ?? seg)
            lastReached = c.checkpoints.reachedCount
            events.push(`porte ${lastReached}/${total} à ${(f / 60).toFixed(1)} s${c.checkpoints.last?.label ? ' (' + c.checkpoints.last.label + ')' : ''}`)
        }
        if(c.state !== 3) break
    }
    return { finished: c.checkpoints.reachedCount >= total, time: c.timer.elapsedTime, frames: movie.length, reached: c.checkpoints.reachedCount, total, events, movie }
    } catch(e) { return { error: e.stack.split('\n').slice(0, 8).join('\n') + '\nimage ' + (tas.frame - tas.raceStartFrame) + ' portes ' + c.checkpoints.reachedCount, events: [], movie: [], time: 0 } }
}, { path, gateIdx, clear, res: RES, half, N, opts })
if(res.error) { console.log(res.error); process.exit(0) }
console.log(res.events.join('\n'))
console.log(`→ ${res.finished ? 'ARRIVÉE' : 'non terminé'} : portes ${res.reached}/${res.total}, ${res.frames} images, chrono ${res.time.toFixed(2)} s`)
if(res.finished) fs.writeFileSync('autopilot-tour.json', JSON.stringify(res.movie))
if(errors.length) console.log('Erreurs :', [ ...new Set(errors) ].slice(0, 3))
await close()
