from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
    InlineKeyboardMarkup, InlineKeyboardButton
)


def main_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 جستجو"), KeyboardButton(text="👤 پروفایل من")],
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
        resize_keyboard=True,
        one_time_keyboard=True
    )


def remove_kb():
    return ReplyKeyboardRemove()


def province_kb(provinces: list):
    keyboard = []
    for i in range(0, len(provinces), 2):
        row = []
        for j in range(i, min(i + 2, len(provinces))):
            row.append(KeyboardButton(text=provinces[j]))
        keyboard.append(row)
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def city_kb(cities: list):
    keyboard = []
    for i in range(0, len(cities), 3):
        row = []
        for j in range(i, min(i + 3, len(cities))):
            row.append(KeyboardButton(text=cities[j]))
        keyboard.append(row)
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


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
            InlineKeyboardButton(text="💌 لایک و دایرکت", callback_data=f"likedirect_{target_user_id}"),
            InlineKeyboardButton(text="👎 دیسلایک", callback_data=f"reject_{target_user_id}")
        ],
        [
            InlineKeyboardButton(text="🔙 بازگشت", callback_data="go_back" if is_premium else "go_back_locked"),
            InlineKeyboardButton(text="خروج", callback_data="exit_explore"),
            InlineKeyboardButton(text="⚙️ بیشتر", callback_data=f"explore_more_{target_user_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def explore_more_kb(target_user_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🚫 بلاک", callback_data=f"block_user_{target_user_id}"),
            InlineKeyboardButton(text="⚠️ گزارش", callback_data=f"report_user_{target_user_id}")
        ],
        [InlineKeyboardButton(text="🔙 بازگشت به اکسپلور", callback_data="back_to_explore")]
    ])


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


def verification_optional_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎥 ارسال ویدیو احراز هویت", callback_data="start_verification")],
        [InlineKeyboardButton(text="⏭️ فعلاً انجام نمیدم", callback_data="skip_verification")]
    ])


def photos_done_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✅ تمام، ادامه بده")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def my_profile_kb(is_verified: bool = False):
    keyboard = [
        [
            InlineKeyboardButton(text="✏️ ویرایش پروفایل", callback_data="edit_profile"),
            InlineKeyboardButton(text="📋 تکمیل پروفایل", callback_data="complete_profile")
        ],
        [
            InlineKeyboardButton(text="💬 تعاملات", callback_data="interactions"),
            InlineKeyboardButton(text="📊 آمار", callback_data="my_stats")
        ],
    ]
    if not is_verified:
        keyboard.append([InlineKeyboardButton(text="🎥 احراز هویت", callback_data="start_verification")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def edit_profile_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="تغییر نام", callback_data="edit_name"),
            InlineKeyboardButton(text="تغییر سن", callback_data="edit_age")
        ],
        [
            InlineKeyboardButton(text="تغییر لوکیشن", callback_data="edit_location"),
            InlineKeyboardButton(text="تغییر هدف", callback_data="edit_purpose")
        ],
        [
            InlineKeyboardButton(text="ایموجی‌ها", callback_data="edit_interests"),
            InlineKeyboardButton(text="تصاویر پروفایل", callback_data="edit_photos")
        ],
        [InlineKeyboardButton(text="✏️ ویرایش بیو", callback_data="edit_bio")],
        [InlineKeyboardButton(text="🔙 بازگشت به پروفایل", callback_data="back_profile")]
    ])


def complete_profile_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📐 قد", callback_data="cp_height")],
        [InlineKeyboardButton(text="👁️ رنگ چشم", callback_data="cp_eye_color")],
        [InlineKeyboardButton(text="🏋️ ورزش", callback_data="cp_exercise")],
        [InlineKeyboardButton(text="💕 وضعیت رابطه", callback_data="cp_relationship")],
        [InlineKeyboardButton(text="💼 زمینه شغلی", callback_data="cp_job")],
        [InlineKeyboardButton(text="⭐ ماه تولد", callback_data="cp_zodiac")],
        [InlineKeyboardButton(text="🧠 شخصیت", callback_data="cp_personality")],
        [InlineKeyboardButton(text="🎨 رنگ پوست", callback_data="cp_skin_color")],
        [InlineKeyboardButton(text="🎓 تحصیلات", callback_data="cp_education")],
        [InlineKeyboardButton(text="🔙 بازگشت به پروفایل", callback_data="back_profile")]
    ])


def interactions_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Likers ❤️", callback_data="view_likers"),
            InlineKeyboardButton(text="Matches 💕", callback_data="view_matches_list")
        ],
        [
            InlineKeyboardButton(text="💌 لایک‌های ارسالی", callback_data="view_sent_likes"),
            InlineKeyboardButton(text="🚫 بلاک‌شده‌ها", callback_data="view_blocked")
        ],
        [InlineKeyboardButton(text="🗑️ پاک کردن دیسلایک‌ها", callback_data="clear_dislikes")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_profile")]
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
        [InlineKeyboardButton(text="🌙 دریافت الماس روزانه", callback_data="daily_diamond")],
        [InlineKeyboardButton(text="🎁 وظایف الماسی", callback_data="diamond_tasks")],
        [
            InlineKeyboardButton(text="📜 تاریخچه تراکنش‌ها", callback_data="transaction_history"),
            InlineKeyboardButton(text="🛒 خرید الماس", callback_data="buy_diamonds")
        ],
        [InlineKeyboardButton(text="👥 معرفی دوستان", callback_data="referral_link")],
        [InlineKeyboardButton(text="💎 الماس رایگان", callback_data="free_diamond_info")]
    ])


def diamond_tasks_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 جوین کانال رسمی (3 💎)", callback_data="task_join_channel")],
        [InlineKeyboardButton(text="💬 کامنت زیر آخرین پست (4 💎)", callback_data="task_comment")],
        [InlineKeyboardButton(text="👍 ری‌اکشن به 5 پست اخیر (2 💎)", callback_data="task_react")],
        [InlineKeyboardButton(text="📣 جوین کانال اسپانسر (6 💎)", callback_data="task_sponsor")],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_diamonds")]
    ])


def admin_group_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 آمار", callback_data="admin_stats")],
        [InlineKeyboardButton(text="⏳ احرازهای منتظر", callback_data="admin_pending")],
        [InlineKeyboardButton(text="📢 پیام همگانی", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="🔍 جستجوی کاربر", callback_data="admin_search_user")],
    ])
