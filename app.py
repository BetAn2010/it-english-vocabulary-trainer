import sqlite3
import random
import io
import re
import streamlit as st
from gtts import gTTS

DB_NAME = "it_english.db"
ITEMS_PER_PAGE = 20

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_and_fix_db():
    """Перевірка та підтримка будь-якої структури таблиці."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='terms'")
    if not cursor.fetchone():
        cursor.execute("""
            CREATE TABLE terms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT DEFAULT 'Загальне',
                term TEXT NOT NULL,
                transcription TEXT,
                transcription_ua TEXT,
                translation TEXT NOT NULL,
                context TEXT DEFAULT '',
                example_en TEXT DEFAULT '',
                example_ua TEXT DEFAULT ''
            )
        """)
    conn.commit()
    conn.close()

init_and_fix_db()

@st.cache_data(ttl=300)
def fetch_categories():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT category FROM terms ORDER BY category")
    categories = [row["category"] for row in cursor.fetchall() if row["category"]]
    conn.close()
    return categories

def fetch_terms_paginated(category=None, search_query=None, page=1, limit=ITEMS_PER_PAGE):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM terms WHERE 1=1"
    count_query = "SELECT COUNT(*) FROM terms WHERE 1=1"
    params = []
    
    if category and category != "Всі категорії":
        query += " AND category = ?"
        count_query += " AND category = ?"
        params.append(category)
        
    if search_query:
        query += " AND (term LIKE ? OR translation LIKE ? OR context LIKE ?)"
        count_query += " AND (term LIKE ? OR translation LIKE ? OR context LIKE ?)"
        pattern = f"%{search_query}%"
        params.extend([pattern, pattern, pattern])
        
    cursor.execute(count_query, params)
    total_count = cursor.fetchone()[0]
    
    offset = (page - 1) * limit
    query += " ORDER BY id ASC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(r) for r in rows], total_count

def clean_text(text: str) -> str:
    """Видаляє цифри та номери версій з тексту."""
    if not text:
        return ""
    cleaned = re.sub(r'\bv?\d+\b', '', text, flags=re.IGNORECASE)
    cleaned = re.sub(r'^\d+[\.\)]\s*', '', cleaned)
    return re.sub(r'\s+', ' ', cleaned).strip()

def generate_audio(text: str):
    clean_t = clean_text(text)
    if not clean_t:
        clean_t = "Empty"
    tts = gTTS(text=clean_t, lang='en')
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    return fp

# -------------------------------------------------------------------
# Streamlit UI
# -------------------------------------------------------------------
st.set_page_config(
    page_title="IT English Vocabulary (5000+ Cards)",
    page_icon="💻",
    layout="wide"
)

st.title("💻 IT English Vocabulary Trainer")
st.caption("База з 5000+ індивідуальних IT-карток")

st.sidebar.header("📌 Навігація та Фільтри")

categories = ["Всі категорії"] + fetch_categories()
selected_category = st.sidebar.selectbox("Оберіть категорію:", categories)
search_term = st.sidebar.text_input("🔍 Пошук терміну:", value="")

mode = st.sidebar.radio(
    "Режим роботи:", 
    ["Словник / Списком", "Картки (Flashcards)", "Тренажер / Квіз"]
)

if "current_page" not in st.session_state:
    st.session_state.current_page = 1

# -------------------------------------------------------------------
# Режим 1: Словник / Списком (Посторінкова навігація)
# -------------------------------------------------------------------
if mode == "Словник / Списком":
    st.subheader("📚 Список IT-карток")
    
    terms, total_terms = fetch_terms_paginated(
        category=selected_category, 
        search_query=search_term, 
        page=st.session_state.current_page
    )
    
    st.sidebar.markdown("---")
    st.sidebar.info(f"Всього знайдено карток: **{total_terms}**")
    
    total_pages = max(1, (total_terms + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    
    col_p1, col_p2, col_p3 = st.columns([1, 2, 1])
    with col_p1:
        if st.button("⬅️ Попередня сторінка") and st.session_state.current_page > 1:
            st.session_state.current_page -= 1
            st.rerun()
    with col_p2:
        st.write(f"Сторінка **{st.session_state.current_page}** з **{total_pages}**")
    with col_p3:
        if st.button("Наступна сторінка ➡️") and st.session_state.current_page < total_pages:
            st.session_state.current_page += 1
            st.rerun()

    st.markdown("---")

    if not terms:
        st.warning("Карток не знайдено.")
    else:
        for item in terms:
            item_id = item.get('id')
            term_clean = clean_text(item['term'])
            ex_en_clean = clean_text(item.get('example_en', ''))
            
            with st.expander(f"🇬🇧 **{term_clean}** — {item['translation']} [{item.get('category', 'General')}]"):
                # Номер картки (ID) окремим рядком
                st.caption(f"🔢 **Номер картки:** `{item_id}`")
                
                col1, col2 = st.columns([1, 2])
                with col1:
                    if item.get('transcription'):
                        st.code(item['transcription'], language="text")
                    if item.get('transcription_ua'):
                        st.write(f"🇺🇦 **Вимова (UA):** `{item['transcription_ua']}`")
                        
                    if st.button("🔊 Озвучити термін", key=f"audio_t_{item_id}"):
                        st.audio(generate_audio(term_clean), format="audio/mp3")
                
                with col2:
                    st.write(f"📖 **Контекст:** {item.get('context', '')}")
                    if ex_en_clean:
                        st.markdown(f"💬 **Приклад (EN):** *{ex_en_clean}*")
                        
                        # Кнопка озвучення прикладу без номерів
                        if st.button("🔊 Озвучити приклад (EN)", key=f"audio_ex_{item_id}"):
                            st.audio(generate_audio(ex_en_clean), format="audio/mp3")
                            
                    if item.get('example_ua'):
                        st.markdown(f"🇺🇦 **Переклад прикладу:** {item['example_ua']}")

# -------------------------------------------------------------------
# Режим 2: Flashcards (Окремі картки)
# -------------------------------------------------------------------
elif mode == "Картки (Flashcards)":
    st.subheader("🟨 Інтерактивні картки")
    
    terms, total_terms = fetch_terms_paginated(
        category=selected_category, 
        search_query=search_term, 
        page=1, 
        limit=5000
    )
    
    if not terms:
        st.warning("Немає доступних карток.")
    else:
        if "card_index" not in st.session_state:
            st.session_state.card_index = 0

        current = terms[st.session_state.card_index % len(terms)]
        item_id = current.get('id')
        term_clean = clean_text(current['term'])
        ex_en_clean = clean_text(current.get('example_en', ''))

        col_prev, col_info, col_next = st.columns([1, 2, 1])
        with col_prev:
            if st.button("⬅️ Попередня"):
                st.session_state.card_index = (st.session_state.card_index - 1) % len(terms)
                st.rerun()

        with col_info:
            st.write(f"Картка **{(st.session_state.card_index % len(terms)) + 1}** з **{len(terms)}**")

        with col_next:
            if st.button("Наступна ➡️"):
                st.session_state.card_index = (st.session_state.card_index + 1) % len(terms)
                st.rerun()

        st.markdown("---")
        
        # Номер картки окремим рядком
        st.caption(f"🔢 **Номер картки (ID):** `{item_id}`")
        st.markdown(f"### 🇬🇧 {term_clean}")
        
        if current.get('transcription'):
            st.code(current['transcription'], language="text")
        if current.get('transcription_ua'):
            st.write(f"🇺🇦 **Вимова (UA):** `{current['transcription_ua']}`")
        
        if st.button("🔊 Озвучити термін", key=f"audio_card_{item_id}"):
            st.audio(generate_audio(term_clean), format="audio/mp3")

        show_answer = st.checkbox("Показати переклад та контекст", key=f"card_check_{item_id}")
        
        if show_answer:
            st.success(f"**Переклад:** {current['translation']}")
            st.info(f"**Контекст:** {current.get('context', '')}")
            
            if ex_en_clean:
                st.markdown(f"**Приклад:** {ex_en_clean}")
                if st.button("🔊 Озвучити приклад (EN)", key=f"audio_card_ex_{item_id}"):
                    st.audio(generate_audio(ex_en_clean), format="audio/mp3")
                
            if current.get('example_ua'):
                st.markdown(f"**Переклад прикладу:** {current['example_ua']}")

# -------------------------------------------------------------------
# Режим 3: Квіз / Тренажер
# -------------------------------------------------------------------
elif mode == "Тренажер / Квіз":
    st.subheader("🎯 Перевірка знань")
    
    terms, total_terms = fetch_terms_paginated(
        category=selected_category, 
        page=1, 
        limit=100
    )
    
    if len(terms) < 4:
        st.warning("Потрібно принаймні 4 терміни.")
    else:
        if "quiz_term" not in st.session_state or st.button("🔄 Наступне питання"):
            st.session_state.quiz_term = random.choice(terms)
            correct = st.session_state.quiz_term['translation']
            others = [t['translation'] for t in terms if t['translation'] != correct]
            
            options = random.sample(others, min(3, len(others))) + [correct]
            random.shuffle(options)
            st.session_state.quiz_options = options

        q = st.session_state.quiz_term
        term_clean = clean_text(q['term'])
        
        st.caption(f"🔢 **Номер картки (ID):** `{q.get('id')}`")
        st.markdown(f"### Як перекладається термін: **{term_clean}**?")
        if q.get('transcription_ua'):
            st.caption(f"Вимова: `{q['transcription_ua']}`")

        selected_option = st.radio("Оберіть варіант відповіді:", st.session_state.quiz_options)

        if st.button("Перевірити"):
            if selected_option == q['translation']:
                st.balloons()
                st.success("🎉 Правильно!")
            else:
                st.error(f"❌ Невірно. Правильний переклад: **{q['translation']}**")