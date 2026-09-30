"""MediLens design system: deep-navy glass dashboard, per the product spec."""

BASE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@600;700;800&family=DM+Sans:wght@400;500;600&display=swap');

:root {
  --bg-1:#07111F; --bg-2:#0B1B2B; --card:#10263A; --card-hi:#15334A;
  --cyan:#36C5F0; --mint:#42E6B5; --amber:#F6C85F; --red:#FF7A7A; --info:#7FB3FF;
  --text:#F4F8FC; --text-2:#AFC1D1; --muted:#71879A;
}

.stApp, .stApp p, .stApp label, .stApp li, .stApp span,
.stApp [data-testid="stMarkdownContainer"] { font-family:'DM Sans',sans-serif; color:var(--text); }
h1,h2,h3,h4 { font-family:'Sora',sans-serif !important; letter-spacing:-.01em; color:var(--text) !important; }
[data-testid="stIconMaterial"], span[class*="material"] {
  font-family:'Material Symbols Rounded','Material Symbols Outlined','Material Icons' !important;
  letter-spacing:normal !important; }

.stApp {
  background:
    radial-gradient(900px 500px at 15% -8%, rgba(54,197,240,.10), transparent 60%),
    radial-gradient(700px 500px at 90% 0%, rgba(66,230,181,.08), transparent 55%),
    linear-gradient(180deg, var(--bg-1) 0%, var(--bg-2) 100%);
  background-attachment: fixed;
}
#MainMenu, header[data-testid="stHeader"], footer { visibility:hidden; height:0; }
.block-container { padding-top:1.2rem; max-width:1180px; }
[data-testid="stSidebar"] { background:var(--bg-2); border-right:1px solid rgba(255,255,255,.06); }
[data-testid="stSidebar"] * { color:var(--text-2) !important; }

/* glass cards */
[class*="st-key-card"], [class*="st-key-detail_"], [class*="st-key-demo_"] {
  background:linear-gradient(180deg, rgba(21,51,74,.9), rgba(16,38,58,.85));
  border:1px solid rgba(255,255,255,.08); border-radius:18px; padding:22px 24px;
  box-shadow:0 1px 0 rgba(255,255,255,.05) inset, 0 18px 34px rgba(0,0,0,.35);
  backdrop-filter: blur(6px);
  transition: transform .18s ease, box-shadow .18s ease;
  margin-bottom: 14px;
}
[class*="st-key-card"]:hover { transform:translateY(-2px); box-shadow:0 1px 0 rgba(255,255,255,.06) inset, 0 24px 44px rgba(0,0,0,.4); }
[data-testid="stForm"] { background:rgba(255,255,255,.03); border:1px solid rgba(255,255,255,.08); border-radius:14px; padding:16px; }

/* inputs */
[data-baseweb="input"] { background:rgba(255,255,255,.05) !important; border:1px solid rgba(255,255,255,.14) !important; border-radius:10px !important; }
[data-baseweb="input"]:focus-within { border-color:var(--cyan) !important; box-shadow:0 0 0 3px rgba(54,197,240,.2); }
.stTextInput input { color:var(--text) !important; -webkit-text-fill-color:var(--text); background:transparent !important; }
.stTextInput input::placeholder { color:var(--muted); }
[data-testid="InputInstructions"] { display:none; }

/* tabs */
.stTabs [data-baseweb="tab"] p { color:var(--text-2) !important; font-weight:600; }
.stTabs [data-baseweb="tab"][aria-selected="true"] p { color:var(--cyan) !important; }

/* buttons */
.stApp .stButton>button, .stApp .stFormSubmitButton>button, .stApp [data-testid="stFileUploaderDropzone"] button {
  background:linear-gradient(135deg, var(--cyan), #2AA9D8); border:0; border-radius:12px;
  padding:.65rem 1.7rem; font-weight:600; color:#052430 !important;
  box-shadow:0 4px 0 #1c7f9e, 0 14px 22px rgba(54,197,240,.25);
  transition: transform .12s ease, box-shadow .12s ease;
}
.stApp .stButton>button *, .stApp .stFormSubmitButton>button *, .stApp [data-testid="stFileUploaderDropzone"] button * { color:#052430 !important; }
.stApp .stButton>button:hover, .stApp .stFormSubmitButton>button:hover { transform:translateY(-2px); box-shadow:0 6px 0 #1c7f9e, 0 18px 28px rgba(54,197,240,.3); }
.stApp .stButton>button:active { transform:translateY(3px); box-shadow:0 1px 0 #1c7f9e; }
.stApp button[kind="secondary"] { background:rgba(255,255,255,.06) !important; box-shadow:none !important; color:var(--text) !important; }
.stApp button[kind="secondary"] * { color:var(--text) !important; }

/* upload */
[data-testid="stFileUploaderDropzone"] {
  background:rgba(255,255,255,.03); border:2px dashed var(--cyan); border-radius:18px; padding:20px;
}
[data-testid="stFileUploaderDropzoneInstructions"] * { color:var(--text) !important; }

/* alerts */
[data-testid="stAlert"] { border-radius:12px !important; background:rgba(127,179,255,.10) !important; border:1px solid rgba(127,179,255,.35) !important; }
[data-testid="stAlert"] * { color:var(--text) !important; }

/* status chips */
.chip { display:inline-block; padding:3px 11px; border-radius:999px; font-size:.78em; font-weight:700; letter-spacing:.02em; }
.chip-normal { background:rgba(66,230,181,.14); color:var(--mint); border:1px solid rgba(66,230,181,.4); }
.chip-attention { background:rgba(246,200,95,.14); color:var(--amber); border:1px solid rgba(246,200,95,.4); }
.chip-high { background:rgba(255,122,122,.14); color:var(--red); border:1px solid rgba(255,122,122,.4); }
.chip-info { background:rgba(127,179,255,.14); color:var(--info); border:1px solid rgba(127,179,255,.4); }
.chip-synthetic { background:rgba(255,255,255,.08); color:var(--text-2); border:1px solid rgba(255,255,255,.2); }

.muted { color:var(--muted); font-size:.88em; }
.section-divider { border-top:1px solid rgba(255,255,255,.08); margin:18px 0; }
</style>
"""

FLAIR = """
<style>
[class*="st-key-card"], [class*="st-key-detail_"], [class*="st-key-demo_"] { animation:flipin .45s cubic-bezier(.2,.9,.2,1) both; }
@keyframes flipin { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }
[data-testid="stInfo"], [data-testid="stAlert"] { animation:fadein .25s ease both; }
@keyframes fadein { from{opacity:0} to{opacity:1} }
</style>
"""

LANDING = """
<style>
.block-container { max-width:100%; padding:0; }
iframe { border:0; display:block; }
div[data-testid="stHorizontalBlock"]:has(button) { position:relative; z-index:5; margin-top:-130px; }
div[data-testid="stButton"] button { font-size:1.02rem; padding:.85rem 2.2rem; }
</style>
"""
