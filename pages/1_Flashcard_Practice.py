import streamlit as st

st.set_page_config(page_title="Flashcard Practice", layout="wide")

st.title("🧠 Flashcard Practice")

# Display user context
name = st.session_state.get("name", "Anonymous")
role = st.session_state.get("role", "Not specified")
st.markdown(f"👤 Practicing as **{name}**, for **{role}**")
st.markdown("---")

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

#Navigation Buttons: Left + right aligend 
left_col, center_col, right_col = st.columns([1, 4, 1])

with left_col:
    if st.button("⬅️ Previous"):
        if st.session_state.card_index > 0:
            st.session_state.card_index -= 1

with right_col:
    if st.button("Next ➡️"):
        if st.session_state.card_index < len(flashcards) - 1:
            st.session_state.card_index += 1


#Spacing before suggested answer 
st.markdown("<div style='margin-top: 30px'></div>", unsafe_allow_html=True)

#Suggested answer box 
with st.container():
    st.markdown("#### 💡 Suggested Answer")
    with st.expander("Click to show"):
        st.write(card["answer"])

#Centered recording button
st.markdown("<div style='margin-top: 40px'></div>", unsafe_allow_html=True)
st.markdown("<div style='text-align:center'>", unsafe_allow_html=True)
if st.button("🎙️ Start Recording"):
    st.info("Recording started")
st.markdown("</div>", unsafe_allow_html=True)
