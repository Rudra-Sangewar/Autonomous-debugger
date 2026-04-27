from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
import re
import os
import time
from dotenv import load_dotenv
from sandbox.runner import run_code
from api.benchmark import get_stats, record_run

load_dotenv()

app = FastAPI(title="BugSlayer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class DebugRequest(BaseModel):
    code: str
    test_code: str
    language: str = "python"
    max_attempts: int = 5

def call_gemini(prompt: str) -> str:
    from google import genai
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    models = ["gemini-2.5-flash", "gemini-2.0-flash-lite", "gemini-2.0-flash"]
    for model in models:
        try:
            response = client.models.generate_content(model=model, contents=prompt)
            return response.text
        except Exception as e:
            if "429" in str(e):
                continue
            raise e
    return None

def parse_response(text: str):
    if "FIXED_CODE:" in text and "EXPLANATION:" in text:
        code_part = text.split("FIXED_CODE:")[1].split("EXPLANATION:")[0].strip()
        explanation = text.split("EXPLANATION:")[1].strip()
        code = re.sub(r"```[\w]*", "", code_part)
        code = re.sub(r"```", "", code).strip()
    else:
        code = re.sub(r"```[\w]*", "", text)
        code = re.sub(r"```", "", code).strip()
        explanation = "Bug fixed successfully."
    return code, explanation

@app.get("/")
def root():
    return {
        "name": "BugSlayer",
        "version": "1.0.0",
        "languages": ["python", "cpp", "java"],
        "status": "running"
    }

@app.get("/stats")
def stats():
    return get_stats()

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/debug")
def debug(request: DebugRequest):
    def generate():
        start_time = time.time()
        history = []
        current_code = request.code
        final_explanation = ""

        yield f"data: {json.dumps({'type': 'start', 'message': 'Agent started', 'language': request.language})}\n\n"

        for attempt in range(1, request.max_attempts + 1):
            yield f"data: {json.dumps({'type': 'attempt', 'attempt': attempt, 'max': request.max_attempts, 'message': f'Attempt {attempt} running tests...'})}\n\n"

            result = run_code(current_code, request.test_code, language=request.language)

            if result["success"] and "failed" not in result["stdout"].lower():
                elapsed = round(time.time() - start_time, 1)
                record_run(request.language, True, attempt, elapsed)
                yield f"data: {json.dumps({'type': 'success', 'message': 'All tests passed!', 'fixed_code': current_code, 'attempts': attempt, 'explanation': final_explanation, 'time': elapsed})}\n\n"
                return

            yield f"data: {json.dumps({'type': 'test_failed', 'attempt': attempt, 'output': result['stdout'][-800:], 'message': f'Tests failed on attempt {attempt}'})}\n\n"

            history_text = ""
            for i, h in enumerate(history):
                history_text += f"\nAttempt {i+1} failed:\nCode:\n{h['code']}\nError:\n{h['error']}\n"

            prompt = f"""You are an expert software engineer and debugger.
Fix the broken {request.language} code below.

Your response must be in EXACTLY this format:

FIXED_CODE:
<only the fixed code, no markdown, no backticks>

EXPLANATION:
- <bullet point 1: what bug was found and fixed>
- <bullet point 2: if another bug>
- <bullet point 3: if another bug>

BROKEN CODE:
{request.code}

TEST CODE:
{request.test_code}

{history_text}

LATEST ERROR:
{result['stdout']}
{result['stderr']}"""

            ai_response = call_gemini(prompt)

            if ai_response is None:
                yield f"data: {json.dumps({'type': 'failed', 'message': 'Quota exhausted. Try again tomorrow.'})}\n\n"
                return

            fixed_code, explanation = parse_response(ai_response)
            final_explanation = explanation

            yield f"data: {json.dumps({'type': 'ai_fix', 'attempt': attempt, 'message': f'AI fix #{attempt} generated', 'code': fixed_code, 'explanation': explanation})}\n\n"

            history.append({"attempt": attempt, "code": current_code, "error": result["stdout"][-300:]})
            current_code = fixed_code

        elapsed = round(time.time() - start_time, 1)
        record_run(request.language, False, request.max_attempts, elapsed)
        yield f"data: {json.dumps({'type': 'failed', 'message': 'Could not fix after max attempts', 'fixed_code': current_code, 'attempts': request.max_attempts})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
