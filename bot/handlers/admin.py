from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from bot.database import db
from config import ADMIN_IDS

router = Router()


@router.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    total = await db.fetchone("SELECT COUNT(*) as cnt FROM users")
    verified = await db.fetchone("SELECT COUNT(*) as cnt FROM users WHERE is_verified = 1")
    pending = await db.fetchone("SELECT COUNT(*) as cnt FROM verifications WHERE status = 'pending'")
    matches = await db.fetchone("SELECT COUNT(*) as cnt FROM matches WHERE is_active = 1")
    premium = await db.fetchone("SELECT COUNT(*) as cnt FROM users WHERE is_premium = 1")

    text = (
        f"⚙️ پنل ادمین\n"
        f"━━━━━━━━━━━━\n"
        f"👥 کل کاربران: {total['cnt']}\n"
        f"✅ تأیید شده: {verified['cnt']}\n"
        f"⏳ در انتظار تأیید: {pending['cnt']}\n"
        f"💑 جفت‌شده‌ها: {matches['cnt']}\n"
        f"⭐ پرمیوم: {premium['cnt']}\n"
        f"\n━━━━━━━━━━━━\n"
        f"دستورات:\n"
        f"/pending - درخواست‌های احراز هویت\n"
        f"/ban <user_id> - بن کردن\n"
        f"/unban <user_id> - آنبن\n"
        f"/adddiamonds <user_id> <amount> - اضافه کردن الماس\n"
        f"/setpremium <user_id> <days> - فعال‌سازی پرمیوم\n"
        f"/broadcast <message> - پیام همگانی\n"
        f"/reply <user_id> <message> - پاسخ به کاربر\n"
    )
    await message.answer(text)


@router.message(Command("pending"))
async def view_pending(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    pending = await db.get_pending_verifications()
    if not pending:
        await message.answer("✅ هیچ درخواست منتظری نیست!")
        return

    await message.answer(f"⏳ {len(pending)} درخواست در انتظار:")
    from bot.keyboards.main_kb import verification_admin_kb
    for v in pending[:10]:
        user = await db.get_user(v['user_id'])
        photos = await db.get_photos(v['user_id'])
        text = f"👤 {user['name']} | ID: {v['user_id']}\n🎂 {user['age']} | 📍 {user['province']}"

        if photos:
            await message.answer_photo(photos[0]['file_id'], caption=text)
        try:
            await message.bot.send_video(
                message.chat.id, v['video_file_id'],
                caption="ویدیو احراز هویت 👆",
                reply_markup=verification_admin_kb(v['user_id'], v['id'])
            )
        except Exception:
            await message.answer(
                f"ویدیو (video_note)\nکاربر: {v['user_id']}",
                reply_markup=verification_admin_kb(v['user_id'], v['id'])
            )


@router.message(Command("ban"))
async def ban_user(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ فرمت: /ban <user_id>")
        return
    try:
        user_id = int(args[1])
    except ValueError:
        await message.answer("❌ آیدی نامعتبر!")
        return
    await db.update_user(user_id, is_banned=1, is_active=0)
    await message.answer(f"✅ کاربر {user_id} بن شد.")


@router.message(Command("unban"))
async def unban_user(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ فرمت: /unban <user_id>")
        return
    try:
        user_id = int(args[1])
    except ValueError:
        await message.answer("❌ آیدی نامعتبر!")
        return
    await db.update_user(user_id, is_banned=0, is_active=1)
    await message.answer(f"✅ کاربر {user_id} آنبن شد.")


@router.message(Command("adddiamonds"))
async def add_diamonds(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    args = message.text.split()
    if len(args) < 3:
        await message.answer("❌ فرمت: /adddiamonds <user_id> <amount>")
        return
    try:
        user_id = int(args[1])
        amount = int(args[2])
    except ValueError:
        await message.answer("❌ مقادیر نامعتبر!")
        return
    await db.add_diamonds(user_id, amount, 'gift', f'هدیه ادمین')
    await message.answer(f"✅ {amount} الماس به {user_id} اضافه شد.")


@router.message(Command("setpremium"))
async def set_premium(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    args = message.text.split()
    if len(args) < 3:
        await message.answer("❌ فرمت: /setpremium <user_id> <days>")
        return
    try:
        user_id = int(args[1])
        days = int(args[2])
    except ValueError:
        await message.answer("❌ مقادیر نامعتبر!")
        return
    from datetime import datetime, timedelta
    expires = datetime.now() + timedelta(days=days)
    await db.update_user(user_id, is_premium=1, premium_expires_at=expires)
    await message.answer(f"✅ پرمیوم {days} روزه برای {user_id} فعال شد.")


@router.message(Command("broadcast"))
async def broadcast(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    text = message.text.replace("/broadcast ", "", 1)
    if not text or text == "/broadcast":
        await message.answer("❌ فرمت: /broadcast <message>")
        return

    users = await db.fetchall("SELECT id FROM users WHERE is_active = 1")
    sent = 0
    for user in users:
        try:
            await message.bot.send_message(user['id'], f"📢 {text}")
            sent += 1
        except Exception:
            pass
    await message.answer(f"✅ پیام به {sent} نفر ارسال شد.")


@router.message(Command("reply"))
async def reply_to_user(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer("❌ فرمت: /reply <user_id> <message>")
        return
    try:
        user_id = int(args[1])
    except ValueError:
        await message.answer("❌ آیدی نامعتبر!")
        return
    reply_text = args[2]
    try:
        await message.bot.send_message(user_id, f"📞 پاسخ پشتیبانی:\n\n{reply_text}")
        await message.answer("✅ پاسخ ارسال شد.")
    except Exception:
        await message.answer("❌ ارسال ناموفق! شاید کاربر ربات رو بلاک کرده.")
