import platform
import psutil
import subprocess
import socket
import datetime
import os
import sys
import re
import json
import winreg
import ctypes
import tempfile
from typing import Dict, List, Optional

def run_command(cmd: str) -> str:
    """Выполняет команду и возвращает результат"""
    try:
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, text=True, encoding='cp866')
        return result.strip()
    except:
        return ""

def run_command_powershell(cmd: str) -> str:
    """Выполняет PowerShell команду"""
    try:
        ps_command = f'powershell -Command "{cmd}"'
        result = subprocess.check_output(ps_command, shell=True, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, text=True, encoding='utf-8')
        return result.strip()
    except:
        return ""

def get_windows_serial_number() -> str:
    """Получает серийный номер Windows (системы)"""
    serial = ""
    try:
        # Способ 1: через wmic
        output = run_command('wmic bios get serialnumber /value')
        if output and 'SerialNumber' in output:
            for line in output.split('\n'):
                if 'SerialNumber' in line:
                    serial = line.split('=')[-1].strip()
                    break
        
        # Способ 2: через PowerShell (более надежный)
        if not serial or serial == '0' or 'OEM' in serial.upper():
            ps_output = run_command_powershell('Get-WmiObject Win32_BIOS | Select-Object SerialNumber | ConvertTo-Json')
            if ps_output:
                try:
                    data = json.loads(ps_output)
                    if isinstance(data, dict) and 'SerialNumber' in data:
                        serial = data['SerialNumber']
                    elif isinstance(data, list) and len(data) > 0 and 'SerialNumber' in data[0]:
                        serial = data[0]['SerialNumber']
                except:
                    pass
        
        # Способ 3: через реестр (для OEM систем)
        if not serial or serial == '0' or len(serial) < 3:
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\OEMInformation")
                serial = winreg.QueryValueEx(key, "SerialNumber")[0]
                winreg.CloseKey(key)
            except:
                pass
        
        # Способ 4: через systeminfo
        if not serial or serial == '0':
            output = run_command('systeminfo | findstr /C:"System Serial Number"')
            if output:
                serial = output.split(':')[-1].strip()
    except Exception as e:
        print(f"Ошибка получения серийного номера Windows: {e}")
    
    return serial if serial and serial != '0' and 'OEM' not in serial.upper() else "Не доступен"

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
                        ps_command = '''
                        Get-WmiObject Win32_PhysicalMemory | Select-Object BankLabel, Capacity, Speed, Manufacturer, PartNumber, SerialNumber, DeviceLocator | ConvertTo-Json
                        '''
                        
                        result = run_command_powershell(ps_command)
                        
                        if result:
                            mem_data = json.loads(result) if result.strip() else []
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
                        ps_command = '''
                        Get-WmiObject Win32_DiskDrive | Select-Object DeviceID, Model, Size, InterfaceType, MediaType | ConvertTo-Json
                        '''
                        
                        result = run_command_powershell(ps_command)
                        
                        if result:
                            disks_data = json.loads(result) if result.strip() else []
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
                    
                    user32 = ctypes.windll.user32
                    width = user32.GetSystemMetrics(0)  # SM_CXSCREEN
                    height = user32.GetSystemMetrics(1) # SM_CYSCREEN

                    name = monitor_info.get('Name', 'Неизвестно')
                    
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

