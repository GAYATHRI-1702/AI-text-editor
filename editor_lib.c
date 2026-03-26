/*
 * editor_lib.c — All logic as a shared library (.dll / .so)
 * Python calls these functions via ctypes
 */

#include <stdio.h>
#include <string.h>
#include <ctype.h>
#include <stdlib.h>

#ifdef _WIN32
#define EXPORT __declspec(dllexport)
#else
#define EXPORT __attribute__((visibility("default")))
#endif

/* ─── Constants ─────────────────────────────────────────────── */
#define MAX_DOC      8000
#define MAX_NAME       50
#define MAX_USERS      20
#define MAX_CHAT      100
#define MAX_MSG_LEN   500
#define MAX_VERSIONS   20
#define MAX_MEDIA      20
#define MAX_DOC_ENTRIES 200
#define MAX_SUGGESTIONS 10
#define MAX_SUGG_LEN   200

/* ─── Structs ────────────────────────────────────────────────── */
typedef struct {
    char name[MAX_NAME];
    int  role;           /* 1=Editor, 0=Viewer */
    char registered_at[30];
} User;

typedef struct {
    char type[10];       /* "text" or "code" */
    char user[MAX_NAME];
    char text[MAX_MSG_LEN];
    char fmt[10];        /* "Normal","Bold","Italic","code" */
    char time[30];
} DocEntry;

typedef struct {
    char user[MAX_NAME];
    char message[MAX_MSG_LEN];
    char time[30];
} ChatMsg;

typedef struct {
    char label[100];
    char time[30];
    char saved_by[MAX_NAME];
    DocEntry snapshot[MAX_DOC_ENTRIES];
    int  count;
} Version;

typedef struct {
    char user[MAX_NAME];
    char filename[200];
    char mime[50];
    char time[30];
    char data_b64[1024 * 512];  /* up to ~384KB base64 */
} MediaItem;

/* ─── Global State ───────────────────────────────────────────── */
static User       users[MAX_USERS];
static int        user_count   = 0;

static DocEntry   doc[MAX_DOC_ENTRIES];
static int        doc_count    = 0;
static char       locked_by[MAX_NAME] = "";

static ChatMsg    chat[MAX_CHAT];
static int        chat_count   = 0;

static Version    versions[MAX_VERSIONS];
static int        version_count = 0;

static MediaItem  media[MAX_MEDIA];
static int        media_count  = 0;

/* ─── Result buffer (returned to Python as const char*) ─────── */
static char _result[MAX_DOC * 2];

/* ═══════════════════════════════════════════════════════════════
 *  USER MANAGEMENT
 * ═══════════════════════════════════════════════════════════════ */
EXPORT int register_user(const char *name, int role, const char *timestamp) {
    if (user_count >= MAX_USERS) return -1;          /* limit reached */
    for (int i = 0; i < user_count; i++)
        if (strcmp(users[i].name, name) == 0) return -2; /* already exists */
    strncpy(users[user_count].name, name, MAX_NAME - 1);
    users[user_count].role = role;
    strncpy(users[user_count].registered_at, timestamp, 29);
    user_count++;
    return 0; /* success */
}

EXPORT int login_user(const char *name) {
    for (int i = 0; i < user_count; i++)
        if (strcmp(users[i].name, name) == 0) return i;
    return -1; /* not found */
}

EXPORT int get_user_role(int idx) {
    if (idx < 0 || idx >= user_count) return -1;
    return users[idx].role;
}

EXPORT const char *get_user_name(int idx) {
    if (idx < 0 || idx >= user_count) return "";
    return users[idx].name;
}

EXPORT int get_user_count(void) { return user_count; }

EXPORT const char *get_user_info(int idx) {
    if (idx < 0 || idx >= user_count) return "";
    snprintf(_result, sizeof(_result), "%s|%d|%s",
             users[idx].name, users[idx].role, users[idx].registered_at);
    return _result;
}

/* ═══════════════════════════════════════════════════════════════
 *  LOCK / UNLOCK
 * ═══════════════════════════════════════════════════════════════ */
EXPORT int lock_document(const char *username, int role) {
    if (role != 1) return -1;               /* not editor */
    if (strlen(locked_by) > 0) return -2;   /* already locked */
    strncpy(locked_by, username, MAX_NAME - 1);
    return 0;
}

EXPORT int unlock_document(const char *username) {
    if (strlen(locked_by) == 0) return -1;              /* not locked */
    if (strcmp(locked_by, username) != 0) return -2;    /* not owner */
    locked_by[0] = '\0';
    return 0;
}

EXPORT const char *get_locked_by(void) { return locked_by; }

/* ═══════════════════════════════════════════════════════════════
 *  DOCUMENT EDIT
 * ═══════════════════════════════════════════════════════════════ */
EXPORT int append_text(const char *username, int role,
                       const char *text, const char *fmt,
                       const char *timestamp) {
    if (role != 1) return -1;
    if (strlen(locked_by) == 0) return -2;
    if (strcmp(locked_by, username) != 0) return -3;
    if (doc_count >= MAX_DOC_ENTRIES) return -4;

    strncpy(doc[doc_count].type, "text", 9);
    strncpy(doc[doc_count].user, username, MAX_NAME - 1);
    strncpy(doc[doc_count].text, text, MAX_MSG_LEN - 1);
    strncpy(doc[doc_count].fmt,  fmt,  9);
    strncpy(doc[doc_count].time, timestamp, 29);
    doc_count++;
    return 0;
}

