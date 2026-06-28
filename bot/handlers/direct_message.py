from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from bot.database import db
from bot.states.registration import Chat
from config import DIRECT_MESSAGE_COST

router = Router()


@router.callback_query(F.data.startswith("direct_"))
async def process_direct_start(callback: CallbackQuery, state: FSMContext):
    target_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    user = await db.get_user(user_id)
    if user['coins'] < DIRECT_MESSAGE_COST:
        await callback.answer(
            f"❌ سکه کافی نداری!\n"
            f"برای ارسال دایرکت {DIRECT_MESSAGE_COST} سکه نیاز داری.\n"
            f"موجودی: {user['coins']} سکه",
            show_alert=True
        )
        return

    await state.update_data(direct_target=target_id)
    await state.set_state(Chat.direct_message)
    await callback.message.answer(
        f"✉️ پیامت رو بنویس (هزینه: {DIRECT_MESSAGE_COST} سکه):\n"
        f"برای لغو /cancel رو بفرست."
    )
    await callback.answer()


@router.message(Chat.direct_message, F.text)
async def process_direct_send(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ لغو شد.")
        return

    data = await state.get_data()
    target_id = data.get('direct_target')
    user_id = message.from_user.id

    # Spend coins
    success = await db.spend_coins(user_id, DIRECT_MESSAGE_COST, "ارسال دایرکت")
    if not success:
        await message.answer("❌ سکه کافی نداری!")
        await state.clear()
        return

    # Save direct message
    await db.send_direct_message(user_id, target_id, message.text, DIRECT_MESSAGE_COST)

    # Send to target
    try:
        sender = await db.get_user(user_id)
        await message.bot.send_message(
            target_id,
            f"✉️ پیام مستقیم از {sender['name']}:\n\n"
            f"{message.text}"
        )
    except Exception:
        pass

    user = await db.get_user(user_id)
    await message.answer(
        f"✅ پیامت ارسال شد!\n"
        f"💰 موجودی: {user['coins']} سکه"
    )
    await state.clear()
