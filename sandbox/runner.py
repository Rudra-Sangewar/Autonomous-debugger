import subprocess
import tempfile
import os
import shutil

USE_DOCKER = shutil.which("docker") is not None

def run_python_code(code, test_code, timeout=30):
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "solution.py"), "w") as f:
            f.write(code)
        with open(os.path.join(tmpdir, "test_solution.py"), "w") as f:
            f.write("from solution import *\n" + test_code)
        if USE_DOCKER:
            cmd = ["docker", "run", "--rm", "--network", "none",
                   "--memory", "256m", "--cpus", "0.5",
                   "-v", f"{tmpdir}:/code", "-w", "/code",
                   "debugger-sandbox", "sh", "-c",
                   "python3 -m pytest test_solution.py -v --tb=short; chmod -R 777 /code"]
        else:
            cmd = ["python3", "-m", "pytest", "test_solution.py", "-v", "--tb=short"]
        result = subprocess.run(cmd, capture_output=True, text=True,
                               timeout=timeout, cwd=None if USE_DOCKER else tmpdir)
        failed = "failed" in result.stdout.lower() or result.returncode != 0
        return {"success": not failed, "stdout": result.stdout,
                "stderr": result.stderr, "language": "python"}

def run_cpp_code(code, test_code, timeout=30):
    if not USE_DOCKER:
        return {"success": False, "stdout": "",
                "stderr": "C++ requires Docker.", "language": "cpp"}
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "test_solution.cpp"), "w") as f:
            f.write(code)
        result = subprocess.run([
            "docker", "run", "--rm", "--network", "none",
            "--memory", "256m", "--cpus", "0.5",
            "-v", f"{tmpdir}:/code", "-w", "/code",
            "debugger-sandbox", "sh", "-c",
            "g++ -o runner test_solution.cpp -lgtest -lgtest_main -lpthread 2>&1 && ./runner 2>&1; chmod -R 777 /code"
        ], capture_output=True, text=True, timeout=timeout)
        failed = "FAILED" in result.stdout or result.returncode != 0
        return {"success": not failed, "stdout": result.stdout,
                "stderr": result.stderr, "language": "cpp"}

def run_java_code(code, test_code, timeout=30):
    if not USE_DOCKER:
        return {"success": False, "stdout": "",
                "stderr": "Java requires Docker.", "language": "java"}
    with tempfile.TemporaryDirectory() as tmpdir:
        class_name = "Solution"
        for line in code.split("\n"):
            if "public class" in line:
                class_name = line.split("public class")[1].strip().split()[0]
                break
        with open(os.path.join(tmpdir, f"{class_name}.java"), "w") as f:
            f.write(code)
        with open(os.path.join(tmpdir, "TestSolution.java"), "w") as f:
            f.write(test_code)
        result = subprocess.run([
            "docker", "run", "--rm", "--network", "none",
            "--memory", "512m", "--cpus", "0.5",
            "-v", f"{tmpdir}:/code", "-w", "/code",
            "debugger-sandbox", "sh", "-c",
            f"javac {class_name}.java TestSolution.java -cp /usr/local/junit/junit.jar 2>&1 && java -jar /usr/local/junit/junit.jar --class-path . --select-class TestSolution 2>&1; chmod -R 777 /code"
        ], capture_output=True, text=True, timeout=timeout)
        failed = "FAILED" in result.stdout or result.returncode != 0
        return {"success": not failed, "stdout": result.stdout,
                "stderr": result.stderr, "language": "java"}

def run_code(code, test_code, language="python", timeout=30):
    runners = {"python": run_python_code, "cpp": run_cpp_code, "java": run_java_code}
    if language not in runners:
        return {"success": False, "stdout": "", "stderr": f"Unsupported: {language}", "language": language}
    return runners[language](code, test_code, timeout)
