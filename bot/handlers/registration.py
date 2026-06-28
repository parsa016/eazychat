from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from bot.database import db
from bot.states.registration import Registration
from bot.keyboards.main_kb import (
    phone_kb, gender_kb, purpose_kb, interests_kb,
    photos_done_kb, main_menu_kb
)
from bot.data.cities import get_provinces, get_cities, is_valid_province, is_valid_city
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)

    if user and user['is_verified']:
        await message.answer(
            "👋 خوش اومدی به ایزی‌چت!\n"
            "از منوی زیر یکی رو انتخاب کن:",
            reply_markup=main_menu_kb()
        )
        return

    if user and user['registration_step'] != 'start':
        # Resume registration
        step = user['registration_step']
        await resume_registration(message, state, step)
        return

    # New user
    await db.create_user(message.from_user.id)
    await message.answer(
        "👋 سلام! به ربات دوست‌یابی ایزی‌چت خوش اومدی!\n\n"
        "برای شروع، لطفاً شماره موبایلت رو با دکمه زیر ارسال کن:",
        reply_markup=phone_kb()
    )
    await state.set_state(Registration.phone)


async def resume_registration(message: Message, state: FSMContext, step: str):
    step_map = {
        'phone': (Registration.phone, "📱 لطفاً شماره موبایلت رو ارسال کن:", phone_kb()),
        'name': (Registration.name, "✍️ لطفاً اسمت رو وارد کن:", ReplyKeyboardRemove()),
        'gender': (Registration.gender, "👤 جنسیتت رو انتخاب کن:", gender_kb()),
        'age': (Registration.age, "🎂 سنت چنده؟ (عدد وارد کن):", ReplyKeyboardRemove()),
        'province': (Registration.province, "🏠 استانت رو انتخاب کن:", province_keyboard()),
        'city': (Registration.city, "🏙️ شهرت رو انتخاب کن:", ReplyKeyboardRemove()),
        'photos': (Registration.photos, "📸 حداقل ۱ و حداکثر ۳ عکس برای پروفایلت بفرست:", ReplyKeyboardRemove()),
        'verification': (Registration.verification_video, "🎥 برای احراز هویت یه ویدیو مسیج بفرست و بگو:\n«احراز هویت در ربات ایزی‌چت»", ReplyKeyboardRemove()),
        'purpose': (Registration.purpose, "🎯 هدفت از اومدن به ربات چیه؟", purpose_kb()),
        'interests': (Registration.interests, "💡 علاقه‌مندی‌هات رو انتخاب کن (حداکثر ۵ تا):", interests_kb()),
    }
    if step in step_map:
        st, text, kb = step_map[step]
        await state.set_state(st)
        if hasattr(kb, 'inline_keyboard'):
            await message.answer(text, reply_markup=kb)
        else:
            await message.answer(text, reply_markup=kb)


def province_keyboard():
    provinces = get_provinces()
    keyboard = []
    for i in range(0, len(provinces), 3):
        row = [KeyboardButton(text=p) for p in provinces[i:i+3]]
        keyboard.append(row)
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def city_keyboard(province: str):
    cities = get_cities(province)
    keyboard = []
    for i in range(0, len(cities), 3):
        row = [KeyboardButton(text=c) for c in cities[i:i+3]]
        keyboard.append(row)
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


# ============ PHONE ============

