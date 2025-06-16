import os
import streamlit as st
from openai import OpenAI
from datetime import datetime
from gtts import gTTS
from io import BytesIO

secret_token = os.getenv("SECRET_TOKEN")
if secret_token is None:
    from dotenv import load_dotenv
    load_dotenv()
    secret_token = os.getenv("SECRET_TOKEN")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.set_page_config(page_title="🍲 AI-интервью", page_icon="🍲")
    st.markdown("## 🔐 Введите токен для доступа")

    with st.form("auth_form"):
        user_token = st.text_input("Токен", type="password")
        submitted = st.form_submit_button("Войти")

    if submitted:
        if user_token == secret_token:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ Неверный токен. Доступ запрещён.")
    st.stop()

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

labels = {
    "title": "🍲 AI-интервью: Семейные рецепты и традиции",
    "start_msg": "🧠 Ответьте на 3 вопроса, и я составлю вашу историю",
    "generate_btn": "✍️ Составить историю",
    "download_btn": "📄 Скачать историю",
    "audio_btn": "🎵 Скачать аудио",
    "result_title": "📖 Семейная история:",
    "spinner": "Генерация истории..."
}

def generate_questions():
    prompt = (
        "Придумай 3 тёплых и личных вопроса для интервью о семейных рецептах, традициях и воспоминаниях. "
        "Один вопрос — одна строка. Без лишнего текста."
    )
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Ты интервьюер, собирающий семейные воспоминания и рецепты."},
            {"role": "user", "content": prompt}
        ]
    )
    raw_text = response.choices[0].message.content
    questions = [q.strip("•-1234567890. ").strip() for q in raw_text.split("\n") if q.strip()]
    return questions[:3]

def generate_audio(text, lang="ru"):
    tts = gTTS(text=text, lang=lang)
    audio_data = BytesIO()
    tts.write_to_fp(audio_data)
    audio_data.seek(0)
    return audio_data

# Состояния
if "step" not in st.session_state:
    st.session_state.step = 0
if "questions" not in st.session_state:
    st.session_state.questions = generate_questions()
if "answers" not in st.session_state:
    st.session_state.answers = []
if "story" not in st.session_state:
    st.session_state.story = None

# Интерфейс
st.title(labels["title"])
st.info(labels["start_msg"])

if st.session_state.step < len(st.session_state.questions):
    question = st.session_state.questions[st.session_state.step]
    answer = st.text_input(f"🤖 Вопрос {st.session_state.step + 1}: {question}", key=f"answer_{st.session_state.step}")
    if st.button("Ответить"):
        if answer.strip():
            st.session_state.answers.append(answer)
            st.session_state.step += 1
            st.experimental_rerun()
        else:
            st.warning("Пожалуйста, введите ответ.")

elif st.session_state.story is None:
    interview_text = "\n".join([f"Q: {q}\nA: {a}" for q, a in zip(st.session_state.questions, st.session_state.answers)])
    story_prompt = (
        "На основе следующего интервью напиши тёплую семейную историю (3–5 абзацев), "
        "сохранив реальные названия блюд и не добавляя вымышленных фамилий.\n\n" + interview_text
    )
    with st.spinner(labels["spinner"]):
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты писатель, создающий вдохновляющие семейные истории."},
                {"role": "user", "content": story_prompt}
            ]
        )
        st.session_state.story = response.choices[0].message.content
        st.success("✅ Готово!")
        st.experimental_rerun()
else:
    st.markdown(f"### {labels['result_title']}")
    st.write(st.session_state.story)

    audio_file = generate_audio(st.session_state.story)
    st.audio(audio_file, format="audio/mp3")
    st.download_button(labels["audio_btn"], data=audio_file, file_name="family_story.mp3", mime="audio/mp3")

    filename = f"family_story_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    st.download_button(labels["download_btn"], data=st.session_state.story, file_name=filename, mime="text/plain")
