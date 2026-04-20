import tkinter as tk
import customtkinter as ctk
import sys
import os

from config import *
from config import APP_THEME
from languages import LANGS, LANG_NAMES, LANG_CODES


def _patch_combo_hover_text(combo):
    """
    Fixes CTkComboBox hover text color in light theme.

    In CTK 5.2.x the dropdown is a tk.Menu subclass (DropdownMenu). CTK sets
    activeforeground (the text color while hovering) to the same dark value as
    the normal foreground, which is unreadable on the blue hover background.
    We override it to white after the combo is initialised.

    The fix is a single configure(activeforeground="#ffffff") call. Because
    tk.Menu applies this widget-level option to all entries — present and
    future — no further patching is needed when values are refreshed.

    No-op in dark theme (CTK already uses near-white text there).
    """
    if APP_THEME != "light":
        return
    try:
        menu = getattr(combo, "_dropdown_menu", None)
        if menu is None:
            return
        # Primary: call CTK/Tkinter configure
        menu.configure(activeforeground=COLOR_TEXT_ON_ACCENT)
    except Exception:
        try:
            # Fallback: call tk.Menu base configure directly in case CTK
            # overrides configure() and rejects unknown parameters
            tk.Menu.configure(menu, activeforeground=COLOR_TEXT_ON_ACCENT)
        except Exception:
            pass


