// Carte de l'île : hauteur du sol, hauteur des obstacles, type de surface (grille 1 m)
import { launch } from './runner.mjs'
import fs from 'node:fs'
const { newGame, close } = await launch({ root: process.env.FOLIO_DIST || new URL('../../../folio-2025/dist', import.meta.url).pathname })
const page = await newGame()
const data = await page.evaluate(() =>
{
    const g = window.game, R = g.RAPIER, world = g.physics.world
    window.tas.step(5)
    window.__includeDisabled = true
    let en = 0, dis = 0, fixedEn = 0, fixedDis = 0
    world.bodies.forEach(b => { if(b.isEnabled()) { en++; if(b.isFixed()) fixedEn++ } else { dis++; if(b.isFixed()) fixedDis++ } })
    console.log('corps', en, dis, fixedEn, fixedDis)
    world.queryPipeline.update(world.colliders)
    const floorBody = g.world.floor.physical.body
    const half = g.terrain.size / 2
    const RES = 0.5
    const N = Math.round(g.terrain.size / RES)
    const ground = new Float32Array(N * N), top = new Float32Array(N * N), kind = new Uint8Array(N * N), low = new Float32Array(N * N)
    const up = new R.Ray({ x: 0, y: 0.3, z: 0 }, { x: 0, y: 1, z: 0 })
    const ray = new R.Ray({ x: 0, y: 60, z: 0 }, { x: 0, y: -1, z: 0 })
    const isFloor = (c) => c.parent() && c.parent().handle === floorBody.handle
    for(let iz = 0; iz < N; iz++)
        for(let ix = 0; ix < N; ix++)
        {
            const x = -half + (ix + 0.5) * RES, z = -half + (iz + 0.5) * RES
            ray.origin = { x, y: 60, z }
            const k = iz * N + ix
            // sol seul
            const hg = world.castRay(ray, 120, true, undefined, undefined, undefined, undefined, (c) => isFloor(c))
            ground[k] = hg ? 60 - hg.timeOfImpact : -99
            // premier obstacle (corps fixes ou dynamiques activés, hors sol)
            const ho = world.castRay(ray, 120, true, undefined, undefined, undefined, undefined, (c) => !isFloor(c) && c.parent() && (window.__includeDisabled || c.parent().isEnabled()))
            if(ho)
            {
                const c = typeof ho.collider === 'number' ? world.getCollider(ho.collider) : ho.collider
                top[k] = 60 - ho.timeOfImpact
                kind[k] = c.parent().isDynamic() ? 2 : 1
            }
            else top[k] = -99
            // bas de l'obstacle : rayon vers le haut depuis 30 cm au-dessus du sol
            up.origin = { x, y: Math.max(ground[k], 0) + 0.3, z }
            const hu = world.castRay(up, 20, false, undefined, undefined, undefined, undefined, (c) => !isFloor(c) && c.parent() && (window.__includeDisabled || c.parent().isEnabled()))
            low[k] = hu ? up.origin.y + hu.timeOfImpact : 99
        }
    // zones
    const zones = {}
    for(const [ name, area ] of Object.entries(g.world.areas)) if(area?.model) zones[name] = [ area.model.position.x, area.model.position.z ]
    return { stats: { en, dis, fixedEn, fixedDis }, N, half, res: RES, ground: Array.from(ground), top: Array.from(top), low: Array.from(low), kind: Array.from(kind), zones, water: g.water.surfaceElevation }
})
fs.writeFileSync('map.json', JSON.stringify(data))
console.log('corps activés/désactivés (fixes)', JSON.stringify(data.stats)); console.log('carte', data.N, 'x', data.N, 'zones', Object.keys(data.zones).join(', '))
await close()
