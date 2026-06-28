from aiogram import Router, F
from aiogram.types import Message

from bot.database import db

router = Router()


@router.message(F.text == "🎁 کسب درآمد")
async def view_referral(message: Message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    ref_count = await db.get_referral_count(user_id)

    bot_info = await message.bot.me()
    bot_username = bot_info.username
    invite_link = f"https://t.me/{bot_username}?start={user['referral_code']}"

    text = (
        f"🎁 کسب درآمد با دعوت دوستان\n"
        f"━━━━━━━━━━━━\n\n"
        f"🔗 لینک دعوت شما:\n{invite_link}\n\n"
        f"━━━━━━━━━━━━\n"
        f"👥 تعداد دعوت‌شده‌ها: {ref_count} نفر\n"
        f"💎 الماس کسب‌شده: {ref_count * 10} الماس\n\n"
        f"━━━━━━━━━━━━\n"
        f"📋 شرایط:\n"
        f"• با هر دعوت از دوستت: 10 الماس رایگان\n"
        f"• 10% از مبلغ خریدهای دوستت رو دریافت کنی\n\n"
        f"━━━━━━━━━━━━\n"
        f"📨 متن آماده برای ارسال:\n\n"
        f"سلام! بیا تو ربات دوست‌یابی ایزی‌چت 💕\n"
        f"ثبت‌نام کن و شروع کن به آشنا شدن با آدمای جدید!\n"
        f"🎁 با ثبت‌نام از لینک من 2 الماس هدیه بگیر:\n"
        f"{invite_link}"
    )

    await message.answer(text)
