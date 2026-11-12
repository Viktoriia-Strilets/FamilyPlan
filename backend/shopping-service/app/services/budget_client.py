import os
import httpx


BUDGET_SERVICE_URL = os.getenv(
    "BUDGET_SERVICE_URL",
    "http://budget-service:8000"
)

INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "")


async def send_purchase_to_budget(
    purchase_id: int,
    family_id: int,
    email: str,
    username: str,
    title: str,
    amount: float,
    category: str,
    date: str
):
    if not INTERNAL_API_KEY:
        raise RuntimeError(
            "INTERNAL_API_KEY не налаштований"
        )

    payload = {
        "purchase_id": purchase_id,
        "family_id": family_id,
        "email": email,
        "username": username,
        "title": title,
        "amount": amount,
        "category": category,
        "date": date
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            f"{BUDGET_SERVICE_URL}/budgets/expenses/from-shopping",
            json=payload,
            headers={
                "X-Internal-Api-Key": INTERNAL_API_KEY
            }
        )

        if response.status_code >= 400:
            try:
                detail = response.json().get(
                    "detail",
                    "Помилка Budget Service"
                )
            except (ValueError, AttributeError):
                detail = "Помилка Budget Service"

            raise RuntimeError(str(detail))

        return response.json()


async def complete_planned_expense(
    expense_id: int,
    purchase_id: int,
    family_id: int,
    amount: float,
    date: str
):
    if not INTERNAL_API_KEY:
        raise RuntimeError(
            "INTERNAL_API_KEY не налаштований"
        )

    payload = {
        "expense_id": expense_id,
        "purchase_id": purchase_id,
        "family_id": family_id,
        "amount": amount,
        "date": date
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            (
                f"{BUDGET_SERVICE_URL}"
                "/budgets/expenses/complete-planned-from-shopping"
            ),
            json=payload,
            headers={
                "X-Internal-Api-Key": INTERNAL_API_KEY
            }
        )

        if response.status_code >= 400:
            try:
                detail = response.json().get(
                    "detail",
                    "Помилка Budget Service"
                )
            except (ValueError, AttributeError):
                detail = "Помилка Budget Service"

            raise RuntimeError(str(detail))

        return response.json()
