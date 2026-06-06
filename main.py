"""
NFR Requirements Classifier - Desktop Application
Master's Thesis: AI-based classification of software requirements
Uses Groq API (Llama 3.3 70B) with multiple prompt strategies from Chapter 5.
"""

import os
import sys
import threading
import datetime
import time
import csv
import customtkinter as ctk
from tkinter import messagebox, filedialog
import tkinter as tk
from collections import Counter, OrderedDict

# ── Path helpers (PyInstaller-compatible) ────────────────────────────────────

def _get_base_dir():
    """Return the directory where the exe (or .py script) lives."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def _get_resource_path(filename):
    """Return path to a bundled resource (icon, etc.)."""
    if getattr(sys, 'frozen', False):
        # PyInstaller extracts to _MEIPASS
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

BASE_DIR = _get_base_dir()

# ── API Setup ────────────────────────────────────────────────────────────────
from dotenv import load_dotenv

def _load_env_file():
    """Dynamically load the .env file with override=True."""
    for _env_candidate in [
        os.path.join(BASE_DIR, ".env"),
        os.path.join(os.path.dirname(BASE_DIR), ".env"),
    ]:
        if os.path.exists(_env_candidate):
            load_dotenv(_env_candidate, override=True)
            break

_load_env_file()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# ── Prompt Strategies ────────────────────────────────────────────────────────

PROMPTS = OrderedDict()

PROMPTS["Basic Zero-Shot"] = (
    "Classify the following software requirement into exactly ONE of these categories. "
    "Reply with ONLY the label.\n\n"
    "Categories: F (Functional), LF (Look & Feel), O (Operability), PE (Performance), "
    "SE (Security), US (Usability), Other (Other NFR)\n\n"
    "Reply with exactly one of: F, LF, O, Other, PE, SE, US"
)

PROMPTS["Improved Zero-Shot"] = (
    "You are an expert Requirements Engineer. Classify the following software requirement "
    "into exactly ONE of these 7 categories. Reply with ONLY the label.\n\n"
    "CATEGORIES:\n"
    "- F = Functional Requirement: describes a specific behavior, feature, or capability the system must provide.\n"
    "- LF = Look and Feel: requirements about the system's appearance, visual design, or branding.\n"
    "- O = Operability: requirements about the operational environment, platform support, or deployment constraints.\n"
    "- PE = Performance: requirements about speed, response time, throughput, capacity, or resource efficiency.\n"
    "- SE = Security: requirements about encryption, authentication, authorization, data protection, or access control.\n"
    "- US = Usability: requirements about ease of use, learnability, accessibility, or user satisfaction.\n"
    "- Other = Other Non-Functional Requirement. Use this category for ANY requirement related to:\n"
    "    * Availability, Scalability, Maintainability, Legal, Fault Tolerance, Portability\n\n"
    "IMPORTANT: Reply with exactly one of: F, LF, O, Other, PE, SE, US\n"
    "Do not output anything else."
)

PROMPTS["Few-Shot (3 examples)"] = (
    "You are an expert Requirements Engineer. Classify the following software requirement "
    "into exactly ONE of these 7 categories. Reply with ONLY the label.\n\n"
    "CATEGORIES:\n"
    "- F = Functional Requirement: describes a specific behavior, feature, or capability the system must provide.\n"
    "- LF = Look and Feel: requirements about the system's appearance, visual design, or branding.\n"
    "- O = Operability: requirements about the operational environment, platform support, or deployment constraints.\n"
    "- PE = Performance: requirements about speed, response time, throughput, capacity, or resource efficiency.\n"
    "- SE = Security: requirements about encryption, authentication, authorization, data protection, or access control.\n"
    "- US = Usability: requirements about ease of use, learnability, accessibility, or user satisfaction.\n"
    "- Other = Other Non-Functional Requirement. Use this category for ANY requirement related to:\n"
    "    * Availability, Scalability, Maintainability, Legal, Fault Tolerance, Portability\n\n"
    "EXAMPLES:\n"
    '"The system shall allow users to reset their password via email." → F\n'
    '"The system shall respond to all queries within 2 seconds." → PE\n'
    '"All data transmissions shall be encrypted using TLS 1.3." → SE\n\n'
    "IMPORTANT: Reply with exactly one of: F, LF, O, Other, PE, SE, US\n"
    "Do not output anything else."
)

PROMPT_DESCRIPTIONS = {
    "Basic Zero-Shot": "Minimal prompt with category labels only",
    "Improved Zero-Shot": "Detailed prompt with category descriptions (Chapter 5)",
    "Few-Shot (3 examples)": "Detailed prompt augmented with 3 classification examples",
}

# ── Constants ────────────────────────────────────────────────────────────────

LABEL_FULL = {
    "F":     "Functional (F)",
    "LF":    "Look & Feel (LF)",
    "O":     "Operability (O)",
    "Other": "Other NFR (Other)",
    "PE":    "Performance (PE)",
    "SE":    "Security (SE)",
    "US":    "Usability (US)",
}

LABEL_DESC = {
    "F":     "Describes a specific behaviour, feature, or capability the system must provide.",
    "LF":    "Requirements about the system's appearance, visual design, or branding.",
    "O":     "Requirements about the operational environment, platform support, or deployment constraints.",
    "Other": "Availability, scalability, maintainability, legal, fault tolerance, portability, etc.",
    "PE":    "Requirements about speed, response time, throughput, capacity, or resource efficiency.",
    "SE":    "Requirements about encryption, authentication, authorization, data protection, or access control.",
    "US":    "Requirements about ease of use, learnability, accessibility, or user satisfaction.",
}

LABELS_ORDER = ["F", "LF", "O", "Other", "PE", "SE", "US"]

VALID_LABELS = {"F", "LF", "O", "OTHER", "PE", "SE", "US"}

# ── Theme ────────────────────────────────────────────────────────────────────

BG          = "#FAFAFA"
BG_CARD     = "#FFFFFF"
BG_HEADER   = "#2C3E6B"
FG_HEADER   = "#FFFFFF"
FG          = "#1A1A2E"
FG_MUTED    = "#6B7280"
ACCENT      = "#2C3E6B"
ACCENT_LIGHT = "#E8EBF0"
BORDER      = "#D1D5DB"
SUCCESS_BG  = "#F0F7F0"
SUCCESS_BD  = "#4A7C59"

LABEL_COLORS = {
    "F":     "#2C3E6B",
    "LF":    "#7C3E8E",
    "O":     "#3E6B5A",
    "Other": "#8B6914",
    "PE":    "#B85C2F",
    "SE":    "#9B2335",
    "US":    "#2E6B8A",
}

LABEL_COLORS_LIGHT = {
    "F":     "#D6DCE8",
    "LF":    "#E8D6EE",
    "O":     "#D6E8E0",
    "Other": "#EDE4CC",
    "PE":    "#F0DDD2",
    "SE":    "#EDCDD3",
    "US":    "#D2E4EC",
}


# ── Groq Classification ─────────────────────────────────────────────────────

def classify_requirement(text: str, prompt: str) -> dict:
    """Call Groq API to classify a single requirement. Returns dict with label info."""
    from groq import Groq

    _load_env_file()
    current_api_key = os.environ.get("GROQ_API_KEY", "")

    if not current_api_key:
        return {"status": "error", "error": "GROQ_API_KEY not set. Check your .env file."}

    try:
        start_time = time.perf_counter()
        client = Groq(api_key=current_api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f'Classify this requirement: "{text}"'},
            ],
            temperature=0,
            max_tokens=5,
        )
        elapsed = time.perf_counter() - start_time
        pred = response.choices[0].message.content.strip().upper()
        pred = pred.replace('"', "").replace("'", "").replace(".", "").strip()

        if pred == "OTHER":
            pred = "Other"
        elif pred not in VALID_LABELS:
            return {"status": "error", "error": f"Model returned unexpected label: '{pred}'"}

        return {
            "status": "success",
            "label": pred,
            "full_name": LABEL_FULL.get(pred, pred),
            "description": LABEL_DESC.get(pred, ""),
            "elapsed": round(elapsed, 2),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ── Application ──────────────────────────────────────────────────────────────

class ClassifierApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # ── Window setup ─────────────────────────────────────────────────
        self.title("NFR Requirements Classifier")
        self.geometry("1080x780")
        self.minsize(920, 650)
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        self.configure(fg_color=BG)

        # Set window icon
        ico_path = _get_resource_path("requify.ico")
        png_path = _get_resource_path("requify.png")
        if not os.path.exists(png_path):
            png_path = os.path.join(os.path.dirname(BASE_DIR), "requify.png")

        try:
            if os.path.exists(ico_path):
                self.iconbitmap(ico_path)
            if os.path.exists(png_path):
                icon_image = tk.PhotoImage(file=png_path)
                self.iconphoto(True, icon_image)
                self._icon_ref = icon_image
        except Exception:
            pass

        # Data
        self.history = []          # (timestamp, text, label, full_name, elapsed, strategy)
        self.batch_results = []    # same format as history entries
        self._anim_id = None
        self._batch_running = False

        self._build_ui()

    # ── UI Construction ──────────────────────────────────────────────────

    def _build_ui(self):
        # ── Header ───────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color=BG_HEADER, corner_radius=0, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="NFR Requirements Classifier",
            font=ctk.CTkFont(family="Georgia", size=22, weight="bold"),
            text_color=FG_HEADER,
        ).place(relx=0.5, rely=0.5, anchor="center")

        # ── Main container ───────────────────────────────────────────────
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=20, pady=12)
        main.grid_columnconfigure(0, weight=3)
        main.grid_columnconfigure(1, weight=2)
        main.grid_rowconfigure(0, weight=1)

        # ── Left: Tabview ────────────────────────────────────────────────
        self.tabview = ctk.CTkTabview(
            main, fg_color=BG_CARD,
            segmented_button_fg_color=ACCENT_LIGHT,
            segmented_button_selected_color=ACCENT,
            segmented_button_unselected_color=ACCENT_LIGHT,
            corner_radius=8, border_width=1, border_color=BORDER,
        )
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self.tabview.add("  Classify  ")
        self.tabview.add("  Batch  ")
        self.tabview.add("  Statistics  ")

        self._build_classify_tab()
        self._build_batch_tab()
        self._build_statistics_tab()

        # ── Right: History ───────────────────────────────────────────────
        self._build_history_panel(main)

        # ── Footer ───────────────────────────────────────────────────────
        footer = ctk.CTkFrame(self, fg_color="transparent", height=28)
        footer.pack(fill="x", padx=20, pady=(0, 8))
        ctk.CTkLabel(
            footer,
            text="Model: Llama 3.3 70B (Groq API)  ·  Dataset: PROMISE NFR",
            font=ctk.CTkFont(size=11), text_color=FG_MUTED,
        ).pack()

        # Keyboard shortcut
        self.bind("<Control-Return>", lambda e: self._on_classify())

    # ══════════════════════════════════════════════════════════════════════
    #  CLASSIFY TAB
    # ══════════════════════════════════════════════════════════════════════

    def _build_classify_tab(self):
        tab = self.tabview.tab("  Classify  ")

        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # ── Strategy selector ────────────────────────────────────────────
        strategy_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        strategy_frame.pack(fill="x", pady=(4, 2))

        ctk.CTkLabel(
            strategy_frame, text="Prompt Strategy:",
            font=ctk.CTkFont(size=12, weight="bold"), text_color=ACCENT,
        ).pack(side="left")

        self.strategy_var = ctk.StringVar(value="Improved Zero-Shot")
        self.strategy_menu = ctk.CTkOptionMenu(
            strategy_frame, values=list(PROMPTS.keys()),
            variable=self.strategy_var, fg_color=ACCENT, button_color="#1E2D4D",
            font=ctk.CTkFont(size=12), width=210, height=28,
        )
        self.strategy_menu.pack(side="left", padx=(8, 0))

        self.strategy_desc = ctk.CTkLabel(
            scroll, text=PROMPT_DESCRIPTIONS["Improved Zero-Shot"],
            font=ctk.CTkFont(size=11, slant="italic"), text_color=FG_MUTED, anchor="w",
        )
        self.strategy_desc.pack(fill="x", pady=(0, 8))
        self.strategy_var.trace_add("write", self._on_strategy_change)

        # ── Input area ───────────────────────────────────────────────────
        ctk.CTkLabel(
            scroll, text="Enter a Software Requirement",
            font=ctk.CTkFont(family="Georgia", size=14, weight="bold"),
            text_color=ACCENT, anchor="w",
        ).pack(fill="x", pady=(0, 4))

        self.input_box = ctk.CTkTextbox(
            scroll, height=80, corner_radius=6, border_width=1,
            border_color=BORDER, fg_color="#F5F5F5", text_color=FG,
            font=ctk.CTkFont(size=13), wrap="word",
        )
        self.input_box.pack(fill="x", pady=(0, 8))
        self.input_box.insert("1.0", "e.g. The system shall respond to all user requests within 2 seconds.")
        self.input_box.bind("<FocusIn>", self._clear_placeholder)
        self._placeholder_active = True

        # ── Buttons ──────────────────────────────────────────────────────
        btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_row.pack(fill="x", pady=(0, 4))

        self.classify_btn = ctk.CTkButton(
            btn_row, text="▶  Classify", width=130, height=34, corner_radius=6,
            fg_color=ACCENT, hover_color="#1E2D4D",
            font=ctk.CTkFont(size=13, weight="bold"), command=self._on_classify,
        )
        self.classify_btn.pack(side="left")

        self.compare_btn = ctk.CTkButton(
            btn_row, text="⚡  Compare Strategies", width=180, height=34,
            corner_radius=6, fg_color="#7C3E8E", hover_color="#5E2D6B",
            font=ctk.CTkFont(size=12, weight="bold"), command=self._on_compare,
        )
        self.compare_btn.pack(side="left", padx=(8, 0))

        self.clear_btn = ctk.CTkButton(
            btn_row, text="Clear", width=70, height=34, corner_radius=6,
            fg_color="transparent", hover_color=ACCENT_LIGHT,
            text_color=FG_MUTED, border_width=1, border_color=BORDER,
            font=ctk.CTkFont(size=12), command=self._on_clear,
        )
        self.clear_btn.pack(side="right")

        # ── Animated loading bar ─────────────────────────────────────────
        self.loading_frame = ctk.CTkFrame(scroll, fg_color="transparent")

        self.loading_bar = ctk.CTkProgressBar(
            self.loading_frame, mode="indeterminate",
            progress_color=ACCENT, height=4, corner_radius=2, width=400,
        )
        self.loading_bar.pack(fill="x", pady=(4, 0))

        self.loading_label = ctk.CTkLabel(
            self.loading_frame, text="Classifying...",
            font=ctk.CTkFont(size=11, slant="italic"), text_color=FG_MUTED,
        )
        self.loading_label.pack(pady=(2, 4))

        # ── Result card ──────────────────────────────────────────────────
        self.result_card = ctk.CTkFrame(
            scroll, fg_color=SUCCESS_BG, corner_radius=8,
            border_width=1, border_color=SUCCESS_BD,
        )

        result_top = ctk.CTkFrame(self.result_card, fg_color="transparent")
        result_top.pack(fill="x", padx=16, pady=(12, 4))

        ctk.CTkLabel(
            result_top, text="Classification Result",
            font=ctk.CTkFont(family="Georgia", size=13, weight="bold"),
            text_color=ACCENT, anchor="w",
        ).pack(side="left")

        self.time_label = ctk.CTkLabel(
            result_top, text="",
            font=ctk.CTkFont(family="Consolas", size=11), text_color=FG_MUTED,
        )
        self.time_label.pack(side="right")

        self.badge_frame = ctk.CTkFrame(self.result_card, fg_color="transparent")
        self.badge_frame.pack(fill="x", padx=16, pady=(4, 0))

        self.label_badge = ctk.CTkLabel(
            self.badge_frame, text="  F  ",
            font=ctk.CTkFont(family="Consolas", size=18, weight="bold"),
            text_color="#FFFFFF", fg_color=ACCENT, corner_radius=6, width=60, height=36,
        )
        self.label_badge.pack(side="left")

        self.label_name = ctk.CTkLabel(
            self.badge_frame, text="",
            font=ctk.CTkFont(family="Georgia", size=16, weight="bold"),
            text_color=FG, anchor="w",
        )
        self.label_name.pack(side="left", padx=(12, 0))

        self.label_desc = ctk.CTkLabel(
            self.result_card, text="",
            font=ctk.CTkFont(size=12), text_color=FG_MUTED, anchor="w", wraplength=450,
        )
        self.label_desc.pack(fill="x", padx=16, pady=(6, 12))

        # ── Compare card ─────────────────────────────────────────────────
        self.compare_card = ctk.CTkFrame(
            scroll, fg_color=BG_CARD, corner_radius=8,
            border_width=1, border_color="#7C3E8E",
        )

        ctk.CTkLabel(
            self.compare_card, text="⚡ Strategy Comparison",
            font=ctk.CTkFont(family="Georgia", size=13, weight="bold"),
            text_color="#7C3E8E", anchor="w",
        ).pack(fill="x", padx=16, pady=(12, 8))

        self.compare_inner = ctk.CTkFrame(self.compare_card, fg_color="transparent")
        self.compare_inner.pack(fill="x", padx=16, pady=(0, 12))

        # ── Category reference ───────────────────────────────────────────
        ref_card = ctk.CTkFrame(
            scroll, fg_color=BG_CARD, corner_radius=8,
            border_width=1, border_color=BORDER,
        )
        ref_card.pack(fill="x", pady=(12, 4))

        ctk.CTkLabel(
            ref_card, text="Category Reference",
            font=ctk.CTkFont(family="Georgia", size=13, weight="bold"),
            text_color=ACCENT, anchor="w",
        ).pack(fill="x", padx=16, pady=(12, 6))

        for lk in LABELS_ORDER:
            row = ctk.CTkFrame(ref_card, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=1)

            ctk.CTkLabel(
                row, text=f" {lk} ",
                font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
                text_color="#FFFFFF", fg_color=LABEL_COLORS[lk],
                corner_radius=3, width=40, height=20,
            ).pack(side="left")

            ctk.CTkLabel(
                row, text=LABEL_DESC[lk],
                font=ctk.CTkFont(size=10), text_color=FG_MUTED,
                anchor="w", wraplength=380,
            ).pack(side="left", padx=(6, 0))

        ctk.CTkFrame(ref_card, fg_color="transparent", height=10).pack()

    # ══════════════════════════════════════════════════════════════════════
    #  BATCH TAB
    # ══════════════════════════════════════════════════════════════════════

    def _build_batch_tab(self):
        tab = self.tabview.tab("  Batch  ")

        # ── Upload section ───────────────────────────────────────────────
        upload_card = ctk.CTkFrame(tab, fg_color=BG_CARD, corner_radius=8, border_width=1, border_color=BORDER)
        upload_card.pack(fill="x", padx=4, pady=(8, 8))

        ctk.CTkLabel(
            upload_card, text="Batch Classification",
            font=ctk.CTkFont(family="Georgia", size=14, weight="bold"),
            text_color=ACCENT, anchor="w",
        ).pack(fill="x", padx=16, pady=(12, 2))

        ctk.CTkLabel(
            upload_card,
            text="Upload a CSV or TXT file with requirements. CSV files should have a column named "
                 '"Requirement" or "Text". TXT files should have one requirement per line.',
            font=ctk.CTkFont(size=11), text_color=FG_MUTED, anchor="w", wraplength=520,
        ).pack(fill="x", padx=16, pady=(0, 8))

        btn_row = ctk.CTkFrame(upload_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 4))

        self.batch_upload_btn = ctk.CTkButton(
            btn_row, text="📂  Upload File", width=140, height=34,
            corner_radius=6, fg_color=ACCENT, hover_color="#1E2D4D",
            font=ctk.CTkFont(size=13, weight="bold"), command=self._on_batch_upload,
        )
        self.batch_upload_btn.pack(side="left")

        self.batch_export_btn = ctk.CTkButton(
            btn_row, text="💾  Export Results", width=140, height=34,
            corner_radius=6, fg_color="#3E6B5A", hover_color="#2D5244",
            font=ctk.CTkFont(size=12, weight="bold"), command=self._on_batch_export,
        )
        self.batch_export_btn.pack(side="left", padx=(8, 0))

        self.batch_stop_btn = ctk.CTkButton(
            btn_row, text="Stop", width=60, height=34, corner_radius=6,
            fg_color="#9B2335", hover_color="#7A1B2A",
            font=ctk.CTkFont(size=12, weight="bold"), command=self._on_batch_stop,
        )
        self.batch_stop_btn.pack(side="right")

        # Strategy selector for batch
        batch_strat_row = ctk.CTkFrame(upload_card, fg_color="transparent")
        batch_strat_row.pack(fill="x", padx=16, pady=(4, 12))

        ctk.CTkLabel(
            batch_strat_row, text="Strategy:",
            font=ctk.CTkFont(size=11, weight="bold"), text_color=ACCENT,
        ).pack(side="left")

        self.batch_strategy_var = ctk.StringVar(value="Improved Zero-Shot")
        ctk.CTkOptionMenu(
            batch_strat_row, values=list(PROMPTS.keys()),
            variable=self.batch_strategy_var, fg_color=ACCENT, button_color="#1E2D4D",
            font=ctk.CTkFont(size=11), width=200, height=26,
        ).pack(side="left", padx=(8, 0))

        # ── Progress section ─────────────────────────────────────────────
        self.batch_progress_frame = ctk.CTkFrame(tab, fg_color="transparent")
        self.batch_progress_frame.pack(fill="x", padx=4, pady=(0, 4))

        self.batch_progress_bar = ctk.CTkProgressBar(
            self.batch_progress_frame, progress_color=ACCENT, height=6,
            corner_radius=3, width=400,
        )
        self.batch_progress_bar.pack(fill="x")
        self.batch_progress_bar.set(0)

        self.batch_status_label = ctk.CTkLabel(
            self.batch_progress_frame, text="Ready — upload a file to begin",
            font=ctk.CTkFont(size=11), text_color=FG_MUTED, anchor="w",
        )
        self.batch_status_label.pack(fill="x", pady=(2, 0))

        # ── Results table ────────────────────────────────────────────────
        self.batch_results_scroll = ctk.CTkScrollableFrame(
            tab, fg_color=BG_CARD, corner_radius=8, border_width=1, border_color=BORDER,
        )
        self.batch_results_scroll.pack(fill="both", expand=True, padx=4, pady=(4, 4))

        # Table header
        header_row = ctk.CTkFrame(self.batch_results_scroll, fg_color=ACCENT_LIGHT, corner_radius=4)
        header_row.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(
            header_row, text="#", width=35,
            font=ctk.CTkFont(size=11, weight="bold"), text_color=ACCENT,
        ).pack(side="left", padx=(8, 0))
        ctk.CTkLabel(
            header_row, text="Requirement", width=320,
            font=ctk.CTkFont(size=11, weight="bold"), text_color=ACCENT, anchor="w",
        ).pack(side="left", padx=(8, 0))
        ctk.CTkLabel(
            header_row, text="Label", width=60,
            font=ctk.CTkFont(size=11, weight="bold"), text_color=ACCENT,
        ).pack(side="left", padx=(8, 0))
        ctk.CTkLabel(
            header_row, text="Time", width=60,
            font=ctk.CTkFont(size=11, weight="bold"), text_color=ACCENT,
        ).pack(side="left", padx=(8, 0))

        self.batch_empty_label = ctk.CTkLabel(
            self.batch_results_scroll,
            text="No batch results yet.\nUpload a file to classify multiple requirements.",
            font=ctk.CTkFont(size=12, slant="italic"), text_color=FG_MUTED, justify="center",
        )
        self.batch_empty_label.pack(pady=30)

    # ══════════════════════════════════════════════════════════════════════
    #  STATISTICS TAB
    # ══════════════════════════════════════════════════════════════════════

    def _build_statistics_tab(self):
        tab = self.tabview.tab("  Statistics  ")

        # ── Summary stats row ────────────────────────────────────────────
        self.stats_summary = ctk.CTkFrame(tab, fg_color=BG_CARD, corner_radius=8, border_width=1, border_color=BORDER)
        self.stats_summary.pack(fill="x", padx=4, pady=(8, 8))

        ctk.CTkLabel(
            self.stats_summary, text="Classification Overview",
            font=ctk.CTkFont(family="Georgia", size=14, weight="bold"),
            text_color=ACCENT, anchor="w",
        ).pack(fill="x", padx=16, pady=(12, 8))

        self.stats_cards_frame = ctk.CTkFrame(self.stats_summary, fg_color="transparent")
        self.stats_cards_frame.pack(fill="x", padx=16, pady=(0, 12))

        # Build 3 stat cards
        self.stat_total = self._make_stat_card(self.stats_cards_frame, "Total", "0")
        self.stat_top = self._make_stat_card(self.stats_cards_frame, "Most Common", "—")
        self.stat_avgtime = self._make_stat_card(self.stats_cards_frame, "Avg. Time", "—")

        # ── Chart canvas ─────────────────────────────────────────────────
        chart_frame = ctk.CTkFrame(tab, fg_color=BG_CARD, corner_radius=8, border_width=1, border_color=BORDER)
        chart_frame.pack(fill="both", expand=True, padx=4, pady=(0, 4))

        ctk.CTkLabel(
            chart_frame, text="Category Distribution",
            font=ctk.CTkFont(family="Georgia", size=14, weight="bold"),
            text_color=ACCENT, anchor="w",
        ).pack(fill="x", padx=16, pady=(12, 4))

        self.stats_canvas = tk.Canvas(chart_frame, bg="#FFFFFF", highlightthickness=0)
        self.stats_canvas.pack(fill="both", expand=True, padx=16, pady=(4, 16))
        self.stats_canvas.bind("<Configure>", lambda e: self._draw_chart())

    def _make_stat_card(self, parent, title, value):
        card = ctk.CTkFrame(parent, fg_color=ACCENT_LIGHT, corner_radius=8, width=150, height=60)
        card.pack(side="left", expand=True, fill="x", padx=(0, 8))
        card.pack_propagate(False)

        val_label = ctk.CTkLabel(
            card, text=value,
            font=ctk.CTkFont(family="Georgia", size=20, weight="bold"), text_color=ACCENT,
        )
        val_label.pack(pady=(8, 0))
        ctk.CTkLabel(
            card, text=title,
            font=ctk.CTkFont(size=10), text_color=FG_MUTED,
        ).pack()
        return val_label

    # ══════════════════════════════════════════════════════════════════════
    #  HISTORY PANEL (Right)
    # ══════════════════════════════════════════════════════════════════════

    def _build_history_panel(self, parent):
        right = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=8, border_width=1, border_color=BORDER)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_rowconfigure(1, weight=1)

        hist_header = ctk.CTkFrame(right, fg_color="transparent")
        hist_header.pack(fill="x", padx=14, pady=(12, 4))

        ctk.CTkLabel(
            hist_header, text="Classification History",
            font=ctk.CTkFont(family="Georgia", size=14, weight="bold"),
            text_color=ACCENT, anchor="w",
        ).pack(side="left")

        self.clear_hist_btn = ctk.CTkButton(
            hist_header, text="Clear", width=48, height=24, corner_radius=4,
            fg_color="transparent", hover_color=ACCENT_LIGHT,
            text_color=FG_MUTED, border_width=1, border_color=BORDER,
            font=ctk.CTkFont(size=10), command=self._clear_history,
        )
        self.clear_hist_btn.pack(side="right")

        self.export_hist_btn = ctk.CTkButton(
            hist_header, text="Export", width=52, height=24, corner_radius=4,
            fg_color="transparent", hover_color=ACCENT_LIGHT,
            text_color=FG_MUTED, border_width=1, border_color=BORDER,
            font=ctk.CTkFont(size=10), command=self._export_history,
        )
        self.export_hist_btn.pack(side="right", padx=(0, 6))

        ctk.CTkFrame(right, fg_color=BORDER, height=1).pack(fill="x", padx=14, pady=(6, 0))

        self.history_scroll = ctk.CTkScrollableFrame(right, fg_color="transparent")
        self.history_scroll.pack(fill="both", expand=True, padx=6, pady=(4, 6))

        self.hist_empty_label = ctk.CTkLabel(
            self.history_scroll,
            text="No classifications yet.\nResults will appear here.",
            font=ctk.CTkFont(size=12, slant="italic"), text_color=FG_MUTED, justify="center",
        )
        self.hist_empty_label.pack(pady=40)

    # ══════════════════════════════════════════════════════════════════════
    #  EVENT HANDLERS — CLASSIFY
    # ══════════════════════════════════════════════════════════════════════

    def _on_strategy_change(self, *_args):
        name = self.strategy_var.get()
        self.strategy_desc.configure(text=PROMPT_DESCRIPTIONS.get(name, ""))

    def _clear_placeholder(self, _event=None):
        if self._placeholder_active:
            self.input_box.delete("1.0", "end")
            self._placeholder_active = False

    def _on_clear(self):
        self.input_box.delete("1.0", "end")
        self._placeholder_active = False
        self.result_card.pack_forget()
        self.compare_card.pack_forget()
        self._stop_loading()

    def _on_classify(self):
        self._clear_placeholder()
        text = self.input_box.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Empty Input", "Please enter a requirement to classify.")
            return

        strategy = self.strategy_var.get()
        prompt = PROMPTS[strategy]

        self.classify_btn.configure(state="disabled")
        self.compare_btn.configure(state="disabled")
        self.result_card.pack_forget()
        self.compare_card.pack_forget()
        self._start_loading("Classifying...")

        thread = threading.Thread(target=self._classify_thread, args=(text, prompt, strategy), daemon=True)
        thread.start()

    def _classify_thread(self, text, prompt, strategy):
        result = classify_requirement(text, prompt)
        self.after(0, self._show_result, text, result, strategy)

    def _show_result(self, text, result, strategy):
        self.classify_btn.configure(state="normal")
        self.compare_btn.configure(state="normal")
        self._stop_loading()

        if result["status"] == "error":
            messagebox.showerror("Classification Error", result["error"])
            return

        label = result["label"]
        color = LABEL_COLORS.get(label, ACCENT)
        elapsed = result.get("elapsed", 0)

        self.label_badge.configure(text=f"  {label}  ", fg_color=color)
        self.label_name.configure(text=result["full_name"])
        self.label_desc.configure(text=result["description"])
        self.time_label.configure(text=f"⏱ {elapsed:.2f}s")
        self.result_card.pack(fill="x", pady=(8, 0))

        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.history.insert(0, (timestamp, text, label, result["full_name"], elapsed, strategy))
        self._refresh_history()
        self._refresh_statistics()

    # ══════════════════════════════════════════════════════════════════════
    #  EVENT HANDLERS — COMPARE
    # ══════════════════════════════════════════════════════════════════════

    def _on_compare(self):
        self._clear_placeholder()
        text = self.input_box.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Empty Input", "Please enter a requirement to compare.")
            return

        self.classify_btn.configure(state="disabled")
        self.compare_btn.configure(state="disabled")
        self.result_card.pack_forget()
        self.compare_card.pack_forget()
        self._start_loading("Comparing strategies...")

        thread = threading.Thread(target=self._compare_thread, args=(text,), daemon=True)
        thread.start()

    def _compare_thread(self, text):
        results = {}
        for name, prompt in PROMPTS.items():
            result = classify_requirement(text, prompt)
            results[name] = result
        self.after(0, self._show_compare, text, results)

    def _show_compare(self, text, results):
        self.classify_btn.configure(state="normal")
        self.compare_btn.configure(state="normal")
        self._stop_loading()

        # Clear previous comparison
        for w in self.compare_inner.winfo_children():
            w.destroy()

        any_success = False
        for name in PROMPTS:
            r = results.get(name, {})
            row = ctk.CTkFrame(self.compare_inner, fg_color="transparent")
            row.pack(fill="x", pady=3)

            # Strategy name
            ctk.CTkLabel(
                row, text=name, width=180,
                font=ctk.CTkFont(size=11, weight="bold"), text_color=FG, anchor="w",
            ).pack(side="left")

            if r.get("status") == "success":
                any_success = True
                label = r["label"]
                color = LABEL_COLORS.get(label, ACCENT)
                elapsed = r.get("elapsed", 0)

                ctk.CTkLabel(
                    row, text=f" {label} ",
                    font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
                    text_color="#FFFFFF", fg_color=color,
                    corner_radius=4, width=48, height=24,
                ).pack(side="left", padx=(4, 0))

                ctk.CTkLabel(
                    row, text=r["full_name"],
                    font=ctk.CTkFont(size=11), text_color=FG, anchor="w",
                ).pack(side="left", padx=(8, 0))

                ctk.CTkLabel(
                    row, text=f"⏱ {elapsed:.2f}s",
                    font=ctk.CTkFont(family="Consolas", size=10), text_color=FG_MUTED,
                ).pack(side="right")
            else:
                ctk.CTkLabel(
                    row, text=f"Error: {r.get('error', 'unknown')}",
                    font=ctk.CTkFont(size=11), text_color="#9B2335",
                ).pack(side="left", padx=(4, 0))

        # Check agreement
        labels = [results[n]["label"] for n in PROMPTS if results[n].get("status") == "success"]
        if labels:
            if len(set(labels)) == 1:
                agreement_text = f"✅  All strategies agree: {labels[0]}"
                agreement_color = "#3E6B5A"
            else:
                agreement_text = "⚠  Strategies disagree — review the results above"
                agreement_color = "#8B6914"

            ctk.CTkLabel(
                self.compare_inner, text=agreement_text,
                font=ctk.CTkFont(size=12, weight="bold"), text_color=agreement_color, anchor="w",
            ).pack(fill="x", pady=(8, 0))

        self.compare_card.pack(fill="x", pady=(8, 0))

        # Add to history (use the improved zero-shot result)
        if any_success:
            best = results.get("Improved Zero-Shot", {})
            if best.get("status") == "success":
                timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                self.history.insert(0, (
                    timestamp, text, best["label"], best["full_name"],
                    best.get("elapsed", 0), "Compare",
                ))
                self._refresh_history()
                self._refresh_statistics()

    # ══════════════════════════════════════════════════════════════════════
    #  EVENT HANDLERS — BATCH
    # ══════════════════════════════════════════════════════════════════════

    def _on_batch_upload(self):
        if self._batch_running:
            messagebox.showwarning("Busy", "A batch classification is already running.")
            return

        filepath = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("Text files", "*.txt"), ("All files", "*.*")],
            title="Select Requirements File",
        )
        if not filepath:
            return

        requirements = self._parse_file(filepath)
        if not requirements:
            messagebox.showwarning("Empty File", "No requirements found in the selected file.")
            return

        self._batch_running = True
        self.batch_results.clear()
        self.batch_upload_btn.configure(state="disabled")
        self.batch_progress_bar.set(0)
        self.batch_status_label.configure(text=f"Classifying {len(requirements)} requirements...")

        # Clear previous results (keep header)
        children = self.batch_results_scroll.winfo_children()
        for child in children[1:]:  # skip header row
            child.destroy()

        self.batch_empty_label = None

        thread = threading.Thread(
            target=self._batch_thread, args=(requirements,), daemon=True,
        )
        thread.start()

    def _parse_file(self, filepath):
        """Parse CSV or TXT file and return list of requirement strings."""
        requirements = []
        ext = os.path.splitext(filepath)[1].lower()

        if ext == ".csv":
            try:
                with open(filepath, "r", encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f)
                    # Find the requirement column
                    req_col = None
                    for col in reader.fieldnames or []:
                        if col.strip().lower() in ("requirement", "requirements", "text", "description", "req"):
                            req_col = col
                            break
                    if req_col is None and reader.fieldnames:
                        req_col = reader.fieldnames[0]  # fallback to first column

                    if req_col:
                        for row in reader:
                            text = row.get(req_col, "").strip()
                            if text:
                                requirements.append(text)
            except Exception as e:
                messagebox.showerror("File Error", f"Could not read CSV: {e}")
        else:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    for line in f:
                        text = line.strip()
                        if text:
                            requirements.append(text)
            except Exception as e:
                messagebox.showerror("File Error", f"Could not read file: {e}")

        return requirements

    def _batch_thread(self, requirements):
        strategy = self.batch_strategy_var.get()
        prompt = PROMPTS[strategy]
        total = len(requirements)

        for i, text in enumerate(requirements):
            if not self._batch_running:
                self.after(0, self._batch_stopped, i, total)
                return

            result = classify_requirement(text, prompt)
            self.after(0, self._batch_update, i, total, text, result, strategy)
            time.sleep(0.05)  # small delay to avoid rate limits

        self.after(0, self._batch_done, total)

    def _batch_update(self, index, total, text, result, strategy):
        progress = (index + 1) / total
        self.batch_progress_bar.set(progress)
        self.batch_status_label.configure(
            text=f"Classified {index + 1} / {total}  ({progress * 100:.0f}%)"
        )

        if result["status"] == "success":
            label = result["label"]
            elapsed = result.get("elapsed", 0)
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")

            self.batch_results.append((timestamp, text, label, result["full_name"], elapsed, strategy))

            # Add row to table
            bg = "#F8F9FA" if index % 2 == 0 else BG_CARD
            row = ctk.CTkFrame(self.batch_results_scroll, fg_color=bg, corner_radius=4)
            row.pack(fill="x", pady=1)

            ctk.CTkLabel(
                row, text=str(index + 1), width=35,
                font=ctk.CTkFont(size=11), text_color=FG_MUTED,
            ).pack(side="left", padx=(8, 0))

            display_text = text if len(text) <= 60 else text[:57] + "…"
            ctk.CTkLabel(
                row, text=display_text, width=320,
                font=ctk.CTkFont(size=11), text_color=FG, anchor="w",
            ).pack(side="left", padx=(8, 0))

            color = LABEL_COLORS.get(label, ACCENT)
            ctk.CTkLabel(
                row, text=f" {label} ",
                font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
                text_color="#FFFFFF", fg_color=color,
                corner_radius=3, width=48, height=20,
            ).pack(side="left", padx=(8, 0))

            ctk.CTkLabel(
                row, text=f"{elapsed:.2f}s",
                font=ctk.CTkFont(family="Consolas", size=10), text_color=FG_MUTED,
            ).pack(side="left", padx=(8, 0))

            # Also add to main history
            self.history.insert(0, (timestamp, text, label, result["full_name"], elapsed, strategy))

    def _batch_done(self, total):
        self._batch_running = False
        self.batch_upload_btn.configure(state="normal")
        self.batch_status_label.configure(text=f"✅  Done — {total} requirements classified")
        self._refresh_history()
        self._refresh_statistics()

    def _batch_stopped(self, stopped_at, total):
        self._batch_running = False
        self.batch_upload_btn.configure(state="normal")
        self.batch_status_label.configure(text=f"⛔  Stopped at {stopped_at} / {total}")
        self._refresh_history()
        self._refresh_statistics()

    def _on_batch_stop(self):
        self._batch_running = False

    def _on_batch_export(self):
        if not self.batch_results:
            messagebox.showinfo("Export", "No batch results to export.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Batch Results",
        )
        if not filepath:
            return

        try:
            with open(filepath, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Label", "Category", "Time (s)", "Strategy", "Requirement"])
                for ts, text, label, full, elapsed, strat in self.batch_results:
                    writer.writerow([ts, label, full, f"{elapsed:.2f}", strat, text])
            messagebox.showinfo("Export", f"Batch results exported to:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    # ══════════════════════════════════════════════════════════════════════
    #  LOADING ANIMATION
    # ══════════════════════════════════════════════════════════════════════

    def _start_loading(self, text="Classifying..."):
        self.loading_label.configure(text=text)
        self.loading_frame.pack(fill="x", pady=(4, 0))
        self.loading_bar.start()
        self._anim_dots = 0
        self._anim_base_text = text.rstrip(".")
        self._animate_dots()

    def _stop_loading(self):
        self.loading_bar.stop()
        self.loading_frame.pack_forget()
        if self._anim_id is not None:
            self.after_cancel(self._anim_id)
            self._anim_id = None

    def _animate_dots(self):
        self._anim_dots = (self._anim_dots % 3) + 1
        dots = "." * self._anim_dots
        self.loading_label.configure(text=f"{self._anim_base_text}{dots}")
        self._anim_id = self.after(400, self._animate_dots)

    # ══════════════════════════════════════════════════════════════════════
    #  HISTORY
    # ══════════════════════════════════════════════════════════════════════

    def _refresh_history(self):
        for w in self.history_scroll.winfo_children():
            w.destroy()

        if not self.history:
            self.hist_empty_label = ctk.CTkLabel(
                self.history_scroll,
                text="No classifications yet.\nResults will appear here.",
                font=ctk.CTkFont(size=12, slant="italic"), text_color=FG_MUTED, justify="center",
            )
            self.hist_empty_label.pack(pady=40)
            return

        # Show last 50 entries max
        for i, (ts, text, label, full, elapsed, strategy) in enumerate(self.history[:50]):
            color = LABEL_COLORS.get(label, ACCENT)
            entry_bg = "#F8F9FA" if i % 2 == 0 else BG_CARD

            entry = ctk.CTkFrame(self.history_scroll, fg_color=entry_bg, corner_radius=6)
            entry.pack(fill="x", pady=2, padx=2)

            top_row = ctk.CTkFrame(entry, fg_color="transparent")
            top_row.pack(fill="x", padx=10, pady=(6, 1))

            ctk.CTkLabel(
                top_row, text=f" {label} ",
                font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
                text_color="#FFFFFF", fg_color=color,
                corner_radius=3, width=38, height=18,
            ).pack(side="left")

            ctk.CTkLabel(
                top_row, text=full,
                font=ctk.CTkFont(size=11, weight="bold"), text_color=FG, anchor="w",
            ).pack(side="left", padx=(6, 0))

            ctk.CTkLabel(
                top_row, text=f"{elapsed:.2f}s",
                font=ctk.CTkFont(family="Consolas", size=9), text_color=FG_MUTED,
            ).pack(side="right")

            ctk.CTkLabel(
                top_row, text=ts,
                font=ctk.CTkFont(size=9), text_color=FG_MUTED,
            ).pack(side="right", padx=(0, 6))

            display_text = text if len(text) <= 80 else text[:77] + "…"
            ctk.CTkLabel(
                entry, text=display_text,
                font=ctk.CTkFont(size=10), text_color=FG_MUTED,
                anchor="w", wraplength=260,
            ).pack(fill="x", padx=10, pady=(0, 6))

    def _clear_history(self):
        self.history.clear()
        self._refresh_history()
        self._refresh_statistics()

    def _export_history(self):
        if not self.history:
            messagebox.showinfo("Export", "No history to export.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Classification History",
        )
        if not filepath:
            return

        try:
            with open(filepath, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Label", "Category", "Time (s)", "Strategy", "Requirement"])
                for ts, text, label, full, elapsed, strategy in self.history:
                    writer.writerow([ts, label, full, f"{elapsed:.2f}", strategy, text])
            messagebox.showinfo("Export", f"History exported to:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    # ══════════════════════════════════════════════════════════════════════
    #  STATISTICS
    # ══════════════════════════════════════════════════════════════════════

    def _refresh_statistics(self):
        if not self.history:
            self.stat_total.configure(text="0")
            self.stat_top.configure(text="—")
            self.stat_avgtime.configure(text="—")
            self._draw_chart()
            return

        total = len(self.history)
        counts = Counter(entry[2] for entry in self.history)
        top_label = counts.most_common(1)[0]
        avg_time = sum(entry[4] for entry in self.history) / total

        self.stat_total.configure(text=str(total))
        self.stat_top.configure(text=f"{top_label[0]} ({top_label[1]})")
        self.stat_avgtime.configure(text=f"{avg_time:.2f}s")

        self._draw_chart()

    def _draw_chart(self):
        canvas = self.stats_canvas
        canvas.delete("all")

        w = canvas.winfo_width()
        h = canvas.winfo_height()

        if w < 10 or h < 10:
            return

        if not self.history:
            canvas.create_text(
                w // 2, h // 2, text="No data yet — classify some requirements first",
                font=("Georgia", 12, "italic"), fill="#9CA3AF",
            )
            return

        counts = Counter(entry[2] for entry in self.history)
        total = sum(counts.values())
        max_count = max(counts.values()) if counts else 1

        margin_left = 70
        margin_right = 90
        margin_top = 20
        bar_height = max(18, min(32, (h - margin_top - 20) // len(LABELS_ORDER) - 10))
        gap = max(6, min(14, (h - margin_top - 20 - bar_height * len(LABELS_ORDER)) // (len(LABELS_ORDER))))
        bar_area_w = w - margin_left - margin_right

        for i, lk in enumerate(LABELS_ORDER):
            count = counts.get(lk, 0)
            y = margin_top + i * (bar_height + gap)
            pct = (count / total * 100) if total > 0 else 0

            # Label
            canvas.create_text(
                margin_left - 10, y + bar_height // 2,
                text=lk, anchor="e",
                font=("Consolas", 11, "bold"), fill=LABEL_COLORS.get(lk, ACCENT),
            )

            # Background bar
            canvas.create_rectangle(
                margin_left, y, margin_left + bar_area_w, y + bar_height,
                fill=LABEL_COLORS_LIGHT.get(lk, "#F0F0F0"), outline="",
            )

            # Filled bar
            if count > 0:
                fill_w = max(4, (count / max_count) * bar_area_w)
                canvas.create_rectangle(
                    margin_left, y, margin_left + fill_w, y + bar_height,
                    fill=LABEL_COLORS.get(lk, ACCENT), outline="",
                )

            # Count + percentage
            canvas.create_text(
                margin_left + bar_area_w + 8, y + bar_height // 2,
                text=f"{count}  ({pct:.0f}%)", anchor="w",
                font=("Consolas", 10), fill=FG_MUTED,
            )

    # ══════════════════════════════════════════════════════════════════════
    #  ENTRY POINT
    # ══════════════════════════════════════════════════════════════════════


if __name__ == "__main__":
    app = ClassifierApp()
    app.mainloop()
