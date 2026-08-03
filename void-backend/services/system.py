import psutil
# pyrefly: ignore [missing-import]
import GPUtil
import time
import socket
import threading
from typing import Dict, Any

def get_network_info() -> Dict[str, Any]:
    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        return {
            "name": hostname,
            "ip": ip_address,
        }
    except Exception:
        return {"name": "Unknown", "ip": "Unknown"}

# Global cache for system metrics
_cached_metrics = None
_metrics_lock = threading.Lock()

def _update_metrics_loop():
    global _cached_metrics
    
    # Initialize psutil CPU percent (discard first 0.0 reading)
    psutil.cpu_percent(interval=None)
    
    _last_net_io = psutil.net_io_counters()
    _last_time = time.time()
    
    while True:
        # Sleep for 1 second to create a stable interval for CPU and Network calculations
        time.sleep(1)
        
        try:
            # CPU
            cpu_usage = psutil.cpu_percent(interval=None)
            
            cpu_freq = psutil.cpu_freq()
            freq_current = round(cpu_freq.current / 1000, 2) if cpu_freq else 0

            # CPU Temp is often not available on Windows via psutil, fallback to 0
            cpu_temp = 0
            if hasattr(psutil, "sensors_temperatures"):
                temps = psutil.sensors_temperatures()
                if temps and "coretemp" in temps:
                    cpu_temp = temps["coretemp"][0].current

            # RAM
            ram = psutil.virtual_memory()
            total_ram = round(ram.total / (1024**3), 2)
            used_ram = round(ram.used / (1024**3), 2)
            available_ram = round(ram.available / (1024**3), 2)

            # Disk
            disk = psutil.disk_usage('/')
            disk_total = round(disk.total / (1024**3), 2)
            disk_used = round(disk.used / (1024**3), 2)
            disk_percent = disk.percent

            # Network Speed
            current_net_io = psutil.net_io_counters()
            current_time = time.time()
            time_delta = current_time - _last_time
            
            download_speed = 0
            upload_speed = 0
            if time_delta > 0:
                download_speed = (current_net_io.bytes_recv - _last_net_io.bytes_recv) / time_delta
                upload_speed = (current_net_io.bytes_sent - _last_net_io.bytes_sent) / time_delta
                
            _last_net_io = current_net_io
            _last_time = current_time
            
            # Convert speed to Mbps
            download_speed_mbps = round((download_speed * 8) / 1_000_000, 2)
            upload_speed_mbps = round((upload_speed * 8) / 1_000_000, 2)
            
            net_info = get_network_info()

            # System Uptime
            uptime = int(time.time() - psutil.boot_time())

            # Battery
            battery_status = "N/A"
            battery_percent = 100
            if hasattr(psutil, "sensors_battery"):
                battery = psutil.sensors_battery()
                if battery:
                    battery_percent = battery.percent
                    battery_status = "Plugged In" if battery.power_plugged else "Discharging"

            # GPU
            gpus = GPUtil.getGPUs()
            gpu_usage = 0
            gpu_temp = 0
            gpu_vram_total = 0
            gpu_vram_used = 0
            if gpus:
                gpu = gpus[0]
                gpu_usage = round(gpu.load * 100, 1)
                gpu_temp = gpu.temperature
                gpu_vram_total = gpu.memoryTotal
                gpu_vram_used = gpu.memoryUsed

            metrics = {
                "cpu": {
                    "usage": cpu_usage,
                    "temp": cpu_temp
                },
                "gpu": {
                    "usage": gpu_usage,
                    "temp": gpu_temp,
                    "vram_used": gpu_vram_used,
                    "vram_total": gpu_vram_total
                },
                "ram": {
                    "total": total_ram,
                    "used": used_ram,
                    "available": available_ram,
                    "percent": ram.percent
                },
                "disk": {
                    "total": disk_total,
                    "used": disk_used,
                    "percent": disk_percent
                },
                "network": {
                    "name": net_info["name"],
                    "ip": net_info["ip"],
                    "download_speed_mbps": download_speed_mbps,
                    "upload_speed_mbps": upload_speed_mbps
                },
                "system": {
                    "uptime_seconds": uptime,
                    "battery_percent": battery_percent,
                    "battery_status": battery_status
                }
            }
            
            with _metrics_lock:
                _cached_metrics = metrics
                
        except Exception as e:
            print(f"Error in _update_metrics_loop: {e}")

# Start the background monitoring thread
_monitor_thread = threading.Thread(target=_update_metrics_loop, daemon=True)
_monitor_thread.start()

def get_system_metrics() -> Dict[str, Any]:
    with _metrics_lock:
        if _cached_metrics is not None:
            return _cached_metrics
            
    # Fallback if called before the first thread update completes
    net_info = get_network_info()
    return {
        "cpu": {"usage": 0, "temp": 0},
        "gpu": {"usage": 0, "temp": 0, "vram_used": 0, "vram_total": 0},
        "ram": {"total": 0, "used": 0, "available": 0, "percent": 0},
        "disk": {"total": 0, "used": 0, "percent": 0},
        "network": {"name": net_info["name"], "ip": net_info["ip"], "download_speed_mbps": 0, "upload_speed_mbps": 0},
        "system": {"uptime_seconds": 0, "battery_percent": 100, "battery_status": "N/A"}
    }

