from __future__ import annotations
import streamlit as st
import os


def _get_supabase():
    try:
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
        st.error(f"Supabase connection failed: {e}")
        return None


def _init_session():
    for key in ["auth_user", "auth_token", "auth_mode"]:
        if key not in st.session_state:
            st.session_state[key] = None
    if "auth_mode" not in st.session_state or st.session_state.auth_mode is None:
        st.session_state.auth_mode = "login"


def get_current_user():
    """Returns current user dict or None."""
    return st.session_state.get("auth_user", None)


def is_logged_in() -> bool:
    return st.session_state.get("auth_user") is not None


def logout():
    st.session_state.auth_user  = None
    st.session_state.auth_token = None
    st.session_state.result     = None
    st.session_state.compared   = None
    st.session_state.batch_results = None


def render_forgot_password():
    """
    Renders forgot password form using email OTP (6-digit code) —
    NOT a magic link. This avoids the broken hash-fragment parsing
    that magic links require inside a Streamlit iframe, and is free
    on Supabase's existing plan (just needs the email template
    configured to show {{ .Token }} — see NOTE below).
    """
    st.markdown("#### Reset Password")

    stage = st.session_state.get("reset_otp_stage", "request")

    if stage == "request":
        st.markdown(
            "<div style='font-size:12px;color:#888;margin-bottom:12px'>"
            "Enter your email and we'll send you a 6-digit code.</div>",
            unsafe_allow_html=True,
        )
        email = st.text_input("Email", key="forgot_email",
                              placeholder="you@example.com")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Send Code", type="primary",
                         use_container_width=True):
                if not email:
                    st.error("Please enter your email.")
                else:
                    if _do_send_otp(email.strip()):
                        st.session_state.reset_otp_email = email.strip()
                        st.session_state.reset_otp_stage = "verify"
                        st.rerun()
        with col2:
            if st.button("Back to Login", use_container_width=True):
                st.session_state.auth_mode = "login"
                st.rerun()

    elif stage == "verify":
        email = st.session_state.get("reset_otp_email", "")
        st.markdown(
            f"<div style='font-size:12px;color:#888;margin-bottom:12px'>"
            f"Enter the 6-digit code sent to <b>{email}</b>, then "
            f"choose your new password.</div>",
            unsafe_allow_html=True,
        )
        otp_code = st.text_input(
            "6-Digit Code", key="reset_otp_code",
            placeholder="123456", max_chars=6,
        )
        new_pass = st.text_input(
            "New Password", type="password",
            key="reset_otp_new_pass", placeholder="Min 6 characters",
        )
        confirm_pass = st.text_input(
            "Confirm Password", type="password",
            key="reset_otp_confirm_pass", placeholder="Repeat new password",
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Set New Password", type="primary",
                         use_container_width=True):
                if not otp_code or not new_pass or not confirm_pass:
                    st.error("Please fill all fields.")
                elif len(new_pass) < 6:
                    st.error("Password must be at least 6 characters.")
                elif new_pass != confirm_pass:
                    st.error("Passwords do not match.")
                else:
                    if _do_verify_otp_and_reset(email, otp_code.strip(), new_pass):
                        st.session_state.reset_otp_stage = "request"
                        st.session_state.auth_mode = "login"
                        st.success("Password updated! Please log in.")
                        st.rerun()
        with col2:
            if st.button("Resend Code", use_container_width=True):
                if _do_send_otp(email):
                    st.info("New code sent.")
            if st.button("Use Different Email", use_container_width=True):
                st.session_state.reset_otp_stage = "request"
                st.rerun()


