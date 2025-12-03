import telebot
from telebot import types
from datetime import datetime
from db import *
from vaccines import calc_dates, get_vaccine_info
from scheduler import start_scheduler

# --- Konfiguratsiya ---
# ...
TOKEN = ""
ADMIN = 6602964695
ADMIN2 = 7857976480  

bot = telebot.TeleBot(TOKEN)
# Barcha jadvallarni yaratish va test ma'lumotlarini yuklash
init_db() 
# Eslatmalar schedulerini ishga tushirish
start_scheduler(bot)

# Foydalanuvchilarning joriy sessiyasini saqlash (bir vaqtning o'zida ishlash uchun)
# Format: {chat_id: current_parent_id}
user_sessions = {}


# ----------- Foydalanuvchi qismi -------------

@bot.message_handler(commands=["start"])
def send_welcome(m):
    # ReplyKeyboardRemove orqali eski ReplyKeyboard larni olib tashlaymiz
    kb_remove = types.ReplyKeyboardRemove(selective=False)
    
    text = (
        "Assalomu alaykum! Emlash botiga xush kelibsiz.\n\n"
        "Iltimos, shaxsingizni tasdiqlash uchun **JSHR (PINFL)** raqamingizni yuboring:"
    )
    bot.send_message(m.chat.id, text, parse_mode="Markdown", reply_markup=kb_remove)
    bot.register_next_step_handler(m, check_jshr)


def check_jshr(m):
    jshr = m.text.strip()
    
    parent = get_parent_by_jshr(jshr) # qaytadi: (id, name)
    
    if not parent:
        bot.send_message(m.chat.id, "❌ Bunday JSHR bazada topilmadi. Qaytadan /start bosing.")
        return

    pid, name = parent
    
    # MUHIM: chat_id ni saqlaymiz, faqatgina yangilamaymiz (ko'p qurilmadan kirish uchun)
    add_parent_chat_id(pid, m.chat.id)
    user_sessions[m.chat.id] = pid
    
    # Reply Keyboardni chiqarish (Tizimdan chiqish tugmasi uchun)
    kb_reply = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    kb_reply.add(types.KeyboardButton("🚪 Tizimdan chiqish"))
    bot.send_message(m.chat.id, f"Xush kelibsiz, **{name}**!", reply_markup=kb_reply, parse_mode="Markdown")

    show_main_menu(m.chat.id, name, pid)


def show_main_menu(chat_id, parent_name, pid, message_id_to_edit=None):
    children = get_children(pid)
    
    text = f"👤 **{parent_name}**, xush kelibsiz!\n\nEmlash jadvalini ko'rish uchun bolani tanlang:"
    
    kb_inline = types.InlineKeyboardMarkup(row_width=1)
    
    # Har bir bola uchun tugma
    for cid, child_name in children:
        kb_inline.add(types.InlineKeyboardButton(text=f"👶 {child_name}", callback_data=f"child_{cid}"))
    
    # Qo'shimcha ma'lumot tugmasi
    kb_inline.add(types.InlineKeyboardButton(text="ℹ️ Vaksinalar haqida ma'lumot", callback_data="info_vaccines"))

    if message_id_to_edit:
        # Eski xabarni tahrirlash (toza UI)
        bot.edit_message_text(text, chat_id, message_id_to_edit, reply_markup=kb_inline, parse_mode="Markdown")
    else:
        # Yangi xabar yuborish
        bot.send_message(chat_id, text, reply_markup=kb_inline, parse_mode="Markdown")


# ----------------- Callback Handlers -----------------

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    
    # Boshqa callbacklar bu yerdan boshlanadi
    if call.data.startswith("child_"):
        cid = int(call.data.split("_")[1])
        show_child_vaccines(call, cid)
    
    elif call.data == "info_vaccines":
        show_vaccine_info(call)

    elif call.data == "back_main":
        # Orqaga qaytishda joriy sessiya ma'lumotlarini ishlatamiz
        pid = user_sessions.get(chat_id)
        parent = get_parent_by_pid(pid) # db.py da yaratilgan yangi funksiya
        if parent:
            show_main_menu(chat_id, parent[1], pid, message_id_to_edit=message_id)
        else:
            bot.edit_message_text("Sessiya yangilanishi kerak. Iltimos /start bosing.", chat_id, message_id)
    
    # Log out callbacklari (keyingi bo'limda)
    elif call.data.startswith("logout_"):
        handle_logout_callback(call)
        
    bot.answer_callback_query(call.id) # Callback ni yopish

# --- Yordamchi Callback funksiyalari ---

def show_child_vaccines(call, cid):
    vaccines = get_vaccines(cid)
    
    # Bola ismini DB dan olish
    c = sqlite3.connect(DB_NAME)
    cur = c.cursor()
    cur.execute("SELECT name FROM children WHERE id=?", (cid,))
    child_name = cur.fetchone()[0]
    c.close()

    text = f"👶 **{child_name}** uchun emlash jadvali:\n\n"
    today = datetime.now().strftime("%Y-%m-%d")
    
    if not vaccines:
        text += "Ma'lumot topilmadi."
    else:
        for v_name, v_date in vaccines:
            status = "✅" if v_date < today else "⏳"
            text += f"{status} `{v_date}` — **{v_name}**\n"
            
    text += "\n✅ - O'tgan\n⏳ - Kutilayotgan"

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_main"))
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

def show_vaccine_info(call):
    text = get_vaccine_info()
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_main"))
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")


# ----------------- LOGOUT QISMI -----------------

# bot.py ichida, @bot.message_handler(func=lambda m: m.text == "🚪 Tizimdan chiqish")

