#!/usr/bin/env python3
"""Scripted Responses API and network traps for worker sandbox tests. Nothing here talks to a real model.

argv: STATE_DIR. STATE_DIR/scenario.json is a list of steps, re-read on every request:
  {"label": str, "cmd": str, "escalate": bool}  -> one shell tool call
  {"label": str, "tool": "[NAMESPACE/]NAME", "args": {...}}   -> another tool, MCP tools by namespace
Steps are counted from the last user message, so a resumed thread replays the scenario; steps whose tool is
not offered are skipped and logged as "TOOL NOT OFFERED". After the last step the model answers "DONE". Requests are summarised in requests.jsonl, tool outputs in outputs.jsonl, the
offered tools of the first turn in tools.json. Writes `port` (model), `trap-port` (TCP trap) and creates
`trap.sock` (unix trap); every connection to a trap is logged to net.log.
"""
import http.server
import json
import os
import socket
import socketserver
import sys
import threading

STATE = sys.argv[1]
SHELL_TOOLS = ("exec_command", "shell_command", "shell", "local_shell")
OUTPUT_TYPES = ("function_call_output", "custom_tool_call_output", "mcp_tool_call_output")


def append(name, record):
    with open(os.path.join(STATE, name), "a") as f:
        f.write(json.dumps(record) + "\n")


def tool_names(tools):
    return [t.get("name") or (t.get("function") or {}).get("name") or t.get("type") for t in tools or []]


def shell_args(tool, step):
    cmd = step["cmd"]
    if tool == "exec_command":
        args = {"cmd": cmd, "yield_time_ms": 10000}
    elif tool == "shell_command":
        args = {"command": cmd, "timeout_ms": 10000}
    else:
        args = {"command": ["/bin/zsh", "-c", cmd], "timeout_ms": 10000}
    if step.get("escalate"):
        args["sandbox_permissions"] = "require_escalated"
        args["justification"] = "sandbox test"
    return args


def sse(events):
    return "".join(f"event: {e['type']}\ndata: {json.dumps(e)}\n\n" for e in events).encode()


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def reply(self, status, body, kind="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        append("requests.jsonl", {"method": "GET", "path": self.path})
        self.reply(200, b'{"object":"list","data":[]}')

    def do_POST(self):
        raw = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        try:
            body = json.loads(raw)
        except ValueError:
            append("requests.jsonl", {"method": "POST", "path": self.path, "undecodable": len(raw)})
            return self.reply(400, b"{}")
        if not self.path.endswith("/responses"):
            append("requests.jsonl", {"method": "POST", "path": self.path})
            return self.reply(200, b"{}")
        with open(os.path.join(STATE, "scenario.json")) as f:
            scenario = json.load(f)
        items = [i for i in body.get("input") or [] if isinstance(i, dict)]
        users = [n for n, i in enumerate(items) if i.get("type", "message") == "message" and i.get("role") == "user"]
        turn = items[users[-1] + 1:] if users else items
        outputs = [i for i in turn if i.get("type") in OUTPUT_TYPES]
        names = tool_names(body.get("tools"))
        append("requests.jsonl", {"method": "POST", "path": self.path, "model": body.get("model"),
                                  "tools": names, "outputs": len(outputs)})
        if not os.path.exists(os.path.join(STATE, "tools.json")):
            with open(os.path.join(STATE, "tools.json"), "w") as f:
                json.dump(body.get("tools"), f, indent=1)
        # A tool step names "namespace/function" (MCP tools are namespaces); steps whose tool is not offered
        # are skipped and reported once, so one scenario fits every configuration.
        offered = [s for s in scenario if "tool" not in s or s["tool"].split("/")[0] in names]
        n = len(outputs)
        if n == 0 and names:
            for s in scenario:
                if s not in offered:
                    append("outputs.jsonl", {"label": s["label"], "output": f"TOOL NOT OFFERED: {s['tool']}"})
        if outputs:
            text = outputs[-1].get("output")
            text = text if isinstance(text, str) else json.dumps(text)
            label = offered[n - 1]["label"] if n - 1 < len(offered) else "?"
            append("outputs.jsonl", {"label": label, "output": text[:4000]})
        rid = f"resp_{os.getpid()}_{n}_{len(items)}"
        item = {"type": "message", "role": "assistant", "id": f"msg_{rid}",
                "content": [{"type": "output_text", "text": "DONE"}]}
        if n < len(offered) and names:
            step = offered[n]
            item = {"type": "function_call", "id": f"fc_{rid}", "call_id": f"call_{n}_{step['label']}"}
            if "tool" in step:
                namespace, _, function = step["tool"].rpartition("/")
                item.update(name=function, arguments=json.dumps(step.get("args", {})))
                if namespace:
                    item["namespace"] = namespace
            else:
                tool = next((t for t in SHELL_TOOLS if t in names), None)
                item.update(name=tool, arguments=json.dumps(shell_args(tool, step)))
        events = [{"type": "response.created", "response": {"id": rid}},
                  {"type": "response.output_item.done", "output_index": 0, "item": item},
                  {"type": "response.completed", "response": {"id": rid, "usage": {
                      "input_tokens": 10, "input_tokens_details": {"cached_tokens": 0}, "output_tokens": 5,
                      "output_tokens_details": {"reasoning_tokens": 0}, "total_tokens": 15}}}]
        self.reply(200, sse(events), "text/event-stream")


class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


def trap(sock, kind):
    while True:
        conn, _ = sock.accept()
        append("net.log", {"trap": kind})
        conn.close()


def publish(name, value):
    with open(os.path.join(STATE, name + ".tmp"), "w") as f:
        f.write(str(value))
    os.rename(os.path.join(STATE, name + ".tmp"), os.path.join(STATE, name))


tcp = socket.socket()
tcp.bind(("127.0.0.1", 0))
tcp.listen(8)
unix_path = os.path.join(STATE, "trap.sock")
if os.path.exists(unix_path):
    os.unlink(unix_path)
unix = socket.socket(socket.AF_UNIX)
unix.bind(unix_path)
unix.listen(8)
for s, kind in ((tcp, "tcp"), (unix, "unix")):
    threading.Thread(target=trap, args=(s, kind), daemon=True).start()
server = Server(("127.0.0.1", 0), Handler)
publish("trap-port", tcp.getsockname()[1])
publish("port", server.server_address[1])
server.serve_forever()
