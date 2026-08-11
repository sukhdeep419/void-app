import { useEffect, useState } from 'react'
import { Cloud, Sun, CloudRain, Wind, MapPin } from 'lucide-react'

type WeatherData = {
  temperature: number
  windSpeed: number
  isDay: number
  weatherCode: number
  city: string
}

export default function WeatherPanel() {
  const [data, setData] = useState<WeatherData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchWeather() {
      try {
        // 1. Get location via browser
        let lat: number, lon: number, city = 'Unknown Location'
        
        try {
          const pos = await new Promise<GeolocationPosition>((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 10000 })
          })
          lat = pos.coords.latitude
          lon = pos.coords.longitude
          
          // Reverse geocode to get city name
          const geoRes = await fetch(`https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${lat}&longitude=${lon}&localityLanguage=en`)
          const geoData = await geoRes.json()
          city = geoData.city || geoData.locality || 'Local Area'
        } catch (err) {
          console.warn("Geolocation failed, falling back to IP:", err)
          const locRes = await fetch('https://ipapi.co/json/')
          const locData = await locRes.json()
          lat = locData.latitude
          lon = locData.longitude
          city = locData.city || 'Unknown Location'
        }

        // 2. Get weather
        const weatherRes = await fetch(
          `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,is_day,weather_code,wind_speed_10m`
        )
        const weatherJson = await weatherRes.json()
        
        setData({
          temperature: weatherJson.current.temperature_2m,
          windSpeed: weatherJson.current.wind_speed_10m,
          isDay: weatherJson.current.is_day,
          weatherCode: weatherJson.current.weather_code,
          city
        })
      } catch (err) {
        console.error("Failed to fetch weather:", err)
      } finally {
        setLoading(false)
      }
    }
    
    fetchWeather()
    // Refresh every 30 mins
    const interval = setInterval(fetchWeather, 30 * 60 * 1000)
    return () => clearInterval(interval)
  }, [])

  // Basic WMO weather code to icon mapping
  const getWeatherIcon = () => {
    if (!data) return <Sun size={24} className="text-yellow-400" />
    if (data.weatherCode === 0) return data.isDay ? <Sun size={24} className="text-yellow-400" /> : <Sun size={24} className="text-gray-300" />
    if (data.weatherCode < 40) return <Cloud size={24} className="text-gray-300" />
    return <CloudRain size={24} className="text-blue-400" />
  }

  return (
    <div className="glass-panel p-4 flex flex-col gap-3 min-h-[120px]">
      <div className="flex items-center gap-2 text-void-cyan border-b border-white/10 pb-2">
        <Cloud size={16} />
        <span className="font-rajdhani font-semibold tracking-widest text-sm uppercase">Weather Data</span>
      </div>
      
      {loading ? (
        <div className="flex-1 flex items-center justify-center">
          <span className="animate-pulse text-gray-500 text-sm">Synchronizing...</span>
        </div>
      ) : data ? (
        <div className="flex items-center justify-between mt-1">
          <div className="flex flex-col">
            <div className="flex items-center gap-3">
              {getWeatherIcon()}
              <div className="text-3xl font-rajdhani font-bold neon-text">{data.temperature}°C</div>
            </div>
            <div className="flex items-center gap-1 text-gray-400 text-xs mt-2 truncate max-w-[150px]">
              <MapPin size={12} /> {data.city}
            </div>
          </div>
          <div className="bg-black/30 rounded-lg p-2 border border-white/5 flex flex-col items-center min-w-[60px]">
            <div className="flex items-center gap-1 text-[10px] text-gray-400 mb-1">
              <Wind size={10} className="text-void-cyan" /> WIND
            </div>
            <div className="font-rajdhani font-bold text-sm">
              {data.windSpeed} <span className="text-[10px] text-gray-500">km/h</span>
            </div>
          </div>
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center">
          <span className="text-gray-500 text-sm">Unavailable</span>
        </div>
      )}
    </div>
  )
}
