import sqlite3
# calc_dates funksiyasiga bog'lanish, admin qo'shishda kerak bo'ladi
from vaccines import calc_dates 
from datetime import datetime

DB_NAME = "db.sqlite3"

def init_db():
    c = sqlite3.connect(DB_NAME)
    cur = c.cursor()
    
    # 1. Parents jadvali: chat_id olib tashlandi, faqat jshr, id, name qoldi
    cur.execute("""
        CREATE TABLE IF NOT EXISTS parents(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jshr TEXT UNIQUE,
            name TEXT
        )
    """)
    
    # 2. Yangi jadval: Parent va uning chat_id lari orasidagi bog'lanishni saqlaydi
    cur.execute("""
        CREATE TABLE IF NOT EXISTS parent_chats(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_id INTEGER,
            chat_id INTEGER, -- 'UNIQUE' cheklovi olib tashlandi
            FOREIGN KEY(parent_id) REFERENCES parents(id)
        )
    """)
    
    # 3. Children jadvali
    cur.execute("""
        CREATE TABLE IF NOT EXISTS children(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_id INTEGER,
            name TEXT,
            birth TEXT,
            FOREIGN KEY(parent_id) REFERENCES parents(id)
        )
    """)
    
    # 4. Vaccines jadvali
    cur.execute("""
        CREATE TABLE IF NOT EXISTS vaccines(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            child_id INTEGER,
            name TEXT,
            date TEXT,
            FOREIGN KEY(child_id) REFERENCES children(id)
        )
    """)
    
    # Jadvallarni bazaga saqlash
    c.commit() 
    c.close()
    
    # Test uchun soxta ma'lumotlar yaratish
    create_fake_data()

# ----------------- FAKE DATA (TEST UCHUN) -----------------

def create_fake_data():
    """Baza bo'sh bo'lsa, test uchun ma'lumot qo'shadi"""
    c = sqlite3.connect(DB_NAME)
    cur = c.cursor()
    
    # Tekshiramiz, agar ma'lumot bo'lsa qo'shmaymiz
    cur.execute("SELECT count(*) FROM parents")
    if cur.fetchone()[0] > 0:
        c.close()
        return

    print("--- Test ma'lumotlari yozilmoqda ---")
    
    # 1-Ota-ona (JSHR: 123456789)
    cur.execute("INSERT INTO parents(jshr, name) VALUES(?, ?)", ("123456789", "Aliyev Vali"))
    pid = cur.lastrowid
    
    # Bolalari
    children = [("Aliyev Axad", "2023-01-01"), ("Aliyeva Zebo", "2024-03-15")]
    for name, birth in children:
        cur.execute("INSERT INTO children(parent_id, name, birth) VALUES(?, ?, ?)", (pid, name, birth))
        cid = cur.lastrowid
        # Vaksinalarni hisoblash
        for v_name, v_date in calc_dates(birth):
            cur.execute("INSERT INTO vaccines(child_id, name, date) VALUES(?, ?, ?)", (cid, v_name, v_date))

    # 2-Ota-ona (JSHR: 987654321)
    cur.execute("INSERT INTO parents(jshr, name) VALUES(?, ?)", ("987654321", "Olimova Dildora"))
    pid2 = cur.lastrowid
    cur.execute("INSERT INTO children(parent_id, name, birth) VALUES(?, ?, ?)", (pid2, "Olimov Bekzod", "2023-11-20"))
    cid2 = cur.lastrowid
    for v_name, v_date in calc_dates("2023-11-20"):
        cur.execute("INSERT INTO vaccines(child_id, name, date) VALUES(?, ?, ?)", (cid2, v_name, v_date))

    c.commit()
    c.close()
    print("--- Test ma'lumotlari tayyor! JSHR: 123456789 yoki 987654321 ---")

# ----------------- ASOSIY QIDIRUV FUNKSIYALARI -----------------

def get_parent_by_jshr(jshr):
    """JSHR bo'yicha ota-onani (id, name) qaytaradi."""
    c = sqlite3.connect(DB_NAME)
    cur = c.cursor()
    cur.execute("SELECT id, name FROM parents WHERE jshr=?", (jshr,))
    r = cur.fetchone()
    c.close()
    return r 

def get_parent_by_pid(pid):
    """Parent ID bo'yicha ota-onani (id, name) qaytaradi."""
    c = sqlite3.connect(DB_NAME)
    cur = c.cursor()
    cur.execute("SELECT id, name FROM parents WHERE id=?", (pid,))
    r = cur.fetchone()
    c.close()
    return r 

