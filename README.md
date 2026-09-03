# 📝 AI Collaborative Rich Text Editor

> A collaborative document editing system built with **C + Python + Streamlit**, combining role-based document access, locking, version control, chat, document analytics, multimedia support, and rule-based AI assistance in a single interactive application.

[![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python)](https://www.python.org/)
[![C](https://img.shields.io/badge/C-Core%20Logic-blue?logo=c)](https://en.wikipedia.org/wiki/C_%28programming_language%29)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32%2B-FF4B4B?logo=streamlit)](https://streamlit.io/)
[![ctypes](https://img.shields.io/badge/Python%20%2B%20C-ctypes-orange)](https://docs.python.org/3/library/ctypes.html)

---

## 🚀 Overview

**AI Collaborative Rich Text Editor** is a software project that demonstrates how a traditional C-based document management system can be integrated with a modern Python user interface.

The project uses:

* **C** for the core document and collaboration logic
* **Python** for application orchestration
* **Streamlit** for the interactive web interface
* **ctypes** to connect Python with the compiled C shared library

The application simulates a collaborative editing environment where multiple users can have different permissions, editors can acquire document locks before making changes, users can communicate through an integrated chat, and document versions can be saved and restored.

It also includes a lightweight **rule-based AI suggestion system** that analyzes the document and provides structural writing recommendations.

---

## 🎯 Problem Statement

Modern collaborative editors provide several capabilities in one environment:

* Multiple user roles
* Controlled document editing
* Collaboration and communication
* Version history
* Document statistics
* Intelligent writing assistance
* Multimedia content

The goal of this project was to design a simplified version of such a system while demonstrating **data structures, access control, document state management, C programming, Python integration, and AI-assisted analysis** within a limited development timeframe.

---

## 💡 Solution

The application separates the system into two major layers:

```text
                    ┌───────────────────────────┐
                    │      Streamlit UI         │
                    │         Python            │
                    │                           │
                    │  Login • Editor • Chat    │
                    │  AI • Stats • Media       │
                    │  Version History           │
                    └─────────────┬─────────────┘
                                  │
                              ctypes
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │       C Shared Library    │
                    │       Core Logic          │
                    │                           │
                    │ Users • Documents         │
                    │ Locks • Chat • Versions   │
                    │ Media • Analysis          │
                    └───────────────────────────┘
```

Python handles the presentation and interaction layer, while the core document state and operations are maintained in C.

---

# ✨ Key Features

## 👥 User Management

Users can register and log in with one of two roles:

* **Editor**
* **Viewer**

Editors have permission to modify documents, while viewers can access the document without editing privileges.

The C layer maintains user information including username, role, and registration timestamp.

---

## 🔒 Document Locking

A document-locking mechanism controls editing access.

An editor must first acquire the document lock before modifying the document.

```text
Document Unlocked
       │
       ▼
Editor requests lock
       │
       ▼
   Lock acquired
       │
       ▼
   Editor edits
       │
       ▼
   Lock released
```

If another user currently holds the lock, the document cannot be edited by other users.

This demonstrates a basic form of **concurrency control and controlled resource access**.

The locking rules are implemented in the C core.

---

## ✏️ Rich Text Editing

Editors can add document entries with different formatting options:

* Normal
* Bold
* Italic

The system stores each document entry along with:

* User
* Content
* Format
* Timestamp
* Entry type

The editor also supports adding executable Python code blocks to the document.

---

## 💻 Code Blocks

Users can insert Python code blocks into the document.

The interface displays the code separately and provides an execution option with a restricted set of built-in functions and checks for several potentially unsafe operations.

> **Note:** The code execution feature is intended as a demonstration feature and should not be considered a production-grade Python sandbox.

---

## 💬 Collaborative Chat

An integrated chat system allows registered users to communicate while working on the document.

Each message stores:

* Username
* Message
* Timestamp

The chat history is maintained by the C backend and displayed through the Streamlit interface.

---

## 🤖 AI-Powered Document Suggestions

The application includes a lightweight **rule-based AI analysis module** implemented in C.

Instead of calling an external LLM API, the analyzer examines the document and generates structural suggestions.

Examples include:

* Suggesting an **Introduction** section when one is missing
* Suggesting a **Conclusion** section
* Detecting very short documents
* Checking whether the document starts with a capital letter
* Checking whether the document ends with appropriate punctuation

The Streamlit interface exposes this through the **AI Suggestions** tab.

### Example

```text
Document
   │
   ▼
C-based Analyzer
   │
   ├── Introduction check
   ├── Conclusion check
   ├── Length check
   ├── Capitalization check
   └── Punctuation check
   │
   ▼
Suggestions
```

This component demonstrates how deterministic text analysis can be integrated into an application and provides a foundation for replacing or extending the rules with NLP/LLM-based models in future versions.

---

## 📊 Document Analytics

The application provides document-level statistics including:

* Word count
* Character count
* Document entries
* Number of editors
* Number of viewers
* Chat messages
* Saved versions
* Media files

These statistics are calculated using the C core and exposed to the Streamlit interface.

---

## 🕓 Version History

Users can save named snapshots of the document.

Each version stores:

* Version label
* User who saved it
* Timestamp
* Document snapshot

Saved versions can be previewed and restored through the Version History interface.

The C implementation maintains document snapshots using version structures.

---

## 🖼️ Multimedia Support

Editors can upload multimedia files directly through the application.

Supported formats include:

### Images

* PNG
* JPG
* JPEG
* GIF

### Videos

* MP4
* WebM

Uploaded media is encoded and stored by the C layer, then decoded and displayed through Streamlit.

---

# 🧠 Technical Architecture

The project follows a two-layer architecture.

### Frontend / Application Layer

Built using:

* Python
* Streamlit
* HTML/CSS through Streamlit rendering
* `ctypes`

Responsibilities:

* User interface
* Session management
* Form handling
* Rendering documents
* Displaying analytics
* Handling media uploads
* Connecting to the C library

### Core Logic Layer

Built using C.

Responsibilities:

* User management
* Role management
* Document entries
* Lock/unlock operations
* Chat storage
* Version snapshots
* Media storage
* Document statistics
* Rule-based document analysis

---

# 🔗 Python–C Integration

One of the main technical aspects of the project is the integration between Python and C.

The Streamlit application loads the compiled C library using:

```python
import ctypes

lib = ctypes.CDLL(_lib_path)
```

The application then invokes exported C functions from Python.

For example:

```text
Python / Streamlit
       │
       │ ctypes
       ▼
Compiled C Library
       │
       ▼
Core document operation
       │
       ▼
Result returned to Python
       │
       ▼
Streamlit UI updated
```

The application also compiles the C source into a shared library when required, producing a `.dll` on Windows or `.so` on Linux-based systems.

This architecture demonstrates practical **cross-language interoperability** rather than implementing the entire application in a single language.

---

# 📁 Project Structure

```text
AI-text-editor/
│
├── app.py
│   └── Streamlit application and UI
│
├── collaborative_editor.c
│   └── Original console-based collaborative editor implementation
│
├── editor_lib.c
│   └── C core exposed as a shared library
│
├── style.css
│   └── Custom Streamlit styling
│
├── requirements.txt
│   └── Python dependencies
│
└── .streamlit/
    └── Streamlit configuration
```

The repository currently follows this structure.

---

# 🛠️ Tech Stack

| Technology    | Purpose                               |
| ------------- | ------------------------------------- |
| **C**         | Core document and collaboration logic |
| **Python**    | Application orchestration             |
| **Streamlit** | Interactive web interface             |
| **ctypes**    | Python ↔ C integration                |
| **CSS**       | UI customization                      |
| **Base64**    | Multimedia data handling              |
| **GCC**       | C shared-library compilation          |

---

# ⚙️ Installation

## 1. Clone the repository

```bash
git clone https://github.com/GAYATHRI-1702/AI-text-editor.git
cd AI-text-editor
```

## 2. Create a virtual environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

The current project requires Streamlit 1.32.0 or newer.

---

# 🔧 C Compiler Requirement

Because the Streamlit application loads the C core as a shared library, a C compiler such as **GCC** is required.

Verify GCC:

```bash
gcc --version
```

If GCC is unavailable, install a suitable compiler for your operating system before running the application.

---

# ▶️ Running the Application

Start the Streamlit application with:

```bash
streamlit run app.py
```

Streamlit will provide a local URL in the terminal, typically:

```text
http://localhost:8501
```

Open that address in your browser.

---

# 🧪 Using the Application

## Step 1 — Register a User

From the sidebar:

1. Enter a username.
2. Select either:

   * Editor
   * Viewer
3. Click **Register**.

## Step 2 — Login

Select the registered user and click **Login**.

## Step 3 — Edit the Document

If logged in as an Editor:

1. Acquire the document lock.
2. Add text.
3. Select formatting.
4. Optionally add a Python code block.
5. Save a document version.
6. Release the lock when finished.

## Step 4 — Explore Other Modules

Use the application tabs:

```text
✏️ Edit
📄 View
💬 Chat
🤖 AI Suggestions
📊 Stats
🖼️ Media
🕓 Version History
```

The application exposes these seven major sections through the Streamlit interface.

---

# 🔐 Access Control Model

The project uses a simple role-based permission model.

| Operation             | Editor | Viewer |
| --------------------- | :----: | :----: |
| Login                 |    ✅   |    ✅   |
| View document         |    ✅   |    ✅   |
| Send chat messages    |    ✅   |    ✅   |
| Acquire document lock |    ✅   |    ❌   |
| Edit document         |    ✅   |    ❌   |
| Add code block        |    ✅   |    ❌   |
| Save versions         |    ✅   |    ❌   |
| Restore versions      |    ✅   |    ❌   |
| Upload media          |    ✅   |    ❌   |

The underlying C implementation explicitly represents roles as `Editor` and `Viewer` and checks permissions before operations.

---

# 📌 Design Highlights

### 1. Separation of Concerns

The UI and core logic are separated:

```text
Streamlit → Presentation
Python    → Integration
C         → Core state and operations
```

### 2. Explicit State Management

The C layer maintains structured state for:

* Users
* Documents
* Locks
* Chat
* Versions
* Media

### 3. Controlled Editing

The locking mechanism prevents multiple editors from modifying the document state simultaneously within the application's shared state model.

### 4. Extensible AI Layer

The current rule-based analyser can be extended into a more sophisticated NLP/LLM pipeline without redesigning the entire UI.

---

# ⚠️ Current Limitations

This project is primarily a **prototype / educational implementation** rather than a production collaborative editor.

Current limitations include:

* Collaboration is simulated through shared application state rather than a distributed real-time synchronization protocol.
* There is no WebSocket-based operational transformation or CRDT implementation.
* User authentication is intentionally lightweight.
* Document data is maintained in application memory.
* The AI component currently uses deterministic rule-based analysis rather than an external LLM.
* The Python code execution feature should not be treated as a secure production sandbox.
* The system is not designed for large-scale concurrent users.
* Persistent database-backed storage is not currently implemented.

These limitations also provide clear directions for future development.

---

# 🚀 Future Enhancements

Potential improvements include:

### 🤖 Advanced AI

* LLM-powered grammar correction
* Text rewriting
* Summarization
* Context-aware suggestions
* Semantic document analysis
* AI-assisted content generation
* NLP-based document classification

### 👥 True Real-Time Collaboration

* WebSocket communication
* Operational Transformation
* CRDT-based synchronization
* User presence indicators
* Cursor tracking
* Conflict resolution

### 🗄️ Persistent Storage

* PostgreSQL / MySQL integration
* Document persistence
* User authentication
* Cloud storage
* Automatic backups

### 🔐 Security

* Secure authentication
* Password hashing
* Session management
* Permission policies
* Secure code execution using isolated containers

### 📈 Scalability

* Backend API
* Distributed state management
* Caching
* Asynchronous processing
* Horizontal scaling

---

# 🎓 What This Project Demonstrates

This project combines several software engineering concepts in one system:

* Data structures in C
* Role-based access control
* Resource locking
* State management
* Versioning
* Cross-language integration
* Python application development
* Streamlit UI development
* Rule-based text analysis
* Multimedia processing
* Modular system design

It also demonstrates how a **low-level systems-oriented language such as C can serve as the core logic layer of a higher-level Python application**.

---

# 🌐 Live Demo

A deployed Streamlit version of the application is available here:

**AI Collaborative Editor — Streamlit Demo**

https://ai-text-editor-iechy63wyhshhmyzqlp5uh.streamlit.app/

The repository currently links to this deployed application.

---


# 🏆 Promptathon

This project was developed as part of **Promptathon**, an AI-driven sprint challenge conducted by **Pallavi Engineering College**.

The project was developed under time constraints with a focus on quickly designing, implementing, and integrating multiple software components.

The experience provided practical exposure to:

* Rapid prototyping
* AI-assisted development
* C/Python integration
* Modular architecture
* UI development
* Software design under time constraints

---

# 👩‍💻 Authors
Gayathri Ravula

GitHub:
https://github.com/GAYATHRI-1702

LinkedIn:
https://www.linkedin.com/in/gayathri-ravula-31a840339/

Talada Jahnavi

GitHub:
https://github.com/JahnaviTalada

LinkedIn:
https://www.linkedin.com/in/jahnavi-talada-266882357/


---

# 📄 License

This project is currently intended primarily for educational and demonstration purposes.

If you plan to distribute or reuse the project, add an explicit open-source license such as MIT after deciding the intended licensing terms.

---

## ⭐ If you find this project useful

Consider giving the repository a ⭐ and exploring the implementation.

**Repository:**
https://github.com/GAYATHRI-1702/AI-text-editor
