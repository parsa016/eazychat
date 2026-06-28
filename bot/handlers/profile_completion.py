from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.database import db
from bot.states.registration import Registration
from bot.keyboards.main_kb import interests_kb, main_menu_kb

router = Router()


# ============ PURPOSE ============

@router.callback_query(F.data.startswith("purpose_"))
async def process_purpose(callback: CallbackQuery, state: FSMContext):
    purpose = callback.data.split("_")[1]  # dating, fun, marriage
    await db.update_user(callback.from_user.id, purpose=purpose, registration_step='interests')

    purpose_text = {
        'dating': '💕 دوست‌یابی',
        'fun': '🎉 سرگرمی',
        'marriage': '💍 همسریابی'
    }

    await callback.message.edit_text(f"✅ هدف: {purpose_text.get(purpose, purpose)}")
    await state.update_data(selected_interests=[])
    await callback.message.answer(
        "💡 حالا علاقه‌مندی‌هات رو انتخاب کن.\n"
        "حداکثر ۵ تا می‌تونی انتخاب کنی.\n"
        "بعد از انتخاب، «تایید و ادامه» رو بزن.",
        reply_markup=interests_kb()
    )
    await state.set_state(Registration.interests)


# ============ INTERESTS ============

@router.callback_query(Registration.interests, F.data.startswith("interest_"))
async def process_interest_select(callback: CallbackQuery, state: FSMContext):
    interest = callback.data.replace("interest_", "")
    data = await state.get_data()
    selected = data.get('selected_interests', [])

    if interest in selected:
        selected.remove(interest)
    else:
        if len(selected) >= 5:
            await callback.answer("❌ حداکثر ۵ علاقه‌مندی می‌تونی انتخاب کنی!", show_alert=True)
            return
        selected.append(interest)

    await state.update_data(selected_interests=selected)
    await callback.message.edit_reply_markup(reply_markup=interests_kb(selected))
    await callback.answer(f"انتخاب شده: {len(selected)}/5")


@router.callback_query(Registration.interests, F.data == "interests_done")
async def process_interests_done(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get('selected_interests', [])

    if not selected:
        await callback.answer("❌ حداقل یه علاقه‌مندی انتخاب کن!", show_alert=True)
        return

    # Save interests to DB
    user_id = callback.from_user.id
    await db.delete_interests(user_id)
    for interest in selected:
        await db.add_interest(user_id, interest)

    await db.update_user(user_id, registration_step='completed')

    await callback.message.edit_text("✅ علاقه‌مندی‌ها ثبت شدن!")
    await callback.message.answer(
        "🎉 تبریک! پروفایلت تکمیل شد!\n\n"
        "حالا می‌تونی از منوی اصلی استفاده کنی:",
        reply_markup=main_menu_kb()
    )
    await state.clear()