EXPORT int append_code(const char *username, int role,
                       const char *code, const char *timestamp) {
    if (role != 1) return -1;
    if (strlen(locked_by) == 0) return -2;
    if (strcmp(locked_by, username) != 0) return -3;
    if (doc_count >= MAX_DOC_ENTRIES) return -4;

    strncpy(doc[doc_count].type, "code", 9);
    strncpy(doc[doc_count].user, username, MAX_NAME - 1);
    strncpy(doc[doc_count].text, code, MAX_MSG_LEN - 1);
    strncpy(doc[doc_count].fmt,  "code", 9);
    strncpy(doc[doc_count].time, timestamp, 29);
    doc_count++;
    return 0;
}

EXPORT int get_doc_count(void) { return doc_count; }

EXPORT const char *get_doc_entry(int idx) {
    if (idx < 0 || idx >= doc_count) return "";
    snprintf(_result, sizeof(_result), "%s|%s|%s|%s|%s",
             doc[idx].type, doc[idx].user,
             doc[idx].text, doc[idx].fmt, doc[idx].time);
    return _result;
}

/* ═══════════════════════════════════════════════════════════════
 *  CHAT
 * ═══════════════════════════════════════════════════════════════ */
EXPORT int send_message(const char *username, const char *message,
                        const char *timestamp) {
    if (chat_count >= MAX_CHAT) return -1;
    strncpy(chat[chat_count].user,    username,  MAX_NAME - 1);
    strncpy(chat[chat_count].message, message,   MAX_MSG_LEN - 1);
    strncpy(chat[chat_count].time,    timestamp, 29);
    chat_count++;
    return 0;
}

EXPORT int get_chat_count(void) { return chat_count; }

EXPORT const char *get_chat_entry(int idx) {
    if (idx < 0 || idx >= chat_count) return "";
    snprintf(_result, sizeof(_result), "%s|%s|%s",
             chat[idx].user, chat[idx].message, chat[idx].time);
    return _result;
}

/* ═══════════════════════════════════════════════════════════════
 *  STATS
 * ═══════════════════════════════════════════════════════════════ */
EXPORT int get_word_count(void) {
    int count = 0, in_word = 0;
    for (int i = 0; i < doc_count; i++) {
        if (strcmp(doc[i].type, "code") == 0) continue;
        const char *p = doc[i].text;
        while (*p) {
            if (!isspace((unsigned char)*p)) {
                if (!in_word) { count++; in_word = 1; }
            } else { in_word = 0; }
            p++;
        }
    }
    return count;
}

EXPORT int get_char_count(void) {
    int count = 0;
    for (int i = 0; i < doc_count; i++) {
        if (strcmp(doc[i].type, "code") == 0) continue;
        count += (int)strlen(doc[i].text);
    }
    return count;
}

EXPORT int get_version_count(void)  { return version_count; }
EXPORT int get_media_count(void)    { return media_count; }
EXPORT int get_editor_count(void) {
    int c = 0;
    for (int i = 0; i < user_count; i++) if (users[i].role == 1) c++;
    return c;
}
EXPORT int get_viewer_count(void) {
    int c = 0;
    for (int i = 0; i < user_count; i++) if (users[i].role == 0) c++;
    return c;
}

/* ═══════════════════════════════════════════════════════════════
 *  AI SUGGESTIONS
 * ═══════════════════════════════════════════════════════════════ */
static char suggestions[MAX_SUGGESTIONS][MAX_SUGG_LEN];
static int  suggestion_count = 0;

