# scheduler.py

import threading, time, datetime, pytz, sqlite3
import telebot
# --- O'zgarish shu yerda ---
from db import get_all_parent_chat_ids 
# --- O'zgarish shu yerda ---

bot = None
# ... qolgan kod o'zgarishsiz qoladi
def start_scheduler(b):
    global bot
    bot = b
    t = threading.Thread(target=loop, daemon=True)
    t.start()

def loop():
    tz = pytz.timezone("Asia/Tashkent")
    while True:
        now = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M")
        check(now)
        time.sleep(60)

# scheduler.py ichida, check(now) funksiyasi

# scheduler.py ichida, check(now) funksiyasi

def check(now):
    c = sqlite3.connect("db.sqlite3")
    cur = c.cursor()
    
    # Endi parents.chat_id ni emas, balki parent.id ni olamiz
    cur.execute("""
        SELECT parents.id, children.name, vaccines.name, vaccines.date
        FROM vaccines
        JOIN children ON children.id=vaccines.child_id
        JOIN parents ON parents.id=children.parent_id
    """)
    rows = cur.fetchall()
    c.close()

    for parent_id, child_name, vac_name, date in rows: # E'tibor bering: parent_id ni olyapmiz
        
        # 1. Ushbu parent_id ga tegishli bo'lgan barcha chat_id larni topish
        chat_ids = get_all_parent_chat_ids(parent_id) 
        
        if not chat_ids:
            continue

        day_before = (datetime.datetime.strptime(date, "%Y-%m-%d") - datetime.timedelta(days=1)).strftime("%Y-%m-%d") + " 07:00"
        notif_day = date + " 08:20"

        # 2. Har bir chat_id ga xabar yuborish
        for chat_id in chat_ids:
            if now == day_before:
                try:
                    bot.send_message(chat_id, f"⚠️ Ertaga {child_name} uchun '{vac_name}' emlash bor.")
                except Exception as e:
                    # print(f"Xatolik ({chat_id}): {e}") 
                    pass 
                    
            if now == notif_day:
                try:
                    bot.send_message(chat_id, f"❗ Bugun {child_name} uchun '{vac_name}' emlash kuni.")
                except Exception as e:
                    # print(f"Xatolik ({chat_id}): {e}")
                    pass