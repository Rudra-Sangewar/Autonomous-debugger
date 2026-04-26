# ⚡ BugSlayer — Autonomous AI Debugging Agent

> Paste broken code. Watch AI fix it. No manual debugging.

BugSlayer is an autonomous debugging agent that finds and fixes bugs in your code automatically. It runs your tests in an isolated Docker sandbox, sends failures to Gemini AI, gets a fix, retests — and loops until all tests pass.

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square)
![C++](https://img.shields.io/badge/C++-11-orange?style=flat-square)
![Java](https://img.shields.io/badge/Java-11-red?style=flat-square)
![Docker](https://img.shields.io/badge/Docker-sandboxed-green?style=flat-square)
![Gemini](https://img.shields.io/badge/Gemini-2.5_Flash-purple?style=flat-square)

---

## How it works

Broken code + tests
↓
Docker sandbox runs tests safely
↓
Tests fail → error sent to Gemini AI
↓
AI reasons about bug → generates fix
↓
Fix tested again in sandbox
↓
Loop until all tests pass ✓


## Features

- **Multi-language** — Python, C++, Java (more coming)
- **Sandboxed execution** — untrusted code runs in isolated Docker containers with no internet, limited RAM and CPU
- **Agentic loop** — agent remembers previous failed attempts and learns within session
- **Live streaming UI** — watch the agent think in real time, attempt by attempt
- **Verified fixes** — agent never claims success without proof from passing tests

## Tech stack

- **Backend** — Python, FastAPI, Server-Sent Events streaming
- **AI** — Google Gemini 2.5 Flash via tool calling
- **Sandbox** — Docker with pytest (Python), Google Test (C++), JUnit (Java)
- **Frontend** — Vanilla JS, CodeMirror editor

## Run locally

**Prerequisites:** Python 3.11+, Docker

```bash
# clone
git clone https://github.com/Rudra-Sangewar/Autonomous-debugger.git
cd Autonomous-debugger

# setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# add your Gemini API key
echo "GEMINI_API_KEY=your_key_here" > .env

# build Docker sandbox
docker build -t debugger-sandbox sandbox/

# start API
python3 -m uvicorn api.main:app --reload --port 8000

# open ui/index.html in your browser
```

## Example

**Input — broken Python:**
```python
def add(a, b):
    return a - b   # bug

def divide(a, b):
    return b / a   # bug
```

**BugSlayer output — fixed in 2 attempts:**
```python
def add(a, b):
    return a + b   # fixed

def divide(a, b):
    return a / b   # fixed
```

## Architecture


┌─────────────────────────────────────┐
│           BugSlayer UI              │
│     (CodeMirror + live log)         │
└────────────────┬────────────────────┘
│ HTTP POST /debug
┌────────────────▼────────────────────┐
│         FastAPI Backend             │
│      (streaming SSE response)       │
└────────────────┬────────────────────┘
│
┌─────────▼──────────┐
│    Agentic Loop     │
│  (loop.py)          │
└──────┬──────────────┘
│              │
┌─────────▼───┐    ┌─────▼────────┐
│Docker Sandbox│    │  Gemini AI   │
│ pytest/gtest │    │ 2.5 Flash    │
│ /junit       │    │              │
└─────────────┘    └──────────────┘




## Roadmap

- [ ] Auto test generation — agent writes tests automatically
- [ ] JavaScript support (Jest)
- [ ] GitHub PR integration — auto-fix failing CI
- [ ] VS Code extension

## Built by

Rudra Sangewar — ENTC Final Year Student
[GitHub](https://github.com/Rudra-Sangewar)

---

*BugSlayer fixes bugs so you don't have to.*
