import os
import config
from config import *
from config import APP_THEME
from languages import LANGS, LANG_NAMES


class SessionMixin:
    """Manages the saving and loading of user configuration."""

    def save_session(self):
        """
        Saves the current application state with perfectly aligned comments.
        """
        try:
            modes = ["all", "info", "warning", "error", "debug"]
            filter_states = ",".join(["1" if self.filter_vars[m].get() else "0" for m in modes])

            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                # We use a fixed width of 50 characters for the value part
                w = 50
                config_data = [
                    f"{str(self.log_file_path):<{w}} # Log file path",
                    f"{str(self.current_lang.get()):<{w}} # Language",
                    f"{('1' if self.load_full_file.get() else '0'):<{w}} # Load full file",
                    f"{str(self.font_size):<{w}} # Font size",
                    f"{str(self.window_geometry):<{w}} # Window geometry",
                    f"{str(self.selected_list.get()):<{w}} # Selected keyword list",
                    f"{filter_states:<{w}} # Filter states (ALL, INFO, WARNING, ERROR, DEBUG)",
                    f"{('1' if self.show_google_search.get() else '0'):<{w}} # Show google search menu (0=hide)",
                    f"{'deprecated':<{w}} # Theme mode (deprecated - kept for backward compat)",
                    f"{str(self.inactivity_limit):<{w}} # Inactivity limit seconds (0=disable)",
                    f"{str(self.paste_url):<{w}} # Url for upload",
                    f"{str(self.max_size_mb):<{w}} # Max size Mo limit (10 Mo default)",
                    f"{str(self.skip_version):<{w}} # Skip latest version",
                    f"{('1' if self.updates_enabled else '0'):<{w}} # Updates (1=enable 0=disable)",
                    f"{str(SINGLE_INSTANCE_HOST):<{w}} # Single instance host",
                    f"{str(SINGLE_INSTANCE_PORT):<{w}} # Single instance port",
                    f"{('1' if self.enable_single_instance_var else '0'):<{w}} # Enable single instance (1=True, 0=False)",
                    f"{str(self.app_theme.get()):<{w}} # App color theme (dark/light)",
                    f"{str(self.window_state):<{w}} # Window state (normal/zoomed)",
                    f"{('1' if self.debug_mode else '0'):<{w}} # Debug mode (1=on 0=off)",
                ]
                f.write("\n".join(config_data))
        except (IOError, OSError) as e:
            print(f"Error saving session: {e}")

    def load_session(self):
        """
        Load previous session settings from the configuration file.
        """
        if not os.path.exists(CONFIG_FILE):
            # First launch — no config file yet.
            # Start maximised so the user sees the full interface immediately.
            self.window_state = "zoomed"
            self.retranslate_ui(False)
            self.update_tags_config()
            return

        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                # Use split('#')[0] to get only the value before the comment
                lines = [line.split('#')[0].strip() for line in f.read().splitlines()]

                # 1. Log file path
                if len(lines) >= 1 and os.path.exists(lines[0]):
                    self.log_file_path = lines[0]

                # 2. Current language
                if len(lines) >= 2 and lines[1] in LANGS:
                    self.current_lang.set(lines[1])
                    # Sync combo display (shows full name, not code)
                    if hasattr(self, "combo_lang"):
                        self.combo_lang.set(LANG_NAMES.get(lines[1], lines[1]))

                # 3. Load full file preference
                if len(lines) >= 3:
                    self.load_full_file.set(lines[2] == "1")

                # 4. Font size
                if len(lines) >= 4:
                    try:
                        self.font_size = int(lines[3])
                    except ValueError:
                        pass

                # 5. Window geometry
                if len(lines) >= 5:
                    self.window_geometry = lines[4]

                # 6. Selected keyword list
                if len(lines) >= 6:
                    none_values = [v["none"] for v in LANGS.values()]
                    if lines[5] not in none_values:
                        self.selected_list.set(lines[5])
                    else:
                        current_none = LANGS[self.current_lang.get()]["none"]
                        self.selected_list.set(current_none)

                # 7. Filter states
                if len(lines) >= 7:
                    states = lines[6].split(",")
                    modes = ["all", "info", "warning", "error", "debug"]
                    for i, state in enumerate(states):
                        if i < len(modes):
                            self.filter_vars[modes[i]].set(state == "1")

                # 8. Google Search Context Menu Visibility
                if len(lines) >= 8:
                    self.show_google_search.set(lines[7] == "1")
                else:
                    # Default to enabled if the line doesn't exist yet
                    self.show_google_search.set(True)

                # 9. (deprecated - was OS title-bar theme combobox, now ignored)

                # 10. Inactivity Limit
                if len(lines) >= 10:
                    try:
                        self.inactivity_limit = int(lines[9])
                    except ValueError:
                        self.inactivity_limit = 300

                # 11. Paste URL (AJOUT)
                if len(lines) >= 11:
                    self.paste_url = lines[10].strip()
                else:
                    self.paste_url = DEFAULT_PASTE_URL

                # 12. Max Size MB Limit (AJOUT)
                if len(lines) >= 12:
                    try:
                        self.max_size_mb = int(lines[11])
                    except ValueError:
                        self.max_size_mb = 10

                # 13. Skip version
                if len(lines) >= 13:
                    self.skip_version = lines[12].strip()

                # 14. Updates Enabled
                if len(lines) >= 14:
                    self.updates_enabled = (lines[13].strip() == "1")

                # 15. Single Instance Host (AJOUT)
                if len(lines) >= 15:
                    config.SINGLE_INSTANCE_HOST = lines[14].strip()

                # 16. Single Instance Port (AJOUT)
                if len(lines) >= 16:
                    try:
                        config.SINGLE_INSTANCE_PORT = int(lines[15].strip())
                    except ValueError:
                        pass

                # Line 17: Enable single instance (Global variable)
                if len(lines) >= 17:
                    is_enabled = (lines[16].strip() == "1")
                    config.ENABLE_SINGLE_INSTANCE = is_enabled
                    self.enable_single_instance_var = is_enabled
                else:
                    self.enable_single_instance_var = config.ENABLE_SINGLE_INSTANCE

                # Line 18: App color theme (dark / light)
                if len(lines) >= 18:
                    val = lines[17].strip().lower()
                    if val in ("dark", "light"):
                        self.app_theme.set(val)

                # Line 19: Window state (normal / zoomed)
                if len(lines) >= 19:
                    val = lines[18].strip().lower()
                    if val in ("normal", "zoomed"):
                        self.window_state = val

                # Line 20: Debug mode (0 / 1)
                if len(lines) >= 20:
                    self.debug_mode = (lines[19].strip() == "1")

        except Exception as e:
            print(f"Error loading configuration: {e}")

        # Finalize UI setup after loading data
        if hasattr(self, 'btn_log'):
            self.retranslate_ui(False)
            self.update_tags_config()

        # Resume monitoring if path exists
        if self.log_file_path:
            self.start_monitoring(self.log_file_path, False, False)