def render_auth_page():
    """
    Renders the full login/signup page.
    Returns True if user is now authenticated, False otherwise.
    """
    _init_session()

    # ── Show forgot password page if requested ────────────
    if st.session_state.auth_mode == "forgot":
        if "reset_otp_stage" not in st.session_state:
            st.session_state.reset_otp_stage = "request"
        _, col, _ = st.columns([1, 1.2, 1])
        with col:
            render_forgot_password()
        return False

    # ── Page header ───────────────────────────────────────
    st.markdown(
        """
        <div style='text-align:center;padding:40px 0 10px 0'>
          <div style='font-size:11px;color:#9ecfc0;letter-spacing:3px;
                      margin-bottom:10px'>RETAIL LOCATION INTELLIGENCE</div>
          <div style='font-size:40px;font-weight:800;color:#1D9E75;
                      letter-spacing:-1px'>SiteIQ</div>
          <div style='font-size:14px;color:#888;margin-top:8px'>
            Data-driven retail location intelligence for Gujarat
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Center card ───────────────────────────────────────
    _, col, _ = st.columns([1, 1.2, 1])

    with col:
        # Tab switcher
        t1, t2 = st.tabs(["Login", "Sign Up"])

        # ── LOGIN TAB ─────────────────────────────────────
        with t1:
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            login_email = st.text_input(
                "Email", key="login_email",
                placeholder="you@example.com",
            )
            login_pass = st.text_input(
                "Password", type="password", key="login_pass",
                placeholder="Your password",
            )

            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

            if st.button("Login", type="primary", use_container_width=True, key="btn_login"):
                if not login_email or not login_pass:
                    st.error("Please enter email and password.")
                else:
                    _do_login(login_email.strip(), login_pass)

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            if st.button("Forgot Password?", use_container_width=True,
                         key="btn_forgot"):
                st.session_state.auth_mode = "forgot"
                st.rerun()

        # ── SIGN UP TAB ───────────────────────────────────
        with t2:
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            signup_name = st.text_input(
                "Full Name", key="signup_name",
                placeholder="Your name",
            )
            signup_email = st.text_input(
                "Email", key="signup_email",
                placeholder="you@example.com",
            )
            signup_pass = st.text_input(
                "Password", type="password", key="signup_pass",
                placeholder="Min 6 characters",
            )
            signup_pass2 = st.text_input(
                "Confirm Password", type="password", key="signup_pass2",
                placeholder="Repeat password",
            )

            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

            if st.button("Create Account", type="primary", use_container_width=True, key="btn_signup"):
                if not signup_name or not signup_email or not signup_pass:
                    st.error("Please fill all fields.")
                elif len(signup_pass) < 6:
                    st.error("Password must be at least 6 characters.")
                elif signup_pass != signup_pass2:
                    st.error("Passwords do not match.")
                else:
                    _do_signup(signup_email.strip(), signup_pass, signup_name.strip())

        st.markdown(
            "<div style='text-align:center;font-size:11px;color:#555;"
            "margin-top:20px'>SiteIQ Analytics · Gujarat · Confidential</div>",
            unsafe_allow_html=True,
        )

    return is_logged_in()

def _do_send_otp(email: str) -> bool:
    """
    Sends a 6-digit OTP code to the user's email via Supabase Auth.

    NOTE — one-time Supabase dashboard setup required (free, ~2 min):
    Supabase Auth → Email Templates → "Magic Link" template.
    By default the template only renders {{ .ConfirmationURL }} (a link).
    Edit it to also/instead show {{ .Token }} — that raw token IS the
    6-digit OTP code. Example template body:
        <h2>Your SiteIQ verification code</h2>
        <p>{{ .Token }}</p>
    Once that's saved, sign_in_with_otp() below sends that code instead
    of (or alongside) a clickable link, and verify_otp() consumes it.
    No SMS, no per-send cost — this is Supabase's existing free email flow.
    """
    client = _get_supabase()
    if not client:
        st.error("Database not configured.")
        return False
    try:
        client.auth.sign_in_with_otp({
            "email": email,
            "options": {"should_create_user": False},
        })
        st.success(f"Code sent to {email}. Check your inbox (and spam folder).")
        return True
    except Exception as e:
        err = str(e)
        if "not found" in err.lower() or "user not found" in err.lower():
            st.error("No account found with that email.")
        else:
            st.error(f"Error sending code: {err}")
        return False


def _do_verify_otp_and_reset(email: str, otp_code: str, new_password: str) -> bool:
    """Verifies the OTP code, establishes a session, then updates the password."""
    client = _get_supabase()
    if not client:
        st.error("Database not configured.")
        return False
    try:
        res = client.auth.verify_otp({
            "email": email,
            "token": otp_code,
            "type": "email",
        })
        if not res.session:
            st.error("Invalid or expired code. Please try again.")
            return False

        client.auth.set_session(
            res.session.access_token, res.session.refresh_token
        )
        client.auth.update_user({"password": new_password})
        return True
    except Exception as e:
        err = str(e)
        if "expired" in err.lower():
            st.error("Code expired. Please request a new one.")
        elif "invalid" in err.lower():
            st.error("Incorrect code. Please check and try again.")
        else:
            st.error(f"Error resetting password: {err}")
        return False

def _do_login(email: str, password: str):
    client = _get_supabase()
    if not client:
        st.error("Database not configured. Check Supabase secrets.")
        return

    try:
        res = client.auth.sign_in_with_password({
            "email": email,
            "password": password,
        })
        if res.user:
            st.session_state.auth_user  = {
                "id":    res.user.id,
                "email": res.user.email,
                "name":  res.user.user_metadata.get("full_name", email.split("@")[0]),
            }
            st.session_state.auth_token = res.session.access_token
            st.rerun()
        else:
            st.error("Login failed. Check your credentials.")
    except Exception as e:
        err = str(e)
        if "Email not confirmed" in err:
            st.warning("Please confirm your email before logging in. Check your inbox.")
        elif "Invalid login credentials" in err:
            st.error("Incorrect email or password.")
        else:
            st.error(f"Login error: {err}")


def _do_signup(email: str, password: str, full_name: str):
    client = _get_supabase()
    if not client:
        st.error("Database not configured. Check Supabase secrets.")
        return

    try:
        res = client.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {"full_name": full_name}
            },
        })
        if res.user:
            st.success(
                "Account created! Please check your email to confirm "
                "your account, then come back and log in."
            )
        else:
            st.error("Sign up failed. Please try again.")
    except Exception as e:
        err = str(e)
        if "already registered" in err or "already been registered" in err:
            st.error("This email is already registered. Please login instead.")
        else:
            st.error(f"Sign up error: {err}")