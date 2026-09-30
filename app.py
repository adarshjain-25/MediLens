import os
import time
import tempfile
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env", override=True)

import auth
from agent import ask_medical_agent
from config import CHAT_DISCLAIMER, DISCLAIMER, PRIVACY_NOTE, PROJECT_NAME, SUPPORT_TEXT, TAGLINE
from landing import landing_html
from llm import MissingGroqKey, get_api_key, get_model, test_connection
from rag_pipeline import process_document, process_text, search_vector_store, split_by_section
from sample_report import DEMO_REPORTS
from styles import BASE, FLAIR, LANDING
from tools import (DETECTION_METHOD, SPECIALTY_REASONS, discussion_questions,
                    find_specialist, generate_guidance, severity, simplify_and_flag_results)

st.set_page_config(page_title=PROJECT_NAME, layout="wide", page_icon="🩺", initial_sidebar_state="expanded")
st.markdown(BASE, unsafe_allow_html=True)
st.markdown(FLAIR, unsafe_allow_html=True)

st.session_state.setdefault("page", "landing")
st.session_state.setdefault("user", None)
st.session_state.setdefault("nav", "Dashboard")
st.session_state.setdefault("processed", False)
st.session_state.setdefault("chat_history", [])
st.session_state.setdefault("confirm_clear", False)


def go(page: str, nav: str | None = None):
    st.session_state.page = page
    if nav:
        st.session_state.nav = nav
    st.rerun()


# ================================================================== Landing
def landing_page():
    st.markdown(LANDING, unsafe_allow_html=True)
    components.html(landing_html(PROJECT_NAME, TAGLINE, SUPPORT_TEXT), height=640)

    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        if st.button("Analyze My Report", use_container_width=True):
            st.session_state.pending_nav = "Analyze Report"
            go("app" if st.session_state.user else "login")
    with c2:
        if st.button("Try Synthetic Report", use_container_width=True):
            st.session_state.pending_nav = "Demo Reports"
            go("app" if st.session_state.user else "login")
    with c3:
        st.write("")

    f1, f2, f3 = st.columns(3)
    for col, title in zip((f1, f2, f3),
                           ("Plain-language explanation", "Deterministic result flagging",
                            "Document-grounded answers")):
        with col:
            with st.container(key=f"card_feat_{title[:6]}"):
                st.markdown(f"**{title}**")
    st.markdown(f"<p class='muted' style='text-align:center;margin-top:18px;'>{PRIVACY_NOTE}</p>",
                unsafe_allow_html=True)


# ==================================================================== Login
def login_page():
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        with st.container(key="card_login"):
            st.markdown(f"## 🩺 {PROJECT_NAME}")
            st.caption("Your account is used only to access your application session.")
            tab_in, tab_up = st.tabs(["LOGIN", "SIGN UP"])

            with tab_in:
                with st.form("login"):
                    email = st.text_input("Email")
                    pw = st.text_input("Password", type="password")
                    if st.form_submit_button("Log in"):
                        ok, res = auth.login(email, pw)
                        if ok:
                            st.session_state.user = res
                            go("app", st.session_state.pop("pending_nav", "Dashboard"))
                        else:
                            st.error(res)

            with tab_up:
                with st.form("signup"):
                    name = st.text_input("Full name")
                    email = st.text_input("Email", key="su_email")
                    pw = st.text_input("Password (8+ characters)", type="password", key="su_pw")
                    if st.form_submit_button("Create account"):
                        ok, res = auth.signup(name, email, pw)
                        if ok:
                            st.session_state.user = res
                            go("app", st.session_state.pop("pending_nav", "Dashboard"))
                        else:
                            st.error(res)

            if st.button("← Back"):
                go("landing")


# ============================================================ Shared helpers
def reset_report():
    for k in ("processed", "summary", "vector_store", "specialists", "guidance",
              "tiers", "chat_history", "doc_meta"):
        st.session_state.pop(k, None)
    st.session_state.chat_history = []


PIPELINE_STEPS = [
    "Document received", "Text extracted", "Sections identified", "Values detected",
    "Reference ranges checked", "Follow-up items identified",
    "Plain-language explanation generated", "Report ready",
]


