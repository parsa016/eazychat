from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ContentType
# ContentType still used for photo filter
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart

from bot.database import db
from bot.states.registration import Registration
from bot.keyboards.main_kb import (
    phone_kb, gender_kb, photos_done_kb, main_menu_kb, purpose_kb, interests_kb,
    remove_kb, province_kb, city_kb, verification_optional_kb
)
from bot.data.cities import get_provinces, get_cities, is_valid_province, is_valid_city
from config import ADMIN_IDS, VERIFICATION_GROUP_ID, SIGNUP_BONUS, PROFILE_COMPLETE_BONUS

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id

    # Check referral
    referrer_id = None
    args = message.text.split()
    if len(args) > 1:
        ref_code = args[1]
        referrer = await db.fetchone(
            "SELECT id FROM users WHERE referral_code = %s AND id != %s",
            (ref_code, user_id)
        )
        if referrer:
            referrer_id = referrer['id']

    user = await db.get_user(user_id)

    if not user:
        code = await db.create_user(user_id)
        # Process referral
        if referrer_id:
            await db.process_referral(user_id, referrer_id)

        # Signup bonus
        await db.add_diamonds(user_id, SIGNUP_BONUS, 'signup', 'جایزه ثبت‌نام')

        await message.answer(
            f"👋 به ربات EazyChat خوش اومدی!\n\n"
            f"🎁 {SIGNUP_BONUS} الماس هدیه ثبت‌نام دریافت کردی!\n\n"
            f"لطفاً شماره موبایلت رو ارسال کن:",
            reply_markup=phone_kb()
        )
        await state.set_state(Registration.phone)
        return

    # Resume registration based on step
    step = user.get('registration_step', 'start')
    if step == 'completed':
        await state.clear()
        await message.answer("🏠 منوی اصلی", reply_markup=main_menu_kb())
        # Update streak
        await db.update_streak(user_id)
    elif step == 'phone':
        await message.answer("📱 لطفاً شماره موبایلت رو ارسال کن:", reply_markup=phone_kb())
        await state.set_state(Registration.phone)
    elif step == 'name':
        await message.answer("✏️ اسمت رو بنویس:", reply_markup=remove_kb())
        await state.set_state(Registration.name)
    elif step == 'gender':
        await message.answer("👤 جنسیتت رو انتخاب کن:", reply_markup=gender_kb())
        await state.set_state(Registration.gender)
    elif step == 'age':
        await message.answer("🎂 سنت رو بنویس (18 تا 60):", reply_markup=remove_kb())
        await state.set_state(Registration.age)
    elif step == 'province':
        provinces = get_provinces()
        await message.answer("🏠 استانت رو انتخاب کن:", reply_markup=province_kb(provinces))
        await state.set_state(Registration.province)
    elif step == 'city':
        province = user.get('province', '')
        cities = get_cities(province) if province else []
        await message.answer("🏙️ شهرت رو انتخاب کن:", reply_markup=city_kb(cities))
        await state.set_state(Registration.city)
    elif step == 'photos':
        await message.answer(
            "📸 عکس‌های پروفایلت رو بفرست (1 تا 3 عکس).\n"
            "بعد از ارسال دکمه «تمام» رو بزن.",
            reply_markup=photos_done_kb()
        )
        await state.set_state(Registration.photos)
    elif step == 'verification_video':
        await message.answer(
            "🎥 احراز هویت:",
            reply_markup=verification_optional_kb()
        )
    elif step == 'waiting_verification':
        await state.clear()
        await message.answer(
            "⏳ ویدیو احراز هویتت در حال بررسیه.\n"
            "بعد از تأیید بهت اطلاع میدیم. تا اون موقع می‌تونی از ربات استفاده کنی!",
            reply_markup=main_menu_kb()
        )
    elif step == 'purpose':
        await message.answer("🎯 هدفت از اومدن تو ربات:", reply_markup=purpose_kb())
    elif step == 'interests':
        await message.answer("💡 علاقه‌مندی‌هات رو انتخاب کن (حداکثر 5):", reply_markup=interests_kb())
    elif step == 'bio':
        await message.answer("📝 یه بیوگرافی کوتاه بنویس (حداکثر 300 کاراکتر):\nیا /skip بزن.")
        await state.set_state(Registration.bio)


# ============ PHONE ============

@router.message(Registration.phone, F.content_type == ContentType.CONTACT)
async def process_phone_contact(message: Message, state: FSMContext):
    phone = message.contact.phone_number
    await db.update_user(message.from_user.id, phone=phone, registration_step='name')
    await message.answer("✅ شماره ثبت شد!\n\n✏️ حالا اسمت رو بنویس:", reply_markup=remove_kb())
    await state.set_state(Registration.name)


@router.message(Registration.phone)
async def process_phone_text(message: Message, state: FSMContext):
    phone = message.text.strip()
    if not phone.replace("+", "").replace("-", "").isdigit() or len(phone) < 10:
        await message.answer("❌ شماره نامعتبره! لطفاً شماره درست بفرست یا دکمه رو بزن.", reply_markup=phone_kb())
        return
    await db.update_user(message.from_user.id, phone=phone, registration_step='name')
    await message.answer("✅ شماره ثبت شد!\n\n✏️ حالا اسمت رو بنویس:", reply_markup=remove_kb())
    await state.set_state(Registration.name)


# ============ NAME ============

