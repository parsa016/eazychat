from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from bot.database import db
from bot.states.registration import Registration
from bot.keyboards.main_kb import interests_kb, main_menu_kb
from config import PROFILE_COMPLETE_BONUS

router = Router()


# ============ PURPOSE ============

@router.callback_query(F.data.startswith("purpose_"))
async def process_purpose(callback: CallbackQuery, state: FSMContext):
    purpose = callback.data.replace("purpose_", "")
    await db.update_user(callback.from_user.id, purpose=purpose, registration_step='interests')
    await callback.message.edit_text(
        "💡 علاقه‌مندی‌هات رو انتخاب کن (حداکثر 5 تا):",
        reply_markup=interests_kb()
    )
    await state.update_data(selected_interests=[])


# ============ INTERESTS ============

@router.callback_query(F.data.startswith("interest_"))
async def process_interest(callback: CallbackQuery, state: FSMContext):
    interest = callback.data.replace("interest_", "")
    data = await state.get_data()
    selected = data.get('selected_interests', [])

    if interest in selected:
        selected.remove(interest)
    else:
        if len(selected) >= 5:
            await callback.answer("❌ حداکثر 5 علاقه‌مندی!", show_alert=True)
            return
        selected.append(interest)

    await state.update_data(selected_interests=selected)
    await callback.message.edit_reply_markup(reply_markup=interests_kb(selected))
    await callback.answer()


@router.callback_query(F.data == "interests_done")
async def interests_done(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get('selected_interests', [])

    if not selected:
        await callback.answer("❌ حداقل یه علاقه‌مندی انتخاب کن!", show_alert=True)
        return

    user_id = callback.from_user.id
    await db.delete_interests(user_id)
    for interest in selected:
        await db.add_interest(user_id, interest)

    await db.update_user(user_id, registration_step='bio')
    await callback.message.edit_text(
        "📝 یه بیوگرافی کوتاه از خودت بنویس (حداکثر 300 کاراکتر):\n\n"
        "یا /skip بزن اگه نمی‌خوای بیو بذاری."
    )
    await state.set_state(Registration.bio)


# ============ BIO ============

@router.message(Registration.bio)
async def process_bio(message: Message, state: FSMContext):
    user_id = message.from_user.id

    if message.text == "/skip":
        bio = None
    else:
        bio = message.text.strip()
        if len(bio) > 300:
            await message.answer("❌ بیو حداکثر 300 کاراکتر باشه!")
            return

    if bio:
        await db.update_user(user_id, bio=bio, registration_step='completed')
    else:
        await db.update_user(user_id, registration_step='completed')

    # Profile complete bonus
    await db.add_diamonds(user_id, PROFILE_COMPLETE_BONUS, 'profile_complete', 'جایزه تکمیل پروفایل')

    await message.answer(
        f"🎉 پروفایلت تکمیل شد!\n\n"
        f"🎁 {PROFILE_COMPLETE_BONUS} الماس جایزه تکمیل پروفایل دریافت کردی!\n\n"
        f"حالا می‌تونی از ربات استفاده کنی.",
        reply_markup=main_menu_kb()
    )
    await state.clear()