def run_pipeline(full_text: str, doc_meta: dict):
    """Fixed order the track/spec requires, with a visible step-by-step pipeline."""
    box = st.empty()

    def render(done):
        lines = [f"{'✅' if i < done else '⬜'} {s}" for i, s in enumerate(PIPELINE_STEPS)]
        box.markdown("  \n".join(lines))

    render(0)
    store, text = process_text(full_text)
    render(3)  # received, extracted, sections identified (section split happens inside chunk_text)

    summary = simplify_and_flag_results(text)
    render(5)  # values detected + reference ranges checked

    flags = summary.get("flags", [])
    specialists = find_specialist(",".join(flags)) if flags else {}
    render(6)  # follow-up items identified

    guidance = generate_guidance(summary.get("details", {}))
    render(7)  # explanation generated
    time.sleep(0.15)
    render(8)
    time.sleep(0.2)
    box.empty()

    tiers = {}
    for label, d in summary.get("details", {}).items():
        _, _, tier, _ = severity(d["value"], d["low"], d["high"], d["status"])
        tiers[label] = tier

    st.session_state.vector_store = store
    st.session_state.summary = summary
    st.session_state.specialists = specialists
    st.session_state.guidance = guidance
    st.session_state.tiers = tiers
    st.session_state.doc_meta = doc_meta
    st.session_state.processed = True


def gauge_html(d: dict) -> str:
    value, low, high, unit = d["value"], d["low"], d["high"], d["unit"]
    span = max(high - low, 0.001)
    pos = min(max(12.5 + 75 * ((value - low) / span), -6), 106)
    color = "var(--mint)" if d["status"] == "normal" else "var(--red)"
    return f"""
    <div style="margin:8px 0 4px;">
      <div style="display:flex;justify-content:space-between;font-size:.78em;color:var(--muted);font-weight:700;letter-spacing:.04em;">
        <span>LOW</span><span>REFERENCE RANGE</span><span>HIGH</span>
      </div>
      <div style="position:relative;height:12px;border-radius:8px;margin-top:4px;
                  background:linear-gradient(90deg,var(--red) 0%,var(--red) 25%,var(--mint) 25%,var(--mint) 75%,var(--red) 75%,var(--red) 100%);">
        <div style="position:absolute;left:{pos}%;top:-6px;width:3px;height:24px;background:var(--text);
                    box-shadow:0 0 0 4px rgba(244,248,252,.15);border-radius:2px;transition:left .4s ease;"></div>
      </div>
      <div style="display:flex;justify-content:space-between;font-size:.8em;color:var(--text-2);margin-top:4px;">
        <span>{low} {unit}</span><span>{high} {unit}</span>
      </div>
      <div style="margin-top:8px;font-size:.95em;">
        Your value: <b style="color:{color}">{value} {unit}</b>
      </div>
    </div>"""


def status_chip(tier: str, text: str) -> str:
    cls = {"normal": "chip-normal", "followup": "chip-attention", "high": "chip-high"}.get(tier, "chip-info")
    return f'<span class="chip {cls}">{text}</span>'


# ============================================================== Result cards
def flagged_card(label: str, d: dict, tier: str):
    level, urgency, _, _ = severity(d["value"], d["low"], d["high"], d["status"])
    doc = st.session_state.specialists.get(label.lower(), "General Practitioner")
    with st.container(key=f"card_row_{label}"):
        top = st.columns([3, 1])
        with top[0]:
            st.markdown(f"**{label.title()}**  {status_chip(tier, urgency)}", unsafe_allow_html=True)
        with top[1]:
            if st.button("View details →", key=f"open_{label}", use_container_width=True):
                st.session_state.detail_label = label
                st.session_state.prev_nav = st.session_state.nav
                go("app", "detail")
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<span class='muted'>Your value</span><br><b>{d['value']} {d['unit']}</b>", unsafe_allow_html=True)
        c2.markdown(f"<span class='muted'>Reference range</span><br><b>{d['low']}–{d['high']} {d['unit']}</b>", unsafe_allow_html=True)
        c3.markdown(f"<span class='muted'>Status</span><br><b>{level}</b>", unsafe_allow_html=True)
        st.markdown(f"<span class='muted'>Specialist</span> — {doc}", unsafe_allow_html=True)


def normal_row(label: str, d: dict):
    c1, c2, c3, c4 = st.columns([2, 1.4, 1.8, 1.6])
    c1.write(f"**{label.title()}**")
    c2.write(f"{d['value']} {d['unit']}")
    c3.write(f"{d['low']}–{d['high']} {d['unit']}")
    c4.markdown(status_chip("normal", "Within configured range"), unsafe_allow_html=True)


