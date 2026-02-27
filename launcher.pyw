import tkinter as tk
from tkinter import scrolledtext
import subprocess
import threading
import os
import queue
import shutil
import re
import webbrowser
from datetime import datetime

# Prevents black CMD windows from flashing on Windows
NO_WINDOW = subprocess.CREATE_NO_WINDOW

APP_DIR    = os.path.dirname(os.path.abspath(__file__))
PYTHON     = r"C:\Users\Windows\AppData\Local\Python\pythoncore-3.14-64\python.exe"
TOKEN_FILE = os.path.join(APP_DIR, ".ngrok_token")

def _load_saved_token():
    try:
        with open(TOKEN_FILE) as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""

def _save_token(token):
    with open(TOKEN_FILE, "w") as f:
        f.write(token.strip())

# ── colours ──────────────────────────────────────────────────────────────────
BG        = "#1e1e2e"
PANEL     = "#2a2a3e"
ACCENT    = "#7c3aed"
BTN_START = "#16a34a"
BTN_STOP  = "#dc2626"
BTN_PULL  = "#0369a1"
BTN_FG    = "#ffffff"
LOG_BG    = "#0f0f1a"
LOG_FG    = "#a0e0a0"
TXT_FG    = "#e2e8f0"
TXT_DIM   = "#94a3b8"
ON        = "#22c55e"   # green
OFF       = "#ef4444"   # red
IDLE      = "#475569"   # grey

# ── processes held globally ───────────────────────────────────────────────────
server_proc  = None
tunnel_proc  = None
log_queue    = queue.Queue()
ngrok_url    = None   # public URL detected from ngrok output

# ─────────────────────────────────────────────────────────────────────────────

def ts():
    return datetime.now().strftime("%H:%M:%S")

def log(msg, colour=LOG_FG):
    log_queue.put((f"[{ts()}]  {msg}", colour))

def stream_output(proc, label, colour, url_hook=None):
    """Read stdout from a subprocess, push lines to log; optionally call url_hook(line)."""
    for line in proc.stdout:
        line = line.rstrip()
        if line:
            log_queue.put((f"[{ts()}] {label}: {line}", colour))
            if url_hook:
                url_hook(line)

# ── server controls ───────────────────────────────────────────────────────────

def start_server():
    global server_proc
    if server_proc and server_proc.poll() is None:
        log("Server is already running.", "#facc15")
        return
    log("Starting Flask server…", "#60a5fa")
    server_proc = subprocess.Popen(
        [PYTHON, "app.py"],
        cwd=APP_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        creationflags=NO_WINDOW,
    )
    threading.Thread(target=stream_output, args=(server_proc, "SERVER", "#86efac"), daemon=True).start()
    threading.Thread(target=watch_server, daemon=True).start()
    update_lights()

def watch_server():
    global server_proc
    if server_proc:
        server_proc.wait()
        log("Flask server stopped.", "#f87171")
        update_lights()

def stop_server():
    global server_proc
    if server_proc and server_proc.poll() is None:
        log("Stopping Flask server…", "#facc15")
        server_proc.terminate()
        server_proc = None
    else:
        log("Server is not running.", TXT_DIM)
    update_lights()

# ── ngrok URL detection ───────────────────────────────────────────────────────

def _restart_tunnel_after_kill():
    """Called when ERR_NGROK_334 is detected — kill strays and retry once."""
    global tunnel_proc
    if tunnel_proc and tunnel_proc.poll() is None:
        tunnel_proc.terminate()
        tunnel_proc = None
    _kill_stray_ngrok()
    start_tunnel()

def _parse_ngrok_url(line):
    global ngrok_url
    # Detect "already online" error — stray process from previous session
    if "ERR_NGROK_334" in line or "already online" in line:
        log("⚠ ngrok: endpoint already running — killing stray process and retrying…", "#facc15")
        root.after(500, _restart_tunnel_after_kill)
        return
    # Detect auth errors
    if any(x in line for x in ("ERR_NGROK_4018", "ERR_NGROK_8012", "ERR_NGROK_105",
                                "authentication failed", "authtoken", "account not found",
                                "auth token", "sign up", "ngrok.com/signup")):
        log("⚠ ngrok AUTH ERROR — you need a free authtoken!", "#f87171")
        log("  1. Go to https://ngrok.com/signup (free)", "#facc15")
        log("  2. Copy your authtoken from the dashboard", "#facc15")
        log("  3. Paste it in the Authtoken box below and click  Save & Start", "#facc15")
        return
    m = re.search(r'url=(https?://[^\s]+)', line)
    if not m:
        m = re.search(r'(https://[a-z0-9\-]+\.ngrok[^\s]+)', line)
    if m:
        found = m.group(1)
        if ngrok_url != found:
            ngrok_url = found
            root.after(0, _refresh_tunnel_url_btn)

