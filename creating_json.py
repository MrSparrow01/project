import openpyxl

# Створення порожнього словника
icao_dict = {}

# Відкриття Excel-файлу
file_path = 'your_file.xlsx'
workbook = openpyxl.load_workbook(file_path)
sheet = workbook.active

# Читаємо дані з Excel і створюємо словник
for row in sheet.iter_rows(min_row=2, values_only=True):  # Починаємо з другого рядка, оскільки перший рядок містить заголовки
    icao_code = row[0]
    icao_airport = row[1]
    country_name = row[2].strip()
    if not icao_dict.get(country_name):
        icao_dict[country_name] = []
    icao_dict[country_name].append(f"{icao_airport} - {icao_code}")

# Зберігаємо словник у JSON-файл
import json

json_file_path = 'icao_dict.json'
with open(json_file_path, 'w', encoding='utf-8') as json_file:
    json.dump(icao_dict, json_file, ensure_ascii=False, indent=4)
