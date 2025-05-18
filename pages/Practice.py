import streamlit as st
import json
import os

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


# === Load flashcards from local JSON file (with full question text as keys) ===
if os.path.exists("interview_combined_20250517_190401.json"):
    with open("interview_combined_20250517_190401.json", "r") as f:
        raw_data = json.load(f)

    # Convert to flashcard format using 'question' and 'ai_answer'
    flashcards = [
        {"question": item["question"], "answer": item["ai_answer"], "feedback": item["feedback"]}
        for item in raw_data
    ]
else:
    flashcards = [{"question": "No flashcards loaded.", "answer": "", "feedback": ""}]

# === Initialize session state for card navigation ===
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


# === Upload Audio and Load Local Feedback JSON ===
st.markdown("### Upload Your Recorded Answer")

uploaded_audio = st.file_uploader("Upload your `.wav` or `.mp3` audio file", type=["wav", "mp3"])

if uploaded_audio is not None:
    st.audio(uploaded_audio, format="audio/wav")
    local_audio_path = os.path.join("tmp", uploaded_audio.name)
    os.makedirs("tmp", exist_ok=True)
    with open(local_audio_path, "wb") as f:
        f.write(uploaded_audio.read())
    st.session_state["uploaded_audio_path"] = local_audio_path

    if st.button("Transcribe and Show Feedback"):
        from transcript import run_transcription
        run_transcription(local_audio_path)
audio_name = uploaded_audio.name

if uploaded_audio:
    st.audio(uploaded_audio, format="audio/wav")

    if st.button("Submit and Show Feedback"):
        try:
            import json

            # Load local feedback file
            if os.path.exists("interview_combined_20250517_190401.json"):
                with open("interview_combined_20250517_190401.json", "r") as f:
                    feedback_list = json.load(f)

                current_question = card["question"]

                # Find feedback matching current question
                match = next((entry for entry in feedback_list if entry["question"] == current_question), None)

                if match:
                    st.success("Feedback loaded")

                    st.markdown("### Feedback")
                    st.warning(match.get("feedback", "No feedback found."))
                else:
                    st.error("No matching feedback found for this question.")
            else:
                st.error("file not found.")

        except Exception as e:
            st.error(f"Failed to load or parse feedback: {e}")
