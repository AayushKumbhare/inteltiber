import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode
import av
import asyncio
import websockets
import threading
import json


st.set_page_config(page_title="Flashcard Practice", layout="wide")

st.title("Flashcard Practice")

# Display user context

query = st.query_params
name = query.get("name", "Anonymous")
role = query.get("role", "Not specified")
st.markdown(
    f"""
    <p style='font-size: 1rem; margin-top: -10px;'>
        Practicing as <strong>{name}</strong>, for <strong>{role}</strong>
    </p>
    """,
    unsafe_allow_html=True
)
st.markdown("<div style='margin-top: 30px'></div>", unsafe_allow_html=True)


# Flashcard content
flashcards = [
    {"question": "Tell me about yourself.", "answer": "Use a brief career story + what you're looking for now."},
    {"question": "What is your greatest strength?", "answer": "Pick 1 strength and support with a real example."},
    {"question": "Describe a challenge you overcame.", "answer": "Use the STAR format to explain the situation and resolution."},
]

if "card_index" not in st.session_state:
    st.session_state.card_index = 0

card = flashcards[st.session_state.card_index]

# Flashcard Display
st.markdown(
    f"""
    <div style='
        display: flex;
        justify-content: center;
        align-items: center;
        height: 60vh;
    '>
        <div style='
            width: 70vw;
            height: 70vh;
            background-color: #2563eb;
            color: white;
            border-radius: 30px;
            padding: 40px;
            font-size: 2.5rem;
            font-weight: bold;
            display: flex;
            justify-content: center;
            align-items: center;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            text-align: center;
        '>
            {card['question']}
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Navigation Buttons
left_col, spacer, right_col = st.columns([1, 10, 1])

with left_col:
    if st.button("⬅️ Previous", key="prev_button"):
        st.session_state._go_prev = True

with right_col:
    if st.button("Next ➡️", key="next_button"):
        st.session_state._go_next = True

if st.session_state.get("_go_prev", False):
    if st.session_state.card_index > 0:
        st.session_state.card_index -= 1
    st.session_state._go_prev = False

if st.session_state.get("_go_next", False):
    if st.session_state.card_index < len(flashcards) - 1:
        st.session_state.card_index += 1
    st.session_state._go_next = False

# Spacing before suggested answer
st.markdown("<div style='margin-top: 30px'></div>", unsafe_allow_html=True)

# Suggested answer box
with st.container():
    st.markdown("#### Suggested Answer")
    with st.expander("Click to show"):
        st.write(card["answer"])


# === Upload Audio and Feedback JSON ===
st.markdown("### Upload Your Recorded Answer and Feedback")

uploaded_audio = st.file_uploader("Upload your `.wav` or `.mp3` audio file", type=["wav", "mp3"])
uploaded_json = st.file_uploader("Upload feedback `.json` file", type=["json"])

if uploaded_audio:
    st.audio(uploaded_audio, format="audio/wav")

if uploaded_audio and uploaded_json:
    if st.button("Submit and Show Feedback"):
        try:
            import json

            feedback_data = json.load(uploaded_json)

            st.success("✅ Feedback loaded!")

            st.markdown("### Transcript")
            st.markdown(feedback_data.get("transcript", "_No transcript in file._"))

            st.markdown("### Filler Word Analysis")
            st.json(feedback_data.get("analysis", {}))

            st.markdown("### Words Per Minute (WPM)")
            st.write(feedback_data.get("wpm", "N/A"))

        except Exception as e:
            st.error(f"Failed to parse feedback: {e}")
