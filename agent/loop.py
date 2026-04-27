from google import genai
import os
import re
from dotenv import load_dotenv
from sandbox.runner import run_code

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_PROMPT = """You are an expert software engineer and debugger.
You will be given broken code and failing test output.

Your response must be in this EXACT format and nothing else:

FIXED_CODE:
<only the fixed code here, no markdown, no backticks>

EXPLANATION:
<2-4 bullet points explaining what bugs were found and fixed, each starting with a dash>

Do not add anything before FIXED_CODE: or after the explanation."""

def extract_fix_and_explanation(text: str) -> tuple:
    code = ""
    explanation = ""
    try:
        if "FIXED_CODE:" in text and "EXPLANATION:" in text:
            code_part = text.split("FIXED_CODE:")[1].split("EXPLANATION:")[0].strip()
            explanation_part = text.split("EXPLANATION:")[1].strip()
            code = re.sub(r"```[\w]*", "", code_part)
            code = re.sub(r"```", "", code).strip()
            explanation = explanation_part.strip()
        else:
            code = re.sub(r"```[\w]*", "", text)
            code = re.sub(r"```", "", code).strip()
            explanation = "Bug fixed successfully."
    except:
        code = text.strip()
        explanation = "Bug fixed successfully."
    return code, explanation

def run_agent(broken_code: str, test_code: str, language: str = "python", max_attempts: int = 5) -> dict:
    print("\n" + "="*50)
    print("AUTONOMOUS DEBUGGER AGENT STARTED")
    print("="*50)

    history = []
    current_code = broken_code
    final_explanation = ""

    for attempt in range(1, max_attempts + 1):
        print(f"\n[Attempt {attempt}/{max_attempts}]")
        print("Running tests...")

        result = run_code(current_code, test_code, language=language)

        if result["success"] and "failed" not in result["stdout"].lower():
            print(f"ALL TESTS PASSED on attempt {attempt}!")
            return {
                "success": True,
                "fixed_code": current_code,
                "attempts": attempt,
                "explanation": final_explanation,
                "history": history
            }

        print(f"Tests failed. Asking AI to fix...")

        history_text = ""
        for i, h in enumerate(history):
            history_text += f"\n--- Attempt {i+1} (FAILED) ---\n"
            history_text += f"Code:\n{h['code']}\nError:\n{h['error']}\n"

        prompt = f"""{SYSTEM_PROMPT}

LANGUAGE: {language}

ORIGINAL BROKEN CODE:
{broken_code}

TEST CODE:
{test_code}

{history_text}

LATEST ERROR:
{result['stdout']}
{result['stderr']}"""

        models_to_try = ["gemini-2.5-flash", "gemini-2.0-flash-lite", "gemini-2.0-flash"]
        response = None
        for model_name in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                break
            except Exception as e:
                if "429" in str(e):
                    continue
                raise e

        if response is None:
            raise Exception("All Gemini models quota exhausted. Try again tomorrow.")

        fixed_code, explanation = extract_fix_and_explanation(response.text)
        final_explanation = explanation

        history.append({
            "attempt": attempt,
            "code": current_code,
            "error": result["stdout"][-300:]
        })

        current_code = fixed_code
        print(f"AI generated fix. Explanation: {explanation[:100]}")

    return {
        "success": False,
        "fixed_code": current_code,
        "attempts": max_attempts,
        "explanation": final_explanation,
        "history": history
    }


if __name__ == "__main__":
    broken_code = """
def add(a, b):
    return a - b

def multiply(a, b):
    return a + b

def divide(a, b):
    return a * b
"""
    test_code = """
def test_add():
    assert add(2, 3) == 5

def test_multiply():
    assert multiply(3, 4) == 12

def test_divide():
    assert divide(10, 2) == 5.0
"""
    result = run_agent(broken_code, test_code)
    print("\n" + "="*50)
    print("RESULT:", result["success"])
    print("ATTEMPTS:", result["attempts"])
    print("EXPLANATION:\n", result["explanation"])
    print("FIXED CODE:\n", result["fixed_code"])
