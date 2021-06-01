import logging

from telegram.ext import CallbackContext
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from Member import Member
import datetime
EVENT_ID_KEY, EVENT_NAME_KEY, EVENT_DATE_KEY, EVENT_LOCATION_KEY, EVENT_TIME_KEY, EVENT_LIMIT_KEY, EVENT_PARTICIPANT_KEY, EVENT_CREATOR_KEY = "id", "name", "date", "location", "time", "limit", "participant", "creator"
from Utils import *

class Event(object):
    def __init__(self, **kwargs):
        self.id = 0 if kwargs.get(EVENT_ID_KEY) is None else kwargs.get(EVENT_ID_KEY)
        self.name = kwargs.get(EVENT_NAME_KEY)
        self.date = kwargs.get(EVENT_DATE_KEY)
        self.location = kwargs.get(EVENT_LOCATION_KEY)
        self.time = kwargs.get(EVENT_TIME_KEY)
        self.limit = 0 if kwargs.get(EVENT_LIMIT_KEY) is None else kwargs.get(EVENT_LIMIT_KEY)
        self.participant = [] if kwargs.get(EVENT_PARTICIPANT_KEY) is None else kwargs.get(EVENT_PARTICIPANT_KEY)
        self.creator_id = "" if kwargs.get(EVENT_CREATOR_KEY) is None else kwargs.get(EVENT_CREATOR_KEY)

    def get_name(self) -> str:
        return self.name or ""

    def get_date_str(self) -> str:
        return self.date or ""

    def get_date(self) -> datetime:
        if self.date is None:
            return None
        rc = datetime.datetime.strptime(self.date, '%d/%m/%y %a')

        return rc

    def set_date(self, date: datetime):
        date_string = date.strftime("%d/%m/%y %a")
        self.date = date_string

    def get_time_str(self) -> str:
        return self.time or ""

    # get the complete datetime by combining the date and time str
    # if time is not set, will default to 23:59 (for sorting purpose)
    def get_date_time(self) -> datetime:
        date = self.get_date_str()
        time = self.get_time_str()

        if not time:
            time = "23:59"

        datetime_str = date + " " + time
        datetime_format = "%d/%m/%y %a %H:%M"

        return datetime.datetime.strptime(datetime_str, datetime_format)

    def get_location(self) -> str:
        return self.location or ""

    def add_participant(self, member: Member):
        for m in self.participant:
            if m == member:
                m.nickname = member.nickname
                return
        self.participant.append(member)

    def get_printable(self) -> str:
        rc = f"{self.get_date_str()} {self.get_time_str()} {self.get_name()} {self.get_location()}"
        count: int = max(self.limit, len(self.participant), 4)

        for i in range(count):
            if len(self.participant) > i:
                p = self.participant[i]
                name = p.nickname if p.nickname else p.name
            else:
                name = ""
            rc += f"\n {i+1}. {name}"
        if self.limit > 0:
            rc += f"\n{self.limit}人full"
        return rc

    def sort_by_time(event):
        return event.get_date_time()

    def clear(self):
        self.name = None
        self.date = None
        self.time = None
        self.location = None
        self.limit = 0
        self.participant = []


class EventManager:
    PENDING_EVENTS_KEY = "pending_events"
    @classmethod
    def get_pending_events(cls, context: CallbackContext) -> {str:Event}:
        if EventManager.PENDING_EVENTS_KEY in context.chat_data.keys():
            return context.chat_data[EventManager.PENDING_EVENTS_KEY]
        else:
            return None

    @classmethod
    def set_pending_event(cls, event: Event, context: CallbackContext):
        pending_event = EventManager.get_pending_events(context)
        if pending_event is None:
            pending_event = {event.creator_id: event}
        else:
            pending_event[event.creator_id] = event
        context.chat_data[EventManager.PENDING_EVENTS_KEY] = pending_event

    @classmethod
    def get_pending_event(cls, id: str, context: CallbackContext)->Event:
        pending_event = EventManager.get_pending_events(context)
        if pending_event is None:
            return None
        elif id in pending_event.keys():
            return pending_event[id]
        else:
            return None

    @classmethod
    def get_editable_event(cls, update: Update, context: CallbackContext) -> {int:Event}:
        if has_right(update):
            return EventManager.get_events(context)

        events = EventManager.get_events(context)
        editableEvent = {}
        for key in events.keys():
            event = events[key]
            if event.creator_id == update.effective_user.id:
                editableEvent[key] = event

        return editableEvent

    @classmethod
    def remove_pending_event(cls, context: CallbackContext):
        context.chat_data.pop(EventManager.PENDING_EVENTS_KEY)

    @classmethod
    def get_events(cls, context: CallbackContext) -> {int: Event}:
        events_key = "events"
        if events_key in context.chat_data.keys():
            return context.chat_data[events_key]
        else:
            events = {}
            context.chat_data[events_key] = events
            return events

    @classmethod
    def get_event(cls, id: int, context: CallbackContext) -> Event:
        events = EventManager.get_events(context)
        if id in events.keys():
            return events[id]

    # Return the latest event id to be used for next new event
    @classmethod
    def get_event_id(cls, context: CallbackContext) -> int:
        event_id_key = "event_id"
        if event_id_key in context.chat_data.keys():
            event_id = context.chat_data[event_id_key] + 1
            context.chat_data[event_id_key] = event_id
            return event_id
        else:
            context.chat_data[event_id_key] = 1
            return 1

    @classmethod
    def save_event(cls, event: Event, context: CallbackContext):

        # Assign an event id if it's a new event
        if event.id == 0:
            event_id = EventManager.get_event_id(context)
            event.id = event_id

        events = EventManager.get_events(context=context)
        events[event.id] = event


    @classmethod
    def print_events(cls, context: CallbackContext) -> str:
        rc = ""
        sorted_events = sorted(EventManager.get_events(context).values(), key=Event.sort_by_time)
        for event in sorted_events:
            rc = rc + "\n------------------------------------\n" + event.get_printable()

        rc = rc + "\n------------------------------------"
        return rc

    @classmethod
    def create_events_selector(cls, context: CallbackContext) -> InlineKeyboardMarkup:
        sorted_events = sorted(EventManager.get_events(context).values(), key=Event.sort_by_time)
        buttons = []
        for event in sorted_events:
            button = InlineKeyboardButton(event.name, callback_data=event.id)
            buttons.append([button])

        buttons.append([InlineKeyboardButton("Cancel", callback_data="cancel")])
        return InlineKeyboardMarkup(buttons)

    @classmethod
    def create_event_selector(cls, events: {int: Event}) -> InlineKeyboardMarkup:
        sorted_events = sorted(events.values(), key=Event.sort_by_time)
        buttons = []
        for event in sorted_events:
            button = InlineKeyboardButton(event.name, callback_data=event.id)
            buttons.append([button])

        buttons.append([InlineKeyboardButton("Cancel", callback_data="cancel")])
        return InlineKeyboardMarkup(buttons)