from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    phone = State()
    name = State()
    gender = State()
    age = State()
    province = State()
    city = State()
    photos = State()
    verification_video = State()
    purpose = State()
    interests = State()


class Search(StatesGroup):
    browsing = State()
    select_gender = State()


class Chat(StatesGroup):
    chatting = State()
    direct_message = State()


class Admin(StatesGroup):
    reviewing = State()
