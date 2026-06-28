from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.database import db
from bot.states.registration import Search
from bot.keyboards.main_kb import (
    search_gender_kb, search_location_kb, search_age_kb,
    profile_action_kb, main_menu_kb, like_notification_kb
)
from config import DAILY_VIEW_LIMIT, DAILY_LIKE_LIMIT, LIKE_WITH_DIRECT_COST

router = Router()


@router.message(F.text == "🔍 جستجو")
async def search_start(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ ابتدا ثبت‌نام کن! /start")
        return
    if user['registration_step'] != 'completed':
        await message.answer("❌ ابتدا باید پروفایلت رو تکمیل کنی.")
        return

    await state.set_state(Search.select_gender)
    await message.answer(
        "🔍 جنسیت مورد نظرت رو انتخاب کن:",
        reply_markup=search_gender_kb()
    )


# ============ SEARCH FILTERS ============

@router.callback_query(F.data.startswith("sf_gender_"))
async def filter_gender(callback: CallbackQuery, state: FSMContext):
    choice = callback.data.replace("sf_gender_", "")
    gender = None if choice == "any" else choice
    await state.update_data(search_gender=gender)
    await callback.message.edit_text(
        "📍 موقعیت مکانی رو انتخاب کن:",
        reply_markup=search_location_kb()
    )


@router.callback_query(F.data.startswith("sf_loc_"))
async def filter_location(callback: CallbackQuery, state: FSMContext):
    choice = callback.data.replace("sf_loc_", "")
    await state.update_data(search_location=choice)
    await callback.message.edit_text(
        "🎂 ترجیح سنی رو انتخاب کن:",
        reply_markup=search_age_kb()
    )


@router.callback_query(F.data.startswith("sf_age_"))
async def filter_age(callback: CallbackQuery, state: FSMContext):
    choice = callback.data.replace("sf_age_", "")
    await state.update_data(search_age=choice)
    await callback.message.edit_text("🔍 در حال جستجو...")
    await state.set_state(Search.browsing)
    await show_next_profile(callback.message, state, callback.from_user.id)


# ============ SHOW PROFILE ============

async def show_next_profile(message: Message, state: FSMContext, user_id: int):
    user = await db.get_user(user_id)
    usage = await db.get_daily_usage(user_id)

    # Check daily limit
    if not user['is_premium'] and usage['views_count'] >= DAILY_VIEW_LIMIT:
        await message.answer(
            f"❌ محدودیت روزانه!\n\n"
            f"امروز {DAILY_VIEW_LIMIT} پروفایل دیدی.\n"
            f"فردا دوباره می‌تونی جستجو کنی.\n\n"
            f"⭐ یا اشتراک پرمیوم بخر و نامحدود جستجو کن!",
            reply_markup=main_menu_kb()
        )
        await state.clear()
        return

    data = await state.get_data()
    search_gender = data.get('search_gender')
    search_location = data.get('search_location', 'any')
    search_age = data.get('search_age', 'any')

    # Build age filter
    min_age, max_age = None, None
    if search_age == 'older':
        min_age = user['age']
        max_age = user['age'] + 10
    elif search_age == 'younger':
        min_age = max(18, user['age'] - 10)
        max_age = user['age']
    elif search_age == 'same':
        min_age = user['age'] - 2
        max_age = user['age'] + 2
    # 'any' = no age filter

    # Build location filter
    province = None
    city = None
    if search_location == 'province':
        province = user['province']
    elif search_location == 'city':
        province = user['province']
        city = user['city']

    profiles = await db.get_profiles_for_user(
        user_id, gender=search_gender,
        min_age=min_age, max_age=max_age,
        province=province, city=city, limit=1
    )

    if not profiles:
        await message.answer(
            "😔 فعلاً پروفایلی با این فیلترها پیدا نشد.\n"
            "بعداً دوباره تلاش کن!",
            reply_markup=main_menu_kb()
        )
        await state.clear()
        return

    profile = profiles[0]
    await db.increment_views(user_id)
    await db.increment_views_received(profile['id'])
    await db.add_search_history(user_id, profile['id'])
    await state.update_data(current_profile_id=profile['id'])
    await send_profile_card(message, profile, user['is_premium'])


async def send_profile_card(message: Message, profile: dict, is_premium: bool = False):
    photos = await db.get_photos(profile['id'])

    gender_emoji = "👨" if profile['gender'] == 'male' else "👩"
    purpose_map = {'dating': '👫 دوست‌یابی', 'fun': '🎉 گپ و گفتگو', 'marriage': '💍 همسریابی'}

    verified_badge = " ✅" if profile.get('is_verified') else ""
    text = f"{gender_emoji} {profile['name']} ({profile['age']}){verified_badge} | Fa\n"
    text += f"📍 {profile['province']}، {profile['city']}\n\n"

    # Info line like reference
    info_parts = []
    if profile.get('purpose'):
        info_parts.append(purpose_map.get(profile['purpose'], ''))
    if profile.get('height'):
        info_parts.append(f"📐 {profile['height']}")
    if profile.get('eye_color'):
        info_parts.append(f"👁️ {profile['eye_color']}")
    if profile.get('skin_color'):
        info_parts.append(f"🎨 {profile['skin_color']}")
    if profile.get('education'):
        info_parts.append(f"🎓 {profile['education']}")
    if profile.get('job'):
        info_parts.append(f"💼 {profile['job']}")
    if profile.get('relationship_status'):
        info_parts.append(f"💕 {profile['relationship_status']}")
    if profile.get('personality'):
        info_parts.append(f"🧠 {profile['personality']}")
    if profile.get('exercise'):
        info_parts.append(f"🏋️ {profile['exercise']}")
    if profile.get('zodiac'):
        info_parts.append(f"⭐ {profile['zodiac']}")
    if info_parts:
        text += " | ".join(info_parts) + "\n"

    if profile.get('bio'):
        text += f"\n📝 {profile['bio']}\n"

    if photos:
        await message.answer_photo(
            photos[0]['file_id'],
            caption=text,
            reply_markup=profile_action_kb(profile['id'], is_premium)
        )
    else:
        await message.answer(text, reply_markup=profile_action_kb(profile['id'], is_premium))


# ============ LIKE ============

@router.callback_query(F.data.startswith("like_") & ~F.data.startswith("like_back_") & ~F.data.startswith("likedirect_"))
async def process_like(callback: CallbackQuery, state: FSMContext):
    target_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    user = await db.get_user(user_id)
    usage = await db.get_daily_usage(user_id)

    if not user['is_premium'] and usage['likes_count'] >= DAILY_LIKE_LIMIT:
        await callback.answer(
            f"❌ محدودیت لایک روزانه! ({DAILY_LIKE_LIMIT} لایک)\nفردا ریست میشه یا پرمیوم بخر.",
            show_alert=True
        )
        return

    await db.add_like(user_id, target_id)
    await db.increment_likes(user_id)

    # Check if mutual like (match)
    mutual = await db.check_like(target_id, user_id)
    if mutual:
        await db.create_match(user_id, target_id)
        try:
            await callback.message.edit_caption(
                caption="💑 جفت شدید! هر دو همدیگه رو لایک کردید!\nاز بخش «جفت‌شده‌ها» می‌تونید باهم چت کنید."
            )
        except Exception:
            await callback.message.edit_text(
                "💑 جفت شدید! هر دو همدیگه رو لایک کردید!\nاز بخش «جفت‌شده‌ها» می‌تونید باهم چت کنید."
            )
        try:
            liker = await db.get_user(user_id)
            await callback.bot.send_message(
                target_id,
                f"💑 جفت جدید!\n{liker['name']} هم تو رو لایک کرد!\nاز بخش «جفت‌شده‌ها» می‌تونی باهاش چت کنی."
            )
        except Exception:
            pass
    else:
        try:
            await callback.message.edit_caption(caption="❤️ لایک شد!")
        except Exception:
            await callback.message.edit_text("❤️ لایک شد!")
        # Notify target
        try:
            liker = await db.get_user(user_id)
            photos = await db.get_photos(user_id)
            like_text = f"❤️ یه نفر تو رو لایک کرد!\n👤 {liker['name']} | 🎂 {liker['age']} ساله"
            if photos:
                await callback.bot.send_photo(
                    target_id, photos[0]['file_id'],
                    caption=like_text, reply_markup=like_notification_kb(user_id)
                )
            else:
                await callback.bot.send_message(
                    target_id, like_text, reply_markup=like_notification_kb(user_id)
                )
        except Exception:
            pass

    await show_next_profile(callback.message, state, user_id)


# ============ LIKE + DIRECT ============

@router.callback_query(F.data.startswith("likedirect_"))
async def process_like_direct(callback: CallbackQuery, state: FSMContext):
    target_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    user = await db.get_user(user_id)

    if user['diamonds'] < LIKE_WITH_DIRECT_COST:
        await callback.answer(
            f"❌ الماس کافی نداری! ({LIKE_WITH_DIRECT_COST} الماس لازمه)\nموجودی: {user['diamonds']} 💎",
            show_alert=True
        )
        return

    await state.update_data(likedirect_target=target_id)
    await callback.message.answer(
        f"✉️ پیام دایرکتت رو بنویس (هزینه: {LIKE_WITH_DIRECT_COST} 💎):\nبرای لغو /cancel بفرست."
    )
    await state.set_state(Search.direct_with_like)
    await callback.answer()


@router.message(Search.direct_with_like)
async def process_like_direct_send(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.set_state(Search.browsing)
        await message.answer("❌ لغو شد. ادامه جستجو...")
        await show_next_profile(message, state, message.from_user.id)
        return

    data = await state.get_data()
    target_id = data.get('likedirect_target')
    user_id = message.from_user.id

    success = await db.spend_diamonds(user_id, LIKE_WITH_DIRECT_COST, "لایک + دایرکت")
    if not success:
        await message.answer("❌ الماس کافی نداری!")
        await state.set_state(Search.browsing)
        return

    # Like + send direct
    await db.add_like(user_id, target_id)
    await db.increment_likes(user_id)
    await db.send_direct_message(user_id, target_id, message.text, LIKE_WITH_DIRECT_COST)

    # Check match
    mutual = await db.check_like(target_id, user_id)
    if mutual:
        await db.create_match(user_id, target_id)
        await message.answer("💑 لایک + دایرکت ارسال شد و جفت شدید!")
    else:
        await message.answer("✅ لایک + دایرکت ارسال شد!")

    # Notify target
    try:
        sender = await db.get_user(user_id)
        photos = await db.get_photos(user_id)
        text = f"❤️ {sender['name']} تو رو لایک کرد و پیام داد:\n\n✉️ {message.text}"
        if photos:
            await message.bot.send_photo(
                target_id, photos[0]['file_id'],
                caption=text, reply_markup=like_notification_kb(user_id)
            )
        else:
            await message.bot.send_message(
                target_id, text, reply_markup=like_notification_kb(user_id)
            )
    except Exception:
        pass

    await state.set_state(Search.browsing)
    await show_next_profile(message, state, user_id)


# ============ REJECT ============

@router.callback_query(F.data.startswith("reject_") & ~F.data.startswith("reject_like_"))
async def process_reject(callback: CallbackQuery, state: FSMContext):
    target_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    await db.add_reject(user_id, target_id)
    try:
        await callback.message.edit_caption(caption="❌ رد شد!")
    except Exception:
        await callback.message.edit_text("❌ رد شد!")
    await show_next_profile(callback.message, state, user_id)


# ============ GO BACK (premium) ============

@router.callback_query(F.data == "go_back")
async def go_back_premium(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    profile = await db.get_previous_profile(user_id)
    if not profile:
        await callback.answer("❌ پروفایل قبلی موجود نیست!", show_alert=True)
        return
    user = await db.get_user(user_id)
    await send_profile_card(callback.message, profile, user['is_premium'])
    await callback.answer()


@router.callback_query(F.data == "go_back_locked")
async def go_back_locked(callback: CallbackQuery):
    await callback.answer(
        "🔒 این قابلیت فقط برای کاربران پرمیوم فعاله!\n"
        "از بخش «اشتراک پرمیوم» می‌تونی خریداری کنی.",
        show_alert=True
    )


# ============ LIKE BACK (from notification) ============

@router.callback_query(F.data.startswith("like_back_"))
async def process_like_back(callback: CallbackQuery):
    from_user_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id

    await db.add_like(user_id, from_user_id)
    await db.create_match(user_id, from_user_id)

    try:
        await callback.message.edit_caption(
            caption="💑 جفت شدید! از بخش «جفت‌شده‌ها» می‌تونی چت کنی."
        )
    except Exception:
        await callback.message.edit_text(
            "💑 جفت شدید! از بخش «جفت‌شده‌ها» می‌تونی چت کنی."
        )

    try:
        user = await db.get_user(user_id)
        await callback.bot.send_message(
            from_user_id,
            f"💑 جفت جدید!\n{user['name']} هم تو رو لایک کرد!\nاز بخش «جفت‌شده‌ها» می‌تونی باهاش چت کنی."
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("reject_like_"))
async def process_reject_like(callback: CallbackQuery):
    from_user_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    await db.add_reject(user_id, from_user_id)
    try:
        await callback.message.edit_caption(caption="❌ رد شد!")
    except Exception:
        await callback.message.edit_text("❌ رد شد!")
