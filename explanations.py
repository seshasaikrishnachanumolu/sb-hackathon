# explanations.py
import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

# ----------------------------
# Load keys & model
# ----------------------------
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash")  # must exist in ListModels

if not API_KEY:
    raise ValueError("❌ GEMINI_API_KEY missing in .env")

print(f"🔥 USING GEMINI MODEL = {MODEL}")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel(MODEL)
print("✅ Gemini is ready. Model in use:", MODEL)

# ----------------------------
# Plain Text Prompt
# ----------------------------
PLAIN_PROMPT = """
You are a senior financial analyst.

You will receive computed financial ratios as JSON. For EACH ratio, produce ONLY plain text (no markdown, no bold, no JSON):

FORMAT PER RATIO:
📌 <Ratio Name>
• What it measures: <1 sentence>
• Why it matters: <1 sentence>
• Healthy range: <brief range>
• Your value: <value> → <1-line interpretation>
• If weak: <1–2 corrective actions>
---

After all ratios, produce a short plain bullet summary:

📝 Summary
• <point 1>
• <point 2>
• <point 3>
...

STRICT MARKERS (do NOT remove them):
<<EXPLANATIONS_START>>
[ratio blocks here, plain text only]
<<EXPLANATIONS_END>>
<<SUMMARY_START>>
[summary bullets here]
<<SUMMARY_END>>

Now the ratios (JSON):
{ratios}
"""

def _split_text_with_markers(text: str):
    """Extract explanation and summary using markers."""
    def _between(s, start, end):
        i = s.find(start)
        if i == -1: return ""
        i += len(start)
        j = s.find(end, i)
        if j == -1: return s[i:].strip()
        return s[i:j].strip()

    exp = _between(text, "<<EXPLANATIONS_START>>", "<<EXPLANATIONS_END>>")
    summ = _between(text, "<<SUMMARY_START>>", "<<SUMMARY_END>>")
    return exp.strip(), summ.strip()

def generate_explanations(ratios: dict, context: str = "") -> dict:
    """
    Returns plain text strings:
      {
        "ratio_text": "<📌 titles + • bullets + --- separators>",
        "summary_text": "<📝 Summary + • bullets>"
      }
    """
    prompt = PLAIN_PROMPT.format(ratios=json.dumps(ratios, indent=2))
    try:
        resp = model.generate_content(prompt)
        raw = (resp.text or "").strip()
    except Exception as e:
        return {
            "ratio_text": f"📌 General\n• Gemini failed: {e}\n---",
            "summary_text": "📝 Summary\n• AI explanation unavailable."
        }

    exp_text, sum_text = _split_text_with_markers(raw)

    if not exp_text:
        exp_text = f"📌 General\n• {raw}\n---"
    if not sum_text:
        sum_text = "📝 Summary\n• No summary returned."

    # Hard cleanup: remove stray asterisks if any
    exp_text = exp_text.replace("**", "")
    sum_text = sum_text.replace("**", "")

    return {"ratio_text": exp_text, "summary_text": sum_text}

def answer_chat_question(question: str, context: str = "") -> str:
    q_prompt = (
        "You are a financial expert. Answer in clear plain text.\n"
        "Use short bullet points if helpful.\n\n"
        f"Question:\n{question}"
    )
    try:
        resp = model.generate_content(q_prompt)
        return (resp.text or "").strip()
    except Exception as e:
        return f"⚠️ Gemini error: {e}"