def get_hardware_serial_numbers() -> Dict[str, Dict[str, str]]:
    """Получает серийные номера всех аппаратных компонентов"""
    print("🔍 Поиск серийных номеров устройств...")
    serials = {}
    
    if platform.system() != "Windows":
        serials['Ошибка'] = {"Сообщение": "Функция доступна только для Windows"}
        return serials
    
    try:
        # 1. Серийный номер системы (BIOS)
        system_serial = get_windows_serial_number()
        serials['Система (BIOS)'] = {
            'Серийный номер': system_serial,
            'Метод получения': 'BIOS/System Information'
        }
        
        # 2. Процессор
        try:
            cpu_info = run_command('wmic cpu get processorid,serialnumber /value')
            cpu_serial = ""
            for line in cpu_info.split('\n'):
                if 'SerialNumber' in line and '=' in line:
                    cpu_serial = line.split('=')[-1].strip()
                    if cpu_serial and cpu_serial != '0' and cpu_serial != 'N/A':
                        break
                elif 'ProcessorId' in line and '=' in line and not cpu_serial:
                    cpu_serial = line.split('=')[-1].strip()
            
            if cpu_serial and cpu_serial != '0' and cpu_serial != 'N/A':
                serials['Процессор'] = {
                    'Серийный номер': cpu_serial,
                    'Метод получения': 'WMIC CPU'
                }
        except Exception as e:
            print(f"Ошибка получения серийного номера процессора: {e}")
        
        # 3. Материнская плата
        try:
            mb_info = run_command('wmic baseboard get serialnumber,product /value')
            mb_serial = ""
            mb_model = ""
            for line in mb_info.split('\n'):
                if 'SerialNumber' in line and '=' in line:
                    mb_serial = line.split('=')[-1].strip()
                elif 'Product' in line and '=' in line:
                    mb_model = line.split('=')[-1].strip()
            
            if mb_serial and mb_serial != '0' and mb_serial != 'N/A' and 'OEM' not in mb_serial.upper():
                serials['Материнская плата'] = {
                    'Серийный номер': mb_serial,
                    'Модель': mb_model if mb_model else "Неизвестно",
                    'Метод получения': 'WMIC Baseboard'
                }
        except Exception as e:
            print(f"Ошибка получения серийного номера материнской платы: {e}")
        
        # 4. Оперативная память (все модули)
        try:
            # Через PowerShell для более надежного получения
            ps_command = '''
            $memory = Get-WmiObject Win32_PhysicalMemory
            $result = @()
            foreach ($module in $memory) {
                $obj = New-Object PSObject
                $obj | Add-Member -MemberType NoteProperty -Name "BankLabel" -Value $module.BankLabel
                $obj | Add-Member -MemberType NoteProperty -Name "CapacityGB" -Value ([math]::Round($module.Capacity/1GB, 2))
                $obj | Add-Member -MemberType NoteProperty -Name "SerialNumber" -Value $module.SerialNumber
                $obj | Add-Member -MemberType NoteProperty -Name "PartNumber" -Value $module.PartNumber
                $result += $obj
            }
            $result | ConvertTo-Json
            '''
            
            memory_output = run_command_powershell(ps_command)
            if memory_output:
                try:
                    memory_modules = json.loads(memory_output) if memory_output.strip() else []
                    if not isinstance(memory_modules, list):
                        memory_modules = [memory_modules]
                    
                    for i, module in enumerate(memory_modules):
                        serial_num = module.get('SerialNumber', '').strip()
                        if serial_num and serial_num != '0' and len(serial_num) > 3:
                            bank = module.get('BankLabel', f'Слот {i+1}')
                            capacity = module.get('CapacityGB', 'Неизвестно')
                            part_num = module.get('PartNumber', 'Неизвестно')
                            
                            serials[f'ОЗУ Модуль {i+1} ({bank})'] = {
                                'Серийный номер': serial_num,
                                'Емкость': f"{capacity} ГБ" if capacity != 'Неизвестно' else capacity,
                                'Модель': part_num,
                                'Метод получения': 'WMI PhysicalMemory'
                            }
                except:
                    pass
        except Exception as e:
            print(f"Ошибка получения серийных номеров памяти: {e}")
        
        # 5. Диски (HDD/SSD)
        try:
            ps_command = '''
            $disks = Get-PhysicalDisk
            $result = @()
            foreach ($disk in $disks) {
                $obj = New-Object PSObject
                $obj | Add-Member -MemberType NoteProperty -Name "DeviceID" -Value $disk.DeviceId
                $obj | Add-Member -MemberType NoteProperty -Name "Model" -Value $disk.Model
                $obj | Add-Member -MemberType NoteProperty -Name "SerialNumber" -Value $disk.SerialNumber
                $obj | Add-Member -MemberType NoteProperty -Name "SizeGB" -Value ([math]::Round($disk.Size/1GB, 2))
                $obj | Add-Member -MemberType NoteProperty -Name "MediaType" -Value $disk.MediaType
                $result += $obj
            }
            $result | ConvertTo-Json
            '''
            
            disks_output = run_command_powershell(ps_command)
            if not disks_output:
                # Альтернативный метод через Win32_DiskDrive
                disks_output = run_command_powershell('Get-WmiObject Win32_DiskDrive | Select-Object DeviceID,Model,SerialNumber,Size,InterfaceType | ConvertTo-Json')
            
            if disks_output:
                try:
                    disks = json.loads(disks_output) if disks_output.strip() else []
                    if not isinstance(disks, list):
                        disks = [disks]
                    
                    for i, disk in enumerate(disks):
                        serial_num = disk.get('SerialNumber', '').strip()
                        if serial_num and serial_num != '0' and len(serial_num) > 3:
                            model = disk.get('Model', 'Неизвестный диск').strip()
                            size = disk.get('SizeGB', 0)
                            if not size and 'Size' in disk:
                                size = round(int(disk.get('Size', 0)) / (1024**3), 2)
                            
                            media_type = disk.get('MediaType', '')
                            if not media_type:
                                model_upper = model.upper()
                                if 'SSD' in model_upper:
                                    media_type = 'SSD'
                                elif 'HDD' in model_upper or 'HARD' in model_upper:
                                    media_type = 'HDD'
                                elif 'NVME' in model_upper or 'M.2' in model_upper:
                                    media_type = 'NVMe'
                                else:
                                    media_type = 'Неизвестно'
                            
                            serials[f'Диск {i+1} ({model})'] = {
                                'Серийный номер': serial_num,
                                'Модель': model,
                                'Емкость': f"{size} ГБ" if size else "Неизвестно",
                                'Тип носителя': media_type,
                                'Метод получения': 'WMI DiskDrive/PhysicalDisk'
                            }
                except:
                    pass
        except Exception as e:
            print(f"Ошибка получения серийных номеров дисков: {e}")
        
        # 6. Видеокарты
        try:
            gpu_output = run_command_powershell('Get-WmiObject Win32_VideoController | Select-Object Name,AdapterRAM,DriverVersion,PNPDeviceID | ConvertTo-Json')
            if gpu_output:
                try:
                    gpus = json.loads(gpu_output) if gpu_output.strip() else []
                    if not isinstance(gpus, list):
                        gpus = [gpus]
                    
                    for i, gpu in enumerate(gpus):
                        pnp_id = gpu.get('PNPDeviceID', '')
                        serial_num = ""
                        
                        # Пытаемся извлечь серийный номер из PNPDeviceID или через другие методы
                        if pnp_id:
                            # Иногда серийный номер может быть в PNPDeviceID
                            parts = pnp_id.split('\\')
                            if len(parts) > 1:
                                # Ищем серийный номер в формате VID_xxxx&PID_xxxx
                                for part in parts:
                                    if 'VID_' in part and 'PID_' in part:
                                        serial_num = part
                                        break
                        
                        # Альтернативный метод через SMBIOS
                        if not serial_num:
                            smbios_output = run_command('wmic path win32_videocontroller get pnpdeviceid /value')
                            for line in smbios_output.split('\n'):
                                if 'PNPDeviceID' in line and '=' in line:
                                    pnp_full = line.split('=')[-1].strip()
                                    if 'VEN_' in pnp_full and 'DEV_' in pnp_full:
                                        serial_num = pnp_full
                                        break
                        
                        name = gpu.get('Name', f'Видеокарта {i+1}').strip()
                        if serial_num:
                            serials[f'Видеокарта {i+1} ({name})'] = {
                                'Серийный номер (ID)': serial_num,
                                'Модель': name,
                                'Метод получения': 'WMI VideoController'
                            }
                except:
                    pass
        except Exception as e:
            print(f"Ошибка получения информации о видеокартах: {e}")
        
        # 7. Сетевые адаптеры
        try:
            nic_output = run_command_powershell('Get-WmiObject Win32_NetworkAdapter | Where-Object {$_.PhysicalAdapter -eq $true} | Select-Object Name,MACAddress,PNPDeviceID | ConvertTo-Json')
            if nic_output:
                try:
                    nics = json.loads(nic_output) if nic_output.strip() else []
                    if not isinstance(nics, list):
                        nics = [nics]
                    
                    for i, nic in enumerate(nics):
                        pnp_id = nic.get('PNPDeviceID', '')
                        serial_num = ""
                        mac = nic.get('MACAddress', '')
                        
                        if pnp_id and 'VEN_' in pnp_id and 'DEV_' in pnp_id:
                            serial_num = pnp_id
                        
                        name = nic.get('Name', f'Сетевой адаптер {i+1}').strip()
                        if serial_num or mac:
                            nic_info = {
                                'Модель': name,
                                'Метод получения': 'WMI NetworkAdapter'
                            }
                            if serial_num:
                                nic_info['Серийный номер (ID)'] = serial_num
                            if mac:
                                nic_info['MAC адрес'] = mac
                            
                            serials[f'Сетевой адаптер {i+1}'] = nic_info
                except:
                    pass
        except Exception as e:
            print(f"Ошибка получения информации о сетевых адаптерах: {e}")
        
        # 8. Мониторы (через WMI)
        try:
            monitor_output = run_command_powershell('Get-WmiObject WmiMonitorID -Namespace root\\wmi | ForEach-Object { $serial = ($_.SerialNumberID -ne 0) ? [System.Text.Encoding]::ASCII.GetString($_.SerialNumberID).TrimEnd([char]0) : "Не доступен"; $manufacturer = [System.Text.Encoding]::ASCII.GetString($_.ManufacturerNameID).TrimEnd([char]0); @{SerialNumber=$serial; Manufacturer=$manufacturer} } | ConvertTo-Json')
            
            if monitor_output and monitor_output != '[]':
                try:
                    monitors = json.loads(monitor_output) if monitor_output.strip() else []
                    if not isinstance(monitors, list):
                        monitors = [monitors]
                    
                    for i, monitor in enumerate(monitors):
                        serial_num = monitor.get('SerialNumber', '').strip()
                        manufacturer = monitor.get('Manufacturer', '').strip()
                        
                        if serial_num and serial_num != 'Не доступен' and len(serial_num) > 3:
                            monitor_name = f"{manufacturer} Монитор" if manufacturer else f"Монитор {i+1}"
                            serials[monitor_name] = {
                                'Серийный номер': serial_num,
                                'Производитель': manufacturer if manufacturer else 'Неизвестно',
                                'Метод получения': 'WMI MonitorID'
                            }
                except:
                    pass
        except Exception as e:
            print(f"Ошибка получения информации о мониторах: {e}")
        
        # 9. Батарея (для ноутбуков)
        try:
            battery_output = run_command('wmic path win32_battery get serialnumber /value')
            battery_serial = ""
            for line in battery_output.split('\n'):
                if 'SerialNumber' in line and '=' in line:
                    battery_serial = line.split('=')[-1].strip()
                    break
            
            if battery_serial and battery_serial != '0' and battery_serial != 'N/A':
                serials['Батарея'] = {
                    'Серийный номер': battery_serial,
                    'Метод получения': 'WMIC Battery'
                }
        except Exception as e:
            pass  # Батарея может отсутствовать на ПК
        
        # 10. Через SMBIOS (дополнительный метод)
        try:
            smbios_output = run_command_powershell('Get-WmiObject -Class Win32_SystemEnclosure | Select-Object SerialNumber,SMBIOSAssetTag | ConvertTo-Json')
            if smbios_output:
                try:
                    smbios_data = json.loads(smbios_output) if smbios_output.strip() else {}
                    if isinstance(smbios_data, list) and len(smbios_data) > 0:
                        smbios_data = smbios_data[0]
                    
                    smbios_serial = smbios_data.get('SerialNumber', '').strip()
                    asset_tag = smbios_data.get('SMBIOSAssetTag', '').strip()
                    
                    if smbios_serial and smbios_serial != '0' and smbios_serial != system_serial:
                        serials['Система (SMBIOS)'] = {
                            'Серийный номер': smbios_serial,
                            'Asset Tag': asset_tag if asset_tag else 'Не указан',
                            'Метод получения': 'SMBIOS SystemEnclosure'
                        }
                except:
                    pass
        except Exception as e:
            print(f"Ошибка получения SMBIOS информации: {e}")
    
    except Exception as e:
        serials['Ошибка'] = {"Сообщение": f"Критическая ошибка: {str(e)}"}
    
    return serials

