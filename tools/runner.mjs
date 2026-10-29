// Pilote le vrai jeu (mode #tas) dans un Chromium sans affichage
import http from 'node:http'
import fs from 'node:fs'
import path from 'node:path'
import { createRequire } from 'node:module'
const require = createRequire(import.meta.url)
const { chromium } = require('playwright')

const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.wasm': 'application/wasm', '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.webp': 'image/webp', '.mp3': 'audio/mpeg', '.woff2': 'font/woff2', '.woff': 'font/woff', '.ttf': 'font/ttf' }

export function serve(root, port = 0)
{
    return new Promise(resolve =>
    {
        const server = http.createServer((req, res) =>
        {
            let p = decodeURIComponent(new URL(req.url, 'http://x').pathname)
            if(p === '/') p = '/index.html'
            const file = path.normalize(path.join(root, p))
            if(!file.startsWith(root) || !fs.existsSync(file)) { res.writeHead(404); return res.end() }
            res.writeHead(200, { 'Content-Type': TYPES[path.extname(file)] || 'application/octet-stream' })
            fs.createReadStream(file).pipe(res)
        })
        server.listen(port, '127.0.0.1', () => resolve(server))
    })
}

export async function launch({ root, headless = true, width = 320, height = 180 } = {})
{
    const server = await serve(path.resolve(root))
    const port = server.address().port
    const browser = await chromium.launch({ headless, args: [ '--mute-audio', '--autoplay-policy=no-user-gesture-required' ] })
    const errors = []
    async function newGame()
    {
        const page = await browser.newPage({ viewport: { width, height } })
        page.on('pageerror', e => errors.push(e.message))
        await page.route(/^https?:\/\/(?!127\.0\.0\.1)/, r => r.abort()) // aucun accès extérieur
        await page.goto(`http://127.0.0.1:${port}/index.html#tas&skip`)
        await page.waitForFunction(() => window.game?.overlay && window.tas?.active, null, { timeout: 180000 })
        return page
    }
    async function close() { await browser.close(); server.close() }
    return { browser, newGame, close, errors }
}
