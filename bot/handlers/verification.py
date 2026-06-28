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


# ============ START VERIFICATION (from profile or registration) ============

@router.callback_query(F.data == "start_verification")
async def start_verification(callback: CallbackQuery, state: FSMContext):
    try:
        user_id = callback.from_user.id
        user = await db.get_user(user_id)

        # Already verified
        if user and user.get('is_verified'):
            await callback.answer("✅ قبلاً احراز هویت کردی!", show_alert=True)
            return

        # Check pending
        pending = await db.fetchone(
            "SELECT id FROM verifications WHERE user_id = %s AND status = 'pending'",
            (user_id,)
        )
        if pending:
            await callback.answer("⏳ درخواست قبلیت هنوز در حال بررسیه! صبر کن.", show_alert=True)
            return

        await state.set_state(Registration.verification_video)
        await callback.message.answer(
            "🎥 یه ویدیو مسیج بفرست و توش بگو:\n\n"
            "«احراز هویت در ربات ایزی‌چت»\n\n"
            "⚠️ صورتت باید مشخص باشه و شبیه عکس پروفایلت باشه."
        )
        await callback.answer()
    except Exception as e:
        try:
            await callback.message.answer(f"❌ خطایی رخ داد! دوباره تلاش کنید.")
            await callback.answer()
        except Exception:
            pass


# ============ SKIP VERIFICATION ============

@router.callback_query(F.data == "skip_verification")
async def skip_verification(callback: CallbackQuery, state: FSMContext):
    await db.update_user(callback.from_user.id, registration_step='purpose')
    try:
        await callback.message.edit_text(
            "⏭️ احراز هویت رد شد.\n"
            "⚠️ بدون احراز هویت نمی‌تونی لایک‌ها و مچ‌هات رو ببینی.\n"
            "هر وقت خواستی از بخش پروفایل می‌تونی انجام بدی.\n\n"
            "🎯 حالا هدفت از اومدن تو ربات رو انتخاب کن:",
            reply_markup=purpose_kb()
        )
    except Exception:
        await callback.message.answer(
            "⏭️ احراز هویت رد شد.\n"
            "⚠️ بدون احراز هویت نمی‌تونی لایک‌ها و مچ‌هات رو ببینی.\n\n"
            "🎯 حالا هدفت از اومدن تو ربات رو انتخاب کن:",
            reply_markup=purpose_kb()
        )
    await state.clear()


# ============ VERIFICATION VIDEO (single handler, no filter) ============

@router.message(Registration.verification_video)
async def process_verification_video(message: Message, state: FSMContext):
    """Handle ALL messages in verification_video state - check content type manually."""
    user_id = message.from_user.id

    # Check if it's a video or video_note
    file_id = None
    is_video = False
    if message.video:
        file_id = message.video.file_id
        is_video = True
    elif message.video_note:
        file_id = message.video_note.file_id
        is_video = False

    if not file_id:
        await message.answer(
            "❌ لطفاً یه ویدیو مسیج (دایره‌ای) یا ویدیو معمولی بفرست!\n"
            "⚠️ فقط فرمت ویدیو قبول می‌شه (عکس، متن و فایل قبول نیست)."
        )
        return

    # Check pending
    pending = await db.fetchone(
        "SELECT id FROM verifications WHERE user_id = %s AND status = 'pending'",
        (user_id,)
    )
    if pending:
        await message.answer(
            "⏳ درخواست قبلیت هنوز در حال بررسیه! صبر کن.",
            reply_markup=main_menu_kb()
        )
        await state.clear()
        return

    try:
        verification_id = await db.create_verification(user_id, file_id)
    except Exception:
        await message.answer(
            "❌ خطایی رخ داد! دوباره تلاش کنید.",
            reply_markup=main_menu_kb()
        )
        await state.clear()
        return

    # Check if user is in first registration or verifying from profile
    user_before = await db.get_user(user_id)
    if user_before and user_before.get('registration_step') == 'verification_video':
        # First registration — move to purpose step
        await db.update_user(user_id, registration_step='purpose')
    else:
        # From profile — keep completed
        await db.update_user(user_id, registration_step='completed')

    # Send to verification group or admins
    user = await db.get_user(user_id)
    photos = await db.get_photos(user_id)
    text = (
        f"🔍 درخواست احراز هویت جدید:\n\n"
        f"👤 نام: {user['name']}\n"
        f"🆔 ID: {user_id}\n"
        f"📱 شماره: {user.get('phone') or 'ندارد'}\n"
        f"🎂 سن: {user['age']}\n"
        f"👤 جنسیت: {'مرد' if user['gender'] == 'male' else 'زن'}\n"
        f"📍 {user['province']}، {user['city']}"
    )

    target = VERIFICATION_GROUP_ID if VERIFICATION_GROUP_ID else None

    try:
        if target:
            # Send photos to group
            if photos:
                for photo in photos[:3]:
                    try:
                        await message.bot.send_photo(target, photo['file_id'])
                    except Exception:
                        pass

            # Send info text
            await message.bot.send_message(target, text)

            # Send video with admin buttons
            if is_video:
                await message.bot.send_video(
                    target, file_id,
                    caption="🎥 ویدیو احراز هویت 👆",
                    reply_markup=verification_admin_kb(user_id, verification_id)
                )
            else:
                await message.bot.send_video_note(target, file_id)
                await message.bot.send_message(
                    target,
                    "🎥 ویدیو احراز هویت 👆",
                    reply_markup=verification_admin_kb(user_id, verification_id)
                )
        else:
            for admin_id in ADMIN_IDS:
                try:
                    if photos:
                        for photo in photos[:3]:
                            await message.bot.send_photo(admin_id, photo['file_id'])
                    await message.bot.send_message(admin_id, text)
                    if is_video:
                        await message.bot.send_video(
                            admin_id, file_id,
                            caption="🎥 ویدیو احراز هویت 👆",
                            reply_markup=verification_admin_kb(user_id, verification_id)
                        )
                    else:
                        await message.bot.send_video_note(admin_id, file_id)
                        await message.bot.send_message(
                            admin_id,
                            "🎥 ویدیو احراز هویت 👆",
                            reply_markup=verification_admin_kb(user_id, verification_id)
                        )
                except Exception:
                    pass
    except Exception:
        pass

    # Check if first registration (needs purpose step)
    user_after = await db.get_user(user_id)
    if user_after and user_after.get('registration_step') == 'purpose':
        await message.answer(
            "✅ درخواست احراز هویتت ثبت شد!\n"
            "⏳ منتظر بررسی ادمین باش.\n\n"
            "🎯 حالا هدفت از اومدن تو ربات رو انتخاب کن:",
            reply_markup=purpose_kb()
        )
    else:
        await message.answer(
            "✅ درخواست احراز هویتت ثبت شد!\n"
            "⏳ منتظر بررسی ادمین باش. بعد از تأیید بهت اطلاع میدیم.\n\n"
            "می‌تونی از ربات استفاده کنی 👇",
            reply_markup=main_menu_kb()
        )
    await state.clear()
