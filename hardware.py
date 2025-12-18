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
        
        # Основная информация об ОЗУ
        info['Всего ОЗУ'] = f"{virtual_mem.total / (1024**3):.2f} ГБ"
        info['Используется ОЗУ'] = f"{virtual_mem.used / (1024**3):.2f} ГБ"
        info['Доступно ОЗУ'] = f"{virtual_mem.available / (1024**3):.2f} ГБ"
        info['Использование ОЗУ'] = f"{virtual_mem.percent:.1f}%"
        info['Всего файла подкачки'] = f"{swap_mem.total / (1024**3):.2f} ГБ"
        info['Используется файла подкачки'] = f"{swap_mem.used / (1024**3):.2f} ГБ"
        info['Использование файла подкачки'] = f"{swap_mem.percent:.1f}%"
        
        # Детальная информация о модулях памяти (Windows)
        if platform.system() == "Windows":
            try:
                # Используем CSV формат для более стабильного парсинга
                mem_output = run_command('wmic memorychip get BankLabel, Capacity, Speed, Manufacturer, PartNumber, SerialNumber, DeviceLocator /format:csv')
                
                lines = [line.strip() for line in mem_output.strip().split('\n') if line.strip()]
                
                if len(lines) > 1:
                    headers = lines[0].split(',')
                    module_count = 0
                    
                    for line in lines[1:]:
                        values = line.split(',')
                        # Дополняем значения до нужной длины
                        while len(values) < len(headers):
                            values.append('')
                        
                        mem_data = dict(zip(headers, values))
                        
                        # Извлекаем данные
                        capacity_raw = mem_data.get('Capacity', '0').strip('"').strip()
                        try:
                            capacity = int(capacity_raw) if capacity_raw.isdigit() else 0
                            capacity_gb = capacity / (1024**3)
                            # Пропускаем пустые модули (емкость 0)
                            if capacity_gb == 0:
                                continue
                        except:
                            continue
                        
                        speed_raw = mem_data.get('Speed', '').strip('"').strip()
                        speed = f"{speed_raw} МГц" if speed_raw and speed_raw.isdigit() else "Неизвестно"
                        
                        manufacturer = mem_data.get('Manufacturer', '').strip('"').strip()
                        if not manufacturer or manufacturer == 'NULL':
                            manufacturer = 'Неизвестно'
                        
                        part_number = mem_data.get('PartNumber', '').strip('"').strip()
                        if not part_number or part_number == 'NULL':
                            part_number = 'Неизвестно'
                        
                        bank_label = mem_data.get('BankLabel', '').strip('"').strip()
                        device_locator = mem_data.get('DeviceLocator', '').strip('"').strip()
                        
                        location = bank_label if bank_label else (device_locator if device_locator else f"Слот {module_count+1}")
                        
                        info[f'Модуль {module_count+1} ({location})'] = f"{capacity_gb:.1f} ГБ"
                        info[f'  Модуль {module_count+1} Производитель'] = manufacturer
                        info[f'  Модуль {module_count+1} Скорость'] = speed
                        info[f'  Модуль {module_count+1} Модель'] = part_number
                        
                        module_count += 1
                
                # Альтернативный метод через PowerShell (более надежный)
                if module_count == 0:
                    try:
                        import subprocess
                        import json
                        
                        ps_command = '''
                        Get-WmiObject Win32_PhysicalMemory | Select-Object BankLabel, Capacity, Speed, Manufacturer, PartNumber, SerialNumber, DeviceLocator | ConvertTo-Json
                        '''
                        
                        result = subprocess.run(['powershell', '-Command', ps_command], 
                                              capture_output=True, 
                                              text=True,
                                              encoding='utf-8')
                        
                        if result.returncode == 0 and result.stdout.strip():
                            mem_data = json.loads(result.stdout) if result.stdout.strip() else []
                            if not isinstance(mem_data, list):
                                mem_data = [mem_data]
                            
                            for i, module in enumerate(mem_data):
                                capacity = module.get('Capacity', 0)
                                if capacity == 0:
                                    continue
                                    
                                capacity_gb = capacity / (1024**3)
                                speed = module.get('Speed', 0)
                                manufacturer = module.get('Manufacturer', '').strip()
                                part_number = module.get('PartNumber', '').strip()
                                bank_label = module.get('BankLabel', '').strip()
                                device_locator = module.get('DeviceLocator', '').strip()
                                
                                location = bank_label if bank_label else (device_locator if device_locator else f"Слот {i+1}")
                                
                                info[f'Модуль {i+1} ({location})'] = f"{capacity_gb:.1f} ГБ"
                                info[f'  Модуль {i+1} Производитель'] = manufacturer if manufacturer else 'Неизвестно'
                                info[f'  Модуль {i+1} Скорость'] = f"{speed} МГц" if speed else 'Неизвестно'
                                info[f'  Модуль {i+1} Модель'] = part_number if part_number else 'Неизвестно'
                                
                                module_count += 1
                    except Exception as e:
                        print(f"Ошибка при получении информации о памяти через PowerShell: {e}")
                
                # Дополнительная информация о конфигурации памяти
                try:
                    mem_config = run_command('wmic memphysical get MaxCapacity, MemoryDevices, TotalPhysicalMemory /format:list')
                    if mem_config:
                        lines = mem_config.strip().split('\n')
                        config = {}
                        for line in lines:
                            if '=' in line:
                                key, value = line.split('=', 1)
                                config[key.strip()] = value.strip()
                        
                        max_capacity = config.get('MaxCapacity', '0')
                        if max_capacity and max_capacity.isdigit():
                            max_capacity_gb = int(max_capacity) / 1024  # wmic возвращает в МБ
                            info['Максимальный объем ОЗУ'] = f"{max_capacity_gb:.0f} ГБ"
                        
                        memory_devices = config.get('MemoryDevices', '0')
                        if memory_devices and memory_devices.isdigit():
                            info['Всего слотов памяти'] = memory_devices
                        
                        total_physical = config.get('TotalPhysicalMemory', '0')
                        if total_physical and total_physical.isdigit():
                            total_physical_gb = int(total_physical) / (1024**3)
                            info['Установлено ОЗУ (физически)'] = f"{total_physical_gb:.2f} ГБ"
                except:
                    pass
                        
            except Exception as e:
                info['Ошибка модулей памяти'] = str(e)
        
        # Для Linux/Mac используем другую команду
        elif platform.system() in ['Linux', 'Darwin']:
            try:
                # Для Linux
                if platform.system() == 'Linux':
                    mem_info = run_command('sudo dmidecode --type 17 2>/dev/null || echo "Требуются права root"')
                    # Парсинг вывода dmidecode...
                # Для Mac
                else:
                    mem_info = run_command('system_profiler SPMemoryDataType')
                    # Парсинг вывода system_profiler...
            except:
                pass
        
        # Рассчитываем дополнительную информацию
        try:
            # Используемая память процессами
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
                try:
                    mem = proc.info['memory_info']
                    if mem:
                        processes.append((proc.info['pid'], proc.info['name'], mem.rss))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Сортируем по использованию памяти
            processes.sort(key=lambda x: x[2], reverse=True)
            
            # Топ-5 процессов по использованию памяти
            info['Топ процессов по использованию ОЗУ:'] = ""
            for i, (pid, name, rss) in enumerate(processes[:5]):
                rss_gb = rss / (1024**3)
                info[f'  {i+1}. {name} (PID: {pid})'] = f"{rss_gb:.2f} ГБ"
        except:
            pass
        
    except Exception as e:
        info['Ошибка'] = str(e)
    
    return info

