from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.database import db
from bot.states.registration import Chat
from bot.keyboards.main_kb import (
    match_profile_kb, main_menu_kb, chat_request_kb, like_notification_kb
)
from config import CHAT_REQUEST_COST, DIRECT_MESSAGE_COST

router = Router()


# ============ VIEW MATCHES ============

@router.message(F.text == "💑 جفت‌شده‌ها")
async def view_matches(message: Message):
    user_id = message.from_user.id
    matches = await db.get_matches(user_id)

    if not matches:
        await message.answer("😔 هنوز کسی باهات جفت نشده!\nبرو جستجو کن و لایک بده 💕")
        return

    await message.answer(f"💑 جفت‌شده‌های تو ({len(matches)} نفر):")
    for match in matches[:10]:
        photos = await db.get_photos(match['id'])
        text = f"👤 {match['name']} | 🎂 {match['age']} ساله\n📍 {match['province']}، {match['city']}"
        if match.get('bio'):
            text += f"\n📝 {match['bio']}"

        if photos:
            await message.answer_photo(
                photos[0]['file_id'],
                caption=text,
                reply_markup=match_profile_kb(match['id'])
            )
        else:
            await message.answer(text, reply_markup=match_profile_kb(match['id']))


# ============ VIEW WHO LIKED ME ============

@router.message(F.text == "❤️ لایک‌های من")
async def view_likes(message: Message):
    user_id = message.from_user.id
    likers = await db.get_who_liked_me(user_id)

    if not likers:
        await message.answer("😔 هنوز کسی تو رو لایک نکرده!\nبرو جستجو کن تا دیده بشی.")
        return

    await message.answer(f"❤️ افرادی که تو رو لایک کردن ({len(likers)} نفر):")
    for liker in likers[:10]:
        photos = await db.get_photos(liker['id'])
        text = f"👤 {liker['name']} | 🎂 {liker['age']} ساله\n📍 {liker['province']}، {liker['city']}"
        if liker.get('bio'):
            text += f"\n📝 {liker['bio']}"

        if photos:
            await message.answer_photo(
                photos[0]['file_id'],
                caption=text,
                reply_markup=like_notification_kb(liker['id'])
            )
        else:
            await message.answer(text, reply_markup=like_notification_kb(liker['id']))


# ============ CHAT REQUEST ============

@router.callback_query(F.data.startswith("chat_request_"))
async def send_chat_request(callback: CallbackQuery):
    partner_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    user = await db.get_user(user_id)

    # Check match
    is_matched = await db.check_match(user_id, partner_id)
    if not is_matched:
        await callback.answer("❌ این کاربر جفت‌شده‌ات نیست!", show_alert=True)
        return

    # Check if already has accepted chat
    already_chat = await db.check_chat_accepted(user_id, partner_id)
    if already_chat:
        await callback.answer("✅ چت قبلاً قبول شده! می‌تونی پیام بدی.", show_alert=True)
        return

    # Spend diamonds
    success = await db.spend_diamonds(user_id, CHAT_REQUEST_COST, "درخواست چت")
    if not success:
        await callback.answer(
            f"❌ الماس کافی نداری! ({CHAT_REQUEST_COST} الماس لازمه)\nموجودی: {user['diamonds']} 💎",
            show_alert=True
        )
        return

    request_id = await db.create_chat_request(user_id, partner_id)

    # Notify partner
    try:
        await callback.bot.send_message(
            partner_id,
            f"💬 {user['name']} درخواست چت داده!\nقبول می‌کنی؟",
            reply_markup=chat_request_kb(user_id, request_id)
        )
    except Exception:
        pass

    await callback.answer("✅ درخواست چت ارسال شد! منتظر پاسخ باش.", show_alert=True)


# ============ ACCEPT/DECLINE CHAT ============

@router.callback_query(F.data.startswith("accept_chat_"))
async def accept_chat(callback: CallbackQuery):
    parts = callback.data.split("_")
    request_id = int(parts[2])
    from_user_id = int(parts[3])
    user_id = callback.from_user.id

    await db.update_chat_request(request_id, 'accepted')

    await callback.message.edit_text("✅ درخواست چت قبول شد!\nحالا می‌تونید باهم چت کنید.")

    # Notify sender
    try:
        user = await db.get_user(user_id)
        await callback.bot.send_message(
            from_user_id,
            f"🎉 {user['name']} درخواست چتت رو قبول کرد!\nبرو بخش «جفت‌شده‌ها» و بهش پیام بده."
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("decline_chat_"))
async def decline_chat(callback: CallbackQuery):
    parts = callback.data.split("_")
    request_id = int(parts[2])
    from_user_id = int(parts[3])

    await db.update_chat_request(request_id, 'rejected')
    await callback.message.edit_text("❌ درخواست چت رد شد.")

    try:
        user = await db.get_user(callback.from_user.id)
        await callback.bot.send_message(
            from_user_id,
            f"😔 {user['name']} درخواست چتت رو رد کرد."
        )
    except Exception:
        pass


# ============ MATCH DIRECT MESSAGE ============

@router.callback_query(F.data.startswith("match_direct_"))
async def match_direct(callback: CallbackQuery, state: FSMContext):
    partner_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    user = await db.get_user(user_id)

    if user['diamonds'] < DIRECT_MESSAGE_COST:
        await callback.answer(
            f"❌ الماس کافی نداری! ({DIRECT_MESSAGE_COST} الماس لازمه)",
            show_alert=True
        )
        return

    await state.update_data(match_direct_target=partner_id)
    await state.set_state(Chat.match_direct)
    await callback.message.answer(
        f"✉️ پیامت رو بنویس ({DIRECT_MESSAGE_COST} 💎):\nبرای لغو /cancel بفرست."
    )
    await callback.answer()


@router.message(Chat.match_direct)
async def send_match_direct(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ لغو شد.", reply_markup=main_menu_kb())
        return

    data = await state.get_data()
    target_id = data['match_direct_target']
    user_id = message.from_user.id

    success = await db.spend_diamonds(user_id, DIRECT_MESSAGE_COST, "دایرکت به جفت‌شده")
    if not success:
        await message.answer("❌ الماس کافی نداری!")
        await state.clear()
        return

    await db.send_direct_message(user_id, target_id, message.text, DIRECT_MESSAGE_COST)

    # Notify target
    try:
        sender = await db.get_user(user_id)
        await message.bot.send_message(
            target_id,
            f"✉️ پیام از {sender['name']}:\n\n{message.text}"
        )
    except Exception:
        pass

    await message.answer("✅ پیام ارسال شد!", reply_markup=main_menu_kb())
    await state.clear()


# ============ UNMATCH ============

@router.callback_query(F.data.startswith("unmatch_"))
async def process_unmatch(callback: CallbackQuery):
    partner_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    await db.unmatch(user_id, partner_id)

    try:
        await callback.message.edit_caption(caption="💔 آن‌مچ شد.")
    except Exception:
        await callback.message.edit_text("💔 آن‌مچ شد.")

    await callback.answer("💔 آن‌مچ شد!", show_alert=True)