def _refresh_tunnel_url_btn():
    if ngrok_url:
        tunnel_url_btn.config(text=f"\U0001f310  {ngrok_url}", fg="#38bdf8", state=tk.NORMAL,
                              command=lambda: webbrowser.open(ngrok_url))
        log(f"Tunnel URL: {ngrok_url}", "#c4b5fd")
    else:
        tunnel_url_btn.config(text="Tunnel URL — not running", fg=TXT_DIM, state=tk.DISABLED)

# ── tunnel controls ───────────────────────────────────────────────────────────
def _apply_authtoken_and_start():
    """Save token from entry field, configure ngrok, then start tunnel."""
    token = token_entry.get().strip()
    if not token:
        log("Enter your ngrok authtoken first.", "#f87171")
        return
    _save_token(token)
    ngrok = shutil.which("ngrok") or (
        os.path.join(APP_DIR, "ngrok.exe") if os.path.exists(os.path.join(APP_DIR, "ngrok.exe")) else None
    )
    if not ngrok:
        log("ngrok not found.", "#f87171")
        return
    log("Saving authtoken to ngrok config\u2026", "#60a5fa")
    result = subprocess.run(
        [ngrok, "config", "add-authtoken", token],
        capture_output=True, text=True, creationflags=NO_WINDOW
    )
    if result.returncode == 0:
        log("Authtoken saved. Starting tunnel\u2026", "#22c55e")
    else:
        log(f"ngrok config error: {result.stdout.strip() or result.stderr.strip()}", "#f87171")
    start_tunnel()
def _kill_stray_ngrok():
    """Kill any ngrok processes already running (from previous sessions)."""
    try:
        result = subprocess.run(
            ["taskkill", "/F", "/IM", "ngrok.exe"],
            capture_output=True, text=True, creationflags=NO_WINDOW
        )
        if "SUCCESS" in result.stdout:
            log("Killed existing ngrok process.", "#facc15")
    except Exception:
        pass
    import time; time.sleep(0.8)   # give OS time to release the port

def start_tunnel():
    global tunnel_proc, ngrok_url
    ngrok = shutil.which("ngrok") or (
        os.path.join(APP_DIR, "ngrok.exe") if os.path.exists(os.path.join(APP_DIR, "ngrok.exe")) else None
    )
    if not ngrok:
        log("ngrok not found. Download ngrok.exe from https://ngrok.com/download", "#f87171")
        log("Drop ngrok.exe in the same folder as this launcher.", "#facc15")
        return
    if tunnel_proc and tunnel_proc.poll() is None:
        log("Tunnel is already running.", "#facc15")
        return
    # Kill any stray ngrok left over from a previous session
    _kill_stray_ngrok()
    ngrok_url = None
    root.after(0, _refresh_tunnel_url_btn)
    log("Starting ngrok tunnel on port 5001…", "#60a5fa")
    tunnel_proc = subprocess.Popen(
        [ngrok, "http", "5001", "--log=stdout"],
        cwd=APP_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        creationflags=NO_WINDOW,
    )
    threading.Thread(
        target=stream_output,
        args=(tunnel_proc, "TUNNEL", "#c4b5fd"),
        kwargs={"url_hook": _parse_ngrok_url},
        daemon=True,
    ).start()
    threading.Thread(target=watch_tunnel, daemon=True).start()
    update_lights()

def watch_tunnel():
    global tunnel_proc, ngrok_url
    if tunnel_proc:
        tunnel_proc.wait()
        log("Tunnel stopped.", "#f87171")
        ngrok_url = None
        root.after(0, _refresh_tunnel_url_btn)
        update_lights()

def stop_tunnel():
    global tunnel_proc, ngrok_url
    if tunnel_proc and tunnel_proc.poll() is None:
        log("Stopping tunnel…", "#facc15")
        tunnel_proc.terminate()
        tunnel_proc = None
    else:
        log("Tunnel is not running.", TXT_DIM)
    ngrok_url = None
    root.after(0, _refresh_tunnel_url_btn)
    update_lights()

# ── git pull ──────────────────────────────────────────────────────────────────

def pull_changes():
    def _pull():
        log("Pulling latest changes from GitHub…", "#60a5fa")
        git = shutil.which("git") or "git"
        result = subprocess.run(
            [git, "pull"],
            cwd=APP_DIR,
            capture_output=True,
            text=True,
            creationflags=NO_WINDOW,
        )
        for line in (result.stdout + result.stderr).splitlines():
            if line.strip():
                log(f"GIT: {line}", "#e0c97a")
        if result.returncode == 0:
            log("Pull complete.", "#22c55e")
        else:
            log("Git pull failed — see output above.", "#f87171")
    threading.Thread(target=_pull, daemon=True).start()

# ── status lights ─────────────────────────────────────────────────────────────

