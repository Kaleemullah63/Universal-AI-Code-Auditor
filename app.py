import streamlit as st
from groq import Groq
import json
from datetime import datetime

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="OmniReview AI Code Auditor",
    layout="wide",
    page_icon="🤖"
)

MODEL_NAME = "llama-3.3-70b-versatile"

# ---------------- UI ----------------
st.markdown("""
<style>
.stApp {
    background: white;
    color: black;
}

textarea {
    background-color: #f5f5f5 !important;
    color: black !important;
    border-radius: 10px !important;
}

.stButton button {
    background-color: black !important;
    color: white !important;
    border-radius: 8px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# ---------------- API KEY ----------------
try:
    api_key = st.secrets["GROQ_API_KEY"]
except:
    st.error("❌ Add GROQ_API_KEY in Streamlit secrets")
    st.stop()

# ---------------- SIDEBAR ----------------
st.sidebar.title("⚙️ Settings")

depth = st.sidebar.select_slider(
    "Technical Depth",
    ["Beginner", "Intermediate", "Advanced", "Expert"],
    value="Advanced"
)

verbose = st.sidebar.toggle("Verbose Mode", True)

# ---------------- MAIN ----------------
st.title("🤖 OmniReview AI Code Auditor")
st.write("Analyze, Debug, Optimize your code with AI")

code_input = st.text_area("📥 Paste Your Code", height=350)

# 🔥 Language Selection (NEW FEATURE)
language_options = [
    "Auto Detect",
    "Python", "C", "C++", "Java", "JavaScript",
    "TypeScript", "Go", "Rust", "PHP", "Ruby",
    "Assembly", "Bash", "SQL"
]

selected_language = st.selectbox("🌐 Select Language (Optional)", language_options)

analyze_btn = st.button("🚀 Analyze Code")

# ---------------- PROMPT ----------------
def build_prompt(code, depth, verbose, language):
    lang_instruction = ""
    if language != "Auto Detect":
        lang_instruction = f"The code language is: {language}. Do NOT auto-detect."

    return f"""
You are a strict AI code auditor.

IMPORTANT:
- Return ONLY valid JSON
- No text outside JSON

{lang_instruction}

Technical Depth: {depth}
Verbose: {verbose}

Tasks:
- Detect language (if not provided)
- Detect purpose
- Find bugs (syntax, logic, security, performance)
- Explain each issue
- Provide fixes
- Score (0-100)
- Provide optimized code

JSON FORMAT:

{{
  "language": "",
  "purpose": "",
  "issues": [
    {{
      "title": "",
      "severity": "",
      "explanation": "",
      "root_cause": "",
      "fix_steps": ""
    }}
  ],
  "score": 0,
  "summary": "",
  "optimized_code": ""
}}

CODE:
{code}
"""

# ---------------- API ----------------
def call_ai(prompt):
    client = Groq(api_key=api_key)

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "Return ONLY JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )

    return response.choices[0].message.content

# ---------------- PARSER ----------------
def extract_json(text):
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        return json.loads(text[start:end])
    except:
        return None

# ---------------- RETRY ----------------
def get_valid_response(prompt):
    for _ in range(2):
        raw = call_ai(prompt)
        data = extract_json(raw)
        if data:
            return data
    return None

# ---------------- REPORT ----------------
def generate_report(data):
    return f"""
# OmniReview Report

Language: {data.get('language')}
Purpose: {data.get('purpose')}
Score: {data.get('score')}%

## Summary
{data.get('summary')}

## Issues
{json.dumps(data.get('issues'), indent=2)}

## Optimized Code
{data.get('optimized_code')}
"""

# ---------------- MAIN LOGIC ----------------
if analyze_btn:
    if not code_input.strip():
        st.warning("⚠️ Please paste your code.")
    else:
        with st.spinner("🧠 Analyzing..."):
            data = get_valid_response(
                build_prompt(code_input, depth, verbose, selected_language)
            )

            if not data:
                st.error("❌ Failed to parse AI response.")
            else:
                tabs = st.tabs(["📄 Code", "🐞 Analysis", "✅ Optimized"])

                # TAB 1
                with tabs[0]:
                    st.code(code_input)

                # TAB 2
                with tabs[1]:
                    st.subheader(f"🌐 Detected Language: {data.get('language')}")

                    score = data.get("score", 0)
                    st.progress(score / 100)
                    st.write(f"Score: {score}%")

                    for issue in data.get("issues", []):
                        with st.expander(f"{issue.get('title')} ({issue.get('severity')})"):
                            st.write(issue.get("explanation"))
                            st.write("Root Cause:", issue.get("root_cause"))
                            st.write("Fix:", issue.get("fix_steps"))

                # TAB 3
                with tabs[2]:
                    st.code(data.get("optimized_code"))

                    st.download_button(
                        "⬇️ Download Code",
                        data.get("optimized_code"),
                        file_name="optimized_code.txt"
                    )

                report = generate_report(data)

                st.download_button(
                    "📥 Download Report",
                    report,
                    file_name=f"report_{datetime.now().strftime('%Y%m%d')}.md"
                )