def get_disk_info() -> Dict[str, str]:
    """Информация о дисках"""
    print("🔍 Получение информации о дисках...")
    info = {}
    try:
        # Информация о разделах (логических дисках)
        partitions = psutil.disk_partitions(all=False)  # all=False исключает специальные разделы
        for i, partition in enumerate(partitions):
            try:
                # Пропускаем CD/DVD диски и сетевые диски
                if 'cdrom' in partition.opts.lower() or partition.fstype == '':
                    continue
                    
                usage = psutil.disk_usage(partition.mountpoint)
                info[f'Диск {i}'] = f"{partition.device} -> {partition.mountpoint}"
                info[f'  Диск {i} Файловая система'] = f"{partition.fstype if partition.fstype else 'Неизвестно'}"
                info[f'  Диск {i} Общий размер'] = f"{usage.total / (1024**3):.1f} ГБ"
                info[f'  Диск {i} Использовано'] = f"{usage.percent:.1f}%"
                info[f'  Диск {i} Свободно'] = f"{usage.free / (1024**3):.1f} ГБ"
                info[f'  Диск {i} Использовано (ГБ)'] = f"{(usage.total - usage.free) / (1024**3):.1f} ГБ"
            except (PermissionError, FileNotFoundError):
                info[f'Диск {i}'] = f"{partition.device} -> {partition.mountpoint}"
                info[f'  Диск {i} Файловая система'] = f"{partition.fstype if partition.fstype else 'Неизвестно'}"
                info[f'  Диск {i} Статус'] = "Нет доступа"
                continue
            except Exception as e:
                continue
        
        # Информация о физических дисках (Windows) - улучшенный парсинг
        if platform.system() == "Windows":
            try:
                # Используем CSV формат для более стабильного парсинга
                disk_output = run_command('wmic diskdrive get DeviceID,Model,Size,InterfaceType,MediaType /format:csv')
                
                lines = [line.strip() for line in disk_output.strip().split('\n') if line.strip()]
                
                if len(lines) > 1:
                    headers = lines[0].split(',')
                    
                    physical_disk_count = 0
                    for line in lines[1:]:
                        values = line.split(',')
                        # Дополняем значения до нужной длины
                        while len(values) < len(headers):
                            values.append('')
                        
                        disk_data = dict(zip(headers, values))
                        
                        device_id = disk_data.get('DeviceID', '').strip('"').strip()
                        model = disk_data.get('Model', '').strip('"').strip()
                        
                        # Если модель пустая или "Неизвестно", пропускаем
                        if not model or model == 'NULL' or 'Неизвестно' in model:
                            continue
                        
                        size_raw = disk_data.get('Size', '0').strip('"').strip()
                        try:
                            size = int(size_raw) if size_raw.isdigit() else 0
                            size_gb = size / (1024**3)
                            size_str = f"{size_gb:.1f} ГБ"
                        except:
                            size_str = "Неизвестно"
                        
                        interface = disk_data.get('InterfaceType', 'N/A').strip('"').strip()
                        media_type = disk_data.get('MediaType', 'N/A').strip('"').strip()
                        
                        # Определяем тип диска по модели
                        disk_type = "HDD"
                        if "SSD" in model.upper() or "SOLID" in model.upper():
                            disk_type = "SSD"
                        elif "NVME" in model.upper() or "M.2" in model.upper():
                            disk_type = "NVMe"
                        
                        info[f'Физический диск {physical_disk_count}'] = f"{model}"
                        info[f'  Физический диск {physical_disk_count} Устройство'] = f"{device_id}"
                        info[f'  Физический диск {physical_disk_count} Размер'] = f"{size_str}"
                        info[f'  Физический диск {physical_disk_count} Тип'] = f"{disk_type}"
                        if interface and interface != 'N/A' and interface != 'NULL':
                            info[f'  Физический диск {physical_disk_count} Интерфейс'] = f"{interface}"
                        if media_type and media_type != 'N/A' and media_type != 'NULL':
                            info[f'  Физический диск {physical_disk_count} Тип носителя'] = f"{media_type}"
                        
                        physical_disk_count += 1
                
                # Альтернативный метод через PowerShell (более надежный)
                if physical_disk_count == 0:
                    try:
                        import subprocess
                        import json
                        
                        ps_command = '''
                        Get-WmiObject Win32_DiskDrive | Select-Object DeviceID, Model, Size, InterfaceType, MediaType | ConvertTo-Json
                        '''
                        
                        result = subprocess.run(['powershell', '-Command', ps_command], 
                                              capture_output=True, 
                                              text=True,
                                              encoding='utf-8')
                        
                        if result.returncode == 0 and result.stdout.strip():
                            disks_data = json.loads(result.stdout) if result.stdout.strip() else []
                            if not isinstance(disks_data, list):
                                disks_data = [disks_data]
                            
                            for i, disk in enumerate(disks_data):
                                model = disk.get('Model', '').strip()
                                if model:
                                    info[f'Физический диск {i}'] = model
                                    
                                    size = disk.get('Size', 0)
                                    if size and size > 0:
                                        size_gb = size / (1024**3)
                                        info[f'  Физический диск {i} Размер'] = f"{size_gb:.1f} ГБ"
                                    
                                    interface = disk.get('InterfaceType', '')
                                    if interface:
                                        info[f'  Физический диск {i} Интерфейс'] = interface
                                    
                                    media_type = disk.get('MediaType', '')
                                    if media_type:
                                        info[f'  Физический диск {i} Тип носителя'] = media_type
                    except:
                        pass
                        
            except Exception as e:
                print(f"Ошибка при получении информации о физических дисках: {e}")
                info['Ошибка физических дисков'] = str(e)
        
        # Если нет информации о дисках, попробуем получить через df на Linux/Mac
        if platform.system() != "Windows" and not info:
            try:
                df_output = run_command('df -h')
                lines = df_output.strip().split('\n')[1:]  # Пропускаем заголовок
                
                disk_count = 0
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 6:
                        filesystem = parts[0]
                        size = parts[1]
                        used = parts[2]
                        avail = parts[3]
                        use_percent = parts[4]
                        mountpoint = parts[5]
                        
                        # Пропускаем специальные файловые системы
                        if not filesystem.startswith('/dev/') or 'loop' in filesystem:
                            continue
                            
                        info[f'Диск {disk_count}'] = f"{filesystem} -> {mountpoint}"
                        info[f'  Диск {disk_count} Общий размер'] = size
                        info[f'  Диск {disk_count} Использовано'] = used
                        info[f'  Диск {disk_count} Доступно'] = avail
                        info[f'  Диск {disk_count} Использовано (%)'] = use_percent
                        
                        disk_count += 1
            except:
                pass
                
    except Exception as e:
        info['Ошибка'] = str(e)
    
    return info

