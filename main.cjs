const { app, BrowserWindow, protocol, net, Menu } = require('electron')
const path = require('path')
const { pathToFileURL } = require('url')

const root = path.join(__dirname, 'app')

// Protocole app:// pour servir le jeu comme depuis un vrai serveur (fetch, wasm, modules ES)
protocol.registerSchemesAsPrivileged([
    { scheme: 'app', privileges: { standard: true, secure: true, supportFetchAPI: true, corsEnabled: true, stream: true } }
])

// Rendu : WebGL2 par défaut (fiable sous Linux) ; --webgpu pour tenter WebGPU via Vulkan
app.commandLine.appendSwitch('ignore-gpu-blocklist')
if(process.argv.includes('--webgpu'))
{
    app.commandLine.appendSwitch('enable-unsafe-webgpu')
    app.commandLine.appendSwitch('enable-features', 'Vulkan,WebGPU')
}
app.commandLine.appendSwitch('autoplay-policy', 'no-user-gesture-required')

// Options : --debug ouvre le jeu avec #debug (Tweakpane), --tas démarre directement dans l'éditeur TAS
const debug = process.argv.includes('--debug')
const tasMode = process.argv.includes('--tas')

// Pas de menu : les raccourcis (Ctrl+Z, Ctrl+S…) vont au jeu / à l'éditeur
Menu.setApplicationMenu(null)

function gameUrl()
{
    // Le paramètre "mode" force un vrai rechargement quand on bascule (un simple changement de # ne recharge pas)
    const hash = [ debug ? 'debug' : null, tasMode ? 'tas&skip&editor' : null ].filter(Boolean).join('&')
    return `app://game/index.html?mode=${tasMode ? 'tas' : 'play'}` + (hash ? '#' + hash : '')
}

function createWindow()
{
    const win = new BrowserWindow({
        width: 1600,
        height: 900,
        title: 'BS Folio Race',
        backgroundColor: '#000000',
        autoHideMenuBar: true,
        webPreferences: { contextIsolation: true, backgroundThrottling: false }
    })
    // F9 (bascule jeu normal ⟷ éditeur TAS) est géré dans la page (Tas.js)
    win.loadURL(gameUrl())
    win.webContents.on('before-input-event', (event, input) =>
    {
        if(input.type === 'keyDown' && input.key === 'F11') { win.setFullScreen(!win.isFullScreen()); event.preventDefault() }
        if(input.type === 'keyDown' && input.key === 'F12') { win.webContents.toggleDevTools(); event.preventDefault() }
    })
}

app.whenReady().then(() =>
{
    protocol.handle('app', (request) =>
    {
        let pathname = decodeURIComponent(new URL(request.url).pathname)
        if(pathname === '/' || pathname === '') pathname = '/index.html'
        const filePath = path.normalize(path.join(root, pathname))
        if(!filePath.startsWith(root)) return new Response('Forbidden', { status: 403 })
        return net.fetch(pathToFileURL(filePath).toString())
    })
    createWindow()
})

app.on('window-all-closed', () => app.quit())
