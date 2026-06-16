import tkinter as tk
import json, os, sys, winreg, subprocess, threading

APP_NAME = "FolderCreator"
CONFIG_FILE = os.path.join(
    os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__)),
    "config.json"
)
AHK_FILE = os.path.join(os.environ.get("LOCALAPPDATA", ""), "FolderCreator", "hotkey.ahk")

DEFAULT = {
    "folders": ["Assets", "PSD + AI", "Ae", "Pr", "Render", "Music", "Sfx", "VO"],
    "shortcut": "ctrl+shift+f"
}

def load_cfg():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except: pass
    return DEFAULT.copy()

def save_cfg(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

def shortcut_to_ahk(sc):
    parts = sc.lower().split("+")
    mods, key = "", ""
    for p in parts:
        if p == "ctrl": mods += "^"
        elif p == "shift": mods += "+"
        elif p == "alt": mods += "!"
        elif p == "win": mods += "#"
        else: key = p
    return mods + key

def write_ahk(cfg):
    sc = shortcut_to_ahk(cfg.get("shortcut", "ctrl+shift+f"))
    folders = cfg.get("folders", [])
    folder_lines = "\n".join([
        f'        if !DirExist(path . "\\{f}")\n            DirCreate(path . "\\{f}")'
        for f in folders
    ])
    # Use WinAPI to get active Explorer path instantly — no COM enumeration delay
    ahk = f'''#Requires AutoHotkey v2.0
#SingleInstance Force

GetExplorerPath() {{
    hwnd := WinExist("A")
    if !hwnd
        return ""
    class := WinGetClass("ahk_id " hwnd)
    if (class != "CabinetWClass" && class != "ExploreWClass")
        return ""
    for w in ComObject("Shell.Application").Windows() {{
        try {{
            if (w.hwnd = hwnd)
                return w.Document.Folder.Self.Path
        }}
    }}
    return ""
}}

{sc}::
{{
    path := GetExplorerPath()
    if (path = "")
        return
{folder_lines}
}}
'''
    os.makedirs(os.path.dirname(AHK_FILE), exist_ok=True)
    with open(AHK_FILE, "w", encoding="utf-8") as f:
        f.write(ahk)

def find_ahk():
    paths = [
        r"C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe",
        r"C:\Program Files\AutoHotkey\v2\AutoHotkey32.exe",
        r"C:\Program Files\AutoHotkey\AutoHotkey.exe",
        r"C:\Program Files (x86)\AutoHotkey\AutoHotkey.exe",
    ]
    for p in paths:
        if os.path.exists(p): return p
    return None

ahk_proc = None

def start_ahk(cfg):
    global ahk_proc
    if ahk_proc:
        try: ahk_proc.terminate()
        except: pass
        ahk_proc = None
    write_ahk(cfg)
    ahk = find_ahk()
    if ahk:
        ahk_proc = subprocess.Popen([ahk, AHK_FILE])
        return True
    return False

def set_startup(enable):
    exe = f'"{sys.executable}"' if getattr(sys, 'frozen', False) else f'pythonw "{os.path.abspath(__file__)}"'
    try:
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        if enable: winreg.SetValueEx(k, APP_NAME, 0, winreg.REG_SZ, exe)
        else:
            try: winreg.DeleteValue(k, APP_NAME)
            except: pass
        winreg.CloseKey(k)
    except: pass

def is_startup():
    try:
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
        winreg.QueryValueEx(k, APP_NAME)
        winreg.CloseKey(k); return True
    except: return False


class App:
    def __init__(self):
        self.cfg = load_cfg()
        self.recording = False
        self.recorded_sc = self.cfg.get("shortcut", "ctrl+shift+f")

        self.root = tk.Tk()
        self.root.title("Folder Creator")
        self.root.geometry("460x560")
        self.root.resizable(False, False)
        self.root.configure(bg="#0F0F0F")
        self.root.protocol("WM_DELETE_WINDOW", self.root.withdraw)
        self._ui()
        ok = start_ahk(self.cfg)
        self._set_status(f"Active: {self.cfg.get('shortcut')}" if ok else "Install AutoHotkey v2!")
        self._tray()

    def _ui(self):
        BG, CARD, BORDER = "#0F0F0F", "#1C1C1C", "#2C2C2C"
        FG, MUTED, BLUE = "#F0F0F0", "#777777", "#3B82F6"

        def sep():
            tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x", padx=24, pady=12)

        h = tk.Frame(self.root, bg=BG)
        h.pack(fill="x", padx=24, pady=(20,0))
        tk.Label(h, text="Folder Creator", font=("Segoe UI",16,"bold"), bg=BG, fg=FG).pack(anchor="w")
        tk.Label(h, text="Open any folder in Explorer then press the shortcut",
                 font=("Segoe UI",9), bg=BG, fg=MUTED).pack(anchor="w", pady=(2,0))
        sep()

        sf = tk.Frame(self.root, bg=BG)
        sf.pack(fill="x", padx=24)
        tk.Label(sf, text="Shortcut", font=("Segoe UI",10,"bold"), bg=BG, fg=FG).pack(anchor="w", pady=(0,4))

        row = tk.Frame(sf, bg=BG)
        row.pack(fill="x", pady=(0,4))

        self.sc_label = tk.Label(row, text=self.recorded_sc,
                                  font=("Consolas",11), bg=CARD, fg=BLUE,
                                  anchor="w", padx=10,
                                  highlightthickness=1, highlightbackground=BORDER)
        self.sc_label.pack(side="left", fill="x", expand=True, ipady=8)

        self.record_btn = tk.Button(row, text="Record", font=("Segoe UI",9),
                                     bg=CARD, fg=MUTED, relief="flat", bd=0,
                                     cursor="hand2", padx=12, pady=8,
                                     highlightthickness=1, highlightbackground=BORDER,
                                     command=self._start_recording)
        self.record_btn.pack(side="left", padx=(6,0))

        self.apply_btn = tk.Button(row, text="Apply", font=("Segoe UI",9),
                                    bg=BLUE, fg="white", relief="flat", bd=0,
                                    cursor="hand2", padx=12, pady=8,
                                    command=self._apply_sc)
        self.apply_btn.pack(side="left", padx=(6,0))

        self.sc_hint = tk.Label(sf, text="Press Record, then press your key combination",
                                 font=("Segoe UI",8), bg=BG, fg=MUTED)
        self.sc_hint.pack(anchor="w")

        self.key_capture = tk.Entry(self.root, width=1)
        self.key_capture.place(x=-100, y=-100)
        self.key_capture.bind("<KeyPress>", self._on_key)

        sep()

        ff = tk.Frame(self.root, bg=BG)
        ff.pack(fill="both", expand=True, padx=24)

        fh = tk.Frame(ff, bg=BG)
        fh.pack(fill="x", pady=(0,8))
        tk.Label(fh, text="Folders", font=("Segoe UI",10,"bold"), bg=BG, fg=FG).pack(side="left")
        tk.Button(fh, text="+ Add", font=("Segoe UI",9), bg=CARD, fg=MUTED,
                  relief="flat", bd=0, cursor="hand2", padx=10, pady=4,
                  highlightthickness=1, highlightbackground=BORDER,
                  command=self._add).pack(side="right")

        lb_wrap = tk.Frame(ff, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        lb_wrap.pack(fill="both", expand=True)
        sb = tk.Scrollbar(lb_wrap, bg=CARD, troughcolor=CARD, bd=0, width=5)
        sb.pack(side="right", fill="y")
        self.lb = tk.Listbox(lb_wrap, bg=CARD, fg=FG, font=("Segoe UI",10),
                              selectbackground=BLUE, selectforeground="white",
                              relief="flat", bd=0, highlightthickness=0,
                              activestyle="none", yscrollcommand=sb.set)
        self.lb.pack(fill="both", expand=True, padx=2, pady=2)
        sb.config(command=self.lb.yview)
        self._refresh()

        br = tk.Frame(ff, bg=BG)
        br.pack(fill="x", pady=(8,0))
        for t, cmd in [("Delete", self._del), ("Rename", self._edit)]:
            tk.Button(br, text=t, font=("Segoe UI",9), bg=CARD, fg=MUTED,
                      relief="flat", bd=0, cursor="hand2", padx=14, pady=5,
                      highlightthickness=1, highlightbackground=BORDER,
                      command=cmd).pack(side="left", padx=(0,6))
        sep()

        bot = tk.Frame(self.root, bg=BG)
        bot.pack(fill="x", padx=24, pady=(0,20))
        self.su_var = tk.BooleanVar(value=is_startup())
        tk.Checkbutton(bot, text="Run automatically with Windows",
                       variable=self.su_var, command=self._toggle_startup,
                       font=("Segoe UI",9), bg=BG, fg=MUTED,
                       selectcolor=CARD, activebackground=BG,
                       activeforeground=FG, relief="flat").pack(side="left")
        self.status = tk.Label(bot, text="", font=("Segoe UI",9), bg=BG, fg=MUTED)
        self.status.pack(side="right")

    def _start_recording(self):
        self.recording = True
        self.sc_label.config(text="Press keys...", fg="#F0F0F0")
        self.record_btn.config(text="Cancel", command=self._cancel_recording)
        self.sc_hint.config(text="Press your key combination now... (Esc to cancel)")
        self.key_capture.focus_set()

    def _cancel_recording(self, e=None):
        self.recording = False
        self.sc_label.config(text=self.recorded_sc, fg="#3B82F6")
        self.record_btn.config(text="Record", command=self._start_recording)
        self.sc_hint.config(text="Press Record, then press your key combination")
        self.root.focus_set()

    def _on_key(self, e):
        if not self.recording: return
        if e.keysym in ("Shift_L","Shift_R","Control_L","Control_R","Alt_L","Alt_R"):
            return "break"
        if e.keysym == "Escape":
            self._cancel_recording()
            return "break"
        parts = []
        if e.state & 0x4: parts.append("ctrl")
        if e.state & 0x1: parts.append("shift")
        if e.state & 0x20000: parts.append("alt")
        key = e.keysym.lower()
        if key not in parts: parts.append(key)
        self.recorded_sc = "+".join(parts)
        self.sc_label.config(text=self.recorded_sc, fg="#3B82F6")
        self.recording = False
        self.record_btn.config(text="Record", command=self._start_recording)
        self.sc_hint.config(text="Press Apply to save")
        self.root.focus_set()
        return "break"

    def _apply_sc(self):
        if not self.recorded_sc: return
        self.cfg["shortcut"] = self.recorded_sc
        save_cfg(self.cfg)
        start_ahk(self.cfg)
        self.root.focus_set()
        self._set_status(f"Active: {self.recorded_sc}")

    def _refresh(self):
        self.lb.delete(0, tk.END)
        for f in self.cfg["folders"]:
            self.lb.insert(tk.END, f"   {f}")

    def _dialog(self, title, prompt, default=""):
        result = [None]
        d = tk.Toplevel(self.root)
        d.title(title); d.geometry("320x120")
        d.configure(bg="#0F0F0F"); d.resizable(False,False); d.grab_set()
        tk.Label(d, text=prompt, font=("Segoe UI",10), bg="#0F0F0F", fg="#F0F0F0").pack(pady=(14,5))
        v = tk.StringVar(value=default)
        e = tk.Entry(d, textvariable=v, font=("Segoe UI",11),
                     bg="#1C1C1C", fg="#F0F0F0", insertbackground="#F0F0F0",
                     relief="flat", highlightthickness=1,
                     highlightbackground="#2C2C2C", highlightcolor="#3B82F6")
        e.pack(fill="x", padx=18, ipady=6)
        e.focus(); e.select_range(0, tk.END)
        def ok(ev=None): result[0] = v.get().strip(); d.destroy()
        e.bind("<Return>", ok)
        tk.Button(d, text="OK", font=("Segoe UI",9), bg="#3B82F6", fg="white",
                  relief="flat", bd=0, command=ok, padx=18, pady=5).pack(pady=10)
        self.root.wait_window(d)
        return result[0] or None

    def _add(self):
        n = self._dialog("New Folder", "Folder name:")
        if n: self.cfg["folders"].append(n); save_cfg(self.cfg); self._refresh(); start_ahk(self.cfg)

    def _del(self):
        s = self.lb.curselection()
        if s: self.cfg["folders"].pop(s[0]); save_cfg(self.cfg); self._refresh(); start_ahk(self.cfg)

    def _edit(self):
        s = self.lb.curselection()
        if not s: return
        i = s[0]
        n = self._dialog("Rename", "New name:", self.cfg["folders"][i])
        if n: self.cfg["folders"][i] = n; save_cfg(self.cfg); self._refresh(); start_ahk(self.cfg)

    def _toggle_startup(self):
        set_startup(self.su_var.get()); self._set_status("Saved")

    def _set_status(self, msg):
        self.status.config(text=msg)
        self.root.after(5000, lambda: self.status.config(text=""))

    def _tray(self):
        try:
            import pystray
            from PIL import Image, ImageDraw
            img = Image.new("RGB", (64,64), "#3B82F6")
            d = ImageDraw.Draw(img)
            d.rectangle([14,22,50,50], fill="white")
            d.rectangle([14,14,30,24], fill="white")
            menu = pystray.Menu(
                pystray.MenuItem("Open Settings", lambda: self.root.after(0, self.root.deiconify)),
                pystray.MenuItem("Quit", lambda: self.root.after(0, self._quit))
            )
            self.icon = pystray.Icon(APP_NAME, img, "Folder Creator", menu)
            threading.Thread(target=self.icon.run, daemon=True).start()
        except: pass

    def _quit(self):
        global ahk_proc
        if ahk_proc:
            try: ahk_proc.terminate()
            except: pass
        try: self.icon.stop()
        except: pass
        self.root.destroy()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    App().run()
