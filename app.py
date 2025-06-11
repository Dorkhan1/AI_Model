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
    "start_msg": "🧠 Я задам тебе 5 вопросов. Ответь свободно!",
    "generate_btn": "✍️ Сгенерировать историю",
    "download_btn": "📄 Скачать историю",
    "audio_btn": "🎵 Скачать аудио",
    "result_title": "📖 Семейная история:",
    "spinner": "Генерация истории..."
}


def generate_questions():
    prompt = (
        "Придумай 5 тёплых и личных вопросов для интервью о семейных рецептах, традициях и воспоминаниях. "
        "Вопросы должны быть уникальными. Один вопрос — одна строка. Без лишнего текста."
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
    return questions[:5]


def generate_audio(text, lang="ru"):
    tts = gTTS(text=text, lang=lang)
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
        st.session_state["story"] = response.choices[0].message.content
        st.success("✅ Готово!")


if "story" in st.session_state:
    st.markdown(f"### {labels['result_title']}")
    st.write(st.session_state["story"])


    audio_file = generate_audio(st.session_state["story"])
    st.markdown("### 🎧 Аудиоверсия")
    st.audio(audio_file, format="audio/mp3")
    st.caption("⚠️ Если плеер не работает — скачайте аудио ниже. Файл безопасен и создан локально.")


    st.download_button(
        label=labels["audio_btn"],
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