// Rejoue un movie dans une instance neuve et vérifie l'arrivée
import { launch } from './runner.mjs'
import fs from 'node:fs'
const data = JSON.parse(fs.readFileSync(process.argv[2]))
const map = { l: 'low', m: 'mid', h: 'high' }
const movie = data.inputs.map(([ t, s, b, k, j ]) => ({ throttle: t, steer: s, boost: !!b, brake: !!k, susp: j ? [ ...j ].map(c => map[c]) : null }))
const { newGame, close, errors } = await launch({ root: process.argv[3] || process.env.FOLIO_DIST || new URL('../../../folio-2025/dist', import.meta.url).pathname })
for(let run = 0; run < 2; run++)
{
    const page = await newGame(`tas&skip&course=${data.course}`)
    const r = await page.evaluate(({ movie, course }) => { window.tas.startRace(course); const r = window.tas.playMovie(movie, { record: false }); return { finished: r.finished, frame: r.finishFrame, time: r.time, reached: r.reached, p: r.final.p } }, { movie, course: data.course })
    console.log(`instance ${run + 1} : ${r.finished ? 'ARRIVÉE' : 'non terminé'} image ${r.frame}, chrono ${r.time?.toFixed(3)} s, portes ${r.reached}, position finale ${r.p.map(v => v.toFixed(4)).join(', ')}`)
    await page.close()
}
if(errors.length) console.log('Erreurs :', [ ...new Set(errors) ].slice(0, 3))
await close()
