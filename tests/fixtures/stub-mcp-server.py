#!/usr/bin/env python3
"""Stub MCP server (stdio) with one fake "write" tool. It only appends to a log: argv LOG NAME.

A line "NAME start" proves that a worker started the server; "NAME call ..." that the model called the tool.
"""
import json
import sys

log, name = sys.argv[1], sys.argv[2]


def note(text):
    with open(log, "a") as f:
        f.write(f"{name} {text}\n")


note("start")
for line in sys.stdin:
    try:
        msg = json.loads(line)
    except ValueError:
        continue
    method, mid = msg.get("method"), msg.get("id")
    if method == "tools/call":
        note("call " + json.dumps(msg.get("params")))
    if mid is None:
        continue
    if method == "initialize":
        result = {"protocolVersion": msg["params"].get("protocolVersion", "2025-06-18"),
                  "capabilities": {"tools": {}}, "serverInfo": {"name": name, "version": "0"}}
    elif method == "tools/list":
        result = {"tools": [{"name": "write_table", "description": "Writes a production table (test stub: only logs).",
                             "inputSchema": {"type": "object", "properties": {"table": {"type": "string"}}}}]}
    elif method == "tools/call":
        result = {"content": [{"type": "text", "text": "stub write logged"}]}
    elif method == "ping":
        result = {}
    else:
        sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": method}}) + "\n")
        sys.stdout.flush()
        continue
    sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": mid, "result": result}) + "\n")
    sys.stdout.flush()
