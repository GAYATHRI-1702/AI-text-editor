import streamlit as st
import re
import json
import os
import io
import sys
import base64
import copy
import shelve
import builtins
from datetime import datetime, timezone

# ─── Page Config ─────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Collaborative Editor",
    page_icon="📝",
    layout="wide"
)

# ─── Shared State (shelve — persists on Streamlit Cloud) ──────────
DB_PATH = os.path.join(os.path.dirname(__file__), "collab_db")

EMPTY_STATE = {
    "users":     {},
    "document":  [],
    "locked_by": None,
    "chat":      [],
    "versions":  [],
    "media":     []
}

TESTING_MODE = False  # Set to True to wipe data on every restart

def load_state():
    with shelve.open(DB_PATH) as db:
        if TESTING_MODE or "state" not in db:
            db["state"] = copy.deepcopy(EMPTY_STATE)
        state = dict(db["state"])
    # back-compat: add any missing keys
    for k, v in EMPTY_STATE.items():
        if k not in state:
            state[k] = copy.deepcopy(v)
    return state

def save_state(state):
    with shelve.open(DB_PATH) as db:
        db["state"] = state

# ─── Per-session ──────────────────────────────────────────────────
if "current_user" not in st.session_state:
    st.session_state.current_user = None

# ─── Helpers ─────────────────────────────────────────────────────
def is_editor(state):
    u = st.session_state.current_user
    return u is not None and state["users"].get(u, {}).get("role") == "Editor"

def doc_text(state):
    return " ".join(e["text"] for e in state["document"] if e.get("type", "text") != "code")

def word_count(text):
    return len(re.findall(r'\S+', text)) if text.strip() else 0

def char_count(text):
    return len(text)

def get_ai_suggestions(state):
    content = doc_text(state)
    suggestions = []
    if not content.strip():
        return ["Document is empty. Start with an introduction."]
    if "introduction" not in content.lower():
        suggestions.append("Consider adding an **Introduction** section.")
    if "conclusion" not in content.lower():
        suggestions.append("Consider adding a **Conclusion** section.")
    wc = word_count(content)
    if wc < 20:
        suggestions.append(f"Document is short ({wc} words). Add more details.")
    if content[0].islower():
        suggestions.append("Start the document with a capital letter.")
    last_char = content.rstrip()[-1] if content.strip() else ""
    if last_char and last_char not in ".!?":
        suggestions.append("Last sentence may be missing end punctuation.")
    words = content.split()
    for i in range(1, len(words)):
        if words[i].lower() == words[i - 1].lower():
            suggestions.append(f'Repeated word detected: **"{words[i]}"**.')
            break
    if not suggestions:
        suggestions.append("Document looks good! No suggestions.")
    return suggestions

# Safe builtins allowed in code execution sandbox
_SAFE_BUILTINS = {
    name: getattr(builtins, name)
    for name in [
        "print", "range", "len", "int", "float", "str", "bool",
        "list", "dict", "tuple", "set", "sum", "min", "max",
        "abs", "round", "sorted", "enumerate", "zip", "map",
        "filter", "isinstance", "type", "repr", "reversed"
    ]
}

def run_code(code):
    """Execute Python code in a restricted sandbox and capture stdout."""
    # Reject any import or dangerous keyword before running
    forbidden = ["import", "open", "exec", "eval", "__", "os.", "sys.", "subprocess"]
    for word in forbidden:
        if word in code:
            return "", f"Blocked: '{word}' is not allowed in code blocks."
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    try:
        sys.stdout = stdout_capture
        sys.stderr = stderr_capture
        safe_globals = {"__builtins__": _SAFE_BUILTINS}
        compiled = compile(code, "<sandbox>", "exec")
        eval(compiled, safe_globals)  # noqa: S307 — sandboxed namespace
    except Exception as e:
        stderr_capture.write(str(e))
    finally:
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
    return stdout_capture.getvalue(), stderr_capture.getvalue()

