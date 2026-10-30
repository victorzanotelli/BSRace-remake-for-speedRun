// Carte du Grand tour (tracé A) : départ lancé en mode 'tour' (route + terrain + barrières avec ouvertures)
import { launch } from './runner.mjs'
import fs from 'node:fs'
const { newGame, close, errors } = await launch({ root: process.env.FOLIO_DIST || new URL('../../../folio-2025/dist', import.meta.url).pathname })
const page = await newGame('tas&skip&course=tour')
const data = await page.evaluate(() =>
{
    const g = window.game, R = g.RAPIER, world = g.physics.world
    window.tas.startRace('tour')
    const c = g.world.areas.circuit
    world.queryPipeline?.update?.(world.colliders)
    const floorBody = g.world.floor.physical.body, road = c.roadBody, rails = c.rails.object.physical.body
    const vehicle = g.physicalVehicle.chassis.physical.body
    const half = g.terrain.size / 2, RES = 0.5, N = Math.round(g.terrain.size / RES)
    const ground = new Float32Array(N * N), top = new Float32Array(N * N), kind = new Uint8Array(N * N), low = new Float32Array(N * N)
    const up = new R.Ray({ x: 0, y: 0.3, z: 0 }, { x: 0, y: 1, z: 0 })
    const ray = new R.Ray({ x: 0, y: 60, z: 0 }, { x: 0, y: -1, z: 0 })
    const h = (c) => c.parent() && c.parent().handle
    // sol : terrain, route du circuit, et maillages fixes sur lesquels on roule (îlot de l'Autel…)
    const isGround = (c) => h(c) === floorBody.handle || h(c) === road.handle || (c.shapeType() === 6 && c.parent()?.isFixed() && h(c) !== rails.handle)
    const isObstacle = (c) => c.parent() && c.parent().isEnabled() && c.isEnabled() && !isGround(c) && h(c) !== vehicle.handle && h(c) !== rails.handle
    for(let iz = 0; iz < N; iz++)
        for(let ix = 0; ix < N; ix++)
        {
            const x = -half + (ix + 0.5) * RES, z = -half + (iz + 0.5) * RES, k = iz * N + ix
            ray.origin = { x, y: 60, z }
            const hg = world.castRay(ray, 120, true, undefined, undefined, undefined, undefined, (c) => isGround(c) && c.parent().isEnabled())
            ground[k] = hg ? 60 - hg.timeOfImpact : -99
            // obstacles : rayon depuis 2,2 m au-dessus du sol (ce qui est plus haut, toits et portiques, ne gêne pas la voiture)
            const base = Math.max(ground[k], 0) + 2.2
            ray.origin = { x, y: base, z }
            const ho = world.castRay(ray, base + 5, true, undefined, undefined, undefined, undefined, isObstacle)
            if(ho) { const cc = typeof ho.collider === 'number' ? world.getCollider(ho.collider) : ho.collider; top[k] = base - ho.timeOfImpact; kind[k] = cc.parent().isDynamic() ? 2 : 1 }
            else top[k] = -99
            up.origin = { x, y: Math.max(ground[k], 0) + 0.3, z }
            const hu = world.castRay(up, 20, false, undefined, undefined, undefined, undefined, isObstacle)
            low[k] = 0   // les obstacles relevés touchent tous la zone de la voiture
        }
    // petits obstacles ronds (troncs d'arbres, poteaux…) que la grille de 0,5 m peut manquer : on reporte leur emprise
    let small = 0
    world.colliders.forEach((cc) =>
    {
        if(!isObstacle(cc) || typeof cc.radius !== 'function') return
        const st = cc.shapeType()
        if(st !== 0 && st !== 2 && st !== 10 && st !== 11) return
        const r = cc.radius(), t = cc.translation()
        if(!(r > 0) || r > 3) return
        let hh = typeof cc.halfHeight === 'function' ? cc.halfHeight() : r
        if(!Number.isFinite(hh)) hh = r
        if(t.y - hh > 2.2) return
        small++
        for(let iz = Math.floor((t.z - r - 0.3 + half) / RES); iz <= Math.floor((t.z + r + 0.3 + half) / RES); iz++)
            for(let ix = Math.floor((t.x - r - 0.3 + half) / RES); ix <= Math.floor((t.x + r + 0.3 + half) / RES); ix++)
            {
                if(ix < 0 || iz < 0 || ix >= N || iz >= N) continue
                const x = -half + (ix + 0.5) * RES, z = -half + (iz + 0.5) * RES
                if(Math.hypot(x - t.x, z - t.z) > r + 0.3) continue
                const k = iz * N + ix
                top[k] = Math.max(top[k], t.y + hh)
                kind[k] = cc.parent().isDynamic() ? 2 : (kind[k] || 1)
            }
    })
    // barrières (collider du Grand tour) : segments au sol des triangles
    const col = c.rails.tourCollider, v = col.vertices(), ix = col.indices(), t = col.translation()
    const segs = []
    for(let i = 0; i < ix.length; i += 3)
    {
        const p = [ ix[i], ix[i + 1], ix[i + 2] ].map(j => [ v[j * 3] + t.x, v[j * 3 + 1] + t.y, v[j * 3 + 2] + t.z ])
        for(let a = 0; a < 3; a++) { const b = (a + 1) % 3; segs.push([ p[a][0], p[a][2], p[b][0], p[b][2] ]) }
    }
    const zones = {}
    for(const [ name, area ] of Object.entries(g.world.areas)) if(area?.model) zones[name] = [ area.model.position.x, area.model.position.z ]
    const gates = c.checkpoints.items.map(k => ({ x: k.position.x, z: k.position.z, rot: k.rotation, w: k.scale, label: k.label, respawn: [ k.respawnPosition.x, k.respawnPosition.z ] }))
    const st = window.tas.state()
    return { N, half, res: RES, ground: Array.from(ground), top: Array.from(top), low: Array.from(low), kind: Array.from(kind), zones, segs, gates, start: st.p,
        info: { railsEnabled: rails.isEnabled(), orig: c.rails.collider.isEnabled(), tour: col.isEnabled(), tri: ix.length / 3, origTri: c.rails.collider.indices().length / 3, road: road.isEnabled(), floor: floorBody.isEnabled(), count: c.checkpoints.count, course: c.course, hidden: g.interactivePoints.temporaryHidden, small } }
})
fs.writeFileSync('map-a.json', JSON.stringify(data))
console.log(JSON.stringify(data.info), 'départ', data.start, errors.slice(0, 2))
await close()
