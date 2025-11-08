from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
import pandas as pd
import os, json

from ratio_engine import compute_ratios
from explanations import generate_explanations, answer_chat_question

app = FastAPI(
    title="Financial Ratio Tutor",
    description="Upload balance sheet and PnL CSVs to compute and explain key financial ratios.",
    version="1.2.1"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(openapi_url="/openapi.json", title="Financial Ratio Tutor - API Docs")

@app.get("/")
def health():
    return {"message": "✅ Financial Ratio Tutor API is running"}

LATEST_FILE = "latest_explanations.json"

def run_gemini_background(ratios: dict, context: str):
    try:
        result = generate_explanations(ratios=ratios, context=context or "")
        with open(LATEST_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print("✅ Saved explanations to", LATEST_FILE)
    except Exception as e:
        fallback = {
            "ratio_text": f"📌 General\n• Gemini failed: {e}\n---",
            "summary_text": "📝 Summary\n• AI explanation unavailable."
        }
        with open(LATEST_FILE, "w", encoding="utf-8") as f:
            json.dump(fallback, f, ensure_ascii=False, indent=2)
        print("⚠️ Gemini background generation failed:", e)

@app.post("/upload")
async def upload_files(
    background_tasks: BackgroundTasks,
    balance_sheet: UploadFile = File(...),
    pnl: UploadFile = File(...),
    context: str = Form("")
):
    try:
        bs_df = pd.read_csv(balance_sheet.file)
        pnl_df = pd.read_csv(pnl.file)

        need_cols = {"line_item", "amount"}
        if not need_cols.issubset(set(bs_df.columns)):
            return JSONResponse(status_code=400, content={"error": "balance_sheet.csv must have columns: line_item, amount"})
        if not need_cols.issubset(set(pnl_df.columns)):
            return JSONResponse(status_code=400, content={"error": "pnl.csv must have columns: line_item, amount"})

        ratios = compute_ratios(bs_df, pnl_df)

        # Clear any stale explanation file so you don't read an old error
        if os.path.exists(LATEST_FILE):
            os.remove(LATEST_FILE)

        # IMPORTANT: no include_topics here
        background_tasks.add_task(run_gemini_background, ratios, context)

        return {"status": "✅ Ratios computed. Explanations are being generated…", "ratios": ratios}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Internal server error: {str(e)}"})

@app.get("/explanations")
def get_latest_explanations():
    try:
        if os.path.exists(LATEST_FILE):
            with open(LATEST_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {"explanations": data}
        return {"message": "⏳ Explanations not ready yet. Please wait a moment."}
    except Exception as e:
        return {"error": f"Failed to load explanations: {str(e)}"}

@app.post("/ask")
async def ask(question: str = Form(...)):
    try:
        answer = answer_chat_question(question=question, context="")
        return {"answer": answer}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)
