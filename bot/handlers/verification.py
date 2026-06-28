from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.database import db
from bot.keyboards.main_kb import purpose_kb
from bot.states.registration import Registration
from config import ADMIN_IDS

router = Router()


@router.callback_query(F.data.startswith("verify_approve_"))
async def verify_approve(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ شما ادمین نیستید!", show_alert=True)
        return

    parts = callback.data.split("_")
    verification_id = int(parts[2])
    user_id = int(parts[3])

    await db.update_verification(verification_id, 'approved', callback.from_user.id)
    await db.update_user(user_id, is_verified=1, registration_step='purpose')

    await callback.message.edit_text("✅ احراز هویت تأیید شد!")

    # Notify user
    try:
        await callback.bot.send_message(
            user_id,
            "🎉 احراز هویتت تأیید شد!\n\n"
            "حالا بیا پروفایلت رو تکمیل کنیم.\n"
            "🎯 هدفت از اومدن به ربات چیه؟",
            reply_markup=purpose_kb()
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("verify_reject_"))
async def verify_reject(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ شما ادمین نیستید!", show_alert=True)
        return

    parts = callback.data.split("_")
    verification_id = int(parts[2])
    user_id = int(parts[3])

    await db.update_verification(verification_id, 'rejected', callback.from_user.id)
    await db.update_user(user_id, registration_step='verification')

    await callback.message.edit_text("❌ احراز هویت رد شد!")

    # Notify user
    try:
        await callback.bot.send_message(
            user_id,
            "❌ متأسفانه احراز هویتت رد شد.\n\n"
            "دلایل احتمالی:\n"
            "- عکس پروفایل با ویدیو مطابقت نداره\n"
            "- متن احراز هویت درست گفته نشده\n\n"
            "لطفاً دوباره یه ویدیو مسیج بفرست و بگو:\n"
            "«احراز هویت در ربات ایزی‌چت»"
        )
    except Exception:
        pass
