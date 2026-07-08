# Password Manager

<p align="center">

![Python](https://img.shields.io/badge/Python-3.14%2B-blue?logo=python\&logoColor=white)
![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?logo=sqlite\&logoColor=white)
![Cryptography](https://img.shields.io/badge/Encryption-Fernet%20AES--256-orange)
![Rich](https://img.shields.io/badge/UI-Rich%20CLI-purple)
![License](https://img.shields.io/github/license/SMHO179/Password-Manager?color=green)
![Last Commit](https://img.shields.io/github/last-commit/SMHO179/Password-Manager)
![Repo Size](https://img.shields.io/github/repo-size/SMHO179/Password-Manager)

</p>

یک **مدیریت‌کننده رمز عبور امن و سبک مبتنی بر خط فرمان (CLI)** که با زبان پایتون ساخته شده است.

رمزهای عبور با استفاده از **رمزنگاری متقارن Fernet (AES-256)** رمزگذاری شده و به صورت محلی در یک **پایگاه داده SQLite** ذخیره می‌شوند.

بدون فضای ابری، بدون ردیابی و بدون وابستگی به سرویس‌های خارجی.

---

## ✨ امکانات

* 🔒 رمزنگاری AES-256 با استفاده از Fernet
* 💾 ذخیره‌سازی محلی اطلاعات در SQLite
* 🖥️ رابط کاربری زیبا و تعاملی ترمینال با استفاده از [Rich](https://github.com/Textualize/rich)
* 🔑 تولید خودکار کلید رمزنگاری
* 🙈 مخفی کردن رمز عبور هنگام ورود
* ✅ اعتبارسنجی ورودی‌ها
* 🛑 مدیریت صحیح خروج با `Ctrl+C`
* 🔄 تراکنش‌های اتمیک پایگاه داده با بازگشت خودکار (Rollback)
* 📦 کاملاً آفلاین — اطلاعات شما فقط روی سیستم خودتان باقی می‌ماند

---

## 🛠 فناوری‌های استفاده شده

| فناوری | کاربرد |
|---|---|
| Python 3.14+ | زبان اصلی برنامه‌نویسی |
| SQLite3 | پایگاه داده داخلی و محلی |
| cryptography | رمزنگاری Fernet |
| Rich | رابط کاربری ترمینال |

---

## 📂 ساختار پروژه

```text
.
├── main.py           # فایل اصلی برنامه
├── generate_key.py   # تولیدکننده کلید رمزنگاری
├── secret.key        # کلید رمزنگاری (امن نگه دارید!)
├── vault.db          # پایگاه داده رمزها
├── requirements.txt  # وابستگی‌های پایتون
├── README.md         # مستندات انگلیسی
├── README-FA.md      # مستندات فارسی
└── LICENSE
```

---

## 🚀 نصب

### دریافت پروژه

```bash
git clone https://github.com/SMHO179/Password-Manager.git
cd Password-Manager
```

### ساخت محیط مجازی

```bash
python -m venv .venv
source .venv/bin/activate
```

### نصب وابستگی‌ها

```bash
pip install -r requirements.txt
```

---

## ▶️ استفاده

اجرای برنامه:

```bash
python main.py
```

### منو

```text
1. افزودن رمز عبور
2. نمایش رمزهای عبور
3. خروج
```

---

## 🔐 امنیت

* رمزهای عبور **هرگز به صورت متن ساده ذخیره نمی‌شوند**
* هر خزانه (Vault) دارای کلید رمزنگاری اختصاصی خود است
* برای بازیابی رمزهای ذخیره‌شده، کلید رمزنگاری لازم است
* هنگام وارد کردن رمز، ورودی نمایش داده نمی‌شود
* ورودی‌های خالی و نامعتبر رد می‌شوند

> ⚠️ از دست دادن فایل `secret.key` به معنی غیرقابل‌بازیابی شدن رمزهای رمزگذاری‌شده است.

فایل کلید را در مکانی امن نگهداری کرده و از آن نسخه پشتیبان تهیه کنید.

---

## 🗄 ساختار پایگاه داده

| ستون | نوع | توضیحات |
|---|---|---|
| id | INTEGER | کلید اصلی |
| site | TEXT | نام سایت یا سرویس |
| username | TEXT | نام کاربری حساب |
| password | TEXT | رمز عبور رمزگذاری‌شده با Fernet |
| created_at | TIMESTAMP | زمان ایجاد |

---

## 🤝 مشارکت در پروژه

مشارکت شما در توسعه پروژه خوشحال‌کننده است!

1. پروژه را Fork کنید
2. یک Branch جدید ایجاد کنید
3. تغییرات خود را Commit کنید
4. یک Pull Request ارسال کنید

---

## 📜 مجوز

این پروژه تحت قوانین فایل [LICENSE](LICENSE) منتشر شده است.
