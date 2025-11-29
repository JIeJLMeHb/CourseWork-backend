import platform
import psutil
import subprocess
import socket
import datetime
import os
import sys
from typing import Dict, List, Optional

def run_command(cmd: str) -> str:
    """Выполняет команду и возвращает результат"""
    try:
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, text=True, encoding='cp866')
        return result.strip()
    except:
        return "Не доступно"

def get_os_info() -> Dict[str, str]:
    """Информация об операционной системе"""
    print("🔍 Получение информации об ОС...")
    info = {}
    try:
        info['Система'] = platform.system()
        info['Версия ОС'] = platform.release()
        info['Версия сборки'] = platform.version()
        info['Платформа'] = platform.platform()
        info['Архитектура'] = platform.architecture()[0]
        info['Имя компьютера'] = platform.node()
        info['Процессор'] = platform.processor()
        
        # Дополнительная информация через WMIC
        if platform.system() == "Windows":
            info['Производитель ОС'] = run_command('wmic os get caption /value').split('=')[-1]
            info['Дата установки'] = run_command('wmic os get installdate /value').split('=')[-1][:8]
            info['Время работы'] = run_command('wmic os get lastbootuptime /value').split('=')[-1]
    except Exception as e:
        info['Ошибка'] = str(e)
    
    return info

def get_cpu_info() -> Dict[str, str]:
    """Информация о процессоре"""
    print("🔍 Получение информации о процессоре...")
    info = {}
    try:
        if platform.system() == "Windows":
            # Основная информация
            cpu_name = run_command('wmic cpu get name /value').split('=')[-1]
            cpu_cores = run_command('wmic cpu get numberofcores /value').split('=')[-1]
            cpu_logical = run_command('wmic cpu get numberoflogicalprocessors /value').split('=')[-1]
            cpu_max_speed = run_command('wmic cpu get maxclockspeed /value').split('=')[-1]
            cpu_manufacturer = run_command('wmic cpu get manufacturer /value').split('=')[-1]
            cpu_architecture = run_command('wmic cpu get architecture /value').split('=')[-1]
            
            # Преобразование архитектуры
            arch_map = {'0': 'x86', '1': 'MIPS', '2': 'Alpha', '3': 'PowerPC', '5': 'ARM', '6': 'ia64', '9': 'x64'}
            cpu_architecture = arch_map.get(cpu_architecture, cpu_architecture)
            
            info['Модель'] = cpu_name
            info['Производитель'] = cpu_manufacturer
            info['Архитектура'] = cpu_architecture
            info['Количество ядер'] = cpu_cores
            info['Логические процессоры'] = cpu_logical
            info['Макс. частота'] = f"{cpu_max_speed} МГц"
            
            # Дополнительная информация
            info['L2 кэш'] = run_command('wmic cpu get l2cachesize /value').split('=')[-1] + " KB"
            info['L3 кэш'] = run_command('wmic cpu get l3cachesize /value').split('=')[-1] + " KB"
            info['Сокет'] = run_command('wmic cpu get socketdesignation /value').split('=')[-1]
            
        # Информация через psutil
        info['Текущая частота'] = f"{psutil.cpu_freq().current if psutil.cpu_freq() else 'N/A'} МГц"
        info['Загрузка CPU'] = f"{psutil.cpu_percent(interval=1)}%"
        
    except Exception as e:
        info['Ошибка'] = str(e)
    
    return info

