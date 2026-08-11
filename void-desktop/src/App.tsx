import { useEffect } from 'react'
import Titlebar from './components/Titlebar'
import SystemStatus from './components/LeftPanel/SystemStatus'
import NetworkStatus from './components/RightPanel/NetworkStatus'
import WeatherPanel from './components/RightPanel/WeatherData'
import NotificationsPanel from './components/RightPanel/NotificationsData'
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

    const handleGlobalKey = (e: KeyboardEvent) => {
      if (e.key === 'F12') {
        // @ts-ignore
        if (window.electronAPI && window.electronAPI.openDevTools) {
          // @ts-ignore
          window.electronAPI.openDevTools()
        }
      }
    }
    window.addEventListener('keydown', handleGlobalKey)
    return () => window.removeEventListener('keydown', handleGlobalKey)
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
          <div className="flex-1 flex flex-col justify-end relative z-20">
            <CommandInput />
          </div>

          <div className="panel-right w-[350px] flex flex-col gap-4">
            <NetworkStatus />
            <WeatherPanel />
            <NotificationsPanel />
          </div>
        </div>

      </div>
    </SystemProvider>
  )
}

export default App
