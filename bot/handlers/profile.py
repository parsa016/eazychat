from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.database import db
from bot.keyboards.main_kb import my_profile_kb, main_menu_kb

router = Router()


@router.message(F.text == "👤 پروفایل من")
async def view_profile(message: Message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)

    if not user:
        await message.answer("❌ ابتدا /start رو بزن.")
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

    verified_text = "✅ تأیید شده" if user['is_verified'] else "⏳ در انتظار تأیید"
    premium_text = "⭐ پرمیوم" if user['is_premium'] else "رایگان"

    text = (
        f"👤 پروفایل من:\n\n"
        f"📛 نام: {user['name']}\n"
        f"{gender_text} | 🎂 {user['age']} ساله\n"
        f"📍 {user['province']}، {user['city']}\n"
        f"🎯 هدف: {purpose_map.get(user['purpose'], 'تعیین نشده')}\n"
        f"💰 سکه: {user['coins']}\n"
        f"📋 وضعیت: {verified_text}\n"
        f"💎 اشتراک: {premium_text}\n"
    )

    if interests:
        interests_text = " | ".join(interest_map.get(i, i) for i in interests)
        text += f"💡 علاقه‌مندی‌ها: {interests_text}\n"

    if photos:
        await message.answer_photo(
            photos[0]['file_id'],
            caption=text,
            reply_markup=my_profile_kb()
        )
    else:
        await message.answer(text, reply_markup=my_profile_kb())


@router.message(F.text == "💰 سکه‌ها")
async def view_coins(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        return

    await message.answer(
        f"💰 موجودی سکه: {user['coins']}\n\n"
        f"📌 نرخ‌ها:\n"
        f"• ارسال دایرکت: 2 سکه\n\n"
        f"برای خرید سکه با پشتیبانی تماس بگیر."
    )


@router.message(F.text == "⭐ اشتراک پرمیوم")
async def view_premium(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        return

    if user['is_premium']:
        await message.answer(
            "⭐ تو اشتراک پرمیوم داری!\n\n"
            "مزایا:\n"
            "• مشاهده نامحدود پروفایل\n"
            "• لایک نامحدود\n"
            "• مشاهده کسایی که لایکت کردن"
        )
    else:
        await message.answer(
            "⭐ اشتراک پرمیوم:\n\n"
            "مزایا:\n"
            "• مشاهده نامحدود پروفایل\n"
            "• لایک نامحدود\n"
            "• مشاهده کسایی که لایکت کردن\n\n"
            "📌 پلن‌ها:\n"
            "• هفتگی: تماس با پشتیبانی\n"
            "• ماهانه: تماس با پشتیبانی\n"
            "• ۳ ماهه: تماس با پشتیبانی\n\n"
            "برای خرید با پشتیبانی تماس بگیر."
        )


@router.message(F.text == "📞 پشتیبانی")
async def support(message: Message):
    await message.answer(
        "📞 پشتیبانی ایزی‌چت:\n\n"
        "برای ارتباط با پشتیبانی:\n"
        "• مشکل فنی\n"
        "• گزارش تخلف\n"
        "• خرید سکه و اشتراک\n\n"
        "پیامت رو اینجا بنویس و ادمین بهت جواب میده."
    )


@router.message(F.text == "🏠 بازگشت به منو")
async def back_to_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 منوی اصلی:", reply_markup=main_menu_kb())
