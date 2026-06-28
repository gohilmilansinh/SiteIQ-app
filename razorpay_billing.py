"""
razorpay_billing.py
─────────────────────
Basic Razorpay integration: monthly premium access via one-time
order charges (NOT Razorpay's auto-recurring Subscriptions API).

WHY one-time orders instead of true auto-recurring subscriptions:
Razorpay's Subscriptions API (auto-debit every month without the
user re-entering payment details) requires a webhook endpoint to
reliably receive "subscription.charged" / "subscription.halted"
events. Streamlit alone can't host a webhook route — you'd need a
small separate Flask/FastAPI process. That's a real Phase 2 upgrade,
not a Phase 1 blocker.

What THIS gives you, fully working today:
  1. User clicks "Upgrade" → sees a Razorpay Checkout popup
  2. Pays once (card/UPI/netbanking — Razorpay handles all of that)
  3. We verify the payment signature server-side (never trust the
     browser alone) and activate 30 days of premium access
  4. When it expires, they see a "Renew" button and repeat step 1

This is genuinely secure (signature verification prevents someone
faking a successful payment) and genuinely sells subscription-style
access — it just requires a manual click each month instead of
silent auto-debit. Good enough to start charging real money today.

Setup required (one-time, ~5 min):
  1. Sign up at razorpay.com, complete KYC (needed to accept real payments)
  2. Get API Key ID + Key Secret from Dashboard → Settings → API Keys
  3. Add to Streamlit secrets:
        RAZORPAY_KEY_ID = "rzp_test_xxxx"      (or rzp_live_ for production)
        RAZORPAY_KEY_SECRET = "xxxx"
  4. Start in TEST mode (rzp_test_ keys) — use Razorpay's test card
     4111 1111 1111 1111 / any future expiry / any CVV — before
     going live with rzp_live_ keys.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# ── Plan catalogue — adjust pricing freely, this is the only place
# you need to change it ──────────────────────────────────────────
PLANS: Dict[str, Dict[str, Any]] = {
    "monthly": {
        "label":        "Premium Monthly",
        "amount_paise": 49900,   # ₹499 — PLACEHOLDER, tune to your pricing plan
        "days":         30,
        "description":  "Unlimited scoring + full detailed reports + PDF export",
    },
}


def _get_keys() -> tuple[str, str]:
    try:
        import streamlit as st
        key_id = st.secrets.get("RAZORPAY_KEY_ID", "") or os.environ.get("RAZORPAY_KEY_ID", "")
        key_secret = st.secrets.get("RAZORPAY_KEY_SECRET", "") or os.environ.get("RAZORPAY_KEY_SECRET", "")
    except Exception:
        key_id = os.environ.get("RAZORPAY_KEY_ID", "")
        key_secret = os.environ.get("RAZORPAY_KEY_SECRET", "")
    return key_id, key_secret


def _get_client():
    key_id, key_secret = _get_keys()
    if not key_id or not key_secret:
        return None
    try:
        import razorpay
        return razorpay.Client(auth=(key_id, key_secret))
    except Exception as e:
        logger.warning("Razorpay client init failed: %s", e)
        return None


def is_configured() -> bool:
    return _get_client() is not None


def _get_supabase():
    try:
        import streamlit as st
        url = st.secrets.get("SUPABASE_URL", "") or os.environ.get("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_KEY", "") or os.environ.get("SUPABASE_KEY", "")
    except Exception:
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_KEY", "")
    if not url or not key:
        return None
    try:
        from supabase import create_client
        return create_client(url, key)
    except Exception as e:
        logger.warning("Billing: Supabase unavailable: %s", e)
        return None


def create_order(user_id: str, plan_key: str = "monthly") -> Optional[Dict[str, Any]]:
    """Creates a Razorpay order for the given plan. Returns order dict or None."""
    client = _get_client()
    if not client:
        logger.warning("Razorpay not configured — cannot create order.")
        return None

    plan = PLANS.get(plan_key)
    if not plan:
        return None

    try:
        order = client.order.create({
            "amount": plan["amount_paise"],
            "currency": "INR",
            "notes": {"user_id": user_id, "plan": plan_key},
            "payment_capture": 1,
        })

        # Log the attempt immediately (status=created) so we have a
        # record even if the user abandons checkout
        sb = _get_supabase()
        if sb:
            try:
                sb.table("payments").insert({
                    "user_id": user_id,
                    "razorpay_order_id": order["id"],
                    "amount": plan["amount_paise"],
                    "currency": "INR",
                    "plan": plan_key,
                    "status": "created",
                }).execute()
            except Exception as e:
                logger.warning("Failed to log order creation: %s", e)

        return order
    except Exception as e:
        logger.warning("Razorpay order creation failed: %s", e)
        return None


def verify_and_activate(
    order_id: str,
    payment_id: str,
    signature: str,
    user_id: str,
    plan_key: str = "monthly",
) -> tuple[bool, str]:
    """
    Verifies the Razorpay payment signature server-side (critical —
    never trust a "success" message from the browser alone, since
    that could be faked by anyone editing the page/JS). Only after
    verification passes do we activate premium access.

    Returns (success, message)
    """
    client = _get_client()
    if not client:
        return False, "Billing not configured."

    plan = PLANS.get(plan_key)
    if not plan:
        return False, "Unknown plan."

    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature,
        })
    except Exception as e:
        logger.warning("Payment signature verification FAILED for user %s: %s", user_id, e)
        _log_payment_status(user_id, order_id, payment_id, "failed", plan_key)
        return False, "Payment verification failed. If money was deducted, contact support."

    # Signature valid — activate premium
    period_end = datetime.now(timezone.utc) + timedelta(days=plan["days"])
    sb = _get_supabase()
    if not sb:
        return False, "Database not configured — cannot activate plan."

    try:
        existing = (
            sb.table("subscriptions").select("*").eq("user_id", user_id).limit(1).execute()
        )
        if existing.data:
            sb.table("subscriptions").update({
                "plan": "premium",
                "status": "active",
                "current_period_end": period_end.isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }).eq("user_id", user_id).execute()
        else:
            sb.table("subscriptions").insert({
                "user_id": user_id,
                "plan": "premium",
                "status": "active",
                "current_period_end": period_end.isoformat(),
            }).execute()

        _log_payment_status(user_id, order_id, payment_id, "verified", plan_key)
        return True, f"Premium activated until {period_end.strftime('%d %b %Y')}."
    except Exception as e:
        logger.error("Failed to activate subscription for %s: %s", user_id, e)
        return False, "Payment verified but activation failed. Contact support with this reference."


def _log_payment_status(user_id, order_id, payment_id, status, plan_key) -> None:
    sb = _get_supabase()
    if not sb:
        return
    try:
        sb.table("payments").update({
            "razorpay_payment_id": payment_id,
            "status": status,
        }).eq("razorpay_order_id", order_id).execute()
    except Exception as e:
        logger.warning("Failed to log payment status: %s", e)


def get_checkout_widget_html(
    order: Dict[str, Any],
    user_email: str,
    user_name: str,
    plan_key: str = "monthly",
) -> str:
    """
    Returns the HTML/JS for an embeddable Razorpay Checkout popup.
    On success, pushes payment_id/order_id/signature into the parent
    page's URL query params (same pattern app.py already uses for the
    Google Maps address search) so the Python side can read them on
    the next rerun and call verify_and_activate().
    """
    key_id, _ = _get_keys()
    plan = PLANS.get(plan_key, PLANS["monthly"])

    return f"""
    <div id="rzp-status" style="font-family:sans-serif;font-size:13px;
         color:#9ecfc0;text-align:center;padding:10px 0">
      Click below to pay securely via Razorpay
    </div>
    <button id="rzp-pay-btn" style="width:100%;padding:14px;
        background:#1D9E75;color:white;border:none;border-radius:8px;
        font-size:15px;font-weight:600;cursor:pointer;font-family:sans-serif">
      Pay ₹{plan['amount_paise']/100:.0f} — {plan['label']}
    </button>
    <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
    <script>
      document.getElementById('rzp-pay-btn').onclick = function() {{
        var options = {{
          "key": "{key_id}",
          "amount": "{order['amount']}",
          "currency": "{order['currency']}",
          "name": "SiteIQ Analytics",
          "description": "{plan['label']}",
          "order_id": "{order['id']}",
          "prefill": {{
            "name": "{user_name}",
            "email": "{user_email}"
          }},
          "theme": {{ "color": "#1D9E75" }},
          "handler": function (response) {{
            var url = new URL(window.parent.location.href);
            url.searchParams.set('rzp_payment_id', response.razorpay_payment_id);
            url.searchParams.set('rzp_order_id', response.razorpay_order_id);
            url.searchParams.set('rzp_signature', response.razorpay_signature);
            window.parent.location.replace(url.toString());
          }},
          "modal": {{
            "ondismiss": function() {{
              document.getElementById('rzp-status').textContent =
                'Payment cancelled. Click the button to try again.';
            }}
          }}
        }};
        var rzp = new Razorpay(options);
        rzp.open();
      }};
    </script>
    """
