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
    bio = State()


class Search(StatesGroup):
    select_gender = State()
    browsing = State()
    direct_with_like = State()


class Chat(StatesGroup):
    chatting = State()
    direct_message = State()
    match_direct = State()


class Admin(StatesGroup):
    reviewing = State()
    rejection_reason = State()


class Support(StatesGroup):
    waiting_message = State()


class Profile(StatesGroup):
    editing_name = State()
    editing_bio = State()
    editing_age = State()
    editing_height = State()
    editing_eye_color = State()
    editing_exercise = State()
    editing_relationship = State()
    editing_job = State()
    editing_zodiac = State()
    editing_personality = State()
    editing_skin_color = State()
    editing_education = State()
    editing_location = State()
    editing_location_city = State()


class Report(StatesGroup):
    waiting_reason = State()