def get_children(pid):
    """Parent ID bo'yicha bolalarni (id, name) qaytaradi."""
    c = sqlite3.connect(DB_NAME)
    cur = c.cursor()
    cur.execute("SELECT id,name FROM children WHERE parent_id=?", (pid,))
    r = cur.fetchall()
    c.close()
    return r

def get_vaccines(cid):
    """Bola ID bo'yicha emlash jadvallarini (name, date) qaytaradi."""
    c = sqlite3.connect(DB_NAME)
    cur = c.cursor()
    cur.execute("SELECT name,date FROM vaccines WHERE child_id=? ORDER BY date", (cid,))
    r = cur.fetchall()
    c.close()
    return r

# ----------------- CHAT ID (KO'P QURILMA) FUNKSIYALARI -----------------


def add_parent_chat_id(pid, chat_id):
    """Ota-ona uchun yangi chat_id ni qo'shadi, faqat u bog'lanish mavjud bo'lmasa."""
    c = sqlite3.connect(DB_NAME)
    cur = c.cursor()
    
    # Tekshiruv: Ushbu parent_id bu chat_id bilan allaqachon bog'langanmi?
    cur.execute("SELECT 1 FROM parent_chats WHERE parent_id=? AND chat_id=?", (pid, chat_id))
    if cur.fetchone() is None:
        # Agar bog'lanish yo'q bo'lsa, qo'shamiz
        cur.execute("INSERT INTO parent_chats(parent_id, chat_id) VALUES(?, ?)", (pid, chat_id))
    
    c.commit()
    c.close()

def get_all_parent_chat_ids(pid):
    """Parent ID ga bog'langan barcha chat_id larni qaytaradi (Scheduler uchun)."""
    c = sqlite3.connect(DB_NAME)
    cur = c.cursor()
    cur.execute("SELECT chat_id FROM parent_chats WHERE parent_id=?", (pid,))
    r = cur.fetchall()
    c.close()
    return [row[0] for row in r] # [12345, 67890] kabi ro'yxat qaytadi

# ----------------- LOGOUT FUNKSIYALARI -----------------

def get_linked_parents_by_chat_id(chat_id):
    """Berilgan chat_id ga bog'langan barcha ota-onalarning (pid, jshr, name) ma'lumotini qaytaradi."""
    c = sqlite3.connect(DB_NAME)
    cur = c.cursor()
    cur.execute("""
        SELECT p.id, p.jshr, p.name 
        FROM parents p
        JOIN parent_chats pc ON p.id = pc.parent_id
        WHERE pc.chat_id = ?
    """, (chat_id,))
    r = cur.fetchall()
    c.close()
    return r # [(pid, jshr, name), ...]

def delete_chat_id_link(pid, chat_id):
    """Ma'lum bir JSHR (pid) va chat_id o'rtasidagi bog'lanishni o'chiradi."""
    c = sqlite3.connect(DB_NAME)
    cur = c.cursor()
    cur.execute("DELETE FROM parent_chats WHERE parent_id=? AND chat_id=?", (pid, chat_id))
    rows_deleted = cur.rowcount
    c.commit()
    c.close()
    return rows_deleted

def delete_all_chat_ids_for_user(chat_id):
    """Berilgan chat_id ga tegishli barcha bog'lanishlarni o'chiradi."""
    c = sqlite3.connect(DB_NAME)
    cur = c.cursor()
    cur.execute("DELETE FROM parent_chats WHERE chat_id=?", (chat_id,))
    rows_deleted = cur.rowcount
    c.commit()
    c.close()
    return rows_deleted

# ----------------- ADMIN FUNKSIYALARI -----------------

def add_parent_jshr(jshr, name):
    """Admin panel orqali yangi ota-onani qo'shadi."""
    c = sqlite3.connect(DB_NAME)
    cur = c.cursor()
    try:
        cur.execute("INSERT INTO parents(jshr, name) VALUES(?, ?)", (jshr, name))
        c.commit()
        pid = cur.lastrowid
    except sqlite3.IntegrityError:
        pid = None # JSHR band
    c.close()
    return pid

def add_child_db(pid, name, birth):
    """Admin panel orqali bolani qo'shadi."""
    c = sqlite3.connect(DB_NAME)
    cur = c.cursor()
    cur.execute("INSERT INTO children(parent_id, name, birth) VALUES(?, ?, ?)", (pid, name, birth))
    cid = cur.lastrowid
    c.commit()
    c.close()
    return cid

def add_vaccine_db(cid, name, date):
    """Admin panel orqali vaksina jadvalini qo'shadi."""
    c = sqlite3.connect(DB_NAME)
    cur = c.cursor()
    cur.execute("INSERT INTO vaccines(child_id, name, date) VALUES(?, ?, ?)", (cid, name, date))
    c.commit()
    c.close()