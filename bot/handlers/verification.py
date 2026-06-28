from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from bot.database import db
from bot.states.registration import Admin, Registration
from bot.keyboards.main_kb import verification_admin_kb, purpose_kb, main_menu_kb
from config import ADMIN_IDS, VERIFICATION_GROUP_ID

router = Router()


@router.callback_query(F.data.startswith("verify_approve_"))
async def approve_verification(callback: CallbackQuery):
    parts = callback.data.split("_")
    verification_id = int(parts[2])
    user_id = int(parts[3])

    # Check admin
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ فقط ادمین‌ها دسترسی دارن!", show_alert=True)
        return

    await db.update_verification(verification_id, 'approved', callback.from_user.id)

    # Check user step - if waiting_verification, move to purpose
    user = await db.get_user(user_id)
    if user and user['registration_step'] == 'waiting_verification':
        await db.update_user(user_id, is_verified=1, registration_step='purpose')
        try:
            await callback.bot.send_message(
                user_id,
                "🎉 احراز هویتت تأیید شد! ✅\n\nحالا هدفت از اومدن تو ربات رو انتخاب کن:",
                reply_markup=purpose_kb()
            )
        except Exception:
            pass
    else:
        await db.update_user(user_id, is_verified=1)
        try:
            await callback.bot.send_message(
                user_id,
                "🎉 احراز هویتت تأیید شد! ✅\nحالا کنار اسمت تیک سبز نمایش داده میشه.",
                reply_markup=main_menu_kb()
            )
        except Exception:
            pass

    try:
        await callback.message.edit_caption(
            caption=f"✅ تأیید شد توسط {callback.from_user.full_name}"
        )
    except Exception:
        try:
            await callback.message.edit_text(
                f"✅ تأیید شد توسط {callback.from_user.full_name}"
            )
        except Exception:
            pass

    await callback.answer("✅ تأیید شد!")


@router.callback_query(F.data.startswith("verify_reject_"))
async def reject_verification(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    verification_id = int(parts[2])
    user_id = int(parts[3])

    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ فقط ادمین‌ها دسترسی دارن!", show_alert=True)
        return

    await state.update_data(reject_verification_id=verification_id, reject_user_id=user_id)
    await state.set_state(Admin.rejection_reason)

    await callback.message.reply(
        "📝 دلیل رد رو بنویس:\n(یا /skip برای رد بدون دلیل)"
    )
    await callback.answer()


@router.message(Admin.rejection_reason)
async def process_rejection_reason(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return

    data = await state.get_data()
    verification_id = data['reject_verification_id']
    user_id = data['reject_user_id']

    reason = None if message.text == "/skip" else message.text

    await db.update_verification(verification_id, 'rejected', message.from_user.id, reason)
    await db.update_user(user_id, registration_step='verification_video')

    # Notify user
    try:
        reject_text = "❌ احراز هویتت رد شد.\n"
        if reason:
            reject_text += f"📝 دلیل: {reason}\n"
        reject_text += "\nلطفاً دوباره ویدیو مسیج بفرست."
        await message.bot.send_message(user_id, reject_text)
    except Exception:
        pass

    await message.answer("✅ رد شد. کاربر مطلع شد.")
    await state.clear()
