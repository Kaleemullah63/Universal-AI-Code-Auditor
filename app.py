import streamlit as st
from groq import Groq
import json
from datetime import datetime

# ---------------------- PAGE CONFIG ----------------------
st.set_page_config(
    page_title="OmniReview AI Code Auditor",
    page_icon="🤖",
    layout="wide"
)

# ---------------------- CUSTOM DARK UI ----------------------
st.markdown("""
<style>
.main {
    background-color: #0e1117;
    color: #ffffff;
}
textarea {
    background-color: #1c1f26 !important;
    color: #ffffff !important;
    border-radius: 10px !important;
}
.stButton button {
    background: linear-gradient(90deg, #00ADB5, #007BFF);
    color: white;
    border-radius: 8px;
    font-weight: bold;
}
.stMetric {
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# ---------------------- GET API KEY FROM SECRETS ----------------------
def get_api_key():
    try:
        return st.secrets["GROQ_API_KEY"]
    except:
        return None

api_key = get_api_key()

# ---------------------- SIDEBAR ----------------------
st.sidebar.title("⚙️ Configuration")

depth = st.sidebar.select_slider(
    "Technical Depth",
    options=["Beginner", "Intermediate", "Advanced", "Expert"],
    value="Advanced"
)

verbose = st.sidebar.toggle("Verbose Mode", value=True)

# Optional fallback (only if secret not found)
if not api_key:
    st.sidebar.warning("Using manual API key (Secrets not found)")
    api_key = st.sidebar.text_input("Enter Groq API Key", type="password")

# ---------------------- MAIN UI ----------------------
st.title("🤖 OmniReview: Universal AI Code Auditor")

st.markdown("Analyze, debug, and optimize code using AI 🔥")

col1, col2 = st.columns([2, 1])

with col1:
    code_input = st.text_area("📥 Paste Your Code", height=350)

with col2:
    st.info("""
💡 Features:
- Multi-language support  
- Bug detection  
- Security audit  
- Code optimization  
- Score system  
""")

analyze_btn = st.button("🚀 Run AI Audit")

# ---------------------- PROMPT ----------------------
def build_prompt(code, depth, verbose):
    return f"""
You are a Principal AI Code Auditor.

Return ONLY valid JSON.

Technical Depth: {depth}
Verbose Mode: {verbose}

Tasks:
1. Detect language & purpose
2. Find bugs (syntax, logic, security, performance)
3. Explain each issue clearly
4. Provide fixes
5. Give score (0-100)
6. Provide optimized code

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

# ---------------------- API CALL ----------------------
def analyze_code(api_key, prompt):
    client = Groq(api_key=api_key)

    response = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return response.choices[0].message.content

# ---------------------- JSON PARSER ----------------------
def parse_json(response):
    try:
        start = response.find("{")
        end = response.rfind("}") + 1
        return json.loads(response[start:end])
    except:
        return None

# ---------------------- REPORT ----------------------
def generate_report(data):
    report = f"# OmniReview Report\n\n"
    report += f"## Language\n{data.get('language')}\n\n"
    report += f"## Purpose\n{data.get('purpose')}\n\n"
    report += f"## Score\n{data.get('score')}%\n\n"
    report += f"## Summary\n{data.get('summary')}\n\n"

    report += "## Issues\n"
    for i in data.get("issues", []):
        report += f"\n### {i.get('title')} ({i.get('severity')})\n"
        report += f"- {i.get('explanation')}\n"
        report += f"- Root Cause: {i.get('root_cause')}\n"
        report += f"- Fix: {i.get('fix_steps')}\n"

    report += "\n## Optimized Code\n```\n"
    report += data.get("optimized_code", "")
    report += "\n```"

    return report

# ---------------------- MAIN LOGIC ----------------------
if analyze_btn:
    if not api_key:
        st.error("❌ API key missing. Add it in Streamlit secrets.")
    elif not code_input.strip():
        st.warning("⚠️ Please paste your code first.")
    else:
        with st.spinner("🧠 AI is analyzing your code..."):
            try:
                prompt = build_prompt(code_input, depth, verbose)
                raw = analyze_code(api_key, prompt)
                data = parse_json(raw)

                if not data:
                    st.error("❌ Failed to parse response. Try again.")
                else:
                    tabs = st.tabs([
                        "📄 Original Code",
                        "🐞 Analysis",
                        "✅ Optimized Code"
                    ])

                    # TAB 1
                    with tabs[0]:
                        st.code(code_input)

                    # TAB 2
                    with tabs[1]:
                        st.metric("Code Quality Score", f"{data.get('score')}%")

                        for issue in data.get("issues", []):
                            with st.expander(f"{issue.get('title')} ({issue.get('severity')})"):
                                st.write(f"**Explanation:** {issue.get('explanation')}")
                                st.write(f"**Root Cause:** {issue.get('root_cause')}")
                                st.write(f"**Fix:** {issue.get('fix_steps')}")

                    # TAB 3
                    with tabs[2]:
                        st.code(data.get("optimized_code"))

                        st.download_button(
                            "⬇️ Download Code",
                            data.get("optimized_code"),
                            file_name="optimized_code.txt"
                        )

                    # REPORT
                    report = generate_report(data)

                    st.download_button(
                        "📥 Download Full Report",
                        report,
                        file_name=f"report_{datetime.now().strftime('%Y%m%d')}.md"
                    )

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
