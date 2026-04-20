"""
Frontend Code Quality Checker — Desktop GUI
Jalankan: python gui.py
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from datetime import datetime
import threading
import json
import os

# ── Theme ────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ── Palette ──────────────────────────────────────────────────────────
C = {
    "bg":      "#080812",
    "bg2":     "#0f0f1e",
    "bg3":     "#15152a",
    "bg4":     "#1c1c35",
    "border":  "#252540",
    "border2": "#303060",
    "text":    "#e2e2f0",
    "text2":   "#9090bb",
    "text3":   "#5c5c88",
    "blue":    "#6366f1",
    "green":   "#34d399",
    "yellow":  "#fbbf24",
    "red":     "#f87171",
    "cyan":    "#22d3ee",
}

FILE_ICON = {
    "html": "HTML", "htm": "HTML",
    "css": "CSS",   "scss": "SCSS", "sass": "SASS",
    "js": "JS",     "jsx": "JSX",
    "ts": "TS",     "tsx": "TSX",
    "vue": "VUE",   "svelte": "SVT",
}


def score_color(s: int) -> str:
    if s >= 80: return C["green"]
    if s >= 60: return C["yellow"]
    return C["red"]


# ═══════════════════════════════════════════════════════════════════════
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Frontend Code Quality Checker")
        self.geometry("1380x840")
        self.minsize(1100, 720)
        self.configure(fg_color=C["bg"])

        self._data        = None
        self._all_issues  = []
        self._active_filt = "all"
        self._filter_btns = {}

        self._build_header()
        self._build_input()
        self._build_body()

    # ── Header ────────────────────────────────────────────────────────
    def _build_header(self):
        bar = ctk.CTkFrame(self, fg_color=C["bg2"], corner_radius=0, height=58)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        left = ctk.CTkFrame(bar, fg_color="transparent")
        left.pack(side="left", fill="y", padx=20)
        ctk.CTkLabel(left, text="FQ", font=ctk.CTkFont(size=20, weight="bold"),
                     text_color="#fff", fg_color=C["blue"],
                     width=40, height=40, corner_radius=10).pack(side="left", padx=(0, 12))

        tf = ctk.CTkFrame(left, fg_color="transparent")
        tf.pack(side="left")
        ctk.CTkLabel(tf, text="Frontend Code Quality Checker",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=C["blue"]).pack(anchor="w")
        ctk.CTkLabel(tf, text="Periksa standar kode sebelum deploy ke produksi",
                     font=ctk.CTkFont(size=10), text_color=C["text3"]).pack(anchor="w")

        ctk.CTkLabel(bar, text=" Python GUI ",
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=C["blue"], fg_color="#14143a",
                     corner_radius=10).pack(side="right", padx=20)

    # ── Input ─────────────────────────────────────────────────────────
    def _build_input(self):
        card = ctk.CTkFrame(self, fg_color=C["bg2"], corner_radius=12,
                            border_width=1, border_color=C["border"])
        card.pack(fill="x", padx=16, pady=(12, 6))

        ctk.CTkLabel(card, text="Folder Project Frontend",
                     font=ctk.CTkFont(size=13, weight="bold")
                     ).pack(anchor="w", padx=16, pady=(12, 2))
        ctk.CTkLabel(card,
                     text="Klik Browse untuk memilih folder. "
                          "File .html .css .js .jsx .ts .tsx .vue .svelte .scss akan di-scan otomatis.",
                     font=ctk.CTkFont(size=11), text_color=C["text2"]
                     ).pack(anchor="w", padx=16)

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(10, 14))

        self.path_var = tk.StringVar()
        self.path_entry = ctk.CTkEntry(
            row, textvariable=self.path_var, height=42, corner_radius=9,
            font=ctk.CTkFont(family="Consolas", size=12),
            placeholder_text="Contoh: C:\\Users\\nama\\my-react-app",
            border_color=C["border"], fg_color=C["bg3"],
        )
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.path_entry.bind("<Return>", lambda _: self.start_analyze())

        self.browse_btn = ctk.CTkButton(
            row, text="Browse Folder", width=140, height=42, corner_radius=9,
            fg_color=C["bg3"], hover_color=C["bg4"], border_width=1,
            border_color=C["border2"], text_color=C["text"],
            command=self.browse_folder,
        )
        self.browse_btn.pack(side="left", padx=(0, 8))

        self.analyze_btn = ctk.CTkButton(
            row, text="Analisis Sekarang", width=190, height=42, corner_radius=9,
            fg_color=C["blue"], hover_color="#4f52d9",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.start_analyze,
        )
        self.analyze_btn.pack(side="left")

        self.status_var = tk.StringVar(value="")
        ctk.CTkLabel(card, textvariable=self.status_var,
                     font=ctk.CTkFont(size=11), text_color=C["text3"]
                     ).pack(anchor="w", padx=16)
        self.progress = ctk.CTkProgressBar(card, mode="indeterminate", height=3)

    # ── Body ──────────────────────────────────────────────────────────
    def _build_body(self):
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=16, pady=(4, 16))

        self.left = ctk.CTkFrame(body, fg_color="transparent")
        self.left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Sidebar kanan — scrollable agar semua card selalu bisa diakses
        self.right = ctk.CTkScrollableFrame(body, fg_color="transparent", width=318)
        self.right.pack(side="right", fill="both")

        self._build_empty_state()
        self._build_sidebar()

    def _build_empty_state(self):
        self.empty = ctk.CTkFrame(self.left, fg_color=C["bg2"], corner_radius=12)
        self.empty.pack(fill="both", expand=True)
        ctk.CTkLabel(self.empty, text="Belum Ada Analisis",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=C["text2"]).pack(expand=True, pady=(80, 6))
        ctk.CTkLabel(self.empty,
                     text="Pilih folder project dan klik Analisis Sekarang.\n"
                          "Tool akan mendeteksi framework dan memeriksa 100+ standar kode.",
                     font=ctk.CTkFont(size=12), text_color=C["text3"],
                     justify="center").pack(pady=(0, 80))

    # ── Sidebar ───────────────────────────────────────────────────────
    def _build_sidebar(self):
        # Score card
        self.score_card = ctk.CTkFrame(self.right, fg_color=C["bg2"], corner_radius=12,
                                       border_width=1, border_color=C["border"])
        self.score_card.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(self.score_card, text="Skor Keseluruhan",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=C["text3"]).pack(anchor="w", padx=14, pady=(8, 2))

        # Smaller gauge: 180x100
        self.gauge_canvas = tk.Canvas(self.score_card, width=180, height=100,
                                      bg=C["bg2"], highlightthickness=0)
        self.gauge_canvas.pack()
        self._draw_gauge(0, C["border"])

        # Score + grade in one compact row
        info_row = ctk.CTkFrame(self.score_card, fg_color="transparent")
        info_row.pack(pady=(0, 4))
        self.score_num = ctk.CTkLabel(info_row, text="--",
                                      font=ctk.CTkFont(size=28, weight="bold"),
                                      text_color=C["blue"])
        self.score_num.pack(side="left")
        ctk.CTkLabel(info_row, text="/100",
                     font=ctk.CTkFont(size=12), text_color=C["text3"]).pack(side="left", padx=(2,10), pady=8)
        self.grade_lbl = ctk.CTkLabel(info_row, text="Grade: --",
                                      font=ctk.CTkFont(size=12, weight="bold"),
                                      text_color=C["blue"])
        self.grade_lbl.pack(side="left")
        self.verdict_lbl = ctk.CTkLabel(self.score_card, text="",
                                        font=ctk.CTkFont(size=11))
        self.verdict_lbl.pack(pady=(0, 8))

        # Stats card
        self.stats_card = ctk.CTkFrame(self.right, fg_color=C["bg2"], corner_radius=12,
                                       border_width=1, border_color=C["border"])
        self.stats_card.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(self.stats_card, text="Ringkasan",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=C["text3"]).pack(anchor="w", padx=14, pady=(8, 3))

        # Checklist card — FIXED height, does NOT expand so export always visible
        self.cl_card = ctk.CTkFrame(self.right, fg_color=C["bg2"], corner_radius=12,
                                    border_width=1, border_color=C["border"])
        self.cl_card.pack(fill="x", pady=(0, 6))
        self.cl_title = ctk.CTkLabel(self.cl_card, text="Pre-Deploy Checklist",
                                     font=ctk.CTkFont(size=11, weight="bold"),
                                     text_color=C["text3"])
        self.cl_title.pack(anchor="w", padx=14, pady=(8, 3))
        # Fixed-height scrollable area so items below are never hidden
        self.cl_scroll = ctk.CTkScrollableFrame(self.cl_card, fg_color="transparent",
                                                corner_radius=0, height=110)
        self.cl_scroll.pack(fill="x", padx=4, pady=(0, 6))

        # ── Export card ──────────────────────────────────────────────
        exp_card = ctk.CTkFrame(self.right, fg_color=C["bg2"], corner_radius=12,
                                border_width=1, border_color=C["border"])
        exp_card.pack(fill="x")

        ctk.CTkLabel(exp_card, text="Download Laporan",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=C["text3"]).pack(anchor="w", padx=14, pady=(10, 6))

        # PDF — full-width primary button
        ctk.CTkButton(
            exp_card,
            text="Download Laporan PDF",
            height=40, corner_radius=9,
            fg_color=C["blue"], hover_color="#4f52d9",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.export_pdf,
        ).pack(fill="x", padx=14, pady=(0, 6))

        # JSON + TXT row
        btn_row = ctk.CTkFrame(exp_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=14, pady=(0, 12))
        ctk.CTkButton(
            btn_row, text="JSON", width=148, height=34, corner_radius=8,
            fg_color=C["bg3"], hover_color=C["bg4"],
            border_width=1, border_color=C["border2"], text_color=C["text2"],
            command=self.export_json,
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            btn_row, text="TXT", width=148, height=34, corner_radius=8,
            fg_color=C["bg3"], hover_color=C["bg4"],
            border_width=1, border_color=C["border2"], text_color=C["text2"],
            command=self.export_txt,
        ).pack(side="left")

    # ── Gauge canvas ──────────────────────────────────────────────────
    def _draw_gauge(self, score: int, color: str = "#252540"):
        c = self.gauge_canvas
        c.delete("all")
        # Adjusted for 180x100 canvas
        cx, cy, r = 90, 92, 68
        c.create_arc(cx - r, cy - r, cx + r, cy + r,
                     start=210, extent=-240, style="arc",
                     outline="#252540", width=11)
        if score > 0:
            c.create_arc(cx - r, cy - r, cx + r, cy + r,
                         start=210, extent=-int(240 * score / 100),
                         style="arc", outline=color, width=11)

    # ── Browse & Analyze ──────────────────────────────────────────────
    def browse_folder(self):
        folder = filedialog.askdirectory(title="Pilih Folder Project Frontend")
        if folder:
            self.path_var.set(folder.replace("/", os.sep))

    def start_analyze(self):
        path = self.path_var.get().strip()
        if not path:
            messagebox.showwarning("Peringatan", "Pilih folder terlebih dahulu!")
            return
        if not os.path.isdir(path):
            messagebox.showerror("Folder Tidak Ditemukan",
                                 f"Folder tidak ditemukan:\n\n{path}")
            return
        self.analyze_btn.configure(state="disabled", text="Menganalisis...")
        self.browse_btn.configure(state="disabled")
        self.status_var.set("  Sedang menganalisis folder...")
        self.progress.pack(fill="x", padx=16, pady=(0, 4))
        self.progress.start()
        threading.Thread(target=self._do_analyze, args=(path,), daemon=True).start()

    def _do_analyze(self, path: str):
        try:
            from analyzer.checker import analyze_folder
            data = analyze_folder(path)
            self.after(0, lambda: self._render(data))
        except Exception as exc:
            import traceback
            tb = traceback.format_exc()
            self.after(0, lambda: messagebox.showerror(
                "Error Analisis", f"{exc}\n\n{tb[:600]}"))
        finally:
            self.after(0, self._restore_ui)

    def _restore_ui(self):
        self.analyze_btn.configure(state="normal", text="Analisis Sekarang")
        self.browse_btn.configure(state="normal")
        self.progress.stop()
        self.progress.pack_forget()
        self.status_var.set("")

    # ── Render results ────────────────────────────────────────────────
    def _render(self, data: dict):
        self._data        = data
        self._all_issues  = data.get("issues", [])
        self._active_filt = "all"

        self.empty.pack_forget()
        self._build_tabs(data)

        sc  = data.get("score", 0)
        col = score_color(sc)
        self._draw_gauge(sc, col)
        self.score_num.configure(text=str(sc), text_color=col)
        self.grade_lbl.configure(text=f"Grade: {data.get('grade', '--')}")

        if data.get("deploy_ready"):
            self.verdict_lbl.configure(text="Siap Deploy!", text_color=C["green"])
        elif data.get("total_errors", 0) <= 3:
            self.verdict_lbl.configure(text="Hampir Siap", text_color=C["yellow"])
        else:
            self.verdict_lbl.configure(text="Perlu Perbaikan", text_color=C["red"])

        # Rebuild stats
        for w in self.stats_card.winfo_children():
            if isinstance(w, ctk.CTkFrame):
                w.destroy()

        for lbl, val, col2 in [
            ("Error Kritis",  data.get("total_errors",   0), C["red"]),
            ("Warning",       data.get("total_warnings", 0), C["yellow"]),
            ("Info & Saran",  data.get("total_info",     0), C["cyan"]),
            ("Lulus Cek",     data.get("total_passed",   0), C["green"]),
            ("Total File",    data.get("file_count",     0), C["text"]),
        ]:
            r = ctk.CTkFrame(self.stats_card, fg_color="transparent")
            r.pack(fill="x", padx=14, pady=1)
            ctk.CTkLabel(r, text=lbl, font=ctk.CTkFont(size=12),
                         text_color=C["text2"]).pack(side="left")
            ctk.CTkLabel(r, text=str(val),
                         font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=col2).pack(side="right")

        # Framework badges
        fws = data.get("frameworks", [])
        if fws:
            fw_frame = ctk.CTkFrame(self.stats_card, fg_color=C["bg3"], corner_radius=8)
            fw_frame.pack(fill="x", padx=14, pady=(4, 10))
            ctk.CTkLabel(fw_frame, text="Framework Terdeteksi:",
                         font=ctk.CTkFont(size=10, weight="bold"),
                         text_color=C["text3"]).pack(anchor="w", padx=8, pady=(6, 2))
            wrap = ctk.CTkFrame(fw_frame, fg_color="transparent")
            wrap.pack(fill="x", padx=8, pady=(0, 6))
            for i, fw in enumerate(fws):
                ctk.CTkLabel(
                    wrap,
                    text=f"{fw.get('icon','')} {fw['label']}",
                    font=ctk.CTkFont(size=10, weight="bold"),
                    text_color=fw.get("color", C["text2"]),
                    fg_color=fw.get("bg", C["bg4"]),
                    corner_radius=8,
                ).grid(row=i // 2, column=i % 2, padx=2, pady=2, sticky="w")
        else:
            ctk.CTkFrame(self.stats_card, fg_color="transparent", height=4).pack()

        # Checklist
        for w in self.cl_scroll.winfo_children():
            w.destroy()
        checklist = data.get("checklist", [])
        passed_n  = sum(1 for c in checklist if c.get("passed"))
        self.cl_title.configure(text=f"Pre-Deploy Checklist  ({passed_n}/{len(checklist)})")
        for item in checklist:
            ok  = item.get("passed", False)
            row = ctk.CTkFrame(self.cl_scroll, fg_color="transparent")
            row.pack(fill="x", pady=1)
            ctk.CTkLabel(row, text="OK" if ok else "XX",
                         font=ctk.CTkFont(size=10, weight="bold"),
                         text_color=C["green"] if ok else C["red"],
                         fg_color="#0a2a1a" if ok else "#2a0a0a",
                         corner_radius=4, width=28).pack(side="left")
            ctk.CTkLabel(row, text=item.get("text", ""),
                         font=ctk.CTkFont(size=11),
                         text_color=C["green"] if ok else C["red"],
                         wraplength=260, justify="left",
                         anchor="w").pack(side="left", padx=(4, 0))

    # ── Tab view ──────────────────────────────────────────────────────
    def _build_tabs(self, data: dict):
        for w in self.left.winfo_children():
            w.destroy()

        tab = ctk.CTkTabview(
            self.left, fg_color=C["bg2"],
            segmented_button_fg_color=C["bg3"],
            segmented_button_selected_color=C["blue"],
            segmented_button_unselected_color=C["bg3"],
            segmented_button_selected_hover_color="#4f52d9",
            text_color=C["text2"], corner_radius=12,
        )
        tab.pack(fill="both", expand=True)
        tab.add("File Analysis")
        tab.add("Semua Issue")
        tab.set("File Analysis")

        self._tab_files(tab.tab("File Analysis"), data)
        self._tab_issues(tab.tab("Semua Issue"), data.get("issues", []))

    # ── Tab 1 : File Analysis ─────────────────────────────────────────
    def _tab_files(self, parent, data: dict):
        ready = data.get("deploy_ready", False)
        errs  = data.get("total_errors", 0)
        if ready:
            bgc, fgc = "#0a2a1a", C["green"]
            msg = "SIAP DEPLOY — Tidak ada error kritis."
        elif errs <= 3:
            bgc, fgc = "#2a2010", C["yellow"]
            msg = f"HAMPIR SIAP — {errs} error harus diperbaiki."
        else:
            bgc, fgc = "#2a0a0a", C["red"]
            msg = f"BELUM SIAP DEPLOY — {errs} error kritis ditemukan."

        banner = ctk.CTkFrame(parent, fg_color=bgc, corner_radius=8, height=38)
        banner.pack(fill="x", padx=8, pady=(8, 6))
        banner.pack_propagate(False)
        ctk.CTkLabel(banner, text=msg,
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=fgc).pack(expand=True)

        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent", corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=2, pady=2)

        files = sorted(data.get("files", []),
                       key=lambda f: (f.get("errors", 0), f.get("warnings", 0)),
                       reverse=True)

        for f in files:
            ftype = f.get("type", "js")
            sc    = f.get("score", 0)
            col   = score_color(sc)

            card = ctk.CTkFrame(scroll, fg_color=C["bg3"], corner_radius=10,
                                border_width=1, border_color=C["border"])
            card.pack(fill="x", pady=3, padx=4)

            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=12, pady=(8, 2))
            ctk.CTkLabel(top, text=FILE_ICON.get(ftype, "FILE"),
                         font=ctk.CTkFont(size=10, weight="bold"),
                         text_color=C["blue"], fg_color=C["bg4"],
                         corner_radius=4, width=36).pack(side="left")
            ctk.CTkLabel(top, text=f.get("file", ""),
                         font=ctk.CTkFont(family="Consolas", size=12),
                         text_color=C["text"], anchor="w"
                         ).pack(side="left", padx=(8, 0), fill="x", expand=True)
            ctk.CTkLabel(top, text=f"Score: {sc}",
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=col).pack(side="right")

            bot = ctk.CTkFrame(card, fg_color="transparent")
            bot.pack(fill="x", padx=12, pady=(0, 8))
            ctk.CTkLabel(bot, text=f"{ftype.upper()} · {f.get('lines', 0)} baris",
                         font=ctk.CTkFont(size=10), text_color=C["text3"]
                         ).pack(side="left")

            pills = ctk.CTkFrame(bot, fg_color="transparent")
            pills.pack(side="right")
            for val, lbl, bgp, tcp in [
                (f.get("errors",   0), "E", "#301010", C["red"]),
                (f.get("warnings", 0), "W", "#302010", C["yellow"]),
                (f.get("info",     0), "I", "#10203a", C["cyan"]),
            ]:
                if val:
                    ctk.CTkLabel(pills, text=f" {val}{lbl} ",
                                 font=ctk.CTkFont(size=10, weight="bold"),
                                 text_color=tcp, fg_color=bgp,
                                 corner_radius=8).pack(side="left", padx=2)

    # ── Tab 2 : Issue list ────────────────────────────────────────────
    def _tab_issues(self, parent, issues: list):
        fbar = ctk.CTkFrame(parent, fg_color="transparent")
        fbar.pack(fill="x", padx=8, pady=(8, 4))
        ctk.CTkLabel(fbar, text="Filter:",
                     font=ctk.CTkFont(size=11), text_color=C["text3"]
                     ).pack(side="left", padx=(0, 8))

        self._filter_btns = {}
        for mode, label in [("all", "Semua"), ("error", "Error"),
                             ("warning", "Warning"), ("info", "Info")]:
            btn = ctk.CTkButton(
                fbar, text=label, width=90, height=30, corner_radius=15,
                fg_color=C["blue"] if mode == "all" else C["bg3"],
                hover_color=C["bg4"], border_width=1, border_color=C["border2"],
                text_color=C["text"], font=ctk.CTkFont(size=11),
                command=lambda m=mode: self._apply_filter(m),
            )
            btn.pack(side="left", padx=3)
            self._filter_btns[mode] = btn

        self.issue_cnt_lbl = ctk.CTkLabel(fbar, text="",
                                          font=ctk.CTkFont(size=11),
                                          text_color=C["text3"])
        self.issue_cnt_lbl.pack(side="right", padx=6)

        self.issue_scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent",
                                                   corner_radius=0)
        self.issue_scroll.pack(fill="both", expand=True, padx=2, pady=2)
        self._render_issues(issues)

    def _apply_filter(self, mode: str):
        self._active_filt = mode
        for m, btn in self._filter_btns.items():
            btn.configure(fg_color=C["blue"] if m == mode else C["bg3"])
        self._render_issues(self._all_issues)

    def _render_issues(self, issues: list):
        for w in self.issue_scroll.winfo_children():
            w.destroy()

        filtered = [i for i in issues
                    if self._active_filt == "all" or i.get("severity") == self._active_filt]
        self.issue_cnt_lbl.configure(text=f"{len(filtered)} item")

        if not filtered:
            ctk.CTkLabel(self.issue_scroll,
                         text="Tidak ada issue untuk filter ini!",
                         font=ctk.CTkFont(size=13), text_color=C["green"]).pack(pady=40)
            return

        SEV = [("error", "Error Kritis",  C["red"]),
               ("warning", "Warning",     C["yellow"]),
               ("info",    "Info & Saran", C["cyan"])]

        for sev, sev_label, sev_col in SEV:
            group = [i for i in filtered if i.get("severity") == sev]
            if not group:
                continue

            gh = ctk.CTkFrame(self.issue_scroll, fg_color=C["bg3"],
                              corner_radius=8, height=36)
            gh.pack(fill="x", pady=(8, 2), padx=2)
            gh.pack_propagate(False)
            inner = ctk.CTkFrame(gh, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=10)
            ctk.CTkLabel(inner, text=sev_label,
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=sev_col).pack(side="left", expand=True, anchor="w")
            ctk.CTkLabel(inner, text=str(len(group)),
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=sev_col).pack(side="right")

            for issue in group:
                self._issue_card(issue, sev_col)

    def _issue_card(self, issue: dict, col: str):
        card = ctk.CTkFrame(self.issue_scroll, fg_color=C["bg3"], corner_radius=9,
                            border_width=1, border_color=C["border"])
        card.pack(fill="x", pady=2, padx=2)

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=12, pady=(9, 2))
        ctk.CTkLabel(top, text=issue.get("name", ""),
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=col).pack(side="left")

        meta = ctk.CTkFrame(top, fg_color="transparent")
        meta.pack(side="right")
        for txt in [
            issue.get("framework", ""),
            Path(issue.get("file", "")).name if issue.get("file") else "",
            f"Baris {issue['line']}" if issue.get("line") else "",
        ]:
            if txt:
                ctk.CTkLabel(meta, text=f" {txt} ",
                             font=ctk.CTkFont(family="Consolas", size=10),
                             text_color=C["text3"], fg_color=C["bg4"],
                             corner_radius=5).pack(side="left", padx=2)

        if issue.get("snippet"):
            sf = ctk.CTkFrame(card, fg_color=C["bg"], corner_radius=6)
            sf.pack(fill="x", padx=12, pady=2)
            ctk.CTkLabel(sf, text=issue["snippet"][:120],
                         font=ctk.CTkFont(family="Consolas", size=10),
                         text_color=C["text3"], anchor="w"
                         ).pack(fill="x", padx=8, pady=5)

        ctk.CTkLabel(card, text=issue.get("message", ""),
                     font=ctk.CTkFont(size=11), text_color=C["text2"],
                     wraplength=860, justify="left", anchor="w"
                     ).pack(fill="x", padx=12, pady=(2, 2))

        if issue.get("fix"):
            fix_row = ctk.CTkFrame(card, fg_color="transparent")
            fix_row.pack(fill="x", padx=12, pady=(0, 8))
            ctk.CTkLabel(fix_row, text="Solusi:",
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=C["cyan"]).pack(side="left")
            ctk.CTkLabel(fix_row, text=issue["fix"],
                         font=ctk.CTkFont(size=11), text_color=C["cyan"],
                         wraplength=820, justify="left"
                         ).pack(side="left", padx=(4, 0), anchor="w")

    # ══════════════════════════════════════════════════════════════════
    # EXPORT FUNCTIONS
    # ══════════════════════════════════════════════════════════════════

    def _check_data(self) -> bool:
        if not self._data:
            messagebox.showwarning("Export", "Belum ada hasil analisis.\nJalankan analisis folder terlebih dahulu.")
            return False
        return True

    # ── Download Laporan PDF ──────────────────────────────────────────
    def export_pdf(self):
        if not self._check_data():
            return

        try:
            from fpdf import FPDF
        except ImportError:
            messagebox.showerror(
                "Library Diperlukan",
                "fpdf2 belum terinstall.\n\nBuka terminal dan jalankan:\n  pip install fpdf2",
            )
            return

        path = filedialog.asksaveasfilename(
            title="Simpan Laporan Masalah PDF",
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf"), ("Semua File", "*.*")],
            initialfile="laporan-masalah.pdf",
        )
        if not path:
            return

        d   = self._data
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Sanitize text for latin-1 (FPDF default encoding)
        def s(text, limit: int = 0) -> str:
            t = str(text or "").encode("latin-1", errors="replace").decode("latin-1")
            return t[:limit] if limit else t

        SEV_LABEL = {"error": "ERROR KRITIS", "warning": "WARNING", "info": "INFO"}
        SEV_COLOR = {
            "error":   (220, 60,  60),
            "warning": (230, 160, 30),
            "info":    (40,  180, 210),
        }

        # ── Custom PDF class ─────────────────────────────────────────
        class PDF(FPDF):
            def header(self):
                self.set_fill_color(15, 15, 30)
                self.rect(0, 0, 210, 18, "F")
                self.set_text_color(99, 102, 241)
                self.set_font("Helvetica", "B", 9)
                self.set_xy(10, 5)
                self.cell(0, 8, "Frontend Code Quality Checker  |  Laporan Masalah", align="L")
                self.set_text_color(80, 80, 120)
                self.set_font("Helvetica", "", 8)
                self.set_xy(10, 5)
                self.cell(0, 8, f"Hal. {self.page_no()}", align="R")
                self.ln(16)

            def footer(self):
                self.set_y(-12)
                self.set_fill_color(15, 15, 30)
                self.rect(0, 285, 210, 12, "F")
                self.set_text_color(80, 80, 120)
                self.set_font("Helvetica", "", 7)
                self.cell(0, 8, f"Dibuat: {now}", align="C")

        pdf = PDF()
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.add_page()

        # ── HALAMAN 1 : Ringkasan ─────────────────────────────────────
        # Title block
        pdf.set_fill_color(18, 18, 40)
        pdf.rect(10, pdf.get_y(), 190, 32, "F")
        pdf.set_text_color(99, 102, 241)
        pdf.set_font("Helvetica", "B", 20)
        pdf.set_x(14)
        pdf.cell(0, 12, "LAPORAN MASALAH KODE", ln=True)
        pdf.set_text_color(180, 180, 210)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_x(14)
        pdf.cell(0, 5, f"Folder : {s(d.get('folder',''), 90)}", ln=True)
        pdf.set_x(14)
        pdf.cell(0, 5, f"Tanggal: {now}", ln=True)
        pdf.ln(8)

        # Score + Status badges
        score = d.get("score", 0)
        grade = d.get("grade", "-")
        sc_rgb = (50, 200, 100) if score >= 80 else (230, 160, 30) if score >= 60 else (220, 60, 60)
        st_rgb = (50, 200, 100) if d.get("deploy_ready") else (220, 60, 60)

        pdf.set_fill_color(*sc_rgb)
        pdf.set_text_color(10, 10, 20)
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_x(10)
        pdf.cell(60, 11, f"  Skor : {score}/100  (Grade {grade})", fill=True)
        pdf.set_fill_color(*st_rgb)
        st_txt = "  SIAP DEPLOY" if d.get("deploy_ready") else "  BELUM SIAP DEPLOY"
        pdf.cell(60, 11, st_txt, fill=True)
        pdf.ln(14)

        # Stats table
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(80, 80, 120)
        pdf.cell(0, 6, "RINGKASAN HASIL ANALISIS:", ln=True)
        pdf.ln(1)
        for lbl, val, rgb in [
            ("Error Kritis",  d.get("total_errors",   0), (220, 60,  60)),
            ("Warning",       d.get("total_warnings", 0), (230, 160, 30)),
            ("Info & Saran",  d.get("total_info",     0), (40,  180, 210)),
            ("Lulus Cek",     d.get("total_passed",   0), (50,  200, 100)),
            ("Total File",    d.get("file_count",     0), (160, 160, 210)),
        ]:
            pdf.set_fill_color(22, 22, 44)
            pdf.set_text_color(180, 180, 210)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_x(10)
            pdf.cell(52, 7, f"  {lbl}", fill=True)
            pdf.set_text_color(*rgb)
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(20, 7, str(val), fill=True, ln=True)
        pdf.ln(4)

        # Frameworks
        fws = d.get("frameworks", [])
        if fws:
            pdf.set_text_color(80, 80, 120)
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(0, 6, "FRAMEWORK TERDETEKSI:", ln=True)
            pdf.set_text_color(150, 150, 210)
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(0, 6, "  " + ", ".join(s(fw["label"]) for fw in fws), ln=True)
            pdf.ln(4)

        # ── File Analysis Table ───────────────────────────────────────
        pdf.set_fill_color(12, 12, 28)
        pdf.rect(10, pdf.get_y(), 190, 8, "F")
        pdf.set_text_color(99, 102, 241)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 8, "  FILE ANALYSIS", ln=True)
        pdf.ln(1)

        # Header row
        pdf.set_fill_color(28, 28, 52)
        pdf.set_text_color(130, 130, 190)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_x(10)
        for hdr, w in [("File / Path", 88), ("Tipe", 18), ("Baris", 20),
                       ("Score", 20), ("Error", 16), ("Warn", 16), ("Info", 12)]:
            pdf.cell(w, 7, hdr, fill=True)
        pdf.ln(7)

        alt = False
        for f in sorted(d.get("files", []),
                        key=lambda f: (f.get("errors", 0), f.get("warnings", 0)),
                        reverse=True):
            pdf.set_fill_color(16, 16, 34) if alt else pdf.set_fill_color(20, 20, 40)
            alt = not alt
            sc2 = f.get("score", 0)
            sc_rgb2 = (50, 200, 100) if sc2 >= 80 else (230, 160, 30) if sc2 >= 60 else (220, 60, 60)
            pdf.set_text_color(190, 190, 220)
            pdf.set_font("Helvetica", "", 7.5)
            pdf.set_x(10)
            pdf.cell(88, 6.5, s(f.get("file", ""), 52), fill=True)
            pdf.cell(18, 6.5, s(f.get("type", "")).upper(), fill=True)
            pdf.cell(20, 6.5, str(f.get("lines", 0)), fill=True)
            pdf.set_text_color(*sc_rgb2)
            pdf.cell(20, 6.5, str(sc2), fill=True)
            pdf.set_text_color(220, 60, 60)
            pdf.cell(16, 6.5, str(f.get("errors", 0)), fill=True)
            pdf.set_text_color(230, 160, 30)
            pdf.cell(16, 6.5, str(f.get("warnings", 0)), fill=True)
            pdf.set_text_color(40, 180, 210)
            pdf.cell(12, 6.5, str(f.get("info", 0)), fill=True, ln=True)
        pdf.ln(8)

        # ── HALAMAN 2+ : Detail Masalah ───────────────────────────────
        pdf.add_page()
        pdf.set_fill_color(12, 12, 28)
        pdf.rect(10, pdf.get_y(), 190, 8, "F")
        pdf.set_text_color(99, 102, 241)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 8, "  DETAIL MASALAH", ln=True)
        pdf.ln(2)

        issues_all = d.get("issues", [])
        if not issues_all:
            pdf.set_text_color(50, 200, 100)
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 10, "  Tidak ada masalah ditemukan! Kode siap deploy.", ln=True)
        else:
            for sev in ("error", "warning", "info"):
                group = [i for i in issues_all if i.get("severity") == sev]
                if not group:
                    continue

                r2, g2, b2 = SEV_COLOR[sev]
                # Section header
                pdf.set_fill_color(r2, g2, b2)
                pdf.set_text_color(10, 10, 20)
                pdf.set_font("Helvetica", "B", 9)
                pdf.set_x(10)
                pdf.cell(190, 8, f"  {SEV_LABEL[sev]}  ({len(group)} item)", fill=True, ln=True)
                pdf.ln(1)

                for idx, issue in enumerate(group, 1):
                    # Issue title
                    pdf.set_fill_color(22, 22, 46)
                    pdf.set_text_color(r2, g2, b2)
                    pdf.set_font("Helvetica", "B", 8.5)
                    pdf.set_x(11)
                    pdf.cell(187, 7, f"{idx}. {s(issue.get('name',''))}", fill=True, ln=True)

                    # Meta line (file | baris | framework)
                    parts = []
                    if issue.get("file"):       parts.append(f"File: {s(Path(issue['file']).name)}")
                    if issue.get("line"):       parts.append(f"Baris: {issue['line']}")
                    if issue.get("framework"):  parts.append(f"[{s(issue['framework'])}]")
                    if parts:
                        pdf.set_text_color(90, 90, 140)
                        pdf.set_font("Helvetica", "", 7.5)
                        pdf.set_x(13)
                        pdf.cell(185, 5, "  " + "  |  ".join(parts), ln=True)

                    # Code snippet
                    if issue.get("snippet"):
                        pdf.set_fill_color(10, 10, 22)
                        pdf.set_text_color(120, 120, 170)
                        pdf.set_font("Courier", "", 7)
                        pdf.set_x(13)
                        pdf.cell(185, 5.5, "  " + s(issue["snippet"], 105), fill=True, ln=True)

                    # Description
                    pdf.set_text_color(170, 170, 200)
                    pdf.set_font("Helvetica", "", 8)
                    pdf.set_x(13)
                    pdf.multi_cell(185, 5, "  Masalah : " + s(issue.get("message", ""), 180))

                    # Fix suggestion
                    if issue.get("fix"):
                        pdf.set_text_color(30, 160, 190)
                        pdf.set_font("Helvetica", "I", 8)
                        pdf.set_x(13)
                        pdf.multi_cell(185, 5, "  Solusi  : " + s(issue.get("fix", ""), 180))

                    pdf.ln(2)
                pdf.ln(3)

        # ── Halaman Terakhir : Pre-Deploy Checklist ────────────────────
        pdf.add_page()
        pdf.set_fill_color(12, 12, 28)
        pdf.rect(10, pdf.get_y(), 190, 8, "F")
        pdf.set_text_color(99, 102, 241)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 8, "  PRE-DEPLOY CHECKLIST", ln=True)
        pdf.ln(3)

        checklist = d.get("checklist", [])
        passed_n  = sum(1 for c in checklist if c.get("passed"))
        pdf.set_text_color(130, 130, 190)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 7, f"  {passed_n} dari {len(checklist)} item lulus", ln=True)
        pdf.ln(2)

        for item in checklist:
            ok = item.get("passed", False)
            pdf.set_fill_color(10, 32, 18) if ok else pdf.set_fill_color(32, 10, 10)
            pdf.set_text_color(50, 200, 100) if ok else pdf.set_text_color(220, 60, 60)
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_x(10)
            pdf.cell(22, 7, "  LULUS" if ok else "  GAGAL", fill=True)
            pdf.set_text_color(190, 190, 220)
            pdf.set_font("Helvetica", "", 8)
            pdf.cell(168, 7, s(item.get("text", ""), 95), fill=True, ln=True)
            pdf.ln(0.5)

        # ── Save ──────────────────────────────────────────────────────
        try:
            pdf.output(path)
            total = len(issues_all)
            messagebox.showinfo(
                "Laporan Berhasil Didownload",
                f"File PDF berhasil disimpan!\n\nLokasi:\n{path}\n\n"
                f"Total masalah: {total}\n"
                f"Skor: {score}/100  (Grade {grade})"
            )
        except Exception as e:
            messagebox.showerror("Gagal Simpan PDF", f"Tidak bisa menyimpan file:\n{e}")

    # ── Export JSON ───────────────────────────────────────────────────
    def export_json(self):
        if not self._check_data():
            return
        path = filedialog.asksaveasfilename(
            title="Simpan Laporan JSON",
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("Semua File", "*.*")],
            initialfile="quality-report.json",
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Export Berhasil", f"Laporan JSON disimpan:\n{path}")

    # ── Export TXT ────────────────────────────────────────────────────
    def export_txt(self):
        if not self._check_data():
            return
        path = filedialog.asksaveasfilename(
            title="Simpan Laporan TXT",
            defaultextension=".txt",
            filetypes=[("Text", "*.txt"), ("Semua File", "*.*")],
            initialfile="quality-report.txt",
        )
        if not path:
            return

        d   = self._data
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines = [
            "=" * 60,
            "  FRONTEND CODE QUALITY REPORT",
            "=" * 60,
            f"Dibuat  : {now}",
            f"Folder  : {d.get('folder', '')}",
            "",
            f"SKOR    : {d.get('score', 0)}/100  (Grade: {d.get('grade', '-')})",
            f"STATUS  : {'SIAP DEPLOY' if d.get('deploy_ready') else 'BELUM SIAP DEPLOY'}",
            "",
            "FRAMEWORK: " + (", ".join(fw["label"] for fw in d.get("frameworks", [])) or "Vanilla"),
            "",
            "RINGKASAN",
            "-" * 30,
            f"  Error   : {d.get('total_errors', 0)}",
            f"  Warning : {d.get('total_warnings', 0)}",
            f"  Info    : {d.get('total_info', 0)}",
            f"  Passed  : {d.get('total_passed', 0)}",
            f"  Files   : {d.get('file_count', 0)}",
            "",
            "FILE ANALYSIS",
            "-" * 30,
        ]
        for f in d.get("files", []):
            lines.append(
                f"  {f.get('file',''):<50} "
                f"Score:{f.get('score',0):3d} "
                f"Err:{f.get('errors',0)} Warn:{f.get('warnings',0)} Info:{f.get('info',0)}"
            )
        lines += ["", "DETAIL MASALAH", "-" * 30]
        for i in d.get("issues", []):
            lines.append(
                f"\n  [{i.get('severity','').upper()}] {i.get('name','')} "
                f"({i.get('file','')}  Baris:{i.get('line','-')})"
            )
            lines.append(f"    Masalah : {i.get('message','')}")
            lines.append(f"    Solusi  : {i.get('fix','')}")
        lines += ["", "PRE-DEPLOY CHECKLIST", "-" * 30]
        for c in d.get("checklist", []):
            lines.append(f"  [{'LULUS' if c.get('passed') else 'GAGAL'}] {c.get('text','')}")

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        messagebox.showinfo("Export Berhasil", f"Laporan TXT disimpan:\n{path}")


# ═══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = App()
    app.mainloop()
