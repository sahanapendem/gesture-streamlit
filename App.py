import streamlit as st
import cv2
import mediapipe as mp
import numpy as np

st.set_page_config(page_title="SGEC Sterile Console", layout="wide")

def load_css():
    try:
        with open("assets/style.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except: pass

load_css()

# --- STATE MANAGEMENT ---
if "page" not in st.session_state:
    st.session_state.page = "home"

for key, val in {"light": "OFF", "fan": "OFF", "ac": "OFF", "brightness": 50}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# --- GESTURE LOGIC ---
def get_gesture_output(hl):
    fingers = []
    # Thumb (Horizontal)
    if hl.landmark[4].x < hl.landmark[3].x: fingers.append(1)
    else: fingers.append(0)
    # Fingers (Vertical)
    tips = [8, 12, 16, 20]
    for tip in tips:
        if hl.landmark[tip].y < hl.landmark[tip-2].y: fingers.append(1)
        else: fingers.append(0)
    
    total = sum(fingers)
    # Mapping based on Plan
    if total == 5: return "✋ OPEN PALM → Light ON"
    elif total == 0: return "✊ FIST → Light OFF"
    elif fingers == [1, 0, 0, 0, 0]: return "👍 THUMBS UP → Fan ON"
    # Thumbs Down detection
    elif fingers == [1, 0, 0, 0, 0] and hl.landmark[4].y > hl.landmark[3].y: return "👎 THUMBS DOWN → Fan OFF"
    elif fingers == [0, 1, 1, 0, 0]: return "✌️ TWO FINGERS → Brightness UP"
    elif fingers == [0, 1, 0, 0, 0]: return "☝️ ONE FINGER → Brightness DOWN"
    elif fingers == [0, 1, 1, 1, 0]: return "🤟 THREE FINGERS → AC ON"
    return "SEARCHING..."

# --- PAGE: HOME ---
if st.session_state.page == "home":
    st.markdown("""
        <div style="text-align: center; margin-top: 30px; margin-bottom: 40px;">
            <h1 class="home-title">SGEC</h1>
            <p style="color:#4ade80; font-size:18px; letter-spacing:2px;">STERILE GESTURE ENVIRONMENT CONTROL</p>
            <p style="opacity:0.6;">A Zero-Contact Infrastructure Solution for Hospital Hygiene</p>
        </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        with st.popover("✋ LIGHTING CONTROL", use_container_width=True):
            st.subheader("Hygiene: Pathogen Prevention")
            st.write("Eliminates switch-based cross-contamination in surgical theaters.")
            st.caption("Open Palm: ON | Fist: OFF")
        
        with st.popover("🤟 CLIMATE CONTROL", use_container_width=True):
            st.subheader("Hygiene: Maintaining Scrub")
            st.write("Adjust AC without breaking the sterile scrub protocol.")
            st.caption("Three Fingers: AC ON")

    with c2:
        with st.popover("👍 AIRFLOW CONTROL", use_container_width=True):
            st.subheader("Hygiene: Laminar Management")
            st.write("Manage theater fans to control air-borne particulate flow.")
            st.caption("Thumbs Up: ON | Thumbs Down: OFF")

        with st.popover("✌️ INTENSITY CONTROL", use_container_width=True):
            st.subheader("Hygiene: Sterile Exam")
            st.write("Modify examination light intensity without physical touch.")
            st.caption("2-Fingers: Increase | 1-Finger: Decrease")

    st.markdown("<br>", unsafe_allow_html=True)
    _, btn_col, _ = st.columns([1, 1.2, 1])
    with btn_col:
        if st.button("LAUNCH STERILE CONSOLE"):
            st.session_state.page = "dashboard"
            st.rerun()
    st.stop()

# --- PAGE: DASHBOARD ---
t1, t2, t3 = st.columns([7, 1, 2])
with t1:
    st.markdown("<h2 style='color:#4ade80; margin:0;'>LIVE STERILE CONSOLE</h2>", unsafe_allow_html=True)
with t2:
    with st.popover("❓", help="Gesture Guide"):
        st.markdown("### 📖 Command Guide")
        st.markdown("""
        <table class="help-table">
            <tr><th>✋</th><td>Open Palm → Light ON</td></tr>
            <tr><th>✊</th><td>Fist → Light OFF</td></tr>
            <tr><th>👍</th><td>Thumbs Up → Fan ON</td></tr>
            <tr><th>👎</th><td>Thumbs Down → Fan OFF</td></tr>
            <tr><th>✌️</th><td>2 Fingers → Brightness UP</td></tr>
            <tr><th>☝️</th><td>1 Finger → Brightness DOWN</td></tr>
            <tr><th>🤟</th><td>3 Fingers → AC ON</td></tr>
        </table>
        """, unsafe_allow_html=True)
with t3:
    if st.button("EXIT SYSTEM"):
        st.session_state.page = "home"
        st.rerun()

col1, col2 = st.columns([1, 2.5])
with col1:
    st.markdown('<div class="status-card">', unsafe_allow_html=True)
    st.markdown("### 📊 Metrics")
    ui_l, ui_f, ui_a, ui_b = st.empty(), st.empty(), st.empty(), st.empty()
    st.markdown("<br>", unsafe_allow_html=True)
    ui_g = st.empty()
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    ui_cam = st.empty()

# Camera Processing
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils
cap = cv2.VideoCapture(0)

while cap.isOpened() and st.session_state.page == "dashboard":
    ret, frame = cap.read()
    if not ret: break
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) # Correct Blue Skin
    res = hands.process(rgb_frame)
    current_out = "SEARCHING..."

    if res.multi_hand_landmarks:
        for hl in res.multi_hand_landmarks:
            mp_draw.draw_landmarks(rgb_frame, hl, mp_hands.HAND_CONNECTIONS,
                                 mp_draw.DrawingSpec(color=(74, 222, 128), thickness=2))
            current_out = get_gesture_output(hl)
            
            # Update Logic
            if "Light ON" in current_out: st.session_state.light = "ON"
            elif "Light OFF" in current_out: st.session_state.light = "OFF"
            elif "Fan ON" in current_out: st.session_state.fan = "ON"
            elif "Fan OFF" in current_out: st.session_state.fan = "OFF"
            elif "Brightness UP" in current_out: st.session_state.brightness = min(100, st.session_state.brightness + 2)
            elif "Brightness DOWN" in current_out: st.session_state.brightness = max(0, st.session_state.brightness - 2)
            elif "AC ON" in current_out: st.session_state.ac = "ON"

    # UI Refresh
    ui_l.markdown(f'<div class="status-item"><span class="status-label">💡 Light</span><span class="status-value">{st.session_state.light}</span></div>', unsafe_allow_html=True)
    ui_f.markdown(f'<div class="status-item"><span class="status-label">🌀 Fan</span><span class="status-value">{st.session_state.fan}</span></div>', unsafe_allow_html=True)
    ui_a.markdown(f'<div class="status-item"><span class="status-label">❄️ AC</span><span class="status-value">{st.session_state.ac}</span></div>', unsafe_allow_html=True)
    ui_b.markdown(f'<div style="margin-top:10px;"><p style="font-size:11px; color:#4ade80;">INTENSITY: {st.session_state.brightness}%</p><div style="background:rgba(255,255,255,0.1); height:5px; border-radius:10px;"><div style="background:#4ade80; width:{st.session_state.brightness}%; height:100%; border-radius:10px;"></div></div></div>', unsafe_allow_html=True)
    ui_g.info(f"OUTPUT: {current_out}")
    ui_cam.image(rgb_frame, channels="RGB")

cap.release()