import streamlit as st
from groq import Groq
import json
from datetime import datetime

# ---------------------- PAGE CONFIG ----------------------
st.set_page_config(
    page_title="OmniReview: AI Code Auditor",
    page_icon="🤖",
    layout="wide"
)

# ---------------------- DARK MODE CSS ----------------------
st.markdown("""
<style>
body {
    background-color: #0e1117;
    color: #ffffff;
}
textarea, .stTextInput input {
    background-color: #1e1e1e !important;
    color: white !important;
}
.stButton button {
    background-color: #00ADB5;
    color: white;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# ---------------------- SIDEBAR ----------------------
st.sidebar.title("⚙️ Settings")

api_key = st.sidebar.text_input("Groq API Key", type="password")

depth = st.sidebar.select_slider(
    "Technical Depth",
    options=["Beginner", "Intermediate", "Advanced", "Expert"],
    value="Advanced"
)

verbose = st.sidebar.toggle("Verbose Mode", value=True)

# ---------------------- MAIN UI ----------------------
st.title("🤖 OmniReview: Universal AI Code Auditor")

code_input = st.text_area("📥 Paste Your Code Here", height=300)

analyze_btn = st.button("🚀 Analyze Code")


# ---------------------- PROMPT BUILDER ----------------------
def build_prompt(code: str, depth: str, verbose: bool) -> str:
    return f"""
You are a Principal AI Code Auditor.

STRICTLY return ONLY valid JSON.

Technical Depth: {depth}
Verbose Mode: {verbose}

Perform:
1. Detect language & purpose
2. Identify bugs (syntax, logic, security, performance)
3. Explain each issue clearly
4. Provide step-by-step fixes
5. Give code quality score (0-100)
6. Provide fully optimized final code

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


# ---------------------- API HANDLER ----------------------
def analyze_code(api_key: str, prompt: str) -> str:
    client = Groq(api_key=api_key)

    response = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )

    return response.choices[0].message.content


# ---------------------- SAFE JSON PARSER ----------------------
def parse_response(response: str):
    try:
        start = response.find("{")
        end = response.rfind("}") + 1
        clean_json = response[start:end]
        return json.loads(clean_json)
    except Exception:
        return None


# ---------------------- REPORT GENERATOR ----------------------
def generate_report(data: dict) -> str:
    report = f"# OmniReview Report\n\n"
    report += f"## Language\n{data.get('language')}\n\n"
    report += f"## Purpose\n{data.get('purpose')}\n\n"
    report += f"## Code Quality Score\n{data.get('score')}%\n\n"
    report += f"## Summary\n{data.get('summary')}\n\n"
    report += f"## Issues\n"

    for issue in data.get("issues", []):
        report += f"\n### {issue.get('title')} ({issue.get('severity')})\n"
        report += f"- Explanation: {issue.get('explanation')}\n"
        report += f"- Root Cause: {issue.get('root_cause')}\n"
        report += f"- Fix: {issue.get('fix_steps')}\n"

    report += "\n## Optimized Code\n```\n"
    report += data.get("optimized_code", "")
    report += "\n```\n"

    return report


# ---------------------- MAIN LOGIC ----------------------
if analyze_btn:
    if not api_key:
        st.error("⚠️ Please enter your Groq API key.")
    elif not code_input.strip():
        st.error("⚠️ Please paste your code.")
    else:
        with st.spinner("🔍 AI is analyzing your code..."):
            try:
                prompt = build_prompt(code_input, depth, verbose)
                raw_response = analyze_code(api_key, prompt)
                data = parse_response(raw_response)

                if not data:
                    st.error("❌ Failed to parse AI response. Try again.")
                else:
                    tab1, tab2, tab3 = st.tabs([
                        "📄 Original Code",
                        "🐞 Bug Analysis",
                        "✅ Final Code"
                    ])

                    # -------- TAB 1 --------
                    with tab1:
                        st.code(code_input)

                    # -------- TAB 2 --------
                    with tab2:
                        st.subheader("🔍 Bug Analysis")

                        st.metric("Code Quality Score", f"{data.get('score')}%")

                        for issue in data.get("issues", []):
                            with st.expander(f"{issue.get('title')} ({issue.get('severity')})"):
                                st.write(f"**Explanation:** {issue.get('explanation')}")
                                st.write(f"**Root Cause:** {issue.get('root_cause')}")
                                st.write(f"**Fix Steps:** {issue.get('fix_steps')}")

                    # -------- TAB 3 --------
                    with tab3:
                        st.subheader("✅ Optimized Code")
                        st.code(data.get("optimized_code"))

                        st.download_button(
                            "⬇️ Download Optimized Code",
                            data.get("optimized_code"),
                            file_name="optimized_code.txt"
                        )

                    # -------- REPORT DOWNLOAD --------
                    report = generate_report(data)

                    st.download_button(
                        "📥 Download Full Report (.md)",
                        report,
                        file_name=f"omnireview_{datetime.now().strftime('%Y%m%d')}.md"
                    )

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