def update_lights():
    s_on = server_proc is not None and server_proc.poll() is None
    t_on = tunnel_proc is not None and tunnel_proc.poll() is None
    root.after(0, lambda: _refresh_lights(s_on, t_on))

def _refresh_lights(s_on, t_on):
    server_canvas.itemconfig("light", fill=ON if s_on else OFF)
    tunnel_canvas.itemconfig("light", fill=ON if t_on else OFF)
    server_label.config(text="Server  " + ("RUNNING" if s_on else "STOPPED"), fg=ON if s_on else OFF)
    tunnel_label.config(text="Tunnel  " + ("RUNNING" if t_on else "STOPPED"), fg=ON if t_on else OFF)
    local_url_btn.config(state=tk.NORMAL if s_on else tk.DISABLED,
                         fg="#38bdf8" if s_on else TXT_DIM)

# ── log poller ────────────────────────────────────────────────────────────────

def poll_log():
    while not log_queue.empty():
        msg, colour = log_queue.get_nowait()
        log_box.config(state=tk.NORMAL)
        log_box.insert(tk.END, msg + "\n", colour)
        log_box.tag_config(colour, foreground=colour)
        log_box.see(tk.END)
        log_box.config(state=tk.DISABLED)
    root.after(150, poll_log)

def clear_log():
    log_box.config(state=tk.NORMAL)
    log_box.delete("1.0", tk.END)
    log_box.config(state=tk.DISABLED)

# ── on close ─────────────────────────────────────────────────────────────────

def on_close():
    stop_server()
    stop_tunnel()
    root.destroy()

# ─────────────────────────────────────────────────────────────────────────────
# GUI BUILD
# ─────────────────────────────────────────────────────────────────────────────

root = tk.Tk()
root.title("Mental Health Resources — Launcher")
root.configure(bg=BG)
root.resizable(True, True)
root.minsize(620, 500)
root.protocol("WM_DELETE_WINDOW", on_close)

# ── header ────────────────────────────────────────────────────────────────────
header = tk.Frame(root, bg=ACCENT, pady=12)
header.pack(fill=tk.X)
tk.Label(header, text="Mental Health Resources", font=("Segoe UI", 16, "bold"),
         bg=ACCENT, fg="white").pack()
tk.Label(header, text="Local Launcher & Control Panel", font=("Segoe UI", 9),
         bg=ACCENT, fg="#ddd6fe").pack()

# ── status row ────────────────────────────────────────────────────────────────
status_frame = tk.Frame(root, bg=PANEL, pady=10)
status_frame.pack(fill=tk.X, padx=0)

def make_light(parent):
    c = tk.Canvas(parent, width=18, height=18, bg=PANEL, highlightthickness=0)
    c.create_oval(2, 2, 16, 16, fill=OFF, outline="", tags="light")
    return c

# server status
s_row = tk.Frame(status_frame, bg=PANEL)
s_row.pack(side=tk.LEFT, padx=30, pady=2)
server_canvas = make_light(s_row)
server_canvas.pack(side=tk.LEFT, padx=(0, 6))
server_label = tk.Label(s_row, text="Server:  STOPPED", font=("Segoe UI", 10, "bold"),
                        bg=PANEL, fg=OFF)
server_label.pack(side=tk.LEFT)

# tunnel status
t_row = tk.Frame(status_frame, bg=PANEL)
t_row.pack(side=tk.LEFT, padx=30, pady=2)
tunnel_canvas = make_light(t_row)
tunnel_canvas.pack(side=tk.LEFT, padx=(0, 6))
tunnel_label = tk.Label(t_row, text="Tunnel:  STOPPED", font=("Segoe UI", 10, "bold"),
                        bg=PANEL, fg=OFF)
tunnel_label.pack(side=tk.LEFT)



# ── button row ────────────────────────────────────────────────────────────────
def btn(parent, text, cmd, colour, width=14):
    b = tk.Button(parent, text=text, command=cmd, bg=colour, fg=BTN_FG,
                  font=("Segoe UI", 9, "bold"), relief=tk.FLAT,
                  activebackground=colour, activeforeground=BTN_FG,
                  cursor="hand2", width=width, pady=7)
    b.pack(side=tk.LEFT, padx=6, pady=10)
    return b

# ── URL panel ────────────────────────────────────────────────────────────────
url_panel = tk.Frame(root, bg="#162032", pady=8)
url_panel.pack(fill=tk.X)

tk.Label(url_panel, text="Open in browser:", font=("Segoe UI", 8),
         bg="#162032", fg=TXT_DIM).pack(side=tk.LEFT, padx=(16, 8))