def print_serial_numbers(serials: Dict[str, Dict[str, str]]):
    """Выводит серийные номера в удобном формате"""
    print(f"\n{'='*80}")
    print("🔢 СЕРИЙНЫЕ НОМЕРА УСТРОЙСТВ")
    print(f"{'='*80}")
    
    if not serials:
        print("❌ Не удалось получить серийные номера")
        return
    
    error_count = 0
    success_count = 0
    
    for device, info in serials.items():
        if device == 'Ошибка':
            print(f"\n⚠️  Ошибки при получении данных:")
            if isinstance(info, dict):
                for key, value in info.items():
                    print(f"   {key}: {value}")
            error_count += 1
            continue
        
        print(f"\n📟 {device}:")
        print(f"   {'─' * 60}")
        
        if 'Серийный номер' in info:
            serial = info['Серийный номер']
            if serial and serial != 'Не доступен' and len(serial) > 3:
                print(f"   🔑 Серийный номер: {serial}")
                success_count += 1
            else:
                print(f"   ❌ Серийный номер: Не доступен или некорректный")
        elif 'Серийный номер (ID)' in info:
            print(f"   🔑 Идентификатор устройства: {info['Серийный номер (ID)']}")
            success_count += 1
        
        # Выводим дополнительную информацию
        for key, value in info.items():
            if key not in ['Серийный номер', 'Серийный номер (ID)', 'Метод получения'] and value:
                print(f"   📋 {key}: {value}")
        
        if 'Метод получения' in info:
            print(f"   🔧 Метод получения: {info['Метод получения']}")
    
    print(f"\n{'='*80}")
    print(f"📊 ИТОГО:")
    print(f"   ✅ Успешно получено: {success_count} серийных номеров")
    if error_count > 0:
        print(f"   ⚠️  Ошибок: {error_count}")
    print(f"{'='*80}")

