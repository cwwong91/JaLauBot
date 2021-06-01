#!/usr/bin/python3

import logging

from telegram.ext import Updater
from telegram.ext import  CallbackQueryHandler
from telegram.ext import  CommandHandler
from telegram import  ReplyKeyboardRemove
from telegram.ext import CallbackContext
from telegram import Update


import telegramcalendar


TOKEN = "1871810746:AAHDHM1pAPv1_MExYyxy_udqDNm3cAcv-fI"


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

def calendar_handler(bot,update):

    bot.message.reply_text("Please select a date: ",
                        reply_markup=telegramcalendar.create_calendar())


def inline_handler(update: Update, context:CallbackContext):
    selected,date = telegramcalendar.process_calendar_selection(context.bot, update)
    if selected:
        context.bot.send_message(chat_id=update.callback_query.from_user.id,
                        text="You selected %s" % (date.strftime("%d/%m/%Y")),
                        reply_markup=ReplyKeyboardRemove())


if TOKEN == "":
    print("Please write TOKEN into file")
else:
    up = Updater("1871810746:AAHDHM1pAPv1_MExYyxy_udqDNm3cAcv-fI")

    up.dispatcher.add_handler(CommandHandler("calendar",calendar_handler))
    up.dispatcher.add_handler(CallbackQueryHandler(inline_handler))

    up.start_polling()
    up.idle()
