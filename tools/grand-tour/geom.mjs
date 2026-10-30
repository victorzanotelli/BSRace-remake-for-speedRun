import { launch } from './runner.mjs'
import fs from 'node:fs'
const { newGame, close, errors } = await launch({ root: process.env.FOLIO_DIST || new URL('../../../folio-2025/dist', import.meta.url).pathname })
const page = await newGame('tas&skip')
const out = await page.evaluate(() => {
    const c = window.game.world.areas.circuit
    const pts = (mesh) => { mesh.updateWorldMatrix(true, true); const res = []; mesh.traverse(m => { if(!m.geometry) return; const p = m.geometry.attributes.position; const v = new m.position.constructor(); for(let i = 0; i < p.count; i++) { v.fromBufferAttribute(p, i).applyMatrix4(m.matrixWorld); res.push([ +v.x.toFixed(2), +v.y.toFixed(2), +v.z.toFixed(2) ]) } }); return res }
    const rails = pts(c.references.items.get('rails')[0])
    const road = pts(c.references.items.get('road')[0])
    const cps = c.courses.circuit.map(k => ({ x: k.position.x, z: k.position.z, rot: k.rotation, w: k.scale }))
    const body = c.roadBody; const cols = []
    for(let i = 0; i < body.numColliders(); i++) { const col = body.collider(i); { const t = col.translation(), r = col.rotation(), h = col.halfExtents(); cols.push({ t, r, h }) } }
    return { rails, road, cps, cols }
})
console.log(out.rails.length, JSON.stringify(out.cols.slice(0,3)), errors.slice(0,2))
fs.writeFileSync('circuit-geom.json', JSON.stringify(out))
await close()
