import { createRequire as e } from "node:module";
import { BrowserWindow as t, app as n, ipcMain as r } from "electron";
import { fileURLToPath as i } from "node:url";
import a from "node:path";
//#region electron/main.ts
var o = e(import.meta.url), s = a.dirname(i(import.meta.url));
process.env.APP_ROOT = a.join(s, "..");
var c = process.env.VITE_DEV_SERVER_URL, l = a.join(process.env.APP_ROOT, "dist-electron"), u = a.join(process.env.APP_ROOT, "dist");
process.env.VITE_PUBLIC = c ? a.join(process.env.APP_ROOT, "public") : u;
var d;
function f() {
	d = new t({
		width: 1280,
		height: 720,
		frame: !1,
		transparent: !0,
		webPreferences: {
			preload: a.join(s, "preload.js"),
			contextIsolation: !0,
			nodeIntegration: !1
		}
	}), r.on("window-minimize", () => {
		d?.minimize();
	}), r.on("window-maximize", () => {
		d?.isMaximized() ? d?.restore() : d?.maximize();
	}), r.on("window-close", () => {
		d?.close();
	}), r.on("window-open-devtools", () => {
		d?.webContents.openDevTools({ mode: "detach" });
	}), d.maximize(), c ? d.loadURL(c) : d.loadFile(a.join(u, "index.html"));
}
n.on("window-all-closed", () => {
	process.platform !== "darwin" && (n.quit(), d = null);
}), n.on("activate", () => {
	t.getAllWindows().length === 0 && f();
}), n.whenReady().then(() => {
	let { session: e, globalShortcut: t } = o("electron");
	e.defaultSession.setPermissionRequestHandler((e, t, n) => {
		n(t === "geolocation");
	}), t.register("F12", () => {
		d && d.webContents.openDevTools({ mode: "detach" });
	}), f();
}), n.on("will-quit", () => {
	let { globalShortcut: e } = o("electron");
	e.unregisterAll();
});
//#endregion
export { l as MAIN_DIST, u as RENDERER_DIST, c as VITE_DEV_SERVER_URL };
