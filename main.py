"""
First of all, you need to have all the imported modules installed on your computer. It will not work without them.
"""

import requests
import asyncio

import telebot.types
from bs4 import BeautifulSoup
from telebot import types
from telebot.async_telebot import AsyncTeleBot

"""
In this part of the code, we declare the variable TOKEN, which contains our bot's token. 
A token is like a key that allows us to connect to and control the bot.
"""

TOKEN = "6587599801:AAHiSvV9fTZGGHHPv-od8Ohw_G0JdhJF_Kg"
bot = AsyncTeleBot(TOKEN)

url = "https://airmundo.com/en/blog/airport-codes-european-airports/"

data = []
airport_countries = []
icao_message = []
def get_airport():
    """
    The function responsible for obtaining the names and ICAO of European airports.
    """
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
    """
    The function is used to create and return an inline keyboard with the names of European countries.
    The name of the country is passed to each button as callback_data.
    This is necessary in order to get the ICAO codes of the airports when you click on the button.
    :return: airport_keyboard
    """
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
    """
    The function uses the data from the 'data' variable to generate an SMS in the form of a country
    when you click on the corresponding country:
    Airport - ICAO
    :param airport_country: airport_country
    :return: icao_message
    """
    for airports_info in data:
        if airport_country in airports_info[1]:
            icao_message.append(f"*{airports_info[0]}* - `{airports_info[3]}`")
    return icao_message
# function for recieving short info
def get_info(type, icao):
    """
    the function accesses the weather website through the API and, according to the
    transmitted data - 'type' (metar, taf or stationinfo) and 'icao',
    returns a response from thtae website with the relevant data.
    :param type: 'metar', 'taf' or 'stationinfo'
    :param icao: ICAO code
    :return: response from site
    """
    response = requests.get(f"https://aviationweather.gov/api/data/{type}.php?ids={icao.upper()}")
    return response.text

# function for recieving full info
def get_decoded_info(type, icao):
    """
    The function works in a similar way to the previous function: it accesses the weather website via API and,
    according to the transmitted data - 'type' (metar or taf) and 'icao',
    returns the decoded weather data from the website.
    :param type: 'metar', 'taf' or 'stationinfo'
    :param icao: ICAO code
    :return: decoded response from site
    """
    response = requests.get(f"https://aviationweather.gov/api/data/{type}.php?ids={icao.upper()}&format=decoded")
    return response.text

@bot.message_handler(commands=['start'])
async def fn_start(message):
    """
    This is part of the bot launch processing. When the user presses the /start command, the bot automatically creates commands for easy operation.
    :param message: message from user
    """
    await bot.set_my_commands([
        telebot.types.BotCommand("/start", "Запуск"),
        telebot.types.BotCommand("/info", "Допомога"),
        telebot.types.BotCommand("/radar24", "FlightRadar24")
    ])
    await bot.send_message(message.chat.id, "Привіт. Я допоможу тобі отримати дані про METAR та TAF на будь-якому аеродромі світу. "
                                            "Для цього тобі потрібно ввести номер ICAO (неважливо яким регістром). "
                                            "\n\nЯкщо потрібні підказки - сміливо тисни /info☺️")
@bot.message_handler(commands=['info'])
async def fn_info(message):
    data.clear()
    airport_countries.clear()
    airport_keyboard = get_airport_keyboard()
    await bot.send_message(message.chat.id, "Для зручності, було додано дані про аеропорти Европи.",
                           reply_markup=types.InlineKeyboardMarkup(airport_keyboard), parse_mode="Markdown")
    await bot.send_message(message.chat.id, "Дані про інші аеропорти ти можеш знайти за [посиланням](https://telegra.ph/ICAO-aeroportіv-svіtu-09-07-3)",
                           parse_mode="Markdown")

@bot.message_handler(commands=['radar24'])
async def fn_info(message):
    await bot.send_message(message.chat.id, "Посилання на [FlightRadar](https://www.flightradar24.com/)",
                           disable_web_page_preview=True, parse_mode="Markdown")
@bot.message_handler(content_types=['text'])
async def fn_start(message):
    """
    a text message that is not a command is processed in this cleaner. If the length is not equal to 4,
    an error message will be displayed. Otherwise, the process of creating inline buttons and
    displaying the corresponding messages takes place
    :param message: message from user
    """
    if len(message.text) != 4:
        return await bot.send_message(message.chat.id,
                                      "Код аеропорту ІКАО — *чотирилітерний* унікальний індивідуальний ідентифікатор аеропорта",
                                      parse_mode="Markdown")
    icao = message.text.upper()
    info_about_airport = get_info("airport", icao)

    inline_keyboard = [
        [
            types.InlineKeyboardButton("METAR", callback_data=f"Type:metar-{message.text}"),
            types.InlineKeyboardButton("TAF", callback_data=f"Type:taf-{message.text}")
        ]
    ]
    try:
        await bot.send_message(message.chat.id, f"{info_about_airport}", reply_markup=types.InlineKeyboardMarkup(inline_keyboard))
    except:
        await bot.send_message(message.chat.id, "Виникла помилка при завантажені даних. Спробуй /info "
                                                       "чи спробуй пізніше")


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
                                    text="Для зручності, було додано дані про аеропорти Европи. ",
                                    reply_markup=types.InlineKeyboardMarkup(airport_keyboard))

    elif call.data.startswith("back"):
        icao = call.data.split(":")[1]
        info = get_info("airport", icao)
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
