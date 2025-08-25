import streamlit as st
import PyPDF2
import io
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

st.markdown("""
    <style>
        body {
            background-color: #f3e5f5;
        }
        .stApp {
            background-color: #f3e5f5;
        }
    </style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="AI Resume Reviewer", page_icon="📜", layout="centered")

st.title("📜 CareerLens – AI Resume Reviewer")
st.markdown("Upload your resume in PDF format and get AI-powered instant feedback tailored to your career goals!")


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
uploaded_file = st.file_uploader("Choose your Resume (PDF or Text)", type=["pdf", "txt"])
job_role = st.text_input("Enter the job role you are targeting (optional)")
analyze = st.button("Analyze Resume")

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

if analyze and uploaded_file:
    try:
        file_content = extract_text_from_file(uploaded_file)
        if not file_content.strip():
            st.error("The uploaded file is empty or could not be read. Please upload a valid PDF or text file.")
            st.stop()

        prompt = f"""Please analyze this resume and provide constructive feedback.
Focus on the following aspects:
1. Content clarity and impact
2. Skills presentation
3. Experience descriptions
4. Specific improvements for {job_role if job_role else 'general job roles'}

Resume content:
{file_content}

Please provide your analysis in a clear, structured format with specific recommendations."""

        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.5-flash")


        response = model.generate_content(prompt)

        st.markdown("### Analysis Results")
        st.markdown(response.text)

    except Exception as e:
        st.error(f"An error occurred: {e}")
