"""A beginner-friendly MCP server: a personal notes manager.

This server exposes a few *tools* (actions Claude can take) and one *resource*
(read-only data Claude can pull into context). Notes are stored as plain
Markdown files in a local `notes/` folder next to this script — so everything
is offline and you can inspect the files yourself.

Run it directly with `uv run notes_server.py` (stdio transport), or use
`uv run mcp dev notes_server.py` to open the MCP Inspector for testing.
"""

from pathlib import Path

from mcp.server.fastmcp import FastMCP

# Where notes live. Created on first run if it doesn't exist.
NOTES_DIR = Path(__file__).parent / "notes"
NOTES_DIR.mkdir(exist_ok=True)

# The server. The name "notes" is how Claude will refer to this server.
mcp = FastMCP("notes")


def _note_path(title: str) -> Path:
    """Turn a human title into a safe filename like `my_first_note.md`.

    We strip out anything that isn't a letter, number, space, dash, or
    underscore so a title can never escape the notes folder.
    """
    safe = "".join(c for c in title if c.isalnum() or c in (" ", "-", "_")).strip()
    safe = safe.replace(" ", "_").lower()
    if not safe:
        raise ValueError("Title must contain at least one letter or number.")
    return NOTES_DIR / f"{safe}.md"


@mcp.tool()
def add_note(title: str, content: str) -> str:
    """Create a new note.

    Args:
        title: A short name for the note, e.g. "Groceries".
        content: The body text of the note.
    """
    path = _note_path(title)
    if path.exists():
        return f"A note titled '{title}' already exists. Use update_note to change it."
    path.write_text(content, encoding="utf-8")
    return f"Saved note '{title}'."


@mcp.tool()
def update_note(title: str, content: str) -> str:
    """Replace the content of an existing note.

    Args:
        title: The title of the note to update.
        content: The new body text (overwrites the old content).
    """
    path = _note_path(title)
    if not path.exists():
        return f"No note titled '{title}'. Use add_note to create it first."
    path.write_text(content, encoding="utf-8")
    return f"Updated note '{title}'."


@mcp.tool()
def list_notes() -> str:
    """List the titles of all saved notes."""
    titles = sorted(p.stem for p in NOTES_DIR.glob("*.md"))
    if not titles:
        return "You have no notes yet."
    return "Your notes:\n" + "\n".join(f"- {t}" for t in titles)


@mcp.tool()
def read_note(title: str) -> str:
    """Read the full content of one note.

    Args:
        title: The title of the note to read.
    """
    path = _note_path(title)
    if not path.exists():
        return f"No note titled '{title}'."
    return path.read_text(encoding="utf-8")


@mcp.tool()
def search_notes(query: str) -> str:
    """Find notes whose title or content contains the query (case-insensitive).

    Args:
        query: The text to search for.
    """
    query_lower = query.lower()
    hits = []
    for path in sorted(NOTES_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if query_lower in path.stem.lower() or query_lower in text.lower():
            hits.append(path.stem)
    if not hits:
        return f"No notes match '{query}'."
    return f"Notes matching '{query}':\n" + "\n".join(f"- {t}" for t in hits)


@mcp.tool()
def delete_note(title: str) -> str:
    """Delete a note permanently.

    Args:
        title: The title of the note to delete.
    """
    path = _note_path(title)
    if not path.exists():
        return f"No note titled '{title}'."
    path.unlink()
    return f"Deleted note '{title}'."


@mcp.resource("notes://all")
def all_notes() -> str:
    """A read-only snapshot of every note, concatenated.

    Resources are data Claude can load into its context on demand, as opposed
    to tools, which perform actions. This one lets Claude "see" all notes at
    once without calling a tool for each.
    """
    paths = sorted(NOTES_DIR.glob("*.md"))
    if not paths:
        return "No notes yet."
    chunks = []
    for path in paths:
        chunks.append(f"# {path.stem}\n\n{path.read_text(encoding='utf-8')}")
    return "\n\n---\n\n".join(chunks)


if __name__ == "__main__":
    # Default transport is stdio: the server talks to Claude over standard
    # input/output. This is what Claude Desktop and Claude Code launch.
    mcp.run()
