from telegraph import Telegraph
import json, time

# Підключення до Telegraph API
telegraph = Telegraph()
telegraph.create_account(short_name='Project')

with open('icao_dict.json', 'r', encoding='utf-8') as json_file:
    data = json.load(json_file)

# Створення статті
article_title = "ICAO аеропортів світу"
article_content = []
country_content = []

# Додавання посилань на сторінки країн у зміст
article_content.append('<ul>')

for country, airports in data.items():
    # Додавання аеропортів до сторінки
    airport_list = '<ul>'
    for airport in airports:
        airport_list += f'<li>{airport}</li>'
    airport_list += '</ul>'
    country_content.append(airport_list)
    page = telegraph.create_page(title=country, html_content='\n'.join(country_content))
    country_url = page['url']
    time.sleep(1)
    country_content.clear()
    article_content.append(f'<li><a href="{country_url}">{country}</a></li>')

article_content.append('</ul>')

# Збірка контенту статті
article_content = '\n\n'.join(data)

# Створення статті на Telegraph
article = telegraph.create_page(title=article_title, html_content=article_content)

# Отримання посилання на статтю
article_url = article['url']
print(f'Посилання на Вашу статтю: {article_url}')