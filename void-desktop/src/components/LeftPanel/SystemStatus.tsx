import { useSystemStats } from '../../hooks/useSystemStats'
import { Cpu, HardDrive, MemoryStick, Activity } from 'lucide-react'

export default function SystemStatus() {
  const stats = useSystemStats()

  return (
    <>
      <StatusCard 
        icon={<Cpu size={20} className="text-void-cyan" />}
        title="CPU CORE"
        value={`${stats.cpu.usage.toFixed(1)}%`}
        subValue={stats.cpu.temp > 0 ? `${stats.cpu.temp}°C` : 'Temp N/A'}
        progress={stats.cpu.usage}
      />
      <StatusCard 
        icon={<Activity size={20} className="text-purple-400" />}
        title="GPU CORE"
        value={`${stats.gpu.usage.toFixed(1)}%`}
        subValue={stats.gpu.temp > 0 ? `${stats.gpu.temp}°C` : 'Temp N/A'}
        progress={stats.gpu.usage}
      />
      <StatusCard 
        icon={<MemoryStick size={20} className="text-void-blue" />}
        title="MEMORY"
        value={`${stats.ram.used.toFixed(1)}GB`}
        subValue={`/ ${stats.ram.total.toFixed(1)}GB`}
        progress={stats.ram.percent}
      />
      <StatusCard 
        icon={<HardDrive size={20} className="text-green-400" />}
        title="STORAGE"
        value={`${stats.disk.used.toFixed(1)}GB`}
        subValue={`/ ${stats.disk.total.toFixed(1)}GB`}
        progress={stats.disk.percent}
      />
    </>
  )
}

function StatusCard({ icon, title, value, subValue, progress }: { icon: React.ReactNode, title: string, value: string, subValue: string, progress: number }) {
  return (
    <div className="glass-panel p-4 flex flex-col gap-3 group hover:border-void-cyan transition-colors duration-300">
      <div className="flex items-center gap-2">
        {icon}
        <span className="font-rajdhani font-semibold tracking-wider text-sm">{title}</span>
      </div>
      
      <div className="flex items-end justify-between">
        <div className="flex items-baseline gap-1">
          <span className="text-2xl font-bold font-rajdhani">{value}</span>
          <span className="text-xs text-gray-400 font-medium">{subValue}</span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="h-1.5 w-full bg-black/40 rounded-full overflow-hidden">
        <div 
          className="h-full bg-void-cyan shadow-[0_0_10px_#00f3ff] transition-all duration-500 ease-out"
          style={{ width: `${Math.max(0, Math.min(100, progress))}%` }}
        />
      </div>
    </div>
  )
}
