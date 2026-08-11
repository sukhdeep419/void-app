import { Mic } from 'lucide-react'
import { useState, useRef, useEffect } from 'react'
import gsap from 'gsap'

type Message = { id: string; role: 'user' | 'ai'; content: string; }

function formatMessage(content: string) {
  // Replace <br> tags with newlines
  const cleanedContent = content.replace(/<br\s*\/?>/gi, '\n')
  return cleanedContent.split(/(\*\*[^*]+?\*\*)/g).map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={index}>{part.slice(2, -2)}</strong>
    }
    return part
  })
}

export default function CommandInput() {
  const [isRecording, setIsRecording] = useState(false)
  const [inputValue, setInputValue] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [isExpanded, setIsExpanded] = useState(false)
  
  const [customHeight, setCustomHeight] = useState(384)
  const isDragging = useRef(false)
  const startY = useRef(0)
  const startHeight = useRef(0)
  
  const micRef = useRef<HTMLButtonElement>(null)
  const pulseRef = useRef<HTMLDivElement>(null)
  const chatRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    let ctx = gsap.context(() => {
      if (isRecording) {
        gsap.to(pulseRef.current, { scale: 1.5, opacity: 0, duration: 1, repeat: -1, ease: "power2.out" })
        gsap.to(micRef.current, { color: '#00f3ff', scale: 1.1, duration: 0.3, yoyo: true, repeat: -1 })
      } else {
        gsap.killTweensOf(pulseRef.current)
        gsap.killTweensOf(micRef.current)
        gsap.to(pulseRef.current, { scale: 1, opacity: 0, duration: 0.2 })
        gsap.to(micRef.current, { color: '#9ca3af', scale: 1, duration: 0.2 })
      }
    })
    return () => ctx.revert()
  }, [isRecording])

  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight
    }
  }, [messages, isExpanded])

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputValue(e.target.value)
    e.target.style.height = 'auto'
    e.target.style.height = `${Math.min(e.target.scrollHeight, 200)}px`
  }

  const handleKeyDown = async (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (inputValue.trim() !== '') {
        const command = inputValue.trim()
        setInputValue('')
        if (e.currentTarget) {
          e.currentTarget.style.height = 'auto'
        }
        
        if (command.toLowerCase() === '/dev') {
          // @ts-ignore
          if (window.electronAPI && window.electronAPI.openDevTools) {
            // @ts-ignore
            window.electronAPI.openDevTools()
          }
          return
        }
      
        const aiId = Date.now().toString()
      
      // Build the history array for the backend BEFORE we add the empty loading bubble
      const currentMessages = messages
        .filter(m => m.content !== '')
        .map(m => ({ role: m.role, content: m.content }));
      currentMessages.push({ role: 'user', content: command });

      setMessages(prev => [...prev, 
        { id: aiId + '-user', role: 'user', content: command },
        { id: aiId, role: 'ai', content: '' }
      ])
      
      const controller = new AbortController()
      let timeoutId: number | undefined
      const resetTimeout = () => {
        if (timeoutId !== undefined) window.clearTimeout(timeoutId)
        timeoutId = window.setTimeout(() => controller.abort(), 120_000)
      }

      try {
        resetTimeout()
        const res = await fetch('http://localhost:8000/api/command', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ messages: currentMessages }),
          signal: controller.signal
        })
        
        if (!res.ok) throw new Error(`The AI backend returned an error (${res.status}).`)
        
        const reader = res.body?.getReader()
        const decoder = new TextDecoder()
        let receivedContent = false
        
        if (reader) {
          let done = false
          while (!done) {
            const { value, done: doneReading } = await reader.read()
            done = doneReading
            if (value) {
              const chunk = decoder.decode(value, { stream: true })
              if (chunk) {
                receivedContent = true
                resetTimeout()
              }
              setMessages(prev => prev.map(msg => 
                msg.id === aiId ? { ...msg, content: msg.content + chunk } : msg
              ))
            }
          }
        }

        if (!receivedContent) {
          throw new Error("The assistant couldn't complete that request. Please try again.")
        }
      } catch (err) {
        console.error(err)
        const message = err instanceof DOMException && err.name === 'AbortError'
          ? "I couldn't complete that request in time. Please try a simpler request."
          : err instanceof Error
            ? err.message
            : 'Failed to connect to the AI backend.'
        setMessages(prev => prev.map(msg => 
          msg.id === aiId ? { ...msg, content: `Error: ${message}` } : msg
        ))
      } finally {
        if (timeoutId !== undefined) window.clearTimeout(timeoutId)
      }
    }
    }
  }

  // Handle clicking outside to collapse
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (chatRef.current && !chatRef.current.contains(e.target as Node) && !document.getElementById('command-input-container')?.contains(e.target as Node)) {
        setIsExpanded(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Handle resizing
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging.current) return
      const deltaY = e.clientY - startY.current
      const newHeight = Math.max(384, startHeight.current - deltaY)
      setCustomHeight(newHeight)
    }
    const handleMouseUp = () => {
      isDragging.current = false
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [])

  return (
    <div id="command-input-container" className="flex flex-col gap-2 w-full max-w-4xl mx-auto" onClick={() => setIsExpanded(true)}>
      
      {/* Scrollable Chat History */}
      {messages.length > 0 && (
        <div 
          ref={chatRef}
          className={`relative flex flex-col gap-3 overflow-y-auto scrollbar-hide transition-colors duration-300 ease-in-out rounded-3xl ${
            isExpanded 
              ? 'p-4 bg-black/30 backdrop-blur-2xl border border-white/10 shadow-[0_8px_32px_rgba(0,0,0,0.4)]' 
              : 'max-h-32 px-4 pointer-events-none bg-transparent border border-transparent'
          }`}
          style={{
            height: isExpanded ? `${customHeight}px` : undefined,
            maxHeight: isExpanded ? '85vh' : undefined,
            maskImage: !isExpanded ? 'linear-gradient(to bottom, transparent 0%, black 80%)' : 'none',
            WebkitMaskImage: !isExpanded ? 'linear-gradient(to bottom, transparent 0%, black 80%)' : 'none'
          }}
        >
          {isExpanded && (
            <div 
               className="sticky top-0 left-0 w-full flex justify-center items-center cursor-ns-resize z-20 hover:bg-white/5 py-2 -mt-2 mb-2 rounded-t-xl"
               onMouseDown={(e) => {
                 isDragging.current = true;
                 startY.current = e.clientY;
                 startHeight.current = customHeight;
                 e.preventDefault();
               }}
            >
               <div className="w-12 h-1.5 bg-white/20 rounded-full transition-colors hover:bg-white/40" />
            </div>
          )}
          {messages.map(msg => (
            <div key={msg.id} className={`max-w-[85%] select-text whitespace-pre-wrap break-words rounded-xl px-4 py-2 text-sm font-rajdhani tracking-wide ${
              msg.role === 'user' 
                ? 'self-end bg-void-cyan/10 border border-void-cyan/30 text-void-cyan shadow-[0_0_10px_rgba(0,243,255,0.1)]' 
                : 'self-start bg-void-panel/80 backdrop-blur-md border border-white/10 text-gray-200 shadow-lg'
            }`}>
              {msg.content ? formatMessage(msg.content) : <span className="animate-pulse">...</span>}
            </div>
          ))}
        </div>
      )}

      {/* Input Panel */}
      <div className="glass-panel w-full flex items-center p-2 rounded-2xl relative overflow-hidden group hover:border-void-cyan/50 transition-colors z-10">
        <div className="absolute inset-0 bg-gradient-to-r from-void-cyan/5 via-transparent to-void-cyan/5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
        
        <div className="relative flex items-center justify-center w-14 h-14 shrink-0">
          <div ref={pulseRef} className="absolute inset-2 bg-void-cyan rounded-full opacity-0" />
          <button 
            ref={micRef}
            onClick={(e) => { e.stopPropagation(); setIsRecording(!isRecording); }}
            className="relative z-10 w-12 h-12 flex items-center justify-center rounded-full bg-black/50 border border-white/10 hover:bg-black/80 transition-colors"
          >
            <Mic size={24} />
          </button>
        </div>
        
        <textarea 
          rows={1}
          value={inputValue}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          onFocus={() => setIsExpanded(true)}
          className="flex-1 bg-transparent border-none outline-none text-white font-rajdhani text-[16px] tracking-wide px-4 placeholder:text-gray-600 resize-none py-3 max-h-[200px] overflow-y-auto"
          style={{ minHeight: '52px' }}
          placeholder="What would you like me to do?"
        />
        
        <button 
          onClick={(e) => { e.stopPropagation(); setMessages([]); setInputValue(''); }}
          className="mx-4 px-3 py-1.5 rounded-lg border border-white/10 bg-black/30 text-xs font-mono text-gray-400 uppercase tracking-widest hidden md:block hover:bg-white/10 hover:text-void-cyan hover:border-void-cyan/50 transition-all cursor-pointer"
        >
          New Chat
        </button>
      </div>
    </div>
  )
}
