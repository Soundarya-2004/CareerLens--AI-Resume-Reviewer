import streamlit as st
import PyPDF2
import io
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ✅ Uniform model initialization
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-2.5-flash")

USER_CREDENTIALS = {
    "soundarya": "visionary123",
    "admin": "adminpass"
}

# Chat history file
CHAT_HISTORY_FILE = "chat_history.json"

# Styling
st.markdown("""
    <style>
        body, .stApp {
            background-color: #f3e5f5;
            font-family: 'Segoe UI', sans-serif;
            color: #4a148c;
        }
        .css-1cpxqw2, .css-1d391kg {
            background-color: #ffffff;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 12px rgba(74, 20, 140, 0.1);
        }
        .stButton>button {
            background-color: #6a1b9a;
            color: white;
            border-radius: 8px;
            padding: 0.5em 1.5em;
            font-weight: bold;
        }
        .stTextInput>div>input, .stTextArea textarea {
            border: 2px solid #ba68c8;
            border-radius: 8px;
        }
        .thinking {
            font-size: 1.2em;
            font-style: italic;
            color: #6a1b9a;
            margin-top: 1em;
        }
    </style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="AI Resume Reviewer", page_icon="📜", layout="centered")

# Login system
def login_form():
    st.title(" Login to CareerLens")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_btn = st.button("Login")

    if login_btn:
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.success(f"Welcome, {username}!")
            st.rerun()
        else:
            st.error("Invalid credentials. Please try again.")

def logout_button():
    if st.button("Sign Out"):
        st.session_state["logged_in"] = False
        st.session_state["username"] = ""
        st.rerun()

# Chat history saver
def save_chat(user_email, user_query, ai_response):
    chat_entry = {
        "user": user_email,
        "timestamp": datetime.now().isoformat(),
        "user_query": user_query,
        "ai_response": ai_response
    }

    if os.path.exists(CHAT_HISTORY_FILE):
        with open(CHAT_HISTORY_FILE, "r") as f:
            history = json.load(f)
    else:
        history = []

    history.append(chat_entry)

    with open(CHAT_HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

# Resume text extraction
def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

def extract_text_from_file(uploaded_file):
    if uploaded_file.type == "application/pdf":
        return extract_text_from_pdf(io.BytesIO(uploaded_file.read()))
    return uploaded_file.read().decode("utf-8")

# Session state initialization
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# Login check
if not st.session_state["logged_in"]:
    login_form()
    st.stop()
else:
    st.sidebar.write(f" Logged in as: {st.session_state['username']}")
    logout_button()

    # Main app
    st.title("📜 CareerLens – AI Resume Reviewer")
    st.markdown("Upload your resume in PDF format and get AI-powered instant feedback tailored to your career goals!")

    uploaded_file = st.file_uploader("Choose your Resume (PDF or Text)", type=["pdf", "txt"])
    job_role = st.text_input("Enter the job role you are targeting (optional)")
    analyze = st.button("Analyze Resume")

    file_content = ""
    response = None

    if analyze and uploaded_file:
        with st.spinner(" Thinking..."):
            try:
                file_content = extract_text_from_file(uploaded_file)
                if not file_content.strip():
                    st.error("The uploaded file is empty or could not be read. Please upload a valid PDF or text file.")
                    st.stop()

                trimmed_resume = file_content[:5000]  # Speed optimization
                st.session_state["resume_text"] = trimmed_resume  # Store for follow-up
                prompt = f"""Please analyze this resume and provide constructive feedback.
Focus on the following aspects:
1. Content clarity and impact
2. Skills presentation
3. Experience descriptions
4. Specific improvements for {job_role if job_role else 'general job roles'}

Resume content:
{trimmed_resume}

Please provide your analysis in a clear, structured format with specific recommendations."""

                response = gemini_model.generate_content(prompt)
                st.session_state["analysis_response"] = response.text  # Store for follow-up

                st.markdown("###  Analysis Results")
                st.markdown(response.text)

            except Exception as e:
                st.error(f"An error occurred: {e}")

  
   # Follow-up chat interface
resume_text = st.session_state.get("resume_text", "")
analysis_response = st.session_state.get("analysis_response", "")

if resume_text and analysis_response:
    st.markdown("### 🤔 Ask Questions About Your Resume")
    
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    # Display previous Q&A
    for entry in st.session_state["chat_history"]:
        st.markdown(f"**You:** {entry['question']}")
        st.markdown(f"**AI:** {entry['answer']}")

    user_question = st.text_area("Type your question here", key="followup_input")
    ask_btn = st.button("Ask another question")

    if ask_btn and user_question:
        with st.spinner("Thinking..."):
            try:
                followup_prompt = f"""You previously analyzed this resume:\n\n{resume_text}\n\nYour analysis was:\n{analysis_response}\n\nNow the user has a follow-up question:\n{user_question}\n\nPlease answer clearly and helpfully, referencing the resume and your analysis."""
                followup_response = gemini_model.generate_content(followup_prompt)

                # Save and display
                st.session_state["chat_history"].append({
                    "question": user_question,
                    "answer": followup_response.text
                })

                save_chat(
                    user_email=st.session_state["username"],
                    user_query=user_question,
                    ai_response=followup_response.text
                )

                st.rerun()  # 🔁 Refresh to show updated chat

            except Exception as e:
                st.error(f"An error occurred while answering your question: {e}")
