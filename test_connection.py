"""
Quick connectivity test — run this BEFORE main.py to verify everything works.
  python test_connection.py

Uses the TopstepX HTTP API directly (bypasses project_x_py SDK auth bugs).
Auth flow per API docs:
  1. POST /api/Auth/loginKey → get session token (valid 24h)
  2. Pass token as Bearer in Authorization header for all subsequent calls
"""
import asyncio
import logging
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("test")

BASE_URL = "https://api.topstepx.com/api"


async def test():
    # ------------------------------------------------------------------ #
    # Step 1: Authenticate
    # ------------------------------------------------------------------ #
    logger.info("Testing TopstepX connection...")
    username = os.getenv("PROJECTX_USERNAME", "")
    api_key  = os.getenv("PROJECTX_API_KEY", "")

    if not username or not api_key:
        logger.error("PROJECTX_USERNAME or PROJECTX_API_KEY not set in .env — aborting.")
        return

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=15) as http:
        # Step 2: POST /Auth/loginKey
        resp = await http.post(
            "/Auth/loginKey",
            json={"userName": username, "apiKey": api_key},
            headers={"accept": "text/plain", "Content-Type": "application/json"},
        )
        body = resp.json()

        # Step 3: Validate and store the session token
        if not body.get("success") or body.get("errorCode", -1) != 0:
            logger.error(
                f"TopstepX authentication FAILED — "
                f"success={body.get('success')}, "
                f"errorCode={body.get('errorCode')}, "
                f"errorMessage={body.get('errorMessage')!r}"
            )
            logger.error(
                "Check that PROJECTX_USERNAME and PROJECTX_API_KEY in .env match your "
                "TopstepX account credentials exactly (API key from the TopstepX portal)."
            )
            return

        session_token = body["token"]
        logger.info("Authenticated with TopstepX — session token obtained (valid 24h).")

        auth_headers = {
            "Authorization": f"Bearer {session_token}",
            "Content-Type": "application/json",
        }

        # ------------------------------------------------------------------ #
        # Fetch accounts
        # ------------------------------------------------------------------ #
        acc_resp = await http.post(
            "/Account/search",
            json={"onlyActiveAccounts": True},
            headers=auth_headers,
        )
        acc_body = acc_resp.json()
        accounts = acc_body.get("accounts", [])
        logger.info(f"All accounts ({len(accounts)} total):")
        for acc in accounts:
            eligible = "YES - eligible for trading" if acc.get("canTrade") else "NO  - not eligible"
            logger.info(
                f"  [{eligible}]  {acc.get('name')}  "
                f"(id={acc.get('id')}, balance=${acc.get('balance', 0):,.2f})"
            )

        if not accounts:
            logger.error("No accounts returned — the session token may still be invalid.")
            return

        # ------------------------------------------------------------------ #
        # Fetch MES bars using the first account
        # ------------------------------------------------------------------ #
        account_id = accounts[0]["id"]
        logger.info(f"Using account id={account_id} for bar fetch test.")

        # Search for MES contract
        contract_resp = await http.post(
            "/Contract/search",
            json={"searchText": "MES", "live": False},
            headers=auth_headers,
        )
        contracts = contract_resp.json().get("contracts", [])
        if contracts:
            contract_id = contracts[0]["id"]
            logger.info(f"Found contract: {contracts[0].get('name')} (id={contract_id})")
        else:
            logger.warning("No MES contracts found — skipping bar fetch.")
            contract_id = None

        if contract_id:
            import datetime
            now  = datetime.datetime.utcnow()
            from_ = (now - datetime.timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
            to_   = now.strftime("%Y-%m-%dT%H:%M:%SZ")
            bar_resp = await http.post(
                "/History/retrieveBars",
                json={
                    "contractId": contract_id,
                    "live": False,
                    "startTime": from_,
                    "endTime": to_,
                    "unit": 2,        # 2 = minute bars
                    "unitNumber": 5,  # 5-minute bars
                    "limit": 50,
                    "includePartialBar": False,
                },
                headers=auth_headers,
            )
            bars = bar_resp.json().get("bars", [])
            logger.info(f"Got {len(bars)} 5-min bars for MES.")

        logger.info("TopstepX connection test PASSED.")

    # ------------------------------------------------------------------ #
    # Anthropic API
    # ------------------------------------------------------------------ #
    logger.info("Testing Anthropic API connection...")
    try:
        import anthropic
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=32,
            messages=[{"role": "user", "content": "Reply with just: OK"}],
        )
        logger.info(f"Anthropic API response: {response.content[0].text}")
        logger.info("Anthropic connection test PASSED.")
    except Exception as e:
        logger.error(f"Anthropic API FAILED: {e}")


if __name__ == "__main__":
    asyncio.run(test())
