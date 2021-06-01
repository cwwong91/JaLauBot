import logging

from telegram import (
    ReplyKeyboardMarkup,
    Update,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message
)
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    PicklePersistence,
    CallbackContext,
    CallbackQueryHandler
)
from Utils import *

from Event.Event import EventManager


SELECT_REMOVE_EVENT, CONFIRM_REMOVE_EVENT = range(2)


def remove_event(update: Update, context: CallbackContext) -> int:

    editable_events = EventManager.get_editable_event(update, context)
    # show the selection keyboard if the editable list is > 0
    if len(editable_events.keys()) > 0:
        update.message.reply_text("你想delete 邊個聚？", quote=True,
                                  reply_markup=EventManager.create_event_selector(events=editable_events))
    else:
        return ConversationHandler.END

    return SELECT_REMOVE_EVENT


confirm_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("Remove Event", callback_data="true"), InlineKeyboardButton("Cancel", callback_data="false")]
])


def confirm_remove_event(update: Update, context: CallbackContext) -> int:
    data = update.callback_query.data
    if data == "Cancel":
        return ConversationHandler.END
    else:
        event = EventManager.get_event(int(data), context)
        if event is not None:
            context.bot.send_message(chat_id=update.callback_query.message.chat_id,
                                     text="Remove Event? \n" + event.get_printable(),
                                     reply_markup=confirm_keyboard)
        logging.info(data)

    return CONFIRM_REMOVE_EVENT


def handle_confirm_action(update: Update, context: CallbackContext) -> int:

    data = update.callback_query.data

    if data == "true":
        EventManager
    logging.info(data)
    return ConversationHandler.END
