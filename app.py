import streamlit as st
from groq import Groq
import json
from datetime import datetime

# ---------------------- CONFIG ----------------------
st.set_page_config(
    page_title="OmniReview AI Code Auditor",
    layout="wide",
    page_icon="🤖"
)

# ---------------------- MODERN UI CSS ----------------------
st.markdown("""
<style>

/* Background */
.stApp {
    background: linear-gradient(135deg, #0f172a, #020617);
    color: white;
}

/* Title */
.title {
    font-size: 42px;
    font-weight: bold;
    background: linear-gradient(90deg, #00ADB5, #3B82F6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* Card */
.card {
    background: rgba(255,255,255,0.05);
    padding: 20px;
    border-radius: 15px;
    backdrop-filter: blur(10px);
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}

/* Text Area */
textarea {
    background-color: #020617 !important;
    color: #fff !important;
    border-radius: 10px !important;
}

/* Button */
.stButton button {
    width: 100%;
    background: linear-gradient(90deg, #00ADB5, #3B82F6);
    color: white;
    border-radius: 10px;
    font-size: 16px;
    font-weight: bold;
}

/* Metric */
.metric-box {
    text-align: center;
    padding: 10px;
    background: rgba(255,255,255,0.05);
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)

# ---------------------- API KEY (ONLY SECRETS) ----------------------
try:
    api_key = st.secrets["GROQ_API_KEY"]
except:
    st.error("❌ API key not found. Please add it in Streamlit secrets.")
    st.stop()

# ---------------------- SIDEBAR ----------------------
st.sidebar.markdown("## ⚙️ Configuration")

depth = st.sidebar.select_slider(
    "Technical Depth",
    options=["Beginner", "Intermediate", "Advanced", "Expert"],
    value="Advanced"
)

verbose = st.sidebar.toggle("Verbose Mode", True)

# ---------------------- HEADER ----------------------
st.markdown('<div class="title">🤖 OmniReview AI Code Auditor</div>', unsafe_allow_html=True)
st.markdown("### Analyze • Debug • Optimize your code using AI")

# ---------------------- MAIN LAYOUT ----------------------
col1, col2 = st.columns([3, 1])

with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    code_input = st.text_area("📥 Paste Your Code", height=350)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 🚀 Features")
    st.markdown("""
- Multi-language support  
- Bug detection  
- Security analysis  
- Code optimization  
- AI scoring system  
    """)
    st.markdown('</div>', unsafe_allow_html=True)

analyze_btn = st.button("🚀 Run AI Audit")

# ---------------------- PROMPT ----------------------
def build_prompt(code, depth, verbose):
    return f"""
Return ONLY JSON.

Technical Depth: {depth}
Verbose Mode: {verbose}

Tasks:
- Detect language & purpose
- Find bugs
- Explain issues
- Give fixes
- Score (0-100)
- Provide optimized code

JSON:
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

# ---------------------- API ----------------------
def analyze_code(api_key, prompt):
    client = Groq(api_key=api_key)

    res = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return res.choices[0].message.content

# ---------------------- PARSER ----------------------
def parse_json(text):
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        return json.loads(text[start:end])
    except:
        return None

# ---------------------- REPORT ----------------------
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

# ---------------------- MAIN ----------------------
if analyze_btn:
    if not code_input.strip():
        st.warning("⚠️ Please enter code.")
    else:
        with st.spinner("🧠 AI is analyzing your code..."):
            try:
                raw = analyze_code(api_key, build_prompt(code_input, depth, verbose))
                data = parse_json(raw)

                if not data:
                    st.error("❌ Failed to parse response.")
                else:
                    st.markdown("---")

                    tabs = st.tabs(["📄 Code", "🐞 Analysis", "✅ Optimized"])

                    # TAB 1
                    with tabs[0]:
                        st.code(code_input)

                    # TAB 2
                    with tabs[1]:
                        score = data.get("score", 0)

                        st.markdown("### 📊 Code Quality Score")
                        st.progress(score / 100)
                        st.write(f"**{score}% Quality**")

                        for issue in data.get("issues", []):
                            with st.expander(f"{issue.get('title')} ({issue.get('severity')})"):
                                st.write(issue.get("explanation"))
                                st.write("**Root Cause:**", issue.get("root_cause"))
                                st.write("**Fix:**", issue.get("fix_steps"))

                    # TAB 3
                    with tabs[2]:
                        st.code(data.get("optimized_code"))

                        st.download_button(
                            "⬇️ Download Code",
                            data.get("optimized_code"),
                            file_name="optimized_code.txt"
                        )

                    # DOWNLOAD REPORT
                    report = generate_report(data)

                    st.download_button(
                        "📥 Download Report",
                        report,
                        file_name=f"report_{datetime.now().strftime('%Y%m%d')}.md"
                    )

            except Exception as e:
                st.error(str(e))