# ==================================================================== Detail
def detail_page():
    label = st.session_state.get("detail_label")
    summary = st.session_state.get("summary")
    if not label or not summary or label not in summary.get("details", {}):
        go("app", "Dashboard")
        return

    if st.button("← Back to Report"):
        go("app", st.session_state.get("prev_nav", "Dashboard"))

    d = summary["details"][label]
    guidance = st.session_state.guidance.get(label, {})
    tier = st.session_state.tiers.get(label, "normal")
    level, urgency, _, _ = severity(d["value"], d["low"], d["high"], d["status"])
    doc = st.session_state.specialists.get(label.lower(), "General Practitioner")
    reason = SPECIALTY_REASONS.get(doc, "This specialist can evaluate this result in the context of your overall health.")

    st.title(label.title())
    st.markdown(status_chip(tier, level), unsafe_allow_html=True)

    with st.container(key="card_gauge"):
        st.subheader("Your value")
        st.markdown(gauge_html(d), unsafe_allow_html=True)
        st.markdown(f"Reference range: **{d['low']}–{d['high']} {d['unit']}**")

    if d["status"] != "normal":
        with st.container(key="card_why"):
            st.subheader("Why this was flagged")
            direction = "above" if d["status"] == "high" else "below"
            st.write(f"The reported value is {direction} the reference range configured for this test. "
                     f"Discuss the result with a qualified healthcare professional.")
            st.markdown(f"<span class='muted'>Detection method: {DETECTION_METHOD}</span>", unsafe_allow_html=True)

    with st.container(key="card_about"):
        st.subheader("What is this test?")
        st.write(guidance.get("definition", "—"))
        st.markdown(f"**Healthy target:** {guidance.get('limit', '—')}")

    fc1, fc2 = st.columns(2)
    with fc1:
        with st.container(key="card_eat"):
            st.subheader("🥗 Basic food tips — recommended")
            for f in guidance.get("foods_to_eat", []):
                st.markdown(f"- {f}")
    with fc2:
        with st.container(key="card_avoid"):
            st.subheader("🚫 Basic food tips — not recommended")
            for f in guidance.get("foods_to_avoid", []):
                st.markdown(f"- {f}")

    if d["status"] != "normal":
        with st.container(key="card_discuss"):
            st.subheader("Suggested discussion")
            st.markdown(f"**Why it may matter:** {guidance.get('disadvantages', '—')}")
            st.markdown("**Questions you could ask:**")
            for q in discussion_questions(label):
                st.markdown(f"- {q}")

        with st.container(key="card_specialist"):
            st.subheader("Who could help?")
            st.markdown(f"### {doc}")
            st.write(f"Consider discussing this result with a {doc.lower()} or another qualified "
                     f"healthcare professional, depending on your overall clinical context.")
            st.markdown(f"**Why this specialty?** {reason}")
            st.markdown("<span class='muted'>Specialist routing is based on the application's "
                        "configured lookup table and is not a diagnosis.</span>", unsafe_allow_html=True)
    else:
        with st.container(key="card_specialist"):
            st.subheader("Who could help?")
            st.write("This value is within the configured reference range — no specialist visit is indicated for it right now.")

    with st.container(key="card_transparency"):
        with st.expander("How this result was produced"):
            st.markdown(f"**RULE-BASED** — {DETECTION_METHOD} against a fixed reference range "
                        f"({d['low']}–{d['high']} {d['unit']}).")
            hits = search_vector_store(st.session_state.vector_store, label, top_k=1)
            src = hits[0].strip().splitlines()[0].strip() if hits and hits[0].strip() else "your uploaded document"
            st.markdown(f"**RETRIEVAL** — This value was located in: *{src}*.")
            st.markdown("**AI EXPLANATION** — The definition, food guidance and plain-language "
                        "phrasing above were generated by an AI model from the rule-based finding; "
                        "the finding itself was not decided by the AI.")

    st.caption(f"⚠️ {DISCLAIMER}")


