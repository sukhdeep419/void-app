import { Minus, Square, X } from 'lucide-react'

export default function Titlebar() {
  const handleMinimize = () => {
    // @ts-ignore
    window.electronAPI?.minimize()
  }

  const handleMaximize = () => {
    // @ts-ignore
    window.electronAPI?.maximize()
  }

  const handleClose = () => {
    // @ts-ignore
    window.electronAPI?.close()
  }

  return (
    <div className="h-10 drag-region flex justify-between items-center px-4 bg-void-bg/50 backdrop-blur-md border-b border-void-border z-50">
      <div className="flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-void-cyan shadow-[0_0_8px_rgba(0,243,255,0.8)]" />
        <span className="font-rajdhani font-bold tracking-widest text-sm text-gray-300">VOID CORE</span>
      </div>
      
      <div className="no-drag flex items-center gap-2 h-full">
        <button onClick={handleMinimize} className="p-2 hover:bg-white/10 text-gray-400 hover:text-white transition-colors h-full">
          <Minus size={16} />
        </button>
        <button onClick={handleMaximize} className="p-2 hover:bg-white/10 text-gray-400 hover:text-white transition-colors h-full">
          <Square size={14} />
        </button>
        <button onClick={handleClose} className="p-2 hover:bg-red-500/80 text-gray-400 hover:text-white transition-colors h-full">
          <X size={18} />
        </button>
      </div>
    </div>
  )
}