@router.message(Registration.name)
async def process_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2 or len(name) > 50:
        await message.answer("❌ اسم باید بین 2 تا 50 کاراکتر باشه.")
        return
    await db.update_user(message.from_user.id, name=name, registration_step='gender')
    await message.answer("👤 جنسیتت رو انتخاب کن:", reply_markup=gender_kb())
    await state.set_state(Registration.gender)


# ============ GENDER ============

@router.callback_query(F.data.startswith("gender_"), Registration.gender)
async def process_gender(callback: CallbackQuery, state: FSMContext):
    gender = callback.data.replace("gender_", "")
    await db.update_user(callback.from_user.id, gender=gender, registration_step='age')
    await callback.message.edit_text("🎂 سنت رو بنویس (18 تا 60):")
    await state.set_state(Registration.age)


# ============ AGE ============

@router.message(Registration.age)
async def process_age(message: Message, state: FSMContext):
    try:
        age = int(message.text.strip())
    except ValueError:
        await message.answer("❌ لطفاً فقط عدد بنویس!")
        return
    if age < 18 or age > 60:
        await message.answer("❌ سن باید بین 18 تا 60 باشه.")
        return
    await db.update_user(message.from_user.id, age=age, registration_step='province')
    provinces = get_provinces()
    await message.answer("🏠 استانت رو انتخاب کن:", reply_markup=province_kb(provinces))
    await state.set_state(Registration.province)


# ============ PROVINCE ============

@router.message(Registration.province)
async def process_province(message: Message, state: FSMContext):
    province = message.text.strip()
    if not is_valid_province(province):
        provinces = get_provinces()
        await message.answer("❌ استان نامعتبر! از دکمه‌ها انتخاب کن:", reply_markup=province_kb(provinces))
        return
    await db.update_user(message.from_user.id, province=province, registration_step='city')
    await state.update_data(province=province)
    cities = get_cities(province)
    await message.answer("🏙️ شهرت رو انتخاب کن:", reply_markup=city_kb(cities))
    await state.set_state(Registration.city)


# ============ CITY ============

@router.message(Registration.city)
async def process_city(message: Message, state: FSMContext):
    city = message.text.strip()
    data = await state.get_data()
    province = data.get('province')
    if not province:
        user = await db.get_user(message.from_user.id)
        province = user['province']
    if not is_valid_city(province, city):
        cities = get_cities(province)
        await message.answer("❌ شهر نامعتبر! از دکمه‌ها انتخاب کن:", reply_markup=city_kb(cities))
        return
    await db.update_user(message.from_user.id, city=city, registration_step='photos')
    await message.answer(
        "📸 عکس‌های پروفایلت رو بفرست (حداقل 1، حداکثر 3).\n"
        "بعد از ارسال دکمه «تمام» رو بزن.",
        reply_markup=photos_done_kb()
    )
    await state.update_data(photos_count=0)
    await state.set_state(Registration.photos)


# ============ PHOTOS ============

@router.message(Registration.photos, F.content_type == ContentType.PHOTO)
async def process_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    count = data.get('photos_count', 0)
    if count >= 3:
        await message.answer("❌ حداکثر 3 عکس! دکمه «تمام» رو بزن.")
        return
    file_id = message.photo[-1].file_id
    await db.add_photo(message.from_user.id, file_id, count + 1)
    await state.update_data(photos_count=count + 1)
    remaining = 3 - (count + 1)
    if remaining > 0:
        await message.answer(
            f"✅ عکس {count + 1} ذخیره شد! (می‌تونی {remaining} عکس دیگه بفرستی یا «تمام» بزن)",
            reply_markup=photos_done_kb()
        )
    else:
        await message.answer("✅ 3 عکس ذخیره شد! حالا دکمه «تمام» رو بزن.", reply_markup=photos_done_kb())


@router.message(Registration.photos, F.text == "✅ تمام، ادامه بده")
async def photos_done_text(message: Message, state: FSMContext):
    data = await state.get_data()
    count = data.get('photos_count', 0)
    if count == 0:
        await message.answer("❌ حداقل 1 عکس لازمه! عکس بفرست.")
        return
    await db.update_user(message.from_user.id, registration_step='verification_video')
    await message.answer(
        "🎥 احراز هویت:\n\n"
        "برای اینکه کنار اسمت ✅ بیاد و لایک‌ها و مچ‌هات رو ببینی، "
        "یه ویدیو مسیج بفرست و توش بگو:\n"
        "«احراز هویت در ربات ایزی‌چت»\n\n"
        "⚠️ صورتت باید مشخص باشه و شبیه عکس پروفایلت باشه.",
        reply_markup=verification_optional_kb()
    )
    await state.clear()


@router.callback_query(F.data == "photos_done")
async def photos_done_inline(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    count = data.get('photos_count', 0)
    if count == 0:
        await callback.answer("❌ حداقل 1 عکس لازمه!", show_alert=True)
        return
    await db.update_user(callback.from_user.id, registration_step='verification_video')
    await callback.message.answer(
        "🎥 احراز هویت:\n\n"
        "برای اینکه کنار اسمت ✅ بیاد و لایک‌ها و مچ‌هات رو ببینی، "
        "یه ویدیو مسیج بفرست و توش بگو:\n"
        "«احراز هویت در ربات ایزی‌چت»\n\n"
        "⚠️ صورتت باید مشخص باشه و شبیه عکس پروفایلت باشه.",
        reply_markup=verification_optional_kb()
    )
    await state.clear()


# NOTE: Verification handlers (start_verification, skip_verification, process_verification_video)
# are all in verification.py to avoid duplicate handler conflicts.
