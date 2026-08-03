import { useSystemStats } from '../../hooks/useSystemStats'
import { Wifi, ArrowDown, ArrowUp, Clock, Battery } from 'lucide-react'
import { useEffect, useState } from 'react'

export default function NetworkStatus() {
  const stats = useSystemStats()
  const [time, setTime] = useState(new Date())

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  const formatUptime = (seconds: number) => {
    const d = Math.floor(seconds / (3600*24))
    const h = Math.floor(seconds % (3600*24) / 3600)
    const m = Math.floor(seconds % 3600 / 60)
    return `${d}d ${h}h ${m}m`
  }

  return (
    <div className="glass-panel p-4 flex flex-col gap-4">
      {/* Time & Uptime */}
      <div className="flex justify-between items-start border-b border-white/10 pb-4">
        <div>
          <div className="text-3xl font-rajdhani font-bold neon-text">
            {time.toLocaleTimeString([], { hour12: false })}
          </div>
          <div className="text-sm text-gray-400 font-medium">
            {time.toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric' })}
          </div>
        </div>
        <div className="text-right">
          <div className="flex items-center gap-1 text-gray-400 text-xs justify-end">
            <Clock size={12} /> UPTIME
          </div>
          <div className="font-rajdhani text-sm font-semibold">{formatUptime(stats.system.uptime_seconds)}</div>
          
          <div className="flex items-center gap-1 text-gray-400 text-xs justify-end mt-2">
            <Battery size={12} /> {stats.system.battery_status.toUpperCase()}
          </div>
          <div className="font-rajdhani text-sm font-semibold">{stats.system.battery_percent}%</div>
        </div>
      </div>

      {/* Network */}
      <div className="flex flex-col gap-3">
        <div className="flex items-center gap-2">
          <Wifi size={18} className="text-void-cyan" />
          <span className="font-rajdhani font-semibold tracking-wider text-sm truncate max-w-[200px]">
            {stats.network.name}
          </span>
        </div>
        
        <div className="grid grid-cols-2 gap-2">
          <div className="bg-black/30 rounded-lg p-2 border border-white/5">
            <div className="flex items-center gap-1 text-xs text-gray-400 mb-1">
              <ArrowDown size={12} className="text-green-400" /> DL
            </div>
            <div className="font-rajdhani font-bold text-lg">
              {stats.network.download_speed_mbps.toFixed(1)} <span className="text-xs text-gray-500">Mbps</span>
            </div>
          </div>
          
          <div className="bg-black/30 rounded-lg p-2 border border-white/5">
            <div className="flex items-center gap-1 text-xs text-gray-400 mb-1">
              <ArrowUp size={12} className="text-purple-400" /> UL
            </div>
            <div className="font-rajdhani font-bold text-lg">
              {stats.network.upload_speed_mbps.toFixed(1)} <span className="text-xs text-gray-500">Mbps</span>
            </div>
          </div>
        </div>
        <div className="text-xs text-gray-500 font-mono text-right truncate">
          IP: {stats.network.ip}
        </div>
      </div>
    </div>
  )
}
