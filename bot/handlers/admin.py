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

    total_users = await db.fetchone("SELECT COUNT(*) as cnt FROM users")
    verified_users = await db.fetchone("SELECT COUNT(*) as cnt FROM users WHERE is_verified = 1")
    pending_verifications = await db.fetchone(
        "SELECT COUNT(*) as cnt FROM verifications WHERE status = 'pending'"
    )
    total_matches = await db.fetchone("SELECT COUNT(*) as cnt FROM matches")
    premium_users = await db.fetchone("SELECT COUNT(*) as cnt FROM users WHERE is_premium = 1")

    text = (
        "🔧 پنل ادمین:\n\n"
        f"👥 کل کاربران: {total_users['cnt']}\n"
        f"✅ تأیید شده: {verified_users['cnt']}\n"
        f"⏳ در انتظار تأیید: {pending_verifications['cnt']}\n"
        f"💑 جفت‌ها: {total_matches['cnt']}\n"
        f"⭐ پرمیوم: {premium_users['cnt']}\n\n"
        "دستورات:\n"
        "/pending - مشاهده درخواست‌های احراز هویت\n"
        "/ban <user_id> - بن کردن کاربر\n"
        "/unban <user_id> - آنبن کردن\n"
        "/addcoins <user_id> <amount> - اضافه کردن سکه\n"
        "/setpremium <user_id> <days> - فعال‌سازی پرمیوم\n"
        "/broadcast <message> - پیام همگانی\n"
    )
    await message.answer(text)


@router.message(Command("pending"))
async def view_pending(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    pending = await db.get_pending_verifications()

    if not pending:
        await message.answer("✅ درخواست احراز هویت در انتظاری وجود نداره!")
        return

    await message.answer(f"⏳ {len(pending)} درخواست در انتظار:")

    from bot.keyboards.main_kb import verification_admin_kb

    for v in pending:
        user = await db.get_user(v['user_id'])
        photos = await db.get_photos(v['user_id'])

        text = (
            f"👤 نام: {user['name']}\n"
            f"🆔 آیدی: {v['user_id']}\n"
            f"📱 شماره: {user['phone']}\n"
        )
        await message.answer(text)

        if photos:
            await message.answer_photo(photos[0]['file_id'], caption="عکس اول پروفایل:")

        await message.bot.send_video_note(message.chat.id, v['video_file_id'])
        await message.answer(
            "تأیید/رد؟",
            reply_markup=verification_admin_kb(v['user_id'], v['id'])
        )


@router.message(Command("ban"))
async def ban_user(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    try:
        parts = message.text.split()
        target_id = int(parts[1])
        await db.update_user(target_id, is_banned=1, is_active=0)
        await message.answer(f"✅ کاربر {target_id} بن شد.")
    except (IndexError, ValueError):
        await message.answer("❌ استفاده: /ban <user_id>")


@router.message(Command("unban"))
async def unban_user(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    try:
        parts = message.text.split()
        target_id = int(parts[1])
        await db.update_user(target_id, is_banned=0, is_active=1)
        await message.answer(f"✅ کاربر {target_id} آنبن شد.")
    except (IndexError, ValueError):
        await message.answer("❌ استفاده: /unban <user_id>")


@router.message(Command("addcoins"))
async def add_coins_cmd(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    try:
        parts = message.text.split()
        target_id = int(parts[1])
        amount = int(parts[2])
        await db.add_coins(target_id, amount, 'gift', 'هدیه ادمین')
        await message.answer(f"✅ {amount} سکه به کاربر {target_id} اضافه شد.")
    except (IndexError, ValueError):
        await message.answer("❌ استفاده: /addcoins <user_id> <amount>")


@router.message(Command("setpremium"))
async def set_premium_cmd(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    try:
        parts = message.text.split()
        target_id = int(parts[1])
        days = int(parts[2])

        await db.execute(
            "UPDATE users SET is_premium = 1, "
            "premium_expires_at = DATE_ADD(NOW(), INTERVAL %s DAY) "
            "WHERE id = %s",
            (days, target_id)
        )
        await message.answer(f"✅ اشتراک پرمیوم {days} روزه برای کاربر {target_id} فعال شد.")
    except (IndexError, ValueError):
        await message.answer("❌ استفاده: /setpremium <user_id> <days>")


@router.message(Command("broadcast"))
async def broadcast_cmd(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    text = message.text.replace("/broadcast ", "", 1).strip()
    if not text:
        await message.answer("❌ استفاده: /broadcast <message>")
        return

    users = await db.fetchall("SELECT id FROM users WHERE is_active = 1")
    sent = 0
    failed = 0

    for user in users:
        try:
            await message.bot.send_message(user['id'], f"📢 پیام از ادمین:\n\n{text}")
            sent += 1
        except Exception:
            failed += 1

    await message.answer(f"✅ پیام ارسال شد!\n📨 موفق: {sent}\n❌ ناموفق: {failed}")