def get_gpu_info() -> Dict[str, str]:
    """Информация о графических процессорах"""
    print("🔍 Получение информации о GPU...")
    info = {}
    try:
        if platform.system() == "Windows":
            # Используем другой формат вывода
            gpu_info = run_command('wmic path win32_videocontroller get name,adapterram,driverversion /format:csv')
            
            # Разделяем строки и удаляем пустые
            lines = [line.strip() for line in gpu_info.strip().split('\n') if line.strip()]
            
            # Первая строка - заголовки
            if len(lines) > 1:
                headers = lines[0].split(',')
                
                for i, line in enumerate(lines[1:], 1):
                    values = line.split(',')
                    gpu_data = dict(zip(headers, values))
                    
                    name = gpu_data.get('Name', '').strip('"')
                    if not name or name == 'NULL':
                        continue  # Пропускаем пустые записи
                    
                    memory_raw = gpu_data.get('AdapterRAM', '0')
                    try:
                        memory = int(memory_raw) / (1024**3)
                        memory_str = f"{memory:.1f} ГБ"
                    except:
                        memory_str = "N/A"
                    
                    driver = gpu_data.get('DriverVersion', 'N/A').strip('"')
                    
                    info[f'GPU {i-1}'] = name
                    info[f'  GPU {i-1} Видеопамять'] = memory_str
                    info[f'  GPU {i-1} Драйвер'] = driver
            
            # Дополнительная попытка получить частоту обновления
            try:
                refresh_info = run_command('wmic path win32_videocontroller get name,currentrefreshrate /format:csv')
                refresh_lines = [line.strip() for line in refresh_info.strip().split('\n') if line.strip()]
                
                if len(refresh_lines) > 1:
                    refresh_headers = refresh_lines[0].split(',')
                    for line in refresh_lines[1:]:
                        values = line.split(',')
                        if len(values) >= 2:
                            gpu_name = values[0].strip('"')
                            refresh_rate = values[1].strip('"') if len(values) > 1 else 'N/A'
                            
                            # Находим соответствующий GPU по имени
                            for key, value in list(info.items()):
                                if value == gpu_name and key.startswith('GPU '):
                                    gpu_num = key.split()[1]
                                    info[f'  GPU {gpu_num} Частота обновления'] = f"{refresh_rate} Гц" if refresh_rate != 'NULL' else "N/A"
            except:
                pass  # Если не удалось получить частоту обновления
            
            # Альтернативный метод через dxdiag (если предыдущий не сработал)
            if not info:
                try:
                    import subprocess
                    import tempfile
                    import os
                    
                    with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as tmp:
                        tmp_path = tmp.name
                    
                    # Запускаем dxdiag и сохраняем в файл
                    subprocess.run(['dxdiag', '/t', tmp_path], 
                                 capture_output=True, 
                                 text=True, 
                                 timeout=10)
                    
                    with open(tmp_path, 'r', encoding='utf-16') as f:
                        dxdiag_output = f.read()
                    
                    os.unlink(tmp_path)
                    
                    # Ищем информацию о GPU в выводе dxdiag
                    import re
                    
                    # Ищем все секции Display Devices
                    sections = re.split(r'-{50,}', dxdiag_output)
                    
                    gpu_count = 0
                    for section in sections:
                        if 'Card name:' in section:
                            lines = section.split('\n')
                            gpu_data = {}
                            for line in lines:
                                if ':' in line:
                                    key, value = line.split(':', 1)
                                    gpu_data[key.strip()] = value.strip()
                            
                            name = gpu_data.get('Card name', '').strip()
                            if name:
                                info[f'GPU {gpu_count}'] = name
                                
                                memory = gpu_data.get('Display Memory', 'N/A')
                                info[f'  GPU {gpu_count} Видеопамять'] = memory
                                
                                driver = gpu_data.get('Driver Version', 'N/A')
                                info[f'  GPU {gpu_count} Драйвер'] = driver
                                
                                gpu_count += 1
                except Exception as e:
                    print(f"Ошибка при получении информации через dxdiag: {e}")
    
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
            
            for i, adapter in enumerate(adapter_list):
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

