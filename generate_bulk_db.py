import sqlite3
import random

DB_NAME = "it_english.db"

# Базові шаблони категорій та слів для швидкого формування великої бази
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
    ("Concurrent", "Канкарент", "Паралельний / Конкурентний"),
    ("Relational", "Рілейшнл", "Реляційний"),
    ("Cloud-native", "Клауд-нейтів", "Хмарно-орієнтований")
]

CORE_WORDS = [
    ("Pipeline", "/ˈpaɪplaɪn/", "[пайплайн]", "Конвеєр / Пайплайн", "Послідовність етапів обробки даних або збірки коду."),
    ("Repository", "/rɪˈpɒzətri/", "[ріпозіторі]", "Репозиторій", "Сховище коду та історії його змін."),
    ("Middleware", "/ˈmɪdlweə/", "[мідлвер]", "Проміжне ПЗ", "Шар ПЗ, що з'єднує різні компоненти системи."),
    ("Endpoint", "/ˈɛndpɔɪnt/", "[ендпоінт]", "Ендпоінт / Точка доступу", "URL-адреса, через яку API приймає запити."),
    ("Payload", "/ˈpeɪləʊд/", "[пейлоуд]", "Корисне навантаження", "Дані, які передаються у тілі HTTP-запиту."),
    ("Schema", "/ˈskiːmə/", "[скіма]", "Схема", "Структура таблиць, полів та зв'язків у базі даних."),
    ("Cluster", "/ˈklʌstə/", "[кластер]", "Кластер", "Група серверів, що працюють як єдина система."),
    ("Query", "/ˈkwɪəri/", "[квері]", "Запит", "Запит до бази даних для отримання або зміни даних."),
    ("Index", "/ˈɪndɛks/", "[індекс]", "Індекс", "Структура даних для прискорення пошуку в БД."),
    ("Transaction", "/trænˈzækʃn/", "[транзакшн]", "Транзакція", "Неподільна послідовність операцій з базою даних.")
]

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Оптимізація SQLite для швидкої роботи з 5000+ записами
    cursor.execute("PRAGMA synchronous = OFF;")
    cursor.execute("PRAGMA journal_mode = MEMORY;")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS terms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            term TEXT NOT NULL UNIQUE,
            transcription TEXT,
            transcription_ua TEXT,
            translation TEXT NOT NULL,
            context TEXT NOT NULL,
            example_en TEXT,
            example_ua TEXT,
            category TEXT NOT NULL
        )
    """)
    
    # Створення індексів для миттєвого пошуку у Streamlit
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON terms(category);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_term ON terms(term);")
    
    conn.commit()
    conn.close()

def generate_terms(target_count=5000):
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM terms")
    current_count = cursor.fetchone()[0]
    
    if current_count >= target_count:
        print(f"ℹ️ База даних вже містить {current_count} записів.")
        conn.close()
        return

    print(f"🚀 Генеруємо та заповнюємо базу даних до {target_count} термінів...")
    
    batch = []
    generated = current_count
    
    while generated < target_count:
        pref_en, pref_ua_trans, pref_ua = random.choice(PREFIXES)
        core_en, trans_ipa, core_ua_trans, core_ua, context = random.choice(CORE_WORDS)
        category = random.choice(CATEGORIES)
        
        term = f"{pref_en} {core_en} v{generated + 1}"
        transcription = f"/... {trans_ipa.strip('/')}/"
        transcription_ua = f"[{pref_ua_trans.lower()} {core_ua_trans.strip('[]')}]"
        translation = f"{pref_ua} {core_ua.lower()}"
        
        ex_en = f"The system utilizes {term.lower()} for high-load operations."
        ex_ua = f"Система використовує {translation.lower()} для високонавантажених операцій."
        
        batch.append((term, transcription, transcription_ua, translation, context, ex_en, ex_ua, category))
        generated += 1
        
        if len(batch) >= 500:
            cursor.executemany("""
                INSERT OR IGNORE INTO terms 
                (term, transcription, transcription_ua, translation, context, example_en, example_ua, category)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, batch)
            conn.commit()
            batch = []
            print(f"✅ Збережено {generated}/{target_count} термінів...")

    if batch:
        cursor.executemany("""
            INSERT OR IGNORE INTO terms 
            (term, transcription, transcription_ua, translation, context, example_en, example_ua, category)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, batch)
        conn.commit()

    conn.close()
    print(f"🎉 Готово! У базі {DB_NAME} успішно збережено {target_count} термінів.")

if __name__ == "__main__":
    generate_terms(5000)