# ─── Load CSS from external file ────────────────────────────────
_css_path = os.path.join(os.path.dirname(__file__), "style.css")
with open(_css_path) as _f:
    st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  LOAD SHARED STATE
# ═══════════════════════════════════════════════════════════════
state = load_state()

# ═══════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<div class="main-title">📝 CollabEditor</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">AI Collaborative Rich Text Editor</div>', unsafe_allow_html=True)
    st.divider()

    # ── Register ──────────────────────────────────────────────
    with st.expander("➕ Register User", expanded=False):
        reg_name = st.text_input("Username", key="reg_name", placeholder="e.g. Alice")
        reg_role = st.selectbox("Role", ["Editor", "Viewer"], key="reg_role")
        if st.button("Register", key="btn_register"):
            name = reg_name.strip()
            if not name:
                st.error("Username cannot be empty.")
            elif name in state["users"]:
                st.warning(f"'{name}' already exists.")
            else:
                state["users"][name] = {
                    "role": reg_role,
                    "registered_at": datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
                }
                save_state(state)
                st.success(f"'{name}' registered as {reg_role}.")
                st.rerun()

    # ── Login ─────────────────────────────────────────────────
    with st.expander("🔑 Login", expanded=True):
        if st.session_state.current_user:
            u    = st.session_state.current_user
            role = state["users"].get(u, {}).get("role", "Unknown")
            badge = "badge-editor" if role == "Editor" else "badge-viewer"
            st.markdown(f"Logged in as **{u}**")
            st.markdown(f'<span class="{badge}">{role}</span>', unsafe_allow_html=True)
            if st.button("Logout", key="btn_logout"):
                st.session_state.current_user = None
                st.rerun()
        else:
            user_list = list(state["users"].keys())
            login_name = st.selectbox(
                "Select user",
                ["-- select --"] + user_list,
                key="login_select"
            )
            if st.button("Login", key="btn_login"):
                if login_name == "-- select --":
                    st.error("Select a user.")
                else:
                    st.session_state.current_user = login_name
                    st.rerun()

    st.divider()

    # ── Status Bar ────────────────────────────────────────────
    st.markdown("**📊 Status Bar**")
    content = doc_text(state)
    col1, col2 = st.columns(2)
    col1.metric("Words", word_count(content))
    col2.metric("Chars", char_count(content))

    if state["locked_by"]:
        st.markdown(f'<span class="badge-locked">🔒 Locked by {state["locked_by"]}</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge-free">🔓 Unlocked</span>', unsafe_allow_html=True)

    st.divider()

    # ── Registered Users ──────────────────────────────────────
    if state["users"]:
        st.markdown("**👥 Registered Users**")
        for uname, udata in state["users"].items():
            badge = "badge-editor" if udata["role"] == "Editor" else "badge-viewer"
            indicator = "🟢" if uname == st.session_state.current_user else "⚪"
            st.markdown(
                f'{indicator} **{uname}** <span class="{badge}">{udata["role"]}</span>',
                unsafe_allow_html=True
            )

    st.divider()
    st.markdown('<div class="sub-title">🔄 Auto-refreshes every 5s</div>', unsafe_allow_html=True)
    if st.button("🔄 Refresh Now", key="manual_refresh"):
        st.rerun()

# ═══════════════════════════════════════════════════════════════
#  MAIN AREA — TABS
# ═══════════════════════════════════════════════════════════════
tab_edit, tab_view, tab_chat, tab_ai, tab_stats, tab_media, tab_version = st.tabs([
    "✏️ Edit", "📄 View", "💬 Chat", "🤖 AI Suggestions",
    "📊 Stats", "🖼️ Media", "🕓 Version History"
])