def save_serial_numbers_to_file(serials: Dict[str, Dict[str, str]], filename: str = "serial_numbers.txt"):
    """Сохраняет серийные номера в файл"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("СЕРИЙНЫЕ НОМЕРА УСТРОЙСТВ\n")
            f.write("=" * 80 + "\n")
            f.write(f"Дата создания: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Система: {platform.system()} {platform.release()}\n")
            f.write(f"Имя компьютера: {platform.node()}\n\n")
            
            for device, info in serials.items():
                if device == 'Ошибка':
                    continue
                
                f.write(f"[{device}]\n")
                f.write("-" * 60 + "\n")
                
                if 'Серийный номер' in info:
                    serial = info['Серийный номер']
                    f.write(f"Серийный номер: {serial}\n")
                elif 'Серийный номер (ID)' in info:
                    f.write(f"Идентификатор устройства: {info['Серийный номер (ID)']}\n")
                
                for key, value in info.items():
                    if key not in ['Серийный номер', 'Серийный номер (ID)', 'Метод получения'] and value:
                        f.write(f"{key}: {value}\n")
                
                if 'Метод получения' in info:
                    f.write(f"Метод получения: {info['Метод получения']}\n")
                
                f.write("\n")
        
        print(f"\n💾 Серийные номера сохранены в файл: {filename}")
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения в файл: {e}")
        return False

def print_section(title: str, data: Dict[str, str]):
    """Выводит секцию информации в консоль"""
    print(f"\n{'='*60}")
    print(f"{title.upper()}")
    print(f"{'='*60}")
    
    for key, value in data.items():
        if value and value != "Не доступно" and value != "":
            print(f"{key:<40} : {value}")

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
    
    # Сбор серийных номеров
    print("\n" + "="*80)
    print("🔍 НАЧИНАЮ ПОИСК СЕРИЙНЫХ НОМЕРОВ УСТРОЙСТВ...")
    print("="*80)
    
    # Проверяем права администратора (рекомендуется для получения полной информации)
    if platform.system() == "Windows":
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
            if not is_admin:
                print("⚠️  ВНИМАНИЕ: Скрипт запущен без прав администратора.")
                print("   Некоторые серийные номера могут быть недоступны.")
                print("   Для получения полной информации запустите от имени администратора.\n")
        except:
            pass
    
    # Получаем серийные номера
    serial_numbers = get_hardware_serial_numbers()
    
    # Выводим серийные номера
    print_serial_numbers(serial_numbers)
    
    # Сохраняем в файл
    save_serial_numbers_to_file(serial_numbers)
    
    # Итоговая информация
    print(f"\n{'='*80}")
    print("✅ СБОР ИНФОРМАЦИИ ЗАВЕРШЕН!")
    print(f"{'='*80}")
    print(f"📅 Дата и время сбора: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"💻 Общее кол-во секций: {len(all_info) + 1} (включая серийные номера)")
    
    total_items = sum(len(data) for data in all_info.values())
    print(f"📋 Всего параметров собрано: {total_items}")
    print(f"🔑 Найдено устройств с серийными номерами: {len([k for k in serial_numbers.keys() if k != 'Ошибка'])}")

if __name__ == "__main__":
    main()
    input("\nНажмите Enter для выхода...")