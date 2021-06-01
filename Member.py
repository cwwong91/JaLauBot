from telegram.ext import CallbackContext

MEMBER_ID_KEY, MEMBER_NAME_KEY, MEMBER_PLANE_KEY, MEMBER_NICKNAME_KEY \
    = "id", "name", "plane", "nickname"


class Member(object):
    def __init__(self, **kwargs):
        self.id = kwargs.get(MEMBER_ID_KEY)
        self.name = kwargs.get(MEMBER_NAME_KEY)
        self.plane_count = 0 if kwargs.get(MEMBER_PLANE_KEY) is None else kwargs.get(MEMBER_PLANE_KEY)
        self.nickname = kwargs.get(MEMBER_NICKNAME_KEY)

    def __eq__(self, obj):
        return self.id == obj.id or self.name == obj.name

class MemberMananger:
    @classmethod
    def get_members(cls, context: CallbackContext):
        if "members" in context.chat_data.keys():
            list = context.chat_data["members"]
        else:
            list = {}
            context.chat_data["members"] = list

        return list

    @classmethod
    def set_members(cls, memberList, context: CallbackContext):
        context.chat_data["members"] = memberList

    @classmethod
    def set_member(cls, member: Member, context: CallbackContext):
        list = MemberMananger.get_members(context)
        list[member.id] = member

        MemberMananger.set_members(list, context)

    @classmethod
    def get_member(cls, id: str, context: CallbackContext)->Member:
        list = MemberMananger.get_members(context)
        if id in list.keys():
            member = list[id]
            return member
        else:
            return None

    @classmethod
    def find_member_with_username(cls, username: str, context: CallbackContext) -> Member:
        members = MemberMananger.get_members(context)
        for member in members:
            if member.name == username:
                return member

