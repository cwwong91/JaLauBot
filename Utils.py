from telegram import (
    Update
)
from telegram.ext import (
    CallbackContext
)
import datetime
tester = ['126546982']


# Display a popup to warn the user if they are not current creating the event
def wrong_user_alert(update: Update):
    callback_id = update.callback_query.id
    update.callback_query.bot.answer_callback_query(callback_id, "咪搞啦", show_alert=True)


def remove_last_message(chat_id: str, last_messages: {}, context: CallbackContext) -> {}:
    last_message_id = last_messages.pop(chat_id)
    context.bot.delete_message(chat_id=chat_id,
                               message_id=last_message_id)
    return last_messages


def has_right(update: Update) -> bool:
    # return true if is admin/creator, otherwise return false
    chat = update.effective_chat
    member = chat.get_member(update.effective_user.id)
    print(f'{update.effective_user.id}')
    accepted_status = ['administrator', 'creator']
    is_admin = member.status in accepted_status or member.user_id in tester

    return is_admin


# get a time in string format and standardise it into our desire format (HH:mm)
# current accepted time format is HH:mm / HHmm
# return None if the input str cannot be resolved to a time
def resolve_time(time_str: str) -> str:
    rc_format = '%H:%M'
    formats = ['%H:%M', '%H:%M']
    for f in formats:
        try:
            time = datetime.datetime.strptime(time_str, f)
            if time is not None:
                return time.strftime(rc_format)
        except ValueError:
            continue
        break

    # failed to match any of the format
    return None