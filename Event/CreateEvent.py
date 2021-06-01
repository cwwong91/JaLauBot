import re

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

from Event.Event import Event, EventManager
from Member import Member, MemberMananger
import datetime, telegramcalendar, logging
from Utils import (
    resolve_time,
    wrong_user_alert,
    remove_last_message
)

EVENT_TYPING_NAME, EVENT_TYPING_DATE, EVENT_TYPING_LOCATION, EVENT_TYPING_TIME, EVENT_TYPING_LIMIT, EVENT_REVIEW, \
EVENT_TYPING_NICKNAME, EVENT_ADDING_PARTICIPANT = range(8)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
last_message_list = {}
logger = logging.getLogger(__name__)


#   ======================== Create Event Handler ========================
def create_event(update: Update, context: CallbackContext) -> int:
    # Get the creator
    creator = MemberMananger.get_member(update.message.from_user.id, context)
    if creator is None:
        creator = Member(id=update.message.from_user.id, name=update.message.from_user.username, plane=0)
        MemberMananger.set_member(creator, context)
    # Create the pending event and save it to the pending list
    pending_event = Event(creator=creator.id)
    EventManager.set_pending_event(pending_event, context)
    logger.info("Start create event")

    last_message = update.message.reply_text("個聚叫咩名？", quote=True)
    last_message_list[last_message.chat_id] = last_message.message_id
    return EVENT_TYPING_NAME


def set_event_name(update: Update, context: CallbackContext) -> int:
    sender = update.message.from_user.id
    # check if the sender is currently creating an event
    pending_event = EventManager.get_pending_event(sender, context)
    if pending_event is None:
        return EVENT_TYPING_NAME

    # Update the name and save it
    remove_last_message(update.message.chat_id,last_message_list,context)

    name = update.message.text
    pending_event.name = name
    EventManager.set_pending_event(pending_event, context)

    last_message = update.message.reply_text(f"{pending_event.get_printable()}\n日期？", quote=True,
                                             reply_markup=telegramcalendar.create_calendar())
    last_message_list[last_message.chat_id] = last_message.message_id

    return EVENT_TYPING_DATE


def set_event_date(update: Update, context: CallbackContext) -> int:
    sender = update.callback_query.from_user.id
    # check if the sender is currently creating an event
    pending_event = EventManager.get_pending_event(sender, context)
    if pending_event is None:
        # Not current creator, prompt a warning and ignore input
        wrong_user_alert(update)
        return EVENT_TYPING_DATE

    selected, date = telegramcalendar.process_calendar_selection(bot=context.bot, update=update)
    pending_event.set_date(date)
    EventManager.set_pending_event(pending_event, context)

    if selected:
        chat_id = update.callback_query.message.chat_id
        remove_last_message(chat_id, last_message_list, context)

        last_message = context.bot.send_message(chat_id=chat_id,
                                                text=f"{pending_event.get_printable()}\n地點？",
                                                reply_markup=ReplyKeyboardRemove())
        last_message_list[chat_id] = last_message.message_id

        return EVENT_TYPING_LOCATION

    return EVENT_TYPING_DATE


def set_event_location(update: Update, context: CallbackContext) -> int:
    sender = update.message.from_user.id
    # check if the sender is currently creating an event
    pending_event = EventManager.get_pending_event(sender, context)
    if pending_event is None:
        return EVENT_TYPING_LOCATION

    remove_last_message(update.message.chat_id, last_message_list, context)

    text = update.message.text
    pending_event.location = text
    EventManager.set_pending_event(pending_event, context)

    last_message = update.message.reply_text(f"{pending_event.get_printable()}\n時間？(e.g. 17:00) 無可以打skip")
    last_message_list[last_message.chat_id] = last_message.message_id

    return EVENT_TYPING_TIME


def set_event_time(update: Update, context: CallbackContext) -> int:
    sender = update.message.from_user.id
    # check if the sender is currently creating an event
    pending_event = EventManager.get_pending_event(sender, context)
    if pending_event is None:
        return EVENT_TYPING_TIME

    time_str = update.message.text
    logging.info(time_str.find("skip"))
    if time_str.find("skip") >= 0:
        remove_last_message(update.message.chat_id, last_message_list, context)

        pending_event.time = None
        EventManager.set_pending_event(pending_event, context)

        last_message = update.message.reply_text("限人數？ 無可以打0")
        last_message_list[last_message.chat_id] = last_message.message_id

        return EVENT_TYPING_LIMIT

    resolved_time = resolve_time(time_str)
    if resolved_time is not None:

        remove_last_message(update.message.chat_id, last_message_list, context)

        pending_event.time = resolved_time
        EventManager.set_pending_event(pending_event, context)

        last_message = update.message.reply_text("限人數？ 無可以打0")
        last_message_list[last_message.chat_id] = last_message.message_id

        return EVENT_TYPING_LIMIT

    else:
        # time format not match, input again
        update.message.reply_text("要跟FORMAT\n時間？(e.g. 17:00, 1700) 無可以打skip", quote=True)
        return EVENT_TYPING_TIME


