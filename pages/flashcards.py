import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode
import av
import asyncio
import websockets
import threading

st.set_page_config(page_title="Flashcard Practice", layout="wide")

st.title("Flashcard Practice")

# Display user context
name = st.session_state.get("name", "Anonymous")
role = st.session_state.get("role", "Not specified")
st.markdown(f"Practicing as **{name}**, for **{role}**")
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

# Navigation Buttons
left_col, spacer, right_col = st.columns([1, 6, 1])

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

# === Realtime WebSocket Audio Streaming ===
st.markdown("### Live Audio Recording (WebSocket Streamed)")

class WebSocketAudioStreamer(AudioProcessorBase):
    def __init__(self) -> None:
        self.ws_url = "http://172.31.22.1:8501"  
        self.connected = False
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._start_loop, daemon=True)
        self.thread.start()

    def _start_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._connect())

    async def _connect(self):
        try:
            self.websocket = await websockets.connect(self.ws_url)
            self.connected = True
        except Exception as e:
            print(f"[WebSocket Error] {e}")

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        if self.connected:
            try:
                pcm_bytes = frame.to_ndarray().flatten().tobytes()
                asyncio.run_coroutine_threadsafe(self.websocket.send(pcm_bytes), self.loop)
            except Exception as e:
                print(f"[WebSocket Send Error] {e}")
        return frame

ctx = webrtc_streamer(
    key="audio_streamer",
    mode=WebRtcMode.SENDONLY,
    audio_processor_factory=WebSocketAudioStreamer,
    media_stream_constraints={"audio": True, "video": False},
)

if ctx.state.playing:
    st.success("Streaming live audio to backend...")
else:
    st.info("Click 'Start' above to begin recording.")
