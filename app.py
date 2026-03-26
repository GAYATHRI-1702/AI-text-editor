import streamlit as st
import ctypes
import os
import base64
from datetime import datetime, timezone

# ─── Page Config ─────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Collaborative Editor",
    page_icon="📝",
    layout="wide"
)

# ─── Load C Shared Library ────────────────────────────────────────
_lib_path = os.path.join(os.path.dirname(__file__), "editor_lib.dll")
lib = ctypes.CDLL(_lib_path)

# ── Define return types for functions returning strings ───────────
for fn in ["get_user_name", "get_user_info", "get_locked_by",
           "get_doc_entry", "get_chat_entry", "get_suggestion",
           "get_version_info", "get_version_entry",
           "get_media_info", "get_media_data"]:
    getattr(lib, fn).restype = ctypes.c_char_p

# ─── Helper: timestamp ───────────────────────────────────────────
def ts():
    return datetime.now(timezone.utc).strftime("%H:%M:%S UTC").encode()

def ts_full():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC").encode()

# ─── Per-session: current logged-in user (index + name + role) ───
if "current_user_idx"  not in st.session_state:
    st.session_state.current_user_idx  = -1
if "current_user_name" not in st.session_state:
    st.session_state.current_user_name = ""
if "current_user_role" not in st.session_state:
    st.session_state.current_user_role = -1

def cu_idx():  return st.session_state.current_user_idx
def cu_name(): return st.session_state.current_user_name
def cu_role(): return st.session_state.current_user_role
def logged_in(): return cu_idx() != -1
def is_editor(): return cu_role() == 1

# ─── Load CSS ─────────────────────────────────────────────────────
_css_path = os.path.join(os.path.dirname(__file__), "style.css")
with open(_css_path) as _f:
    st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)

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
            else:
                role_int = 1 if reg_role == "Editor" else 0
                result = lib.register_user(name.encode(), role_int, ts())
                if result == 0:
                    st.success(f"'{name}' registered as {reg_role}.")
                    st.rerun()
                elif result == -1:
                    st.error("User limit reached.")
                elif result == -2:
                    st.warning(f"'{name}' already exists.")

    # ── Login ─────────────────────────────────────────────────
    with st.expander("🔑 Login", expanded=True):
        if logged_in():
            badge = "badge-editor" if is_editor() else "badge-viewer"
            role_label = "Editor" if is_editor() else "Viewer"
            st.markdown(f"Logged in as **{cu_name()}**")
            st.markdown(f'<span class="{badge}">{role_label}</span>', unsafe_allow_html=True)
            if st.button("Logout", key="btn_logout"):
                st.session_state.current_user_idx  = -1
                st.session_state.current_user_name = ""
                st.session_state.current_user_role = -1
                st.rerun()
        else:
            # Build user list from C
            user_list = []
            for i in range(lib.get_user_count()):
                info = lib.get_user_info(i).decode()
                parts = info.split("|")
                user_list.append(parts[0])

            login_name = st.selectbox("Select user",
                                      ["-- select --"] + user_list,
                                      key="login_select")
            if st.button("Login", key="btn_login"):
                if login_name == "-- select --":
                    st.error("Select a user.")
                else:
                    idx = lib.login_user(login_name.encode())
                    if idx >= 0:
                        st.session_state.current_user_idx  = idx
                        st.session_state.current_user_name = login_name
                        st.session_state.current_user_role = lib.get_user_role(idx)
                        st.rerun()
                    else:
                        st.error("User not found.")

    st.divider()

    # ── Status Bar ────────────────────────────────────────────
    st.markdown("**📊 Status Bar**")
    col1, col2 = st.columns(2)
    col1.metric("Words", lib.get_word_count())
    col2.metric("Chars", lib.get_char_count())

    locked_by = lib.get_locked_by().decode()
    if locked_by:
        st.markdown(f'<span class="badge-locked">🔒 Locked by {locked_by}</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge-free">🔓 Unlocked</span>', unsafe_allow_html=True)

    st.divider()

    # ── Registered Users ──────────────────────────────────────
    count = lib.get_user_count()
    if count > 0:
        st.markdown("**👥 Registered Users**")
        for i in range(count):
            info  = lib.get_user_info(i).decode().split("|")
            uname = info[0]
            urole = "Editor" if info[1] == "1" else "Viewer"
            badge = "badge-editor" if info[1] == "1" else "badge-viewer"
            indicator = "🟢" if uname == cu_name() else "⚪"
            st.markdown(
                f'{indicator} **{uname}** <span class="{badge}">{urole}</span>',
                unsafe_allow_html=True
            )

    st.divider()
    st.markdown('<div class="sub-title">🔄 Click Refresh to see updates</div>', unsafe_allow_html=True)
    if st.button("🔄 Refresh Now", key="manual_refresh"):
        st.rerun()

