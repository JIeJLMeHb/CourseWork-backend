import platform
import psutil
import datetime
import socket


print("======================================== System Information ========================================")
uname = platform.uname()
print(f"System: {uname.system}")
print(f"Node Name: {uname.node}")
print(f"Release: {uname.release}")
print(f"Version: {uname.version}")
print(f"Machine: {uname.machine}")
print(f"Processor: {uname.processor}")

print("======================================== Boot Time ========================================")
boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
print(f"Boot Time: {boot_time}")

print("======================================== CPU Info ========================================")
print(f"Physical cores: {psutil.cpu_count(logical=False)}")
print(f"Total cores: {psutil.cpu_count(logical=True)}")
cpufreq = psutil.cpu_freq()
print(f"Max Frequency: {cpufreq.max:.2f}Mhz")
print(f"Min Frequency: {cpufreq.min:.2f}Mhz")
print(f"Current Frequency: {cpufreq.current:.2f}Mhz")

print("CPU Usage Per Core:")
for i, percentage in enumerate(psutil.cpu_percent(percpu=True, interval=1)):
    print(f"Core {i}: {percentage}%")
print(f"Total CPU Usage: {psutil.cpu_percent()}%")

print("======================================== Memory Information ========================================")
svmem = psutil.virtual_memory()
print(f"Total: {svmem.total / (1024 ** 3):.2f}GB")
print(f"Available: {svmem.available / (1024 ** 3):.2f}GB")
print(f"Used: {svmem.used / (1024 ** 2):.2f}MB")
print(f"Percentage: {svmem.percent}%")

print("==================== SWAP ====================")
swap = psutil.swap_memory()
print(f"Total: {swap.total / (1024 ** 3):.2f}GB")
print(f"Free: {swap.free / (1024 ** 3):.2f}GB")
print(f"Used: {swap.used / (1024 ** 2):.2f}MB")
print(f"Percentage: {swap.percent}%")

print("======================================== Disk Information ========================================")
print("Partitions and Usage:")
partitions = psutil.disk_partitions()
for partition in partitions:
    print(f"=== Device: {partition.device} ===")
    print(f"  Mountpoint: {partition.mountpoint}")
    print(f"  File system type: {partition.fstype}")
    try:
        usage = psutil.disk_usage(partition.mountpoint)
    except PermissionError:
        continue
    print(f"  Total Size: {usage.total / (1024 ** 3):.2f}GB")
    print(f"  Used: {usage.used / (1024 ** 3):.2f}GB")
    print(f"  Free: {usage.free / (1024 ** 3):.2f}GB")
    print(f"  Percentage: {usage.percent}%")

disk_io = psutil.disk_io_counters()
print(f"Total read: {disk_io.read_bytes / (1024 ** 3):.2f}GB")
print(f"Total write: {disk_io.write_bytes / (1024 ** 3):.2f}GB")

print("======================================== Network Information ========================================")
net_io = psutil.net_io_counters()
addrs = psutil.net_if_addrs()
for interface_name, interface_addrs in addrs.items():
    print(f"=== Interface: {interface_name} ===")
    for addr in interface_addrs:
        if addr.family == socket.AF_INET:
            print(f"  IP Address: {addr.address}")
            print(f"  Netmask: {addr.netmask}")
            print(f"  Broadcast IP: {addr.broadcast}")
        elif addr.family == socket.AF_INET6:
            print(f"  IPv6 Address: {addr.address}")
            print(f"  Netmask: {addr.netmask}")
            print(f"  Broadcast IP: {addr.broadcast}")
        elif addr.family == psutil.AF_LINK:
            print(f"  MAC Address: {addr.address}")
            print(f"  Netmask: {addr.netmask}")
            print(f"  Broadcast MAC: {addr.broadcast}")

print(f"Total Bytes Sent: {net_io.bytes_sent / (1024 ** 2):.2f}MB")
print(f"Total Bytes Received: {net_io.bytes_recv / (1024 ** 2):.2f}MB")
