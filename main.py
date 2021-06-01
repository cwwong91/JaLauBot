#!/usr/bin/env python
# pylint: disable=C0116
# This program is dedicated to the public domain under the CC0 license.

"""
First, a few callback functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

from Event.CreateEvent import *
from Event.RemoveEvent import *
from Event.Event import EventManager
import datetime, logging


# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

def start(update:Update, context: CallbackContext) -> None:
    update.message.reply_text("Welcome to 渣流BOT")


def get_name(update: Update, context: CallbackContext) -> None:
    # Get the name in this chat. If not found, return the username
    if 'name' in context.user_data.keys():
        update.message.reply_text(context.user_data['name'])
    else:
        update.message.reply_text(update.effective_user.username)


def set_name(update: Update, context: CallbackContext) -> None:
    name = ' '.join(context.args)
    context.user_data['name'] = name
    update.message.reply_text(f"Your name in this chat has been updated to {name}")


def print_events(update: Update, context: CallbackContext):
    message = update.message.reply_text(EventManager.print_events(context), quote=True, reply_markup=EventManager.create_events_selector(context))
    message.pin()


def timeout(update: Update, context: CallbackContext) -> int:
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="time out")
    return ConversationHandler.END


def done(update: Update, context: CallbackContext) -> int:
    logging.info("Done, cancel create event")
    return ConversationHandler.END


def main() -> None:
    # Create the Updater and pass it your bot's token.
    persistence = PicklePersistence(filename='DataStore')
    updater = Updater("YOUR_BOT_ID", persistence=persistence)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    create_event_handler = ConversationHandler(
        entry_points=[CommandHandler("create_event", create_event)],
        states={
            EVENT_TYPING_NAME: [
                MessageHandler(Filters.text & ~(Filters.command | Filters.regex('^Done$')), set_event_name)
            ],
            EVENT_TYPING_DATE: [
                CallbackQueryHandler(set_event_date),
            ],
            EVENT_TYPING_LOCATION: [
                MessageHandler(Filters.text & ~(Filters.command | Filters.regex('^Done$')), set_event_location)
            ],
            EVENT_TYPING_TIME: [
                MessageHandler(Filters.text & ~(Filters.command | Filters.regex('^Done$')), set_event_time)
            ],
            EVENT_TYPING_LIMIT: [
                MessageHandler(Filters.text & ~(Filters.command | Filters.regex('^Done$')), set_event_limit)
            ],
            EVENT_REVIEW: [
                CallbackQueryHandler(confirm_review)
            ],
            EVENT_TYPING_NICKNAME: [
                MessageHandler(Filters.text & ~(Filters.command | Filters.regex('^Done$')), set_nickname)
            ],
            EVENT_ADDING_PARTICIPANT: [
                MessageHandler(Filters.text & ~(Filters.command | Filters.regex('^Done$')), add_participants)

            ],
            ConversationHandler.TIMEOUT: [
                MessageHandler(Filters.text | Filters.command, timeout)
            ]
        },
        fallbacks=[MessageHandler(Filters.regex('^Done$'), done)],
        name="create_event",
        persistent=True,
        conversation_timeout=10
    )
    dispatcher.add_handler(create_event_handler)

    remove_event_handler = ConversationHandler(
        entry_points=[CommandHandler("remove_event", remove_event)],
        states={
            SELECT_REMOVE_EVENT: [
                CallbackQueryHandler(confirm_remove_event)
            ],
            CONFIRM_REMOVE_EVENT:[
                CallbackQueryHandler(handle_confirm_action)
            ]
        },
        fallbacks=[MessageHandler(Filters.regex('^Done$'), done)],
        name="remove_event",
        persistent=True,
        conversation_timeout=10
    )
    dispatcher.add_handler(remove_event_handler)

    set_name_handler = CommandHandler('set_name', set_name)
    dispatcher.add_handler(set_name_handler)

    get_name_handler = CommandHandler('get_name', get_name)
    dispatcher.add_handler(get_name_handler)

    print_event_handler = CommandHandler('events', print_events)
    dispatcher.add_handler(print_event_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()