class UIBuilderMixin:
    """Builds all widgets for the graphical user interface using CustomTkinter."""

    def detect_os_language(self):
        """
        Detects the OS language for Windows, macOS, and Linux.
        Returns 'FR' if French is detected, otherwise 'EN'.
        """
        try:
            import locale
            import sys

            # 1. Try standard Python locale detection
            lang_code, _ = locale.getlocale()

            # 2. Specific handling for Windows if locale failed
            if (not lang_code or lang_code == 'None') and sys.platform == "win32":
                try:
                    import ctypes as _ctypes
                    windll = _ctypes.windll.kernel32
                    lang_id = windll.GetUserDefaultUILanguage()
                    lang_code = locale.windows_locale.get(lang_id)
                except Exception:
                    pass

            # 3. Specific handling for Linux/macOS via environment variables
            if not lang_code or lang_code == 'None':
                for env_var in ('LC_ALL', 'LC_MESSAGES', 'LANG'):
                    val = os.environ.get(env_var)
                    if val:
                        lang_code = val
                        break

            # 4. Final check: does the string contain 'fr'
            if lang_code and lang_code.lower().startswith('fr'):
                return "FR"

        except Exception:
            pass

        return "EN"

    def set_window_icon(self):
        """
        Sets the application window icon for the taskbar and title bar.
        Works for both frozen (PyInstaller) and normal Python execution.
        """
        if getattr(sys, "frozen", False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")
        icon_path = os.path.join(base_path, ICON_NAME)
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception:
                pass

    def create_custom_button(
        self,
        parent,
        text,
        command,
        bg_color=COLOR_BTN_DEFAULT,
        fg_color=COLOR_TEXT_BRIGHT,
        font=None,
        padx=15,
        pady=3
    ):
        """
        Creates a CTkButton styled as a custom action button.

        Args:
            parent: The parent CTK/tk container.
            text (str): Button label text (may include emoji).
            command (callable): Function executed on click.
            bg_color (str): Button background color.
            fg_color (str): Button text/icon color.
            font (tuple|None): Font specification as (family, size, weight).
            padx (int): Horizontal inner padding (scaled).
            pady (int): Vertical inner padding.

        Returns:
            ctk.CTkButton: The created button widget.
        """
        if font is None:
            ctk_font = ctk.CTkFont(family=self._emoji_font, size=12, weight="bold")
        else:
            weight = font[2] if len(font) > 2 else "normal"
            ctk_font = ctk.CTkFont(family=font[0], size=font[1], weight=weight)

        # Measure the exact width of the text with the current font
        text_width = ctk_font.measure(text)

        # Final width = text width + 30px on each side
        final_width = text_width + (padx * 2)

        btn = ctk.CTkButton(
            parent,
            text=text,
            command=command,
            fg_color=bg_color,
            hover_color=COLOR_BTN_ACTIVE,
            text_color=fg_color,
            font=ctk_font,
            corner_radius=5,
            border_width=0,
            height=28,
            width=final_width,
        )
        return btn

    def setup_ui(self):
        """
        Builds the complete UI layout using CustomTkinter widgets.
        Structure: header row → sub-header row → main text area → footer row.
        """
        # Configure root grid weights so text area expands
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(2, weight=1)

        current_lang_str = self.current_lang.get()
        l_ui = LANGS.get(current_lang_str, LANGS["EN"])

        # Helper: get first font family name for CTkFont
        main_fam  = self._main_font
        emoji_fam = self._emoji_font
        mono_fam  = self._mono_font

        # ──────────────────────────────────────────────────────────────
        # HEADER ROW (row 0)
        # ──────────────────────────────────────────────────────────────
        header = ctk.CTkFrame(
            self.root, fg_color=COLOR_BG_HEADER, corner_radius=0
        )
        header.grid(row=0, column=0, sticky="ew", pady=(5, 0))

        h_left = ctk.CTkFrame(header, fg_color=COLOR_BG_HEADER, corner_radius=0)
        h_left.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=5)

        # --- Button: Open log file ---
        self.btn_log = self.create_custom_button(h_left, l_ui["log"], self.open_file)
        self.btn_log.pack(side=tk.LEFT, padx=5)
        self.btn_open_tooltip = ToolTip(self.btn_log, l_ui["tip_open"], scale=self.scale)

        # --- Button: Export log ---
        self.btn_exp = self.create_custom_button(h_left, l_ui["exp"], self.export_log)
        self.btn_exp.pack(side=tk.LEFT, padx=5)
        self.btn_export_tooltip = ToolTip(self.btn_exp, l_ui["tip_export"], scale=self.scale)

        # --- Button: Upload to Pastebin ---
        self.btn_upl = self.create_custom_button(h_left, l_ui["upl"], self.upload_to_pastebin)
        self.btn_upl.pack(side=tk.LEFT, padx=5)
        self.btn_upload_tooltip = ToolTip(self.btn_upl, l_ui["tip_upload"], scale=self.scale)

        # Vertical separator
        tk.Frame(h_left, bg=COLOR_SEPARATOR, width=2).pack(
            side=tk.LEFT, fill=tk.Y, padx=self.sc(15), pady=10
        )

        # --- Button: Show system summary ---
        self.btn_sum = self.create_custom_button(h_left, l_ui["sum"], self.show_summary)
        self.btn_sum.pack(side=tk.LEFT, padx=5)
        self.btn_summary_tooltip = ToolTip(self.btn_sum, l_ui["tip_summary"], scale=self.scale)

        # --- Button: Clear console ---
        self.btn_clr = self.create_custom_button(h_left, l_ui["clr"], self.clear_console)
        self.btn_clr.pack(side=tk.LEFT, padx=5)
        self.btn_clear_tooltip = ToolTip(self.btn_clr, l_ui["tip_clear"], scale=self.scale)

        # Vertical separator
        tk.Frame(h_left, bg=COLOR_SEPARATOR, width=2).pack(
            side=tk.LEFT, fill=tk.Y, padx=(self.sc(15), self.sc(5)), pady=10
        )

        # --- Filter toggle buttons frame ---
        self.filter_frame = ctk.CTkFrame(h_left, fg_color=COLOR_BG_HEADER, corner_radius=0)
        self.filter_frame.pack(side=tk.LEFT, padx=5)

        # Dictionary to store filter button widget references
        self.filter_widgets = {}
        self.filter_tooltips = {}

        filter_modes = ["all", "info", "warning", "error", "debug"]
        tm = {
            "all":     "all",
            "info":    "info",
            "warning": "warn",
            "error":   "err",
            "debug":   "debug",
        }

        for mode in filter_modes:
            translated_text = l_ui.get(tm[mode], mode.upper())

            btn_font = ctk.CTkFont(family=emoji_fam, size=12, weight="bold")
            text_width = btn_font.measure(translated_text)

            cb = ctk.CTkButton(
                self.filter_frame,
                text=translated_text,
                fg_color=COLOR_BTN_DEFAULT,
                hover_color=COLOR_BTN_ACTIVE,
                text_color=COLOR_TEXT_BRIGHT,
                font=btn_font,
                corner_radius=5,
                border_width=0,
                height=28,
                hover=False,
                width=text_width + 30,  # 15px padding on each side (same as action buttons)
                command=lambda m=mode: (
                    self.filter_vars[m].set(not self.filter_vars[m].get()),
                    self.on_filter_toggle(m)
                ),
            )
            cb.pack(side=tk.LEFT, padx=5)

            # Manual hover bindings preserve active-state color logic
            cb.bind(
                "<Enter>",
                lambda event, w=cb, m=mode: self.on_hover_filter(w, m, True)
            )
            cb.bind(
                "<Leave>",
                lambda event, w=cb, m=mode: self.on_hover_filter(w, m, False)
            )

            self.filter_widgets[mode] = cb
            tip_key = f"tip_filter_{mode}"
            self.filter_tooltips[mode] = ToolTip(cb, l_ui[tip_key], scale=self.scale)

        # --- Right side of header ---
        h_right = ctk.CTkFrame(header, fg_color=COLOR_BG_HEADER, corner_radius=0)
        h_right.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

        # --- Language selection combobox ---
        # Show full names in the dropdown; current_lang still stores the code (FR/EN/…)
        lang_display_values = [LANG_NAMES[k] for k in sorted(LANGS.keys())]
        initial_display = LANG_NAMES.get(current_lang_str, current_lang_str)

        self.combo_lang = ctk.CTkComboBox(
            h_right,
            values=lang_display_values,
            state="readonly",
            width=90,
            fg_color=COLOR_BTN_DEFAULT,
            text_color=COLOR_TEXT_MAIN,
            dropdown_fg_color=COLOR_BTN_DEFAULT,
            dropdown_text_color=COLOR_TEXT_MAIN,
            dropdown_hover_color=COLOR_ACCENT,
            button_color=COLOR_BTN_DEFAULT,
            button_hover_color=COLOR_BTN_ACTIVE,
            border_color=COLOR_BTN_DEFAULT,
            border_width=0,
            corner_radius=5,
            font=ctk.CTkFont(family=main_fam, size=12),
            command=lambda val: self.change_language(),
        )
        self.combo_lang.set(initial_display)
        self.combo_lang.pack(side=tk.LEFT, padx=5)
        _patch_combo_hover_text(self.combo_lang)
        self.combo_lang_tooltip = ToolTip(self.combo_lang, l_ui["tip_lang"], scale=self.scale)

        # Vertical separator
        # tk.Frame(h_right, bg=COLOR_SEPARATOR, width=2).pack(
            # side=tk.LEFT, fill=tk.Y, padx=15, pady=6
        # )

        # --- Single Instance toggle button ---
        initial_icon = "🔒" if self.enable_single_instance_var else "🔓"
        self.btn_single_instance = self.create_custom_button(
            h_right,
            initial_icon,
            self.toggle_single_instance,
            font=(emoji_fam, 12),
            bg_color=COLOR_BTN_SECONDARY,
            padx=12,
            pady=3
        )
        self.btn_single_instance.pack(side=tk.LEFT, padx=5)
        _tip_si_key = "tip_single_instance" if self.enable_single_instance_var else "tip_multi_instance"
        self.btn_single_instance_tooltip = ToolTip(
            self.btn_single_instance, l_ui[_tip_si_key], scale=self.scale
        )

        # Vertical separator
        tk.Frame(h_right, bg=COLOR_SEPARATOR, width=2).pack(
            side=tk.LEFT, fill=tk.Y, padx=self.sc(15), pady=2
        )

        # --- App color theme cycle button (🌙 dark / ☀ light) ---
        _theme_icon = "🌙" if APP_THEME == "dark" else "☀"
        self.btn_theme = self.create_custom_button(
            h_right,
            _theme_icon,
            self.cycle_app_theme,
            font=(emoji_fam, 12),
            bg_color=COLOR_BTN_SECONDARY,
            padx=10,
            pady=3
        )
        self.btn_theme.pack(side=tk.LEFT, padx=5)
        _next_tip = {"dark": "tip_theme_light", "light": "tip_theme_dark"}
        _tip_key = _next_tip.get(APP_THEME, "tip_theme_light")
        self.btn_theme_tooltip = ToolTip(self.btn_theme, l_ui.get(_tip_key, "Toggle theme"), scale=self.scale)

        # --- Help button ---
        self.btn_help = self.create_custom_button(
            h_right,
            "?",
            self.show_help,
            font=(main_fam, 12, "bold"),
            bg_color=COLOR_BTN_SECONDARY,
            padx=12,
            pady=3
        )
        self.btn_help.pack(side=tk.LEFT, padx=5)
        self.btn_help_tooltip = ToolTip(self.btn_help, l_ui["tip_help"], scale=self.scale)

        # ──────────────────────────────────────────────────────────────
        # SUB-HEADER ROW (row 1) — secondary toolbar
        # ──────────────────────────────────────────────────────────────
        sub_header = ctk.CTkFrame(
            self.root, fg_color=COLOR_BG_HEADER, corner_radius=0
        )
        sub_header.grid(row=1, column=0, sticky="ew", pady=(0, 5))

        # Left side of the sub-header
        sh_left = ctk.CTkFrame(sub_header, fg_color=COLOR_BG_HEADER, corner_radius=0)
        sh_left.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=5)

        # --- Keyword list management box ---
        kw_box = ctk.CTkFrame(sh_left, fg_color=COLOR_BG_HEADER, corner_radius=0)
        kw_box.pack(side=tk.LEFT)

        # Keyword list combobox
        self.combo_lists = ctk.CTkComboBox(
            kw_box,
            variable=self.selected_list,
            values=[],
            state="readonly",
            width=180,
            fg_color=COLOR_BTN_DEFAULT,
            text_color=COLOR_TEXT_MAIN,
            dropdown_fg_color=COLOR_BTN_DEFAULT,
            dropdown_text_color=COLOR_TEXT_MAIN,
            dropdown_hover_color=COLOR_ACCENT,
            button_color=COLOR_BTN_DEFAULT,
            button_hover_color=COLOR_BTN_ACTIVE,
            border_color=COLOR_BTN_DEFAULT,
            border_width=0,
            corner_radius=5,
            font=ctk.CTkFont(family=main_fam, size=12),
            command=lambda val: [self.on_list_selected(), self.txt_area.focus_set()],
        )
        self.combo_lists.pack(side=tk.LEFT, padx=5)
        _patch_combo_hover_text(self.combo_lists)
        self.combo_kw_tooltip = ToolTip(self.combo_lists, l_ui["tip_kw_list"], scale=self.scale)

        # Keyword list refresh button — same style as option toggle buttons (♾ ↩ ⏸️)
        btn_refresh = ctk.CTkButton(
            kw_box,
            text="🔄",
            font=ctk.CTkFont(family=emoji_fam, size=12),
            fg_color=COLOR_BTN_DEFAULT,
            hover=False,
            text_color=COLOR_TEXT_BRIGHT,
            corner_radius=5,
            border_width=0,
            height=28,
            width=40,
            command=self.refresh_keyword_list,
        )
        btn_refresh.pack(side=tk.LEFT, padx=5)
        btn_refresh.bind("<Enter>", lambda e: btn_refresh.configure(fg_color=COLOR_BTN_ACTIVE))
        btn_refresh.bind("<Leave>", lambda e: btn_refresh.configure(fg_color=COLOR_BTN_DEFAULT))
        self.btn_kw_refresh_tooltip = ToolTip(btn_refresh, l_ui["tip_kw_refresh"], scale=self.scale)

        # Open keyword folder button — same style as option toggle buttons (♾ ↩ ⏸️)
        btn_folder = ctk.CTkButton(
            kw_box,
            text="📁",
            font=ctk.CTkFont(family=emoji_fam, size=12),
            fg_color=COLOR_BTN_DEFAULT,
            hover=False,
            text_color=COLOR_TEXT_BRIGHT,
            corner_radius=5,
            border_width=0,
            height=28,
            width=40,
            command=self.open_keyword_folder,
        )
        btn_folder.pack(side=tk.LEFT, padx=5)
        btn_folder.bind("<Enter>", lambda e: btn_folder.configure(fg_color=COLOR_BTN_ACTIVE))
        btn_folder.bind("<Leave>", lambda e: btn_folder.configure(fg_color=COLOR_BTN_DEFAULT))
        self.btn_kw_folder_tooltip = ToolTip(btn_folder, l_ui["tip_kw_folder"], scale=self.scale)

        # Vertical separator
        tk.Frame(sh_left, bg=COLOR_SEPARATOR, width=2).pack(
            side=tk.LEFT, fill=tk.Y, padx=self.sc(15), pady=8
        )

        # --- Search box ---
        search_box = ctk.CTkFrame(
            sh_left,
            fg_color=COLOR_BG_MAIN,
            corner_radius=6,
            border_width=1,
            border_color=COLOR_BTN_DEFAULT
        )
        search_box.pack(side=tk.LEFT, padx=5)

        # Search icon label
        ctk.CTkLabel(
            search_box,
            text="🔍",
            fg_color=COLOR_BG_MAIN,
            text_color=COLOR_TEXT_DIM,
            font=ctk.CTkFont(family=emoji_fam, size=12),
        ).pack(side=tk.LEFT, padx=(8, 0), pady=(1, 1))

        # Search entry field — kept as tk.Entry for full API compatibility
        # (icursor, selection_range, event_generate, etc. used throughout actions.py).
        # Wrapped in a plain tk.Frame so the placeholder label can be positioned
        # with relative coordinates (rely=0.5) instead of fragile pixel offsets.
        _entry_frame = tk.Frame(search_box, bg=COLOR_BG_MAIN)
        _entry_frame.pack(side=tk.LEFT, padx=5, pady=3)

        self.search_entry = tk.Entry(
            _entry_frame,
            textvariable=self.search_query,
            bg=COLOR_BG_MAIN,
            fg=COLOR_TEXT_BRIGHT,
            borderwidth=0,
            width=30,
            insertbackground=COLOR_TEXT_BRIGHT,
            font=(main_fam, 12),
            relief="flat",
            highlightthickness=1,
            highlightbackground=COLOR_BG_MAIN,
            highlightcolor=COLOR_BG_MAIN,
        )
        self.search_entry.pack(fill=tk.BOTH, expand=True)

        # --- Visual Placeholder Overlay ---
        # Placed inside _entry_frame with relative coordinates:
        # rely=0.5 + anchor="w" = always vertically centred, regardless of OS or scale.
        # x=5 is a small fixed left-padding (does not depend on scale).
        placeholder_text = l_ui.get("search_localy", "Rechercher")

        self.placeholder_label = tk.Label(
            _entry_frame,
            text=placeholder_text,
            font=(main_fam, 12),
            bg=COLOR_BG_MAIN,
            fg=COLOR_TEXT_LIGHT,   # Very light gray
            cursor="xterm",        # Cursor looks like a text selector
        )
        self.placeholder_label.place(relx=0, rely=0.5, anchor="w", x=5)

        def handle_placeholder(event=None):
            """Hide label if there is text or if the field is focused."""
            if self.search_query.get() or self.search_entry.focus_get() == self.search_entry:
                self.placeholder_label.place_forget()
            else:
                self.placeholder_label.place(relx=0, rely=0.5, anchor="w", x=5)

        # Click on the placeholder must focus the entry
        self.placeholder_label.bind("<Button-1>", lambda e: self.search_entry.focus_set())

        # Update visibility on focus and when typing
        self.search_entry.bind("<FocusIn>", lambda e: self.placeholder_label.place_forget())
        self.search_entry.bind("<FocusOut>", handle_placeholder)

        # Trace the variable to show/hide placeholder if text is cleared via code
        self.search_query.trace_add("write", lambda *args: handle_placeholder())

        # Initial check
        handle_placeholder()

        # Context menu on right-click in search field
        self.search_entry.bind("<Button-3>", self.show_search_context_menu)
        self.search_entry.bind("<Escape>", self.reset_search_and_focus_log)
        self.search_entry.bind("<Return>", self.validate_and_save_search)

        # Fixed-size container for the "×" clear button (prevents accordion effect)
        clear_container = ctk.CTkFrame(
            search_box, fg_color=COLOR_BG_MAIN, corner_radius=0, width=20, height=20
        )
        clear_container.pack(side=tk.LEFT)
        clear_container.pack_propagate(False)

        # "×" clear button — tk.Label for precise vertical centering (CTkLabel has
        # fixed internal padding that ignores font size and resists centering).
        self.btn_clear_search = tk.Label(
            clear_container,
            text="×",
            bg=COLOR_BG_MAIN,
            fg=COLOR_TEXT_DIM,
            font=(main_fam, 13, "bold"),
            cursor="hand2",
            padx=0,
            pady=0,
            anchor="center",
        )
        self.btn_clear_search.bind(
            "<Enter>", lambda e: self.btn_clear_search.configure(fg=COLOR_TEXT_BRIGHT)
        )
        self.btn_clear_search.bind(
            "<Leave>", lambda e: self.btn_clear_search.configure(fg=COLOR_TEXT_DIM)
        )
        self.btn_clear_search.bind("<Button-1>", lambda event: self.clear_search())

        if not self.search_query.get():
            self.btn_clear_search.place_forget()
        else:
            self.btn_clear_search.place(relx=0.5, rely=0.5, anchor="center")

        self.search_bar_tooltip = ToolTip(
            self.search_entry,
            l_ui["tip_search_bar"],
            scale=self.scale,
            condition=lambda: (
                self.root.focus_get() != self.search_entry and
                self.root.focus_get() != self.history_listbox
            )
        )

        # Clear search history button
        self.btn_clear_history = ctk.CTkButton(
            search_box,
            text="🗑",
            fg_color=COLOR_BG_MAIN,
            hover_color=COLOR_BG_MAIN,
            text_color=COLOR_TEXT_DIM,
            font=ctk.CTkFont(family=main_fam, size=12),
            border_width=0,
            corner_radius=0,
            width=28,
            height=28,
            command=self.show_history_manager,
            cursor="hand2",
        )
        self.btn_clear_history.pack(side=tk.RIGHT, padx=(4, 4), pady=(1, 1))
        self.btn_clear_history.bind(
            "<Enter>", lambda e: self.btn_clear_history.configure(text_color=COLOR_TEXT_BRIGHT)
        )
        self.btn_clear_history.bind(
            "<Leave>", lambda e: self.btn_clear_history.configure(
                text_color=COLOR_TEXT_DIM if self.search_history else COLOR_TEXT_LIGHT
            )
        )
        tip_text = l_ui.get("btn_clear_history", "Delete all search history")
        self.history_clear_tooltip = ToolTip(self.btn_clear_history, tip_text, scale=self.scale)

        # Exclusion list button — ☰ = no exclusions, ⛔ = active exclusions.
        # Placed in sh_left, between the search box and the options separator,
        # with the same visual style as the limit/wrap/pause toggle buttons.
        self.btn_exclude_list = ctk.CTkButton(
            sh_left,
            text="☰",
            font=ctk.CTkFont(family=emoji_fam, size=12),
            fg_color=COLOR_BTN_DEFAULT,
            hover=False,
            text_color=COLOR_TEXT_BRIGHT,
            corner_radius=5,
            border_width=0,
            height=28,
            width=40,
            command=self.show_exclude_list,
        )
        self.btn_exclude_list.pack(side=tk.LEFT, padx=(self.sc(10), self.sc(5)))
        self.btn_exclude_list.bind("<Enter>", lambda e: self.btn_exclude_list.configure(
            fg_color=self._lighten_color(COLOR_DANGER, 0.25) if self.exclude_patterns else COLOR_BTN_ACTIVE,
            text_color=COLOR_TEXT_ON_ACCENT if self.exclude_patterns else COLOR_TEXT_BRIGHT,
        ))
        self.btn_exclude_list.bind("<Leave>", lambda e: self.btn_exclude_list.configure(
            fg_color=COLOR_DANGER if self.exclude_patterns else COLOR_BTN_DEFAULT,
            text_color=COLOR_TEXT_ON_ACCENT if self.exclude_patterns else COLOR_TEXT_BRIGHT,
        ))
        self.exclude_list_tooltip = ToolTip(
            self.btn_exclude_list,
            l_ui.get("tip_exclude_empty", "No active exclusions"),
            scale=self.scale,
        )

        # Vertical separator
        tk.Frame(sh_left, bg=COLOR_SEPARATOR, width=2).pack(
            side=tk.LEFT, fill=tk.Y, padx=self.sc(15), pady=8
        )

        # --- Options toggle buttons ---
        opt_box = ctk.CTkFrame(sh_left, fg_color=COLOR_BG_HEADER, corner_radius=0)
        opt_box.pack(side=tk.LEFT)

        # Common style for option toggle buttons
        opt_btn_common = dict(
            fg_color=COLOR_BTN_DEFAULT,
            hover=False,
            text_color=COLOR_TEXT_BRIGHT,
            corner_radius=5,
            border_width=0,
            height=28,
            width=40,
        )

        def _add_opt_hover(widget, active_color=None):
            """Add manual hover bindings for option toggle buttons."""
            widget.bind(
                "<Enter>",
                lambda e: widget.configure(fg_color=COLOR_BTN_ACTIVE)
            )
            if active_color:
                widget.bind(
                    "<Leave>",
                    lambda e: widget.configure(
                        fg_color=active_color if self._get_opt_active(widget) else COLOR_BTN_DEFAULT
                    )
                )
            else:
                widget.bind(
                    "<Leave>",
                    lambda e: widget.configure(fg_color=COLOR_BTN_DEFAULT)
                )

        def _get_opt_active(widget):
            """Placeholder — actual state checked per-button via BooleanVar."""
            return False

        # Remember active check function for each option button
        self._get_opt_active = _get_opt_active

        # Limit toggle: 🛡️ = limited (default), ♾ = unlimited (full load)
        self.cde_limit = ctk.CTkButton(
            opt_box,
            text="🛡️",
            font=ctk.CTkFont(family=emoji_fam, size=12),
            command=self.toggle_full_load,  # toggle_full_load handles .set() internally
            **opt_btn_common
        )
        self.cde_limit.pack(side=tk.LEFT, padx=5)
        self.cde_limit.bind("<Enter>", lambda e: self.cde_limit.configure(
            fg_color=self._lighten_color(LOG_COLORS["warning"], 0.25) if self.load_full_file.get() else COLOR_BTN_ACTIVE,
            text_color=COLOR_TEXT_ON_ACCENT if self.load_full_file.get() else COLOR_TEXT_BRIGHT,
        ))
        self.cde_limit.bind("<Leave>", lambda e: self.cde_limit.configure(
            fg_color=LOG_COLORS["warning"] if self.load_full_file.get() else COLOR_BTN_DEFAULT,
            text_color=COLOR_TEXT_ON_ACCENT if self.load_full_file.get() else COLOR_TEXT_BRIGHT,
        ))
        self.btn_limit_tooltip = ToolTip(self.cde_limit, l_ui["tip_limit_off"], scale=self.scale)

        # Wrap toggle: ➡️ = wrap off (default), ↩ = wrap on
        self.cde_wrap = ctk.CTkButton(
            opt_box,
            text="➡️",
            font=ctk.CTkFont(family=emoji_fam, size=12),
            command=lambda: (
                self.wrap_mode.set(not self.wrap_mode.get()),
                self.toggle_line_break()
            ),
            **opt_btn_common
        )
        self.cde_wrap.pack(side=tk.LEFT, padx=5)
        self.cde_wrap.bind("<Enter>", lambda e: self.cde_wrap.configure(
            fg_color=self._lighten_color(COLOR_ACCENT, 0.25) if self.wrap_mode.get() else COLOR_BTN_ACTIVE,
            text_color=COLOR_TEXT_ON_ACCENT if self.wrap_mode.get() else COLOR_TEXT_BRIGHT,
        ))
        self.cde_wrap.bind("<Leave>", lambda e: self.cde_wrap.configure(
            fg_color=COLOR_ACCENT if self.wrap_mode.get() else COLOR_BTN_DEFAULT,
            text_color=COLOR_TEXT_ON_ACCENT if self.wrap_mode.get() else COLOR_TEXT_BRIGHT,
        ))
        self.btn_wrap_tooltip = ToolTip(self.cde_wrap, l_ui["tip_wrap_off"], scale=self.scale)

        # Pause toggle: ▶️ = running (pause inactive), ⏸️ = paused (pause active)
        self.cde_pause = ctk.CTkButton(
            opt_box,
            text="▶️",
            font=ctk.CTkFont(family=emoji_fam, size=12),
            command=lambda: (
                self.is_paused.set(not self.is_paused.get()),
                self.toggle_pause_scroll()
            ),
            **opt_btn_common
        )
        self.cde_pause.pack(side=tk.LEFT, padx=5)
        self.cde_pause.bind("<Enter>", lambda e: self.cde_pause.configure(
            fg_color=self._lighten_color(COLOR_DANGER, 0.25) if self.is_paused.get() else COLOR_BTN_ACTIVE,
            text_color=COLOR_TEXT_ON_ACCENT if self.is_paused.get() else COLOR_TEXT_BRIGHT,
        ))
        self.cde_pause.bind("<Leave>", lambda e: self.cde_pause.configure(
            fg_color=COLOR_DANGER if self.is_paused.get() else COLOR_BTN_DEFAULT,
            text_color=COLOR_TEXT_ON_ACCENT if self.is_paused.get() else COLOR_TEXT_BRIGHT,
        ))
        self.btn_pause_tooltip = ToolTip(self.cde_pause, l_ui["tip_pause_off"], scale=self.scale)

        # Vertical separator
        tk.Frame(opt_box, bg=COLOR_SEPARATOR, width=2).pack(
            side=tk.LEFT, fill=tk.Y, padx=self.sc(15), pady=2
        )

        # Reset button
        reset_label = l_ui.get('btn_reset', 'RESET')
        self.btn_reset = self.create_custom_button(
            opt_box,
            reset_label,
            self.reset_all_filters,
            bg_color=COLOR_BTN_DEFAULT,
            fg_color=COLOR_WARNING,
            font=(emoji_fam, 12, "bold"),
            padx=15,
            pady=3
        )
        self.btn_reset.pack(side=tk.LEFT, padx=5)
        self.btn_reset_tooltip = ToolTip(self.btn_reset, l_ui["tip_reset"], scale=self.scale)

        # --- Right side of sub-header: font size controls ---
        sh_right = ctk.CTkFrame(sub_header, fg_color=COLOR_BG_HEADER, corner_radius=0)
        sh_right.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

        # Decrease font button — same style as option toggle buttons (♾ ↩ ⏸️)
        self.btn_dec_font = ctk.CTkButton(
            sh_right,
            text="−",
            font=ctk.CTkFont(family=main_fam, size=12, weight="bold"),
            fg_color=COLOR_BTN_DEFAULT,
            hover=False,
            text_color=COLOR_TEXT_BRIGHT,
            corner_radius=5,
            border_width=0,
            height=28,
            width=32,
            command=self.decrease_font,
        )
        self.btn_dec_font.pack(side=tk.LEFT, padx=5)
        self.btn_dec_font.bind("<Enter>", lambda e: self.btn_dec_font.configure(fg_color=COLOR_BTN_ACTIVE))
        self.btn_dec_font.bind("<Leave>", lambda e: self.btn_dec_font.configure(fg_color=COLOR_BTN_DEFAULT))
        self.btn_down_font_tooltip = ToolTip(self.btn_dec_font, l_ui["tip_down_font"], scale=self.scale)

        # Increase font button — same style as option toggle buttons (♾ ↩ ⏸️)
        self.btn_inc_font = ctk.CTkButton(
            sh_right,
            text="+",
            font=ctk.CTkFont(family=main_fam, size=12, weight="bold"),
            fg_color=COLOR_BTN_DEFAULT,
            hover=False,
            text_color=COLOR_TEXT_BRIGHT,
            corner_radius=5,
            border_width=0,
            height=28,
            width=32,
            command=self.increase_font,
        )
        self.btn_inc_font.pack(side=tk.LEFT, padx=5)
        self.btn_inc_font.bind("<Enter>", lambda e: self.btn_inc_font.configure(fg_color=COLOR_BTN_ACTIVE))
        self.btn_inc_font.bind("<Leave>", lambda e: self.btn_inc_font.configure(fg_color=COLOR_BTN_DEFAULT))
        self.btn_up_font_tooltip = ToolTip(self.btn_inc_font, l_ui["tip_up_font"], scale=self.scale)

        # Font size display label
        self.font_label = ctk.CTkLabel(
            sh_right,
            text=str(self.font_size),
            fg_color=COLOR_BG_HEADER,
            text_color=COLOR_TEXT_BRIGHT,
            width=30,
            font=ctk.CTkFont(family=main_fam, size=12, weight="bold"),
        )
        self.font_label.pack(side=tk.LEFT)

        # ──────────────────────────────────────────────────────────────
        # MAIN LOG DISPLAY AREA (row 2)
        # ──────────────────────────────────────────────────────────────
        self.main_container = ctk.CTkFrame(
            self.root, fg_color=COLOR_BG_MAIN, corner_radius=0
        )
        self.main_container.grid(
            row=2, column=0, sticky="nsew",
            padx=10, pady=(0, 5)
        )
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        # tk.Text widget — kept as standard tkinter for full tag/config API compatibility
        self.txt_area = tk.Text(
            self.main_container,
            wrap=tk.NONE,
            width=120,
            height=25,
            bg=COLOR_BG_MAIN,
            fg=COLOR_TEXT_MAIN,
            font=(mono_fam, self.font_size),
            borderwidth=0,
            highlightthickness=0,
            padx=5,
            pady=5,
            undo=False,
            selectforeground=COLOR_LOG_SELECTION_FG,
            insertwidth=max(1, self.sc(4)),
            insertontime=600,
            insertofftime=300,
            insertbackground=COLOR_TEXT_BRIGHT,
            selectbackground=COLOR_LOG_SELECTION,
            inactiveselectbackground=COLOR_LOG_SELECTION,
            exportselection=False,
        )
        self.txt_area.grid(row=0, column=0, sticky="nsew")

        # Vertical scrollbar (CTK styled)
        self.v_scroll = ctk.CTkScrollbar(
            self.main_container,
            orientation="vertical",
            command=self.txt_area.yview,
            width=12,
            fg_color="transparent",
            button_color=SCROLL_THUMB_DEFAULT,
            button_hover_color=SCROLL_THUMB_HOVER,
            corner_radius=10,
            border_spacing=2
        )
        self.txt_area.configure(yscrollcommand=self.v_scroll.set)
        self.v_scroll.grid(row=0, column=1, sticky="ns", padx=(2, 0))

        # Horizontal scrollbar (CTK styled)
        self.h_scrollbar = ctk.CTkScrollbar(
            self.main_container,
            orientation="horizontal",
            command=self.txt_area.xview,
            height=12,
            fg_color="transparent",
            button_color=SCROLL_THUMB_DEFAULT,
            button_hover_color=SCROLL_THUMB_HOVER,
            corner_radius=10,
            border_spacing=2
        )
        self.txt_area.configure(xscrollcommand=self.h_scrollbar.set)
        self.h_scrollbar.grid(row=1, column=0, sticky="ew", pady=(2, 0))

        # --- Custom Context Menu (right-click on log area) ---
        # Uses tk.Toplevel with overrideredirect for a frameless popup;
        # items are ctk.CTkButton for built-in hover + tuple padx support.
        self.context_menu = tk.Toplevel(self.root)
        self.context_menu.withdraw()
        self.context_menu.overrideredirect(True)
        self.context_menu.configure(bg=COLOR_SEPARATOR, padx=1, pady=1)

        self.menu_inner = tk.Frame(self.context_menu, bg=COLOR_BTN_DEFAULT)
        self.menu_inner.pack(fill="both", expand=True)

        # Search entry context menu
        self.search_context_menu = tk.Toplevel(self.root)
        self.search_context_menu.withdraw()
        self.search_context_menu.overrideredirect(True)
        self.search_context_menu.configure(bg=COLOR_SEPARATOR, padx=1, pady=1)

        self.search_menu_inner = tk.Frame(self.search_context_menu, bg=COLOR_BTN_DEFAULT)
        self.search_menu_inner.pack(fill="both", expand=True)

        self._build_search_menu_items()

        def add_custom_item(command):
            """Add a clickable tk.Label as a context menu item.
            tk.Label is used instead of CTkButton because overrideredirect
            windows don't propagate mouse events reliably to CTk's internal
            canvas widgets, breaking hover detection."""
            item = tk.Label(
                self.menu_inner,
                text="",
                bg=COLOR_BTN_DEFAULT,
                fg=COLOR_TEXT_BRIGHT,
                font=(main_fam, 11),
                padx=10,
                pady=self.sc(7),
                anchor="w",
                cursor="hand2",
            )
            item.pack(fill="x")
            item.bind("<Enter>", lambda e, i=item: i.config(bg=COLOR_ACCENT, fg=COLOR_TEXT_ON_ACCENT))
            item.bind("<Leave>", lambda e, i=item: i.config(bg=COLOR_BTN_DEFAULT, fg=COLOR_TEXT_BRIGHT))
            item.bind("<Button-1>", lambda e: [command(), self.context_menu.withdraw()])
            return item

        # Context menu items (order matters)
        self.menu_items = []
        self.menu_items.append(add_custom_item(self.copy_selection))           # 0: Copy
        self.menu_items.append(                                                  # 1: Select All
            add_custom_item(lambda: self.txt_area.tag_add("sel", "1.0", "end"))
        )
        self.menu_items.append(add_custom_item(self.search_selection_locally))  # 2: Local search

        # 3: Google Search (dynamic visibility based on config)
        self.google_menu_item = add_custom_item(self.search_on_google)
        self.menu_items.append(self.google_menu_item)
        if not self.show_google_search.get():
            self.google_menu_item.pack_forget()

        # 4: Exclude selection
        self.menu_items.append(add_custom_item(self.exclude_selection))         # 4: Exclude

        # --- Text area event bindings ---
        self.txt_area.bind("<Button-1>", lambda event: self.txt_area.focus_set())
        self.txt_area.bind("<Button-1>", self.reset_cursor_timer, add="+")
        # A single click means the user is navigating manually: discard the
        # double-click content anchor so Ctrl+L uses the live cursor instead.
        self.txt_area.bind("<Button-1>", lambda e: setattr(self, "_last_wrap_content", None), add="+")
        self.txt_area.bind("<Key>", self.reset_cursor_timer, add="+")
        self.txt_area.bind("<Motion>", self.reset_cursor_timer, add="+")
        self.reset_cursor_timer()

        # "Soft" read-only: allow navigation but block typing
        allowed_keys = ("Up", "Down", "Left", "Right", "Next", "Prior", "Home", "End")
        self.txt_area.bind(
            "<Key>",
            lambda event: "break" if event.keysym not in allowed_keys else None,
        )

        self.txt_area.bind("<Button-3>", self.show_context_menu)
        self.txt_area.bind("<Double-Button-1>", self.on_double_click_line)

        # --- Loading overlay (covers the text area during file load) ---
        self.overlay = ctk.CTkFrame(self.main_container, fg_color=COLOR_BG_MAIN, corner_radius=0)
        self.loading_label = ctk.CTkLabel(
            self.overlay,
            text="",
            fg_color=COLOR_BG_MAIN,
            text_color=COLOR_TEXT_MAIN,
            font=ctk.CTkFont(family=main_fam, size=15, weight="bold"),
        )
        self.loading_label.pack(expand=True)

        # ──────────────────────────────────────────────────────────────
        # FOOTER ROW (row 3) — status bar
        # ──────────────────────────────────────────────────────────────
        footer = ctk.CTkFrame(
            self.root, fg_color=COLOR_BG_FOOTER, corner_radius=0
        )
        footer.grid(row=3, column=0, sticky="ew")

        # Inner frame with padding
        footer_inner = ctk.CTkFrame(footer, fg_color=COLOR_BG_FOOTER, corner_radius=0)
        footer_inner.pack(fill=tk.X, padx=10, pady=5)

        # 1. Activity indicator light (canvas circle)
        self.status_indicator = tk.Canvas(
            footer_inner,
            width=self.sc(32),
            height=self.sc(32),
            bg=COLOR_BG_FOOTER,
            highlightthickness=0,
        )
        self.status_indicator.pack(side=tk.LEFT, padx=(self.sc(28), 0))

        self.status_circle = self.status_indicator.create_oval(
            2, 2, self.sc(28), self.sc(28),
            fill=COLOR_INDICATOR_OFF,
            outline=COLOR_INDICATOR_BORDER,
            width=1,
        )

        # Timer container (inactivity messages)
        self.timer_container = ctk.CTkFrame(footer_inner, fg_color=COLOR_BG_FOOTER, corner_radius=0)
        self.timer_container.pack(side=tk.LEFT, fill=tk.Y)

        self.timer_sep = tk.Frame(self.timer_container, bg=COLOR_SEPARATOR, width=2)

        # 2. Inactivity / status message label
        self.lbl_timer = ctk.CTkLabel(
            self.timer_container,
            textvariable=self.inactivity_timer_var,
            fg_color=COLOR_BG_FOOTER,
            text_color=COLOR_DANGER,
            font=ctk.CTkFont(family=main_fam, size=12, weight="bold"),
        )
        self.lbl_timer.pack(side=tk.LEFT, padx=(10, 5))

        # Show/hide the separator when inactivity message appears
        self.inactivity_timer_var.trace_add("write", self._toggle_timer_separator)

        # Vertical separator
        tk.Frame(footer_inner, bg=COLOR_SEPARATOR, width=2).pack(
            side=tk.LEFT, fill=tk.Y, padx=10, pady=2
        )

        # Tkinter StringVars for footer stat labels
        self.footer_var = tk.StringVar()
        self.stats_var  = tk.StringVar()
        self.size_var   = tk.StringVar()
        self.limit_var  = tk.StringVar()
        self.wrap_var   = tk.StringVar()
        self.paused_var = tk.StringVar()

        # Common font for all footer stat labels (CTkFont handles DPI scaling;
        # passing it to tk.Label widgets ensures identical rendered size)
        footer_font = ctk.CTkFont(family=emoji_fam, size=12, weight="bold")

        # 3. File path label
        self.lbl_path = ctk.CTkLabel(
            footer_inner,
            text="",
            fg_color=COLOR_BG_FOOTER,
            text_color=COLOR_TEXT_MAIN,
            font=footer_font,
            anchor=tk.W,
        )
        self.lbl_path.pack(side=tk.LEFT, padx=(5, 10))
        self.path_tooltip = ToolTip(self.lbl_path, "")

        # Separators and stat labels — shown/hidden dynamically by update_stats().
        # Using ctk.CTkLabel (no textvariable) so font scaling matches the rest
        # of the footer. Text is set explicitly via .configure(text=...) in
        # update_stats(), avoiding the CTK textvariable + pack_forget reliability issue.
        _fs = dict(fg_color=COLOR_BG_FOOTER, font=footer_font, anchor="w")

        self.sep_lines   = tk.Frame(footer_inner, bg=COLOR_SEPARATOR, width=2)
        self.label_lines = ctk.CTkLabel(
            footer_inner, text="",
            text_color=COLOR_TEXT_MAIN, **_fs
        )

        self.sep_size    = tk.Frame(footer_inner, bg=COLOR_SEPARATOR, width=2)
        self.label_size  = ctk.CTkLabel(
            footer_inner, text="",
            text_color=COLOR_TEXT_MAIN, **_fs
        )

        self.sep_duration = tk.Frame(footer_inner, bg=COLOR_SEPARATOR, width=2)
        self.label_duration = ctk.CTkLabel(
            footer_inner, text="",
            text_color=COLOR_TEXT_MAIN, **_fs
        )
        self.label_duration_tooltip = ToolTip(
            self.label_duration, l_ui.get("tip_duration", ""), scale=self.scale
        )

        self.sep_limit   = tk.Frame(footer_inner, bg=COLOR_SEPARATOR, width=2)
        self.label_limit = ctk.CTkLabel(
            footer_inner, text="",
            text_color=COLOR_WARNING, **_fs
        )

        self.sep_wrap    = tk.Frame(footer_inner, bg=COLOR_SEPARATOR, width=2)
        self.label_wrap  = ctk.CTkLabel(
            footer_inner, text="",
            text_color=COLOR_TEXT_WRAP, **_fs
        )

        self.sep_pause   = tk.Frame(footer_inner, bg=COLOR_SEPARATOR, width=2)
        self.label_pause = ctk.CTkLabel(
            footer_inner, text="",
            text_color=COLOR_DANGER, **_fs
        )

        # --- GitHub / version link in the footer (right-aligned) ---
        current_lang_str = self.current_lang.get()
        l_ui = LANGS.get(current_lang_str, LANGS["EN"])

        self.github_label = ctk.CTkLabel(
            footer_inner,
            text=f"{APP_NAME} {APP_VERSION}",
            fg_color=COLOR_BG_FOOTER,
            text_color=COLOR_TEXT_GREY,
            font=ctk.CTkFont(family=main_fam, size=12, weight="bold"),
            cursor="hand2",
        )
        self.github_label.pack(side=tk.RIGHT, padx=5)
        self.github_label.bind("<Button-1>", self.open_github_link, add="+")
        self.github_label.bind(
            "<Enter>", lambda e: self.github_label.configure(text_color=COLOR_TEXT_MAIN), add="+"
        )
        self.github_label.bind(
            "<Leave>", lambda e: self.github_label.configure(text_color=COLOR_TEXT_GREY), add="+"
        )
        self.github_tooltip = ToolTip(
            self.github_label, l_ui.get("tip_github", "View the source code on GitHub"),
            scale=self.scale
        )

        # --- History dropdown listbox (placed on root, shown on demand) ---
        self.history_listbox = tk.Listbox(
            self.root,
            bg=COLOR_BG_MAIN,
            fg=COLOR_TEXT_MAIN,
            selectbackground=COLOR_ACCENT,
            selectforeground=COLOR_TEXT_ON_ACCENT,  # Always white on blue selection (readable in both themes)
            font=(main_fam, 10),
            borderwidth=1,
            highlightthickness=0,
            activestyle="none",
            exportselection=False,
        )
        self.history_listbox.place_forget()
        self.history_listbox.bind("<ButtonRelease-1>", self.on_history_select)
        self.history_listbox.bind("<Return>", self.on_history_select)

    def _toggle_timer_separator(self, *args):
        """
        Dynamically shows/hides the separator to the left of the inactivity timer label.
        """
        message = self.inactivity_timer_var.get().strip()
        if message:
            self.timer_sep.pack(
                side=tk.LEFT,
                fill=tk.Y,
                padx=(10, 0),
                pady=2,
                before=self.lbl_timer,
            )
        else:
            self.timer_sep.pack_forget()

    def update_footer_path(self, full_path):
        """
        Updates the footer label with a shortened path and sets
        the full path in the tooltip for hover display.
        """
        if not full_path:
            self.lbl_path.configure(text="")
            self.path_tooltip.text = ""
            return

        self.path_tooltip.text = full_path

        max_chars = 55
        if len(full_path) > max_chars:
            short_path = full_path[:20] + "..." + full_path[-32:]
        else:
            short_path = full_path

        self.lbl_path.configure(text=f"📄 {short_path}")

    @staticmethod
    def _lighten_color(hex_color, factor=0.25):
        """Blend a hex color toward white by factor (0–1). Used for active-hover tints."""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        r = min(255, int(r + (255 - r) * factor))
        g = min(255, int(g + (255 - g) * factor))
        b = min(255, int(b + (255 - b) * factor))
        return f'#{r:02x}{g:02x}{b:02x}'

    def sc(self, val):
        """Scale a pixel/size value by the application's DPI scaling factor."""
        return int(val * self.scale)


