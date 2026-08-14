import { createRequire } from "node:module";
import { BrowserWindow, app, ipcMain } from "electron";
import { fileURLToPath } from "node:url";
import path from "node:path";
//#region electron/main.ts
var require = createRequire(import.meta.url);
var __dirname = path.dirname(fileURLToPath(import.meta.url));
process.env.APP_ROOT = path.join(__dirname, "..");
var VITE_DEV_SERVER_URL = process.env["VITE_DEV_SERVER_URL"];
var MAIN_DIST = path.join(process.env.APP_ROOT, "dist-electron");
var RENDERER_DIST = path.join(process.env.APP_ROOT, "dist");
process.env.VITE_PUBLIC = VITE_DEV_SERVER_URL ? path.join(process.env.APP_ROOT, "public") : RENDERER_DIST;
var win = null;
function getMainWindow() {
	return win;
}
function sendMaximizedState(browserWindow) {
	browserWindow.webContents.send("window:maximized-changed", browserWindow.isMaximized());
}
function registerWindowControls() {
	ipcMain.handle("window:minimize", () => {
		getMainWindow()?.minimize();
	});
	ipcMain.handle("window:maximize", () => {
		const browserWindow = getMainWindow();
		if (!browserWindow) return false;
		if (browserWindow.isMaximized()) browserWindow.unmaximize();
		else browserWindow.maximize();
		return browserWindow.isMaximized();
	});
	ipcMain.handle("window:close", () => {
		getMainWindow()?.close();
	});
	ipcMain.handle("window:is-maximized", () => {
		return getMainWindow()?.isMaximized() ?? false;
	});
	ipcMain.handle("window:open-devtools", () => {
		getMainWindow()?.webContents.openDevTools({ mode: "detach" });
	});
}
function createWindow() {
	win = new BrowserWindow({
		width: 1280,
		height: 720,
		frame: false,
		transparent: true,
		backgroundColor: "#00000000",
		webPreferences: {
			preload: path.join(__dirname, "preload.js"),
			contextIsolation: true,
			nodeIntegration: false,
			sandbox: false
		}
	});
	win.on("maximize", () => sendMaximizedState(win));
	win.on("unmaximize", () => sendMaximizedState(win));
	win.maximize();
	if (VITE_DEV_SERVER_URL) win.loadURL(VITE_DEV_SERVER_URL);
	else win.loadFile(path.join(RENDERER_DIST, "index.html"));
	win.webContents.on("did-finish-load", () => {
		if (win) sendMaximizedState(win);
	});
}
app.on("window-all-closed", () => {
	if (process.platform !== "darwin") {
		app.quit();
		win = null;
	}
});
app.on("activate", () => {
	if (BrowserWindow.getAllWindows().length === 0) createWindow();
});
app.whenReady().then(() => {
	const { session, globalShortcut } = require("electron");
	registerWindowControls();
	session.defaultSession.setPermissionRequestHandler((_webContents, permission, callback) => {
		callback(permission === "geolocation");
	});
	globalShortcut.register("F12", () => {
		getMainWindow()?.webContents.openDevTools({ mode: "detach" });
	});
	createWindow();
});
app.on("will-quit", () => {
	const { globalShortcut } = require("electron");
	globalShortcut.unregisterAll();
});
//#endregion
export { MAIN_DIST, RENDERER_DIST, VITE_DEV_SERVER_URL };