import ctypes
from ctypes import wintypes
from typing import Dict, List
import platform

def get_monitor_info() -> Dict[str, str]:
    """Информация о мониторах с использованием Windows API"""
    print("🔍 Получение информации о мониторах...")
    info = {}
    
    if platform.system() != "Windows":
        info['Ошибка'] = "Функция поддерживается только на Windows"
        return info
    
    try:
        # Определяем структуры и функции Windows API
        class RECT(ctypes.Structure):
            _fields_ = [
                ("left", wintypes.LONG),
                ("top", wintypes.LONG),
                ("right", wintypes.LONG),
                ("bottom", wintypes.LONG)
            ]
        
        class MONITORINFOEX(ctypes.Structure):
            _fields_ = [
                ("cbSize", wintypes.DWORD),
                ("rcMonitor", RECT),
                ("rcWork", RECT),
                ("dwFlags", wintypes.DWORD),
                ("szDevice", wintypes.WCHAR * 32)
            ]
            
        # Получаем дескрипторы мониторов
        def callback(hmonitor, hdc, lprect, lparam):
            monitors.append(hmonitor)
            return 1
        
        # Импортируем необходимые функции
        user32 = ctypes.windll.user32
        gdi32 = ctypes.windll.gdi32
        
        EnumDisplayMonitors = user32.EnumDisplayMonitors
        GetMonitorInfo = user32.GetMonitorInfoW
        
        monitors = []
        MonitorEnumProc = ctypes.WINFUNCTYPE(
            ctypes.c_int,
            wintypes.HMONITOR,
            wintypes.HDC,
            ctypes.POINTER(RECT),
            wintypes.LPARAM
        )
        
        # Перечисляем мониторы
        EnumDisplayMonitors(None, None, MonitorEnumProc(callback), 0)
        
        monitor_count = len(monitors)
        physical_monitors = []
        
        for i, hmonitor in enumerate(monitors):
            monitor_info = MONITORINFOEX()
            monitor_info.cbSize = ctypes.sizeof(MONITORINFOEX)
            
            if GetMonitorInfo(hmonitor, ctypes.byref(monitor_info)):
                # Получаем дополнительную информацию через DisplayConfig API (только для Windows 10+)
                try:
                    # Пытаемся получить "дружественное" имя монитора
                    from ctypes import POINTER, Structure, byref, c_uint, c_void_p, c_wchar_p
                    
                    # Определяем структуры для QueryDisplayConfig
                    class DISPLAYCONFIG_PATH_INFO(Structure):
                        pass
                    class DISPLAYCONFIG_MODE_INFO(Structure):
                        pass
                    
                    # Простой способ: используем EnumDisplayDevices
                    class DISPLAY_DEVICE(Structure):
                        _fields_ = [
                            ("cb", wintypes.DWORD),
                            ("DeviceName", wintypes.WCHAR * 32),
                            ("DeviceString", wintypes.WCHAR * 128),
                            ("StateFlags", wintypes.DWORD),
                            ("DeviceID", wintypes.WCHAR * 128),
                            ("DeviceKey", wintypes.WCHAR * 128)
                        ]
                    
                    display_device = DISPLAY_DEVICE()
                    display_device.cb = ctypes.sizeof(DISPLAY_DEVICE)
                    
                    device_name = monitor_info.szDevice
                    monitor_name = "Неизвестный монитор"
                    
                    # Перебираем все устройства дисплея
                    device_index = 0
                    while user32.EnumDisplayDevicesW(None, device_index, byref(display_device), 0):
                        if display_device.DeviceName == device_name:
                            # Это наш монитор, получаем его "дружественное" имя
                            monitor_device = DISPLAY_DEVICE()
                            monitor_device.cb = ctypes.sizeof(DISPLAY_DEVICE)
                            
                            if user32.EnumDisplayDevicesW(
                                display_device.DeviceName, 
                                0, 
                                byref(monitor_device), 
                                0
                            ):
                                if monitor_device.DeviceString:
                                    monitor_name = monitor_device.DeviceString
                            
                            break
                        device_index += 1
                    
                except Exception:
                    # Если не получилось, используем имя устройства
                    monitor_name = f"Монитор {i+1}"
                
                # Проверяем, активен ли монитор (не виртуальный)
                width = monitor_info.rcMonitor.right - monitor_info.rcMonitor.left
                height = monitor_info.rcMonitor.bottom - monitor_info.rcMonitor.top
                
                # Фильтруем виртуальные мониторы (у них обычно маленькое разрешение или они отключены)
                if width > 0 and height > 0 and width * height > 10000:  # Минимум 100x100 пикселей
                    physical_monitors.append({
                        'name': monitor_name,
                        'width': width,
                        'height': height,
                        'device': monitor_info.szDevice
                    })
        
        # Формируем результат
        if physical_monitors:
            for i, monitor in enumerate(physical_monitors):
                info[f'Монитор {i+1}'] = monitor['name']
                info[f'  Разрешение'] = f"{monitor['width']}x{monitor['height']}"
                info[f'  Устройство'] = monitor['device']
        else:
            info['Информация'] = "Физические мониторы не обнаружены"
            
        info['Всего мониторов'] = f"{len(physical_monitors)} физических, {monitor_count} всего"
        
    except Exception as e:
        import traceback
        info['Ошибка'] = str(e)
        info['Трассировка'] = traceback.format_exc()
    
    return info


