from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.database import db
from bot.states.registration import Chat
from bot.keyboards.main_kb import chat_partner_kb, main_menu_kb

router = Router()


# ============ VIEW MATCHES ============

@router.message(F.text == "💑 جفت‌شده‌ها")
async def view_matches(message: Message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)

    if not user or not user['is_verified']:
        await message.answer("❌ ابتدا ثبت‌نامت رو تکمیل کن.")
        return

    matches = await db.get_matches(user_id)

    if not matches:
        await message.answer("😔 هنوز جفتی نداری!\nبرو جستجو کن و لایک بزن.")
        return

    text = "💑 جفت‌شده‌های تو:\n\n"
    for i, match in enumerate(matches, 1):
        text += f"{i}. {match['name']} | {match['age']} ساله | {match['city']}\n"

    await message.answer(text)

    # Send each match with chat button
    for match in matches:
        photos = await db.get_photos(match['id'])
        match_text = f"👤 {match['name']} | 🎂 {match['age']} ساله\n📍 {match['city']}"

        if photos:
            await message.answer_photo(
                photos[0]['file_id'],
                caption=match_text,
                reply_markup=chat_partner_kb(match['id'])
            )
        else:
            await message.answer(match_text, reply_markup=chat_partner_kb(match['id']))


# ============ START CHAT ============

@router.callback_query(F.data.startswith("start_chat_"))
async def start_chat(callback: CallbackQuery, state: FSMContext):
    partner_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id

    # Verify match exists
    is_match = await db.check_match(user_id, partner_id)
    if not is_match:
        await callback.answer("❌ این کاربر جفت شما نیست!", show_alert=True)
        return

    partner = await db.get_user(partner_id)
    await state.update_data(chat_partner=partner_id)
    await state.set_state(Chat.chatting)

    await callback.message.answer(
        f"💬 چت با {partner['name']} شروع شد!\n\n"
        f"پیامت رو بنویس. برای خروج /end_chat رو بفرست."
    )
    await callback.answer()


# ============ CHATTING ============

@router.message(Chat.chatting)
async def process_chat_message(message: Message, state: FSMContext):
    if message.text == "/end_chat":
        await state.clear()
        await message.answer("💬 چت تموم شد!", reply_markup=main_menu_kb())
        return

    data = await state.get_data()
    partner_id = data.get('chat_partner')

    if not partner_id:
        await state.clear()
        return

    user_id = message.from_user.id
    sender = await db.get_user(user_id)

    # Save message
    msg_type = 'text'
    file_id = None
    text = message.text or ""

    if message.photo:
        msg_type = 'photo'
        file_id = message.photo[-1].file_id
        text = message.caption or ""
    elif message.voice:
        msg_type = 'voice'
        file_id = message.voice.file_id
    elif message.sticker:
        msg_type = 'sticker'
        file_id = message.sticker.file_id

    await db.send_message(user_id, partner_id, text, msg_type, file_id)

    # Forward to partner
    try:
        if msg_type == 'text':
            await message.bot.send_message(
                partner_id,
                f"💬 {sender['name']}:\n{text}"
            )
        elif msg_type == 'photo':
            await message.bot.send_photo(
                partner_id, file_id,
                caption=f"💬 {sender['name']}:\n{text}"
            )
        elif msg_type == 'voice':
            await message.bot.send_voice(
                partner_id, file_id,
                caption=f"🎤 {sender['name']}"
            )
        elif msg_type == 'sticker':
            await message.bot.send_message(partner_id, f"💬 {sender['name']} استیکر فرستاد:")
            await message.bot.send_sticker(partner_id, file_id)
    except Exception:
        await message.answer("⚠️ ارسال پیام با مشکل مواجه شد. شاید کاربر ربات رو بلاک کرده.")


# ============ WHO LIKED ME ============

@router.message(F.text == "❤️ لایک‌های من")
async def view_who_liked_me(message: Message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)

    if not user or not user['is_verified']:
        await message.answer("❌ ابتدا ثبت‌نامت رو تکمیل کن.")
        return

    likers = await db.get_who_liked_me(user_id)

    if not likers:
        await message.answer("😔 هنوز کسی تو رو لایک نکرده!\nصبر کن یا پروفایلت رو بهتر کن.")
        return

    await message.answer(f"❤️ {len(likers)} نفر تو رو لایک کردن:")

    from bot.keyboards.main_kb import like_notification_kb

    for liker in likers:
        photos = await db.get_photos(liker['id'])
        text = f"👤 {liker['name']} | 🎂 {liker['age']} ساله\n📍 {liker['city']}"

        if photos:
            await message.answer_photo(
                photos[0]['file_id'],
                caption=text,
                reply_markup=like_notification_kb(liker['id'])
            )
        else:
            await message.answer(text, reply_markup=like_notification_kb(liker['id']))
