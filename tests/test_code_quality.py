from projectguard_mcp.reviewers.code_quality import review_code_quality


def test_secret_detection():
    files = {"config.py": 'api_key = "sk_live_abcdef1234567890"'}
    result = review_code_quality(files)
    codes = {f["code"] for f in result["findings"]}
    assert "POSSIBLE_SECRET" in codes


def test_todo_detected():
    files = {"app.py": "# TODO: implement this later\npass"}
    result = review_code_quality(files)
    codes = {f["code"] for f in result["findings"]}
    assert "TODO_LEFT_IN_CODE" in codes


def test_weak_exception_detected():
    files = {"app.py": "try:\n    do_something()\nexcept:\n    pass"}
    result = review_code_quality(files)
    codes = {f["code"] for f in result["findings"]}
    assert "WEAK_EXCEPTION_HANDLING" in codes


def test_risky_command_detected():
    files = {"app.py": "import subprocess\nsubprocess.run(cmd, shell=True)"}
    result = review_code_quality(files)
    codes = {f["code"] for f in result["findings"]}
    assert "RISKY_COMMAND_EXECUTION" in codes


def test_no_test_files_detected():
    files = {"app.py": "code", "utils.py": "code", "models.py": "code"}
    result = review_code_quality(files)
    codes = {f["code"] for f in result["findings"]}
    assert "NO_TEST_FILES" in codes


def test_debug_console_log_detected():
    files = {"app.js": "function init() {\n    console.log('debug');\n}"}
    result = review_code_quality(files)
    codes = {f["code"] for f in result["findings"]}
    assert "DEBUG_STATEMENT_LEFT" in codes


def test_debugger_statement_detected():
    files = {"app.js": "function debug() {\n    debugger;\n}"}
    result = review_code_quality(files)
    codes = {f["code"] for f in result["findings"]}
    assert "DEBUG_STATEMENT_LEFT" in codes


def test_hardcoded_local_url_detected():
    files = {"config.js": 'const API_URL = "http://localhost:3000/api";'}
    result = review_code_quality(files)
    codes = {f["code"] for f in result["findings"]}
    assert "HARDCODED_LOCAL_URL" in codes


def test_empty_catch_detected():
    files = {"app.js": "try {\n    doSomething();\n} catch (e) {\n}"}
    result = review_code_quality(files)
    codes = {f["code"] for f in result["findings"]}
    assert "EMPTY_CATCH_BLOCK" in codes


def test_large_file_detected():
    files = {"big.py": "\n".join(["line"] * 600)}
    result = review_code_quality(files)
    codes = {f["code"] for f in result["findings"]}
    assert "LARGE_FILE" in codes


def test_commented_out_code_detected():
    content = "\n".join([
        "# def process_data(input):",
        "#     for item in input:",
        "#         return item",
        "x = 1",
    ])
    files = {"app.py": content}
    result = review_code_quality(files)
    codes = {f["code"] for f in result["findings"]}
    assert "COMMENTED_OUT_CODE" in codes


def test_async_without_error_handling_detected():
    files = {"handler.js": "async function fetchData() {\n    const res = await fetch(url);\n    return res.json();\n}"}
    result = review_code_quality(files)
    codes = {f["code"] for f in result["findings"]}
    assert "ASYNC_WITHOUT_ERROR_HANDLING" in codes


def test_clean_code_passes():
    files = {
        "app.py": "from flask import Flask\napp = Flask(__name__)\n@app.route('/')\ndef index():\n    return 'Hello'",
        "tests/test_app.py": "def test_index():\n    assert True",
    }
    result = review_code_quality(files)
    assert result["score"] >= 85
