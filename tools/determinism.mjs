// Test 1 : le même movie joué dans deux instances neuves du jeu donne-t-il exactement la même trajectoire ?
import { launch } from './runner.mjs'

const ROOT = process.argv[2] || '../../folio-2025/dist'

// Movie de test : plein gaz + boost, virages alternés, un saut, du frein
const movie = []
for(let f = 0; f < 900; f++)
    movie.push({
        throttle: 1,
        boost: f > 60,
        steer: Math.sin(f / 50) * 0.6,
        brake: f > 400 && f < 420,
        jump: f > 600 && f < 610
    })

const { newGame, close, errors } = await launch({ root: ROOT })
const runs = []
for(let r = 0; r < 2; r++)
{
    const page = await newGame()
    const t0 = Date.now()
    const start = await page.evaluate(() => window.tas.startRace())
    const t1 = Date.now()
    const result = await page.evaluate(m => window.tas.playMovie(m, { stopAtFinish: false }), movie)
    const t2 = Date.now()
    console.log(`run ${r}: départ à l'image ${await page.evaluate(() => window.tas.raceStartFrame)} (${t1 - t0} ms), ${movie.length} images en ${t2 - t1} ms → ${((t2 - t1) / movie.length).toFixed(2)} ms/image ; position finale ${result.final.p.map(v => v.toFixed(3)).join(', ')} ; portes ${result.reached}`)
    runs.push({ start, result })
    await page.close()
}
const [ a, b ] = runs.map(r => r.result.log)
let firstDiff = -1, maxDiff = 0
for(let i = 0; i < Math.min(a.length, b.length); i++)
{
    const d = Math.max(...a[i].p.map((v, k) => Math.abs(v - b[i].p[k])), ...a[i].q.map((v, k) => Math.abs(v - b[i].q[k])))
    if(d > 0 && firstDiff < 0) firstDiff = i
    maxDiff = Math.max(maxDiff, d)
}
console.log(firstDiff < 0 ? `IDENTIQUE au bit près sur ${a.length} images` : `DIVERGENCE dès l'image ${firstDiff}, écart max ${maxDiff}`)
if(errors.length) console.log('Erreurs page :', [...new Set(errors)].slice(0, 5))
await close()
