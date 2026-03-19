import os

from config import *
from languages import LANGS


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
                    f"{('1' if self.show_google_search.get() else '0'):<{w}} # Show google search menu",
                    f"{str(self.theme_mode.get()):<{w}} # Theme mode",
                    f"{str(self.inactivity_limit):<{w}} # Inactivity limit seconds (0 disable)",
                    f"{str(self.paste_url):<{w}} # Url for upload",
                    f"{str(self.max_size_mb):<{w}} # Max size Mo limit (10 Mo default)",
                    f"{str(self.skip_version):<{w}} # Skip latest version",
                    f"{('1' if self.updates_enabled else '0'):<{w}} # Updates enabled 1 disable 0",
                    f"{str(SINGLE_INSTANCE_HOST):<{w}} # Single instance host",
                    f"{str(SINGLE_INSTANCE_PORT):<{w}} # Single instance port"
                ]
                f.write("\n".join(config_data))
        except (IOError, OSError) as e:
            print(f"Error saving session: {e}")

    def load_session(self):
        """
        Load previous session settings from the configuration file.
        """
        if not os.path.exists(CONFIG_FILE):
            # No config file, perform basic UI updates and return
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

                # 9. theme windows light, dark, auto
                if len(lines) >= 9:
                    self.theme_mode.set(lines[8])

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
                    self.updates_enabled = (lines[13] == "1")

                # 15. Single Instance Host (AJOUT)
                if len(lines) >= 15:
                    global SINGLE_INSTANCE_HOST
                    SINGLE_INSTANCE_HOST = lines[14].strip()

                # 16. Single Instance Port (AJOUT)
                if len(lines) >= 16:
                    try:
                        global SINGLE_INSTANCE_PORT
                        SINGLE_INSTANCE_PORT = int(lines[15].strip())
                    except ValueError:
                        pass

        except (IOError, OSError, Exception) as e:
            # Print error for debugging purposes if needed
            print(f"Error loading configuration: {e}")

        # Finalize UI setup after loading data
        self.retranslate_ui(False)
        self.update_tags_config()

        # Automatically resume monitoring if a valid log file was found
        if self.log_file_path:
            self.start_monitoring(self.log_file_path, False, False)