# ═══════════════════════════════════════════════════════════════
#  MAIN TABS
# ═══════════════════════════════════════════════════════════════
tab_edit, tab_view, tab_chat, tab_ai, tab_stats, tab_media, tab_version = st.tabs([
    "✏️ Edit", "📄 View", "💬 Chat", "🤖 AI Suggestions",
    "📊 Stats", "🖼️ Media", "🕓 Version History"
])

# ── TAB 1: EDIT ───────────────────────────────────────────────
with tab_edit:
    st.markdown("### ✏️ Edit Document")

    if not logged_in():
        st.info("Please login from the sidebar.")
    elif not is_editor():
        st.warning("🚫 You are a **Viewer**. Only Editors can edit.")
    else:
        locked_by = lib.get_locked_by().decode()

        if not locked_by:
            st.markdown('<div class="unlock-banner">🔓 Document is unlocked. Lock it to start editing.</div>', unsafe_allow_html=True)
            if st.button("🔒 Lock Document"):
                lib.lock_document(cu_name().encode(), cu_role())
                st.rerun()
        elif locked_by == cu_name():
            st.markdown('<div class="unlock-banner">🔒 You hold the lock. You can edit now.</div>', unsafe_allow_html=True)
            if st.button("🔓 Unlock Document"):
                lib.unlock_document(cu_name().encode())
                st.rerun()
        else:
            st.markdown(f'<div class="lock-banner">🔒 Locked by <b>{locked_by}</b>. Cannot edit.</div>', unsafe_allow_html=True)

        if lib.get_locked_by().decode() == cu_name():
            st.divider()

            # Text entry
            with st.form("edit_form", clear_on_submit=True):
                text = st.text_area("Text to append", placeholder="Type your content here...", height=100)
                fmt  = st.radio("Formatting", ["Normal", "Bold", "Italic"], horizontal=True)
                if st.form_submit_button("➕ Append Text"):
                    if not text.strip():
                        st.error("Text cannot be empty.")
                    else:
                        r = lib.append_text(cu_name().encode(), cu_role(),
                                            text.strip().encode(),
                                            fmt.encode(), ts())
                        if r == 0:
                            st.success("Text appended.")
                            st.rerun()
                        else:
                            st.error(f"Error appending text (code {r}).")

            st.divider()

            # Code block entry
            st.markdown("**💻 Insert Executable Code Block**")
            with st.form("code_form", clear_on_submit=True):
                code = st.text_area("Python code", placeholder="print('Hello World')", height=120)
                if st.form_submit_button("➕ Add Code Block"):
                    if not code.strip():
                        st.error("Code cannot be empty.")
                    else:
                        r = lib.append_code(cu_name().encode(), cu_role(),
                                            code.strip().encode(), ts())
                        if r == 0:
                            st.success("Code block added.")
                            st.rerun()
                        else:
                            st.error(f"Error adding code (code {r}).")

            st.divider()

            # Save version
            st.markdown("**🕓 Save Version Snapshot**")
            with st.form("version_form", clear_on_submit=True):
                version_label = st.text_input("Version label", placeholder="e.g. Draft v1")
                if st.form_submit_button("💾 Save Version"):
                    vc = lib.get_version_count()
                    label = version_label.strip() or f"Version {vc + 1}"
                    r = lib.save_version(label.encode(),
                                         cu_name().encode(), ts_full())
                    if r == 0:
                        st.success(f"Version '{label}' saved.")
                        st.rerun()
                    else:
                        st.error("Version limit reached.")

