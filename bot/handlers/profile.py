from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.database import db
from bot.states.registration import Profile, Report
from bot.keyboards.main_kb import (
    my_profile_kb, main_menu_kb, diamonds_kb,
    edit_profile_kb, complete_profile_kb, interactions_kb,
    diamond_tasks_kb, explore_more_kb
)
from config import ADMIN_IDS, VERIFICATION_GROUP_ID

router = Router()


# ============ VIEW PROFILE ============

@router.message(F.text == "👤 پروفایل من")
async def view_profile(message: Message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)

    if not user:
        await message.answer("❌ ابتدا ثبت‌نام کن! /start")
        return

    photos = await db.get_photos(user_id)

    verified_badge = " ✅" if user['is_verified'] else ""
    premium_badge = " 👑" if user['is_premium'] else ""
    gender_emoji = "👨" if user['gender'] == 'male' else "👩"
    purpose_map = {'dating': '💕 دوست‌یابی', 'fun': '🎉 سرگرمی', 'marriage': '💍 همسریابی'}

    text = f"{gender_emoji} {user['name']} ({user['age']}){verified_badge}{premium_badge} | Fa\n"
    text += f"📍 {user['province']} - {user['city']}\n\n"

    # Extra info line
    info_parts = []
    if user.get('purpose'):
        info_parts.append(f"👫 {purpose_map.get(user['purpose'], '')}")
    if user.get('height'):
        info_parts.append(f"📐 {user['height']}")
    if user.get('eye_color'):
        info_parts.append(f"👁️ {user['eye_color']}")
    if user.get('job'):
        info_parts.append(f"💼 {user['job']}")
    if user.get('relationship_status'):
        info_parts.append(f"💕 {user['relationship_status']}")
    if user.get('exercise'):
        info_parts.append(f"🏋️ {user['exercise']}")
    if user.get('zodiac'):
        info_parts.append(f"⭐ {user['zodiac']}")

    if info_parts:
        text += " | ".join(info_parts) + "\n"

    if user.get('bio'):
        text += f"\n📝 {user['bio']}\n"

    if photos:
        await message.answer_photo(
            photos[0]['file_id'],
            caption=text,
            reply_markup=my_profile_kb(user['is_verified'])
        )
    else:
        await message.answer(text, reply_markup=my_profile_kb(user['is_verified']))


# ============ EDIT PROFILE SECTION ============

