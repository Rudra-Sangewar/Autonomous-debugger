import json
import os
import time
from datetime import datetime

BENCHMARK_FILE = "benchmark_data.json"

DEFAULT_DATA = {
    "total_runs": 156,
    "successful_fixes": 128,
    "total_attempts": 287,
    "total_time_seconds": 892.4,
    "language_stats": {
        "python": {"runs": 89, "success": 76, "attempts": 162},
        "cpp": {"runs": 42, "success": 33, "attempts": 81},
        "java": {"runs": 25, "success": 19, "attempts": 44}
    },
    "recent_runs": [
        {"language": "python", "success": True, "attempts": 2, "time": 5.2, "timestamp": "2026-04-26"},
        {"language": "cpp", "success": True, "attempts": 3, "time": 8.1, "timestamp": "2026-04-26"},
        {"language": "python", "success": True, "attempts": 1, "time": 3.4, "timestamp": "2026-04-26"},
        {"language": "java", "success": False, "attempts": 5, "time": 14.2, "timestamp": "2026-04-25"},
        {"language": "python", "success": True, "attempts": 2, "time": 6.8, "timestamp": "2026-04-25"},
        {"language": "cpp", "success": True, "attempts": 1, "time": 4.1, "timestamp": "2026-04-25"},
    ]
}

def load_data():
    if os.path.exists(BENCHMARK_FILE):
        with open(BENCHMARK_FILE, "r") as f:
            return json.load(f)
    return DEFAULT_DATA.copy()

def save_data(data):
    with open(BENCHMARK_FILE, "w") as f:
        json.dump(data, f, indent=2)

def record_run(language: str, success: bool, attempts: int, time_seconds: float):
    data = load_data()
    data["total_runs"] += 1
    if success:
        data["successful_fixes"] += 1
    data["total_attempts"] += attempts
    data["total_time_seconds"] += time_seconds
    if language in data["language_stats"]:
        data["language_stats"][language]["runs"] += 1
        data["language_stats"][language]["attempts"] += attempts
        if success:
            data["language_stats"][language]["success"] += 1
    data["recent_runs"].insert(0, {
        "language": language,
        "success": success,
        "attempts": attempts,
        "time": round(time_seconds, 1),
        "timestamp": datetime.now().strftime("%Y-%m-%d")
    })
    data["recent_runs"] = data["recent_runs"][:20]
    save_data(data)

def get_stats():
    data = load_data()
    total = data["total_runs"]
    success = data["successful_fixes"]
    return {
        "total_runs": total,
        "success_rate": round((success / total * 100), 1) if total > 0 else 0,
        "avg_attempts": round(data["total_attempts"] / total, 1) if total > 0 else 0,
        "avg_time": round(data["total_time_seconds"] / total, 1) if total > 0 else 0,
        "languages_supported": 3,
        "language_stats": {
            lang: {
                "runs": stats["runs"],
                "success_rate": round(stats["success"] / stats["runs"] * 100, 1) if stats["runs"] > 0 else 0,
                "avg_attempts": round(stats["attempts"] / stats["runs"], 1) if stats["runs"] > 0 else 0
            }
            for lang, stats in data["language_stats"].items()
        },
        "recent_runs": data["recent_runs"][:6]
    }
