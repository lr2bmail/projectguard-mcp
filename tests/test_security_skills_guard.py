from __future__ import annotations

from projectguard_mcp.reviewers.api_security import review_api_security
from projectguard_mcp.reviewers.docker_security import review_docker_security
from projectguard_mcp.reviewers.payment_webhooks import review_payment_webhook_security
from projectguard_mcp.reviewers.security_recommender import recommend_security_reviews


def _codes(result: dict) -> set[str]:
    return {finding["code"] for finding in result["findings"]}


def test_recommender_detects_api_payment_and_docker_reviews():
    result = recommend_security_reviews(
        "paid API SaaS",
        files={
            "routes/api.py": "@app.route('/api/orders/<int:id>', methods=['GET'])\ndef get_order(id): pass",
            "billing/stripe.py": "stripe checkout webhook balance",
            "Dockerfile": "FROM python:3.12",
        },
        features=["Stripe checkout", "account balance", "admin dashboard"],
    )

    assert "review_security" in result["recommended_reviews"]
    assert "review_api_security" in result["recommended_reviews"]
    assert "review_payment_webhook_security" in result["recommended_reviews"]
    assert "review_docker_security" in result["recommended_reviews"]
    assert "review_api_security" in result["blocking_reviews"]
    assert "review_payment_webhook_security" in result["blocking_reviews"]


def test_api_security_flags_missing_object_authorization():
    result = review_api_security(
        "API SaaS",
        files={
            "routes/orders.py": """
@app.route('/api/orders/<int:id>', methods=['GET'])
def get_order(id):
    return Order.query.get(id)
""",
        },
        features=["user dashboard", "orders API"],
    )

    codes = _codes(result)
    assert "MISSING_OBJECT_AUTHORIZATION" in codes
    assert "API_RATE_LIMIT_NOT_VISIBLE" in codes


def test_api_security_flags_admin_route_without_role_check():
    result = review_api_security(
        "admin dashboard",
        files={
            "routes/admin.py": """
@app.route('/admin/users', methods=['POST'])
def create_user():
    return create_user_from_request()
""",
        },
        features=["admin dashboard"],
    )

    assert "ADMIN_ROUTE_WITHOUT_ROLE_CHECK" in _codes(result)


def test_payment_webhook_security_flags_success_redirect_without_webhook():
    result = review_payment_webhook_security(
        "paid SaaS",
        files={
            "billing.py": """
def create_checkout():
    session = stripe.checkout.Session.create(success_url='/success')
    user.balance += 10
""",
        },
        features=["Stripe checkout", "account balance"],
    )

    codes = _codes(result)
    assert "PAYMENT_WEBHOOK_NOT_VISIBLE" in codes
    assert "PAYMENT_IDEMPOTENCY_NOT_VISIBLE" in codes
    assert "SUCCESS_REDIRECT_TRUSTED_AS_PAYMENT_RISK" in codes
    assert "BALANCE_UPDATED_WITHOUT_VISIBLE_WEBHOOK_VERIFICATION" in codes


def test_payment_webhook_security_passes_basic_verified_webhook_flow():
    result = review_payment_webhook_security(
        "paid SaaS",
        files={
            "billing.py": """
def stripe_webhook(request):
    event = stripe.Webhook.construct_event(payload, signature, webhooksecret)
    if ProcessedEvent.exists(provider_event_id=event.id):
        return 'duplicate'
    amount = event.data.object.amount_total
    currency = event.data.object.currency
    before_balance = user.balance
    after_balance = before_balance + amount
    refund_state = 'none'
""",
        },
        features=["Stripe checkout", "account balance", "refunds"],
    )

    assert "PAYMENT_WEBHOOK_NOT_VISIBLE" not in _codes(result)
    assert "WEBHOOK_SIGNATURE_NOT_VISIBLE" not in _codes(result)
    assert "PAYMENT_IDEMPOTENCY_NOT_VISIBLE" not in _codes(result)


def test_docker_security_flags_high_risk_compose_settings():
    result = review_docker_security(
        {
            "docker-compose.yml": """
services:
  app:
    image: projectguard:latest
    privileged: true
    network_mode: host
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      API_KEY: secret-value
""",
        }
    )

    codes = _codes(result)
    assert "DOCKER_PRIVILEGED_CONTAINER" in codes
    assert "DOCKER_HOST_NETWORK" in codes
    assert "DOCKER_SOCKET_MOUNTED" in codes
    assert "DOCKER_SECRET_IN_ENV" in codes
    assert "DOCKERIGNORE_MISSING" in codes


def test_docker_security_flags_root_latest_missing_healthcheck():
    result = review_docker_security({"Dockerfile": "FROM python:latest\nCOPY . /app\nCMD python app.py"})

    codes = _codes(result)
    assert "DOCKER_BASE_IMAGE_LATEST" in codes
    assert "DOCKER_RUNS_AS_ROOT" in codes
    assert "DOCKER_MISSING_HEALTHCHECK" in codes
