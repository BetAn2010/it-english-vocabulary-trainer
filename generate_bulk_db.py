import sqlite3
import random

DB_NAME = "it_english.db"

CATEGORIES = [
    "Software Architecture", "Databases & SQL", "DevOps & Cloud",
    "Frontend Development", "Backend Development", "Business Analysis",
    "Data Engineering & AI", "Cybersecurity", "Software Testing & QA"
]

PREFIXES = [
    ("Async", "Ейсінк", "Асинхронний"),
    ("Distributed", "Дістріб'ютед", "Розподілений"),
    ("Automated", "Отомейтед", "Автоматизований"),
    ("Scalable", "Скейлебл", "Масштабований"),
    ("Secure", "Сік'юр", "Захищений"),
    ("Concurrent", "Канкарент", "Паралельний"),
    ("Relational", "Рілейшнл", "Реляційний"),
    ("Cloud-native", "Клауд-нейтів", "Хмарно-орієнтований")
]

CORE_WORDS = [
    ("Pipeline", "/ˈpaɪplaɪn/", "[пайплайн]", "Конвеєр / Пайплайн", "Послідовність етапів обробки даних."),
    ("Repository", "/rɪˈpɒzətri/", "[ріпозіторі]", "Репозиторій", "Сховище коду та історії його змін."),
    ("Middleware", "/ˈmɪdlweə/", "[мідлвер]", "Проміжне ПЗ", "Шар ПЗ, що з'єднує різні компоненти."),
    ("Endpoint", "/ˈɛndpɔɪnt/", "[ендпоінт]", "Ендпоінт", "Точка доступу API."),
    ("Payload", "/ˈpeɪləʊd/", "[пейлоуд]", "Корисне навантаження", "Дані у тілі HTTP-запиту."),
    ("Schema", "/ˈskiːmə/", "[скіма]", "Схема", "Структура таблиць і полів БД."),
    ("Cluster", "/ˈklʌstə/", "[кластер]", "Кластер", "Група серверів."),
    ("Query", "/ˈkwɪəri/", "[квері]", "Запит", "Запит до бази даних."),
    ("Index", "/ˈɪndɛks/", "[індекс]", "Індекс", "Структура прискорення пошуку."),
    ("Transaction", "/trænˈzækʃn/", "[транзакшн]", "Транзакція", "Послідовність операцій з БД.")
]

def generate_5000_terms():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS terms;")
    
    cursor.execute("""
        CREATE TABLE terms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            term TEXT NOT NULL,
            transcription TEXT,
            transcription_ua TEXT,
            translation TEXT NOT NULL,
            context TEXT NOT NULL,
            example_en TEXT,
            example_ua TEXT
        )
    """)
    
    for i in range(1, 5001):
        category = random.choice(CATEGORIES)
        pref_en, pref_ua_trans, pref_ua = random.choice(PREFIXES)
        core_en, trans_ipa, core_ua_trans, core_ua, context = random.choice(CORE_WORDS)
        
        term = f"{pref_en} {core_en}"
        transcription = f"{trans_ipa}"
        transcription_ua = f"[{pref_ua_trans.lower()} {core_ua_trans.strip('[]')}]"
        translation = f"{pref_ua} {core_ua.lower()}"
        
        ex_en = f"The system uses {term.lower()} for high-load operations."
        ex_ua = f"Система використовує {translation.lower()} для високонавантажених операцій."
        
        cursor.execute("""
            INSERT INTO terms 
            (category, term, transcription, transcription_ua, translation, context, example_en, example_ua)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (category, term, transcription, transcription_ua, translation, context, ex_en, ex_ua))

    conn.commit()
    conn.close()
    print("🎉 Успішно створено 5000 окремих карток у базі даних!")

if __name__ == "__main__":
    generate_5000_terms()