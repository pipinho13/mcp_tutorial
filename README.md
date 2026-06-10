# MCP Notes Server — Your First MCP Server with Claude (Python)

A beginner-friendly, **fully reproducible** tutorial for building a
**Model Context Protocol (MCP)** server in Python and connecting it to Claude.

The example server is a **personal notes manager**: Claude can create, list,
read, search, update, and delete notes that are saved as Markdown files on your
own computer.

> 📖 **New to this? Follow the complete step-by-step guide in
> [`TUTORIAL.md`](./TUTORIAL.md).** It explains every single command and shows
> the exact output you should see.

---

## What is MCP?

**MCP (Model Context Protocol)** is an open standard that lets AI apps like
Claude talk to external programs. You write a small **server** exposing:

- **Tools** — actions Claude can take (e.g. "save a note")
- **Resources** — read-only data Claude can pull in (e.g. "all my notes")

Claude is the **client**: when you ask it something, it can decide to call your
tools. Build the server once, and any MCP-aware app can use it.

> **Do I need to write a client too?** Usually no — the client is an existing
> app like **Claude Desktop** or **Claude Code**. You only write a server. This
> repo includes an optional `client.py` purely to *show* what a client does
> under the hood; see [`TUTORIAL.md` §9](./TUTORIAL.md#9-bonus-write-your-own-client-clientpy).

---

## Quickstart

Requires [**uv**](https://docs.astral.sh/uv/) (the tutorial shows how to install
it). Then, from this folder:

```bash
# 1. Set up the environment (installs Python 3.12 + the MCP SDK, pinned)
uv sync

# 2. Test the server in the visual MCP Inspector
uv run mcp dev notes_server.py
```

To connect it to **Claude Desktop**, add this to your
`claude_desktop_config.json` (use the absolute path from `pwd`):

```json
{
  "mcpServers": {
    "notes": {
      "command": "uv",
      "args": ["--directory", "/ABSOLUTE/PATH/TO/mcp_tutorial", "run", "notes_server.py"]
    }
  }
}
```

To connect it to **Claude Code**:

```bash
claude mcp add notes -- uv --directory "$(pwd)" run notes_server.py
```

Full details, expected output, and troubleshooting are in
[`TUTORIAL.md`](./TUTORIAL.md).

---

## Project structure

| File                 | Purpose                                                        |
| -------------------- | -------------------------------------------------------------- |
| `notes_server.py`    | The MCP **server**: 6 tools + 1 resource                       |
| `client.py`          | Optional standalone MCP **client** — chat with the server from your terminal (no Claude Desktop needed) |
| `pyproject.toml`     | Project metadata, requires Python ≥ 3.10, depends on `mcp[cli]` and `anthropic` |
| `uv.lock`            | Exact pinned versions of every dependency (commit this!)       |
| `.python-version`    | Pins the Python interpreter to 3.12 for reproducibility        |
| `.env.example`       | Template for your API key — copy to `.env` (git-ignored) and fill in |
| `TUTORIAL.md`        | The complete step-by-step walkthrough                          |
| `.gitignore`         | Excludes the virtual env and your personal notes from git      |

---

## The tools

| Tool                    | What it does                                |
| ----------------------- | ------------------------------------------- |
| `add_note(title, body)` | Create a new note                           |
| `update_note(title, body)` | Replace an existing note's content       |
| `list_notes()`          | List all note titles                        |
| `read_note(title)`      | Read one note                               |
| `search_notes(query)`   | Find notes by title or content              |
| `delete_note(title)`    | Delete a note permanently                   |

Plus a resource, `notes://all`, that returns every note concatenated.

---

## Tested with

- **uv** 0.11.19
- **Python** 3.12.13 (pinned via `.python-version`)
- **mcp** 1.27.2

Because `uv.lock` and `.python-version` are committed, anyone who runs
`uv sync` gets the exact same environment.

---

## License

MIT — see [`LICENSE`](./LICENSE). Use it, fork it, teach with it.