@bot.message_handler(func=lambda m: m.text == "🚪 Tizimdan chiqish")
def start_logout(m):
    chat_id = m.chat.id
    
    # 1. Bu chat_id ga bog'langan barcha JSHR larni olish
    linked_parents = get_linked_parents_by_chat_id(chat_id)
    
    if not linked_parents:
        # Agar bog'langan JSHRlar topilmasa, Reply Keyboardni o'chiramiz
        kb_remove = types.ReplyKeyboardRemove(selective=False)
        bot.send_message(chat_id, "Sizning bu qurilmangizda bog'langan JSHRlar topilmadi. Qaytadan kirish uchun /start bosing.", reply_markup=kb_remove)
        return

    text = "👤 Qaysi JSHR (ota-ona) bog'lanishini ushbu qurilmadan uzmoqchisiz?\n\n"
    kb = types.InlineKeyboardMarkup(row_width=1)
    
    # Har bir JSHR uchun alohida tugma yaratish
    for i, parent in enumerate(linked_parents, 1):
        pid, jshr, name = parent
        
        callback_key = f"logout_{pid}" 
        
        # Xabarga ma'lumotni qo'shamiz
        text += f"{i}. **{name}** (JSHR: `{jshr}`)\n"
        
        # Inline tugma yaratamiz (har bir JSHR uchun alohida)
        kb.add(types.InlineKeyboardButton(text=f"{i}. {name} (JSHR: {jshr})", callback_data=callback_key))
        
    # --- Qo'shimcha tugma: Hammasini uzish ---
    kb.add(types.InlineKeyboardButton(text="❌ Hammasini uzish (Butunlay chiqish)", callback_data="logout_all"))

    # Xabarni yuborish
    bot.send_message(chat_id, text, reply_markup=kb, parse_mode="Markdown")

def handle_logout_callback(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    
    if call.data == "logout_all":
        # Barcha bog'lanishlarni uzish
        rows_deleted = delete_all_chat_ids_for_user(chat_id)
        
        # Asosiy menyu tugmasini yo'qotish
        kb_remove = types.ReplyKeyboardRemove(selective=False)
        bot.send_message(chat_id, f"✅ Qurilmangizdagi barcha {rows_deleted} ta JSHR bog'lanishlari uzildi. Eslatmalar endi kelmaydi.\n\nQayta kirish uchun /start bosing.", reply_markup=kb_remove)
        
    else:
        # Ma'lum bir JSHR bog'lanishini uzish
        try:
            pid_to_logout = int(call.data.split("_")[1])
            rows_deleted = delete_chat_id_link(pid_to_logout, chat_id)
            
            if rows_deleted > 0:
                # Ota-ona nomini topib olamiz
                parent = get_parent_by_pid(pid_to_logout)
                name = parent[1] if parent else "Noma'lum"

                bot.edit_message_text(f"✅ **{name}** (JSHR: {pid_to_logout}) bog'lanishi uzildi. Ushbu JSHR uchun eslatmalar endi bu qurilmaga kelmaydi.", chat_id, message_id, parse_mode="Markdown")
                
                # Agar bu JSHR joriy sessiyada ishlatilayotgan bo'lsa, uni ham o'chirish
                if user_sessions.get(chat_id) == pid_to_logout:
                    user_sessions.pop(chat_id)
                    
            else:
                bot.edit_message_text("❌ Xatolik yuz berdi yoki bog'lanish avvaldan mavjud emas.", chat_id, message_id)

        except Exception as e:
            bot.edit_message_text("❌ Tizimdan chiqishda xato. Qaytadan urinib ko'ring.", chat_id, message_id)


# ----------------- ADMIN PANEL -----------------
# Admin panel faqat JSHR qo'shishga moslashgan
@bot.message_handler(commands=["admin"])
def admin_panel(m):
    if m.chat.id not in [ADMIN, ADMIN2]: return
    msg = "Admin panel. Yangi foydalanuvchi qo'shish uchun format:\n\n" \
          "`/add jshr Ism Familiya`\n" \
          "Misol: `/add 123456789 Aliyev Vali`\n\n" \
          "Bolani ota-onaga qo'shish:\n" \
          "`/child jshr Bola_Ismi Tug'ilgan_Sana`\n" \
          "Misol: `/child 123456789 Ali 2024-01-01`"
    bot.send_message(m.chat.id, msg, parse_mode="Markdown")

@bot.message_handler(commands=["add"])
def admin_add_parent(m):
    if m.chat.id not in [ADMIN, ADMIN2]: return
    try:
        parts = m.text.split(maxsplit=2)
        jshr = parts[1]
        name = parts[2]
        pid = add_parent_jshr(jshr, name)
        if pid:
            bot.reply_to(m, f"✅ Qo'shildi: {name} (JSHR: {jshr})")
        else:
            bot.reply_to(m, "❌ Xatolik. Bu JSHR allaqachon mavjud bo'lishi mumkin.")
    except:
        bot.reply_to(m, "Format xato: `/add jshr Ism Familiya`")

@bot.message_handler(commands=["child"])
def admin_add_child(m):
    if m.chat.id not in [ADMIN, ADMIN2]: return
    try:
        parts = m.text.split(maxsplit=3)
        jshr = parts[1]
        child_name = parts[2]
        birth = parts[3]
        
        parent = get_parent_by_jshr(jshr)
        if not parent:
            bot.reply_to(m, "Ota-ona topilmadi.")
            return
            
        cid = add_child_db(parent[0], child_name, birth)
        for vname, vdate in calc_dates(birth):
            add_vaccine_db(cid, vname, vdate)
            
        bot.reply_to(m, f"✅ {child_name} muvaffaqiyatli qo'shildi.")
    except:
        bot.reply_to(m, "Format xato: `/child jshr Bola_Ismi YYYY-MM-DD`")


bot.infinity_polling()