confirm_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("OK 開聚", callback_data="true"), InlineKeyboardButton("算啦不了", callback_data="false")],
    [InlineKeyboardButton("落埋名", callback_data="join_event"),
     InlineKeyboardButton("幫人落名", callback_data="add_participant")]
])


def set_event_limit(update: Update, context: CallbackContext) -> int:
    sender = update.message.from_user.id
    # check if the sender is currently creating an event
    pending_event = EventManager.get_pending_event(sender, context)
    if pending_event is None:
        return EVENT_TYPING_LIMIT

    limit = update.message.text

    if limit.isnumeric():
        remove_last_message(update.message.chat_id, last_message_list, context)

        pending_event.limit = int(limit)
        EventManager.set_pending_event(pending_event, context)

        last_message = update.message.reply_text(f"Confirm 開聚？\n{pending_event.get_printable()}",
                                  reply_markup=confirm_keyboard)
        last_message_list[last_message.chat_id] = last_message.message_id

        return EVENT_REVIEW
    else:
        update.message.reply_text("打數字呀ON9")
        return EVENT_TYPING_LIMIT


def confirm_review(update: Update, context: CallbackContext) -> int:
    sender = update.callback_query.from_user.id
    # check if the sender is currently creating an event
    pending_event = EventManager.get_pending_event(sender, context)
    if pending_event is None:
        # Not current creator, prompt a warning and ignore input
        wrong_user_alert(update)
        return EVENT_TYPING_DATE

    query = update.callback_query
    data = query.data

    remove_last_message(query.message.chat_id, last_message_list, context)

    if data == "true":
        EventManager.save_event(pending_event, context)
        context.bot.send_message(chat_id=update.callback_query.message.chat.id,
                                 text="聚已開")
        return ConversationHandler.END

    elif data == "false":
        context.bot.send_message(chat_id=update.callback_query.message.chat.id,
                                 text="取消左 想開就重新開過啦")

        return ConversationHandler.END

    elif data == "join_event":
        last_message = context.bot.send_message(chat_id=query.message.chat_id,
                                 text="落咩名？")
        last_message_list[last_message.chat_id] = last_message.message_id

        return EVENT_TYPING_NICKNAME
    elif data == "add_participant":
        last_message = context.bot.send_message(chat_id=query.message.chat_id,
                                 text="落咩名? （tag 埋佢）")
        last_message_list[last_message.chat_id] = last_message.message_id

        return EVENT_ADDING_PARTICIPANT


def set_nickname(update: Update, context: CallbackContext) -> int:
    sender = update.message.from_user.id
    # check if the sender is currently creating an event
    pending_event = EventManager.get_pending_event(sender, context)
    if pending_event is None:
        return EVENT_TYPING_NICKNAME

    remove_last_message(update.message.chat_id, last_message_list, context)

    name = update.message.text
    member = MemberMananger.get_member(sender, context)
    member.nickname = name
    pending_event.add_participant(member)
    EventManager.set_pending_event(pending_event, context)
    last_message = update.message.reply_text(f"Confirm 開聚？\n{pending_event.get_printable()}",
                              reply_markup=confirm_keyboard)
    last_message_list[last_message.chat_id] = last_message.message_id

    return EVENT_REVIEW


def add_participants(update: Update, context: CallbackContext) -> int:
    sender = update.message.from_user.id
    # check if the sender is currently creating an event
    pending_event = EventManager.get_pending_event(sender, context)
    if pending_event is None:
        return EVENT_ADDING_PARTICIPANT

    message = update.message.text
    member = Member(nickname=message)

    remove_last_message(update.message.chat_id, last_message_list, context)

    pending_event.add_participant(member)
    EventManager.set_pending_event(pending_event, context)
    last_message = update.message.reply_text(f"Confirm 開聚？\n{pending_event.get_printable()}",
                              reply_markup=confirm_keyboard)
    last_message_list[last_message.chat_id] = last_message.message_id

    return EVENT_REVIEW


