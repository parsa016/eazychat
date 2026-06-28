from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)


def main_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 جستجو"), KeyboardButton(text="❤️ لایک‌های من")],
            [KeyboardButton(text="💑 جفت‌شده‌ها"), KeyboardButton(text="👤 پروفایل من")],
            [KeyboardButton(text="💎 الماس‌ها"), KeyboardButton(text="⭐ اشتراک پرمیوم")],
            [KeyboardButton(text="🎁 کسب درآمد"), KeyboardButton(text="📞 پشتیبانی")]
        ],
        resize_keyboard=True
    )


def phone_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 ارسال شماره موبایل", request_contact=True)]
        ],
        resize_keyboard=True
    )


def gender_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👨 مرد", callback_data="gender_male"),
            InlineKeyboardButton(text="👩 زن", callback_data="gender_female")
        ]
    ])


def search_gender_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👨 مردها", callback_data="sf_gender_male"),
            InlineKeyboardButton(text="👩 زن‌ها", callback_data="sf_gender_female")
        ],
        [InlineKeyboardButton(text="🔄 فرقی نمی‌کنه", callback_data="sf_gender_any")]
    ])


def search_location_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 هم‌استانی", callback_data="sf_loc_province")],
        [InlineKeyboardButton(text="🏙️ هم‌شهری", callback_data="sf_loc_city")],
        [InlineKeyboardButton(text="🔄 فرقی نمی‌کنه", callback_data="sf_loc_any")]
    ])


def search_age_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📈 بزرگ‌تر از من", callback_data="sf_age_older")],
        [InlineKeyboardButton(text="📉 کوچک‌تر از من", callback_data="sf_age_younger")],
        [InlineKeyboardButton(text="🎂 هم‌سن", callback_data="sf_age_same")],
        [InlineKeyboardButton(text="🔄 فرقی نمی‌کنه", callback_data="sf_age_any")]
    ])


def purpose_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💕 دوست‌یابی", callback_data="purpose_dating")],
        [InlineKeyboardButton(text="🎉 سرگرمی", callback_data="purpose_fun")],
        [InlineKeyboardButton(text="💍 همسریابی", callback_data="purpose_marriage")]
    ])


def interests_kb(selected: list = None):
    if selected is None:
        selected = []
    interests = [
        ("☕ قهوه", "coffee"),
        ("🍵 چای", "tea"),
        ("🚬 سیگار", "smoking"),
        ("🍷 مشروب", "alcohol"),
        ("🏋️ ورزش", "sports"),
        ("🎮 گیمینگ", "gaming"),
        ("📚 کتاب‌خوانی", "reading"),
        ("🎵 موسیقی", "music"),
        ("🎬 فیلم و سریال", "movies"),
        ("✈️ سفر", "travel"),
        ("🍳 آشپزی", "cooking"),
        ("📸 عکاسی", "photography"),
    ]
    keyboard = []
    for i in range(0, len(interests), 2):
        row = []
        for j in range(i, min(i + 2, len(interests))):
            text, data = interests[j]
            if data in selected:
                text = "✅ " + text
            row.append(InlineKeyboardButton(text=text, callback_data=f"interest_{data}"))
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton(text="✅ تایید و ادامه", callback_data="interests_done")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def profile_action_kb(target_user_id: int, is_premium: bool = False):
    keyboard = [
        [
            InlineKeyboardButton(text="❤️ لایک", callback_data=f"like_{target_user_id}"),
            InlineKeyboardButton(text="❌ رد", callback_data=f"reject_{target_user_id}")
        ],
        [
            InlineKeyboardButton(text="💎 لایک + دایرکت", callback_data=f"likedirect_{target_user_id}")
        ]
    ]
    if is_premium:
        keyboard.append([InlineKeyboardButton(text="⬅️ بازگشت", callback_data="go_back")])
    else:
        keyboard.append([InlineKeyboardButton(text="🔒 بازگشت (پرمیوم)", callback_data="go_back_locked")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def like_notification_kb(from_user_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="❤️ لایک متقابل", callback_data=f"like_back_{from_user_id}"),
            InlineKeyboardButton(text="❌ رد", callback_data=f"reject_like_{from_user_id}")
        ]
    ])


def verification_admin_kb(user_id: int, verification_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ تأیید", callback_data=f"verify_approve_{verification_id}_{user_id}"),
            InlineKeyboardButton(text="❌ رد", callback_data=f"verify_reject_{verification_id}_{user_id}")
        ]
    ])


def photos_done_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ تمام، ادامه بده", callback_data="photos_done")]
    ])


def my_profile_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ ویرایش اسم", callback_data="edit_name")],
        [InlineKeyboardButton(text="📝 ویرایش بیو", callback_data="edit_bio")],
        [InlineKeyboardButton(text="📸 تغییر عکس‌ها", callback_data="edit_photos")],
        [InlineKeyboardButton(text="🎯 تغییر هدف", callback_data="edit_purpose")],
        [InlineKeyboardButton(text="💡 تغییر علاقه‌مندی‌ها", callback_data="edit_interests")],
    ])


def back_to_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🏠 بازگشت به منو")]],
        resize_keyboard=True
    )


def match_profile_kb(partner_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 درخواست چت (2 💎)", callback_data=f"chat_request_{partner_id}")],
        [InlineKeyboardButton(text="✉️ دایرکت (2 💎)", callback_data=f"match_direct_{partner_id}")],
        [InlineKeyboardButton(text="💔 آن‌مچ", callback_data=f"unmatch_{partner_id}")]
    ])


def chat_request_kb(from_user_id: int, request_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ قبول", callback_data=f"accept_chat_{request_id}_{from_user_id}"),
            InlineKeyboardButton(text="❌ رد", callback_data=f"decline_chat_{request_id}_{from_user_id}")
        ]
    ])


def diamonds_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 دریافت الماس رایگان روزانه", callback_data="daily_diamond")],
        [InlineKeyboardButton(text="🔥 جایزه 3 روز متوالی (10 💎)", callback_data="streak_3")],
        [InlineKeyboardButton(text="🔥 جایزه 7 روز متوالی (30 💎)", callback_data="streak_7")],
        [InlineKeyboardButton(text="🔥 جایزه 30 روز متوالی (70 💎)", callback_data="streak_30")],
    ])
