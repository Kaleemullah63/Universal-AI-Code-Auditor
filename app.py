import streamlit as st
from groq import Groq
import json
import re
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
.stApp { background: white; color: black; }
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
code_input = st.text_area("📥 Paste Your Code", height=350)

language_options = [
    "Auto Detect", "Python", "C", "C++", "Java",
    "JavaScript", "TypeScript", "Go", "Rust",
    "PHP", "Ruby", "Assembly", "Bash", "SQL"
]

selected_language = st.selectbox("🌐 Language (Optional)", language_options)

analyze_btn = st.button("🚀 Analyze Code")

# ---------------- PROMPT ----------------
def build_prompt(code, depth, verbose, language):
    lang_instruction = ""
    if language != "Auto Detect":
        lang_instruction = f"Language is {language}. Do not detect."

    return f"""
You are a strict AI code auditor.

RULES:
- Output MUST be valid JSON only
- No explanation outside JSON
- Do NOT truncate JSON

{lang_instruction}

Return EXACTLY:

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

Analyze this code:
{code}
"""

# ---------------- API ----------------
def call_ai(prompt):
    client = Groq(api_key=api_key)
    res = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "ONLY JSON OUTPUT"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1
    )
    return res.choices[0].message.content

# ---------------- JSON FIXER ----------------
def fix_json(text):
    try:
        return json.loads(text)
    except:
        pass

    # extract JSON block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group()

    # fix common issues
    text = text.replace("\n", " ")
    text = re.sub(r",\s*}", "}", text)
    text = re.sub(r",\s*]", "]", text)

    try:
        return json.loads(text)
    except:
        return None

# ---------------- RETRY ----------------
def get_response(prompt):
    for _ in range(3):
        raw = call_ai(prompt)
        data = fix_json(raw)
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

Summary:
{data.get('summary')}

Issues:
{json.dumps(data.get('issues'), indent=2)}

Optimized Code:
{data.get('optimized_code')}
"""

# ---------------- MAIN ----------------
if analyze_btn:
    if not code_input.strip():
        st.warning("⚠️ Paste your code first")
    else:
        with st.spinner("🧠 AI analyzing..."):
            data = get_response(
                build_prompt(code_input, depth, verbose, selected_language)
            )

            if not data:
                st.error("❌ AI response failed after retries. Try smaller code chunk.")
            else:
                tabs = st.tabs(["📄 Code", "🐞 Analysis", "✅ Optimized"])

                with tabs[0]:
                    st.code(code_input)

                with tabs[1]:
                    st.subheader(f"Language: {data.get('language')}")
                    score = data.get("score", 0)

                    st.progress(score / 100)
                    st.write(f"Score: {score}%")

                    for issue in data.get("issues", []):
                        with st.expander(f"{issue.get('title')} ({issue.get('severity')})"):
                            st.write(issue.get("explanation"))
                            st.write("Root Cause:", issue.get("root_cause"))
                            st.write("Fix:", issue.get("fix_steps"))

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