def get_memory_info() -> Dict[str, str]:
    """Информация об оперативной памяти"""
    print("🔍 Получение информации об оперативной памяти...")
    info = {}
    try:
        virtual_mem = psutil.virtual_memory()
        swap_mem = psutil.swap_memory()
        
        info['Всего ОЗУ'] = f"{virtual_mem.total / (1024**3):.2f} ГБ"
        info['Доступно ОЗУ'] = f"{virtual_mem.available / (1024**3):.2f} ГБ"
        info['Используется ОЗУ'] = f"{virtual_mem.percent}%"
        info['Всего своп'] = f"{swap_mem.total / (1024**3):.2f} ГБ"
        info['Используется своп'] = f"{swap_mem.percent}%"
        
        # Детальная информация о модулях памяти (Windows)
        if platform.system() == "Windows":
            memory_modules = run_command('wmic memorychip get capacity,speed,manufacturer,partnumber /format:list')
            modules = memory_modules.split('\n\n')
            
            for i, module in enumerate(modules[:4]):  # Ограничим 4 модулями
                if module.strip():
                    lines = module.strip().split('\n')
                    module_info = {}
                    for line in lines:
                        if '=' in line:
                            key, value = line.split('=', 1)
                            module_info[key.strip()] = value.strip()
                    
                    capacity = int(module_info.get('Capacity', 0)) / (1024**3)
                    speed = module_info.get('Speed', 'N/A')
                    manufacturer = module_info.get('Manufacturer', 'Неизвестно')
                    
                    info[f'Модуль {i+1}'] = f"{capacity:.1f} ГБ, {speed} МГц, {manufacturer}"
        
    except Exception as e:
        info['Ошибка'] = str(e)
    
    return info

def get_disk_info() -> Dict[str, str]:
    """Информация о дисках"""
    print("🔍 Получение информации о дисках...")
    info = {}
    try:
        # Информация о разделах
        partitions = psutil.disk_partitions()
        for i, partition in enumerate(partitions):
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                info[f'Диск {i}'] = f"{partition.device} -> {partition.mountpoint}"
                info[f'  Файловая система'] = f"{partition.fstype}"
                info[f'  Общий размер'] = f"{usage.total / (1024**3):.2f} ГБ"
                info[f'  Использовано'] = f"{usage.percent}%"
                info[f'  Свободно'] = f"{usage.free / (1024**3):.2f} ГБ"
            except PermissionError:
                continue
        
        # Информация о физических дисках (Windows)
        if platform.system() == "Windows":
            physical_disks = run_command('wmic diskdrive get model,size,interfaceType,mediaType /format:list')
            disks = physical_disks.split('\n\n')
            
            for i, disk in enumerate(disks):
                if disk.strip():
                    lines = disk.strip().split('\n')
                    disk_info = {}
                    for line in lines:
                        if '=' in line:
                            key, value = line.split('=', 1)
                            disk_info[key.strip()] = value.strip()
                    
                    model = disk_info.get('Model', 'Неизвестно')
                    size = int(disk_info.get('Size', 0)) / (1024**3)
                    interface = disk_info.get('InterfaceType', 'N/A')
                    media_type = disk_info.get('MediaType', 'N/A')
                    
                    info[f'Физический диск {i}'] = f"{model}"
                    info[f'  Размер'] = f"{size:.2f} ГБ"
                    info[f'  Интерфейс'] = f"{interface}"
                    info[f'  Тип носителя'] = f"{media_type}"
        
    except Exception as e:
        info['Ошибка'] = str(e)
    
    return info

def get_gpu_info() -> Dict[str, str]:
    """Информация о графических процессорах"""
    print("🔍 Получение информации о GPU...")
    info = {}
    try:
        if platform.system() == "Windows":
            gpu_info = run_command('wmic path win32_videocontroller get name,adapterram,driverversion,currentrefreshrate /format:list')
            gpus = gpu_info.split('\n\n')
            
            for i, gpu in enumerate(gpus):
                if gpu.strip():
                    lines = gpu.strip().split('\n')
                    gpu_data = {}
                    for line in lines:
                        if '=' in line:
                            key, value = line.split('=', 1)
                            gpu_data[key.strip()] = value.strip()
                    
                    name = gpu_data.get('Name', 'Неизвестно')
                    memory = int(gpu_data.get('AdapterRAM', 0)) / (1024**3) if gpu_data.get('AdapterRAM', '0').isdigit() else 'N/A'
                    driver = gpu_data.get('DriverVersion', 'N/A')
                    refresh_rate = gpu_data.get('CurrentRefreshRate', 'N/A')
                    
                    info[f'GPU {i}'] = f"{name}"
                    info[f'  Видеопамять'] = f"{memory if isinstance(memory, str) else f'{memory:.1f}'} ГБ" 
                    info[f'  Драйвер'] = f"{driver}"
                    info[f'  Частота обновления'] = f"{refresh_rate} Гц"
        
    except Exception as e:
        info['Ошибка'] = str(e)
    
    return info