# ================================================================ Dashboard
def dashboard_view():
    st.subheader("Dashboard")
    with st.container(key="card_timeline"):
        st.markdown("**Report Timeline**")
        steps = ["Report uploaded", "Document processed", "Results analyzed",
                 "Follow-up items identified", "Doctor discussion"]
        done = 5 if st.session_state.processed else 0
        st.markdown("  \n".join(f"{'✅' if i < done else '⬜'} {s}" for i, s in enumerate(steps)))

    if not st.session_state.processed:
        with st.container(key="card_empty"):
            st.write("No report analyzed yet in this session.")
            c1, c2 = st.columns(2)
            if c1.button("Analyze Report", use_container_width=True):
                go("app", "Analyze Report")
            if c2.button("Try a Demo Report", use_container_width=True):
                go("app", "Demo Reports")
        return

    summary = st.session_state.summary
    details = summary.get("details", {})
    tiers = st.session_state.tiers
    total = len(details)
    n_normal = sum(1 for t in tiers.values() if t == "normal")
    n_follow = sum(1 for t in tiers.values() if t == "followup")
    n_high = sum(1 for t in tiers.values() if t == "high")

    with st.container(key="card_overview"):
        st.markdown("**REPORT OVERVIEW**")
        st.write(summary.get("summary", ""))
        st.markdown(f"<span class='muted'>{total} results analyzed</span>", unsafe_allow_html=True)
        st.markdown(
            f"{status_chip('normal', f'{n_normal} within reference range')}&nbsp;&nbsp;"
            f"{status_chip('followup', f'{n_follow} need follow-up')}&nbsp;&nbsp;"
            f"{status_chip('high', f'{n_high} require prompt discussion')}",
            unsafe_allow_html=True,
        )

    p1, p2, p3 = st.columns(3)
    with p1, st.container(key="card_p_normal"):
        st.markdown(status_chip("normal", "NORMAL"), unsafe_allow_html=True)
        st.markdown(f"## {n_normal}")
        st.caption("Within the configured reference range")
    with p2, st.container(key="card_p_follow"):
        st.markdown(status_chip("followup", "FOLLOW-UP"), unsafe_allow_html=True)
        st.markdown(f"## {n_follow}")
        st.caption("Discuss with a healthcare professional")
    with p3, st.container(key="card_p_high"):
        st.markdown(status_chip("high", "HIGH PRIORITY"), unsafe_allow_html=True)
        st.markdown(f"## {n_high}")
        st.caption("Seek timely professional advice")


# ============================================================= Analyze view
def analyze_view():
    if not st.session_state.processed:
        with st.container(key="card_upload"):
            st.subheader("Drop your medical report here")
            st.caption("PDF reports supported — lab report, discharge summary, or prescription. "
                       "Analysis begins automatically; you don't need to ask a question.")
            uploaded = st.file_uploader("Choose PDF", type=["pdf"], label_visibility="collapsed")
            st.markdown("<div style='text-align:center;color:var(--muted);margin:6px 0;'>or</div>",
                        unsafe_allow_html=True)
            _, mid, _ = st.columns([1, 1, 1])
            with mid:
                try_sample = st.button("Try Synthetic Report", use_container_width=True)

        if try_sample:
            go("app", "Demo Reports")

        if uploaded:
            with st.container(key="card_pipeline"):
                st.markdown(f"📄 **{uploaded.name}** · {uploaded.size // 1024} KB · uploaded")
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded.getvalue())
                    path = tmp.name
                try:
                    reader_text = None
                    try:
                        from pypdf import PdfReader
                        reader_text = "\n".join((p.extract_text() or "") for p in PdfReader(path).pages)
                    except Exception:
                        st.error("We couldn't read this document.")
                        reader_text = None
                    if reader_text is not None:
                        if not reader_text.strip():
                            st.error("We couldn't read this document.")
                        else:
                            run_pipeline(reader_text, {"name": uploaded.name, "source": "upload"})
                except MissingGroqKey as e:
                    st.error(f"⚠️ {e}")
                except Exception as e:
                    st.error(f"Could not process this report: {e}")
                finally:
                    if os.path.exists(path):
                        os.unlink(path)
            if st.session_state.processed:
                st.rerun()
        return

    render_results()


