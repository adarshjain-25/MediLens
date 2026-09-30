import os
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

ENV_PATH = Path(__file__).resolve().parent / ".env"
DEFAULT_MODEL = "openai/gpt-oss-20b"


class MissingGroqKey(RuntimeError):
    pass


def get_api_key() -> str:
    """Retrieve Groq API key from session state, .env, or os.environ."""
    try:
        import streamlit as st
        if st.session_state.get("custom_groq_api_key"):
            return st.session_state["custom_groq_api_key"].strip()
    except Exception:
        pass

    load_dotenv(ENV_PATH, override=True)
    return (os.getenv("GROQ_API_KEY") or "").strip()


def get_model() -> str:
    """Retrieve Groq Model from session state, .env, or os.environ."""
    try:
        import streamlit as st
        if st.session_state.get("custom_groq_model"):
            return st.session_state["custom_groq_model"].strip()
    except Exception:
        pass

    load_dotenv(ENV_PATH, override=True)
    return os.getenv("GROQ_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL


def test_connection(api_key: str | None = None, model: str | None = None) -> tuple[bool, str]:
    """Test the Groq API key and model connectivity."""
    key = api_key or get_api_key()
    if not key:
        return False, "GROQ_API_KEY is not set."
    selected_model = model or get_model()
    try:
        client = Groq(api_key=key)
        client.chat.completions.create(
            model=selected_model,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5,
        )
        return True, f"Connection successful! Model '{selected_model}' is responding."
    except Exception as e:
        return False, str(e)


def chat(prompt: str, json_mode: bool = False, temperature: float = 0.2) -> str:
    """Send one prompt to Groq and return the reply text."""
    api_key = get_api_key()
    if not api_key:
        raise MissingGroqKey(
            "GROQ_API_KEY is not set. Put GROQ_API_KEY=your_key in a .env file "
            "next to app.py or configure it under Settings."
        )
    client = Groq(api_key=api_key)
    kwargs = {"response_format": {"type": "json_object"}} if json_mode else {}
    target_model = get_model()

    try:
        response = client.chat.completions.create(
            model=target_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            **kwargs,
        )
        return response.choices[0].message.content
    except Exception as e:
        err_msg = str(e)
        # If the chosen model is not accessible on this account, fall back to openai/gpt-oss-20b
        if ("model_not_found" in err_msg or "does not exist or you do not have access" in err_msg) and target_model != DEFAULT_MODEL:
            fallback_response = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                **kwargs,
            )
            return fallback_response.choices[0].message.content
        raise