LOCAL_URL = "http://127.0.0.1:5001"
local_url_btn = tk.Button(
    url_panel, text=f"\U0001f5a5  {LOCAL_URL}",
    font=("Segoe UI", 9, "underline"), bg="#162032", fg=TXT_DIM,
    relief=tk.FLAT, activebackground="#162032", activeforeground="#38bdf8",
    cursor="hand2", state=tk.DISABLED, bd=0,
    command=lambda: webbrowser.open(LOCAL_URL),
)
local_url_btn.pack(side=tk.LEFT, padx=4)

tk.Frame(url_panel, bg=ACCENT, width=1).pack(side=tk.LEFT, padx=12, pady=2, fill=tk.Y)

tunnel_url_btn = tk.Button(
    url_panel, text="Tunnel URL — not running",
    font=("Segoe UI", 9, "underline"), bg="#162032", fg=TXT_DIM,
    relief=tk.FLAT, activebackground="#162032", activeforeground="#38bdf8",
    cursor="hand2", state=tk.DISABLED, bd=0,
)
tunnel_url_btn.pack(side=tk.LEFT, padx=4)

# ── ngrok authtoken row ────────────────────────────────────────────────────────────
token_row = tk.Frame(root, bg="#1a1a2e", pady=6)
token_row.pack(fill=tk.X, padx=0)

tk.Label(token_row, text="ngrok Authtoken:", font=("Segoe UI", 8),
         bg="#1a1a2e", fg=TXT_DIM).pack(side=tk.LEFT, padx=(16, 6))

token_var = tk.StringVar()
token_entry = tk.Entry(
    token_row, textvariable=token_var, font=("Segoe UI", 9),
    bg="#2a2a3e", fg="#e2e8f0", insertbackground="white",
    relief=tk.FLAT, width=48, show="*"
)
token_entry.pack(side=tk.LEFT, padx=(0, 6), ipady=4)
token_entry.insert(0, _load_saved_token())

tk.Button(
    token_row, text="Save & Start Tunnel",
    command=lambda: threading.Thread(target=_apply_authtoken_and_start, daemon=True).start(),
    bg="#7c3aed", fg="white", font=("Segoe UI", 8, "bold"),
    relief=tk.FLAT, cursor="hand2", pady=4, padx=8,
).pack(side=tk.LEFT, padx=2)

tk.Button(
    token_row, text="Get free token ↗",
    command=lambda: webbrowser.open("https://dashboard.ngrok.com/get-started/your-authtoken"),
    bg="#162032", fg="#38bdf8", font=("Segoe UI", 8),
    relief=tk.FLAT, cursor="hand2", pady=4, padx=6,
).pack(side=tk.LEFT, padx=2)

tk.Button(
    token_row, text="\U0001f441",
    command=lambda: token_entry.config(show="" if token_entry.cget("show") == "*" else "*"),
    bg="#1a1a2e", fg=TXT_DIM, font=("Segoe UI", 8),
    relief=tk.FLAT, cursor="hand2", pady=4,
).pack(side=tk.LEFT)

# ── button row ────────────────────────────────────────────────────────────────
btn_frame = tk.Frame(root, bg=BG)
btn_frame.pack(fill=tk.X, padx=14)

btn(btn_frame, "▶  Start Server",  start_server,  BTN_START)
btn(btn_frame, "■  Stop Server",   stop_server,   BTN_STOP)

sep = tk.Frame(btn_frame, bg=ACCENT, width=2)
sep.pack(side=tk.LEFT, pady=8, padx=4)

btn(btn_frame, "⚡  Start Tunnel",  start_tunnel,  "#7c3aed")
btn(btn_frame, "■  Stop Tunnel",   stop_tunnel,   BTN_STOP)

sep2 = tk.Frame(btn_frame, bg=ACCENT, width=2)
sep2.pack(side=tk.LEFT, pady=8, padx=4)

btn(btn_frame, "⬇  Pull Updates",  pull_changes,  BTN_PULL)
btn(btn_frame, "🗑  Clear Log",     clear_log,     "#334155", width=11)

# ── log window ────────────────────────────────────────────────────────────────
log_frame = tk.Frame(root, bg=BG)
log_frame.pack(fill=tk.BOTH, expand=True, padx=14, pady=(0, 14))

tk.Label(log_frame, text="Console Output", font=("Segoe UI", 8),
         bg=BG, fg=TXT_DIM).pack(anchor=tk.W)

log_box = scrolledtext.ScrolledText(
    log_frame, bg=LOG_BG, fg=LOG_FG, font=("Cascadia Code", 9),
    insertbackground=LOG_FG, state=tk.DISABLED, relief=tk.FLAT,
    wrap=tk.WORD, padx=10, pady=8
)
log_box.pack(fill=tk.BOTH, expand=True)

# ── kick off ─────────────────────────────────────────────────────────────────
log("Launcher ready.  Press  ▶ Start Server  to begin.", "#60a5fa")
log(f"App directory: {APP_DIR}", TXT_DIM)
poll_log()
root.mainloop()