def render_results():
    summary = st.session_state.summary
    details = summary.get("details", {})
    tiers = st.session_state.tiers

    if not details:
        with st.container(key="card_empty_result"):
            st.info("We couldn't identify supported test values in this report. "
                    "You can still ask questions about it below.")
    else:
        flagged = [l for l in summary.get("flags", [])]
        normal = [l for l in summary.get("normal", [])]

        if flagged:
            st.subheader("Results that may need follow-up")
            for label in flagged:
                flagged_card(label, details[label], tiers.get(label, "followup"))

        if normal:
            with st.expander(f"Results within reference range ({len(normal)})", expanded=False):
                for label in normal:
                    normal_row(label, details[label])

    with st.container(key="card_sections"):
        st.markdown("**Report sections detected**")
        sections = [s for s in split_by_section(
            "\n".join(st.session_state.vector_store["chunks"])) if s.strip()]
        for sec in sections[:8]:
            head = sec.strip().splitlines()[0][:40]
            with st.expander(head):
                st.text(sec.strip()[:800])

    b1, b2 = st.columns(2)
    with b1:
        if st.button("Analyze another report", use_container_width=True):
            reset_report()
            st.rerun()
    with b2:
        if details:
            st.download_button("⬇️ Prepare Doctor Summary (TXT)", build_doctor_summary(),
                                file_name="medilens_doctor_summary.txt", use_container_width=True)

    st.divider()
    render_chat()


def render_chat():
    st.subheader("Ask about your report")
    for m in st.session_state.chat_history:
        with st.chat_message(m["role"]):
            st.write(m["content"])
            if m.get("source"):
                st.caption(f"Source: {m['source']}")
    if q := st.chat_input("Ask a question about your uploaded report…"):
        st.session_state.chat_history.append({"role": "user", "content": q})
        with st.chat_message("user"):
            st.write(q)
        with st.chat_message("assistant"):
            with st.spinner("Searching your report…"):
                try:
                    answer, source = ask_medical_agent(q, st.session_state.vector_store)
                except MissingGroqKey as e:
                    answer, source = f"⚠️ {e}", None
                except Exception as e:
                    answer, source = f"⚠️ Something went wrong reaching the AI service: {e}", None
            st.write(answer)
            if source:
                st.caption(f"Source: {source}")
            st.caption(CHAT_DISCLAIMER)
        st.session_state.chat_history.append({"role": "assistant", "content": answer, "source": source})


def build_doctor_summary() -> str:
    s = st.session_state.summary
    meta = st.session_state.get("doc_meta", {})
    lines = [
        f"{PROJECT_NAME} — Doctor Summary", "=" * 42, "",
        f"Document type: {meta.get('source', 'uploaded document')}",
        f"Document name: {meta.get('name', 'n/a')}", "",
        f"Tests analyzed: {len(s.get('details', {}))}", "",
        "Overview:", s.get("summary", ""), "",
    ]
    if s.get("flags"):
        lines.append("Flagged results:")
        for label in s["flags"]:
            d = s["details"][label]
            lines.append(f"  - {label.title()}: {d['value']} {d['unit']} "
                         f"(reference {d['low']}-{d['high']} {d['unit']})")
            lines.append(f"    Specialist routing: {st.session_state.specialists.get(label.lower(), '')}")
            for q in discussion_questions(label):
                lines.append(f"    Discussion point: {q}")
        lines.append("")
    lines.append("This summary reflects rule-based reference-range comparisons only and is not a diagnosis.")
    return "\n".join(lines)


# ============================================================= My Reports
def my_reports_view():
    st.subheader("My Reports")
    if not st.session_state.processed:
        st.info("No report has been analyzed in this session yet.")
        return
    meta = st.session_state.get("doc_meta", {})
    with st.container(key="card_myreport"):
        st.markdown(f"**{meta.get('name', 'Uploaded report')}**")
        st.caption(f"Source: {meta.get('source', 'upload')} · {len(st.session_state.summary.get('details', {}))} tests analyzed")
        if st.button("Open analysis"):
            go("app", "Analyze Report")


# ============================================================= Demo Reports
def demo_view():
    st.subheader("Synthetic Demo Reports")
    st.caption("SYNTHETIC DATA — these reports do not belong to real patients.")
    cols = st.columns(2)
    for i, rep in enumerate(DEMO_REPORTS):
        with cols[i % 2], st.container(key=f"demo_{rep['id']}"):
            st.markdown(f"**{rep['title']}**  " + '<span class="chip chip-synthetic">SYNTHETIC DATA</span>',
                        unsafe_allow_html=True)
            st.write(rep["description"])
            if st.button("Load this report", key=f"load_{rep['id']}", use_container_width=True):
                with st.spinner("Analyzing…"):
                    try:
                        run_pipeline(rep["text"], {"name": rep["title"], "source": "synthetic demo"})
                    except MissingGroqKey as e:
                        st.error(f"⚠️ {e}")
                if st.session_state.get("processed"):
                    go("app", "Analyze Report")


