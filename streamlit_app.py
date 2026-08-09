import os
import uuid
import requests
import streamlit as st

# Configure Streamlit page
st.set_page_config(
    page_title="AI Technical Interviewer - Hackathon Edition",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Configurable backend URL
def get_backend_url() -> str:
    url = os.getenv("BACKEND_URL")
    if not url:
        try:
            url = st.secrets.get("BACKEND_URL")
        except Exception:
            pass
    return (url or "https://03de0931c38a0a.lhr.life").rstrip("/")


BACKEND_URL = get_backend_url()

# Custom CSS for hackathon theme
st.markdown("""
<style>
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
    }
    .main-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 1.5rem;
        background: rgba(30, 41, 59, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        margin-bottom: 1.5rem;
        backdrop-filter: blur(10px);
    }
    .badge-hackathon {
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: #fff;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    .candidate-card-header {
        font-size: 1.2rem;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 0.2rem;
    }
    .detail-pill {
        background: #334155;
        color: #cbd5e1;
        padding: 3px 8px;
        border-radius: 8px;
        font-size: 0.8rem;
        margin-right: 6px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "candidate" not in st.session_state:
    st.session_state.candidate = None
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "feedback" not in st.session_state:
    st.session_state.feedback = None
if "interview_started" not in st.session_state:
    st.session_state.interview_started = False

def reset_interview():
    st.session_state.candidate = None
    st.session_state.session_id = None
    st.session_state.messages = []
    st.session_state.feedback = None
    st.session_state.interview_started = False

# Header Navigation
col_header_1, col_header_2 = st.columns([3, 1])

with col_header_1:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1rem;">
        <span style="font-size: 2.2rem;">💬</span>
        <div>
            <h1 style="margin: 0; padding: 0; font-size: 1.8rem; font-weight: 700; color: #ffffff;">AI Technical Interviewer</h1>
            <span class="badge-hackathon">Hackathon Edition</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_header_2:
    if st.session_state.candidate:
        if st.button("← Back to Candidates", use_container_width=True):
            reset_interview()
            st.rerun()

# -----------------------------------------------------------------------------
# VIEW 1: CANDIDATE SELECTION
# -----------------------------------------------------------------------------
if st.session_state.candidate is None:
    st.subheader("Select Candidate for Technical Assessment")
    st.caption("Choose a candidate profile to initiate an AI-conducted technical interview")
    
    candidates = []
    try:
        res = requests.get(f"{BACKEND_URL}/api/candidates", timeout=10)
        if res.status_code == 200:
            candidates = res.json().get("candidates", [])
        else:
            st.error(f"Failed to load candidates ({res.status_code}). Ensure backend server is running at `{BACKEND_URL}`.")
    except Exception as e:
        st.error(f"Could not connect to backend at `{BACKEND_URL}`. Please ensure FastAPI server is running.")
        st.info("Tip: You can configure the `BACKEND_URL` environment variable if your backend is hosted on a custom port/domain.")

    if candidates:
        search_term = st.text_input("🔍 Search candidate or role...", placeholder="e.g. Data Engineer, Sarah, MS Computer Science")
        
        filtered = []
        for c in candidates:
            member = c.get("member", {})
            name = member.get("name", "").lower()
            role = member.get("jobRole", "").lower()
            edu = member.get("education", "").lower()
            term = search_term.lower().strip()
            if not term or term in name or term in role or term in edu:
                filtered.append(c)
                
        if not filtered:
            st.info(f"No candidates found matching '{search_term}'")
        else:
            cols = st.columns(2)
            for idx, cand in enumerate(filtered):
                member = cand.get("member", {})
                name = member.get("name", "Unknown Candidate")
                role = member.get("jobRole", "Technical Candidate")
                yoe = member.get("yearsExperience", 0)
                edu = member.get("education", "")
                status = member.get("status", "Available")
                
                with cols[idx % 2]:
                    with st.container(border=True):
                        st.markdown(f"<div class='candidate-card-header'>{name}</div>", unsafe_allow_html=True)
                        st.markdown(f"**{role}** • `{status}`")
                        st.markdown(f"⏱️ `{yoe} YOE` &nbsp; 🎓 `{edu}`")
                        st.write("")
                        if st.button("Start Technical Interview ➔", key=f"select_{member.get('id', idx)}", use_container_width=True, type="primary"):
                            st.session_state.candidate = cand
                            st.session_state.session_id = str(uuid.uuid4())
                            st.session_state.messages = []
                            st.session_state.feedback = None
                            st.session_state.interview_started = False
                            st.rerun()

# -----------------------------------------------------------------------------
# VIEW 2 & 3: INTERVIEW CHAT & FEEDBACK REPORT
# -----------------------------------------------------------------------------
else:
    # Auto-start interview session if not initialized
    if not st.session_state.interview_started:
        with st.spinner("Initializing technical interview session..."):
            try:
                resp = requests.post(
                    f"{BACKEND_URL}/api/interview",
                    json={
                        "sessionId": st.session_state.session_id,
                        "candidate": st.session_state.candidate
                    },
                    timeout=45
                )
                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state.messages.append({"role": "interviewer", "text": data.get("reply", "")})
                    st.session_state.interview_started = True
                    if data.get("done"):
                        st.session_state.feedback = data.get("feedback")
                    st.rerun()
                else:
                    st.error(f"Error initializing interview ({resp.status_code}): {resp.text}")
            except Exception as e:
                st.error(f"Failed to connect to backend: {e}")

    # Render candidate profile banner
    member = st.session_state.candidate.get("member", {})
    cand_name = member.get("name", "Candidate")
    cand_role = member.get("jobRole", "Technical Candidate")
    cand_yoe = member.get("yearsExperience", 0)
    short_session = st.session_state.session_id[:8] if st.session_state.session_id else "Active"

    st.markdown(f"""
    <div style="background: #1e293b; padding: 12px 18px; border-radius: 10px; border: 1px solid #334155; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
        <div>
            <strong style="font-size: 1.1rem; color: #f8fafc;">👤 {cand_name}</strong> &nbsp;
            <span style="color: #94a3b8;">({cand_role} • {cand_yoe} YOE)</span>
        </div>
        <div style="font-size: 0.85rem; color: #38bdf8; font-family: monospace;">
            🟢 SESSION: {short_session}...
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Render chat messages
    for msg in st.session_state.messages:
        if msg["role"] == "interviewer":
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(f"**AI Interviewer**\n\n{msg['text']}")
        elif msg["role"] == "candidate":
            with st.chat_message("user", avatar="👤"):
                st.markdown(f"**{cand_name}**\n\n{msg['text']}")
        elif msg["role"] == "system":
            st.info(msg["text"])

    # Render Feedback Panel if interview is completed
    if st.session_state.feedback:
        st.divider()
        st.markdown("## 📊 Technical Assessment Report")
        st.caption("AI-conducted evaluation summary and candidate scorecard")
        
        fb = st.session_state.feedback
        
        st.info(f"**Executive Summary:**\n\n{fb.get('summary', 'No summary provided.')}")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### ✅ Demonstrated Strengths")
            strengths = fb.get("strengths", [])
            if strengths:
                for item in strengths:
                    st.markdown(f"- {item}")
            else:
                st.markdown("- No key strengths noted.")
                
        with col2:
            st.markdown("### ⚠️ Knowledge Gaps")
            gaps = fb.get("gaps", [])
            if gaps:
                for item in gaps:
                    st.markdown(f"- {item}")
            else:
                st.markdown("- No significant gaps identified.")
                
        with col3:
            st.markdown("### 🚀 Next Steps")
            next_steps = fb.get("next", [])
            if next_steps:
                for item in next_steps:
                    st.markdown(f"- {item}")
            else:
                st.markdown("- No specific next steps recommended.")
                
        st.write("")
        if st.button("🔄 Assess Another Candidate", type="primary", use_container_width=True):
            reset_interview()
            st.rerun()

    # Render Chat Input if interview is ongoing
    else:
        user_input = st.chat_input("Type technical response...")
        if user_input:
            st.session_state.messages.append({"role": "candidate", "text": user_input})
            with st.chat_message("user", avatar="👤"):
                st.markdown(f"**{cand_name}**\n\n{user_input}")
                
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("Evaluating response..."):
                    try:
                        resp = requests.post(
                            f"{BACKEND_URL}/api/interview",
                            json={
                                "sessionId": st.session_state.session_id,
                                "message": user_input
                            },
                            timeout=60
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            reply_text = data.get("reply", "")
                            st.session_state.messages.append({"role": "interviewer", "text": reply_text})
                            st.markdown(f"**AI Interviewer**\n\n{reply_text}")
                            if data.get("done"):
                                st.session_state.feedback = data.get("feedback")
                                st.rerun()
                        else:
                            st.error(f"Error from server ({resp.status_code}): {resp.text}")
                    except Exception as e:
                        st.error(f"Error transmitting response to AI interviewer: {e}")
