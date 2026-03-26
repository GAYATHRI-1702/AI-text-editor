/*
 * AI Collaborative Rich Text Editor
 * Combines: document.c, editor.c, user_chat.c
 * Features: Rich Text, Roles, Lock System, Chat, AI Suggestions, Stats
 */

#include <stdio.h>
#include <string.h>
#include <ctype.h>

/* ─── Constants ─────────────────────────────────────────────── */
#define MAX_DOC      4000
#define MAX_NAME       50
#define MAX_USERS       5
#define MAX_CHAT       50
#define MAX_MSG_LEN   200

/* ─── Structs ────────────────────────────────────────────────── */
typedef struct {
    char name[MAX_NAME];
    int  role;          /* 1 = Editor, 0 = Viewer */
} User;

typedef struct {
    char content[MAX_DOC];
    char locked_by[MAX_NAME];
} Document;

typedef struct {
    char username[MAX_NAME];
    char message[MAX_MSG_LEN];
} ChatMsg;

/* ─── Globals ────────────────────────────────────────────────── */
User     users[MAX_USERS];
int      user_count    = 0;
int      current_user  = -1;   /* index into users[] */

Document doc;

ChatMsg  chat[MAX_CHAT];
int      chat_count = 0;

/* ═══════════════════════════════════════════════════════════════
 *  HELPER
 * ═══════════════════════════════════════════════════════════════ */
static void clear_input(void) {
    int c;
    while ((c = getchar()) != '\n' && c != EOF);
}

/* ═══════════════════════════════════════════════════════════════
 *  USER MANAGEMENT
 * ═══════════════════════════════════════════════════════════════ */
void register_user(void) {
    if (user_count >= MAX_USERS) {
        printf("User limit (%d) reached.\n", MAX_USERS);
        return;
    }
    printf("Username: ");
    scanf("%49s", users[user_count].name);

    int role = -1;
    while (role != 0 && role != 1) {
        printf("Role (1=Editor, 0=Viewer): ");
        if (scanf("%d", &role) != 1) { clear_input(); role = -1; }
    }
    users[user_count].role = role;
    user_count++;
    printf("User '%s' registered as %s.\n",
           users[user_count - 1].name,
           role == 1 ? "Editor" : "Viewer");
}

void login(void) {
    char name[MAX_NAME];
    printf("Username: ");
    scanf("%49s", name);
    for (int i = 0; i < user_count; i++) {
        if (strcmp(users[i].name, name) == 0) {
            current_user = i;
            printf("Welcome, %s! Role: %s\n",
                   users[i].name,
                   users[i].role == 1 ? "Editor" : "Viewer");
            return;
        }
    }
    printf("User not found. Please register first.\n");
}

/* Returns 1 if logged-in user is an Editor */
static int is_editor(void) {
    return current_user != -1 && users[current_user].role == 1;
}

static const char *current_name(void) {
    return current_user == -1 ? "" : users[current_user].name;
}

/* ═══════════════════════════════════════════════════════════════
 *  LOCK / UNLOCK
 * ═══════════════════════════════════════════════════════════════ */
void lock_doc(void) {
    if (!is_editor()) { printf("Only Editors can lock the document.\n"); return; }
    if (strlen(doc.locked_by) > 0) {
        printf("Document already locked by %s.\n", doc.locked_by);
        return;
    }
    strcpy(doc.locked_by, current_name());
    printf("Document locked by %s.\n", current_name());
}

void unlock_doc(void) {
    if (strlen(doc.locked_by) == 0) { printf("Document is not locked.\n"); return; }
    if (strcmp(doc.locked_by, current_name()) != 0) {
        printf("Only %s (who locked it) can unlock.\n", doc.locked_by);
        return;
    }
    doc.locked_by[0] = '\0';
    printf("Document unlocked by %s.\n", current_name());
}

/* ═══════════════════════════════════════════════════════════════
 *  RICH TEXT EDIT
 * ═══════════════════════════════════════════════════════════════ */
void edit_document(void) {
    if (!is_editor()) { printf("Access denied: Viewers cannot edit.\n"); return; }
    if (strlen(doc.locked_by) == 0) { printf("Lock the document first.\n"); return; }
    if (strcmp(doc.locked_by, current_name()) != 0) {
        printf("Document is locked by %s.\n", doc.locked_by);
        return;
    }

    char text[MAX_MSG_LEN];
    printf("Text to append: ");
    clear_input();
    fgets(text, sizeof(text), stdin);
    /* strip trailing newline */
    text[strcspn(text, "\n")] = '\0';

    int fmt;
    printf("Format  1=Normal  2=Bold(**)  3=Italic(_): ");
    if (scanf("%d", &fmt) != 1) fmt = 1;

    /* Build entry: [Username]: <formatted text>\n */
    char entry[MAX_MSG_LEN + 80];
    if (fmt == 2)
        snprintf(entry, sizeof(entry), "[%s]: **%s**\n", current_name(), text);
    else if (fmt == 3)
        snprintf(entry, sizeof(entry), "[%s]: _%s_\n", current_name(), text);
    else
        snprintf(entry, sizeof(entry), "[%s]: %s\n", current_name(), text);

    if (strlen(doc.content) + strlen(entry) >= MAX_DOC) {
        printf("Document is full.\n");
        return;
    }
    strcat(doc.content, entry);
    printf("Text appended.\n");
}

/* ═══════════════════════════════════════════════════════════════
 *  VIEW DOCUMENT
 * ═══════════════════════════════════════════════════════════════ */
void view_document(void) {
    printf("\n========== Document ==========\n");
    if (strlen(doc.content) == 0)
        printf("(empty)\n");
    else
        printf("%s", doc.content);
    if (strlen(doc.locked_by) > 0)
        printf("[Locked by: %s]\n", doc.locked_by);
    printf("==============================\n");
}