# ================================================================ Settings
def settings_view():
    st.subheader("Settings")

    with st.container(key="card_api_config"):
        st.markdown("⚙️ **AI Service & Groq API Key**")
        current_key = get_api_key()
        masked_key = (current_key[:6] + "..." + current_key[-4:]) if len(current_key) > 10 else ("Not Set" if not current_key else "Configured")
        current_model = get_model()

        st.write(f"Key Status: **{'🟢 Connected / Key Present' if current_key else '🔴 Missing Key'}** (`{masked_key}`)")

        new_key_input = st.text_input(
            "Groq API Key (enter new key to update)",
            type="password",
            placeholder="gsk_...",
            help="Get your free key from https://console.groq.com/keys",
        )

        models_available = [
            "llama-3.1-8b-instant",
            "llama-3.3-70b-versatile",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
        ]
        curr_idx = models_available.index(current_model) if current_model in models_available else 0
        selected_model = st.selectbox("LLM Model", models_available, index=curr_idx)

        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("💾 Save Key & Model", use_container_width=True):
                active_key = new_key_input.strip() if new_key_input.strip() else current_key
                st.session_state["custom_groq_api_key"] = active_key
                st.session_state["custom_groq_model"] = selected_model
                env_file = Path(__file__).resolve().parent / ".env"
                env_file.write_text(f"GROQ_API_KEY={active_key}\nGROQ_MODEL={selected_model}\n", encoding="utf-8")
                st.success("Configuration saved and applied!")
                st.rerun()
        with c2:
            if st.button("⚡ Test Connection", use_container_width=True):
                with st.spinner("Testing Groq connection..."):
                    test_key = new_key_input.strip() if new_key_input.strip() else current_key
                    ok, msg = test_connection(test_key, selected_model)
                    if ok:
                        st.success(f"✅ {msg}")
                    else:
                        st.error(f"❌ Connection failed: {msg}")

    with st.container(key="card_privacy"):
        st.markdown("🔒 **Private session**")
        st.write("Your uploaded document is used as the source for this session's analysis and retrieval.")
        st.markdown(f"<span class='muted'>{PRIVACY_NOTE}</span>", unsafe_allow_html=True)

    with st.container(key="card_disclaimer"):
        st.markdown("**Medical Disclaimer**")
        st.write(DISCLAIMER)

    with st.container(key="card_clear"):
        st.markdown("**Clear Session**")
        if not st.session_state.confirm_clear:
            if st.button("Clear Session"):
                st.session_state.confirm_clear = True
                st.rerun()
        else:
            st.warning("Clear this document and its session data?")
            c1, c2 = st.columns(2)
            if c1.button("Cancel"):
                st.session_state.confirm_clear = False
                st.rerun()
            if c2.button("Clear Session", key="confirm_clear_btn"):
                reset_report()
                st.session_state.confirm_clear = False
                go("app", "Dashboard")


# ================================================================ App shell
NAV_ITEMS = ["Dashboard", "Analyze Report", "My Reports", "Demo Reports", "Settings"]


def analyzer_page():
    if st.session_state.nav == "detail":
        detail_page()
        return

    with st.sidebar:
        st.markdown(f"### 🩺 {PROJECT_NAME}")
        for item in NAV_ITEMS:
            if st.button(item, key=f"nav_{item}", use_container_width=True,
                         type="primary" if st.session_state.nav == item else "secondary"):
                st.session_state.nav = item
                st.rerun()
        st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
        st.caption("🔒 Private session")
        st.caption("Medical Disclaimer")
        if st.button("Reset Session", use_container_width=True):
            reset_report()
            st.rerun()

    top_l, top_r = st.columns([4, 1])
    top_l.title("Patient Record Companion")
    with top_r:
        st.write(f"👤 **{st.session_state.user}**")
        if st.button("Log out"):
            reset_report()
            st.session_state.user = None
            go("landing")

    {
        "Dashboard": dashboard_view,
        "Analyze Report": analyze_view,
        "My Reports": my_reports_view,
        "Demo Reports": demo_view,
        "Settings": settings_view,
    }.get(st.session_state.nav, dashboard_view)()


# ==================================================================== Router
page = st.session_state.page
if page == "app" and not st.session_state.user:
    page = "login"
{"landing": landing_page, "login": login_page, "app": analyzer_page}.get(page, landing_page)()
