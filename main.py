import requests
import asyncio
import os

from bs4 import BeautifulSoup
from telebot import types
from telebot.async_telebot import AsyncTeleBot

bot = AsyncTeleBot(os.environ['TOKEN'])

url = "https://airmundo.com/en/blog/airport-codes-european-airports/"

data = []
airport_countries = []
icao_message = []
def get_airport():
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    a = soup.find('div', class_="tablescroll").find('tbody').find_all('tr')

    for tr in a:
        text_elements = [element.get_text() for element in tr.find_all('td')]
        data.append(text_elements)

    for airport_info in data:
        if airport_info[1] not in airport_countries:
            airport_countries.append(airport_info[1])
        else:
            continue
def get_airport_keyboard():
    get_airport()
    airport_keyboard = []
    keyboard_row = []
    for country in airport_countries:
        keyboard_row.append(types.InlineKeyboardButton(country, callback_data=f"Country:{country}"))
        if len(keyboard_row) == 3:
            airport_keyboard.append(keyboard_row)
            keyboard_row = []
    if keyboard_row:
        airport_keyboard.append(keyboard_row)
    return airport_keyboard

def get_airport_icao(airport_country):

    for airports_info in data:
        if airport_country in airports_info[1]:
            icao_message.append(f"*{airports_info[0]}* - `{airports_info[3]}`")
    return icao_message
# function for recieving short info
def get_info(type, icao):
    response = requests.get(f"https://beta.aviationweather.gov/cgi-bin/data/{type}.php?ids={icao.upper()}")
    return response.text

# function for recieving full info
def get_decoded_info(type, icao):
    response = requests.get(f"https://beta.aviationweather.gov/cgi-bin/data/{type}.php?ids={icao.upper()}&format=decoded")
    return response.text

@bot.message_handler(commands=['start'])
async def fn_start(message):
    await bot.send_message(message.chat.id, "Привіт. Я допоможу тобі отримати дані про METAR та TAF на будь-якому аеродромі світу. "
                                            "Для цього тобі потрібно ввести номер ICAO (неважливо яким регістром). "
                                            "\n\nЯкщо потрібні підказки - сміливо тисни /info☺️")
@bot.message_handler(commands=['info'])
async def fn_info(message):
    data.clear()
    airport_countries.clear()
    airport_keyboard = get_airport_keyboard()
    await bot.send_message(message.chat.id, "Для зручності, було додано дані про аеропорти Европи. "
                                            "Інші ти можеш знайти [тут](https://telegra.ph/ICAO-aeroportіv-svіtu-09-07-3)",
                           reply_markup=types.InlineKeyboardMarkup(airport_keyboard), parse_mode="Markdown")

@bot.message_handler(commands=['radar24'])
async def fn_info(message):
    await bot.send_message(message.chat.id, "Посилання на [FlightRadar](https://www.flightradar24.com/)",
                           disable_web_page_preview=True, parse_mode="Markdown")
@bot.message_handler(content_types=['text'])
async def fn_start(message):
    if len(message.text) != 4:
        return
    icao = message.text.upper()
    info_about_airport = get_info("stationinfo", icao)
    if not info_about_airport:
        return await bot.send_message(message.chat.id, "Некоректно введено дані. Спробуй скористатись /info "
                                                       "для отримання достовірної інформації про аеропорти")
    inline_keyboard = [
        [
            types.InlineKeyboardButton("METAR", callback_data=f"Type:metar-{message.text}"),
            types.InlineKeyboardButton("TAF", callback_data=f"Type:taf-{message.text}")
        ]
    ]
    await bot.send_message(message.chat.id, f"{info_about_airport}", reply_markup=types.InlineKeyboardMarkup(inline_keyboard))

@bot.callback_query_handler(func=lambda call: True)
async def fn_calldata(call):

    if call.data.startswith("decode"):
        """
        Originally, call.data looks like decode:{metar}-{KORD}.
        This part split it by ':' and it will look like ['decode', 'metar-KORD'].
        Then, using number of location of info ([1]) it split by '-' and it will look like ['metar', 'KORD']
        """
        info = call.data.split(":")[1].split("-")   # ['decode', 'metar-KORD']
        type = info[0]  # 'metar'
        icao = info[1]  # 'KORD'

        # Creating keyboard
        keyboard = [
            [
                types.InlineKeyboardButton("Back", callback_data=f"back:{icao}")
            ]
        ]

        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                    text=f"{get_decoded_info(type, icao)}",
                                    reply_markup=types.InlineKeyboardMarkup(keyboard))

    elif call.data.startswith("Type"):
        # This block will work, if call.data starts from Type
        """
        call.data have next structure 'Type:metar-kord'.
        in 'data_icao' it split by ':'. Now it's looks ['Type, 'metar-kord']. We use number of list to work with [1]
        Then, in 'type' it split be '-'. And it's looks like ['metar', 'kord']
        In 'icao' the same principle.     
        """
        data_icao = call.data.split(":")[1]
        type = data_icao.split("-")[0]
        icao = data_icao.split("-")[1]

        # Creating keyboard
        keyboard = [
            [
                types.InlineKeyboardButton("Decode", callback_data=f"decode:{type}-{icao}"),
                types.InlineKeyboardButton("Back", callback_data=f"back:{icao}")
            ]
        ]
        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                    text=f"{get_info(type, icao)}", reply_markup=types.InlineKeyboardMarkup(keyboard))
    elif call.data == "return":
        icao_message.clear()
        data.clear()
        airport_countries.clear()
        airport_keyboard = get_airport_keyboard()
        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                    text="Для зручності, було додано дані про аеропорти Европи. "
                                            "Інші ти можеш знайти [тут](https://telegra.ph/ICAO-aeroportіv-svіtu-09-07-3)",
                                    reply_markup=types.InlineKeyboardMarkup(airport_keyboard), parse_mode="Markdown")


    elif call.data.startswith("back"):
        icao = call.data.split(":")[1]
        info = get_info("stationinfo", icao)
        inline_keyboard = [
            [
                types.InlineKeyboardButton("METAR", callback_data=f"Type:metar-{icao}"),
                types.InlineKeyboardButton("TAF", callback_data=f"Type:taf-{icao}")
            ]
        ]
        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                    text=f"{info}", reply_markup=types.InlineKeyboardMarkup(inline_keyboard))

    elif call.data.startswith("Country"):

        keyboard = [
            [
                types.InlineKeyboardButton("Back", callback_data="return")
            ]
        ]
        airport_country = call.data.split(":")[1]
        port_info = get_airport_icao(airport_country)

        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                    text=f"У {airport_country} є наступні аеропорти: \n\n" + '\n'.join(port_info),
                                    parse_mode="Markdown", reply_markup=types.InlineKeyboardMarkup(keyboard))

asyncio.run(bot.infinity_polling(skip_pending=True))
