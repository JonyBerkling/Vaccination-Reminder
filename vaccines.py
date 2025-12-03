from datetime import datetime, timedelta

# Vaksinalar haqida qisqacha ma'lumot
VACCINE_DESCRIPTIONS = {
    "VGB": "Gepatit B ga qarshi vaksina. Jigar kasalliklaridan himoya qiladi.",
    "BSJ": "Sil (Tuberkulyoz) kasalligiga qarshi vaksina.",
    "OPV": "Poliomielitga (shol kasalligi) qarshi og'iz orqali tomiziladigan vaksina.",
    "IPV": "Poliomielitga qarshi inyeksiya (ukol) shaklidagi vaksina.",
    "Penta": "Beshta kasallikka qarshi (Bo'g'ma, Qoqoq, Ko'k yo'tal, Gepatit B, XIB).",
    "Rota": "Rotavirus infeksiyasiga (ich ketish) qarshi vaksina.",
    "Pneumo": "Pnevmokokk (zotiljam, meningit) kasalliklariga qarshi.",
    "KPK": "Qizamiq, Parotit (tepki), Qizilcha kasalliklariga qarshi.",
    "AKDS": "Bo'g'ma, Qoqoq va Ko'k yo'talga qarshi vaksina.",
    "ADS-M": "Bo'g'ma va Qoqoqqa qarshi (o'smirlar uchun).",
    "VPCH": "Odam papilloma virusiga qarshi (bachadon bo'yni saratonini oldini olish uchun)."
}

def get_vaccine_info():
    text = "💉 **Vaksinalar haqida ma'lumot:**\n\n"
    for k, v in VACCINE_DESCRIPTIONS.items():
        text += f"🔹 **{k}**: {v}\n"
    return text

def calc_dates(birth):
    d = datetime.strptime(birth, "%Y-%m-%d")
    r = []

    add = lambda name, date: r.append((name, date.strftime("%Y-%m-%d")))

    add("VGB-1", d + timedelta(days=1))
    add("OPV-0 + BSJ-1", d + timedelta(days=2))
    add("Penta-1 / OPV-1 / Rota-1 / Pneumo-1", d + timedelta(days=60))
    add("Penta-2 / OPV-2 / Rota-2 / Pneumo-2", d + timedelta(days=90))
    add("Penta-3 / OPV-3 / IPV", d + timedelta(days=120))
    add("KPK-1 / Pneumo-3", d.replace(year=d.year+1))
    add("AKDS-4 / OPV-4", d + timedelta(days=480))
    add("KPK-2", d.replace(year=d.year+6))
    add("ADS-M-5 / OPV-5", d.replace(year=d.year+7))
    add("VPCH (9-12 yosh)", d.replace(year=d.year+9))
    add("ADS-M-6 (16 yosh)", d.replace(year=d.year+16))

    return r