@router.message(Registration.phone, F.contact)
async def process_phone(message: Message, state: FSMContext):
    phone = message.contact.phone_number
    await db.update_user(message.from_user.id, phone=phone, registration_step='name')
    await message.answer(
        "✅ شماره موبایلت ثبت شد!\n\n"
        "✍️ حالا اسمت رو وارد کن:",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(Registration.name)


@router.message(Registration.phone)
async def process_phone_invalid(message: Message, state: FSMContext):
    await message.answer(
        "❌ لطفاً از دکمه «ارسال شماره موبایل» استفاده کن.",
        reply_markup=phone_kb()
    )


# ============ NAME ============

@router.message(Registration.name)
async def process_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2 or len(name) > 50:
        await message.answer("❌ اسم باید بین ۲ تا ۵۰ کاراکتر باشه.")
        return
    await db.update_user(message.from_user.id, name=name, registration_step='gender')
    await message.answer("👤 جنسیتت رو انتخاب کن:", reply_markup=gender_kb())
    await state.set_state(Registration.gender)


# ============ GENDER ============

@router.callback_query(Registration.gender, F.data.startswith("gender_"))
async def process_gender(callback: CallbackQuery, state: FSMContext):
    gender = callback.data.split("_")[1]  # male or female
    await db.update_user(callback.from_user.id, gender=gender, registration_step='age')
    await callback.message.edit_text("✅ جنسیت ثبت شد!")
    await callback.message.answer("🎂 سنت چنده؟ (یه عدد بین ۱۸ تا ۶۰ وارد کن):")
    await state.set_state(Registration.age)


# ============ AGE ============

@router.message(Registration.age)
async def process_age(message: Message, state: FSMContext):
    try:
        age = int(message.text.strip())
        if age < 18 or age > 60:
            raise ValueError
    except ValueError:
        await message.answer("❌ لطفاً یه عدد معتبر بین ۱۸ تا ۶۰ وارد کن.")
        return

    await db.update_user(message.from_user.id, age=age, registration_step='province')
    await message.answer("🏠 استانت رو انتخاب کن:", reply_markup=province_keyboard())
    await state.set_state(Registration.province)


# ============ PROVINCE ============

@router.message(Registration.province)
async def process_province(message: Message, state: FSMContext):
    province = message.text.strip()
    if not is_valid_province(province):
        await message.answer("❌ استان نامعتبره. لطفاً از لیست انتخاب کن.", reply_markup=province_keyboard())
        return

    await state.update_data(province=province)
    await db.update_user(message.from_user.id, province=province, registration_step='city')
    await message.answer(f"🏙️ شهرت رو از استان {province} انتخاب کن:", reply_markup=city_keyboard(province))
    await state.set_state(Registration.city)


# ============ CITY ============

@router.message(Registration.city)
async def process_city(message: Message, state: FSMContext):
    city = message.text.strip()
    data = await state.get_data()
    province = data.get('province', '')

    if not is_valid_city(province, city):
        await message.answer("❌ شهر نامعتبره. لطفاً از لیست انتخاب کن.", reply_markup=city_keyboard(province))
        return

    await db.update_user(message.from_user.id, city=city, registration_step='photos')
    await state.update_data(photo_count=0)
    await message.answer(
        "📸 حالا عکس‌های پروفایلت رو بفرست.\n"
        "حداقل ۱ و حداکثر ۳ عکس.\n\n"
        "بعد از ارسال عکس‌ها، دکمه «تمام» رو بزن.",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(Registration.photos)


# ============ PHOTOS ============

@router.message(Registration.photos, F.photo)
async def process_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photo_count = data.get('photo_count', 0)

    if photo_count >= 3:
        await message.answer("❌ حداکثر ۳ عکس می‌تونی بفرستی. دکمه «تمام» رو بزن.")
        return

    file_id = message.photo[-1].file_id
    photo_count += 1
    await db.add_photo(message.from_user.id, file_id, photo_count)
    await state.update_data(photo_count=photo_count)

    if photo_count < 3:
        await message.answer(
            f"✅ عکس {photo_count} ثبت شد! ({photo_count}/3)\n"
            f"می‌تونی عکس بعدی رو بفرستی یا «تمام» رو بزن.",
            reply_markup=photos_done_kb()
        )
    else:
        await message.answer(
            "✅ عکس ۳ ثبت شد! حداکثر عکس رسید.\n"
            "دکمه «تمام» رو بزن.",
            reply_markup=photos_done_kb()
        )


@router.callback_query(Registration.photos, F.data == "photos_done")
async def process_photos_done(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    photo_count = data.get('photo_count', 0)

    if photo_count < 1:
        await callback.answer("❌ حداقل ۱ عکس باید بفرستی!", show_alert=True)
        return

    await db.update_user(callback.from_user.id, registration_step='verification')
    await callback.message.edit_text("✅ عکس‌ها ثبت شدن!")
    await callback.message.answer(
        "🎥 مرحله احراز هویت:\n\n"
        "لطفاً یه ویدیو مسیج (دایره‌ای) بفرست و توش بگو:\n"
        "«احراز هویت در ربات ایزی‌چت»\n\n"
        "⚠️ توجه: عکس اول پروفایلت باید با چهره‌ات در ویدیو مطابقت داشته باشه."
    )
    await state.set_state(Registration.verification_video)


@router.message(Registration.photos)
async def process_photos_invalid(message: Message, state: FSMContext):
    await message.answer("❌ لطفاً عکس بفرست یا دکمه «تمام» رو بزن.", reply_markup=photos_done_kb())


# ============ VERIFICATION VIDEO ============

@router.message(Registration.verification_video, F.video_note)
async def process_verification_video(message: Message, state: FSMContext):
    video_file_id = message.video_note.file_id
    await db.create_verification(message.from_user.id, video_file_id)
    await db.update_user(message.from_user.id, registration_step='waiting_verification')

    await message.answer(
        "✅ ویدیو احراز هویت ارسال شد!\n\n"
        "⏳ منتظر بررسی ادمین باش. بعد از تأیید بهت اطلاع داده میشه."
    )
    await state.clear()

    # Notify admins
    from config import ADMIN_IDS
    from bot.keyboards.main_kb import verification_admin_kb

    user = await db.get_user(message.from_user.id)
    photos = await db.get_photos(message.from_user.id)

    for admin_id in ADMIN_IDS:
        try:
            verifications = await db.fetchall(
                "SELECT id FROM verifications WHERE user_id = %s ORDER BY id DESC LIMIT 1",
                (message.from_user.id,)
            )
            v_id = verifications[0]['id'] if verifications else 0

            admin_text = (
                f"🔔 درخواست احراز هویت جدید:\n\n"
                f"👤 نام: {user['name']}\n"
                f"🆔 آیدی: {message.from_user.id}\n"
                f"📱 شماره: {user['phone']}\n"
            )
            await message.bot.send_message(admin_id, admin_text)

            # Send first profile photo
            if photos:
                await message.bot.send_photo(admin_id, photos[0]['file_id'], caption="عکس اول پروفایل:")

            # Send verification video
            await message.bot.send_video_note(admin_id, video_file_id)
            await message.bot.send_message(
                admin_id,
                "آیا تأیید می‌کنید؟",
                reply_markup=verification_admin_kb(message.from_user.id, v_id)
            )
        except Exception:
            pass


@router.message(Registration.verification_video)
async def process_verification_invalid(message: Message, state: FSMContext):
    await message.answer(
        "❌ لطفاً یه ویدیو مسیج (دایره‌ای) بفرست.\n"
        "از دکمه ویدیو مسیج تلگرام استفاده کن."
    )
