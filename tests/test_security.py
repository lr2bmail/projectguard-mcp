from projectguard_mcp.reviewers.security import review_security


def test_sql_injection_detected():
    files = {"app.py": 'query = "SELECT * FROM users WHERE id=" + user_id'}
    result = review_security("web app", files, ["login"])
    codes = {f["code"] for f in result["findings"]}
    assert "POSSIBLE_SQL_INJECTION" in codes


def test_xss_innerhtml_detected():
    files = {"app.js": 'document.getElementById("x").innerHTML = userInput;'}
    result = review_security("web app", files)
    codes = {f["code"] for f in result["findings"]}
    assert "FRAMEWORK_XSS_PATTERN" in codes


def test_ssrf_detected():
    files = {"server.py": "import requests\nurl = request.args.get('url')\nrequests.get(url)"}
    result = review_security("web app", files, ["api"])
    codes = {f["code"] for f in result["findings"]}
    assert "SSRF_USER_CONTROLLED_URL" in codes


def test_insecure_deserialization_detected():
    files = {"app.py": "import pickle\ndata = pickle.loads(user_data)"}
    result = review_security("web app", files)
    codes = {f["code"] for f in result["findings"]}
    assert "INSECURE_DESERIALIZATION" in codes


def test_debug_true_detected():
    files = {"app.py": "app.run(debug=True)"}
    result = review_security("web app", files)
    codes = {f["code"] for f in result["findings"]}
    assert "DEBUG_TRUE" in codes


def test_weak_crypto_detected():
    files = {"auth.py": "import hashlib\nhashlib.md5(password.encode()).hexdigest()"}
    result = review_security("web app", files, ["login"])
    codes = {f["code"] for f in result["findings"]}
    assert "WEAK_CRYPTO" in codes


def test_hardcoded_credentials_detected():
    files = {"config.py": 'DATABASE_URL = "postgresql://admin:pass123@localhost/db"'}
    result = review_security("web app", files)
    codes = {f["code"] for f in result["findings"]}
    assert "HARDCODED_CREDENTIALS" in codes


def test_cors_wildcard_detected():
    files = {"server.py": 'app.add_middleware(CORSMiddleware, allow_origins=["*"])'}
    result = review_security("web app", files)
    codes = {f["code"] for f in result["findings"]}
    assert "CORS_WILDCARD_ORIGIN" in codes


def test_framework_xss_detected():
    files = {"component.jsx": '<div dangerouslySetInnerHTML={{__html: userInput}} />'}
    result = review_security("web app", files)
    codes = {f["code"] for f in result["findings"]}
    assert "FRAMEWORK_XSS_PATTERN" in codes


def test_path_traversal_detected():
    files = {"server.py": "filepath = os.path.join(base, '../' + user_input)"}
    result = review_security("web app", files)
    codes = {f["code"] for f in result["findings"]}
    assert "PATH_TRAVERSAL_RISK" in codes


def test_jwt_algorithm_none_detected():
    files = {"auth.py": 'jwt.decode(token, key="", algorithm="none")'}
    result = review_security("web app", files, ["login"])
    codes = {f["code"] for f in result["findings"]}
    assert "JWT_ALGORITHM_NONE" in codes


def test_clean_code_passes():
    files = {
        "app.py": (
            "from flask import Flask\n"
            "app = Flask(__name__)\n"
            "@app.route('/')\n"
            "def index():\n"
            "    return 'Hello'"
        ),
    }
    result = review_security("web app", files)
    assert result["score"] >= 85
