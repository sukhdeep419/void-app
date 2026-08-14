export {}

declare global {
  interface Window {
    electronAPI?: {
      minimize: () => Promise<void>
      maximize: () => Promise<boolean>
      close: () => Promise<void>
      isMaximized: () => Promise<boolean>
      onMaximizeChange: (callback: (maximized: boolean) => void) => () => void
      openDevTools: () => Promise<void>
    }
  }
}
