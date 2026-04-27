from google import genai
import os
import re
from dotenv import load_dotenv
from sandbox.runner import run_code

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_PROMPT = """You are an expert software engineer and debugger.
You will be given broken Python code and failing test output.
Your job is to analyze the error and return FIXED code.

STRICT RULES:
- Return ONLY the fixed Python code
- No explanations, no markdown, no backticks
- Do not include the test code
- Just raw Python code that will pass the tests
"""

def extract_code(text: str) -> str:
    text = re.sub(r"```python", "", text)
    text = re.sub(r"```", "", text)
    return text.strip()

def run_agent(broken_code: str, test_code: str, language: str = "python", max_attempts: int = 5) -> dict:
    print("\n" + "="*50)
    print("AUTONOMOUS DEBUGGER AGENT STARTED")
    print("="*50)

    history = []
    current_code = broken_code

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
                "history": history
            }

        print(f"Tests failed. Asking AI to fix...")
        print(f"Error:\n{result['stdout'][-500:]}")

        history_text = ""
        for i, h in enumerate(history):
            history_text += f"\n--- Attempt {i+1} (FAILED) ---\n"
            history_text += f"Code tried:\n{h['code']}\n"
            history_text += f"Error:\n{h['error']}\n"

        prompt = f"""{SYSTEM_PROMPT}

ORIGINAL BROKEN CODE:
{broken_code}

TEST CODE (do not modify this):
{test_code}

{history_text}

LATEST ERROR OUTPUT:
{result['stdout']}
{result['stderr']}

Now return the fixed Python code:"""

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

        fixed_code = extract_code(response.text)

        history.append({
            "attempt": attempt,
            "code": current_code,
            "error": result["stdout"][-300:]
        })

        current_code = fixed_code
        print(f"AI generated a fix. Testing it...")

    return {
        "success": False,
        "fixed_code": current_code,
        "attempts": max_attempts,
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
    assert add(-1, 1) == 0

def test_multiply():
    assert multiply(3, 4) == 12
    assert multiply(0, 5) == 0

def test_divide():
    assert divide(10, 2) == 5.0
    assert divide(9, 3) == 3.0
"""

    result = run_agent(broken_code, test_code)

    print("\n" + "="*50)
    print("FINAL RESULT")
    print("="*50)
    print(f"Success: {result['success']}")
    print(f"Total attempts: {result['attempts']}")
    print(f"\nFixed code:\n{result['fixed_code']}")
