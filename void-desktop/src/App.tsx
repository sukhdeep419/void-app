import { useEffect } from 'react'
import Titlebar from './components/Titlebar'
import SystemStatus from './components/LeftPanel/SystemStatus'
import NetworkStatus from './components/RightPanel/NetworkStatus'
import AICore from './components/Center/AICore'
import CommandInput from './components/Bottom/CommandInput'
import { SystemProvider } from './hooks/useSystemStats'
import gsap from 'gsap'

function App() {
  useEffect(() => {
    // Startup animation
    const tl = gsap.timeline()
    
    tl.fromTo('.app-container', { opacity: 0 }, { opacity: 1, duration: 1, ease: 'power2.out' })
      .fromTo('.panel-left', { x: -50, opacity: 0 }, { x: 0, opacity: 1, duration: 0.8, ease: 'back.out(1.2)' }, '-=0.5')
      .fromTo('.panel-right', { x: 50, opacity: 0 }, { x: 0, opacity: 1, duration: 0.8, ease: 'back.out(1.2)' }, '-=0.8')
      .fromTo('.panel-bottom', { y: 50, opacity: 0 }, { y: 0, opacity: 1, duration: 0.8, ease: 'back.out(1.2)' }, '-=0.6')
  }, [])

  return (
    <SystemProvider>
      <div className="app-container h-screen w-screen bg-void-bg overflow-hidden flex flex-col font-sans text-white relative">
        {/* Background glow effects */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-void-cyan opacity-[0.03] rounded-full blur-[120px] pointer-events-none" />
        <div className="absolute top-0 left-0 w-full h-full bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-transparent via-black/50 to-black/90 pointer-events-none z-0" />

        {/* 3D AI Core Background */}
        <div className="fixed inset-0 z-0 pointer-events-none flex justify-center items-center">
          <AICore />
        </div>

        <Titlebar />

        <div className="flex-1 flex overflow-hidden p-6 z-10 gap-6 relative">
          <div className="panel-left w-[350px] flex flex-col gap-4">
            <SystemStatus />
          </div>

          {/* Empty center space to let the background shine through */}
          <div className="flex-1" />

          <div className="panel-right w-[350px] flex flex-col gap-4">
            <NetworkStatus />
            <div className="glass-panel flex-1 flex items-center justify-center text-gray-500 font-rajdhani text-lg">
              WEATHER DATA PLACEHOLDER
            </div>
            <div className="glass-panel flex-1 flex items-center justify-center text-gray-500 font-rajdhani text-lg">
              NOTIFICATIONS PLACEHOLDER
            </div>
          </div>
        </div>

        <div className="panel-bottom p-6 pt-0 z-10 w-full max-w-4xl mx-auto">
          <CommandInput />
        </div>
      </div>
    </SystemProvider>
  )
}

export default App
