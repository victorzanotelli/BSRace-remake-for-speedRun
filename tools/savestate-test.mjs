// Test : une course jouée d'une traite == la même course avec sauvegardes / retours en arrière / reprises
import { launch } from './runner.mjs'
const ROOT = process.argv[2] || '../../folio-2025/dist'

function makeMovie(seed)
{
    let x = seed
    const rnd = () => (x = (x * 16807) % 2147483647) / 2147483647
    const movie = []
    let steer = 0
    for(let f = 0; f < 1500; f++)
    {
        if(f % 20 === 0) steer = (rnd() * 2 - 1) * 0.9
        movie.push({ throttle: rnd() < 0.9 ? 1 : -1, boost: rnd() < 0.7, steer, brake: rnd() < 0.03, jump: rnd() < 0.02 })
    }
    return movie
}

const { newGame, close, errors } = await launch({ root: ROOT })
for(const seed of [ 1, 7, 42 ])
{
    const movie = makeMovie(seed)

    // Référence : d'une traite
    let page = await newGame()
    const ref = await page.evaluate(m => { window.tas.startRace(); return window.tas.playMovie(m, { stopAtFinish: false }).log }, movie)
    await page.close()

    // Avec savestates : avance, sauvegarde, va plus loin, revient, reprend…
    page = await newGame()
    const out = await page.evaluate(m =>
    {
        const tas = window.tas
        tas.startRace()
        const states = {}
        const playTo = (target) => { const start = tas.frame - tas.raceStartFrame; for(let f = start; f < target; f++) { tas.input = m[f]; tas.step() } }
        const report = []
        // aller-retours
        const plan = [ [ 'to', 200 ], [ 'save', 'a' ], [ 'to', 700 ], [ 'save', 'b' ], [ 'to', 1100 ], [ 'load', 'a' ], [ 'to', 900 ], [ 'load', 'b' ], [ 'to', 1000 ], [ 'load', 'a' ], [ 'to', 450 ], [ 'save', 'c' ], [ 'to', 1300 ], [ 'load', 'c' ] ]
        for(const [ op, arg ] of plan)
        {
            if(op === 'to') playTo(arg)
            else if(op === 'save') { states[arg] = tas.saveState(); report.push(`save ${arg} @${tas.frame - tas.raceStartFrame} safe=${states[arg].safe}`) }
            else if(op === 'load') tas.loadState(states[arg])
        }
        // reprise finale enregistrée
        const from = tas.frame - tas.raceStartFrame
        const log = []
        for(let f = from; f < m.length; f++) { tas.input = m[f]; tas.step(); log.push(tas.state()) }
        return { from, log, report }
    }, movie)
    await page.close()

    let first = -1, max = 0
    for(let i = 0; i < out.log.length; i++)
    {
        const a = ref[out.from + 1 + i], b = out.log[i]
        const d = Math.max(...a.p.map((v, k) => Math.abs(v - b.p[k])), ...a.q.map((v, k) => Math.abs(v - b.q[k])), Math.abs(a.timer - b.timer), a.reached !== b.reached ? 1 : 0)
        if(d > 0 && first < 0) first = out.from + 1 + i
        max = Math.max(max, d)
    }
    const last = ref[ref.length - 1]
    console.log(`movie ${seed} (${out.report.join(', ')}) → reprise depuis ${out.from} : ` + (first < 0 ? `IDENTIQUE au bit près (${out.log.length} images ; portes ${last.reached}, y final ${last.p[1].toFixed(2)})` : `DIVERGE dès l'image ${first}, écart max ${max}`))
}
if(errors.length) console.log('Erreurs page :', [ ...new Set(errors) ].slice(0, 5))
await close()
