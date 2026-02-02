import streamlit as st
import re
import speech_recognition as sr
from gtts import gTTS
import tempfile
from groq import Groq

# ---------------- CONFIG ----------------
# API key will be taken from Streamlit secrets
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

st.set_page_config(page_title="Agentic Scam Trap AI", page_icon="🛡", layout="wide")
st.title("🛡 Agentic Scam Trap AI")
st.write("Text + Voice based Scam Conversation Simulator (Hindi + English)")

# ---------------- SESSION ----------------
if "history" not in st.session_state:
    st.session_state.history = []

if "scam_type" not in st.session_state:
    st.session_state.scam_type = "Unknown"

if "last_audio" not in st.session_state:
    st.session_state.last_audio = None

# ---------------- SCAM DETECTOR ----------------
def detect_scam(text):
    t = text.lower()
    if any(k in t for k in ["police", "custody", "arrest", "thana"]):
        return "Fake Police Scam"
    elif any(k in t for k in ["lottery", "won", "kbc", "prize", "jeeta"]):
        return "Lottery Scam"
    elif any(k in t for k in ["loan", "credit", "emi"]):
        return "Loan Scam"
    elif any(k in t for k in ["bank", "account", "blocked", "kyc", "ekyc"]):
        return "Bank / KYC Scam"
    else:
        return "Unknown Scam"

# ---------------- AI REPLY ----------------
def generate_reply(scam_type, msg):
    prompt = f"""
Tum ek normal Indian insaan ho jo scammer se baat kar raha hai (WhatsApp ya call par).

Scam type: {scam_type}
Scammer ka last message: {msg}

Rules:
- Sirf apna reply likho (ek hi message)
- Apne aap ko AI mat batao
- Hinglish (Hindi + English mix) mein reply karo
- Natural sawaal poocho
- In cheezon ki koshish karo:
  • Phone number
  • UPI / payment method
  • Bank ya company ka naam
  • KYC ya payment ka reason

ONLY OUTPUT YOUR REPLY MESSAGE.
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    return response.choices[0].message.content.strip()

# ---------------- VOICE INPUT ----------------
def listen_voice():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎙️ Sun raha hoon... scammer ka message bolo")
        audio = r.listen(source)

    try:
        return r.recognize_google(audio, language="en-IN")
    except:
        return None

# ---------------- EXTRACT ----------------
def extract_evidence(text):
    upi = re.findall(r'\b[\w.-]+@[\w.-]+\b', text)
    phones = re.findall(r'\b\d{10}\b', text)
    links = re.findall(r'https?://\S+', text)
    return upi, phones, links

# ---------------- CHAT DISPLAY ----------------
st.markdown("### 💬 Conversation")
for role, msg in st.session_state.history:
    if role == "Scammer":
        st.chat_message("user").write(msg)
    else:
        st.chat_message("assistant").write(msg)

# 🔊 Play last audio reply (no autoplay param for compatibility)
if st.session_state.last_audio:
    st.audio(st.session_state.last_audio)

# ---------------- INPUT ----------------
col1, col2 = st.columns(2)

with col1:
    text_input = st.chat_input("Type scammer message (text mode)")

with col2:
    voice_btn = st.button("🎤 Speak Scammer Line")

# ---------- TEXT INPUT ----------
if text_input:
    st.session_state.history.append(("Scammer", text_input))

    if len(st.session_state.history) == 1:
        st.session_state.scam_type = detect_scam(text_input)

    reply = generate_reply(st.session_state.scam_type, text_input)
    st.session_state.history.append(("AI", reply))

    tts = gTTS(reply, lang="hi")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tts.save(fp.name)
        st.session_state.last_audio = fp.name

    st.rerun()

# ---------- VOICE INPUT ----------
if voice_btn:
    scammer_text = listen_voice()
    if scammer_text:
        st.session_state.history.append(("Scammer", scammer_text))

        if len(st.session_state.history) == 1:
            st.session_state.scam_type = detect_scam(scammer_text)

        reply = generate_reply(st.session_state.scam_type, scammer_text)
        st.session_state.history.append(("AI", reply))

        tts = gTTS(reply, lang="hi")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            st.session_state.last_audio = fp.name

        st.rerun()
    else:
        st.warning("❌ Awaaz samajh nahi aayi, dobara boliye.")

# ---------------- SIDEBAR ----------------
st.sidebar.title("🕵️ Scam Analysis")
st.sidebar.success(st.session_state.scam_type)

full_text = " ".join([m for _, m in st.session_state.history])
upi, phones, links = extract_evidence(full_text)

st.sidebar.markdown("### 📌 Evidence")
st.sidebar.write("UPI:", upi)
st.sidebar.write("Phones:", phones)
st.sidebar.write("Links:", links)

if st.sidebar.button("🧹 Clear Conversation"):
    st.session_state.history = []
    st.session_state.scam_type = "Unknown"
    st.session_state.last_audio = None
    st.rerun()
