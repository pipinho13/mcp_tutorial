# The Complete Step-by-Step Tutorial

Build a Model Context Protocol (MCP) server in Python and connect it to Claude.

This guide is written for **complete beginners**. Every command is shown in
full, along with the output you should expect. If you can open a terminal and
edit a text file, you can finish this.

**What you'll build:** a *notes manager* server. Once connected, you can tell
Claude things like *"save a note called Groceries with milk, eggs, bread"* and
*"search my notes for Kyoto"*, and it will run your code to do it. Notes are
stored as Markdown files on your own machine — nothing leaves your computer.

**Tested on:** macOS (Apple Silicon), with `uv` 0.11.19, Python 3.12.13, and
`mcp` 1.27.2. The steps are the same on Linux; Windows notes are included where
they differ.

---

## Table of contents

1. [Background: how MCP works](#1-background-how-mcp-works)
2. [Install uv](#2-install-uv)
3. [Get the project](#3-get-the-project)
4. [Set up the environment with `uv sync`](#4-set-up-the-environment-with-uv-sync)
5. [Read the server code](#5-read-the-server-code)
6. [Test the server (two ways)](#6-test-the-server-two-ways)
7. [Connect to Claude Desktop](#7-connect-to-claude-desktop)
8. [Connect to Claude Code](#8-connect-to-claude-code)
9. [Make changes and iterate](#9-make-changes-and-iterate)
10. [How reproducibility works](#10-how-reproducibility-works)
11. [Troubleshooting](#11-troubleshooting)
12. [Next steps](#12-next-steps)

---

## 1. Background: how MCP works

When you chat with Claude, Claude is the **client**. Your program is the
**server**. The protocol between them is **MCP**.

```
You ──ask──▶ Claude (the client)
                │  decides one of your tools is needed,
                │  asks your permission, then calls it
                ▼
        notes_server.py (your MCP server)
                │  reads / writes
                ▼
          notes/*.md  (files on your disk)
```

Your server exposes two kinds of capabilities:

- **Tools** — functions Claude can *call* to take an action. Each tool has a
  name, a description (from its docstring), and typed arguments. Claude reads
  those to decide when and how to call it.
- **Resources** — read-only data Claude can *load* into its context, identified
  by a URI like `notes://all`.

Claude can never touch your files directly. It can only do what your tools
allow. **You** define the boundary.

---

## 2. Install uv

[`uv`](https://docs.astral.sh/uv/) is a fast Python package and project
manager. We use it because it handles **three** annoying things for you in one
tool:

1. Installing the right **Python version** (you don't need Python preinstalled).
2. Creating an isolated **virtual environment**.
3. Installing **dependencies** from a lockfile so everyone gets identical
   versions.

### macOS / Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Expected output (version number may differ):

```
downloading uv 0.11.19 aarch64-apple-darwin
installing to /Users/you/.local/bin
  uv
  uvx
everything's installed!
```

### Windows (PowerShell)

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Activate it in your shell

The installer puts `uv` in `~/.local/bin`. **Open a new terminal window** so
that folder is on your `PATH`, then verify:

```bash
uv --version
```

```
uv 0.11.19
```

> If `uv: command not found`, your shell hasn't picked up `~/.local/bin` yet.
> Either open a brand-new terminal, or run
> `export PATH="$HOME/.local/bin:$PATH"` for the current session.

---

## 3. Get the project

If you're reading this on GitHub, clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/mcp-notes-tutorial.git
cd mcp-notes-tutorial
```

(Replace the URL with your fork's URL.)

The folder contains:

```
notes_server.py     # the MCP server — the code that runs
pyproject.toml      # project metadata + dependencies
uv.lock             # exact pinned versions of every package
.python-version     # pins Python to 3.12
README.md           # overview
TUTORIAL.md         # this file
.gitignore          # keeps your venv and personal notes out of git
```

You do **not** need to create a virtual environment by hand or run
`pip install`. The next step does all of that.

---

## 4. Set up the environment with `uv sync`

From inside the project folder, run:

```bash
uv sync
```

What happens (real output, trimmed):

```
Downloading cpython-3.12... (download)
Using CPython 3.12.13
Creating virtual environment at: .venv
Resolved 41 packages in 662ms
Prepared 36 packages in 626ms
Installed 36 packages in 22ms
 + anyio==4.13.0
 + click==8.4.1
 + httpx==0.28.1
 + mcp==1.27.2
 + pydantic==2.13.4
 ... (and more)
```

In one command, uv:

1. Read `.python-version` and downloaded **Python 3.12** (if you didn't have it).
2. Created a virtual environment in `.venv/`.
3. Installed the **exact** package versions recorded in `uv.lock`, including
   `mcp` (the MCP SDK) and its dependencies.

Confirm the interpreter:

```bash
uv run python --version
```

```
Python 3.12.13
```

> **What is `uv run`?** It runs a command *inside* the project's virtual
> environment without you having to "activate" anything. Prefix any Python
> command with `uv run` and it uses the right Python and packages.

> ⚠️ **The MCP SDK requires Python 3.10 or newer.** If your system Python is
> 3.9 or older, that's fine — uv installed its own 3.12 just for this project,
> separate from your system Python.

---

## 5. Read the server code

Open `notes_server.py`. Every MCP server built with `FastMCP` has the same
four-part shape:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("notes")          # 1. create the server (name = "notes")

@mcp.tool()                     # 2. expose a function as a tool
def add_note(title: str, content: str) -> str:
    """Create a new note."""    #    ← Claude reads this to decide when to call it
    ...
    return f"Saved note '{title}'."

@mcp.resource("notes://all")    # 3. expose read-only data as a resource
def all_notes() -> str:
    ...

if __name__ == "__main__":
    mcp.run()                   # 4. start talking to the client over stdio
```

Three things that matter for beginners:

1. **The docstring is the tool's manual.** Claude chooses tools based on their
   name, docstring, and argument names. Vague docstrings → Claude uses the tool
   at the wrong time. Be clear and specific.
2. **Type hints become the input schema.** `title: str` tells the SDK that
   `title` must be a string. The SDK turns your function signature into a JSON
   schema automatically — no manual schema writing.
3. **The return value is the tool result** that goes back to Claude, which it
   then uses to answer you.

The notes are saved as `.md` files in a `notes/` folder created next to the
script. The helper `_note_path()` sanitizes titles so a note can never write
outside that folder — a small but important safety detail.

---

## 6. Test the server (two ways)

**Always test your server by itself before wiring it into Claude.** That way,
if something breaks later, you know it's the connection, not the server.

### Option A — The MCP Inspector (visual)

The SDK ships a browser-based Inspector:

```bash
uv run mcp dev notes_server.py
```

This launches a local web UI (it prints a URL, usually
`http://localhost:6274`). In the Inspector:

1. Go to the **Tools** tab → click **List Tools**. You'll see all six:
   `add_note`, `update_note`, `list_notes`, `read_note`, `search_notes`,
   `delete_note`.
2. Select `add_note`, enter title `Groceries` and content `Milk, eggs, bread`,
   and click **Run Tool**. You'll get back `Saved note 'Groceries'.`
3. Run `list_notes` (no arguments) → it returns `Your notes:` followed by
   `- groceries`.
4. Open the **Resources** tab → you'll see `notes://all`.

Look in the project's `notes/` folder — there's now a real `groceries.md` file.

Press `Ctrl+C` in the terminal to stop the Inspector.

### Option B — A quick script (no browser)

If you can't open a browser, you can exercise the tools directly. This is also
a great way to confirm the install worked. Run:

```bash
uv run python -c "
import notes_server as ns
print(ns.add_note('Trip ideas', 'Visit Kyoto in spring, see cherry blossoms.'))
print(ns.list_notes())
print(ns.search_notes('kyoto'))
print(ns.read_note('Trip ideas'))
print(ns.delete_note('Trip ideas'))
"
```

Expected output:

```
Saved note 'Trip ideas'.
Your notes:
- trip_ideas
Notes matching 'kyoto':
- trip_ideas
Visit Kyoto in spring, see cherry blossoms.
Deleted note 'Trip ideas'.
```

If you see that, your server works. ✅

---

## 7. Connect to Claude Desktop

[Download Claude Desktop](https://claude.ai/download) if you haven't.

### 7a. Get your project's absolute path

Claude Desktop needs to know exactly where your server lives. From inside the
project folder:

```bash
pwd
```

```
/Users/you/Documents/personal/mcp_tutorial
```

Copy that path — you'll paste it in the next step.

### 7b. Edit the config file

Open Claude Desktop's config file in a text editor:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

If the file doesn't exist, create it. Paste this, replacing the path with the
output of `pwd`:

```json
{
  "mcpServers": {
    "notes": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/you/Documents/personal/mcp_tutorial",
        "run",
        "notes_server.py"
      ]
    }
  }
}
```

This tells Claude Desktop: *to start the `notes` server, run
`uv --directory <path> run notes_server.py`*. The `--directory` flag makes uv
use the project's environment regardless of where Claude launches it from.

> **If `uv` isn't found when Claude starts the server**, Claude Desktop's `PATH`
> doesn't include `~/.local/bin`. Replace `"uv"` with the full path. Find it
> with `which uv` (macOS/Linux) or `where uv` (Windows), e.g.
> `"/Users/you/.local/bin/uv"`.

### 7c. Restart and use it

**Fully quit Claude Desktop and reopen it** — quit the application, don't just
close the window. On restart you'll see a tools/connector icon near the chat
box. Click it to confirm the `notes` server is connected and its tools are
listed.

Now just talk to Claude:

> *Save a note called "Trip ideas" with: visit Kyoto in spring, see the cherry
> blossoms.*

The first time Claude wants to run a tool, it asks for your approval — that's
the safety prompt. Allow it. Then try:

> *What notes do I have?*
>
> *Search my notes for Kyoto.*
>
> *Read my "Trip ideas" note.*

Claude calls your tools and answers using the results.

---

## 8. Connect to Claude Code

Prefer the terminal? [Claude Code](https://claude.com/claude-code) uses the same
server. From inside the project folder:

```bash
claude mcp add notes -- uv --directory "$(pwd)" run notes_server.py
```

Everything after `--` is the command Claude Code will run to launch your
server. `$(pwd)` fills in the absolute path automatically.

Verify it's registered:

```bash
claude mcp list
```

You should see `notes` in the list. Now start Claude Code:

```bash
claude
```

Inside a session, run `/mcp` to see connected servers and their tools, then ask:

> *Use the notes server to save a note titled "Standup" with today's blockers.*

To remove the server later:

```bash
claude mcp remove notes
```

---

## 9. Make changes and iterate

Want to add your own tool? Edit `notes_server.py`. For example, a tool that
counts notes:

```python
@mcp.tool()
def count_notes() -> str:
    """Return how many notes are saved."""
    n = len(list(NOTES_DIR.glob("*.md")))
    return f"You have {n} note(s)."
```

After editing:

- **Claude Desktop:** fully quit and reopen it to reload the server.
- **Claude Code:** the server restarts on the next session; or remove and re-add it.
- **Inspector:** stop (`Ctrl+C`) and re-run `uv run mcp dev notes_server.py`.

If you add a new third-party package, add it with `uv add <package>` (this
updates `pyproject.toml` **and** `uv.lock`), then commit both files.

---

## 10. How reproducibility works

This project is set up so that **anyone who clones it gets the exact same
environment**. Three files make that happen — and all three are committed to
git:

| File              | Role                                                                 |
| ----------------- | -------------------------------------------------------------------- |
| `pyproject.toml`  | Declares what the project needs (`requires-python`, `dependencies`). |
| `uv.lock`         | Records the **exact** version + hash of every package, transitively. |
| `.python-version` | Pins the Python interpreter (3.12) so everyone runs the same one.    |

When someone runs `uv sync`, uv reads all three and recreates an identical
`.venv/`. No "works on my machine" surprises.

**What is *not* committed** (see `.gitignore`):

- `.venv/` — the virtual environment is regenerated by `uv sync`, so there's no
  reason to store it in git.
- `notes/` — your actual notes are personal data; the folder is recreated
  automatically on first run.
- `__pycache__/` — Python's compiled-bytecode cache.

> **Commit `uv.lock`.** It's the heart of reproducibility. A common beginner
> mistake is to gitignore it — don't.

---

## 11. Troubleshooting

| Symptom | Fix |
| --- | --- |
| `uv: command not found` | Open a new terminal, or `export PATH="$HOME/.local/bin:$PATH"`. |
| `uv sync` fails to find Python | uv normally downloads it. Check internet access; retry. The `.python-version` (3.12) tells uv which to fetch. |
| `mcp dev` says command not found | Re-run `uv sync`; confirm `pyproject.toml` lists `mcp[cli]` (the `[cli]` extra provides the `mcp` command). |
| Claude Desktop doesn't show the server | You must **fully quit and reopen** the app. Then check for typos/trailing commas in `claude_desktop_config.json` — it must be valid JSON. |
| Server fails to start in Claude | `uv` likely isn't on Claude's PATH. Use the full path from `which uv` as `"command"`. |
| Tools run but write nowhere | Check the `notes/` folder in the **project** directory; the path is relative to `notes_server.py`. |
| `ModuleNotFoundError: mcp` | You ran plain `python` instead of `uv run python`. Always prefix with `uv run`, or activate `.venv`. |

To inspect what's installed:

```bash
uv pip list
```

---

## 12. Next steps

- **Add a `prompt`.** `@mcp.prompt()` ships reusable prompt templates (e.g.
  "summarize all my notes"). See the SDK docs.
- **Add validation.** Your tools run real code. `delete_note` here is permanent
  — consider a confirmation step or a "trash" folder for anything destructive.
- **Try other transports.** This server uses `stdio` (the default for desktop
  apps). The SDK also supports HTTP for remote servers.
- **Read the official docs:**
  - MCP overview & concepts: <https://modelcontextprotocol.io>
  - Python SDK: <https://github.com/modelcontextprotocol/python-sdk>

Happy building. 🛠️
