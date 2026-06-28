from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.database import db
from bot.states.registration import Search
from bot.keyboards.main_kb import search_gender_kb, profile_action_kb, main_menu_kb
from config import DAILY_VIEW_LIMIT, DAILY_LIKE_LIMIT

router = Router()


@router.message(F.text == "🔍 جستجو")
async def search_start(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    if not user or not user['is_verified']:
        await message.answer("❌ ابتدا باید ثبت‌نام و احراز هویتت رو تکمیل کنی.")
        return

    if user['registration_step'] != 'completed':
        await message.answer("❌ ابتدا باید پروفایلت رو تکمیل کنی.")
        return

    # Check if user already has a search preference
    if user['search_gender']:
        await state.update_data(search_gender=user['search_gender'])
        await show_next_profile(message, state, message.from_user.id)
    else:
        await message.answer(
            "🔍 جنسیت مورد نظرت رو برای جستجو انتخاب کن:",
            reply_markup=search_gender_kb()
        )
        await state.set_state(Search.select_gender)


@router.callback_query(F.data.startswith("search_"))
async def process_search_gender(callback: CallbackQuery, state: FSMContext):
    gender = callback.data.split("_")[1]  # male or female
    await db.update_user(callback.from_user.id, search_gender=gender)
    await state.update_data(search_gender=gender)
    await callback.message.edit_text(f"✅ جستجو: {'👨 مردها' if gender == 'male' else '👩 زن‌ها'}")
    await show_next_profile(callback.message, state, callback.from_user.id)


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
        return

    # Calculate age range
    min_age = max(18, user['age'] - 5)
    max_age = min(60, user['age'] + 5)
    search_gender = user['search_gender']

    profiles = await db.get_profiles_for_user(user_id, search_gender, min_age, max_age, 1)

    if not profiles:
        await message.answer(
            "😔 فعلاً پروفایلی برای نمایش نیست.\n"
            "بعداً دوباره تلاش کن!",
            reply_markup=main_menu_kb()
        )
        return

    profile = profiles[0]
    await db.increment_views(user_id)
    await send_profile_card(message, profile)
    await state.set_state(Search.browsing)


async def send_profile_card(message: Message, profile: dict):
    photos = await db.get_photos(profile['id'])
    interests = await db.get_interests(profile['id'])

    gender_text = "👨 مرد" if profile['gender'] == 'male' else "👩 زن"
    purpose_map = {'dating': '💕 دوست‌یابی', 'fun': '🎉 سرگرمی', 'marriage': '💍 همسریابی'}
    interest_map = {
        'coffee': '☕ قهوه', 'tea': '🍵 چای', 'smoking': '🚬 سیگار',
        'alcohol': '🍷 مشروب', 'sports': '🏋️ ورزش', 'gaming': '🎮 گیمینگ',
        'reading': '📚 کتاب‌خوانی', 'music': '🎵 موسیقی', 'movies': '🎬 فیلم',
        'travel': '✈️ سفر', 'cooking': '🍳 آشپزی', 'photography': '📸 عکاسی'
    }

    text = (
        f"👤 {profile['name']}\n"
        f"{gender_text} | 🎂 {profile['age']} ساله\n"
        f"📍 {profile['province']}، {profile['city']}\n"
        f"🎯 {purpose_map.get(profile['purpose'], '')}\n"
    )

    if interests:
        interests_text = " | ".join(interest_map.get(i, i) for i in interests)
        text += f"💡 {interests_text}\n"

    if photos:
        await message.answer_photo(
            photos[0]['file_id'],
            caption=text,
            reply_markup=profile_action_kb(profile['id'])
        )
    else:
        await message.answer(text, reply_markup=profile_action_kb(profile['id']))


# ============ LIKE ============

@router.callback_query(F.data.startswith("like_") & ~F.data.startswith("like_back_"))
async def process_like(callback: CallbackQuery, state: FSMContext):
    target_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    user = await db.get_user(user_id)
    usage = await db.get_daily_usage(user_id)

    # Check daily like limit
    if not user['is_premium'] and usage['likes_count'] >= DAILY_LIKE_LIMIT:
        await callback.answer(
            f"❌ محدودیت لایک روزانه! ({DAILY_LIKE_LIMIT} لایک)\n"
            f"فردا ریست میشه یا پرمیوم بخر.",
            show_alert=True
        )
        return

    await db.add_like(user_id, target_id)
    await db.increment_likes(user_id)

    # Check if mutual like (match)
    mutual = await db.check_like(target_id, user_id)
    if mutual:
        await db.create_match(user_id, target_id)
        await callback.message.edit_caption(
            caption="💑 جفت شدید! هر دو همدیگه رو لایک کردید!\n"
                    "از بخش «جفت‌شده‌ها» می‌تونید باهم چت کنید."
        )
        # Notify the other user
        try:
            liker = await db.get_user(user_id)
            await callback.bot.send_message(
                target_id,
                f"💑 جفت جدید!\n{liker['name']} هم تو رو لایک کرد!\n"
                f"از بخش «جفت‌شده‌ها» می‌تونی باهاش چت کنی."
            )
        except Exception:
            pass
    else:
        await callback.message.edit_caption(caption="❤️ لایک شد!")
        # Notify target about the like
        try:
            from bot.keyboards.main_kb import like_notification_kb
            liker = await db.get_user(user_id)
            photos = await db.get_photos(user_id)

            like_text = f"❤️ یه نفر تو رو لایک کرد!\n👤 {liker['name']} | 🎂 {liker['age']} ساله"

            if photos:
                await callback.bot.send_photo(
                    target_id,
                    photos[0]['file_id'],
                    caption=like_text,
                    reply_markup=like_notification_kb(user_id)
                )
            else:
                await callback.bot.send_message(
                    target_id,
                    like_text,
                    reply_markup=like_notification_kb(user_id)
                )
        except Exception:
            pass

    # Show next profile
    await show_next_profile(callback.message, state, user_id)


# ============ REJECT ============

@router.callback_query(F.data.startswith("reject_") & ~F.data.startswith("reject_like_"))
async def process_reject(callback: CallbackQuery, state: FSMContext):
    target_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    await db.add_reject(user_id, target_id)
    await callback.message.edit_caption(caption="❌ رد شد!")

    # Show next profile
    await show_next_profile(callback.message, state, user_id)


# ============ LIKE BACK (from notification) ============

@router.callback_query(F.data.startswith("like_back_"))
async def process_like_back(callback: CallbackQuery):
    from_user_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id

    await db.add_like(user_id, from_user_id)
    await db.create_match(user_id, from_user_id)

    await callback.message.edit_caption(
        caption="💑 جفت شدید! از بخش «جفت‌شده‌ها» می‌تونی چت کنی."
    )

    # Notify the other user
    try:
        user = await db.get_user(user_id)
        await callback.bot.send_message(
            from_user_id,
            f"💑 جفت جدید!\n{user['name']} هم تو رو لایک کرد!\n"
            f"از بخش «جفت‌شده‌ها» می‌تونی باهاش چت کنی."
        )
    except Exception:
        pass


# ============ REJECT LIKE ============

@router.callback_query(F.data.startswith("reject_like_"))
async def process_reject_like(callback: CallbackQuery):
    from_user_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id

    await db.add_reject(user_id, from_user_id)
    await callback.message.edit_caption(caption="❌ رد شد!")
