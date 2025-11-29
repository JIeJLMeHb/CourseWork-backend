import time
import os
import sys
import clr
import platform

# Add LibreHardwareMonitor DLLs to the path
libre_hardware_monitor_path = os.path.join(os.path.dirname(__file__), "LibreHardwareMonitorLib")
if os.path.exists(libre_hardware_monitor_path):
    sys.path.append(libre_hardware_monitor_path)

try:
    # Try to load LibreHardwareMonitor
    clr.AddReference("LibreHardwareMonitorLib")
    from LibreHardwareMonitor.Hardware import Computer, SensorType
    print("✅ LibreHardwareMonitor loaded successfully")
except Exception as e:
    print(f"❌ LibreHardwareMonitor loading error: {e}")
    print("Please download from: https://github.com/LibreHardwareMonitor/LibreHardwareMonitor")
    print("And place LibreHardwareMonitorLib.dll in a folder named 'LibreHardwareMonitorLib'")
    sys.exit(1)

class SystemMonitor:
    def __init__(self):
        self.computer = Computer()
        
        # Enable all hardware monitoring
        self.computer.IsCpuEnabled = True
        self.computer.IsGpuEnabled = True
        self.computer.IsMemoryEnabled = True
        self.computer.IsMotherboardEnabled = True
        self.computer.IsControllerEnabled = True
        self.computer.IsNetworkEnabled = True
        self.computer.IsStorageEnabled = True
        self.computer.IsBatteryEnabled = True
        
        try:
            self.computer.Open()
            print("✅ Hardware monitoring initialized")
        except Exception as e:
            print(f"❌ Error initializing hardware monitoring: {e}")
    
    def update_all_hardware(self):
        """Update all hardware components without using visitor pattern"""
        for hardware in self.computer.Hardware:
            hardware.Update()
            # Update sub-hardware if any
            for sub_hardware in hardware.SubHardware:
                sub_hardware.Update()
    
    def get_sensor_readings(self):
        """Get all sensor readings"""
        self.update_all_hardware()
        
        sensor_data = {
            "temperature": [],
            "load": [],
            "clock": [],
            "voltage": [],
            "power": [],
            "fan": [],
            "throughput": [],
            "data": []
        }
        
        for hardware in self.computer.Hardware:
            for sensor in hardware.Sensors:
                if sensor.Value is not None:
                    # Get sensor unit
                    unit = self.get_sensor_unit(sensor.SensorType)
                    
                    sensor_info = {
                        "name": sensor.Name or "Unnamed",
                        "value": float(sensor.Value),
                        "hardware": hardware.Name or "Unknown Hardware",
                        "type": str(sensor.SensorType),
                        "unit": unit,
                        "identifier": str(sensor.Identifier)
                    }
                    
                    # Categorize sensors
                    if sensor.SensorType == SensorType.Temperature:
                        sensor_data["temperature"].append(sensor_info)
                    elif sensor.SensorType == SensorType.Load:
                        sensor_data["load"].append(sensor_info)
                    elif sensor.SensorType == SensorType.Clock:
                        sensor_data["clock"].append(sensor_info)
                    elif sensor.SensorType == SensorType.Voltage:
                        sensor_data["voltage"].append(sensor_info)
                    elif sensor.SensorType == SensorType.Power:
                        sensor_data["power"].append(sensor_info)
                    elif sensor.SensorType == SensorType.Fan:
                        sensor_data["fan"].append(sensor_info)
                    elif sensor.SensorType == SensorType.Throughput:
                        sensor_data["throughput"].append(sensor_info)
                    elif sensor.SensorType == SensorType.Data:
                        sensor_data["data"].append(sensor_info)
        
        return sensor_data
    
    def get_sensor_unit(self, sensor_type):
        """Get the appropriate unit for sensor type"""
        units = {
            SensorType.Temperature: "°C",
            SensorType.Load: "%",
            SensorType.Clock: "MHz",
            SensorType.Voltage: "V",
            SensorType.Power: "W",
            SensorType.Fan: "RPM",
            SensorType.Flow: "L/h",
            SensorType.Throughput: "MB/s",
            SensorType.Level: "%",
            SensorType.Factor: "",
            SensorType.Data: "",
            SensorType.SmallData: "",
            SensorType.Frequency: "Hz"
        }
        return units.get(sensor_type, "")
    
    def print_comprehensive_report(self):
        """Print comprehensive hardware report"""
        try:
            data = self.get_sensor_readings()
            
            print("\n" + "="*80)
            print(f"🏢 ПОЛНЫЙ ОТЧЕТ О СОСТОЯНИИ СИСТЕМЫ - {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("="*80)
            
            # Temperature section - most important
            if data["temperature"]:
                print(f"\n🌡️  ТЕМПЕРАТУРЫ ({len(data['temperature'])} датчиков):")
                print("-" * 60)
                for sensor in sorted(data["temperature"], key=lambda x: x["name"]):
                    status = "🔥" if sensor["value"] > 80 else "⚠️ " if sensor["value"] > 70 else "✅"
                    print(f"   {status} {sensor['name']:25} | {sensor['hardware']:20} | {sensor['value']:6.1f}{sensor['unit']}")
            
            # Load section
            if data["load"]:
                print(f"\n📈 НАГРУЗКА ({len(data['load'])} датчиков):")
                print("-" * 60)
                for sensor in sorted(data["load"], key=lambda x: x["name"]):
                    print(f"   📊 {sensor['name']:25} | {sensor['hardware']:20} | {sensor['value']:6.1f}{sensor['unit']}")
            
            # Clock speeds
            if data["clock"]:
                print(f"\n⚡ ЧАСТОТЫ ({len(data['clock'])} датчиков):")
                print("-" * 60)
                for sensor in sorted(data["clock"], key=lambda x: x["name"]):
                    # Convert to GHz if over 1000 MHz
                    value = sensor["value"] / 1000 if sensor["value"] > 1000 else sensor["value"]
                    unit = "GHz" if sensor["value"] > 1000 else sensor["unit"]
                    print(f"   📊 {sensor['name']:25} | {sensor['hardware']:20} | {value:6.1f}{unit}")
            
            # Power consumption
            if data["power"]:
                print(f"\n🔋 ПОТРЕБЛЕНИЕ ЭНЕРГИИ ({len(data['power'])} датчиков):")
                print("-" * 60)
                for sensor in sorted(data["power"], key=lambda x: x["name"]):
                    print(f"   📊 {sensor['name']:25} | {sensor['hardware']:20} | {sensor['value']:6.1f}{sensor['unit']}")
            
            # Fan speeds
            if data["fan"]:
                print(f"\n🌀 СКОРОСТЬ ВЕНТИЛЯТОРОВ ({len(data['fan'])} датчиков):")
                print("-" * 60)
                for sensor in sorted(data["fan"], key=lambda x: x["name"]):
                    print(f"   📊 {sensor['name']:25} | {sensor['hardware']:20} | {sensor['value']:6.0f}{sensor['unit']}")
            
            # Voltage
            if data["voltage"]:
                print(f"\n🔌 НАПРЯЖЕНИЕ ({len(data['voltage'])} датчиков):")
                print("-" * 60)
                for sensor in sorted(data["voltage"], key=lambda x: x["name"]):
                    print(f"   📊 {sensor['name']:25} | {sensor['hardware']:20} | {sensor['value']:6.3f}{sensor['unit']}")
            
            # Summary
            total_sensors = sum(len(sensors) for sensors in data.values())
            print(f"\n📊 ИТОГО: {total_sensors} датчиков обнаружено")
            
            # Critical temperatures warning
            high_temps = [s for s in data["temperature"] if s["value"] > 80]
            if high_temps:
                print(f"\n🚨 ВНИМАНИЕ: {len(high_temps)} датчиков с температурой выше 80°C!")
                for sensor in high_temps:
                    print(f"   🔥 {sensor['name']}: {sensor['value']:.1f}°C")
            
            print("="*80)
            
        except Exception as e:
            print(f"❌ Ошибка при получении данных: {e}")
    
    def get_hardware_summary(self):
        """Get basic hardware information"""
        try:
            self.update_all_hardware()
            
            hardware_types = {}
            for hardware in self.computer.Hardware:
                hw_type = str(hardware.HardwareType)
                hardware_types[hw_type] = hardware_types.get(hw_type, 0) + 1
            
            return hardware_types
        except Exception as e:
            print(f"Ошибка получения информации о железе: {e}")
            return {}
    
    def close(self):
        """Close hardware monitoring"""
        try:
            self.computer.Close()
            print("✅ Hardware monitoring closed")
        except:
            pass

def check_admin_privileges():
    """Check if script is running with admin privileges"""
    try:
        if os.name == 'nt':
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        else:
            return os.getuid() == 0
    except:
        return False

def print_system_info():
    """Print basic system information"""
    print(f"\n💻 Системная информация:")
    print(f"   ОС: {platform.system()} {platform.release()}")
    print(f"   Процессор: {platform.processor()}")
    print(f"   Архитектура: {platform.architecture()[0]}")
    print(f"   Версия Python: {platform.python_version()}")

def main():
    print("🚀 Запуск комплексного мониторинга системы...")
    print_system_info()
    
    # Check admin privileges
    if not check_admin_privileges():
        print("\n⚠️  ВНИМАНИЕ: Скрипт запущен без прав администратора!")
        print("   Некоторые датчики могут быть недоступны.")
        print("   Для получения полной информации запустите скрипт от имени администратора.")
        print("   Нажмите Enter для продолжения или Ctrl+C для выхода...")
        try:
            input()
        except KeyboardInterrupt:
            print("\nВыход...")
            return
    
    monitor = None
    try:
        monitor = SystemMonitor()
        
        # Print hardware summary
        hardware_info = monitor.get_hardware_summary()
        if hardware_info:
            print(f"\n📋 Обнаруженное оборудование:")
            for hw_type, count in hardware_info.items():
                print(f"   {hw_type}: {count} устройств")
        
        print("\n🔄 Мониторинг запущен. Для остановки нажмите Ctrl+C")
        print("📊 Данные будут обновляться каждые 5 секунд...")
        
        update_count = 0
        while True:
            monitor.print_comprehensive_report()
            update_count += 1
            print(f"\n🔄 Обновление #{update_count}. Следующее обновление через 5 секунд...")
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Мониторинг остановлен пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if monitor:
            monitor.close()

if __name__ == "__main__":
    main()