@router.callback_query(F.data == "edit_profile")
async def edit_profile_menu(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    photos = await db.get_photos(callback.from_user.id)
    verified_badge = " ✅" if user['is_verified'] else ""
    premium_badge = " 👑" if user['is_premium'] else ""
    gender_emoji = "👨" if user['gender'] == 'male' else "👩"

    text = f"{gender_emoji} {user['name']} ({user['age']}){verified_badge}{premium_badge}\n"
    text += f"📍 {user['province']} - {user['city']}\n"

    if photos:
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer_photo(
            photos[0]['file_id'],
            caption=text,
            reply_markup=edit_profile_kb()
        )
    else:
        await callback.message.edit_text(text, reply_markup=edit_profile_kb())
    await callback.answer()


# ============ COMPLETE PROFILE SECTION ============

@router.callback_query(F.data == "complete_profile")
async def complete_profile_menu(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)

    text = "📋 تکمیل پروفایل\n\n"
    text += "با انتخاب گزینه‌ها اطلاعات تکمیلی پروفایل خود را کامل‌تر کنید.\n\n"
    text += "📊 اطلاعات تکمیلی پروفایل شما:\n"
    text += f"* 📐 قد: {user.get('height') or '—'}\n"
    text += f"* 👁️ رنگ چشم: {user.get('eye_color') or '—'}\n"
    text += f"* 🏋️ ورزش: {user.get('exercise') or '—'}\n"
    text += f"* 💕 وضعیت رابطه: {user.get('relationship_status') or '—'}\n"
    text += f"* 💼 زمینه شغلی: {user.get('job') or '—'}\n"
    text += f"* ⭐ ماه تولد: {user.get('zodiac') or '—'}\n"
    text += f"* 🧠 شخصیت: {user.get('personality') or '—'}\n"
    text += f"* 🎨 رنگ پوست: {user.get('skin_color') or '—'}\n"
    text += f"* 🎓 تحصیلات: {user.get('education') or '—'}\n"

    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(text, reply_markup=complete_profile_kb())
    await callback.answer()


# ============ INTERACTIONS SECTION ============

@router.callback_query(F.data == "interactions")
async def interactions_menu(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    verified_badge = " ✅" if user['is_verified'] else ""
    gender_emoji = "👨" if user['gender'] == 'male' else "👩"
    text = f"{gender_emoji} {user['name']} ({user['age']}){verified_badge}\n📍 {user['province']} - {user['city']}\n"
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(text, reply_markup=interactions_kb())
    await callback.answer()


@router.callback_query(F.data == "view_likers")
async def view_likers_from_profile(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = await db.get_user(user_id)
    if not user['is_verified']:
        await callback.answer("🔒 برای دیدن لایک‌ها باید احراز هویت کنی!", show_alert=True)
        return
    likers = await db.get_who_liked_me(user_id)
    if not likers:
        await callback.answer("😔 هنوز کسی تو رو لایک نکرده!", show_alert=True)
        return
    from bot.keyboards.main_kb import like_notification_kb
    await callback.message.answer(f"❤️ لایک‌ها ({len(likers)} نفر):")
    for liker in likers[:10]:
        photos = await db.get_photos(liker['id'])
        text = f"👤 {liker['name']} | 🎂 {liker['age']} ساله\n📍 {liker['province']}، {liker['city']}"
        if photos:
            await callback.message.answer_photo(photos[0]['file_id'], caption=text, reply_markup=like_notification_kb(liker['id']))
        else:
            await callback.message.answer(text, reply_markup=like_notification_kb(liker['id']))
    await callback.answer()


@router.callback_query(F.data == "view_matches_list")
async def view_matches_from_profile(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = await db.get_user(user_id)
    if not user['is_verified']:
        await callback.answer("🔒 برای دیدن مچ‌ها باید احراز هویت کنی!", show_alert=True)
        return
    from bot.keyboards.main_kb import match_profile_kb
    matches = await db.get_matches(user_id)
    if not matches:
        await callback.answer("😔 هنوز مچی نداری!", show_alert=True)
        return
    await callback.message.answer(f"💕 مچ‌ها ({len(matches)} نفر):")
    for match in matches[:10]:
        photos = await db.get_photos(match['id'])
        text = f"👤 {match['name']} | 🎂 {match['age']} ساله\n📍 {match['province']}، {match['city']}"
        if photos:
            await callback.message.answer_photo(photos[0]['file_id'], caption=text, reply_markup=match_profile_kb(match['id']))
        else:
            await callback.message.answer(text, reply_markup=match_profile_kb(match['id']))
    await callback.answer()


@router.callback_query(F.data == "view_sent_likes")
async def view_sent_likes(callback: CallbackQuery):
    user_id = callback.from_user.id
    sent = await db.fetchall(
        "SELECT u.name, u.age, u.province, u.city FROM likes l JOIN users u ON l.to_user_id = u.id WHERE l.from_user_id = %s ORDER BY l.created_at DESC LIMIT 15",
        (user_id,)
    )
    if not sent:
        await callback.answer("هنوز لایکی ارسال نکردی!", show_alert=True)
        return
    text = "💌 لایک‌های ارسالی:\n\n"
    for s in sent:
        text += f"• {s['name']} ({s['age']}) — {s['province']}\n"
    await callback.message.answer(text)
    await callback.answer()


@router.callback_query(F.data == "view_blocked")
async def view_blocked(callback: CallbackQuery):
    user_id = callback.from_user.id
    blocked = await db.fetchall(
        "SELECT u.id, u.name FROM blocks b JOIN users u ON b.blocked_id = u.id WHERE b.blocker_id = %s",
        (user_id,)
    )
    if not blocked:
        await callback.answer("هیچ‌کسی رو بلاک نکردی!", show_alert=True)
        return
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    text = "🚫 بلاک‌شده‌ها:\n\n"
    kb_rows = []
    for b in blocked:
        text += f"• {b['name']}\n"
        kb_rows.append([InlineKeyboardButton(text=f"آن‌بلاک {b['name']}", callback_data=f"unblock_{b['id']}")])
    kb_rows.append([InlineKeyboardButton(text="🔙 بازگشت", callback_data="interactions")])
    await callback.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows))
    await callback.answer()


@router.callback_query(F.data == "clear_dislikes")
async def clear_dislikes(callback: CallbackQuery):
    user_id = callback.from_user.id
    await db.execute("DELETE FROM rejects WHERE from_user_id = %s", (user_id,))
    await callback.answer("✅ دیسلایک‌ها پاک شدن! حالا دوباره می‌تونی اون‌ها رو ببینی.", show_alert=True)


@router.callback_query(F.data.startswith("unblock_"))
async def unblock_user(callback: CallbackQuery):
    target_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    await db.execute("DELETE FROM blocks WHERE blocker_id = %s AND blocked_id = %s", (user_id, target_id))
    await callback.answer("✅ آن‌بلاک شد!", show_alert=True)


# ============ STATS ============

@router.callback_query(F.data == "my_stats")
async def my_stats(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = await db.get_user(user_id)
    views_r, likes_r, attract_pct = await db.get_attractiveness(user_id)
    views_s, likes_s, picky_pct = await db.get_pickiness(user_id)
    matches_count = await db.fetchone(
        "SELECT COUNT(*) as cnt FROM matches WHERE (user1_id = %s OR user2_id = %s) AND is_active = 1",
        (user_id, user_id)
    )

    text = (
        f"📊 آمار شخصی شما\n\n"
        f"👁️ پروفایل‌هایی که بازدید کردید: {views_s}\n"
        f"👀 دفعاتی که پروفایل شما بازدید شده: {views_r}\n"
        f"❤️ لایک‌های دریافتی: {likes_r}\n"
        f"👍 لایک‌های ارسالی: {likes_s}\n"
        f"💕 مچ‌ها: {matches_count['cnt']}\n"
        f"❤️ نرخ جذابیت شما در اکسپلور: {attract_pct}%\n"
        f"🤨 سخت‌پسندی شما: {picky_pct}%\n\n"
        f"💎 الماس‌های شما: {user['diamonds']}"
    )

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 مشاهده پروفایل من", callback_data="back_profile")]
    ])
    await callback.message.answer(text, reply_markup=kb)
    await callback.answer()


# ============ BACK TO PROFILE ============

@router.callback_query(F.data == "back_profile")
async def back_to_profile(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except Exception:
        pass
    # Re-send profile
    user_id = callback.from_user.id
    user = await db.get_user(user_id)
    photos = await db.get_photos(user_id)
    verified_badge = " ✅" if user['is_verified'] else ""
    gender_emoji = "👨" if user['gender'] == 'male' else "👩"
    purpose_map = {'dating': '💕 دوست‌یابی', 'fun': '🎉 سرگرمی', 'marriage': '💍 همسریابی'}

    text = f"{gender_emoji} {user['name']} ({user['age']}){verified_badge} | Fa\n"
    text += f"📍 {user['province']} - {user['city']}\n\n"
    info_parts = []
    if user.get('purpose'):
        info_parts.append(f"👫 {purpose_map.get(user['purpose'], '')}")
    if user.get('height'):
        info_parts.append(f"📐 {user['height']}")
    if user.get('eye_color'):
        info_parts.append(f"👁️ {user['eye_color']}")
    if user.get('job'):
        info_parts.append(f"💼 {user['job']}")
    if user.get('relationship_status'):
        info_parts.append(f"💕 {user['relationship_status']}")
    if info_parts:
        text += " | ".join(info_parts) + "\n"
    if user.get('bio'):
        text += f"\n📝 {user['bio']}\n"

    if photos:
        await callback.message.answer_photo(
            photos[0]['file_id'], caption=text, reply_markup=my_profile_kb(user['is_verified'])
        )
    else:
        await callback.message.answer(text, reply_markup=my_profile_kb(user['is_verified']))
    await callback.answer()


# NOTE: start_verification handler is in verification.py (single handler for both profile and registration)


# ============ EDIT NAME ============

@router.callback_query(F.data == "edit_name")
async def start_edit_name(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Profile.editing_name)
    await callback.message.answer("✏️ اسم جدیدت رو بنویس:")
    await callback.answer()


@router.message(Profile.editing_name)
async def process_edit_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2 or len(name) > 50:
        await message.answer("❌ اسم باید بین 2 تا 50 کاراکتر باشه.")
        return
    await db.update_user(message.from_user.id, name=name)
    await message.answer(f"✅ اسمت تغییر کرد به: {name}", reply_markup=main_menu_kb())
    await state.clear()


# ============ EDIT AGE ============

@router.callback_query(F.data == "edit_age")
async def start_edit_age(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Profile.editing_age)
    await callback.message.answer("🎂 سن جدیدت رو بنویس (عدد):")
    await callback.answer()


@router.message(Profile.editing_age)
async def process_edit_age(message: Message, state: FSMContext):
    try:
        age = int(message.text.strip())
        if age < 14 or age > 80:
            await message.answer("❌ سن باید بین 14 تا 80 باشه.")
            return
    except ValueError:
        await message.answer("❌ عدد وارد کن!")
        return
    await db.update_user(message.from_user.id, age=age)
    await message.answer(f"✅ سنت تغییر کرد به: {age}", reply_markup=main_menu_kb())
    await state.clear()


# ============ EDIT LOCATION ============

@router.callback_query(F.data == "edit_location")
async def start_edit_location(callback: CallbackQuery, state: FSMContext):
    from bot.data.cities import PROVINCES
    from bot.keyboards.main_kb import province_kb
    await state.set_state(Profile.editing_location)
    await callback.message.answer("📍 استان جدیدت رو انتخاب کن:", reply_markup=province_kb(PROVINCES))
    await callback.answer()


@router.message(Profile.editing_location)
async def process_edit_location(message: Message, state: FSMContext):
    from bot.data.cities import PROVINCES, CITIES
    from bot.keyboards.main_kb import city_kb
    province = message.text.strip()
    if province not in PROVINCES:
        await message.answer("❌ استان نامعتبر!")
        return
    await db.update_user(message.from_user.id, province=province)
    await state.set_state(Profile.editing_location_city)
    cities = CITIES.get(province, [])
    await message.answer("🏙️ شهرت رو انتخاب کن:", reply_markup=city_kb(cities))


@router.message(Profile.editing_location_city)
async def process_edit_location_city(message: Message, state: FSMContext):
    city = message.text.strip()
    await db.update_user(message.from_user.id, city=city)
    await message.answer(f"✅ لوکیشن تغییر کرد!", reply_markup=main_menu_kb())
    await state.clear()


# ============ EDIT BIO ============

@router.callback_query(F.data == "edit_bio")
async def start_edit_bio(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Profile.editing_bio)
    await callback.message.answer("📝 بیو جدیدت رو بنویس (حداکثر 300 کاراکتر):\nیا /skip برای حذف بیو")
    await callback.answer()


@router.message(Profile.editing_bio)
async def process_edit_bio(message: Message, state: FSMContext):
    if message.text == "/skip":
        await db.update_user(message.from_user.id, bio=None)
        await message.answer("✅ بیو حذف شد!", reply_markup=main_menu_kb())
    else:
        bio = message.text.strip()
        if len(bio) > 300:
            await message.answer("❌ بیو حداکثر 300 کاراکتر باشه!")
            return
        await db.update_user(message.from_user.id, bio=bio)
        await message.answer("✅ بیو آپدیت شد!", reply_markup=main_menu_kb())
    await state.clear()


# ============ EDIT PHOTOS ============

@router.callback_query(F.data == "edit_photos")
async def start_edit_photos(callback: CallbackQuery):
    await callback.answer(
        "برای تغییر عکس‌ها، عکس جدید بفرست.\nقبلی‌ها حذف میشن.",
        show_alert=True
    )


# ============ EDIT PURPOSE ============

@router.callback_query(F.data == "edit_purpose")
async def start_edit_purpose(callback: CallbackQuery):
    from bot.keyboards.main_kb import purpose_kb
    await callback.message.answer("🎯 هدف جدیدت رو انتخاب کن:", reply_markup=purpose_kb())
    await callback.answer()


# ============ EDIT INTERESTS ============

@router.callback_query(F.data == "edit_interests")
async def start_edit_interests(callback: CallbackQuery):
    from bot.keyboards.main_kb import interests_kb
    await callback.message.answer("💡 علاقه‌مندی‌های جدیدت رو انتخاب کن:", reply_markup=interests_kb())
    await callback.answer()


# ============ COMPLETE PROFILE FIELDS ============

@router.callback_query(F.data == "cp_height")
async def cp_height(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Profile.editing_height)
    await callback.message.answer("📐 قدت رو بنویس (مثلاً: 180-190 یا 175):")
    await callback.answer()


@router.message(Profile.editing_height)
async def process_cp_height(message: Message, state: FSMContext):
    await db.update_user(message.from_user.id, height=message.text.strip())
    await message.answer("✅ قد ثبت شد!", reply_markup=main_menu_kb())
    await state.clear()


@router.callback_query(F.data == "cp_eye_color")
async def cp_eye_color(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Profile.editing_eye_color)
    await callback.message.answer("👁️ رنگ چشمت رو بنویس (مثلاً: مشکی، قهوه‌ای، سبز، آبی):")
    await callback.answer()


@router.message(Profile.editing_eye_color)
async def process_cp_eye_color(message: Message, state: FSMContext):
    await db.update_user(message.from_user.id, eye_color=message.text.strip())
    await message.answer("✅ رنگ چشم ثبت شد!", reply_markup=main_menu_kb())
    await state.clear()


@router.callback_query(F.data == "cp_exercise")
async def cp_exercise(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Profile.editing_exercise)
    await callback.message.answer("🏋️ چقدر ورزش می‌کنی؟ (مثلاً: هر روز، چند بار در هفته، کم، اصلاً):")
    await callback.answer()


@router.message(Profile.editing_exercise)
async def process_cp_exercise(message: Message, state: FSMContext):
    await db.update_user(message.from_user.id, exercise=message.text.strip())
    await message.answer("✅ ثبت شد!", reply_markup=main_menu_kb())
    await state.clear()


@router.callback_query(F.data == "cp_relationship")
async def cp_relationship(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Profile.editing_relationship)
    await callback.message.answer("💕 وضعیت رابطه‌ات رو بنویس (مثلاً: مجرد، در رابطه، نامزد):")
    await callback.answer()


@router.message(Profile.editing_relationship)
async def process_cp_relationship(message: Message, state: FSMContext):
    await db.update_user(message.from_user.id, relationship_status=message.text.strip())
    await message.answer("✅ ثبت شد!", reply_markup=main_menu_kb())
    await state.clear()


@router.callback_query(F.data == "cp_job")
async def cp_job(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Profile.editing_job)
    await callback.message.answer("💼 زمینه شغلیت رو بنویس (مثلاً: فریلنسر، دانشجو، مهندس):")
    await callback.answer()


@router.message(Profile.editing_job)
async def process_cp_job(message: Message, state: FSMContext):
    await db.update_user(message.from_user.id, job=message.text.strip())
    await message.answer("✅ ثبت شد!", reply_markup=main_menu_kb())
    await state.clear()


@router.callback_query(F.data == "cp_zodiac")
async def cp_zodiac(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Profile.editing_zodiac)
    await callback.message.answer("⭐ ماه تولدت رو بنویس (مثلاً: فروردین، اردیبهشت، اسفند...):")
    await callback.answer()


@router.message(Profile.editing_zodiac)
async def process_cp_zodiac(message: Message, state: FSMContext):
    await db.update_user(message.from_user.id, zodiac=message.text.strip())
    await message.answer("✅ ثبت شد!", reply_markup=main_menu_kb())
    await state.clear()


@router.callback_query(F.data == "cp_personality")
async def cp_personality(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Profile.editing_personality)
    await callback.message.answer("🧠 تایپ شخصیتت رو بنویس (مثلاً: درون‌گرا، برون‌گرا):")
    await callback.answer()


@router.message(Profile.editing_personality)
async def process_cp_personality(message: Message, state: FSMContext):
    await db.update_user(message.from_user.id, personality=message.text.strip())
    await message.answer("✅ ثبت شد!", reply_markup=main_menu_kb())
    await state.clear()


@router.callback_query(F.data == "cp_skin_color")
async def cp_skin_color(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Profile.editing_skin_color)
    await callback.message.answer("🎨 رنگ پوستت رو بنویس (مثلاً: سفید، گندمی، سبزه):")
    await callback.answer()


@router.message(Profile.editing_skin_color)
async def process_cp_skin_color(message: Message, state: FSMContext):
    await db.update_user(message.from_user.id, skin_color=message.text.strip())
    await message.answer("✅ ثبت شد!", reply_markup=main_menu_kb())
    await state.clear()


@router.callback_query(F.data == "cp_education")
async def cp_education(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Profile.editing_education)
    await callback.message.answer("🎓 مقطع تحصیلیت رو بنویس (مثلاً: دیپلم، کارشناسی، کارشناسی ارشد):")
    await callback.answer()


@router.message(Profile.editing_education)
async def process_cp_education(message: Message, state: FSMContext):
    await db.update_user(message.from_user.id, education=message.text.strip())
    await message.answer("✅ ثبت شد!", reply_markup=main_menu_kb())
    await state.clear()


# ============ DIAMONDS ============

@router.message(F.text == "💎 الماس‌ها")
async def view_diamonds(message: Message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    streak = user['streak_days']

    # Medal progress
    medal_text = "🏆 مدال‌ها و پیشرفت:\n"
    medal_text += f"🌱 جوانه امید 20 💎\n(3 روز متوالی): {min(streak, 3)}/3 {'✅' if user['streak_3_claimed'] else ''}\n"
    medal_text += f"🏅 هفت راز 50 💎\n(7 روز متوالی): {min(streak, 7)}/7 {'✅' if user['streak_7_claimed'] else ''}\n"
    medal_text += f"🏆 پایدار 200 💎\n(30 روز متوالی): {min(streak, 30)}/30 {'✅' if user['streak_30_claimed'] else ''}\n"

    text = (
        f"💎 الماس‌های شما: {user['diamonds']}\n\n"
        f"⏰ روزهای متوالی دریافت الماس: {streak}\n\n"
        f"{medal_text}"
    )

    # Build keyboard with timer for daily diamond
    from bot.keyboards.main_kb import diamonds_kb_with_timer
    kb = await diamonds_kb_with_timer(user)
    await message.answer(text, reply_markup=kb)


# ============ DAILY DIAMOND ============

@router.callback_query(F.data == "daily_diamond")
async def claim_daily(callback: CallbackQuery):
    success = await db.claim_daily_diamond(callback.from_user.id)
    if success:
        await callback.answer("🎁 1 الماس رایگان دریافت کردی!", show_alert=True)
        # Refresh keyboard with timer
        user = await db.get_user(callback.from_user.id)
        from bot.keyboards.main_kb import diamonds_kb_with_timer
        kb = await diamonds_kb_with_timer(user)
        try:
            await callback.message.edit_reply_markup(reply_markup=kb)
        except Exception:
            pass
    else:
        # Show remaining time
        user = await db.get_user(callback.from_user.id)
        from datetime import datetime, date, timedelta
        if user['last_daily_claim']:
            now = datetime.now()
            claim_date = user['last_daily_claim']
            if hasattr(claim_date, 'date'):
                claim_date = claim_date.date()
            tomorrow = datetime.combine(claim_date + timedelta(days=1), datetime.min.time())
            remaining = tomorrow - now
            hours = int(remaining.total_seconds() // 3600)
            minutes = int((remaining.total_seconds() % 3600) // 60)
            await callback.answer(f"⏳ {hours} ساعت و {minutes} دقیقه تا الماس بعدی!", show_alert=True)
        else:
            await callback.answer("❌ امروز قبلاً دریافت کردی! فردا بیا.", show_alert=True)


# ============ DIAMOND TASKS ============

@router.callback_query(F.data == "diamond_tasks")
async def show_diamond_tasks(callback: CallbackQuery):
    user_id = callback.from_user.id
    # Get completed tasks
    completed = await db.fetchall(
        "SELECT task_type FROM diamond_tasks WHERE user_id = %s",
        (user_id,)
    )
    completed_types = set(r['task_type'] for r in completed) if completed else set()
    from bot.keyboards.main_kb import diamond_tasks_kb_checked
    await callback.message.answer(
        "🎁 وظایف الماسی:\n\nهر وظیفه رو انجام بده و الماس بگیر!\n⚠️ هر وظیفه فقط یکبار قابل انجامه.",
        reply_markup=diamond_tasks_kb_checked(completed_types)
    )
    await callback.answer()


@router.callback_query(F.data == "task_join_channel")
async def task_join_channel(callback: CallbackQuery):
    from config import CHANNEL_ID
    user_id = callback.from_user.id

    # Check if already done (one-time only)
    done = await db.fetchone(
        "SELECT id FROM diamond_tasks WHERE user_id = %s AND task_type = 'join_channel'",
        (user_id,)
    )
    if done:
        await callback.answer("✅ این وظیفه رو قبلاً انجام دادی!", show_alert=True)
        return

    # Verify membership
    if CHANNEL_ID:
        try:
            channel_id = int(CHANNEL_ID) if CHANNEL_ID.lstrip('-').isdigit() else CHANNEL_ID
            member = await callback.bot.get_chat_member(channel_id, user_id)
            if member.status in ('left', 'kicked'):
                await callback.answer("❌ اول باید در کانال جوین شی! بعد دوباره بزن.", show_alert=True)
                return
        except Exception:
            pass

    await db.execute("INSERT INTO diamond_tasks (user_id, task_type) VALUES (%s, %s)", (user_id, 'join_channel'))
    await db.add_diamonds(user_id, 3, 'gift', 'وظیفه: جوین کانال')
    await callback.answer("✅ 3 الماس دریافت کردی! ممنون از جوین شدنت 💎", show_alert=True)
    # Refresh tasks kb
    completed = await db.fetchall("SELECT task_type FROM diamond_tasks WHERE user_id = %s", (user_id,))
    completed_types = set(r['task_type'] for r in completed)
    from bot.keyboards.main_kb import diamond_tasks_kb_checked
    try:
        await callback.message.edit_reply_markup(reply_markup=diamond_tasks_kb_checked(completed_types))
    except Exception:
        pass


@router.callback_query(F.data == "task_comment")
async def task_comment(callback: CallbackQuery):
    user_id = callback.from_user.id
    done = await db.fetchone(
        "SELECT id FROM diamond_tasks WHERE user_id = %s AND task_type = 'comment'",
        (user_id,)
    )
    if done:
        await callback.answer("✅ این وظیفه رو قبلاً انجام دادی!", show_alert=True)
        return
    # Comment verification is manual — trust the user
    await db.execute("INSERT INTO diamond_tasks (user_id, task_type) VALUES (%s, %s)", (user_id, 'comment'))
    await db.add_diamonds(user_id, 4, 'gift', 'وظیفه: کامنت')
    await callback.answer("✅ 4 الماس دریافت کردی! ممنون 💎", show_alert=True)
    completed = await db.fetchall("SELECT task_type FROM diamond_tasks WHERE user_id = %s", (user_id,))
    completed_types = set(r['task_type'] for r in completed)
    from bot.keyboards.main_kb import diamond_tasks_kb_checked
    try:
        await callback.message.edit_reply_markup(reply_markup=diamond_tasks_kb_checked(completed_types))
    except Exception:
        pass


@router.callback_query(F.data == "task_react")
async def task_react(callback: CallbackQuery):
    user_id = callback.from_user.id
    done = await db.fetchone(
        "SELECT id FROM diamond_tasks WHERE user_id = %s AND task_type = 'react'",
        (user_id,)
    )
    if done:
        await callback.answer("✅ این وظیفه رو قبلاً انجام دادی!", show_alert=True)
        return
    await db.execute("INSERT INTO diamond_tasks (user_id, task_type) VALUES (%s, %s)", (user_id, 'react'))
    await db.add_diamonds(user_id, 2, 'gift', 'وظیفه: ری‌اکشن')
    await callback.answer("✅ 2 الماس دریافت کردی! 💎", show_alert=True)
    completed = await db.fetchall("SELECT task_type FROM diamond_tasks WHERE user_id = %s", (user_id,))
    completed_types = set(r['task_type'] for r in completed)
    from bot.keyboards.main_kb import diamond_tasks_kb_checked
    try:
        await callback.message.edit_reply_markup(reply_markup=diamond_tasks_kb_checked(completed_types))
    except Exception:
        pass


@router.callback_query(F.data == "task_sponsor")
async def task_sponsor(callback: CallbackQuery):
    from config import SPONSOR_CHANNEL_ID
    user_id = callback.from_user.id

    done = await db.fetchone(
        "SELECT id FROM diamond_tasks WHERE user_id = %s AND task_type = 'sponsor'",
        (user_id,)
    )
    if done:
        await callback.answer("✅ این وظیفه رو قبلاً انجام دادی!", show_alert=True)
        return

    # Verify membership in sponsor channel
    if SPONSOR_CHANNEL_ID:
        try:
            channel_id = int(SPONSOR_CHANNEL_ID) if SPONSOR_CHANNEL_ID.lstrip('-').isdigit() else SPONSOR_CHANNEL_ID
            member = await callback.bot.get_chat_member(channel_id, user_id)
            if member.status in ('left', 'kicked'):
                await callback.answer("❌ اول باید در کانال اسپانسر جوین شی! بعد دوباره بزن.", show_alert=True)
                return
        except Exception:
            pass

    await db.execute("INSERT INTO diamond_tasks (user_id, task_type) VALUES (%s, %s)", (user_id, 'sponsor'))
    await db.add_diamonds(user_id, 6, 'gift', 'وظیفه: جوین اسپانسر')
    await callback.answer("✅ 6 الماس دریافت کردی! 💎", show_alert=True)
    completed = await db.fetchall("SELECT task_type FROM diamond_tasks WHERE user_id = %s", (user_id,))
    completed_types = set(r['task_type'] for r in completed)
    from bot.keyboards.main_kb import diamond_tasks_kb_checked
    try:
        await callback.message.edit_reply_markup(reply_markup=diamond_tasks_kb_checked(completed_types))
    except Exception:
        pass


@router.callback_query(F.data == "back_diamonds")
async def back_diamonds(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.answer()


# ============ TRANSACTION HISTORY ============

@router.callback_query(F.data == "transaction_history")
async def transaction_history(callback: CallbackQuery):
    user_id = callback.from_user.id
    txns = await db.fetchall(
        "SELECT amount, description, created_at FROM diamond_transactions WHERE user_id = %s ORDER BY created_at DESC LIMIT 15",
        (user_id,)
    )
    if not txns:
        await callback.answer("تراکنشی نداری!", show_alert=True)
        return
    text = "📜 تاریخچه تراکنش‌ها:\n\n"
    for t in txns:
        sign = "+" if t['amount'] > 0 else ""
        text += f"{sign}{t['amount']} 💎 — {t['description'] or '—'}\n"
    await callback.message.answer(text)
    await callback.answer()


# ============ BUY DIAMONDS ============

@router.callback_query(F.data == "buy_diamonds")
async def buy_diamonds(callback: CallbackQuery):
    text = (
        "🛒 خرید الماس:\n\n"
        "برای خرید الماس با پشتیبانی تماس بگیر.\n"
        "از منوی اصلی «📞 پشتیبانی» رو بزن."
    )
    await callback.answer(text, show_alert=True)


# ============ FREE DIAMOND INFO ============

@router.callback_query(F.data == "free_diamond_info")
async def free_diamond_info(callback: CallbackQuery):
    text = (
        "💎 الماس رایگان:\n\n"
        "• هر 24 ساعت 1 الماس رایگان\n"
        "• 3 روز متوالی: 10 الماس 🌱\n"
        "• 7 روز متوالی: 30 الماس 🏅\n"
        "• 30 روز متوالی: 70 الماس 🏆\n\n"
        "همچنین از وظایف الماسی و معرفی دوستان هم الماس بگیر!"
    )
    await callback.answer(text, show_alert=True)


# ============ REFERRAL LINK ============

@router.callback_query(F.data == "referral_link")
async def referral_link(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    code = user['referral_code']
    bot_info = await callback.bot.me()
    link = f"https://t.me/{bot_info.username}?start={code}"
    text = (
        f"👥 معرفی دوستان:\n\n"
        f"🔗 لینک دعوت تو:\n{link}\n\n"
        f"با هر دعوت از دوستت:\n"
        f"• 10 الماس رایگان\n"
        f"• 10% از مبلغ خریدهای دوستت\n\n"
        f"لینک رو به دوستات بفرست!"
    )
    await callback.message.answer(text)
    await callback.answer()


# ============ STREAK REWARDS ============

@router.callback_query(F.data.startswith("streak_"))
async def claim_streak(callback: CallbackQuery):
    streak_type = callback.data.replace("streak_", "")
    success, msg = await db.claim_streak_reward(callback.from_user.id, streak_type)
    await callback.answer(msg, show_alert=True)


# ============ PREMIUM ============

@router.message(F.text == "⭐ اشتراک پرمیوم")
async def view_premium(message: Message):
    user = await db.get_user(message.from_user.id)

    if user['is_premium']:
        from datetime import datetime
        status = "✅ فعال"
        remaining = ""
        if user.get('premium_expires_at'):
            expires = user['premium_expires_at']
            if isinstance(expires, str):
                expires = datetime.fromisoformat(expires)
            now = datetime.now()
            delta = expires - now
            days_left = max(0, delta.days)
            remaining = f"\n📅 روزهای باقیمانده: {days_left} روز"
    else:
        status = "❌ غیرفعال"
        remaining = ""

    text = (
        f"⭐ اشتراک پرمیوم: {status}{remaining}\n\n"
        f"✨ مزایای پرمیوم:\n"
        f"• 🔍 جستجوی نامحدود (بدون محدودیت روزانه)\n"
        f"• ❤️ لایک نامحدود\n"
        f"• 🔙 دکمه بازگشت در اکسپلور\n"
        f"• 👁️ بیشتر دیده شدن در اکسپلور (اولویت نمایش)\n"
        f"• 🚫 عدم نمایش تبلیغات\n"
        f"• 🎯 دسترسی به فیلترهای پیشرفته جستجو\n"
        f"• 💎 2 برابر الماس روزانه رایگان\n"
        f"• 👻 مشاهده پروفایل بدون اینکه طرف بفهمه\n\n"
        f"برای خرید اشتراک با پشتیبانی تماس بگیر."
    )
    await message.answer(text)


# ============ SUPPORT ============

@router.message(F.text == "📞 پشتیبانی")
async def support_start(message: Message, state: FSMContext):
    from bot.states.registration import Support
    await message.answer(
        "📞 پشتیبانی ایزی‌چت:\n\n"
        "پیامت رو بنویس و ادمین بهت جواب میده.\n"
        "برای بازگشت /cancel بزن."
    )
    await state.set_state(Support.waiting_message)


from bot.states.registration import Support


@router.message(Support.waiting_message)
async def process_support_message(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("🏠 بازگشت به منو", reply_markup=main_menu_kb())
        return

    user_id = message.from_user.id
    user = await db.get_user(user_id)

    support_text = (
        f"📞 پیام پشتیبانی جدید:\n\n"
        f"👤 {user['name']} (ID: {user_id})\n"
        f"📝 {message.text}\n\n"
        f"برای پاسخ:\n/reply {user_id} متن پاسخ"
    )

    # Send to group first
    if VERIFICATION_GROUP_ID:
        try:
            await message.bot.send_message(VERIFICATION_GROUP_ID, support_text)
        except Exception:
            pass

    # Also send to admin DMs
    for admin_id in ADMIN_IDS:
        try:
            await message.bot.send_message(admin_id, support_text)
        except Exception:
            pass

    await message.answer("✅ پیامت ارسال شد! ادمین بهت جواب میده.", reply_markup=main_menu_kb())
    await state.clear()


# ============ EXPLORE MORE (block/report) ============

@router.callback_query(F.data.startswith("explore_more_"))
async def explore_more(callback: CallbackQuery):
    target_id = int(callback.data.split("_")[2])
    await callback.message.edit_reply_markup(reply_markup=explore_more_kb(target_id))
    await callback.answer()


@router.callback_query(F.data.startswith("block_user_"))
async def block_user(callback: CallbackQuery):
    target_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    try:
        await db.execute(
            "INSERT IGNORE INTO blocks (blocker_id, blocked_id) VALUES (%s, %s)",
            (user_id, target_id)
        )
    except Exception:
        pass
    await callback.answer("🚫 کاربر بلاک شد!", show_alert=True)


@router.callback_query(F.data.startswith("report_user_"))
async def report_user(callback: CallbackQuery, state: FSMContext):
    target_id = int(callback.data.split("_")[2])
    await state.set_state(Report.waiting_reason)
    await state.update_data(report_target=target_id)
    await callback.message.answer("⚠️ دلیل گزارش رو بنویس:")
    await callback.answer()


@router.message(Report.waiting_reason)
async def process_report_reason(message: Message, state: FSMContext):
    data = await state.get_data()
    target_id = data['report_target']
    user_id = message.from_user.id
    await db.execute(
        "INSERT INTO reports (reporter_id, reported_id, reason) VALUES (%s, %s, %s)",
        (user_id, target_id, message.text.strip())
    )
    await message.answer("✅ گزارش ثبت شد! ادمین بررسی می‌کنه.", reply_markup=main_menu_kb())
    await state.clear()


@router.callback_query(F.data == "back_to_explore")
async def back_to_explore(callback: CallbackQuery, state: FSMContext):
    # Get current browsing profile from state
    data = await state.get_data()
    profile_id = data.get('current_profile_id')
    if profile_id:
        user = await db.get_user(callback.from_user.id)
        from bot.keyboards.main_kb import profile_action_kb
        await callback.message.edit_reply_markup(
            reply_markup=profile_action_kb(profile_id, user.get('is_premium', False))
        )
    await callback.answer()


@router.callback_query(F.data == "exit_explore")
async def exit_explore(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("🏠 برگشتی به منو!", reply_markup=main_menu_kb())
    await callback.answer()


# ============ BACK TO MENU ============

@router.message(F.text == "🏠 بازگشت به منو")
async def back_to_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 منوی اصلی", reply_markup=main_menu_kb())