# ──────────────────────────────────────────────────────────────────────────────
# TOOLTIP CLASS
# ──────────────────────────────────────────────────────────────────────────────

class ToolTip:
    """
    Lightweight tooltip widget that appears after a hover delay.
    Uses a bare tk.Toplevel with overrideredirect for a clean popup.
    """

    def __init__(self, widget, text, scale=1.0, condition=None):
        self.widget = widget
        self.text = text
        self.scale = scale
        self.condition = condition  # Optional callable: tooltip only shows if condition() is True
        self.fg_override = None     # Optional foreground color override; falls back to COLOR_TEXT_TIPS
        self.tip_window = None
        self.id = None
        self.delay = 1000  # milliseconds before tooltip appears

        self.widget.bind('<Enter>', self.schedule_tip, add="+")
        self.widget.bind('<Leave>', self.hide_tip, add="+")
        self.widget.bind('<ButtonPress>', self.hide_tip, add="+")

    def schedule_tip(self, event=None):
        """Cancel any pending tip and schedule a new one."""
        self.cancel_tip()
        self.id = self.widget.after(self.delay, self.show_tip)

    def cancel_tip(self):
        """Cancel a pending scheduled tooltip."""
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

    def show_tip(self, event=None):
        """Create and position the tooltip window."""
        if not self.text:
            return
        if self.condition is not None and not self.condition():
            return

        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.attributes("-topmost", True)

        # On Linux, hide initially to calculate size before positioning
        if sys.platform.startswith("linux"):
            tw.attributes("-alpha", 0.0)

        label = tk.Label(
            tw,
            text=self.text,
            justify="left",
            background=COLOR_BG_TIPS,
            foreground=self.fg_override if self.fg_override else COLOR_TEXT_TIPS,
            relief="solid",
            borderwidth=0,
            font=("Segoe UI", "9", "normal"),
            padx=self.sc(30),
            pady=self.sc(20)
        )
        label.pack()

        tw.update_idletasks()

        tip_width  = tw.winfo_reqwidth()
        tip_height = tw.winfo_reqheight()

        root = self.widget.winfo_toplevel()

        widget_x = self.widget.winfo_rootx()
        widget_y = self.widget.winfo_rooty()
        widget_h = self.widget.winfo_height()

        root_x = root.winfo_rootx()
        root_y = root.winfo_rooty()
        root_w = root.winfo_width()
        root_h = root.winfo_height()

        # Default: below and slightly right of the widget
        x = widget_x + 20
        y = widget_y + widget_h + self.sc(5)

        # Keep inside the right edge
        if x + tip_width > root_x + root_w:
            x = root_x + root_w - tip_width - 10

        # If it would go below the window, display above the widget instead
        if y + tip_height > root_y + root_h:
            y = widget_y - tip_height - self.sc(5)

        # Safety: never clip through left or top edges
        x = max(root_x, x)
        y = max(root_y, y)

        tw.wm_geometry(f"+{int(x)}+{int(y)}")

        if sys.platform.startswith("linux"):
            tw.attributes("-alpha", 1.0)
        else:
            tw.deiconify()

    def hide_tip(self, event=None):
        """Destroy the tooltip window."""
        self.cancel_tip()
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()

    def sc(self, val):
        """Scale a value based on the tooltip's scaling factor."""
        return int(val * self.scale)