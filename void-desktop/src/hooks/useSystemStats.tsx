import React, { createContext, useContext, useEffect, useState } from 'react'
import { getSystemWebSocketUrl } from '../config'

export interface SystemStats {
  cpu: { usage: number; temp: number };
  gpu: { usage: number; temp: number; vram_used: number; vram_total: number };
  ram: { total: number; used: number; available: number; percent: number };
  disk: { total: number; used: number; percent: number };
  network: { name: string; ip: string; download_speed_mbps: number; upload_speed_mbps: number };
  system: { uptime_seconds: number; battery_percent: number; battery_status: string };
}

const defaultStats: SystemStats = {
  cpu: { usage: 0, temp: 0 },
  gpu: { usage: 0, temp: 0, vram_used: 0, vram_total: 0 },
  ram: { total: 0, used: 0, available: 0, percent: 0 },
  disk: { total: 0, used: 0, percent: 0 },
  network: { name: '...', ip: '...', download_speed_mbps: 0, upload_speed_mbps: 0 },
  system: { uptime_seconds: 0, battery_percent: 100, battery_status: 'N/A' },
}

const SystemContext = createContext<SystemStats>(defaultStats)

export const SystemProvider: React.FC<{children: React.ReactNode}> = ({ children }) => {
  const [stats, setStats] = useState<SystemStats>(defaultStats)

  useEffect(() => {
    let ws: WebSocket
    let reconnectTimeout: ReturnType<typeof setTimeout>
    
    const connect = () => {
      ws = new WebSocket(getSystemWebSocketUrl())
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          setStats(data)
        } catch (e) {
          console.error("Failed to parse system stats", e)
        }
      }
      
      ws.onclose = () => {
        console.log("WebSocket disconnected. Reconnecting in 3s...")
        reconnectTimeout = setTimeout(connect, 3000)
      }
      
      ws.onerror = (err) => {
        console.error("WebSocket error:", err)
        ws.close()
      }
    }
    
    connect()
    
    return () => {
      clearTimeout(reconnectTimeout)
      if (ws) ws.close()
    }
  }, [])

  return (
    <SystemContext.Provider value={stats}>
      {children}
    </SystemContext.Provider>
  )
}

export const useSystemStats = () => useContext(SystemContext)
