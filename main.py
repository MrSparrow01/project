import requests
import asyncio

from telebot import types
from telebot.async_telebot import AsyncTeleBot

token = "6587599801:AAHiSvV9fTZGGHHPv-od8Ohw_G0JdhJF_Kg"
bot = AsyncTeleBot(token)

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

@bot.message_handler(content_types=['text'])
async def fn_start(message):
    if len(message.text) != 4:
        return
    icao = message.text.upper()
    info_about_airport = get_info("stationinfo", icao)
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

asyncio.run(bot.infinity_polling(skip_pending=True))
