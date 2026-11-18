# Vaccination Reminder — Emlash Eslatma Boti

Ota-onalarga bolalarining emlash (vaksinatsiya) jadvalini ko'rish va o'z vaqtida eslatma olish imkonini beruvchi Telegram bot.

A Telegram bot that lets parents view their children's vaccination schedule and receive timely reminders.

---

## Xususiyatlar / Features

- 🔐 **JSHR (PINFL) orqali tasdiqlash** — foydalanuvchi shaxsingizni JSHR raqami bilan tasdiqlaydi.
- 👶 **Bolalar ro'yxati** — ota-onaga biriktirilgan barcha bolalarni ko'rish.
- 📅 **Emlash jadvali** — har bir bola uchun vaksina turlari va sanalari (`✅ o'tgan`, `⏳ kutilayotgan`).
- 💉 **Vaksinalar haqida ma'lumot** — har bir vaksina qaysi kasallikdan himoya qilishi haqida qisqacha ma'lumot.
- ⏰ **Avtomatik eslatmalar** — eslatma kunidan **1 kun oldin soat 07:00** va **kunida soat 08:20** (Asia/Tashkent) yuboriladi.
- 📱 **Ko'p qurilma qo'llab-quvvatlash** — bir JSHR bir nechta chat_id ga bog'lanishi mumkin.
- 🚪 **Tizimdan chiqish** — qurilmadagi bog'lanishlarni qisman yoki to'liq uzish.
- 👑 **Admin panel** — yangi ota-ona va bola qo'shish.

## Texnologiyalar / Tech stack

- Python 3
- [pyTelegramBotAPI (`telebot`)](https://github.com/eternnoir/pyTelegramBotAPI)
- `pytz` (vaqt zonasi uchun)
- `sqlite3` (ma'lumotlar bazasi: `db.sqlite3`)

## O'rnatish / Installation

```bash
# 1. Repository ni klonlash
git clone https://github.com/Mrasco2110/Vaccination-Reminder.git
cd Vaccination-Reminder

# 2. Kerakli kutubxonalarni o'rnatish
pip install pyTelegramBotAPI pytz

# 3. bot.py faylida TOKEN va ADMIN larni sozlash
```

`bot.py` faylining yuqori qismidagi o'zgaruvchilarni to'ldiring:

```python
TOKEN = "SIZNING_BOT_TOKENINGIZ"   # @BotFather dan olingan token
ADMIN  = 6602964695                  # asosiy admin chat ID
ADMIN2 = 7857976480                  # qo'shimcha admin chat ID
```

## Ishga tushirish / Usage

```bash
python bot.py
```

Bot ishga tushganda `init_db()` avtomatik ravishda jadvallarni yaratadi va (baza bo'sh bo'lsa) test ma'lumotlarini qo'shadi. Eslatma scheduleri alohida thread'da ishga tushadi.

### Test ma'lumotlari (JSHR)

| JSHR       | Ota-ona           | Bolalar                              |
|------------|-------------------|--------------------------------------|
| 123456789  | Aliyev Vali       | Aliyev Axad, Aliyeva Zebo            |
| 987654321  | Olimova Dildora   | Olimov Bekzod                        |

### Foydalanuvchi buyruqlari

- `/start` — tizimga kirish (JSHR raqamini yuborish orqali)
- `🚪 Tizimdan chiqish` — qurilmadagi bog'lanishlarni uzish

### Admin buyruqlari

- `/admin` — admin panel va formatlar haqida ma'lumot
- `/add <jshr> <Ism Familiya>` — yangi ota-ona qo'shish
  - Misol: `/add 123456789 Aliyev Vali`
- `/child <jshr> <Bola_Ismi> <YYYY-MM-DD>` — bolani qo'shish (emlash jadvali avtomatik hisoblanadi)
  - Misol: `/child 123456789 Ali 2024-01-01`

## Loyiha tuzilması / Project structure

| Fayl           | Tavsif                                                          |
|----------------|-----------------------------------------------------------------|
| `bot.py`       | Telegram bot, handler'lar, foydalanuvchi va admin qismi         |
| `db.py`        | SQLite bazasi va ma'lumotlar bazasi bilan ishlash funksiyalari  |
| `scheduler.py` | Eslatmalarni vaqt bo'yicha yuboruvchi fon jarayoni             |
| `vaccines.py`  | Vaksina tavsiflari va emlash sanalarini hisoblash (`calc_dates`)|

## Eslatma / Note

`db.sqlite3` fayli va bot tokini repository'ga qo'shmang — ular shaxsiy ma'lumot hisoblanadi.
Do not commit `db.sqlite3` or your bot token — they contain sensitive data.
