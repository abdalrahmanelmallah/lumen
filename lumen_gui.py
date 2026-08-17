#!/usr/bin/env python3
"""Lumen Studio — polished desktop IDE for the Lumen language."""

import os
import io
import re
import contextlib
import tkinter as tk
from tkinter import font as tkfont
from tkinter import filedialog, messagebox
import lumen as sm

DEFAULT_CODE = 'run("Hello World")\n'

# ── Professional dark palette ────────────────────────────────────────────────
BG = "#0d1117"
SURFACE = "#111820"
SURFACE_2 = "#161d26"
SURFACE_3 = "#1b2430"
BORDER = "#263241"
BORDER_HOVER = "#344457"
TEXT = "#e6edf3"
MUTED = "#8b98a7"
SUBTLE = "#5f6d7c"
ACCENT = "#7c5cff"
ACCENT_HOVER = "#9277ff"
ACCENT_DARK = "#332765"
GREEN = "#39d98a"
RED = "#ff5c68"
YELLOW = "#f5c451"
EDITOR_BG = "#0b1016"
EDITOR_GUTTER = "#0b1016"
TERM_BG = "#080c11"

C_COMMENT = "#6a9955"
C_KEYWORD = "#c586c0"
C_STRING = "#ce9178"
C_NUMBER = "#b5cea8"
C_FUNC = "#dcdcaa"
C_IDENT = "#9cdcfe"
C_BOOL = "#569cd6"

KEYWORDS = {
    "let","if","elif","else","while","for","in","fn","return",
    "import","as","break","continue","try","catch","class","new"
}
BOOLS = {"true", "false"}
TOKEN_RE = re.compile(r"""
      (?P<COMMENT>\#[^\n]*)
    | (?P<FSTRING>f"(?:[^"\\]|\\.)*")
    | (?P<STRING>"(?:[^"\\]|\\.)*")
    | (?P<NUMBER>\b\d+(?:\.\d+)?\b)
    | (?P<CALL>\b[A-Za-z_][A-Za-z0-9_]*(?=\s*\())
    | (?P<ID>\b[A-Za-z_][A-Za-z0-9_]*\b)
""", re.VERBOSE)

FILE_ICONS = {
    ".lu": ("◇", "#a78bfa"),
    ".py": ("Py", "#4ec9b0"),
    ".js": ("JS", "#f5c451"),
    ".ts": ("TS", "#4aa3ff"),
    ".json": ("{}", "#f5c451"),
    ".md": ("M", "#9aa7b5"),
    ".txt": ("T", "#9aa7b5"),
    ".png": ("IMG", "#67e8f9"),
    ".jpg": ("IMG", "#67e8f9"),
    ".jpeg": ("IMG", "#67e8f9"),
    ".gif": ("IMG", "#67e8f9"),
    ".svg": ("SVG", "#f472b6"),
    ".html": ("<>", "#f97316"),
    ".css": ("#", "#60a5fa"),
}

class TabState:
    def __init__(self, code="", filepath=None, encoding="utf-8"):
        self.code = code
        self.filepath = filepath
        self.modified = False
        self.encoding = encoding

    @property
    def label(self):
        name = os.path.basename(self.filepath) if self.filepath else "untitled.lu"
        return ("● " if self.modified else "") + name

class LineNumbers(tk.Canvas):
    def __init__(self, master, text_widget):
        super().__init__(master, width=54, bg=EDITOR_GUTTER,
                         highlightthickness=0, bd=0)
        self.text_widget = text_widget

    def redraw(self):
        self.delete("all")
        i = self.text_widget.index("@0,0")
        while True:
            info = self.text_widget.dlineinfo(i)
            if info is None:
                break
            y = info[1]
            n = i.split(".")[0]
            active = n == self.text_widget.index("insert").split(".")[0]
            self.create_text(46, y, anchor="ne", text=n,
                             fill="#c2cad3" if active else "#4f5c6b",
                             font=("Menlo", 11))
            i = self.text_widget.index(f"{i}+1line")

