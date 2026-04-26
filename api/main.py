from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
import asyncio
from agent.loop import run_agent

app = FastAPI(title="Autonomous Debugger API")

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

@app.get("/")
def root():
    return {
        "name": "Autonomous Debugger",
        "version": "1.0.0",
        "languages": ["python", "cpp", "java"],
        "status": "running"
    }

@app.post("/debug")
def debug(request: DebugRequest):
    def generate():
        # send start event
        yield f"data: {json.dumps({'type': 'start', 'message': 'Agent started', 'language': request.language})}\n\n"

        history = []
        current_code = request.code

        from sandbox.runner import run_code

        for attempt in range(1, request.max_attempts + 1):
            # send attempt event
            yield f"data: {json.dumps({'type': 'attempt', 'attempt': attempt, 'max': request.max_attempts, 'message': f'Attempt {attempt} — running tests...'})}\n\n"

            # run in sandbox
            result = run_code(current_code, request.test_code, language=request.language)

            if result["success"] and "failed" not in result["stdout"].lower():
                yield f"data: {json.dumps({'type': 'success', 'message': 'All tests passed!', 'fixed_code': current_code, 'attempts': attempt, 'test_output': result['stdout']})}\n\n"
                return

            # send test failure
            yield f"data: {json.dumps({'type': 'test_failed', 'attempt': attempt, 'output': result['stdout'][-800:], 'message': f'Tests failed on attempt {attempt}. Asking AI to fix...'})}\n\n"

            # build history text
            history_text = ""
            for i, h in enumerate(history):
                history_text += f"\n--- Attempt {i+1} (FAILED) ---\nCode:\n{h['code']}\nError:\n{h['error']}\n"

            prompt = f"""You are an expert software engineer. Fix the following broken {request.language} code.

BROKEN CODE:
{request.code}

TEST CODE:
{request.test_code}

{history_text}

LATEST ERROR:
{result['stdout']}
{result['stderr']}

Return ONLY the fixed code. No explanations, no markdown, no backticks. Raw code only."""

            from google import genai
            import os
            from dotenv import load_dotenv
            load_dotenv()
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            import re
            fixed_code = re.sub(r"```[\w]*", "", response.text)
            fixed_code = re.sub(r"```", "", fixed_code).strip()

            yield f"data: {json.dumps({'type': 'ai_fix', 'attempt': attempt, 'message': f'AI generated fix for attempt {attempt}. Testing...', 'code': fixed_code})}\n\n"

            history.append({"attempt": attempt, "code": current_code, "error": result["stdout"][-300:]})
            current_code = fixed_code

        yield f"data: {json.dumps({'type': 'failed', 'message': 'Could not fix after max attempts', 'fixed_code': current_code, 'attempts': request.max_attempts})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

@app.get("/health")
def health():
    return {"status": "healthy"}