# Альтернативный вариант с использованием WMI (более простой, но может показывать виртуальные мониторы)
def get_monitor_info_wmi() -> Dict[str, str]:
    """Информация о мониторах через WMI с фильтрацией виртуальных"""
    print("🔍 Получение информации о мониторах через WMI...")
    info = {}
    
    try:
        import wmi
        
        c = wmi.WMI()
        
        # Получаем информацию о мониторах
        monitors = c.Win32_DesktopMonitor()
        
        physical_monitors = []
        for i, monitor in enumerate(monitors):
            # Фильтруем виртуальные мониторы
            if (monitor.ScreenWidth and monitor.ScreenHeight and 
                monitor.ScreenWidth > 0 and monitor.ScreenHeight > 0):
                
                name = monitor.Name or monitor.Caption or f"Монитор {i+1}"
                
                # Проверяем, не является ли это виртуальным монитором
                virtual_keywords = ['virtual', 'generic', 'стандартный', 'default']
                if any(keyword in name.lower() for keyword in virtual_keywords):
                    continue
                
                physical_monitors.append({
                    'name': name,
                    'width': monitor.ScreenWidth,
                    'height': monitor.ScreenHeight,
                    'pnp_device_id': monitor.PNPDeviceID or 'N/A'
                })
        
        if physical_monitors:
            for i, monitor in enumerate(physical_monitors):
                info[f'Монитор {i+1}'] = monitor['name']
                info[f'  Разрешение'] = f"{monitor['width']}x{monitor['height']}"
        else:
            info['Информация'] = "Физические мониторы не обнаружены"
            
        info['Всего обнаружено'] = f"{len(physical_monitors)} физических мониторов"
        
    except ImportError:
        info['Ошибка'] = "Установите библиотеку wmi: pip install wmi"
    except Exception as e:
        info['Ошибка'] = str(e)
    
    return info


