import { contextBridge as e, ipcRenderer as t } from "electron";
//#region electron/preload.ts
e.exposeInMainWorld("electronAPI", {
	minimize: () => t.send("window-minimize"),
	maximize: () => t.send("window-maximize"),
	close: () => t.send("window-close"),
	openDevTools: () => t.send("window-open-devtools")
});
//#endregion
export {};