def get_network_info() -> Dict[str, str]:
    """Информация о сети"""
    print("🔍 Получение информации о сети...")
    info = {}
    try:
        # Основная информация
        hostname = socket.gethostname()
        info['Имя компьютера'] = hostname
        
        # IP адреса
        try:
            local_ip = socket.gethostbyname(hostname)
            info['Локальный IP'] = local_ip
        except:
            info['Локальный IP'] = "Не доступен"
        
        # Сетевые интерфейсы
        interfaces = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        
        for interface_name, interface_addresses in interfaces.items():
            if interface_name in stats and stats[interface_name].isup:
                info[f'Интерфейс {interface_name}'] = "Активен"
                for addr in interface_addresses:
                    if addr.family == socket.AF_INET:
                        info[f'  IPv4 адрес'] = f"{addr.address}"
                        info[f'  Маска подсети'] = f"{addr.netmask}"
                    elif addr.family == socket.AF_INET6:
                        info[f'  IPv6 адрес'] = f"{addr.address}"
                    elif addr.family == psutil.AF_LINK:
                        info[f'  MAC адрес'] = f"{addr.address}"
        
        # Информация о сетевых адаптерах (Windows)
        if platform.system() == "Windows":
            adapters = run_command('wmic nic get name,manufacturer,netenabled,macaddress /format:list')
            adapter_list = adapters.split('\n\n')
            
            for i, adapter in enumerate(adapter_list[:5]):  # Ограничим 5 адаптерами
                if adapter.strip():
                    lines = adapter.strip().split('\n')
                    adapter_info = {}
                    for line in lines:
                        if '=' in line:
                            key, value = line.split('=', 1)
                            adapter_info[key.strip()] = value.strip()
                    
                    name = adapter_info.get('Name', 'Неизвестно')
                    manufacturer = adapter_info.get('Manufacturer', 'N/A')
                    enabled = "Да" if adapter_info.get('NetEnabled') == 'TRUE' else "Нет"
                    mac = adapter_info.get('MACAddress', 'N/A')
                    
                    info[f'Сетевой адаптер {i}'] = f"{manufacturer} - {name}"
                    info[f'  Включен'] = f"{enabled}"
                    info[f'  MAC'] = f"{mac}"
        
    except Exception as e:
        info['Ошибка'] = str(e)
    
    return info

def get_motherboard_info() -> Dict[str, str]:
    """Информация о материнской плате"""
    print("🔍 Получение информации о материнской плате...")
    info = {}
    try:
        if platform.system() == "Windows":
            # Основная информация о материнской плате
            mb_manufacturer = run_command('wmic baseboard get manufacturer /value').split('=')[-1]
            mb_product = run_command('wmic baseboard get product /value').split('=')[-1]
            mb_version = run_command('wmic baseboard get version /value').split('=')[-1]
            mb_serial = run_command('wmic baseboard get serialnumber /value').split('=')[-1]
            
            info['Производитель'] = mb_manufacturer
            info['Модель'] = mb_product
            info['Версия'] = mb_version
            info['Серийный номер'] = mb_serial
            
            # BIOS
            bios_manufacturer = run_command('wmic bios get manufacturer /value').split('=')[-1]
            bios_version = run_command('wmic bios get version /value').split('=')[-1]
            bios_date = run_command('wmic bios get releasedate /value').split('=')[-1]
            
            info['BIOS Производитель'] = bios_manufacturer
            info['BIOS Версия'] = bios_version
            info['BIOS Дата'] = bios_date if len(bios_date) == 8 else bios_date
            
    except Exception as e:
        info['Ошибка'] = str(e)
    
    return info

def get_monitor_info() -> Dict[str, str]:
    """Информация о мониторах"""
    print("🔍 Получение информации о мониторах...")
    info = {}
    try:
        if platform.system() == "Windows":
            monitors = run_command('wmic desktopmonitor get name,screenwidth,screenheight /format:list')
            monitor_list = monitors.split('\n\n')
            
            for i, monitor in enumerate(monitor_list):
                if monitor.strip():
                    lines = monitor.strip().split('\n')
                    monitor_info = {}
                    for line in lines:
                        if '=' in line:
                            key, value = line.split('=', 1)
                            monitor_info[key.strip()] = value.strip()
                    
                    name = monitor_info.get('Name', 'Неизвестно')
                    width = monitor_info.get('ScreenWidth', 'N/A')
                    height = monitor_info.get('ScreenHeight', 'N/A')
                    
                    info[f'Монитор {i+1}'] = f"{name}"
                    info[f'  Разрешение'] = f"{width}x{height}"
        
    except Exception as e:
        info['Ошибка'] = str(e)
    
    return info

