import tkinter as tk
from tkinter import ttk
import sys
import os

from config import *
from languages import LANGS


class UIBuilderMixin:
    """Builds all widgets for the graphical user interface."""
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
                    import ctypes
                    windll = ctypes.windll.kernel32
                    lang_id = windll.GetUserDefaultUILanguage()
                    lang_code = locale.windows_locale.get(lang_id)
                except Exception:
                    pass

            # 3. Specific handling for Linux/macOS via Environment Variables
            if not lang_code or lang_code == 'None':
                # Check standard env vars in order of priority
                for env_var in ('LC_ALL', 'LC_MESSAGES', 'LANG'):
                    val = os.environ.get(env_var)
                    if val:
                        lang_code = val
                        break

            # 4. Final check: does the string contain 'fr' (e.g., 'fr_FR', 'French_France')
            if lang_code and lang_code.lower().startswith('fr'):
                return "FR"

        except Exception:
            # Fallback in case of any unexpected error during detection
            pass

        return "EN"

    def set_window_icon(self):
        """
        Sets the application window icon for the taskbar and title bar.

        This method attempts to load an icon file (logo.ico) from the local
        directory. It handles the process gracefully by checking if the
        file exists before attempting to apply it, preventing the
        application from crashing on missing assets.

        Technical Note:
        - On Windows, it uses 'iconbitmap' for high-quality .ico support.
        - On other platforms, it uses 'iconphoto' as a fallback.
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
        padx=30,
        pady=3
    ):
        """
        Creates a stylized Tkinter Label acting as a custom button with hover effects.

        Args:
            parent (tk.Widget): The parent container.
            text (str): Button text or emoji.
            command (callable): Function to execute on click.
            ... (Style args)

        Returns:
            tk.Label: The created button-like widget.
        """

        if font is None:
            font = (self.emoji_font_family, 9, "bold")

        label = tk.Label(
            parent,
            text=text,
            bg=bg_color,
            fg=fg_color,
            padx=self.sc(padx),
            pady=pady,
            font=font,
            cursor="hand2",
        )

        label.bind("<Button-1>", lambda event: command())
        label.bind("<Enter>", lambda event: label.config(bg=COLOR_BTN_ACTIVE))
        label.bind("<Leave>", lambda event: label.config(bg=bg_color))

        return label

    def setup_ui(self):
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(2, weight=1)

        style = ttk.Style()
        style.theme_use('clam')

        current_lang_str = self.current_lang.get()
        l_ui = LANGS.get(current_lang_str, LANGS["EN"])

        # --- DARK STYLE FOR COMBOBOX ---
        style.configure(
            "TCombobox",
            fieldbackground=COLOR_BTN_DEFAULT,
            background=COLOR_BTN_DEFAULT,
            foreground=COLOR_TEXT_BRIGHT,
            bordercolor=COLOR_BTN_DEFAULT,
            darkcolor=COLOR_BTN_DEFAULT,
            lightcolor=COLOR_BTN_DEFAULT,
            arrowcolor=COLOR_TEXT_BRIGHT,
            arrowsize=20,
            insertcolor=COLOR_TEXT_BRIGHT,
            selectbackground=COLOR_BTN_DEFAULT,
            selectforeground=COLOR_TEXT_BRIGHT,
            font=(self.main_font_family, 10),
            postoffset=(0, 0, 0, 0)
        )

        style.map(
            "TCombobox",
            fieldbackground=[
                ("readonly", COLOR_BTN_DEFAULT),
                ("focus", COLOR_BTN_DEFAULT),
                ("active", COLOR_BTN_DEFAULT)
            ],
            background=[
                ("readonly", COLOR_BTN_DEFAULT),
                ("focus", COLOR_BTN_DEFAULT),
                ("active", COLOR_BTN_DEFAULT)
            ],
            foreground=[("readonly", COLOR_TEXT_BRIGHT)],
            selectbackground=[
                ("readonly", COLOR_BTN_DEFAULT),
                ("focus", COLOR_BTN_DEFAULT)
            ],
            selectforeground=[
                ("readonly", COLOR_TEXT_BRIGHT),
                ("focus", COLOR_TEXT_BRIGHT)
            ]
        )

        # --- DARK STYLE FOR SCROLLBAR ---
        style.configure(
            "Vertical.TScrollbar",
            gripcount=0,
            background=SCROLL_THUMB_DEFAULT,
            troughcolor=COLOR_BG_HEADER,
            bordercolor=COLOR_BG_HEADER,
            lightcolor=COLOR_BG_HEADER,
            darkcolor=COLOR_BG_HEADER,
            arrowcolor=COLOR_TEXT_DIM,
            width=24,
            arrowsize=24
        )

        style.map("Vertical.TScrollbar",
                  background=[("active", SCROLL_THUMB_HOVER), ("pressed", SCROLL_THUMB_HOVER)])

        self.root.option_add("*TCombobox*exportSelection", False)
        self.root.option_add("*TCombobox*Listbox.background", COLOR_BTN_DEFAULT)
        self.root.option_add("*TCombobox*Listbox.foreground", COLOR_TEXT_BRIGHT)
        self.root.option_add("*TCombobox*Listbox.selectBackground", COLOR_ACCENT)
        self.root.option_add("*TCombobox*Listbox.font", (self.main_font_family, 10))
        self.root.option_add("*TCombobox*Listbox.itemHeight", 60)
        self.root.option_add("*TCombobox*Listbox.padding", 4)
        self.root.option_add("*TCombobox*Listbox.lineSpacing", 10)
        self.root.option_add("*TCombobox*Listbox.listvariable", "")
        self.root.option_add("*TCombobox*Listbox.selectborderwidth", 0)
        self.root.option_add("*TCombobox*Listbox.activestyle", "none")

        if sys.platform.startswith("linux"):
            self.root.option_add("*TCombobox*Listbox.selectForeground", COLOR_TEXT_BRIGHT)

        # --- HEADER ---
        header = tk.Frame(self.root, bg=COLOR_BG_HEADER, padx=self.sc(10), pady=self.sc(10))
        header.grid(row=0, column=0, sticky="ew")

        h_left = tk.Frame(header, bg=COLOR_BG_HEADER)
        h_left.pack(side=tk.LEFT, fill=tk.Y)

        # --- buttons open ---
        self.btn_log = self.create_custom_button(h_left, l_ui["log"], self.open_file)
        self.btn_log.pack(side=tk.LEFT, padx=5)
        self.btn_open_tooltip = ToolTip(self.btn_log, l_ui["tip_wrap"], scale=self.scale)

        # --- buttons export ---
        self.btn_exp = self.create_custom_button(h_left, l_ui["exp"], self.export_log)
        self.btn_exp.pack(side=tk.LEFT, padx=5)
        self.btn_export_tooltip = ToolTip(self.btn_exp, l_ui["tip_export"], scale=self.scale)

        # --- buttons upload ---
        self.btn_upl = self.create_custom_button(h_left, l_ui["upl"], self.upload_to_pastebin)
        self.btn_upl.pack(side=tk.LEFT, padx=5)
        self.btn_upload_tooltip = ToolTip(self.btn_upl, l_ui["tip_upload"], scale=self.scale)

        # --- Addition of the separator ---
        tk.Frame(
            h_left,
            bg=COLOR_SEPARATOR,
            width=2
        ).pack(side=tk.LEFT, fill=tk.Y, padx=self.sc(20), pady=5)

        # --- buttons summary ---
        self.btn_sum = self.create_custom_button(h_left, l_ui["sum"], self.show_summary)
        self.btn_sum.pack(side=tk.LEFT, padx=5)
        self.btn_summary_tooltip = ToolTip(self.btn_sum, l_ui["tip_summary"], scale=self.scale)

        # --- buttons clear ---
        self.btn_clr = self.create_custom_button(h_left, l_ui["clr"], self.clear_console)
        self.btn_clr.pack(side=tk.LEFT, padx=5)
        self.btn_clear_tooltip = ToolTip(self.btn_clr, l_ui["tip_clear"], scale=self.scale)

        # --- Addition of the separator ---
        tk.Frame(
            h_left,
            bg=COLOR_SEPARATOR,
            width=2
        ).pack(side=tk.LEFT, fill=tk.Y, padx=self.sc(20), pady=5)

        self.filter_frame = tk.Frame(h_left, bg=COLOR_BG_HEADER)
        self.filter_frame.pack(side=tk.LEFT, padx=5)

        # Dictionary to store filter toggle widgets
        self.filter_widgets = {}

        # --- FILTER TOGGLE BUTTONS ---
        filter_modes = ["all", "info", "warning", "error", "debug"]
        self.filter_tooltips = {}

        tm = {
            "all": "all",
            "info": "info",
            "warning": "warn",
            "error": "err",
            "debug": "debug",
        }

        for mode in filter_modes:
            translated_text = l_ui.get(tm[mode], mode.upper())

            cb = tk.Checkbutton(
                self.filter_frame,
                variable=self.filter_vars[mode],
                indicatoron=0,
                text=translated_text,
                fg=COLOR_TEXT_BRIGHT,
                font=(self.emoji_font_family, 9, "bold"),
                relief="flat",
                borderwidth=0,
                padx=self.sc(30),
                pady=3,
                cursor="hand2",
                command=lambda m=mode: self.on_filter_toggle(m),
                bg=COLOR_BTN_DEFAULT,
                selectcolor=COLOR_BTN_DEFAULT,
                activebackground=COLOR_BTN_ACTIVE,
                activeforeground=COLOR_TEXT_BRIGHT,
                highlightthickness=0,
                bd=0
            )
            cb.pack(side=tk.LEFT, padx=5)

            cb.bind(
                "<Enter>",
                lambda event, w=cb, m=mode: self.on_hover_filter(w, m, True)
            )
            cb.bind(
                "<Leave>",
                lambda event, w=cb, m=mode: self.on_hover_filter(w, m, False)
            )

            # Store widget reference for later updates
            self.filter_widgets[mode] = cb

            tip_key = f"tip_filter_{mode}"
            self.filter_tooltips[mode] = ToolTip(cb, l_ui[tip_key], scale=self.scale)

        h_right = tk.Frame(header, bg=COLOR_BG_HEADER)
        h_right.pack(side=tk.RIGHT, fill=tk.Y)

        # --- THEME SELECTION  ---
        self.combo_theme = ttk.Combobox(
            h_right,
            textvariable=self.theme_mode,
            values=[],
            state="readonly",
            width=12,
            style="TCombobox"
        )
        self.combo_theme.pack(side=tk.LEFT, padx=5)

        if sys.platform != "win32":
            self.combo_theme.pack_forget()

        self.combo_theme.bind("<<ComboboxSelected>>", lambda e: [self.on_theme_change(e), self.txt_area.focus_set()])

        # --- LANGUAGE SELECTION ---
        self.combo_lang = ttk.Combobox(
            h_right,
            textvariable=self.current_lang,
            values=sorted(LANGS.keys()),
            state="readonly",
            width=5,
            style="TCombobox"
        )
        self.combo_lang.bind("<<ComboboxSelected>>", self.refocus_log)
        self.combo_lang.pack(side=tk.LEFT, padx=5)

        self.combo_lang.bind(
            "<<ComboboxSelected>>",
            lambda event: self.change_language()
        )

        self.combo_lang_tooltip = ToolTip(self.combo_lang, l_ui["tip_lang"], scale=self.scale)

        # --- Addition of the separator ---
        tk.Frame(
            h_right,
            bg=COLOR_SEPARATOR,
            width=2
        ).pack(side=tk.LEFT, fill=tk.Y, padx=self.sc(15), pady=5)

        # --- Single Instance Toggle Button ---
        initial_icon = "🔒" if self.enable_single_instance_var else "🔓"

        self.btn_single_instance = self.create_custom_button(
            h_right,
            initial_icon,
            self.toggle_single_instance,
            font=(self.emoji_font_family, 9, "bold"),
            bg_color=COLOR_BTN_SECONDARY,
            padx=12,
            pady=3
        )
        self.btn_single_instance.pack(side=tk.LEFT, padx=5)
        self.btn_single_instance_tooltip = ToolTip(self.btn_single_instance, l_ui["tip_single_instance"], scale=self.scale)

        # --- Addition of the separator ---
        tk.Frame(
            h_right,
            bg=COLOR_SEPARATOR,
            width=2
        ).pack(side=tk.LEFT, fill=tk.Y, padx=self.sc(15), pady=5)

        # --- Button Help ---
        self.btn_help = self.create_custom_button(
            h_right,
            "?",
            self.show_help,
            font=(self.main_font_family, 9, "bold"),
            bg_color=COLOR_BTN_SECONDARY,
            padx=12,
            pady=3
        )
        self.btn_help.pack(side=tk.LEFT, padx=5)
        self.btn_help_tooltip = ToolTip(self.btn_help, l_ui["tip_help"], scale=self.scale)

        # --- HEADER ---
        # --- SUB-HEADER (SECONDARY TOOLBAR) ---
        sub_header = tk.Frame(self.root, bg=COLOR_BG_HEADER, padx=self.sc(10), pady=self.sc(10))
        sub_header.grid(row=1, column=0, sticky="ew", pady=(0, 5))

        # Left side of the sub-header
        sh_left = tk.Frame(sub_header, bg=COLOR_BG_HEADER)
        sh_left.pack(side=tk.LEFT, fill=tk.Y)

        # Keyword management box
        kw_box = tk.Frame(sh_left, bg=COLOR_BG_HEADER)
        kw_box.pack(side=tk.LEFT)

        # --- LIST KEYWORD SELECTION ---
        self.combo_lists = ttk.Combobox(
            kw_box,
            textvariable=self.selected_list,
            state="readonly",
            width=20,
            style="TCombobox"
        )
        self.combo_lists.pack(side=tk.LEFT, padx=5)
        self.combo_lists.bind("<<ComboboxSelected>>", lambda e: [self.on_list_selected(e), self.txt_area.focus_set()])

        self.combo_kw_tooltip = ToolTip(self.combo_lists, l_ui["tip_kw_list"], scale=self.scale)

        # --- Bouton REFRESH ---
        btn_refresh = self.create_custom_button(
            kw_box,
            "🔄",
            self.refresh_keyword_list,
            bg_color=COLOR_BTN_SECONDARY,
            padx=10,
            pady=3
        )
        btn_refresh.pack(side=tk.LEFT, padx=5)
        self.btn_kw_refresh_tooltip = ToolTip(btn_refresh, l_ui["tip_kw_refresh"], scale=self.scale)

        # --- Bouton FOLDER ---
        btn_folder = self.create_custom_button(
            kw_box,
            "📁",
            self.open_keyword_folder,
            bg_color=COLOR_BTN_SECONDARY,
            padx=10,
            pady=3
        )
        btn_folder.pack(side=tk.LEFT, padx=5)
        self.btn_kw_folder_tooltip = ToolTip(btn_folder, l_ui["tip_kw_folder"], scale=self.scale)

        # --- Addition of the separator ---
        tk.Frame(
            sh_left,
            bg=COLOR_SEPARATOR,
            width=2
        ).pack(side=tk.LEFT, fill=tk.Y, padx=self.sc(20), pady=5)

        # --- Search Box Section ---
        search_box = tk.Frame(sh_left, bg=COLOR_BG_MAIN, padx=8)
        search_box.pack(side=tk.LEFT, padx=5)

        # Search icon
        tk.Label(
            search_box,
            text="🔍",
            bg=COLOR_BG_MAIN,
            fg=COLOR_TEXT_DIM,
            font=(self.emoji_font_family, 9)
        ).pack(side=tk.LEFT)

        # Search entry field
        self.search_entry = tk.Entry(
            search_box,
            textvariable=self.search_query,
            bg=COLOR_BG_MAIN,
            fg=COLOR_TEXT_BRIGHT,
            borderwidth=0,
            width=22,
            insertbackground=COLOR_TEXT_BRIGHT,
            font=(self.main_font_family, 9),
            relief="flat",
            highlightthickness=1,
            highlightbackground=COLOR_BG_MAIN,
            highlightcolor=COLOR_BG_MAIN
        )
        self.search_entry.pack(side=tk.LEFT, padx=5, pady=4)

        self.search_entry.bind("<Button-3>", self.show_search_context_menu)

        # Clear search button (X)
        self.btn_clear_search = tk.Label(
            search_box,
            text="×",
            bg=COLOR_BG_MAIN,
            fg=COLOR_TEXT_DIM,
            font=(self.main_font_family, 11, "bold"),
            cursor="hand2"
        )
        self.btn_clear_search.pack(side=tk.LEFT)
        self.btn_clear_search.bind(
            "<Button-1>",
            lambda event: self.clear_search()
        )

        self.search_tooltip = ToolTip(self.search_entry, l_ui["tip_search"], scale=self.scale)

        # --- Addition of the separator ---
        tk.Frame(
            sh_left,
            bg=COLOR_SEPARATOR,
            width=2
        ).pack(side=tk.LEFT, fill=tk.Y, padx=self.sc(20), pady=5)

        # --- Options Box & Style ---
        opt_box = tk.Frame(sh_left, bg=COLOR_BG_HEADER)
        opt_box.pack(side=tk.LEFT)

        # Common style for option buttons (Checkbuttons used as toggles)
        opt_btn_style = {
            "indicatoron": 0,
            "bg": COLOR_BTN_DEFAULT,
            "fg": COLOR_TEXT_BRIGHT,
            "relief": "flat",
            "font": (self.emoji_font_family, 9),
            "padx": 10,
            "pady": 3,
            "borderwidth": 0,
            "cursor": "hand2",
            "highlightbackground": COLOR_BG_HEADER,
            "activebackground": COLOR_BTN_ACTIVE,
            "activeforeground": COLOR_TEXT_MAIN,
            "highlightthickness": 0,
            "bd": 0
        }

        def add_hover(widget):
            """Add visual hover effects to a widget."""
            widget.bind(
                "<Enter>",
                lambda event: widget.config(bg=COLOR_BTN_ACTIVE)
            )
            widget.bind(
                "<Leave>",
                lambda event: widget.config(bg=COLOR_BTN_DEFAULT)
            )

        # --- Infinity (Full Load) Toggle ---
        self.cde_limit = tk.Checkbutton(
            opt_box,
            text="♾",
            variable=self.load_full_file,
            selectcolor=COLOR_WARNING,
            command=self.toggle_full_load,
            **opt_btn_style
        )
        self.cde_limit.pack(side=tk.LEFT, padx=self.sc(10))
        add_hover(self.cde_limit)
        self.btn_limit_tooltip = ToolTip(self.cde_limit, l_ui["tip_limit"], scale=self.scale)

        # --- Word Wrap Toggle ---
        self.cde_wrap = tk.Checkbutton(
            opt_box,
            text="↩",
            variable=self.wrap_mode,
            selectcolor=COLOR_ACCENT,
            command=self.apply_wrap_mode,
            **opt_btn_style
        )
        self.cde_wrap.pack(side=tk.LEFT, padx=self.sc(10))
        add_hover(self.cde_wrap)
        self.btn_wrap_tooltip = ToolTip(self.cde_wrap, l_ui["tip_wrap"], scale=self.scale)

        # --- Pause Monitoring Toggle ---
        self.cde_pause = tk.Checkbutton(
            opt_box,
            text="⏸️",
            variable=self.is_paused,
            selectcolor=COLOR_DANGER,
            command=self.toggle_pause_scroll,
            **opt_btn_style
        )
        self.cde_pause.pack(side=tk.LEFT, padx=self.sc(10))
        add_hover(self.cde_pause)
        self.btn_pause_tooltip = ToolTip(self.cde_pause, l_ui["tip_pause"], scale=self.scale)

        # --- Addition of the separator ---
        tk.Frame(
            opt_box,
            bg=COLOR_SEPARATOR,
            width=2
        ).pack(side=tk.LEFT, fill=tk.Y, padx=self.sc(20), pady=5)

        # Preparation of the translated text
        reset_label = l_ui.get('btn_reset', 'RESET')
        reset_text = f"{reset_label}"

        # --- Reset Button ---
        self.btn_reset = self.create_custom_button(
            opt_box,
            reset_text,
            self.reset_all_filters,
            fg_color=COLOR_WARNING,
            font=(self.emoji_font_family, 9, "bold"),
            padx=self.sc(30),
            pady=3
        )
        self.btn_reset.pack(side=tk.LEFT, padx=5)
        self.btn_reset_tooltip = ToolTip(self.btn_reset, l_ui["tip_reset"], scale=self.scale)

        # --- Font size controls (sub-header right) ---
        sh_right = tk.Frame(sub_header, bg=COLOR_BG_HEADER)
        sh_right.pack(side=tk.RIGHT, fill=tk.Y)

        # Button Font size
        self.btn_dec_font = self.create_custom_button(
            sh_right, "-",
            self.decrease_font,
            font=(self.main_font_family, 9, "bold"),
            padx=20,
            pady=3
        )
        self.btn_dec_font.pack(side=tk.LEFT, padx=5)
        self.btn_down_font_tooltip = ToolTip(self.btn_dec_font, l_ui["tip_down_font"], scale=self.scale)

        self.btn_inc_font = self.create_custom_button(
            sh_right, "+",
            self.increase_font,
            font=(self.main_font_family, 9, "bold"),
            padx=20,
            pady=3
        )
        self.btn_inc_font.pack(side=tk.LEFT, padx=5)
        self.btn_up_font_tooltip = ToolTip(self.btn_inc_font, l_ui["tip_up_font"], scale=self.scale)

        # Label Font size
        self.font_label = tk.Label(
            sh_right,
            text=str(self.font_size),
            bg=COLOR_BG_HEADER,
            fg=COLOR_TEXT_BRIGHT,
            width=3,
            font=(self.main_font_family, 9, "bold"),
        )
        self.font_label.pack(side=tk.LEFT)

        # --- MAIN LOG DISPLAY AREA ---
        self.main_container = tk.Frame(self.root, bg=COLOR_BG_MAIN)

        # Grid placement with specific padding (top=0, bottom=10)
        self.main_container.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=self.sc(10),
            pady=(0, 10)
        )

        # Configure grid weight to allow the container to expand
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        # cursor
        self.txt_area = tk.Text(
            self.main_container,
            wrap=tk.NONE,
            bg=COLOR_BG_MAIN,
            fg=COLOR_TEXT_MAIN,
            font=(self.mono_font_family, self.font_size),
            borderwidth=0,
            highlightthickness=0,
            padx=5, pady=5,
            undo=False,
            selectforeground="#ffffff",
            insertwidth=4,
            insertontime=600,
            insertofftime=300,
            insertbackground=COLOR_TEXT_BRIGHT,
            selectbackground=COLOR_ACCENT,
            inactiveselectbackground=COLOR_ACCENT,
            exportselection=False
        )

        # --- Custom Context Menu (Right-click) ---
        # Create a hidden top-level window for the menu
        self.context_menu = tk.Toplevel(self.root)
        self.context_menu.withdraw()
        self.context_menu.overrideredirect(True)

        # Outer border configuration
        self.context_menu.configure(
            bg=COLOR_SEPARATOR,
            padx=1,
            pady=1
        )

        # Inner container for menu items
        self.menu_inner = tk.Frame(self.context_menu, bg=COLOR_BTN_DEFAULT)
        self.menu_inner.pack(fill="both", expand=True)

        self.search_context_menu = tk.Toplevel(self.root)
        self.search_context_menu.withdraw()
        self.search_context_menu.overrideredirect(True)
        self.search_context_menu.configure(
            bg=COLOR_SEPARATOR,
            padx=1,
            pady=1
        )

        self.search_menu_inner = tk.Frame(self.search_context_menu, bg=COLOR_BTN_DEFAULT)
        self.search_menu_inner.pack(fill="both", expand=True)

        self._build_search_menu_items()

        def add_custom_item(command):
            """Add a stylized clickable item to the custom context menu."""
            item = tk.Label(
                self.menu_inner,
                text="",
                bg=COLOR_BTN_DEFAULT,
                fg=COLOR_TEXT_BRIGHT,
                font=(self.main_font_family, 10),
                padx=15,
                pady=7,
                anchor="w",
                cursor="hand2"
            )
            item.pack(fill="x")

            item.bind(
                "<Enter>",
                lambda event: item.config(bg=COLOR_ACCENT)
            )
            item.bind(
                "<Leave>",
                lambda event: item.config(bg=COLOR_BTN_DEFAULT)
            )

            # Execute command and hide menu on click
            item.bind(
                "<Button-1>",
                lambda event: [command(), self.context_menu.withdraw()]
            )

            return item

        # --- CONTEXT MENU ITEMS ---
        self.menu_items = []

        # Item 0: Copy
        self.menu_items.append(
            add_custom_item(self.copy_selection)
        )

        # Item 1: Select All
        self.menu_items.append(
            add_custom_item(lambda: self.txt_area.tag_add("sel", "1.0", "end"))
        )

        # Item 2: Google Search (Stored in a variable for dynamic toggle)
        self.google_menu_item = add_custom_item(self.search_on_google)
        self.menu_items.append(self.google_menu_item)

        # Initial visibility check based on loaded config
        if not self.show_google_search.get():
            self.google_menu_item.pack_forget()

        # --- Scrollbar configuration ---
        self.v_scroll = ttk.Scrollbar(
            self.main_container,
            orient="vertical",
            command=self.txt_area.yview,
            style="Vertical.TScrollbar"
        )
        self.txt_area.configure(yscrollcommand=self.v_scroll.set)

        # --- Text area layout ---
        self.txt_area.grid(row=0, column=0, sticky="nsew")
        self.v_scroll.grid(row=0, column=1, sticky="ns")

        # --- Text area bindings ---
        # Focus on click to display the cursor
        self.txt_area.bind("<Button-1>", lambda event: self.txt_area.focus_set())

        # Reset timer and show cursor on click, key press, or mouse movement
        self.txt_area.bind("<Button-1>", self.reset_cursor_timer, add="+")
        self.txt_area.bind("<Key>", self.reset_cursor_timer, add="+")
        self.txt_area.bind("<Motion>", self.reset_cursor_timer, add="+")

        # Start the initial timer
        self.reset_cursor_timer()

        # Prevent typing while allowing navigation ("soft" read-only)
        allowed_keys = (
            "Up", "Down", "Left", "Right", "Next", "Prior", "Home", "End"
        )
        self.txt_area.bind(
            "<Key>",
            lambda event: "break" if event.keysym not in allowed_keys else None
        )

        # Context menu and interactions
        self.txt_area.bind("<Button-3>", self.show_context_menu)
        self.txt_area.bind("<Double-Button-1>", self.on_double_click_line)

        # --- LOADING OVERLAY ---
        self.overlay = tk.Frame(self.main_container, bg=COLOR_BG_MAIN)
        self.loading_label = tk.Label(
            self.overlay,
            text="",
            bg=COLOR_BG_MAIN,
            fg=COLOR_TEXT_MAIN,
            font=(self.main_font_family, 12, "bold")
        )
        self.loading_label.pack(expand=True)

        # --- FOOTER SECTION ---
        footer = tk.Frame(self.root, bg=COLOR_BG_FOOTER, padx=self.sc(10), pady=self.sc(10))
        footer.grid(row=3, column=0, sticky="ew")

        # 1. Indicator Light
        self.status_indicator = tk.Canvas(
            footer, width=self.sc(32), height=self.sc(32),
            bg=COLOR_BG_FOOTER, highlightthickness=0
        )
        self.status_indicator.pack(side=tk.LEFT, padx=(self.sc(32), 0))

        # Creation of the circle
        self.status_circle = self.status_indicator.create_oval(
            2, 2, self.sc(28), self.sc(28),
            fill=COLOR_SEPARATOR,
            outline="#c4c4c4",
            width=1
        )

        self.timer_container = tk.Frame(footer, bg=COLOR_BG_FOOTER)
        self.timer_container.pack(side=tk.LEFT, fill=tk.Y)

        # --- Addition of the separator ---
        self.timer_sep = tk.Frame(self.timer_container, bg=COLOR_SEPARATOR, width=2)

        # 2. Inactivity timer
        self.lbl_timer = tk.Label(
            self.timer_container,
            textvariable=self.inactivity_timer_var,
            bg=COLOR_BG_FOOTER,
            fg=COLOR_DANGER,
            font=(self.main_font_family, 9, "bold")
        )
        self.lbl_timer.pack(side=tk.LEFT, padx=(self.sc(10), self.sc(10)))

        # Attach the observer
        self.inactivity_timer_var.trace_add("write", self._toggle_timer_separator)

        # --- Addition of the separator ---
        tk.Frame(
            footer,
            bg=COLOR_SEPARATOR,
            width=2
        ).pack(side=tk.LEFT, fill=tk.Y, padx=self.sc(10), pady=2)

        self.footer_var = tk.StringVar()
        self.stats_var = tk.StringVar()
        self.size_var = tk.StringVar()
        self.limit_var = tk.StringVar()
        self.paused_var = tk.StringVar()
        self.wrap_var = tk.StringVar()

        # Shared label style to reduce repetition
        footer_style = {
            "anchor": tk.W,
            "bg": COLOR_BG_FOOTER,
            "font": (self.emoji_font_family, 9, "bold")
        }

        # 3. The file path (📍)
        tk.Label(
            footer, textvariable=self.footer_var,
            fg=COLOR_TEXT_MAIN, **footer_style
        ).pack(side=tk.LEFT)

        # --- Addition of the separator ---
        self.sep_lines = tk.Frame(footer, bg=COLOR_SEPARATOR, width=2)

        # 4. Total number of lines (📈)
        self.label_lines = tk.Label(
            footer, textvariable=self.stats_var,
            fg=COLOR_TEXT_MAIN, **footer_style
        )

        # --- Addition of the separator ---
        self.sep_size = tk.Frame(footer, bg=COLOR_SEPARATOR, width=2)

        # 5. File size (📁)
        self.label_size = tk.Label(
            footer, textvariable=self.size_var,
            fg=COLOR_TEXT_MAIN, **footer_style
        )

        # --- Addition of the separators and labels ---
        self.sep_limit = tk.Frame(footer, bg=COLOR_SEPARATOR, width=2)

        # 6. Lines limited to 1000 (⚠️)
        self.label_limit = tk.Label(
            footer,
            textvariable=self.limit_var,
            fg=COLOR_WARNING,
            **footer_style
        )

        self.sep_pause = tk.Frame(footer, bg=COLOR_SEPARATOR, width=2)

        # 7. Paused (⏸️)
        self.label_pause = tk.Label(
            footer,
            textvariable=self.paused_var,
            fg=COLOR_DANGER,
            **footer_style
        )

        self.sep_wrap = tk.Frame(footer, bg=COLOR_SEPARATOR, width=2)

        # 8. Word Wrap Status
        self.label_wrap = tk.Label(
            footer,
            textvariable=self.wrap_var,
            fg=COLOR_ACCENT,
            **footer_style
        )

        # --- GitHub link in the footer ---
        current_lang_str = self.current_lang.get()
        l_ui = LANGS.get(current_lang_str, LANGS["EN"])

        self.github_label = tk.Label(
            footer,
            text=f"Kodi Log Monitor {APP_VERSION}",
            bg=COLOR_BG_FOOTER,
            fg=COLOR_TEXT_GREY,
            font=(self.main_font_family, 9, "bold"),
            cursor="hand2"
        )
        self.github_label.pack(side=tk.RIGHT, padx=5)

        self.github_label.bind("<Button-1>", self.open_github_link, add="+")
        self.github_label.bind("<Enter>", lambda e: self.github_label.config(fg=COLOR_TEXT_MAIN), add="+")
        self.github_label.bind("<Leave>", lambda e: self.github_label.config(fg=COLOR_TEXT_GREY), add="+")

        self.github_tooltip = ToolTip(
            self.github_label,
            l_ui.get("tip_github", "View the source code on GitHub"),
            scale=self.scale
        )

    def _toggle_timer_separator(self, *args):
        """
        Dynamically shows/hides the separator and forces it
        to be positioned to the left of the label.
        """
        message = self.inactivity_timer_var.get().strip()
        if message:
            # Use 'before' to ensure it stays on the left of the label
            self.timer_sep.pack(
                side=tk.LEFT,
                fill=tk.Y,
                padx=(self.sc(10), 0),
                pady=2,
                before=self.lbl_timer
            )
        else:
            self.timer_sep.pack_forget()


class ToolTip:
    def __init__(self, widget, text, scale=1.0):
        self.widget = widget
        self.text = text
        self.scale = scale
        self.tip_window = None
        self.id = None
        self.delay = 1000

        # Bind events to show/hide tooltip
        self.widget.bind('<Enter>', self.schedule_tip, add="+")
        self.widget.bind('<Leave>', self.hide_tip, add="+")
        self.widget.bind('<ButtonPress>', self.hide_tip, add="+")

    def schedule_tip(self, event=None):
        self.cancel_tip()
        # Schedule the tooltip display after the specified delay
        self.id = self.widget.after(self.delay, self.show_tip)

    def cancel_tip(self):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

    def show_tip(self, event=None):
        if not self.text:
            return

        # 1. Create the tooltip window
        self.tip_window = tw = tk.Toplevel(self.widget)
        # Remove window decorations (borders, title bar)
        tw.wm_overrideredirect(True)

        # Ensure the tooltip stays on top of other windows
        tw.attributes("-topmost", True)

        # Linux compatibility: Set alpha to 0 initially to calculate size
        # without showing the window at the wrong position (0,0)
        if sys.platform.startswith('linux'):
            tw.attributes("-alpha", 0.0)

        label = tk.Label(
            tw,
            text=self.text,
            justify='left',
            background=COLOR_BG_TIPS,
            foreground=COLOR_TEXT_TIPS,
            relief='solid',
            borderwidth=1,
            font=("Segoe UI", "9", "normal"),
            padx=self.sc(30),
            pady=self.sc(20)
        )
        label.pack()

        # Force update to calculate the required width and height
        tw.update_idletasks()

        # Use requested width/height for better reliability across OS
        tip_width = tw.winfo_reqwidth()
        tip_height = tw.winfo_reqheight()

        # 2. Retrieve coordinates
        root = self.widget.winfo_toplevel()

        # Absolute coordinates of the widget triggering the tooltip
        widget_x = self.widget.winfo_rootx()
        widget_y = self.widget.winfo_rooty()
        widget_h = self.widget.winfo_height()

        # Main application boundaries
        root_x = root.winfo_rootx()
        root_y = root.winfo_rooty()
        root_w = root.winfo_width()
        root_h = root.winfo_height()

        # Default position: Below the widget with a small offset
        x = widget_x + self.sc(20)
        y = widget_y + widget_h + self.sc(5)

        # 3. BOUNDARY ADJUSTMENTS (Keep tooltip inside the app)

        # If tooltip exceeds the right edge, shift it to the left
        if x + tip_width > root_x + root_w:
            x = root_x + root_w - tip_width - self.sc(10)

        # If tooltip exceeds the bottom edge, display it ABOVE the widget
        if y + tip_height > root_y + root_h:
            y = widget_y - tip_height - self.sc(5)

        # Safety: Ensure it doesn't clip through the left or top edges
        x = max(root_x, x)
        y = max(root_y, y)

        # 4. Apply geometry and make the window visible
        tw.wm_geometry(f"+{int(x)}+{int(y)}")

        if sys.platform.startswith('linux'):
            # Restore visibility for Linux after correct placement
            tw.attributes("-alpha", 1.0)
        else:
            tw.deiconify()

    def hide_tip(self, event=None):
        self.cancel_tip()
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()

    def sc(self, val):
        """Scale a value based on the application's scaling factor."""
        return int(val * self.scale)