class RoundedButton(tk.Canvas):
    """A real rounded button drawn on a canvas; works consistently on macOS/Windows/Linux."""
    def __init__(self, master, text, command, width=100, height=34,
                 accent=False, **kwargs):
        super().__init__(master, width=width, height=height,
                         highlightthickness=0, bd=0, bg=kwargs.pop("bg", SURFACE),
                         cursor="hand2")
        self.text = text
        self.command = command
        self.w = width
        self.h = height
        self.accent = accent
        self.normal = ACCENT if accent else SURFACE_3
        self.hover = ACCENT_HOVER if accent else "#243142"
        self.text_color = "#ffffff"
        self._draw(self.normal)
        self.bind("<Enter>", lambda e: self._draw(self.hover))
        self.bind("<Leave>", lambda e: self._draw(self.normal))
        self.bind("<Button-1>", lambda e: self.command())

    def _draw(self, fill):
        self.delete("all")
        r = 9
        self.create_rounded_rect(1, 1, self.w-1, self.h-1, r, fill, BORDER if not self.accent else fill)
        self.create_text(self.w/2, self.h/2, text=self.text,
                         fill=self.text_color, font=("SF Pro Text", 10, "bold"))

    def create_rounded_rect(self, x1, y1, x2, y2, r, fill, outline):
        pts = [x1+r,y1, x2-r,y1, x2,y1, x2,y1+r,
               x2,y2-r, x2,y2, x2-r,y2, x1+r,y2,
               x1,y2, x1,y2-r, x1,y1+r, x1,y1]
        self.create_polygon(pts, smooth=True, fill=fill, outline=outline, width=1)