def get_battery_info() -> Dict[str, str]:
    """Информация о батарее"""
    print("🔍 Получение информации о батарее...")
    info = {}
    try:
        if hasattr(psutil, "sensors_battery"):
            battery = psutil.sensors_battery()
            if battery:
                info['Заряд'] = f"{battery.percent}%"
                info['Подключено к сети'] = "Да" if battery.power_plugged else "Нет"
                if battery.secsleft != psutil.POWER_TIME_UNLIMITED and battery.secsleft != psutil.POWER_TIME_UNKNOWN:
                    hours = battery.secsleft // 3600
                    minutes = (battery.secsleft % 3600) // 60
                    info['Осталось времени'] = f"{hours}ч {minutes}м"
            else:
                info['Батарея'] = "Не обнаружена (возможно, стационарный ПК)"
        else:
            info['Батарея'] = "Информация недоступна"
    except Exception as e:
        info['Ошибка'] = str(e)
    
    return info

def get_running_processes() -> Dict[str, str]:
    """Информация о запущенных процессах"""
    print("🔍 Получение информации о процессах...")
    info = {}
    try:
        processes = []
        for proc in psutil.processes(['pid', 'name', 'memory_percent', 'cpu_percent'])[:10]:  # Топ 10 процессов
            try:
                processes.append(f"{proc.info['pid']}: {proc.info['name']} (CPU: {proc.info['cpu_percent']}%, MEM: {proc.info['memory_percent']:.1f}%)")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        for i, proc in enumerate(processes):
            info[f'Процесс {i+1}'] = proc
            
    except Exception as e:
        info['Ошибка'] = str(e)
    
    return info

def print_section(title: str, data: Dict[str, str]):
    """Выводит секцию информации в консоль"""
    print(f"\n{'='*60}")
    print(f"📊 {title.upper()}")
    print(f"{'='*60}")
    
    for key, value in data.items():
        if value and value != "Не доступно":
            print(f"{key:<30} : {value}")

def main():
    """Основная функция"""
    print("🖥️  СБОР ПОЛНОЙ ИНФОРМАЦИИ О СИСТЕМЕ")
    print("⏳ Пожалуйста, подождите... Это может занять несколько секунд.\n")
    
    # Сбор всей информации
    all_info = {
        "Операционная система": get_os_info(),
        "Процессор (CPU)": get_cpu_info(),
        "Оперативная память (RAM)": get_memory_info(),
        "Накопители (Диски)": get_disk_info(),
        "Графические процессоры (GPU)": get_gpu_info(),
        "Сеть": get_network_info(),
        "Материнская плата": get_motherboard_info(),
        "Мониторы": get_monitor_info(),
        "Батарея": get_battery_info(),
        "Активные процессы (Топ-10)": get_running_processes()
    }
    
    # Вывод всей информации
    for section, data in all_info.items():
        print_section(section, data)
    
    # Итоговая информация
    print(f"\n{'='*60}")
    print("✅ СБОР ИНФОРМАЦИИ ЗАВЕРШЕН!")
    print(f"{'='*60}")
    print(f"📅 Дата и время сбора: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"💻 Общее кол-во секций: {len(all_info)}")
    
    total_items = sum(len(data) for data in all_info.values())
    print(f"📋 Всего параметров собрано: {total_items}")

if __name__ == "__main__":
    # Проверка прав администратора (для некоторых команд)
    if platform.system() == "Windows" and os.name == 'nt':
        try:
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if not is_admin:
                print("⚠️  Для получения полной информации рекомендуется запустить скрипт от имени администратора!")
        except:
            pass
    
    main()
    
    # Ожидание пользовательского ввода перед закрытием
    input("\nНажмите Enter для выхода...")