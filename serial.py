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

def main():

    
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
    
    print(f"🔑 Найдено устройств с серийными номерами: {len([k for k in serial_numbers.keys() if k != 'Ошибка'])}")

if __name__ == "__main__":
    main()
    input("\nНажмите Enter для выхода...")