class LumenGUI(tk.Tk):
    SPINNER_FRAMES = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]

    def __init__(self):
        super().__init__()
        self.title("Lumen Studio")
        self.geometry("1360x840")
        self.minsize(980, 620)
        self.configure(bg=BG)

        self.tabs = [TabState(DEFAULT_CODE)]
        self.current_tab = 0
        self._current_folder = None
        self._files = []
        self._scroll_job = None
        self._suppress_modified = False

        self._build_header()
        self._build_main()
        self._build_terminal()
        self._load_tab(0)
        self.editor.focus_set()

        self.bind_all("<Command-Return>", lambda e: self.run_code())
        self.bind_all("<Control-Return>", lambda e: self.run_code())
        self.bind_all("<Command-n>", lambda e: self.new_tab())
        self.bind_all("<Control-n>", lambda e: self.new_tab())
        self.bind_all("<Command-o>", lambda e: self.open_file())
        self.bind_all("<Control-o>", lambda e: self.open_file())
        self.bind_all("<Command-s>", lambda e: self.save_file())
        self.bind_all("<Control-s>", lambda e: self.save_file())
        self.bind_all("<Command-Shift-S>", lambda e: self.save_file_as())
        self.bind_all("<Control-Shift-S>", lambda e: self.save_file_as())
        self.bind_all("<Command-w>", lambda e: self.close_tab())
        self.bind_all("<Control-w>", lambda e: self.close_tab())

    def _build_header(self):
        header = tk.Frame(self, bg=SURFACE, height=62, highlightbackground=BORDER, highlightthickness=1)
        header.pack(fill="x")
        header.pack_propagate(False)

        brand = tk.Frame(header, bg=SURFACE)
        brand.pack(side="left", padx=18)
        tk.Label(brand, text="◆", bg=SURFACE, fg=ACCENT,
                 font=("SF Pro Display", 17, "bold")).pack(side="left", padx=(0,8))
        title = tk.Frame(brand, bg=SURFACE)
        title.pack(side="left")
        tk.Label(title, text="LUMEN", bg=SURFACE, fg=TEXT,
                 font=("SF Pro Display", 12, "bold")).pack(anchor="w")
        tk.Label(title, text="LANGUAGE STUDIO", bg=SURFACE, fg=SUBTLE,
                 font=("SF Pro Text", 8, "bold")).pack(anchor="w")

        actions = tk.Frame(header, bg=SURFACE)
        actions.pack(side="right", padx=14)
        RoundedButton(actions, "＋  New", self.new_tab, 82, 34, bg=SURFACE).pack(side="left", padx=4)
        RoundedButton(actions, "↥  Open", self.open_file, 86, 34, bg=SURFACE).pack(side="left", padx=4)
        RoundedButton(actions, "↓  Save", self.save_file, 86, 34, bg=SURFACE).pack(side="left", padx=4)
        RoundedButton(actions, "▶  Run", self.run_code, 92, 34, True, bg=SURFACE).pack(side="left", padx=(10,0))

    def _build_main(self):
        outer = tk.Frame(self, bg=BG)
        outer.pack(fill="both", expand=True)

        self.sidebar = tk.Frame(outer, bg=SURFACE, width=240,
                                highlightbackground=BORDER, highlightthickness=1)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        top = tk.Frame(self.sidebar, bg=SURFACE, height=52)
        top.pack(fill="x")
        top.pack_propagate(False)
        tk.Label(top, text="EXPLORER", bg=SURFACE, fg=MUTED,
                 font=("SF Pro Text", 9, "bold")).pack(side="left", padx=14)
        b = tk.Label(top, text="＋", bg=SURFACE, fg=MUTED,
                     font=("SF Pro Text", 17), cursor="hand2")
        b.pack(side="right", padx=12)
        b.bind("<Button-1>", lambda e: self._browse_folder())
        b.bind("<Enter>", lambda e: b.config(fg=TEXT))
        b.bind("<Leave>", lambda e: b.config(fg=MUTED))

        self.folder_label = tk.Label(self.sidebar, text="NO FOLDER OPEN",
                                      bg=SURFACE_2, fg=SUBTLE, anchor="w",
                                      padx=13, font=("SF Pro Text", 8, "bold"), height=2)
        self.folder_label.pack(fill="x")

        self.file_list = tk.Listbox(
            self.sidebar, bg=SURFACE, fg=TEXT,
            selectbackground=ACCENT_DARK, selectforeground=TEXT,
            relief="flat", borderwidth=0, highlightthickness=0,
            font=("SF Pro Text", 10), activestyle="none",
            cursor="hand2", exportselection=False
        )
        self.file_list.pack(fill="both", expand=True, padx=6, pady=8)
        self.file_list.bind("<Double-Button-1>", self._on_file_dblclick)
        self.file_list.bind("<Return>", self._on_file_dblclick)
        self.file_list.bind("<MouseWheel>", self._smooth_list_scroll)
        self.file_list.bind("<Button-4>", lambda e: self._scroll_units(self.file_list, -1))
        self.file_list.bind("<Button-5>", lambda e: self._scroll_units(self.file_list, 1))

        editor_side = tk.Frame(outer, bg=EDITOR_BG)
        editor_side.pack(side="left", fill="both", expand=True)

        self.tabbar = tk.Frame(editor_side, bg=SURFACE_2, height=42)
        self.tabbar.pack(fill="x")
        self.tabbar.pack_propagate(False)

        editor_wrap = tk.Frame(editor_side, bg=BORDER)
        editor_wrap.pack(fill="both", expand=True, padx=1, pady=1)
        inner = tk.Frame(editor_wrap, bg=EDITOR_BG)
        inner.pack(fill="both", expand=True)

        mono = tkfont.Font(family="Menlo", size=13)
        self.editor = tk.Text(
            inner, bg=EDITOR_BG, fg=TEXT, insertbackground=TEXT,
            selectbackground="#263852", font=mono, relief="flat",
            padx=14, pady=14, wrap="none", undo=True,
            borderwidth=0, highlightthickness=0, spacing1=1, spacing3=1
        )
        self.linenumbers = LineNumbers(inner, self.editor)
        self.linenumbers.pack(side="left", fill="y")
        self.editor.pack(side="left", fill="both", expand=True)

        self.editor.bind("<KeyRelease>", self._on_key)
        self.editor.bind("<<Modified>>", self._on_modified)
        self.editor.bind("<Configure>", lambda e: self.linenumbers.redraw())
        # Mouse/trackpad scrolling.  macOS trackpads often report very small
        # delta values (1/-1), while a mouse wheel commonly reports 120/-120.
        # Handle both instead of converting small deltas to zero.
        self.editor.bind("<MouseWheel>", self._smooth_editor_scroll)
        self.editor.bind("<Button-4>", lambda e: self._scroll_units(self.editor, -1))
        self.editor.bind("<Button-5>", lambda e: self._scroll_units(self.editor, 1))
        self.linenumbers.bind("<MouseWheel>", self._smooth_editor_scroll)
        self.linenumbers.bind("<Button-4>", lambda e: self._scroll_units(self.editor, -1))
        self.linenumbers.bind("<Button-5>", lambda e: self._scroll_units(self.editor, 1))

        for kind, colour in [
            ("comment",C_COMMENT),("string",C_STRING),("number",C_NUMBER),
            ("keyword",C_KEYWORD),("bool",C_BOOL),("call",C_FUNC),("ident",C_IDENT)
        ]:
            self.editor.tag_config(kind, foreground=colour)

    def _build_terminal(self):
        wrap = tk.Frame(self, bg=BORDER, height=190)
        wrap.pack(fill="x", side="bottom")
        wrap.pack_propagate(False)

        hdr = tk.Frame(wrap, bg=SURFACE_2, height=38)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        left = tk.Frame(hdr, bg=SURFACE_2)
        left.pack(side="left", padx=12)
        self.status_dot = tk.Canvas(left, width=9, height=9, bg=SURFACE_2, highlightthickness=0)
        self.status_dot_id = self.status_dot.create_oval(1,1,8,8,fill=SUBTLE,outline="")
        self.status_dot.pack(side="left", padx=(0,8))
        tk.Label(left, text="TERMINAL", bg=SURFACE_2, fg=MUTED,
                 font=("SF Pro Text",9,"bold")).pack(side="left")

        clear = tk.Label(hdr, text="Clear", bg=SURFACE_2, fg=MUTED,
                         font=("SF Pro Text",9), cursor="hand2")
        clear.pack(side="right", padx=14)
        clear.bind("<Button-1>", lambda e: self.clear_output())
        clear.bind("<Enter>", lambda e: clear.config(fg=TEXT))
        clear.bind("<Leave>", lambda e: clear.config(fg=MUTED))

        self.output = tk.Text(
            wrap, bg=TERM_BG, fg=TEXT, insertbackground=TEXT,
            font=("Menlo",11), relief="flat", padx=14, pady=10,
            height=7, state="disabled", wrap="word", borderwidth=0,
            highlightthickness=0
        )
        self.output.pack(fill="both", expand=True)
        self.output.tag_config("ok", foreground=GREEN)
        self.output.tag_config("err", foreground=RED)
        self.output.tag_config("prompt", foreground=ACCENT, font=("Menlo",11,"bold"))
        self.output.tag_config("dim", foreground=SUBTLE)
        self.output.tag_config("cursor", foreground=TEXT)
        self.output.bind("<MouseWheel>", self._smooth_output_scroll)
        self.output.bind("<Button-4>", lambda e: self._scroll_units(self.output, -1))
        self.output.bind("<Button-5>", lambda e: self._scroll_units(self.output, 1))

        self._blink_state = True
        self._cursor_active = False
        self._blink_cursor()

    # ── Smooth scrolling ─────────────────────────────────────────────────────
    def _scroll_units(self, widget, units):
        """Scroll reliably on macOS, Windows and X11."""
        widget.yview_scroll(int(units), "units")
        if widget is self.editor:
            self.linenumbers.redraw()

    def _smooth_scroll(self, widget, units):
        # A small animated scroll feels much better than one large jump.
        # The important part is that every wheel event becomes at least one
        # unit; the old implementation turned macOS delta values like 1 into 0.
        if self._scroll_job:
            try:
                self.after_cancel(self._scroll_job)
            except tk.TclError:
                pass
            self._scroll_job = None

        direction = 1 if units > 0 else -1
        steps = max(1, min(5, abs(int(units))))

        def move(n):
            if n <= 0:
                self._scroll_job = None
                return
            widget.yview_scroll(direction, "units")
            if widget is self.editor:
                self.linenumbers.redraw()
            self._scroll_job = self.after(10, lambda: move(n - 1))

        move(steps)

    def _wheel_units(self, event):
        delta = getattr(event, "delta", 0)
        if delta:
            # macOS trackpads: usually tiny values. Windows/macOS mice: often 120.
            if abs(delta) < 30:
                return -1 if delta > 0 else 1
            return -max(1, min(5, abs(delta) // 120)) if delta > 0 else max(1, min(5, abs(delta) // 120))
        return 0

    def _smooth_list_scroll(self, e):
        units = self._wheel_units(e)
        if units:
            self._smooth_scroll(self.file_list, units)
        return "break"

    def _smooth_editor_scroll(self, e):
        units = self._wheel_units(e)
        if units:
            self._smooth_scroll(self.editor, units)
        return "break"

    def _smooth_output_scroll(self, e):
        units = self._wheel_units(e)
        if units:
            self._smooth_scroll(self.output, units)
        return "break"

    # ── Tabs ──────────────────────────────────────────────────────────────────
    def _rebuild_tabbar(self):
        for w in self.tabbar.winfo_children():
            w.destroy()
        for i, tab in enumerate(self.tabs):
            active = i == self.current_tab
            bg = SURFACE_3 if active else SURFACE_2
            fg = TEXT if active else MUTED
            frame = tk.Frame(self.tabbar, bg=bg, height=42)
            frame.pack(side="left", fill="y", padx=(0,1))
            if active:
                tk.Frame(frame, bg=ACCENT, height=2).pack(fill="x")
            name = tab.label
            if len(name) > 24:
                name = name[:22] + "…"
            lbl = tk.Label(frame, text=name, bg=bg, fg=fg,
                           font=("SF Pro Text",10,"bold" if active else "normal"),
                           padx=13, pady=6, cursor="hand2")
            lbl.pack(side="left")
            close = tk.Label(frame, text="×", bg=bg, fg=SUBTLE,
                             font=("SF Pro Text",12), padx=7, cursor="hand2")
            close.pack(side="left")
            idx = i
            for w in (frame,lbl):
                w.bind("<Button-1>", lambda e,n=idx:self._switch_tab(n))
            close.bind("<Button-1>", lambda e,n=idx:self.close_tab(n))
            close.bind("<Enter>", lambda e,w=close:w.config(fg=RED))
            close.bind("<Leave>", lambda e,w=close:w.config(fg=SUBTLE))
        plus = tk.Label(self.tabbar, text="＋", bg=SURFACE_2, fg=SUBTLE,
                        font=("SF Pro Text",15), padx=12, cursor="hand2")
        plus.pack(side="left", fill="y")
        plus.bind("<Button-1>", lambda e:self.new_tab())
        plus.bind("<Enter>", lambda e:plus.config(fg=TEXT))
        plus.bind("<Leave>", lambda e:plus.config(fg=SUBTLE))

    def _save_tab_state(self):
        self.tabs[self.current_tab].code = self.editor.get("1.0","end-1c")

    def _load_tab(self, index):
        self.current_tab = index
        tab = self.tabs[index]
        self._suppress_modified = True
        self.editor.delete("1.0","end")
        self.editor.insert("1.0",tab.code)
        self.editor.edit_modified(False)
        # Each tab gets a clean undo history. The Text widget's undo stack
        # is shared across all tabs since they reuse one widget; without
        # resetting it here, Ctrl+Z after switching tabs can undo edits
        # belonging to a *different* tab and corrupt its content.
        self.editor.edit_reset()
        self._suppress_modified = False
        self._highlight()
        self.linenumbers.redraw()
        title = os.path.basename(tab.filepath) if tab.filepath else "untitled.lu"
        self.title(f"Lumen Studio — {title}")
        self._rebuild_tabbar()

    def _switch_tab(self,index):
        if index == self.current_tab:return
        self._save_tab_state()
        self._load_tab(index)
        self.editor.focus_set()

    def new_tab(self, code=None, filepath=None):
        self._save_tab_state()
        self.tabs.append(TabState(code if code is not None else DEFAULT_CODE,filepath))
        self._load_tab(len(self.tabs)-1)
        self.editor.focus_set()

    def close_tab(self,index=None):
        index = self.current_tab if index is None else index
        tab=self.tabs[index]
        if tab.modified and not messagebox.askyesno("Unsaved changes",
            f"'{os.path.basename(tab.filepath) if tab.filepath else 'untitled.lu'}' has unsaved changes.\nClose it anyway?"):
            return
        if len(self.tabs)==1:
            self.tabs[0]=TabState(DEFAULT_CODE)
            self._load_tab(0); return
        self.tabs.pop(index)
        self._load_tab(min(index,len(self.tabs)-1))

    # ── Editor ────────────────────────────────────────────────────────────────
    def _on_modified(self,event=None):
        # <<Modified>> only fires on real content changes (insert/delete),
        # never on plain cursor movement, so it's the correct place to mark
        # a tab dirty — unlike KeyRelease, which also fires for arrow keys,
        # Home/End, etc. and would falsely flag untouched tabs as changed.
        if self.editor.edit_modified():
            self.editor.edit_modified(False)
            if not self._suppress_modified and not self.tabs[self.current_tab].modified:
                self.tabs[self.current_tab].modified=True
                self._rebuild_tabbar()
        self.linenumbers.redraw()

    def _on_key(self,event=None):
        self._highlight()
        self.linenumbers.redraw()

    def _highlight(self):
        for tag in ("comment","string","number","keyword","bool","call","ident"):
            self.editor.tag_remove(tag,"1.0","end")
        text=self.editor.get("1.0","end-1c")
        for m in TOKEN_RE.finditer(text):
            kind=m.lastgroup
            start=f"1.0+{m.start()}c"; end=f"1.0+{m.end()}c"
            if kind in ("STRING","FSTRING"): self.editor.tag_add("string",start,end)
            elif kind=="COMMENT": self.editor.tag_add("comment",start,end)
            elif kind=="NUMBER": self.editor.tag_add("number",start,end)
            elif kind=="CALL": self.editor.tag_add("call",start,end)
            elif kind=="ID":
                word=m.group()
                if word in KEYWORDS:self.editor.tag_add("keyword",start,end)
                elif word in BOOLS:self.editor.tag_add("bool",start,end)

    # ── File recognition / browser ───────────────────────────────────────────
    def _file_display(self,name):
        ext=os.path.splitext(name)[1].lower()
        icon,_=FILE_ICONS.get(ext,("FILE","#9aa7b5"))
        return f"  {icon:<4} {name}"

    def _browse_folder(self):
        folder=filedialog.askdirectory(title="Open Project Folder")
        if folder:self._load_folder(folder)

    def _load_folder(self,folder):
        self._current_folder=folder
        self.file_list.delete(0,"end")
        try:
            entries=sorted(
                f for f in os.listdir(folder)
                if not f.startswith(".") and os.path.isfile(os.path.join(folder,f))
            )
        except OSError: entries=[]
        self._files=entries
        for name in entries:self.file_list.insert("end",self._file_display(name))
        base=os.path.basename(folder) or folder
        self.folder_label.config(text=f"  {base.upper()}  •  {len(entries)} FILES")

    def _on_file_dblclick(self,event=None):
        sel=self.file_list.curselection()
        if not sel or not self._current_folder:return
        name=self._files[sel[0]]
        path=os.path.join(self._current_folder,name)
        if not os.path.isfile(path):return
        if not self._is_text_file(path):
            messagebox.showinfo("File recognized",
                f"{name}\n\nThis file is recognized as a binary/media file and is not opened in the code editor.")
            return
        self._open_path(path)

    def _is_text_file(self,path):
        ext=os.path.splitext(path)[1].lower()
        return ext in {".lu",".py",".js",".ts",".json",".md",".txt",".html",".css",".xml",".yaml",".yml",".toml",".sh",".c",".h",".cpp",".java"}

    # Try a sequence of encodings so that real-world files (Windows/Notepad
    # saves, BOM markers, smart quotes, accented characters, etc.) always
    # load their actual content instead of failing silently and leaving
    # whatever was previously in the editor on screen.
    # NOTE: "utf-8-sig" successfully decodes plain UTF-8 files too (it just
    # strips a BOM if one happens to be present), so it must only be picked
    # when the file actually starts with a BOM — otherwise round-tripping
    # a normal UTF-8 file through save would incorrectly stamp a BOM onto
    # it that was never there.
    _BOM = b"\xef\xbb\xbf"
    _FALLBACK_ENCODINGS = ("utf-8", "cp1252", "latin-1")

    def _read_text_file(self, path):
        with open(path, "rb") as f:
            raw = f.read()
        if raw.startswith(self._BOM):
            return raw.decode("utf-8-sig"), "utf-8-sig"
        for enc in self._FALLBACK_ENCODINGS:
            try:
                return raw.decode(enc), enc
            except (UnicodeDecodeError, LookupError):
                continue
        # Last resort: never fail outright — decode what we can so the
        # user at least sees the real bytes instead of nothing/default code.
        return raw.decode("utf-8", errors="replace"), "utf-8"

    def _open_path(self,path):
        abs_path=os.path.abspath(path)
        for i,tab in enumerate(self.tabs):
            if tab.filepath and os.path.abspath(tab.filepath)==abs_path:
                self._switch_tab(i)
                if not self.tabs[i].modified:
                    self._reload_tab_from_disk(i)
                return
        try:
            content, encoding = self._read_text_file(path)
        except OSError as e:
            messagebox.showerror("Cannot open file", str(e));return
        cur=self.tabs[self.current_tab]
        if not cur.filepath and not cur.modified and cur.code.strip()==DEFAULT_CODE.strip():
            cur.code=content;cur.filepath=path;cur.modified=False;cur.encoding=encoding
            self._load_tab(self.current_tab)
        else:
            self.new_tab(content,path)
            new_tab=self.tabs[self.current_tab]
            new_tab.modified=False;new_tab.encoding=encoding
            self._rebuild_tabbar()
        folder=os.path.dirname(path)
        if self._current_folder!=folder:self._load_folder(folder)

    def _reload_tab_from_disk(self, index):
        """Re-read the file for an already-open, unmodified tab so double-
        clicking it again always reflects the real on-disk content."""
        tab = self.tabs[index]
        if not tab.filepath or not os.path.isfile(tab.filepath):
            return
        try:
            content, encoding = self._read_text_file(tab.filepath)
        except OSError:
            return
        tab.code = content
        tab.encoding = encoding
        tab.modified = False
        if index == self.current_tab:
            self._load_tab(index)

    # ── Files ─────────────────────────────────────────────────────────────────
    def open_file(self):
        path=filedialog.askopenfilename(
            filetypes=[("Lumen files","*.lu"),("Source files","*.lu *.py *.js *.ts *.json *.md *.txt"),("All files","*.*")]
        )
        if path:self._open_path(path)

    def save_file(self):
        tab=self.tabs[self.current_tab]
        if not tab.filepath:return self.save_file_as()
        tab.code=self.editor.get("1.0","end-1c")
        encoding = getattr(tab, "encoding", "utf-8") or "utf-8"
        try:
            try:
                with open(tab.filepath,"w",encoding=encoding,newline="") as f:f.write(tab.code)
            except (LookupError,UnicodeEncodeError):
                # Original encoding can't represent the new text (e.g. user
                # typed non-Latin characters into a latin-1 file) — fall
                # back to UTF-8 rather than losing the save entirely.
                encoding="utf-8"
                with open(tab.filepath,"w",encoding=encoding,newline="") as f:f.write(tab.code)
                tab.encoding=encoding
            tab.modified=False
            self._rebuild_tabbar()
            self.title(f"Lumen Studio — {os.path.basename(tab.filepath)}")
            if self._current_folder==os.path.dirname(tab.filepath):self._load_folder(self._current_folder)
        except OSError as e:messagebox.showerror("Save failed",str(e))

    def save_file_as(self):
        path=filedialog.asksaveasfilename(defaultextension=".lu",
            filetypes=[("Lumen files","*.lu"),("All files","*.*")])
        if not path:return
        self.tabs[self.current_tab].filepath=path
        self.save_file()

    # ── Terminal ──────────────────────────────────────────────────────────────
    def clear_output(self):
        self._cursor_active=False
        self.output.config(state="normal");self.output.delete("1.0","end");self.output.config(state="disabled")
        self._set_status("idle")

    def _write_output(self,text,tag="ok"):
        self.output.config(state="normal");self.output.insert("end",text,tag);self.output.see("end");self.output.config(state="disabled")

    def _set_status(self,state):
        colours={"idle":SUBTLE,"running":YELLOW,"ok":GREEN,"err":RED}
        self.status_dot.itemconfig(self.status_dot_id,fill=colours.get(state,SUBTLE))

    def _blink_cursor(self):
        if self._cursor_active:
            self._strip_cursor()
            self.output.config(state="normal")
            if self._blink_state:self.output.insert("end","▍","cursor")
            self.output.config(state="disabled")
            self._blink_state=not self._blink_state
        self.after(500,self._blink_cursor)

    def _strip_cursor(self):
        self.output.config(state="normal")
        ranges=self.output.tag_ranges("cursor")
        if ranges:self.output.delete(ranges[0],ranges[1])
        self.output.config(state="disabled")

    def run_code(self):
        self._save_tab_state()
        self._cursor_active=False;self._strip_cursor()
        code=self.editor.get("1.0","end-1c")
        self.clear_output();self._set_status("running")
        self._write_output("  $ ","prompt");self._write_output("lumen run ","dim")
        self._spin_index=0;self._spin_start=self.output.index("end-1c")
        self._animate_spinner(code,9)

    def _animate_spinner(self,code,ticks):
        frame=self.SPINNER_FRAMES[self._spin_index%len(self.SPINNER_FRAMES)]
        self.output.config(state="normal");self.output.delete(self._spin_start,"end");self.output.insert("end",frame,"dim");self.output.config(state="disabled")
        self._spin_index+=1
        if ticks>0:self.after(45,lambda:self._animate_spinner(code,ticks-1))
        else:
            self.output.config(state="normal");self.output.delete(self._spin_start,"end");self.output.config(state="disabled")
            self._execute_and_reveal(code)

    def _execute_and_reveal(self,code):
        tab=self.tabs[self.current_tab]
        if tab.filepath:
            run_dir=os.path.dirname(os.path.abspath(tab.filepath));search_paths=[run_dir];unsaved_note=False
        else:
            run_dir=os.path.expanduser("~");search_paths=[];unsaved_note=True
        old_cwd=os.getcwd();buf=io.StringIO();error_text=None
        try:
            os.chdir(run_dir)
            with contextlib.redirect_stdout(buf):
                interp=sm.Interpreter(search_paths=search_paths);interp.run(code)
        except Exception as e:error_text=str(e)
        finally:os.chdir(old_cwd)
        out=buf.getvalue()
        self._write_output("\n","ok")
        chunks=[]
        if unsaved_note:chunks.append(("Tip: save this file first so file I/O uses its project folder.\n","dim"))
        if out:chunks.append((out,"ok"))
        elif not error_text:chunks.append(("(no output)\n","dim"))
        if error_text:chunks.append((f"Error: {error_text}\n","err"))
        self._set_status("err" if error_text else "ok")
        self._reveal(chunks,0,0)

    def _reveal(self,chunks,ci,pos):
        if ci>=len(chunks):
            self._cursor_active=True;return
        text,tag=chunks[ci];piece=text[pos:pos+3]
        if piece:
            self._write_output(piece,tag);self.after(8,lambda:self._reveal(chunks,ci,pos+3))
        else:self._reveal(chunks,ci+1,0)

if __name__=="__main__":
    app=LumenGUI()
    app.mainloop()
