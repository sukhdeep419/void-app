import { useEffect, useState } from 'react'
import { Bell, Terminal, ExternalLink } from 'lucide-react'

type Notification = {
  id: number
  title: string
  url: string
  time: number
}

export default function NotificationsPanel() {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchNews() {
      try {
        // Fetch top stories from Hacker News
        const res = await fetch('https://hacker-news.firebaseio.com/v0/topstories.json')
        const storyIds = await res.json()
        
        // Take top 3
        const top3Ids = storyIds.slice(0, 3)
        const stories = await Promise.all(
          top3Ids.map(async (id: number) => {
            const storyRes = await fetch(`https://hacker-news.firebaseio.com/v0/item/${id}.json`)
            return await storyRes.json()
          })
        )
        
        setNotifications(stories)
      } catch (err) {
        console.error("Failed to fetch notifications:", err)
      } finally {
        setLoading(false)
      }
    }
    
    fetchNews()
    const interval = setInterval(fetchNews, 60 * 60 * 1000) // update every hour
    return () => clearInterval(interval)
  }, [])

  const formatTime = (unixTs: number) => {
    const d = new Date(unixTs * 1000)
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
  }

  return (
    <div className="glass-panel p-4 flex flex-col gap-3 min-h-[160px] flex-1">
      <div className="flex items-center justify-between border-b border-white/10 pb-2">
        <div className="flex items-center gap-2 text-void-cyan">
          <Bell size={16} />
          <span className="font-rajdhani font-semibold tracking-widest text-sm uppercase">Tech Intel</span>
        </div>
        <div className="text-[10px] text-gray-500 bg-black/30 px-2 py-0.5 rounded border border-white/5">
          LIVE
        </div>
      </div>
      
      {loading ? (
        <div className="flex-1 flex flex-col gap-3 justify-center">
          {[1, 2, 3].map(i => (
            <div key={i} className="animate-pulse flex gap-2 items-start">
              <div className="w-1 h-3 bg-void-cyan/30 mt-1 rounded"></div>
              <div className="flex flex-col gap-1 w-full">
                <div className="h-3 bg-white/10 rounded w-full"></div>
                <div className="h-3 bg-white/10 rounded w-2/3"></div>
              </div>
            </div>
          ))}
        </div>
      ) : notifications.length > 0 ? (
        <div className="flex flex-col gap-3 overflow-y-auto pr-1 custom-scrollbar">
          {notifications.map((notif) => (
            <div key={notif.id} className="flex gap-2 group cursor-pointer" onClick={() => window.open(notif.url, '_blank')}>
              <div className="w-1 h-full bg-void-cyan/30 mt-1 rounded group-hover:bg-void-cyan transition-colors"></div>
              <div className="flex flex-col flex-1 min-w-0">
                <div className="text-sm font-medium text-gray-200 group-hover:text-white line-clamp-2 leading-tight">
                  {notif.title}
                </div>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-[10px] text-gray-500 font-mono">{formatTime(notif.time)}</span>
                  <ExternalLink size={10} className="text-gray-600 group-hover:text-void-cyan transition-colors" />
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center text-gray-500 text-sm gap-2">
          <Terminal size={14} /> No intelligence available
        </div>
      )}
    </div>
  )
}
