import { app, BrowserWindow, ipcMain } from 'electron'
import { createRequire } from 'node:module'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const require = createRequire(import.meta.url)
const __dirname = path.dirname(fileURLToPath(import.meta.url))

process.env.APP_ROOT = path.join(__dirname, '..')

// The built directory structure
//
// ├─┬─┬ dist
// │ │ └── index.html
// │ │
// │ ├─┬ dist-electron
// │ │ ├── main.js
// │ │ └── preload.js
// │
export const VITE_DEV_SERVER_URL = process.env['VITE_DEV_SERVER_URL']
export const MAIN_DIST = path.join(process.env.APP_ROOT, 'dist-electron')
export const RENDERER_DIST = path.join(process.env.APP_ROOT, 'dist')

process.env.VITE_PUBLIC = VITE_DEV_SERVER_URL ? path.join(process.env.APP_ROOT, 'public') : RENDERER_DIST

let win: BrowserWindow | null

function createWindow() {
  win = new BrowserWindow({
    width: 1280,
    height: 720,
    frame: false,
    transparent: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  })

  // IPC listeners for custom titlebar
  ipcMain.on('window-minimize', () => {
    win?.minimize()
  })
  
  ipcMain.on('window-maximize', () => {
    if (win?.isMaximized()) {
      win?.restore()
    } else {
      win?.maximize()
    }
  })
  
  ipcMain.on('window-close', () => {
    win?.close()
  })

  ipcMain.on('window-open-devtools', () => {
    win?.webContents.openDevTools({ mode: 'detach' })
  })

  // Start maxmized by default
  win.maximize()

  if (VITE_DEV_SERVER_URL) {
    win.loadURL(VITE_DEV_SERVER_URL)
  } else {
    // win.loadFile('dist/index.html')
    win.loadFile(path.join(RENDERER_DIST, 'index.html'))
  }
}

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
    win = null
  }
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow()
  }
})

app.whenReady().then(() => {
  const { session, globalShortcut } = require('electron')
  session.defaultSession.setPermissionRequestHandler((webContents, permission, callback) => {
    if (permission === 'geolocation') {
      callback(true)
    } else {
      callback(false)
    }
  })
  
  globalShortcut.register('F12', () => {
    if (win) win.webContents.openDevTools({ mode: 'detach' })
  })

  createWindow()
})

app.on('will-quit', () => {
  const { globalShortcut } = require('electron')
  globalShortcut.unregisterAll()
})

