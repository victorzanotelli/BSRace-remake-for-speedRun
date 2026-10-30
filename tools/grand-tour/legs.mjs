// Validation tronçon par tronçon : depuis chaque porte, le pilote doit atteindre la suivante en moins de 60 s
import { launch } from './runner.mjs'
import fs from 'node:fs'
const { path, gateIdx, clear, res, half, N } = JSON.parse(fs.readFileSync('path.json'))
const { newGame, close } = await launch({ root: process.env.FOLIO_DIST || new URL('../../../folio-2025/dist', import.meta.url).pathname })
const page = await newGame('tas&skip&course=tour')
if(process.argv[2]) await page.evaluate((k) => { window.__only = k; window.__trace = [] }, Number(process.argv[2]))
const out = await page.evaluate(({ path, gateIdx, clear, res, half, N }) =>
{
    const tas = window.tas, g = window.game, c = g.world.areas.circuit, v = g.physicalVehicle, THREE_V = v.position.constructor
    tas.startRace('tour')
    const items = c.checkpoints.items, total = items.length
    const results = []
    const ONLY = window.__only ?? null
    for(let k = (window.__only ?? 0); k <= (window.__only ?? total); k++)            // k = nombre de portes déjà passées ; on vise items[k % total]
    {
        const target = items[k % total]
        if(k > 0)
        {
            const prev = items[k - 1]
            c.checkpoints.reachedCount = k; c.checkpoints.last = prev; target.setTarget()
            const dx = target.center.x - prev.center.x, dz = target.center.y - prev.center.y
            const p = prev.position.clone(); p.y = 2
            v.moveTo(p, Math.atan2(-dz, dx))
            tas.step(30)                          // la voiture se pose
        }
        let seg = k > 0 ? gateIdx[k - 1] : 0, frames = 0, stuck = 0, reverse = 0, ok = false, stucks = 0
        for(; frames < 60 * 60; frames++)
        {
            const px = v.position.x, pz = v.position.z
            const legEnd = gateIdx[Math.min(k, gateIdx.length - 1)]
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
            let remaining = 7, i = seg, cx = px, cz = pz, tx = path[Math.min(seg + 1, legEnd)][0], tz = path[Math.min(seg + 1, legEnd)][1]
            while(i < legEnd)
            {
                const [ bx, bz ] = path[i + 1]
                const d = Math.hypot(bx - cx, bz - cz)
                if(d >= remaining) { tx = cx + (bx - cx) * remaining / d; tz = cz + (bz - cz) * remaining / d; break }
                remaining -= d; cx = bx; cz = bz; i++; tx = bx; tz = bz
            }
            const gd = Math.hypot(target.center.x - px, target.center.y - pz)
            if(gd < 10) { tx = target.center.x; tz = target.center.y }
            const heading = Math.atan2(v.forward.z, v.forward.x)
            let diff = Math.atan2(tz - pz, tx - px) - heading
            while(diff > Math.PI) diff -= 2 * Math.PI
            while(diff < -Math.PI) diff += 2 * Math.PI
            // dégagement autour du point visé : on ralentit dans les passages étroits
            const cl = (x, z) => { const ix = Math.floor((x + half) / res), iz = Math.floor((z + half) / res); return ix >= 0 && iz >= 0 && ix < N && iz < N ? clear[iz * N + ix] : 0 }
            const tight = Math.min(cl(tx, tz), cl(px, pz), cl((px + tx) / 2, (pz + tz) / 2))
            const maxSpeed = tight < 3.2 ? 7 : tight < 4.5 ? 12 : 30
            let input = { throttle: v.speed > maxSpeed ? 0 : 1, steer: Math.max(-1, Math.min(1, -diff * 2.2)), boost: Math.abs(diff) < 0.3 && gd > 30 && v.speed < 28 && tight > 6, brake: v.speed > maxSpeed * 1.3, susp: null }
            if(Math.abs(diff) > 0.9 && v.speed > 9) input = { ...input, throttle: 0, brake: true, boost: false }
            if(reverse > 0) { input = { throttle: -1, steer: Math.sign(diff) || 1, boost: false, brake: false, susp: null }; reverse-- }
            else if(frames > 60 && v.speed < 1.0 && v.position.y > 0.6) { if(++stuck > 60) { reverse = 50; stuck = 0; stucks++ } }
            else stuck = 0
            tas.input = input; tas.step()
            if(ONLY !== null && frames % 60 === 0) window.__trace.push(`${(frames / 60).toFixed(0)}s (${px.toFixed(1)}, ${v.position.y.toFixed(2)}, ${pz.toFixed(1)}) v=${v.speed.toFixed(1)} seg=${seg} cible=(${tx.toFixed(1)}, ${tz.toFixed(1)}) porte à ${gd.toFixed(1)} m`)
            if(c.checkpoints.reachedCount > k) { ok = true; break }
        }
        const prevLabel = k === 0 ? 'départ' : items[k - 1].label || `circuit ${k - 1}`
        const label = k === total ? 'arrivée' : target.label || (k === 0 ? 'ligne de départ' : `circuit ${k}`)
        results.push(`${ok ? '✔' : '✘'} ${prevLabel.padEnd(28)} → ${label.padEnd(28)} ${ok ? (frames / 60).toFixed(1) + ' s' : 'NON ATTEINTE'}${stucks ? ` (${stucks} blocage${stucks > 1 ? 's' : ''})` : ''}`)
        if(c.state !== 3) break
    }
    return results.concat(window.__trace || [])
}, { path, gateIdx, clear, res, half, N })
console.log(out.join('\n'))
const times = out.filter(l => l.startsWith('✔')).map(l => parseFloat(l.match(/([\d.]+) s/)[1]))
console.log(`total des tronçons réussis : ${times.reduce((a, b) => a + b, 0).toFixed(0)} s ; ${out.filter(l => l.startsWith('✘')).length} tronçon(s) non atteint(s)`)
await close()
