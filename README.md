# MediLens

A patient-facing Patient Record Simplifier & Health Companion Agent. Upload a lab report,
discharge summary or prescription and the app analyzes it automatically -- before you ask
anything -- then answers grounded follow-up questions about it.

## Run
```bash
pip install -r requirements.txt
cp .env.example .env      # add your GROQ_API_KEY
streamlit run app.py
```

## Pages / navigation
- **Landing** -- 3D DNA-helix hero, "Analyze My Report" / "Try Synthetic Report"
- **Login / Sign up**
- **Dashboard** -- report timeline + overview once a report is analyzed
- **Analyze Report** -- upload (or a shortcut to Demo Reports), animated 8-step pipeline, results
- **My Reports** -- this session's analyzed document
- **Demo Reports** -- four labeled SYNTHETIC DATA reports, including two that intentionally
  produce the "no supported values found" empty state, to demonstrate graceful failure
- **Settings** -- privacy note, medical disclaimer, Clear Session (with confirmation)
- **Result detail page** -- gauge (LOW / REFERENCE RANGE / HIGH), why it was flagged, food
  tips, suggested discussion questions, specialist + reason, and a "How this result was
  produced" transparency panel (RULE-BASED / RETRIEVAL / AI EXPLANATION)

## How it maps to the spec
- **Deterministic flagging**: `tools.simplify_and_flag_results` regex-matches known values and
  checks each against a fixed table in `tools.REFERENCE_RANGES`. This decides `flags`/`normal`
  and the priority tier (normal/follow-up/high) -- the LLM never decides this.
- **Deterministic specialist routing**: `tools.find_specialist`, a fixed lookup table, with a
  paired `SPECIALTY_REASONS` table for "why this specialty" -- also not LLM-generated.
- **Deterministic discussion questions**: `tools.discussion_questions` -- a fixed list, not LLM output.
- **AI is used only for**: the one-paragraph plain-language overview, and per-value definitions
  and food guidance (`tools.generate_guidance`) -- all generated *after* the flags are already
  decided, from the fixed findings, so it can't change what's flagged.
- **No-hallucination chat**: `agent.ask_medical_agent` checks the retrieval score before calling
  the LLM at all; below a threshold it returns a fixed "I couldn't find that..." message instead
  of guessing. Every answer shows which report section it came from.
- **Section-aware chunking**: `rag_pipeline.split_by_section` splits on section headers (CBC,
  Lipid Panel, Thyroid, Liver Function, Medications, Clinical Notes) before chunking, so a value
  stays attached to its own reference-range context.
- **Visible pipeline**: the 8-step checklist in `run_pipeline` (received -> extracted -> sections
  identified -> values detected -> ranges checked -> follow-up identified -> explanation
  generated -> ready) makes the automatic, ask-nothing-first behavior visible to the user.
- **No health score**: the dashboard only shows counts (X within range / Y follow-up / Z high
  priority), never a single blended score.

### Honest notes on scope / deviation
- The product spec suggests LangChain + `create_agent`, ChatOllama, HuggingFace embeddings and
  Chroma. This build uses the Groq API directly and a hand-written TF-IDF store instead of
  Chroma/HuggingFace. The pipeline stages and the deterministic-tool requirement are all present,
  just implemented directly. Worth stating plainly in a demo.
- "Download PDF" for the doctor summary is not implemented -- only TXT download -- since no PDF
  generation library was available to install in this environment. Swap in a library such as
  `fpdf2` or `reportlab` if you need a real PDF export.
- The sidebar/dashboard shell, demo reports, and settings pages are all in a single Streamlit
  script using session-state navigation (not separate URLs/routes), since Streamlit is a
  single-page app framework. Mobile/tablet-specific nav variants (bottom nav, hamburger) are not
  separately implemented -- Streamlit's own sidebar collapses on narrow screens by default.
- Animated number counters, skeleton loaders, and per-card 3D tilt-on-hover beyond the existing
  hover-lift are not built -- CSS entrance animations (flip-in, fade-in) are used instead to keep
  the app fast and dependency-free.

## Files
- `app.py` -- page routing, sidebar shell, all nav pages, the visible pipeline, doctor summary
- `landing.py` -- 3D hero (three.js DNA helix + faint grid + particles)
- `auth.py` -- sign up / log in (salted PBKDF2 hashes in `users.json`; demo-grade, not production auth)
- `rag_pipeline.py` -- PDF loading, section-aware chunking, TF-IDF retrieval with scores
- `tools.py` -- deterministic flagging, severity/tiers, specialist lookup + reasons, discussion questions
- `sample_report.py` -- four labeled synthetic demo reports
- `llm.py` -- the one place that calls Groq
- `agent.py` -- grounded Q&A with a deterministic no-hallucination fallback
- `styles.py`, `config.py` -- MediLens dark-glass theme and copy
"# MediLens" 
