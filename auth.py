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
    """Renders forgot password form."""
    st.markdown("#### Reset Password")
    st.markdown(
        "<div style='font-size:12px;color:#888;margin-bottom:12px'>"
        "Enter your email and we'll send you a reset link.</div>",
        unsafe_allow_html=True,
    )
    email = st.text_input("Email", key="forgot_email",
                          placeholder="you@example.com")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Send Reset Link", type="primary",
                     use_container_width=True):
            if not email:
                st.error("Please enter your email.")
            else:
                _do_forgot_password(email.strip())
    with col2:
        if st.button("Back to Login", use_container_width=True):
            st.session_state.auth_mode = "login"
            st.rerun()


def render_auth_page():
    """
    Renders the full login/signup page.
    Returns True if user is now authenticated, False otherwise.
    """
    _init_session()

    # ── Show forgot password page if requested ────────────
    if st.session_state.auth_mode == "forgot":
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

def _do_forgot_password(email: str):
    client = _get_supabase()
    if not client:
        st.error("Database not configured.")
        return
    try:
        client.auth.reset_password_email(email)
        st.success(
            "Reset link sent! Check your email inbox "
            "(and spam folder). Click the link to reset your password."
        )
    except Exception as e:
        st.error(f"Error sending reset email: {e}")

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