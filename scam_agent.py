import streamlit as st
import re, os
from groq import Groq
from langdetect import detect
from gtts import gTTS
import tempfile

# ---------------- SAFE VOICE IMPORT ----------------
try:
    import speech_recognition as sr
    VOICE_ENABLED = True
except:
    VOICE_ENABLED = False

# Disable voice on cloud
if "STREAMLIT_SERVER_RUNNING" in os.environ:
    VOICE_ENABLED = False

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Scam Agent", page_icon="🪤", layout="wide")

st.title("🪤 Scam Agent")
st.markdown("**AI system that traps scammers & extracts evidence**")
st.info("🌍 Supports ALL languages (Hindi, English, Marathi, Bengali, Telugu, Tamil, etc.)")

api_key = st.text_input("🔑 Enter your Groq API Key", type="password")
if not api_key:
    st.warning("Please enter API key to start")
    st.stop()

client = Groq(api_key=api_key)

# ---------------- SESSION ----------------
for key, default in {
    "history": [],
    "scam_type": "Unknown",
    "mode": "Normal Chat",
    "persona": "Old Man",
    "emotion": "Normal",
    "last_audio": None
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ---------------- SIDEBAR ----------------
st.sidebar.title("⚙️ Controls")
st.session_state.mode = st.sidebar.radio("Mode", ["Normal Chat", "🪤 Honeypot Trap"])
st.session_state.persona = st.sidebar.selectbox("Persona", ["Old Man","Student","Poor Person"])
st.session_state.emotion = st.sidebar.selectbox("Emotion", ["Normal","Angry","Scared","Confused"])

st.sidebar.markdown("### 🧠 Scam Type")
st.sidebar.success(st.session_state.scam_type)

# ---------------- MAP ----------------
PERSONA_DESC = {
    "Old Man":"an old village man",
    "Student":"a college student",
    "Poor Person":"a poor daily wage worker"
}

EMOTION_DESC = {
    "Normal":"calm",
    "Angry":"angry",
    "Scared":"scared",
    "Confused":"confused"
}

LANG_MAP={"en":"en","hi":"hi","bn":"bn","ta":"ta","te":"te","mr":"mr","gu":"gu","kn":"kn","ml":"ml","pa":"pa"}

# ---------------- SCAM DETECTOR (EXTENDED) ----------------
def detect_scam(text):
    t = text.lower()
    if any(k in t for k in ["police","arrest","custody","court"]): return "Fake Police Scam"
    if any(k in t for k in ["kyc","ekyc","verify kyc"]): return "KYC Scam"
    if any(k in t for k in ["upi","google pay","phonepe","paytm"]): return "UPI Scam"
    if any(k in t for k in ["atm","pin","card number"]): return "ATM / PIN Scam"
    if any(k in t for k in ["otp","one time password"]): return "OTP Scam"
    if any(k in t for k in ["lottery","kbc","won","prize"]): return "Lottery Scam"
    if any(k in t for k in ["bank","blocked","account suspend"]): return "Bank Scam"
    if any(k in t for k in ["loan","credit"]): return "Loan Scam"
    if any(k in t for k in ["investment","crypto","double money"]): return "Investment Scam"
    if any(k in t for k in ["job","salary","work from home"]): return "Job Scam"
    if any(k in t for k in ["http","www","link"]): return "Phishing Link Scam"
    return "Unknown Scam"

# ---------------- EVIDENCE EXTRACT ----------------
def extract_evidence(text):
    upi = re.findall(r'\b[\w.-]+@[\w.-]+\b', text)
    phones = re.findall(r'\b\d{10}\b', text)
    links = re.findall(r'https?://\S+', text)
    return upi, phones, links

# ---------------- HONEYPOT AGENT ----------------
def honeypot_agent(scam_type,msg,persona,emotion):
    try: lang=detect(msg)
    except: lang="en"

    prompt=f"""
You are pretending to be {PERSONA_DESC[persona]}.
Emotion: {EMOTION_DESC[emotion]}.

Scam type: {scam_type}
Scammer message: {msg}

GOALS:
1. Act innocent & human.
2. Keep scammer talking.
3. Try to get:
   - UPI
   - Phone number
   - Bank name
   - Payment reason
   - Phishing link

RULES:
- Do NOT say you are AI.
- Ask short natural questions.
- Reply ONLY in same language.

Reply only with next message.
"""
    r=client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role":"user","content":prompt}],
        temperature=0.7
    )
    return r.choices[0].message.content.strip(), lang

# ---------------- NORMAL ANALYSIS MODE ----------------
def analyze_call(text):
    try: lang=detect(text)
    except: lang="en"

    prompt=f"""
You are a fraud detection AI.
Analyze the following call message:

{text}

Rules:
- Reply in same language.
- Warn user if scam.
- Explain briefly.
"""
    r=client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role":"user","content":prompt}],
        temperature=0.4
    )
    return r.choices[0].message.content.strip(), lang

# ---------------- CHAT UI ----------------
st.subheader("💬 Conversation")

for role,msg in st.session_state.history:
    if role=="Scammer":
        st.chat_message("user").write(msg)
    else:
        st.chat_message("assistant").write(msg)

if st.session_state.last_audio:
    st.audio(st.session_state.last_audio)

# ---------------- INPUT ----------------
text_input = st.chat_input("Type scammer message...")

if VOICE_ENABLED:
    voice_btn = st.button("🎤 Speak")
else:
    st.info("🎤 Voice works only in local mode")
    voice_btn=False

# ---------- TEXT ----------
if text_input:
    st.session_state.history.append(("Scammer",text_input))
    if len(st.session_state.history)==1:
        st.session_state.scam_type=detect_scam(text_input)

    if st.session_state.mode=="🪤 Honeypot Trap":
        reply,lang=honeypot_agent(st.session_state.scam_type,text_input,st.session_state.persona,st.session_state.emotion)
    else:
        reply,lang=analyze_call(text_input)

    st.session_state.history.append(("AI",reply))

    tts=gTTS(reply,lang=LANG_MAP.get(lang,"en"))
    with tempfile.NamedTemporaryFile(delete=False,suffix=".mp3") as f:
        tts.save(f.name)
        st.session_state.last_audio=f.name

    st.rerun()

# ---------- VOICE LOCAL ----------
if voice_btn:
    r=sr.Recognizer()
    with sr.Microphone() as s: audio=r.listen(s)
    try:
        scam_text=r.recognize_google(audio,language="en-IN")
        st.session_state.history.append(("Scammer",scam_text))
        if len(st.session_state.history)==1:
            st.session_state.scam_type=detect_scam(scam_text)

        reply,lang=honeypot_agent(st.session_state.scam_type,scam_text,st.session_state.persona,st.session_state.emotion)
        st.session_state.history.append(("AI",reply))

        tts=gTTS(reply,lang=LANG_MAP.get(lang,"en"))
        with tempfile.NamedTemporaryFile(delete=False,suffix=".mp3") as f:
            tts.save(f.name)
            st.session_state.last_audio=f.name

        st.rerun()
    except:
        st.warning("Voice not understood")

# ---------------- EVIDENCE PANEL ----------------
st.sidebar.markdown("### 📌 Extracted Evidence")
full_text=" ".join([m for _,m in st.session_state.history])
upi,phones,links=extract_evidence(full_text)
st.sidebar.write("UPI:",upi)
st.sidebar.write("Phones:",phones)
st.sidebar.write("Links:",links)

# ---------------- RESET ----------------
if st.sidebar.button("🧹 Reset"):
    st.session_state.history=[]
    st.session_state.scam_type="Unknown"
    st.session_state.last_audio=None
    st.rerun()
