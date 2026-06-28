from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.database import db
from bot.states.registration import Profile, Registration
from bot.keyboards.main_kb import my_profile_kb, main_menu_kb, diamonds_kb, verification_optional_kb
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
    interests = await db.get_interests(user_id)

    gender_text = "👨 مرد" if user['gender'] == 'male' else "👩 زن"
    purpose_map = {'dating': '💕 دوست‌یابی', 'fun': '🎉 سرگرمی', 'marriage': '💍 همسریابی'}
    interest_map = {
        'coffee': '☕ قهوه', 'tea': '🍵 چای', 'smoking': '🚬 سیگار',
        'alcohol': '🍷 مشروب', 'sports': '🏋️ ورزش', 'gaming': '🎮 گیمینگ',
        'reading': '📚 کتاب‌خوانی', 'music': '🎵 موسیقی', 'movies': '🎬 فیلم',
        'travel': '✈️ سفر', 'cooking': '🍳 آشپزی', 'photography': '📸 عکاسی'
    }

    # Stats
    views_r, likes_r, attract_pct = await db.get_attractiveness(user_id)
    views_s, likes_s, picky_pct = await db.get_pickiness(user_id)

    verified_badge = " ✅" if user['is_verified'] else ""
    text = (
        f"{'✅' if user['is_verified'] else '😶'} {user['name']} ({user['age']}) | {gender_text}{verified_badge}\n"
        f"📍 {user['province']} - {user['city']}\n"
    )
    if user.get('bio'):
        text += f"📝 {user['bio']}\n"

    text += f"\n🎯 {purpose_map.get(user.get('purpose'), '—')}\n"

    if interests:
        interests_text = " | ".join(interest_map.get(i, i) for i in interests)
        text += f"💡 {interests_text}\n"

    text += (
        f"\n━━━━━━━━━━━━\n"
        f"💎 الماس: {user['diamonds']}\n"
        f"⭐ پرمیوم: {'فعال' if user['is_premium'] else 'غیرفعال'}\n"
        f"\n📊 آمار:\n"
        f"✨ جذابیت: از {views_r} نفر، {likes_r} نفر ({attract_pct}%) لایکت کردن\n"
        f"🎯 سخت‌پسندی: از {views_s} نفر، {likes_s} نفر ({picky_pct}%) رو لایک کردی\n"
    )

    if photos:
        await message.answer_photo(
            photos[0]['file_id'],
            caption=text,
            reply_markup=my_profile_kb(user['is_verified'])
        )
    else:
        await message.answer(text, reply_markup=my_profile_kb(user['is_verified']))


# ============ START VERIFICATION FROM PROFILE ============

@router.callback_query(F.data == "start_verification")
async def start_verification_from_profile(callback: CallbackQuery, state: FSMContext):
    user = await db.get_user(callback.from_user.id)
    if user and user['is_verified']:
        await callback.answer("✅ قبلاً احراز هویت کردی!", show_alert=True)
        return
    await state.set_state(Registration.verification_video)
    await callback.message.answer(
        "🎥 یه ویدیو مسیج بفرست و توش بگو:\n\n"
        "«احراز هویت در ربات ایزی‌چت»\n\n"
        "⚠️ صورتت باید مشخص باشه و شبیه عکس پروفایلت باشه."
    )
    await callback.answer()


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
    await callback.message.answer(
        "💡 علاقه‌مندی‌های جدیدت رو انتخاب کن:",
        reply_markup=interests_kb()
    )
    await callback.answer()


# ============ DIAMONDS ============

@router.message(F.text == "💎 الماس‌ها")
async def view_diamonds(message: Message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    streak = user['streak_days']

    text = (
        f"💎 الماس‌های من: {user['diamonds']}\n"
        f"🔥 روزهای متوالی: {streak} روز\n\n"
        f"━━━━━━━━━━━━\n"
        f"🎁 جایزه 3 روز: {'✅ دریافت شده' if user['streak_3_claimed'] else '❌ ' + ('آماده!' if streak >= 3 else f'{3-streak} روز مونده')}\n"
        f"🎁 جایزه 7 روز: {'✅ دریافت شده' if user['streak_7_claimed'] else '❌ ' + ('آماده!' if streak >= 7 else f'{7-streak} روز مونده')}\n"
        f"🎁 جایزه 30 روز: {'✅ دریافت شده' if user['streak_30_claimed'] else '❌ ' + ('آماده!' if streak >= 30 else f'{30-streak} روز مونده')}\n"
    )

    await message.answer(text, reply_markup=diamonds_kb())


# ============ DAILY DIAMOND ============

@router.callback_query(F.data == "daily_diamond")
async def claim_daily(callback: CallbackQuery):
    success = await db.claim_daily_diamond(callback.from_user.id)
    if success:
        await callback.answer("🎁 1 الماس رایگان دریافت کردی!", show_alert=True)
    else:
        await callback.answer("❌ امروز قبلاً دریافت کردی! فردا بیا.", show_alert=True)


# ============ STREAK REWARDS ============

@router.callback_query(F.data.startswith("streak_"))
async def claim_streak(callback: CallbackQuery):
    streak_type = callback.data.replace("streak_", "")
    success, msg = await db.claim_streak_reward(callback.from_user.id, streak_type)
    await callback.answer(msg, show_alert=True)


# ============ BUY DIAMONDS ============

@router.callback_query(F.data == "buy_diamonds")
async def buy_diamonds(callback: CallbackQuery):
    text = (
        "🛒 خرید الماس:\n\n"
        "برای خرید الماس با پشتیبانی تماس بگیر.\n"
        "از منوی اصلی «📞 پشتیبانی» رو بزن."
    )
    await callback.answer(text, show_alert=True)


# ============ PREMIUM ============

@router.message(F.text == "⭐ اشتراک پرمیوم")
async def view_premium(message: Message):
    user = await db.get_user(message.from_user.id)
    status = "✅ فعال" if user['is_premium'] else "❌ غیرفعال"
    text = (
        f"⭐ اشتراک پرمیوم: {status}\n\n"
        f"مزایای پرمیوم:\n"
        f"• جستجوی نامحدود (بدون محدودیت روزانه)\n"
        f"• لایک نامحدود\n"
        f"• دکمه بازگشت در اکسپلور\n\n"
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

    # Forward to all admins
    for admin_id in ADMIN_IDS:
        try:
            await message.bot.send_message(
                admin_id,
                f"📞 پیام پشتیبانی جدید:\n\n"
                f"👤 {user['name']} (ID: {user_id})\n"
                f"📝 {message.text}\n\n"
                f"برای پاسخ:\n/reply {user_id} متن پاسخ"
            )
        except Exception:
            pass

    await message.answer("✅ پیامت ارسال شد! ادمین بهت جواب میده.", reply_markup=main_menu_kb())
    await state.clear()


# ============ BACK TO MENU ============

@router.message(F.text == "🏠 بازگشت به منو")
async def back_to_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 منوی اصلی", reply_markup=main_menu_kb())