# ── TAB 2: VIEW ───────────────────────────────────────────────
with tab_view:
    st.markdown("### 📄 Document")
    dc = lib.get_doc_count()
    if dc == 0:
        st.markdown('<div style="color:#a0aec0;text-align:center;padding:40px;">Document is empty.</div>', unsafe_allow_html=True)
    else:
        for i in range(dc):
            entry = lib.get_doc_entry(i).decode().split("|", 4)
            etype, user, text, fmt, time = entry[0], entry[1], entry[2], entry[3], entry[4]

            if etype == "code":
                st.markdown(
                    f'<div class="code-entry">'
                    f'<span style="color:#10b981;font-weight:600;">💻 [{user}]</span> '
                    f'<span style="color:#a0aec0;font-size:0.78rem;">({time})</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                st.code(text, language="python")
                # Code execution handled in Python (UI only — logic was stored in C)
                if st.button(f"▶ Run", key=f"run_{i}"):
                    import io, sys, builtins
                    _SAFE = {n: getattr(builtins, n) for n in
                             ["print","range","len","int","float","str","bool",
                              "list","dict","tuple","set","sum","min","max",
                              "abs","round","sorted","enumerate","zip","map",
                              "filter","isinstance","type","repr","reversed"]}
                    forbidden = ["import","open","exec","eval","__","os.","sys.","subprocess"]
                    blocked = next((w for w in forbidden if w in text), None)
                    if blocked:
                        st.error(f"Blocked: '{blocked}' is not allowed.")
                    else:
                        buf = io.StringIO()
                        sys.stdout = buf
                        try:
                            eval(compile(text, "<sandbox>", "exec"),
                                 {"__builtins__": _SAFE})
                            sys.stdout = sys.__stdout__
                            out = buf.getvalue()
                            st.success(f"Output:\n{out}" if out else "Ran with no output.")
                        except Exception as e:
                            sys.stdout = sys.__stdout__
                            st.error(f"Error: {e}")
            else:
                display = f"<b>{text}</b>" if fmt == "Bold" else (f"<i>{text}</i>" if fmt == "Italic" else text)
                st.markdown(
                    f'<div class="doc-entry">'
                    f'<span style="color:#7c3aed;font-weight:600;">[{user}]</span> '
                    f'<span style="color:#a0aec0;font-size:0.78rem;">({time})</span><br>'
                    f'<span style="color:#e2e8f0;">{display}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

# ── TAB 3: CHAT ───────────────────────────────────────────────
with tab_chat:
    st.markdown("### 💬 Chat")

    if not logged_in():
        st.info("Login to send messages.")
    else:
        with st.form("chat_form", clear_on_submit=True):
            msg = st.text_input("Message", placeholder="Type a message...")
            if st.form_submit_button("Send 📨"):
                if not msg.strip():
                    st.error("Message cannot be empty.")
                else:
                    r = lib.send_message(cu_name().encode(),
                                         msg.strip().encode(), ts())
                    if r == 0:
                        st.rerun()
                    else:
                        st.error("Chat history full.")

    st.divider()
    cc = lib.get_chat_count()
    if cc == 0:
        st.markdown('<div style="color:#a0aec0;text-align:center;">No messages yet.</div>', unsafe_allow_html=True)
    else:
        for i in range(cc - 1, -1, -1):
            entry = lib.get_chat_entry(i).decode().split("|", 2)
            user, message, time = entry[0], entry[1], entry[2]
            st.markdown(
                f'<div class="chat-bubble">'
                f'<span class="chat-user">{user}</span>'
                f'<span class="chat-time">{time}</span><br>'
                f'<span>{message}</span>'
                f'</div>',
                unsafe_allow_html=True
            )

# ── TAB 4: AI SUGGESTIONS ─────────────────────────────────────
with tab_ai:
    st.markdown("### 🤖 AI Suggestions")
    st.markdown('<div class="sub-title">Rule-based analysis — logic runs in C</div>', unsafe_allow_html=True)
    st.divider()
    if st.button("🔍 Analyze Document"):
        count = lib.analyze_document()
        for i in range(count):
            s = lib.get_suggestion(i).decode()
            icon = "✅" if "looks good" in s else "💡"
            st.markdown(f'<div class="suggestion">{icon} {s}</div>', unsafe_allow_html=True)

# ── TAB 5: STATS ──────────────────────────────────────────────
with tab_stats:
    st.markdown("### 📊 Document Stats")
    st.divider()

    wc       = lib.get_word_count()
    cc       = lib.get_char_count()
    entries  = lib.get_doc_count()
    editors  = lib.get_editor_count()
    viewers  = lib.get_viewer_count()
    messages = lib.get_chat_count()
    versions = lib.get_version_count()
    media    = lib.get_media_count()

    c1, c2, c3 = st.columns(3)
    for col, label, value in zip([c1, c2, c3],
                                  ["Words", "Characters", "Doc Entries"],
                                  [wc, cc, entries]):
        col.markdown(
            f'<div class="stat-box"><div class="stat-number">{value}</div>'
            f'<div class="stat-label">{label}</div></div>',
            unsafe_allow_html=True
        )

    st.divider()
    c4, c5, c6 = st.columns(3)
    for col, label, value in zip([c4, c5, c6],
                                  ["Editors", "Viewers", "Chat Messages"],
                                  [editors, viewers, messages]):
        col.markdown(
            f'<div class="stat-box"><div class="stat-number">{value}</div>'
            f'<div class="stat-label">{label}</div></div>',
            unsafe_allow_html=True
        )

    st.divider()
    c7, c8 = st.columns(2)
    for col, label, value in zip([c7, c8],
                                  ["Saved Versions", "Media Files"],
                                  [versions, media]):
        col.markdown(
            f'<div class="stat-box"><div class="stat-number">{value}</div>'
            f'<div class="stat-label">{label}</div></div>',
            unsafe_allow_html=True
        )

    st.divider()
    locked_by = lib.get_locked_by().decode()
    if locked_by:
        st.markdown(f'<div class="lock-banner">🔒 Locked by <b>{locked_by}</b></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="unlock-banner">🔓 Document is currently unlocked</div>', unsafe_allow_html=True)

# ── TAB 6: MEDIA ──────────────────────────────────────────────
with tab_media:
    st.markdown("### 🖼️ Multimedia")

    if not logged_in():
        st.info("Login to upload media.")
    elif not is_editor():
        st.warning("🚫 Only Editors can upload media.")
    else:
        uploaded = st.file_uploader(
            "Upload image or video",
            type=["png", "jpg", "jpeg", "gif", "mp4", "webm"],
            key="media_upload"
        )
        if uploaded and st.button("📤 Add to Document"):
            data_b64 = base64.b64encode(uploaded.read()).decode("utf-8")
            r = lib.add_media(cu_name().encode(),
                              uploaded.name.encode(),
                              uploaded.type.encode(),
                              data_b64.encode(),
                              ts())
            if r == 0:
                st.success(f"'{uploaded.name}' uploaded.")
                st.rerun()
            else:
                st.error("Media limit reached.")

    st.divider()
    mc = lib.get_media_count()
    if mc == 0:
        st.markdown('<div style="color:#a0aec0;text-align:center;">No media uploaded yet.</div>', unsafe_allow_html=True)
    else:
        for i in range(mc):
            info  = lib.get_media_info(i).decode().split("|")
            user, filename, mime, time = info[0], info[1], info[2], info[3]
            data_b64 = lib.get_media_data(i).decode()
            st.markdown(
                f'<span style="color:#7c3aed;font-weight:600;">[{user}]</span> '
                f'<span style="color:#a0aec0;font-size:0.8rem;">{filename} — {time}</span>',
                unsafe_allow_html=True
            )
            data = base64.b64decode(data_b64)
            if mime.startswith("image"):
                st.image(data, caption=filename, use_container_width=True)
            elif mime.startswith("video"):
                st.video(data)
            st.divider()

# ── TAB 7: VERSION HISTORY ────────────────────────────────────
with tab_version:
    st.markdown("### 🕓 Version History")

    vc = lib.get_version_count()
    if vc == 0:
        st.markdown('<div style="color:#a0aec0;text-align:center;padding:30px;">No versions saved yet.</div>', unsafe_allow_html=True)
    else:
        for i in range(vc - 1, -1, -1):
            info   = lib.get_version_info(i).decode().split("|")
            label  = info[0]
            saved_by = info[1]
            time   = info[2]
            count  = int(info[3])

            st.markdown(
                f'<div class="version-card">'
                f'<span style="color:#f472b6;font-weight:600;">📌 {label}</span><br>'
                f'<span style="color:#a0aec0;font-size:0.8rem;">Saved by {saved_by} at {time}</span><br>'
                f'<span style="color:#e2e8f0;font-size:0.85rem;">{count} entries in this snapshot</span>'
                f'</div>',
                unsafe_allow_html=True
            )

            col_preview, col_restore = st.columns([3, 1])
            with col_preview:
                with st.expander(f"👁 Preview — {label}"):
                    if count == 0:
                        st.write("Empty snapshot.")
                    for j in range(count):
                        e = lib.get_version_entry(i, j).decode().split("|", 4)
                        etype, euser, etext, efmt, etime = e[0], e[1], e[2], e[3], e[4]
                        if etype == "code":
                            st.code(etext, language="python")
                        else:
                            txt = f"**{etext}**" if efmt == "Bold" else (f"*{etext}*" if efmt == "Italic" else etext)
                            st.markdown(f"**[{euser}]** ({etime}): {txt}")

            with col_restore:
                if is_editor():
                    if st.button(f"♻️ Restore", key=f"restore_{i}"):
                        r = lib.restore_version(i, cu_role())
                        if r == 0:
                            st.success(f"Restored to '{label}'.")
                            st.rerun()
