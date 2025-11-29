import subprocess
import os

# Формируем путь для сохранения файла
output_file = os.path.join(os.getcwd(), "system_report.nfo")

# Команда для msinfo32
command = ['msinfo32', '/nfo', output_file]

# Запускаем процесс
try:
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    print(f"Отчёт успешно сохранён в: {output_file}")
except subprocess.CalledProcessError as e:
    print(f"Произошла ошибка: {e}")