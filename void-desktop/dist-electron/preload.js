import { contextBridge, ipcRenderer } from "electron";
//#region electron/preload.ts
contextBridge.exposeInMainWorld("electronAPI", {
	minimize: () => ipcRenderer.invoke("window:minimize"),
	maximize: () => ipcRenderer.invoke("window:maximize"),
	close: () => ipcRenderer.invoke("window:close"),
	isMaximized: () => ipcRenderer.invoke("window:is-maximized"),
	onMaximizeChange: (callback) => {
		const listener = (_event, maximized) => callback(maximized);
		ipcRenderer.on("window:maximized-changed", listener);
		return () => ipcRenderer.removeListener("window:maximized-changed", listener);
	},
	openDevTools: () => ipcRenderer.invoke("window:open-devtools")
});
//#endregion
export {};
