import { useEffect, useState } from 'react'
import { Copy, Minus, Square, X } from 'lucide-react'

function stopTitlebarDrag(event: React.MouseEvent) {
  event.preventDefault()
  event.stopPropagation()
}

export default function Titlebar() {
  const [isMaximized, setIsMaximized] = useState(false)

  useEffect(() => {
    let unsubscribe: (() => void) | undefined

    const syncMaximized = async () => {
      const maximized = await window.electronAPI?.isMaximized()
      if (typeof maximized === 'boolean') {
        setIsMaximized(maximized)
      }
    }

    syncMaximized()
    unsubscribe = window.electronAPI?.onMaximizeChange(setIsMaximized)

    return () => unsubscribe?.()
  }, [])

  const handleMinimize = () => {
    void window.electronAPI?.minimize()
  }

  const handleMaximize = async () => {
    const maximized = await window.electronAPI?.maximize()
    if (typeof maximized === 'boolean') {
      setIsMaximized(maximized)
    }
  }

  const handleClose = () => {
    void window.electronAPI?.close()
  }

  return (
    <div className="h-10 drag-region flex justify-between items-center px-4 bg-void-bg/50 backdrop-blur-md border-b border-void-border z-50 relative">
      <div className="flex items-center gap-2 no-drag">
        <div className="w-2 h-2 rounded-full bg-void-cyan shadow-[0_0_8px_rgba(0,243,255,0.8)]" />
        <span className="font-rajdhani font-bold tracking-widest text-sm text-gray-300">VOID CORE</span>
      </div>

      <div className="no-drag flex items-center h-full">
        <button
          type="button"
          aria-label="Minimize"
          onMouseDown={stopTitlebarDrag}
          onClick={handleMinimize}
          className="no-drag titlebar-btn w-11 h-10 flex items-center justify-center hover:bg-white/10 text-gray-400 hover:text-white transition-colors"
        >
          <Minus size={16} />
        </button>
        <button
          type="button"
          aria-label={isMaximized ? 'Restore' : 'Maximize'}
          onMouseDown={stopTitlebarDrag}
          onClick={() => void handleMaximize()}
          className="no-drag titlebar-btn w-11 h-10 flex items-center justify-center hover:bg-white/10 text-gray-400 hover:text-white transition-colors"
        >
          {isMaximized ? <Copy size={13} /> : <Square size={14} />}
        </button>
        <button
          type="button"
          aria-label="Close"
          onMouseDown={stopTitlebarDrag}
          onClick={handleClose}
          className="no-drag titlebar-btn w-11 h-10 flex items-center justify-center hover:bg-red-500/80 text-gray-400 hover:text-white transition-colors"
        >
          <X size={18} />
        </button>
      </div>
    </div>
  )
}
