"""A standalone MCP client — talk to the notes server from your terminal.

This is the *other half* of MCP. Claude Desktop and Claude Code are clients you
don't have to write; this file shows what a client actually does under the hood:

  1. Launch the MCP server (notes_server.py) and connect to it over stdio.
  2. Ask the server which tools it offers, and hand those tools to Claude.
  3. Run a chat loop: send your message to the Claude API, and whenever Claude
     asks to use a tool, call it on the server and feed the result back.

So this one script is BOTH an MCP client (to the notes server) AND a Claude API
client. The notes server never talks to Claude directly — this client is the
glue in the middle.

Requires an Anthropic API key:

    export ANTHROPIC_API_KEY="sk-ant-..."
    uv run client.py
"""

import asyncio
import os
import sys

import anthropic
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

MODEL = "claude-opus-4-8"

# Keeps Claude's answers tight and avoids it narrating its reasoning in the
# visible reply (thinking is off here to keep the loop simple to read).
SYSTEM_PROMPT = (
    "You are a helpful notes assistant. Use the provided tools to manage the "
    "user's notes. Reply with just the final answer, concisely."
)


async def run_chat(session: ClientSession, claude: anthropic.AsyncAnthropic) -> None:
    """Run the interactive chat loop against an initialized MCP session."""
    # 1. Ask the server for its tools, then translate them into the shape the
    #    Claude API expects: {name, description, input_schema}.
    tool_list = await session.list_tools()
    tools = [
        {
            "name": tool.name,
            "description": tool.description or "",
            "input_schema": tool.inputSchema,
        }
        for tool in tool_list.tools
    ]
    print(f"Connected. Server offers {len(tools)} tools: "
          f"{', '.join(t['name'] for t in tools)}")
    print("Type your message (or 'quit' to exit).\n")

    messages: list[dict] = []

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if user_input.lower() in {"quit", "exit", "q"}:
            break
        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})

        # 2. Inner agentic loop: keep going until Claude stops asking for tools.
        while True:
            response = await claude.messages.create(
                model=MODEL,
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                messages=messages,
                tools=tools,
            )
            # Preserve the assistant turn (including any tool_use blocks) in history.
            messages.append({"role": "assistant", "content": response.content})

            # Print any text Claude produced.
            for block in response.content:
                if block.type == "text":
                    print(f"Claude: {block.text}")

            # If Claude didn't ask for a tool, this turn is done.
            if response.stop_reason != "tool_use":
                break

            # 3. Execute each requested tool ON THE SERVER and collect results.
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                print(f"  [tool] {block.name}({block.input})")
                result = await session.call_tool(block.name, block.input)
                # An MCP tool result is a list of content blocks; pull out the text.
                text = "".join(
                    part.text for part in result.content if getattr(part, "type", "") == "text"
                )
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": text,
                    "is_error": bool(result.isError),
                })

            # Feed the tool results back as the next user turn, then loop.
            messages.append({"role": "user", "content": tool_results})

    print("Bye!")


async def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit(
            "ANTHROPIC_API_KEY is not set.\n"
            'Set it first:  export ANTHROPIC_API_KEY="sk-ant-..."'
        )

    # Launch the server with the SAME Python that's running this client, so it
    # uses the project's virtual environment (where `mcp` is installed).
    server = StdioServerParameters(command=sys.executable, args=["notes_server.py"])
    claude = anthropic.AsyncAnthropic()

    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()  # MCP handshake
            await run_chat(session, claude)


if __name__ == "__main__":
    asyncio.run(main())