# ── TAB 1: EDIT ───────────────────────────────────────────────
with tab_edit:
    st.markdown("### ✏️ Edit Document")
    current = st.session_state.current_user

    if not current:
        st.info("Please login from the sidebar to edit.")
    elif not is_editor(state):
        st.warning("🚫 You are a **Viewer**. Only Editors can edit the document.")
    else:
        locked_by = state["locked_by"]

        if locked_by is None:
            st.markdown('<div class="unlock-banner">🔓 Document is unlocked. Lock it to start editing.</div>', unsafe_allow_html=True)
            if st.button("🔒 Lock Document"):
                state["locked_by"] = current
                save_state(state)
                st.rerun()

        elif locked_by == current:
            st.markdown('<div class="unlock-banner">🔒 You hold the lock. You can edit now.</div>', unsafe_allow_html=True)
            if st.button("🔓 Unlock Document"):
                state["locked_by"] = None
                save_state(state)
                st.rerun()
        else:
            st.markdown(f'<div class="lock-banner">🔒 Document is locked by <b>{locked_by}</b>. Cannot edit.</div>', unsafe_allow_html=True)

        if state["locked_by"] == current:
            st.divider()

            # ── Text Entry ────────────────────────────────────
            with st.form("edit_form", clear_on_submit=True):
                text = st.text_area("Text to append", placeholder="Type your content here...", height=100)
                fmt  = st.radio("Formatting", ["Normal", "Bold", "Italic"], horizontal=True)
                if st.form_submit_button("➕ Append Text"):
                    if not text.strip():
                        st.error("Text cannot be empty.")
                    else:
                        state["document"].append({
                            "type": "text",
                            "user": current,
                            "text": text.strip(),
                            "fmt":  fmt,
                            "time": datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
                        })
                        save_state(state)
                        st.success("Text appended.")
                        st.rerun()

            st.divider()

            # ── Code Block Entry ──────────────────────────────
            st.markdown("**💻 Insert Executable Code Block**")
            with st.form("code_form", clear_on_submit=True):
                code = st.text_area("Python code", placeholder="print('Hello World')", height=120)
                if st.form_submit_button("➕ Add Code Block"):
                    if not code.strip():
                        st.error("Code cannot be empty.")
                    else:
                        state["document"].append({
                            "type": "code",
                            "user": current,
                            "text": code.strip(),
                            "fmt":  "code",
                            "time": datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
                        })
                        save_state(state)
                        st.success("Code block added.")
                        st.rerun()

            st.divider()

            # ── Save Version ──────────────────────────────────
            st.markdown("**🕓 Save Version Snapshot**")
            with st.form("version_form", clear_on_submit=True):
                version_label = st.text_input("Version label", placeholder="e.g. Draft v1")
                if st.form_submit_button("💾 Save Version"):
                    label = version_label.strip() or f"Version {len(state['versions']) + 1}"
                    state["versions"].append({
                        "label":    label,
                        "time":     datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                        "saved_by": current,
                        "snapshot": copy.deepcopy(state["document"])
                    })
                    save_state(state)
                    st.success(f"Version '{label}' saved.")
                    st.rerun()

