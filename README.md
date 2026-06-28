# EazyChat - ربات دوست‌یابی تلگرام

ربات دوست‌یابی تلگرامی با Python و aiogram 3

## امکانات

- ثبت‌نام با شماره موبایل
- پروفایل (نام، جنسیت، سن، استان/شهر، عکس)
- احراز هویت با ویدیو مسیج
- جستجو با فیلتر جنسیت و سن (±5 سال)
- لایک / رد / دایرکت
- سیستم Match (لایک دوطرفه)
- چت بین کاربران جفت‌شده
- محدودیت روزانه (15 مشاهده، 10 لایک)
- اشتراک پرمیوم (نامحدود)
- سیستم سکه برای دایرکت
- پنل ادمین

## نصب و راه‌اندازی

### 1. پیش‌نیازها
- Python 3.10+
- MySQL 8.0+

### 2. نصب وابستگی‌ها
```bash
pip install -r requirements.txt
```

### 3. ساخت دیتابیس
```bash
mysql -u root -p < migrations/schema.sql
```

### 4. تنظیم Environment Variables
فایل `.env.example` رو کپی کن به `.env` و مقادیر رو پر کن:

```bash
cp .env.example .env
```

- `BOT_TOKEN`: توکن ربات از @BotFather
- `ADMIN_IDS`: آیدی عددی ادمین‌ها (کاما جدا)
- `DB_*`: اطلاعات اتصال به MySQL

### 5. اجرا
```bash
python main.py
```

## ساختار پروژه
```
eazychat/
├── main.py                  # فایل اصلی اجرا
├── config.py                # تنظیمات
├── requirements.txt         # وابستگی‌ها
├── .env.example             # نمونه env
├── migrations/
│   └── schema.sql           # اسکیمای دیتابیس
└── bot/
    ├── database.py          # کلاس دیتابیس
    ├── data/
    │   └── cities.py        # شهرهای ایران
    ├── handlers/
    │   ├── registration.py  # ثبت‌نام
    │   ├── verification.py  # احراز هویت
    │   ├── profile_completion.py  # تکمیل پروفایل
    │   ├── search.py        # جستجو و لایک
    │   ├── direct_message.py # دایرکت
    │   ├── matches.py       # جفت‌شده‌ها و چت
    │   ├── profile.py       # پروفایل من
    │   └── admin.py         # پنل ادمین
    ├── keyboards/
    │   └── main_kb.py       # کیبوردها
    └── states/
        └── registration.py  # States (FSM)
```

## دستورات ادمین
- `/admin` - پنل ادمین
- `/pending` - درخواست‌های احراز هویت
- `/ban <user_id>` - بن کردن
- `/unban <user_id>` - آنبن
- `/addcoins <user_id> <amount>` - اضافه کردن سکه
- `/setpremium <user_id> <days>` - فعال‌سازی پرمیوم
- `/broadcast <message>` - پیام همگانی
