import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime
from gtts import gTTS
from io import BytesIO


st.set_page_config(page_title="🍲 AI-интервью", page_icon="🍲")

load_dotenv()
SECRET_TOKEN = os.getenv("SECRET_TOKEN")

st.markdown("## 🔐 Введите токен для доступа")
user_token = st.text_input("Токен", type="password")

if user_token != SECRET_TOKEN:
    st.warning("Введите корректный токен для доступа.")
    st.stop()


load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


labels = {
    "title": "🍲 AI-интервью: Семейные рецепты и традиции",
    "start_msg": "🧠 Я задам тебе 5 вопросов. Ответь свободно!",
    "generate_btn": "✍️ Сгенерировать историю",
    "download_btn": "📄 Скачать текст истории",
    "result_title": "📖 Семейная история:",
    "spinner": "Генерация истории...",
    "audio_title": "🎧 Аудиоверсия истории",
    "audio_caption": "⚠️ Если плеер не работает — скачайте аудио ниже. Файл безопасен и сгенерирован локально.",
    "audio_download": "🎵 Скачать аудио"
}

# Генерация вопросов
def generate_questions():
    prompt = (
        "Придумай 5 тёплых и личных вопросов для интервью о семейных рецептах, традициях и воспоминаниях. "
        "Вопросы должны быть уникальными. Один вопрос — одна строка. Без лишнего текста."
    )
    system_msg = "Ты интервьюер, собирающий воспоминания и семейные традиции."

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt}
        ]
    )

    raw_text = response.choices[0].message.content
    questions = [q.strip("•-1234567890. ").strip() for q in raw_text.split("\n") if q.strip()]
    return questions[:5]


def generate_audio(text):
    tts = gTTS(text=text, lang="ru")
    audio_data = BytesIO()
    tts.write_to_fp(audio_data)
    audio_data.seek(0)
    return audio_data


st.title(labels["title"])
st.info(labels["start_msg"])

if "questions" not in st.session_state:
    st.session_state.questions = generate_questions()
    st.session_state.answers = [""] * len(st.session_state.questions)

for i, q in enumerate(st.session_state.questions):
    st.session_state.answers[i] = st.text_area(f"🤖 Вопрос {i+1}: {q}", value=st.session_state.answers[i])


if st.button(labels["generate_btn"]):
    interview_text = "\n".join([f"Q: {q}\nA: {a}" for q, a in zip(st.session_state.questions, st.session_state.answers)])
    story_prompt = (
        "На основе следующего интервью напиши трогательную и тёплую семейную историю (3–5 абзацев), "
        "обязательно сохранив уникальные детали и названия блюд из ответов, не добавляя вымышленных фамилий.\n\n" + interview_text
    )
    system_msg = "Ты писатель, создающий вдохновляющие семейные истории."

    with st.spinner(labels["spinner"]):
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": story_prompt}
            ]
        )
        st.session_state["story"] = response.choices[0].message.content
        st.success("✅ История готова!")

if "story" in st.session_state:
    st.markdown(f"### {labels['result_title']}")
    st.write(st.session_state["story"])


    audio_file = generate_audio(st.session_state["story"])

    # UI с аудио
    st.markdown(f"### {labels['audio_title']}")
    st.audio(audio_file, format="audio/mp3")
    st.caption(labels["audio_caption"])

    st.download_button(
        label=labels["audio_download"],
        data=audio_file,
        file_name="family_story.mp3",
        mime="audio/mp3"
    )

    filename = f"family_story_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    st.download_button(
        label=labels["download_btn"],
        data=st.session_state["story"],
        file_name=filename,
        mime="text/plain"
    )