# ── TAB 2: VIEW ───────────────────────────────────────────────
with tab_view:
    st.markdown("### 📄 Document")
    if not state["document"]:
        st.markdown('<div style="color:#8892b0;text-align:center;padding:40px;">Document is empty.</div>', unsafe_allow_html=True)
    else:
        for i, entry in enumerate(state["document"]):
            etype = entry.get("type", "text")
            user  = entry["user"]
            time  = entry["time"]

            if etype == "code":
                st.markdown(
                    f'<div class="code-entry">'
                    f'<span style="color:#f97316;font-weight:600;">💻 [{user}]</span> '
                    f'<span style="color:#8892b0;font-size:0.78rem;">({time})</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                st.code(entry["text"], language="python")
                if st.button(f"▶ Run", key=f"run_{i}"):
                    out, err = run_code(entry["text"])
                    if out:
                        st.success(f"Output:\n{out}")
                    if err:
                        st.error(f"Error:\n{err}")
                    if not out and not err:
                        st.info("Code ran with no output.")
            else:
                text    = entry["text"]
                fmt     = entry.get("fmt", "Normal")
                display = f"<b>{text}</b>" if fmt == "Bold" else (f"<i>{text}</i>" if fmt == "Italic" else text)
                st.markdown(
                    f'<div class="doc-entry">'
                    f'<span style="color:#64ffda;font-weight:600;">[{user}]</span> '
                    f'<span style="color:#8892b0;font-size:0.78rem;">({time})</span><br>'
                    f'<span style="color:#ccd6f6;">{display}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

# ── TAB 3: CHAT ───────────────────────────────────────────────
with tab_chat:
    st.markdown("### 💬 Chat")
    current = st.session_state.current_user

    if not current:
        st.info("Login to send messages.")
    else:
        with st.form("chat_form", clear_on_submit=True):
            msg = st.text_input("Message", placeholder="Type a message...")
            if st.form_submit_button("Send 📨"):
                if not msg.strip():
                    st.error("Message cannot be empty.")
                else:
                    state["chat"].append({
                        "user":    current,
                        "message": msg.strip(),
                        "time":    datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
                    })
                    save_state(state)
                    st.rerun()

    st.divider()
    if not state["chat"]:
        st.markdown('<div style="color:#8892b0;text-align:center;">No messages yet.</div>', unsafe_allow_html=True)
    else:
        for msg in reversed(state["chat"]):
            st.markdown(
                f'<div class="chat-bubble">'
                f'<span class="chat-user">{msg["user"]}</span>'
                f'<span class="chat-time">{msg["time"]}</span><br>'
                f'<span>{msg["message"]}</span>'
                f'</div>',
                unsafe_allow_html=True
            )

# ── TAB 4: AI SUGGESTIONS ─────────────────────────────────────
with tab_ai:
    st.markdown("### 🤖 AI Suggestions")
    st.markdown('<div class="sub-title">Rule-based analysis — no external API</div>', unsafe_allow_html=True)
    st.divider()
    if st.button("🔍 Analyze Document"):
        for s in get_ai_suggestions(state):
            icon = "✅" if "looks good" in s else "💡"
            st.markdown(f'<div class="suggestion">{icon} {s}</div>', unsafe_allow_html=True)

# ── TAB 5: STATS ──────────────────────────────────────────────
with tab_stats:
    st.markdown("### 📊 Document Stats")
    st.divider()

    content  = doc_text(state)
    wc       = word_count(content)
    cc       = char_count(content)
    entries  = len(state["document"])
    editors  = sum(1 for u in state["users"].values() if u["role"] == "Editor")
    viewers  = sum(1 for u in state["users"].values() if u["role"] == "Viewer")
    messages = len(state["chat"])
    versions = len(state["versions"])
    media    = len(state["media"])

    c1, c2, c3 = st.columns(3)
    for col, label, value in zip([c1, c2, c3], ["Words", "Characters", "Doc Entries"], [wc, cc, entries]):
        col.markdown(
            f'<div class="stat-box"><div class="stat-number">{value}</div>'
            f'<div class="stat-label">{label}</div></div>',
            unsafe_allow_html=True
        )

    st.divider()
    c4, c5, c6 = st.columns(3)
    for col, label, value in zip([c4, c5, c6], ["Editors", "Viewers", "Chat Messages"], [editors, viewers, messages]):
        col.markdown(
            f'<div class="stat-box"><div class="stat-number">{value}</div>'
            f'<div class="stat-label">{label}</div></div>',
            unsafe_allow_html=True
        )

    st.divider()
    c7, c8 = st.columns(2)
    for col, label, value in zip([c7, c8], ["Saved Versions", "Media Files"], [versions, media]):
        col.markdown(
            f'<div class="stat-box"><div class="stat-number">{value}</div>'
            f'<div class="stat-label">{label}</div></div>',
            unsafe_allow_html=True
        )

    st.divider()
    if state["locked_by"]:
        st.markdown(f'<div class="lock-banner">🔒 Document currently locked by <b>{state["locked_by"]}</b></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="unlock-banner">🔓 Document is currently unlocked</div>', unsafe_allow_html=True)

# ── TAB 6: MEDIA ──────────────────────────────────────────────
with tab_media:
    st.markdown("### 🖼️ Multimedia")
    current = st.session_state.current_user

    if not current:
        st.info("Login to upload media.")
    elif not is_editor(state):
        st.warning("🚫 Only Editors can upload media.")
    else:
        uploaded = st.file_uploader(
            "Upload image or video",
            type=["png", "jpg", "jpeg", "gif", "mp4", "webm"],
            key="media_upload"
        )
        if uploaded and st.button("📤 Add to Document"):
            data_b64 = base64.b64encode(uploaded.read()).decode("utf-8")
            state["media"].append({
                "user":     current,
                "filename": uploaded.name,
                "data_b64": data_b64,
                "mime":     uploaded.type,
                "time":     datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
            })
            save_state(state)
            st.success(f"'{uploaded.name}' uploaded.")
            st.rerun()

    st.divider()
    if not state["media"]:
        st.markdown('<div style="color:#8892b0;text-align:center;">No media uploaded yet.</div>', unsafe_allow_html=True)
    else:
        for item in state["media"]:
            st.markdown(
                f'<span style="color:#64ffda;font-weight:600;">[{item["user"]}]</span> '
                f'<span style="color:#8892b0;font-size:0.8rem;">{item["filename"]} — {item["time"]}</span>',
                unsafe_allow_html=True
            )
            mime = item["mime"]
            data = base64.b64decode(item["data_b64"])
            if mime.startswith("image"):
                st.image(data, caption=item["filename"], use_container_width=True)
            elif mime.startswith("video"):
                st.video(data)
            st.divider()

# ── TAB 7: VERSION HISTORY ────────────────────────────────────
with tab_version:
    st.markdown("### 🕓 Version History")

    if not state["versions"]:
        st.markdown('<div style="color:#8892b0;text-align:center;padding:30px;">No versions saved yet.</div>', unsafe_allow_html=True)
    else:
        for i, ver in enumerate(reversed(state["versions"])):
            idx = len(state["versions"]) - 1 - i
            with st.container():
                st.markdown(
                    f'<div class="version-card">'
                    f'<span style="color:#64ffda;font-weight:600;">📌 {ver["label"]}</span><br>'
                    f'<span style="color:#8892b0;font-size:0.8rem;">Saved by {ver["saved_by"]} at {ver["time"]}</span><br>'
                    f'<span style="color:#ccd6f6;font-size:0.85rem;">{len(ver["snapshot"])} entries in this snapshot</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

                col_preview, col_restore = st.columns([3, 1])

                with col_preview:
                    with st.expander(f"👁 Preview — {ver['label']}"):
                        if not ver["snapshot"]:
                            st.write("Empty snapshot.")
                        for entry in ver["snapshot"]:
                            etype = entry.get("type", "text")
                            if etype == "code":
                                st.code(entry["text"], language="python")
                            else:
                                fmt = entry.get("fmt", "Normal")
                                txt = f"**{entry['text']}**" if fmt == "Bold" else (f"*{entry['text']}*" if fmt == "Italic" else entry["text"])
                                st.markdown(f"**[{entry['user']}]** ({entry['time']}): {txt}")

                with col_restore:
                    if is_editor(state):
                        if st.button(f"♻️ Restore", key=f"restore_{idx}"):
                            state["document"] = copy.deepcopy(ver["snapshot"])
                            save_state(state)
                            st.success(f"Restored to '{ver['label']}'.")
                            st.rerun()
