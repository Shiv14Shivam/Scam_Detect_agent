import streamlit as st
import re, time
import speech_recognition as sr
from gtts import gTTS
import tempfile
from groq import Groq
from langdetect import detect

# ---------------- CONFIG ----------------
api_key = st.text_input("🔑 Enter your Groq API Key", type="password")

if not api_key:
    st.warning("Please enter your API key to start")
    st.stop()

client = Groq(api_key=api_key)

st.set_page_config(page_title="Scam Trap AI", page_icon="💬", layout="wide")

# ---------------- SESSION ----------------
for key, default in {
    "dark_mode": False,
    "history": [],
    "scam_type": "Unknown",
    "last_audio": None,
    "persona": "Student",
    "emotion": "Normal",
    "status": "Idle"
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ---------------- SIDEBAR ----------------
st.sidebar.title("⚙️ Settings")
st.session_state.dark_mode = st.sidebar.toggle("🌙 Dark Mode", st.session_state.dark_mode)

st.sidebar.markdown("### 🎭 Agent")
st.session_state.persona = st.sidebar.selectbox("Personality", ["Old Man", "Student", "Poor Person"])
st.session_state.emotion = st.sidebar.selectbox("Emotion", ["Normal", "Angry", "Scared", "Confused"])

st.sidebar.markdown("### 🧠 Scam Type")
st.sidebar.success(st.session_state.scam_type)

# ---------------- THEME COLORS ----------------
if st.session_state.dark_mode:
    BG = "#0f172a"
    CHAT = "#1e293b"
    LEFT = "#334155"
    RIGHT = "#14532d"
    TXT = "#e5e7eb"
    LANG_COLOR = "#93c5fd"
else:
    BG = "#e8f5e9"
    CHAT = "#ffffff"
    LEFT = "#ffffff"
    RIGHT = "#dcf8c6"
    TXT = "#111827"
    LANG_COLOR = "#0f766e"

# ---------------- CSS ----------------
st.markdown(f"""
<style>
.stApp {{
    background-color: {BG};
    color: {TXT};
}}

.header {{
    background:#075e54;
    color:white;
    padding:15px;
    border-radius:15px;
    text-align:center;
}}

.chat-container {{
    background:{CHAT};
    border-radius:20px;
    padding:15px;
    max-width:750px;
    margin:auto;
    box-shadow:0px 2px 10px rgba(0,0,0,0.1);
}}

.bubble-left {{
    background:{LEFT};
    padding:10px 14px;
    border-radius:14px;
    margin:6px;
    max-width:75%;
}}

.bubble-right {{
    background:{RIGHT};
    padding:10px 14px;
    border-radius:14px;
    margin:6px;
    max-width:75%;
    margin-left:auto;
}}

.status {{
    text-align:center;
    font-weight:bold;
    color:#f97316;
}}

.lang-text {{
    text-align:center;
    margin-top:6px;
    font-size:14px;
    color:{LANG_COLOR};
}}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.markdown("""
<div class="header">
📱 Scam Trap AI<br>
Trap scammers using AI with emotions & personalities
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="lang-text">
🌍 All Indian languages supported (Hindi, English, Marathi, Bengali, Tamil, Telugu, etc.)
</div>
""", unsafe_allow_html=True)

st.markdown(f"<div class='status'>🔔 Status: {st.session_state.status}</div>", unsafe_allow_html=True)

# ---------------- MAP ----------------
LANG_MAP = {"en":"en","hi":"hi","bn":"bn","ta":"ta","te":"te","mr":"mr","gu":"gu","kn":"kn","ml":"ml","pa":"pa"}
PERSONALITIES = {
    "Old Man":"an old village man",
    "Student":"a college student",
    "Poor Person":"a poor worker"
}
EMOTIONS = {
    "Normal":"calm",
    "Angry":"angry",
    "Scared":"scared",
    "Confused":"confused"
}

# ---------------- SCAM DETECTOR ----------------
def detect_scam(text):
    t=text.lower()
    if any(k in t for k in ["police","custody","arrest"]): return "Fake Police Scam"
    if any(k in t for k in ["lottery","won","kbc","prize"]): return "Lottery Scam"
    if any(k in t for k in ["loan","credit"]): return "Loan Scam"
    if any(k in t for k in ["bank","account","blocked","kyc","ekyc"]): return "Bank / KYC Scam"
    return "Unknown Scam"

# ---------------- AI REPLY ----------------
def generate_reply(scam_type,msg,persona,emotion):
    try: lang=detect(msg)
    except: lang="en"
    prompt=f"""
You are roleplaying as {PERSONALITIES[persona]}.
Emotion: {EMOTIONS[emotion]}.
Scam type: {scam_type}
Scammer: {msg}

Rules:
- Reply ONLY in same language.
- Do not say you are AI.
- Ask questions.
- Try to get phone, UPI, bank name, reason.

ONLY reply message.
"""
    r=client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role":"user","content":prompt}],
        temperature=0.7
    )
    return r.choices[0].message.content.strip(), lang

# ---------------- VOICE INPUT ----------------
def listen_voice():
    st.session_state.status="🎤 Listening..."
    r=sr.Recognizer()
    with sr.Microphone() as s: audio=r.listen(s)
    try:
        st.session_state.status="Processing..."
        return r.recognize_google(audio,language="en-IN")
    except:
        st.session_state.status="Idle"
        return None

# ---------------- CHAT ----------------
st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
for role,msg in st.session_state.history:
    if role=="Scammer":
        st.markdown(f"<div class='bubble-left'>🕵️ {msg}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='bubble-right'>🤖 {msg}</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

if st.session_state.last_audio:
    st.audio(st.session_state.last_audio)

# ---------------- INPUT ----------------
text_input=st.chat_input("💬 Type scammer message...")
voice_btn=st.button("🎤 Speak")

# ---------- TEXT ----------
if text_input:
    st.session_state.status="Typing..."
    st.session_state.history.append(("Scammer",text_input))
    if len(st.session_state.history)==1:
        st.session_state.scam_type=detect_scam(text_input)

    reply,lang=generate_reply(st.session_state.scam_type,text_input,st.session_state.persona,st.session_state.emotion)
    st.session_state.history.append(("AI",reply))

    tts=gTTS(reply,lang=LANG_MAP.get(lang,"en"))
    with tempfile.NamedTemporaryFile(delete=False,suffix=".mp3") as f:
        tts.save(f.name)
        st.session_state.last_audio=f.name

    st.session_state.status="Idle"
    st.rerun()

# ---------- VOICE ----------
if voice_btn:
    scam_text=listen_voice()
    if scam_text:
        st.session_state.history.append(("Scammer",scam_text))
        if len(st.session_state.history)==1:
            st.session_state.scam_type=detect_scam(scam_text)

        reply,lang=generate_reply(st.session_state.scam_type,scam_text,st.session_state.persona,st.session_state.emotion)
        st.session_state.history.append(("AI",reply))

        tts=gTTS(reply,lang=LANG_MAP.get(lang,"en"))
        with tempfile.NamedTemporaryFile(delete=False,suffix=".mp3") as f:
            tts.save(f.name)
            st.session_state.last_audio=f.name

        st.session_state.status="Idle"
        st.rerun()

# ---------------- RESET ----------------
if st.sidebar.button("🧹 Reset Chat"):
    st.session_state.history=[]
    st.session_state.scam_type="Unknown"
    st.session_state.last_audio=None
    st.session_state.status="Idle"
    st.rerun()
