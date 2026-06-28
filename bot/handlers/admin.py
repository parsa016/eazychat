from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from bot.database import db
from bot.states.registration import Admin
from bot.keyboards.main_kb import admin_group_kb, verification_admin_kb
from config import ADMIN_IDS

router = Router()


# ============ GROUP PANEL (write "پنل") ============

@router.message(F.text == "پنل")
async def admin_panel(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer(
        "🔧 پنل مدیریت ایزی‌چت:",
        reply_markup=admin_group_kb()
    )


# ============ ADMIN STATS ============

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ دسترسی ندارید!", show_alert=True)
        return

    total = await db.fetchone("SELECT COUNT(*) as cnt FROM users")
    verified = await db.fetchone("SELECT COUNT(*) as cnt FROM users WHERE is_verified = 1")
    pending = await db.fetchone("SELECT COUNT(*) as cnt FROM verifications WHERE status = 'pending'")
    matches_count = await db.fetchone("SELECT COUNT(*) as cnt FROM matches WHERE is_active = 1")
    premium = await db.fetchone("SELECT COUNT(*) as cnt FROM users WHERE is_premium = 1")
    active = await db.fetchone("SELECT COUNT(*) as cnt FROM users WHERE is_active = 1")

    text = (
        f"📊 آمار ربات:\n\n"
        f"👥 کل کاربران: {total['cnt']}\n"
        f"✅ تأییدشده: {verified['cnt']}\n"
        f"🟢 فعال: {active['cnt']}\n"
        f"⏳ منتظر احراز: {pending['cnt']}\n"
        f"💑 مچ‌ها: {matches_count['cnt']}\n"
        f"⭐ پرمیوم: {premium['cnt']}"
    )
    await callback.message.answer(text)
    await callback.answer()


# ============ PENDING VERIFICATIONS ============

@router.callback_query(F.data == "admin_pending")
async def admin_pending(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ دسترسی ندارید!", show_alert=True)
        return

    pending = await db.get_pending_verifications()
    if not pending:
        await callback.answer("✅ هیچ احراز منتظری نیست!", show_alert=True)
        return

    await callback.message.answer(f"⏳ {len(pending)} احراز منتظر بررسی:")
    for v in pending[:5]:
        user = await db.get_user(v['user_id'])
        photos = await db.get_photos(v['user_id'])

        text = (
            f"🔍 درخواست احراز هویت:\n\n"
            f"👤 نام: {v['name']}\n"
            f"🆔 ID: {v['user_id']}\n"
            f"📱 شماره: {user.get('phone') or 'ندارد'}\n"
            f"🎂 سن: {user['age']}\n"
            f"👤 جنسیت: {'مرد' if user['gender'] == 'male' else 'زن'}\n"
            f"📍 {user['province']}، {user['city']}"
        )

        # Send photos
        if photos:
            for photo in photos[:3]:
                try:
                    await callback.message.answer_photo(photo['file_id'])
                except Exception:
                    pass

        # Send info text
        await callback.message.answer(text)

        # Send video
        if v.get('video_file_id'):
            try:
                await callback.message.answer_video_note(v['video_file_id'])
            except Exception:
                try:
                    await callback.message.answer_video(v['video_file_id'])
                except Exception:
                    pass

        # Send admin buttons
        await callback.message.answer(
            "👆 تأیید یا رد کنید:",
            reply_markup=verification_admin_kb(v['user_id'], v['id'])
        )
    await callback.answer()


# ============ ADMIN BROADCAST ============

@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ دسترسی ندارید!", show_alert=True)
        return
    await state.set_state(Admin.reviewing)
    await state.update_data(admin_action='broadcast')
    await callback.message.answer("📢 متن پیام همگانی رو بنویس:\nبرای لغو /cancel بزن")
    await callback.answer()


# ============ SEARCH USER ============

@router.callback_query(F.data == "admin_search_user")
async def admin_search_user_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ دسترسی ندارید!", show_alert=True)
        return
    await state.set_state(Admin.reviewing)
    await state.update_data(admin_action='search_user')
    await callback.message.answer("🔍 آیدی عددی کاربر رو بفرست:")
    await callback.answer()


# ============ ADMIN REVIEWING STATE ============

@router.message(Admin.reviewing)
async def admin_reviewing_handler(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return

    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ لغو شد.")
        return

    data = await state.get_data()
    action = data.get('admin_action')

    if action == 'broadcast':
        users = await db.fetchall("SELECT id FROM users WHERE is_active = 1")
        sent = 0
        for user in users:
            try:
                await message.bot.send_message(user['id'], message.text)
                sent += 1
            except Exception:
                pass
        await message.answer(f"✅ پیام همگانی به {sent} نفر ارسال شد.")
        await state.clear()

    elif action == 'search_user':
        try:
            user_id = int(message.text.strip())
        except ValueError:
            await message.answer("❌ آیدی نامعتبر! عدد بفرست.")
            return

        user = await db.get_user(user_id)
        if not user:
            await message.answer("❌ کاربر پیدا نشد!")
            await state.clear()
            return

        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        text = (
            f"👤 {user['name']}\n"
            f"🆔 ID: {user_id}\n"
            f"📱 {user.get('phone', '—')}\n"
            f"🎂 {user.get('age', '—')} | {user.get('gender', '—')}\n"
            f"📍 {user.get('province', '—')} - {user.get('city', '—')}\n"
            f"✅ احراز: {'بله' if user['is_verified'] else 'خیر'}\n"
            f"⭐ پرمیوم: {'بله' if user['is_premium'] else 'خیر'}\n"
            f"💎 الماس: {user['diamonds']}\n"
            f"🚫 بن: {'بله' if user['is_banned'] else 'خیر'}"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🚫 بن", callback_data=f"admin_ban_{user_id}"),
                InlineKeyboardButton(text="✅ آن‌بن", callback_data=f"admin_unban_{user_id}")
            ],
            [
                InlineKeyboardButton(text="💎 افزودن الماس", callback_data=f"admin_addgems_{user_id}"),
                InlineKeyboardButton(text="⭐ پرمیوم", callback_data=f"admin_premium_{user_id}")
            ],
            [InlineKeyboardButton(text="🗑️ حذف کاربر (ریست)", callback_data=f"admin_delete_{user_id}")]
        ])
        await message.answer(text, reply_markup=kb)
        await state.clear()

    elif action == 'addgems':
        try:
            amount = int(message.text.strip())
        except ValueError:
            await message.answer("❌ عدد بفرست!")
            return
        target_id = data.get('target_user_id')
        await db.add_diamonds(target_id, amount, 'gift', 'هدیه از ادمین')
        await message.answer(f"✅ {amount} الماس به کاربر {target_id} اضافه شد.")
        await state.clear()

    elif action == 'setpremium':
        try:
            days = int(message.text.strip())
        except ValueError:
            await message.answer("❌ عدد بفرست!")
            return
        target_id = data.get('target_user_id')
        from datetime import datetime, timedelta
        expires = datetime.now() + timedelta(days=days)
        await db.update_user(target_id, is_premium=1, premium_expires_at=expires)
        await message.answer(f"✅ پرمیوم {days} روزه برای کاربر {target_id} فعال شد.")
        await state.clear()


# ============ ADMIN COMMANDS ============

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer("🔧 پنل مدیریت:", reply_markup=admin_group_kb())


@router.message(Command("ban"))
async def cmd_ban(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("❌ فرمت: /ban <user_id>")
        return
    try:
        user_id = int(parts[1])
    except ValueError:
        await message.answer("❌ آیدی نامعتبر!")
        return
    await db.update_user(user_id, is_banned=1, is_active=0)
    await message.answer(f"✅ کاربر {user_id} بن شد.")


@router.message(Command("unban"))
async def cmd_unban(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("❌ فرمت: /unban <user_id>")
        return
    try:
        user_id = int(parts[1])
    except ValueError:
        await message.answer("❌ آیدی نامعتبر!")
        return
    await db.update_user(user_id, is_banned=0, is_active=1)
    await message.answer(f"✅ کاربر {user_id} آن‌بن شد.")


@router.message(Command("adddiamonds"))
async def cmd_add_diamonds(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("❌ فرمت: /adddiamonds <user_id> <amount>")
        return
    try:
        user_id = int(parts[1])
        amount = int(parts[2])
    except ValueError:
        await message.answer("❌ مقادیر نامعتبر!")
        return
    await db.add_diamonds(user_id, amount, 'gift', 'هدیه از ادمین')
    await message.answer(f"✅ {amount} الماس به کاربر {user_id} اضافه شد.")


@router.message(Command("setpremium"))
async def cmd_set_premium(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("❌ فرمت: /setpremium <user_id> <days>")
        return
    try:
        user_id = int(parts[1])
        days = int(parts[2])
    except ValueError:
        await message.answer("❌ مقادیر نامعتبر!")
        return
    from datetime import datetime, timedelta
    expires = datetime.now() + timedelta(days=days)
    await db.update_user(user_id, is_premium=1, premium_expires_at=expires)
    await message.answer(f"✅ پرمیوم {days} روزه برای کاربر {user_id} فعال شد.")


@router.message(Command("reply"))
async def cmd_reply(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("❌ فرمت: /reply <user_id> <message>")
        return
    try:
        user_id = int(parts[1])
    except ValueError:
        await message.answer("❌ آیدی نامعتبر!")
        return
    reply_text = parts[2]
    try:
        await message.bot.send_message(user_id, f"📞 پاسخ پشتیبانی:\n\n{reply_text}")
        await message.answer("✅ پاسخ ارسال شد.")
    except Exception:
        await message.answer("❌ ارسال پیام به کاربر ممکن نشد!")


# ============ ADMIN INLINE CALLBACKS ============

@router.callback_query(F.data.startswith("admin_ban_"))
async def admin_ban_callback(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ دسترسی ندارید!", show_alert=True)
        return
    user_id = int(callback.data.split("_")[2])
    await db.update_user(user_id, is_banned=1, is_active=0)
    await callback.answer(f"✅ کاربر {user_id} بن شد.", show_alert=True)


@router.callback_query(F.data.startswith("admin_unban_"))
async def admin_unban_callback(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ دسترسی ندارید!", show_alert=True)
        return
    user_id = int(callback.data.split("_")[2])
    await db.update_user(user_id, is_banned=0, is_active=1)
    await callback.answer(f"✅ کاربر {user_id} آن‌بن شد.", show_alert=True)


@router.callback_query(F.data.startswith("admin_addgems_"))
async def admin_addgems_callback(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ دسترسی ندارید!", show_alert=True)
        return
    user_id = int(callback.data.split("_")[2])
    await state.set_state(Admin.reviewing)
    await state.update_data(admin_action='addgems', target_user_id=user_id)
    await callback.message.answer(f"💎 تعداد الماس برای کاربر {user_id} رو بنویس:")
    await callback.answer()


@router.callback_query(F.data.startswith("admin_premium_"))
async def admin_premium_callback(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ دسترسی ندارید!", show_alert=True)
        return
    user_id = int(callback.data.split("_")[2])
    await state.set_state(Admin.reviewing)
    await state.update_data(admin_action='setpremium', target_user_id=user_id)
    await callback.message.answer(f"⭐ تعداد روز پرمیوم برای کاربر {user_id} رو بنویس:")
    await callback.answer()


@router.callback_query(F.data.startswith("admin_delete_"))
async def admin_delete_callback(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ دسترسی ندارید!", show_alert=True)
        return
    user_id = int(callback.data.split("_")[2])
    await db.delete_user(user_id)
    await callback.answer(f"✅ کاربر {user_id} حذف شد و می‌تونه از اول ثبت‌نام کنه.", show_alert=True)
