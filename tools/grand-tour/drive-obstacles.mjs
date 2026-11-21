// Pilote automatique : suit le trajet calculé dans le vrai jeu (Grand tour), sans affichage
import { launch } from './runner.mjs'
import fs from 'node:fs'
const { path, gateIdx, clear, res: RES, half, N } = JSON.parse(fs.readFileSync('path.json'))
const opts = { look: Number(process.argv[2] || 7), gain: Number(process.argv[3] || 2.2), boostAngle: Number(process.argv[4] || 0.35), corners: !process.env.NOCORNERS, maxf: Number(process.env.MAXF || 21600), trace: process.env.TRACE ? process.env.TRACE.split(',').map(Number) : null }
const { newGame, close, errors } = await launch({ root: '/home/claude/src/folio-2025/dist' })
const page = await newGame('tas&skip&course=tour')
const res = await page.evaluate(({ path, gateIdx, clear, res, half, N, opts }) =>
{
    const tas = window.tas, g = window.game, c = g.world.areas.circuit, v = g.physicalVehicle
    tas.startRace('tour')
    globalThis.__trace = opts.trace
    try {
    const movie = [], events = []
    const O = c.tourObstacles, carBody = v.chassis.physical.body
    let seg = 0, stuckFrames = 0, reverse = 0, lastReached = 0, islandIdx = -1
    const total = c.checkpoints.count + 2
    // abscisse sur la piste de l'île (null hors de l'île)
    const islandS = () =>
    {
        if(c.checkpoints.reachedCount < 8) return null
        const px = v.position.x, pz = v.position.z
        let best = -1, bestD = Infinity
        const from = islandIdx < 0 ? 0 : Math.max(0, islandIdx - 5), to = islandIdx < 0 ? O.centers.length : Math.min(O.centers.length, islandIdx + 30)
        for(let i = from; i < to; i++) { const d = Math.hypot(O.centers[i][0] - px, O.centers[i][1] - pz); if(d < bestD) { bestD = d; best = i } }
        if(bestD > 8 && islandIdx >= 0) { islandIdx = -1; return islandS() }
        if(bestD > 8) return null
        islandIdx = best
        return O.lengths[best]
    }
    // zones d'obstacles mobiles : recherche du meilleur moment de passage (essais avec savestates)
    const zones = [
        { name: 'murs', s0: 34, s1: 62, walls: O.walls, modes: [ 'react', 'L', 'R', 'C' ], waits: 120, waitStep: 6 },
        ...O.bars.map((bar) => ({ name: 'barre ' + bar.s, s0: bar.s - 13, s1: bar.s > 250 ? 286 : bar.s + 9, bars: [ bar ], modes: [ 'L', 'R' ], waits: 160, waitStep: 4 })),
    ]
    const offsetFor = (zone, mode, sCar) =>
    {
        if(zone.bars && sCar > zone.bars[0].s + 3) return 0
        if(mode === 'L') return 3.4
        if(mode === 'R') return -3.4
        if(mode === 'C') return 0
        // react : côté opposé au prochain mur, à l'heure d'arrivée estimée
        const next = zone.walls.find((wall) => wall.s > sCar - 1.5)
        if(!next) return 0
        const eta = (next.s - sCar) / Math.max(v.speed, 4)
        const offset = Math.sin((c.timer.elapsedTime + eta) * O.config.oscillation.speed + next.phase) * O.config.oscillation.amplitude
        return offset > 0 ? -3.8 : 3.8
    }
    const decide = (f, override) =>
    {
        const px = v.position.x, pz = v.position.z
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
        // zone d'obstacle : on vise l'axe de l'île décalé
        if(override)
        {
            const fr = O.frameAt(override.sCar + 6)
            const offset = offsetFor(override.zone, override.mode, override.sCar)
            tx = fr.x + fr.nx * offset; tz = fr.z + fr.nz * offset
        }
        const heading = Math.atan2(v.forward.z, v.forward.x), want = Math.atan2(tz - pz, tx - px)
        let diff = want - heading
        while(diff > Math.PI) diff -= 2 * Math.PI
        while(diff < -Math.PI) diff += 2 * Math.PI
        const cl = (x, z) => { const ix = Math.floor((x + half) / res), iz = Math.floor((z + half) / res); return ix >= 0 && iz >= 0 && ix < N && iz < N ? clear[iz * N + ix] : 0 }
        const tight = Math.min(cl(tx, tz), cl(px, pz), cl((px + tx) / 2, (pz + tz) / 2))
        let maxSpeed = tight < 3.2 ? 7 : tight < 4.5 ? 12 : 30
        if(opts.corners)
        {
            let dist = Math.hypot(path[seg + 1][0] - px, path[seg + 1][1] - pz)
            for(let k = seg + 1; k < Math.min(path.length - 1, seg + 6) && dist < 35; k++)
            {
                const [ ax, az ] = path[k - 1], [ bx, bz ] = path[k], [ cx2, cz2 ] = path[k + 1]
                let turn = Math.atan2(cz2 - bz, cx2 - bx) - Math.atan2(bz - az, bx - ax)
                while(turn > Math.PI) turn -= 2 * Math.PI
                while(turn < -Math.PI) turn += 2 * Math.PI
                const a = Math.abs(turn)
                if(a > 0.5) maxSpeed = Math.min(maxSpeed, 6 + 14 * (1 - a / Math.PI) + dist * 0.45)
                dist += Math.hypot(cx2 - bx, cz2 - bz)
            }
        }
        if(override) maxSpeed = Math.min(maxSpeed, override.zone.bars ? 9 : 11)
        let input = { throttle: v.speed > maxSpeed ? 0 : 1, steer: Math.max(-1, Math.min(1, -diff * opts.gain)), boost: !override && Math.abs(diff) < opts.boostAngle && gateDistance > 30 && v.speed < 28 && tight > 6, brake: v.speed > maxSpeed * 1.3, susp: null }
        if(Math.abs(diff) > 0.9 && v.speed > 9) input = { ...input, throttle: 0, brake: true, boost: false }
        if(override && override.waiting) input = { ...input, throttle: 0, brake: true, boost: false }
        if(reverse > 0) { input = { throttle: -1, steer: Math.sign(diff) || 1, boost: false, brake: false, susp: null }; reverse-- }
        else if(f > 120 && v.speed < 1.0 && v.position.y > 0.6 && !(override && override.waiting)) { if(++stuckFrames > 90) { reverse = 60; stuckFrames = 0; events.push(`coincé à ${f} (${px.toFixed(0)}, ${pz.toFixed(0)})`) } }
        else stuckFrames = 0
        return input
    }
    const hitting = (zone) =>
    {
        const bodies = [ ...(zone.walls || []), ...(zone.bars || []) ].map((item) => item.body)
        let hit = false
        for(const body of bodies)
            for(let i = 0; i < body.numColliders(); i++)
                for(let j = 0; j < carBody.numColliders(); j++)
                    c.game.physics.world.contactPair(body.collider(i), carBody.collider(j), (manifold) => { if(manifold.numContacts() > 0) hit = true })
        return hit
    }
    const afterStep = (f) =>
    {
        if(c.checkpoints.reachedCount !== lastReached)
        {
            seg = Math.max(seg, gateIdx[c.checkpoints.reachedCount - 1] ?? seg)
            lastReached = c.checkpoints.reachedCount
            events.push(`porte ${lastReached}/${total} à ${(f / 60).toFixed(1)} s${c.checkpoints.last?.label ? ' (' + c.checkpoints.last.label + ')' : ''}`)
        }
    }
    const jsState = () => ({ seg, stuckFrames, reverse, lastReached, islandIdx, events: events.length })
    const setJsState = (st) => { ({ seg, stuckFrames, reverse, lastReached, islandIdx } = st); events.length = st.events }
    const runZone = (zone, f0) =>
    {
        const snap = tas.saveState(), js = jsState()
        let best = null, tries = 0
        for(const mode of zone.modes)
            for(let wait = 0; wait <= zone.waits; wait += zone.waitStep)
            {
                if(best && wait >= best.frames) break
                tas.loadState(snap); setJsState(js)
                const inputs = []
                let ok = false, passed = null
                for(let k = 0; k < 60 * 8 + 150; k++)
                {
                    const sCar = passed === null ? islandS() : null
                    if(passed === null && sCar !== null && sCar >= zone.s1) passed = k
                    if(passed !== null && k >= passed + 150) { ok = v.speed > 3 && v.position.y > 0.5; break }
                    if(passed === null && k >= 60 * 8) break
                    const input = decide(f0 + k, passed === null ? { zone, mode, sCar: sCar ?? zone.s0, waiting: k < wait } : null)
                    inputs.push(input); tas.input = input; tas.step()
                    if(c.checkpoints.reachedCount !== lastReached) { seg = Math.max(seg, gateIdx[c.checkpoints.reachedCount - 1] ?? seg); lastReached = c.checkpoints.reachedCount }
                    if(hitting(zone) || v.position.y < 0) break
                }
                tries++
                if(ok && (!best || passed < best.frames)) best = { frames: passed, inputs, mode, wait }
            }
        tas.loadState(snap); setJsState(js)
        events.push(`zone ${zone.name} : ${best ? `mode ${best.mode}, attente ${best.wait} img, ${best.frames} img` : 'AUCUN passage sans contact'} (${tries} essais)`)
        return best
    }
    for(let f = 0; f < (opts.trace ? opts.trace[1] : opts.maxf); f++)
    {
        const px = v.position.x, pz = v.position.z
        const sCar = islandS()
        const zone = sCar !== null && zones.find((z) => !z.done && sCar >= z.s0 && sCar < z.s1)
        if(zone)
        {
            zone.done = true
            const best = runZone(zone, f)
            if(best)
            {
                for(const input of best.inputs)
                {
                    movie.push(input); tas.input = input; tas.step(); f++
                    afterStep(f)
                }
                globalThis.__lastP = [ v.position.x, v.position.z ]
                // resynchronise le suivi de trajet (les images rejouées n'ont pas avancé seg)
                {
                    const from = gateIdx[c.checkpoints.reachedCount - 1] ?? 0, to = gateIdx[Math.min(c.checkpoints.reachedCount, gateIdx.length - 1)]
                    let bestD = Infinity
                    for(let i = from; i < to; i++) { const d = Math.hypot(path[i][0] - v.position.x, path[i][1] - v.position.z); if(d < bestD) { bestD = d; seg = i } }
                }
                f--
                if(c.state !== 3) break
                continue
            }
        }
        const input = decide(f, null)
        if(globalThis.__lastP && Math.hypot(px - __lastP[0], pz - __lastP[1]) > 3) events.push(`téléporté à ${f} : (${__lastP.map(v => v.toFixed(0))}) → (${px.toFixed(0)}, ${pz.toFixed(0)})`)
        globalThis.__lastP = [ px, pz ]
        if(globalThis.__trace && f % (__trace[2] || 60) === 0 && f > __trace[0] && f < __trace[1]) events.push(`  ${f} (${px.toFixed(1)}, ${v.position.y.toFixed(1)}, ${pz.toFixed(1)}) s ${sCar?.toFixed(0)} v ${v.speed.toFixed(1)}`)
        movie.push(input)
        tas.input = input
        tas.step()
        afterStep(f)
        if(c.state !== 3) break
    }
    return { finished: c.checkpoints.reachedCount >= total, time: c.timer.elapsedTime, frames: movie.length, reached: c.checkpoints.reachedCount, total, events, movie }
    } catch(e) { return { error: e.stack.split('\n').slice(0, 8).join('\n') + '\nimage ' + (tas.frame - tas.raceStartFrame) + ' portes ' + c.checkpoints.reachedCount, events: [], movie: [], time: 0 } }
}, { path, gateIdx, clear, res: RES, half, N, opts })
if(res.error) { console.log(res.error); process.exit(0) }
console.log(res.events.join('\n'))
console.log(`→ ${res.finished ? 'ARRIVÉE' : 'non terminé'} : portes ${res.reached}/${res.total}, ${res.frames} images, chrono ${res.time.toFixed(2)} s`)
if(res.finished) fs.writeFileSync(process.env.OUT || 'autopilot-tour.json', JSON.stringify(res.movie))
if(errors.length) console.log('Erreurs :', [ ...new Set(errors) ].slice(0, 3))
await close()