# Самый простой вариант через screeninfo (требует установки библиотеки)
def get_monitor_info_simple() -> Dict[str, str]:
    """Информация о мониторах через screeninfo (только физические)"""
    print("🔍 Получение информации о мониторах через screeninfo...")
    info = {}
    
    try:
        from screeninfo import get_monitors
        
        monitors = get_monitors()
        
        if monitors:
            for i, monitor in enumerate(monitors):
                if monitor.is_primary:
                    info[f'Монитор {i+1}'] = f"{monitor.name or 'Безымянный'} (Основной)"
                else:
                    info[f'Монитор {i+1}'] = monitor.name or f"Монитор {i+1}"
                
                info[f'  Разрешение'] = f"{monitor.width}x{monitor.height}"
                if monitor.x != 0 or monitor.y != 0:
                    info[f'  Положение'] = f"({monitor.x}, {monitor.y})"
        else:
            info['Информация'] = "Мониторы не обнаружены"
            
    except ImportError:
        info['Ошибка'] = "Установите библиотеку screeninfo: pip install screeninfo"
    except Exception as e:
        info['Ошибка'] = str(e)
    
    return info


# Основная функция, которая выбирает лучший способ
def get_monitor_info_fixed() -> Dict[str, str]:
    """Информация о мониторах (использует лучший доступный метод)"""
    if platform.system() != "Windows":
        return get_monitor_info_simple()
    
    # Пробуем разные методы в порядке предпочтения
    try:
        from screeninfo import get_monitors
        return get_monitor_info_simple()
    except:
        try:
            return get_monitor_info()  # Первый вариант с Windows API
        except:
            return get_monitor_info_wmi()  # Вариант с WMI

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


def print_section(title: str, data: Dict[str, str]):
    """Выводит секцию информации в консоль"""
    print(f"\n{'='*60}")
    print(f"{title.upper()}")
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
    main()
    input("\nНажмите Enter для выхода...")