/* ═══════════════════════════════════════════════════════════════
 *  CHAT
 * ═══════════════════════════════════════════════════════════════ */
void send_message(void) {
    if (current_user == -1) { printf("Login first.\n"); return; }
    if (chat_count >= MAX_CHAT) { printf("Chat history full.\n"); return; }

    strcpy(chat[chat_count].username, current_name());
    printf("Message: ");
    clear_input();
    fgets(chat[chat_count].message, MAX_MSG_LEN, stdin);
    chat[chat_count].message[strcspn(chat[chat_count].message, "\n")] = '\0';
    chat_count++;
    printf("Message sent.\n");
}

void view_chat(void) {
    printf("\n========== Chat History ==========\n");
    if (chat_count == 0) { printf("No messages yet.\n"); }
    for (int i = 0; i < chat_count; i++)
        printf("[%s]: %s\n", chat[i].username, chat[i].message);
    printf("==================================\n");
}

/* ═══════════════════════════════════════════════════════════════
 *  STATS (Status Bar)
 * ═══════════════════════════════════════════════════════════════ */
static int word_count(void) {
    int count = 0, in_word = 0;
    for (int i = 0; doc.content[i]; i++) {
        if (!isspace((unsigned char)doc.content[i])) {
            if (!in_word) { count++; in_word = 1; }
        } else {
            in_word = 0;
        }
    }
    return count;
}

void view_stats(void) {
    printf("\n--- Status Bar ---\n");
    printf("Characters : %d\n", (int)strlen(doc.content));
    printf("Words      : %d\n", word_count());
    printf("Lock Status: %s\n",
           strlen(doc.locked_by) ? doc.locked_by : "Unlocked");
    printf("------------------\n");
}

/* ═══════════════════════════════════════════════════════════════
 *  AI SUGGESTIONS  (rule-based, no external API)
 * ═══════════════════════════════════════════════════════════════ */
void ai_suggestions(void) {
    printf("\n--- AI Suggestions ---\n");
    int len = (int)strlen(doc.content);

    if (len == 0) {
        printf("* Document is empty. Start with an introduction.\n");
        return;
    }

    int suggested = 0;

    /* 1. No introduction keyword */
    if (!strstr(doc.content, "introduction") && !strstr(doc.content, "Introduction")) {
        printf("* Consider adding an Introduction section.\n");
        suggested++;
    }

    /* 2. No conclusion keyword */
    if (!strstr(doc.content, "conclusion") && !strstr(doc.content, "Conclusion")) {
        printf("* Consider adding a Conclusion section.\n");
        suggested++;
    }

    /* 3. Short document */
    if (word_count() < 20) {
        printf("* Document is short (%d words). Add more details.\n", word_count());
        suggested++;
    }

    /* 4. Starts with lowercase */
    if (islower((unsigned char)doc.content[0])) {
        printf("* Start the document with a capital letter.\n");
        suggested++;
    }

    /* 5. Sentence doesn't end with punctuation */
    char last = '\0';
    for (int i = len - 1; i >= 0; i--) {
        if (!isspace((unsigned char)doc.content[i])) { last = doc.content[i]; break; }
    }
    if (last && last != '.' && last != '!' && last != '?') {
        printf("* Last sentence may be missing end punctuation.\n");
        suggested++;
    }

    /* 6. Repeated consecutive words */
    char tmp[MAX_DOC];
    strncpy(tmp, doc.content, MAX_DOC - 1);
    tmp[MAX_DOC - 1] = '\0';
    char *prev = NULL, *word = strtok(tmp, " \n\t");
    while (word) {
        if (prev && strcasecmp(prev, word) == 0) {
            printf("* Repeated word detected: \"%s\".\n", word);
            suggested++;
        }
        prev = word;
        word = strtok(NULL, " \n\t");
    }

    if (!suggested) printf("* Document looks good! No suggestions.\n");
    printf("----------------------\n");
}

/* ═══════════════════════════════════════════════════════════════
 *  MAIN MENU
 * ═══════════════════════════════════════════════════════════════ */
static void print_menu(void) {
    printf("\n====== AI Collaborative Editor ======\n");
    if (current_user == -1)
        printf("  (Not logged in)\n");
    else
        printf("  User: %s  |  Role: %s\n",
               users[current_user].name,
               users[current_user].role == 1 ? "Editor" : "Viewer");
    printf("-------------------------------------\n");
    printf(" 0. Register User\n");
    printf(" 1. Login\n");
    printf(" 2. Lock Document\n");
    printf(" 3. Unlock Document\n");
    printf(" 4. Edit Document\n");
    printf(" 5. View Document\n");
    printf(" 6. Chat\n");
    printf(" 7. View Chat\n");
    printf(" 8. AI Suggestion\n");
    printf(" 9. View Stats\n");
    printf("10. Exit\n");
    printf("=====================================\n");
    printf("Choice: ");
}

int main(void) {
    /* Init */
    doc.content[0]   = '\0';
    doc.locked_by[0] = '\0';

    int choice;
    while (1) {
        print_menu();
        if (scanf("%d", &choice) != 1) { clear_input(); continue; }

        switch (choice) {
            case  0: register_user();  break;
            case  1: login();          break;
            case  2: lock_doc();       break;
            case  3: unlock_doc();     break;
            case  4: edit_document();  break;
            case  5: view_document();  break;
            case  6: send_message();   break;
            case  7: view_chat();      break;
            case  8: ai_suggestions(); break;
            case  9: view_stats();     break;
            case 10: printf("Goodbye!\n"); return 0;
            default: printf("Invalid choice.\n");
        }
    }
}