EXPORT int analyze_document(void) {
    suggestion_count = 0;

    /* Build full text */
    char full[MAX_DOC] = "";
    for (int i = 0; i < doc_count; i++) {
        if (strcmp(doc[i].type, "code") == 0) continue;
        strncat(full, doc[i].text, MAX_DOC - strlen(full) - 1);
        strncat(full, " ",         MAX_DOC - strlen(full) - 1);
    }

    int len = (int)strlen(full);

    if (len == 0) {
        strncpy(suggestions[suggestion_count++],
                "Document is empty. Start with an introduction.", MAX_SUGG_LEN - 1);
        return suggestion_count;
    }

    /* 1. No introduction */
    if (!strstr(full, "introduction") && !strstr(full, "Introduction"))
        strncpy(suggestions[suggestion_count++],
                "Consider adding an Introduction section.", MAX_SUGG_LEN - 1);

    /* 2. No conclusion */
    if (!strstr(full, "conclusion") && !strstr(full, "Conclusion"))
        strncpy(suggestions[suggestion_count++],
                "Consider adding a Conclusion section.", MAX_SUGG_LEN - 1);

    /* 3. Short document */
    if (get_word_count() < 20) {
        char buf[MAX_SUGG_LEN];
        snprintf(buf, sizeof(buf),
                 "Document is short (%d words). Add more details.", get_word_count());
        strncpy(suggestions[suggestion_count++], buf, MAX_SUGG_LEN - 1);
    }

    /* 4. Starts with lowercase */
    if (len > 0 && islower((unsigned char)full[0]))
        strncpy(suggestions[suggestion_count++],
                "Start the document with a capital letter.", MAX_SUGG_LEN - 1);

    /* 5. Missing end punctuation */
    char last = '\0';
    for (int i = len - 1; i >= 0; i--) {
        if (!isspace((unsigned char)full[i])) { last = full[i]; break; }
    }
    if (last && last != '.' && last != '!' && last != '?')
        strncpy(suggestions[suggestion_count++],
                "Last sentence may be missing end punctuation.", MAX_SUGG_LEN - 1);

    /* 6. Repeated consecutive words */
    char tmp[MAX_DOC];
    strncpy(tmp, full, MAX_DOC - 1);
    tmp[MAX_DOC - 1] = '\0';
    char *prev = NULL, *word = strtok(tmp, " \n\t");
    while (word && suggestion_count < MAX_SUGGESTIONS) {
        if (prev && strcasecmp(prev, word) == 0) {
            char buf[MAX_SUGG_LEN];
            snprintf(buf, sizeof(buf), "Repeated word detected: \"%s\".", word);
            strncpy(suggestions[suggestion_count++], buf, MAX_SUGG_LEN - 1);
            break;
        }
        prev = word;
        word = strtok(NULL, " \n\t");
    }

    if (suggestion_count == 0)
        strncpy(suggestions[suggestion_count++],
                "Document looks good! No suggestions.", MAX_SUGG_LEN - 1);

    return suggestion_count;
}

EXPORT const char *get_suggestion(int idx) {
    if (idx < 0 || idx >= suggestion_count) return "";
    return suggestions[idx];
}

/* ═══════════════════════════════════════════════════════════════
 *  VERSION HISTORY
 * ═══════════════════════════════════════════════════════════════ */
EXPORT int save_version(const char *label, const char *username,
                        const char *timestamp) {
    if (version_count >= MAX_VERSIONS) return -1;
    strncpy(versions[version_count].label,    label,    99);
    strncpy(versions[version_count].saved_by, username, MAX_NAME - 1);
    strncpy(versions[version_count].time,     timestamp, 29);
    versions[version_count].count = doc_count;
    for (int i = 0; i < doc_count; i++)
        versions[version_count].snapshot[i] = doc[i];
    version_count++;
    return 0;
}

EXPORT const char *get_version_info(int idx) {
    if (idx < 0 || idx >= version_count) return "";
    snprintf(_result, sizeof(_result), "%s|%s|%s|%d",
             versions[idx].label, versions[idx].saved_by,
             versions[idx].time,  versions[idx].count);
    return _result;
}

EXPORT int restore_version(int idx, int role) {
    if (role != 1) return -1;
    if (idx < 0 || idx >= version_count) return -2;
    doc_count = versions[idx].count;
    for (int i = 0; i < doc_count; i++)
        doc[i] = versions[idx].snapshot[i];
    return 0;
}

EXPORT const char *get_version_entry(int ver_idx, int entry_idx) {
    if (ver_idx < 0 || ver_idx >= version_count) return "";
    if (entry_idx < 0 || entry_idx >= versions[ver_idx].count) return "";
    DocEntry *e = &versions[ver_idx].snapshot[entry_idx];
    snprintf(_result, sizeof(_result), "%s|%s|%s|%s|%s",
             e->type, e->user, e->text, e->fmt, e->time);
    return _result;
}

/* ═══════════════════════════════════════════════════════════════
 *  MEDIA
 * ═══════════════════════════════════════════════════════════════ */
EXPORT int add_media(const char *username, const char *filename,
                     const char *mime, const char *data_b64,
                     const char *timestamp) {
    if (media_count >= MAX_MEDIA) return -1;
    strncpy(media[media_count].user,     username,  MAX_NAME - 1);
    strncpy(media[media_count].filename, filename,  199);
    strncpy(media[media_count].mime,     mime,      49);
    strncpy(media[media_count].time,     timestamp, 29);
    strncpy(media[media_count].data_b64, data_b64,
            sizeof(media[media_count].data_b64) - 1);
    media_count++;
    return 0;
}

EXPORT const char *get_media_info(int idx) {
    if (idx < 0 || idx >= media_count) return "";
    snprintf(_result, sizeof(_result), "%s|%s|%s|%s",
             media[idx].user, media[idx].filename,
             media[idx].mime, media[idx].time);
    return _result;
}

EXPORT const char *get_media_data(int idx) {
    if (idx < 0 || idx >= media_count) return "";
    return media[idx].data_b64;
}

/* ═══════════════════════════════════════════════════════════════
 *  RESET (for testing mode)
 * ═══════════════════════════════════════════════════════════════ */
EXPORT void reset_all(void) {
    user_count    = 0;
    doc_count     = 0;
    chat_count    = 0;
    version_count = 0;
    media_count   = 0;
    locked_by[0]  = '\0';
    suggestion_count = 0;
}
