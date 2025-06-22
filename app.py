import os
import streamlit as st
from openai import OpenAI
from datetime import datetime
from gtts import gTTS
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="AI-интервью", page_icon="🍲")

secret_token = os.getenv("SECRET_TOKEN")
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
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

# Настройки OpenAI
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

st.title("AI-интервью: Семейные рецепты и воспоминания")
st.info("🧠 Ответьте на три вопроса — и получите уникальную историю!")

def generate_questions():
    prompt = (
        "Придумай 3 личных вопроса для интервью о семейных рецептах, традициях и воспоминаниях. "
        "Один вопрос — одна строка. Без пояснений."
    )
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Ты интервьюер."},
            {"role": "user", "content": prompt}
        ]
    )
    text = response.choices[0].message.content
    return [q.strip("•-1234567890. ").strip() for q in text.split("\n") if q.strip()][:3]

# Диалоговая память
if "messages" not in st.session_state:
    st.session_state.messages = []
if "questions" not in st.session_state:
    st.session_state.questions = generate_questions()
if "question_index" not in st.session_state:
    st.session_state.question_index = 0

# Отображение истории сообщений
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Вопросы и ответы
if st.session_state.question_index < len(st.session_state.questions):
    question = st.session_state.questions[st.session_state.question_index]
    with st.chat_message("ai"):
        st.markdown(question)

    user_input = st.chat_input("Ваш ответ...")

    st.markdown("#### Или загрузите аудиофайл (.mp3, .wav, .m4a):")
    audio_file = st.file_uploader("🎤 Голосовой ответ", type=["mp3", "wav", "m4a"])

    recognized_text = None

    if user_input:
        recognized_text = user_input
    elif audio_file:
        with st.spinner("🎧 Распознаётся голос..."):
            try:
                audio_bytes = audio_file.read()
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=BytesIO(audio_bytes),
                    filename=audio_file.name,
                    response_format="text"
                )
                recognized_text = transcript.strip()
                st.success(f"✅ Распознано: {recognized_text}")
            except Exception as e:
                st.error(f"❌ Ошибка при распознавании: {e}")

    if recognized_text:
        st.session_state.messages.append({"role": "ai", "content": question})
        st.session_state.messages.append({"role": "user", "content": recognized_text})
        st.session_state.question_index += 1
        st.rerun()

if st.session_state.question_index == len(st.session_state.questions):
    if st.button("✍️ Сгенерировать семейную историю"):
        full_dialogue = "\n".join(
            [f"Q: {m['content']}" if m['role'] == "ai" else f"A: {m['content']}"
             for m in st.session_state.messages]
        )
        story_prompt = (
            "На основе диалога напиши тёплую семейную историю (3–5 абзацев), "
            "сохранив названия блюд и личные детали."
        )
        with st.spinner("История создаётся..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Ты писатель, создающий трогательные истории."},
                        {"role": "user", "content": story_prompt + "\n\n" + full_dialogue}
                    ]
                )
                story = response.choices[0].message.content
                st.session_state.story = story
                st.success("✅ История готова!")
            except Exception as e:
                st.error(f"❌ Ошибка при генерации истории: {e}")

if "story" in st.session_state:
    st.markdown("### 📖 Семейная история")
    st.write(st.session_state.story)

    def generate_audio(text):
        tts = gTTS(text=text, lang="ru")
        audio_data = BytesIO()
        tts.write_to_fp(audio_data)
        audio_data.seek(0)
        return audio_data

    audio_file = generate_audio(st.session_state.story)
    st.audio(audio_file, format="audio/mp3")
    st.download_button("🎵 Скачать аудио", data=audio_file, file_name="family_story.mp3", mime="audio/mp3")

    filename = f"family_story_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    st.download_button("📄 Скачать текст", data=st.session_state.story, file_name=filename, mime="text/plain")