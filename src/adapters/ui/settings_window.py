import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Dict, Any
from loguru import logger
from src.ports.settings_port import SettingsPort
from src.adapters.settings.json_settings_schema_adapter import JsonSettingsSchemaAdapter


class SettingsWindow:
    def __init__(
        self,
        parent,
        settings_port: SettingsPort,
        on_theme_change: Callable[[str], None] = None,
        on_settings_saved: Callable[[], None] = None,
    ):
        self.parent = parent
        self.settings_port = settings_port
        self.on_theme_change = on_theme_change
        self.on_settings_saved = on_settings_saved
        self.schema_adapter = JsonSettingsSchemaAdapter()

        self.window = None
        self.setting_vars: Dict[str, Any] = {}
        self.original_values: Dict[str, Any] = {}

    def show(self):
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.parent)
        self.window.title("Settings")
        self.window.resizable(False, False)
        self.window.transient(self.parent)
        self.window.grab_set()

        self._setup_ui()
        self._auto_size_and_center()

    def _setup_ui(self):
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        for category in self.schema_adapter.get_categories():
            for setting in category.get("settings", []):
                key = setting["key"]
                default = setting.get("default")
                current_value = self.settings_port.get_setting(key, default)
                self.original_values[key] = current_value

        for category in self.schema_adapter.get_categories():
            self._create_category_section(main_frame, category)

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(
            button_frame, text="Reset to Default", command=self._reset_to_default
        ).pack(side=tk.LEFT)

        ttk.Button(button_frame, text="Cancel", command=self._on_cancel).pack(
            side=tk.RIGHT, padx=(5, 0)
        )

        ttk.Button(button_frame, text="Apply", command=self._on_apply).pack(
            side=tk.RIGHT
        )

    def _create_category_section(self, parent, category):
        section = ttk.LabelFrame(parent, text=category["title"], padding="10")
        section.pack(fill=tk.X, pady=(0, 10))

        row = 0
        for setting in category.get("settings", []):
            self._create_setting_control(section, setting, row)
            row += 1

        section.columnconfigure(1, weight=1)

    def _create_setting_control(self, parent, setting, row):
        key = setting["key"]
        title = setting["title"]
        setting_type = setting["type"]
        default = setting.get("default")
        current_value = self.settings_port.get_setting(key, default)

        ttk.Label(parent, text=f"{title}:").grid(row=row, column=0, sticky=tk.W, pady=5)

        if setting_type == "checkbox":
            var = tk.BooleanVar(value=current_value)
            control = ttk.Checkbutton(parent, text="", variable=var)
            control.grid(row=row, column=1, sticky=tk.W, pady=5, padx=(10, 0))
            self.setting_vars[key] = var

        elif setting_type == "select":
            var = tk.StringVar(value=current_value)
            options = setting.get("options", [])
            control = ttk.Combobox(
                parent, textvariable=var, values=options, state="readonly", width=20
            )
            control.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
            self.setting_vars[key] = var

            if key == "theme" and self.on_theme_change:
                control.bind(
                    "<<ComboboxSelected>>", lambda e, k=key: self._on_setting_change(k)
                )

        elif setting_type == "slider":
            var = tk.IntVar(value=current_value)
            min_val = setting.get("min", 0)
            max_val = setting.get("max", 100)
            control = tk.Scale(
                parent,
                variable=var,
                from_=min_val,
                to=max_val,
                orient=tk.HORIZONTAL,
                length=200,
            )
            control.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
            self.setting_vars[key] = var

        elif setting_type == "spinbox":
            var = tk.IntVar(value=current_value)
            min_val = setting.get("min", 0)
            max_val = setting.get("max", 100)
            step = setting.get("step", 1)
            control = tk.Spinbox(
                parent,
                textvariable=var,
                from_=min_val,
                to=max_val,
                increment=step,
                width=10,
                state="readonly",
            )
            control.grid(row=row, column=1, sticky=tk.W, pady=5, padx=(10, 0))
            self.setting_vars[key] = var

        elif setting_type == "text":
            var = tk.StringVar(value=current_value)
            control = ttk.Entry(parent, textvariable=var, width=25)
            control.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
            self.setting_vars[key] = var

    def _on_setting_change(self, key):
        if key != "theme" or not self.on_theme_change:
            return

        new_theme = self.setting_vars[key].get()
        try:
            self.on_theme_change(new_theme)
        except Exception as e:
            logger.error(f"Failed to preview theme {new_theme}: {e}")
            original_theme = self.original_values.get(key, "arc")
            self.setting_vars[key].set(original_theme)
            messagebox.showerror("Error", f"Failed to apply theme: {new_theme}")

    def _auto_size_and_center(self):
        self.window.update_idletasks()

        req_width = self.window.winfo_reqwidth()
        req_height = self.window.winfo_reqheight()

        width = max(req_width, 280)
        height = max(req_height, 120)

        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2

        self.window.geometry(f"{width}x{height}+{x}+{y}")

    def _reset_to_default(self):
        defaults = self.schema_adapter.get_all_defaults()
        for key, default_value in defaults.items():
            if key not in self.setting_vars:
                continue

            self.setting_vars[key].set(default_value)

            if key != "theme" or not self.on_theme_change:
                continue

            try:
                self.on_theme_change(default_value)
            except Exception as exception:
                logger.error(f"Failed to preview default theme {default_value}: {exception}")

    def _on_apply(self):
        try:
            changed_settings = []

            for key, var in self.setting_vars.items():
                value = var.get()
                original_value = self.original_values.get(key)

                if value != original_value:
                    if self.schema_adapter.validate_setting_value(key, value):
                        self.settings_port.set_setting(key, value)
                        changed_settings.append((key, value))
                        logger.info(
                            f"Setting '{key}' changed from {original_value} to: {value}"
                        )
                    else:
                        logger.warning(f"Invalid value for setting {key}: {value}")

            if changed_settings:
                self.settings_port.save_settings()
                logger.info(f"Saved {len(changed_settings)} changed settings")
            else:
                logger.debug("No settings were changed")

            if self.on_settings_saved:
                self.on_settings_saved()

            self.window.destroy()
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            messagebox.showerror("Error", "Failed to save settings")

    def _on_cancel(self):
        # Revert all changes
        if self.on_theme_change and "theme" in self.setting_vars:
            original_theme = self.original_values.get("theme", "arc")
            current_theme = self.setting_vars["theme"].get()
            if current_theme != original_theme:
                try:
                    self.on_theme_change(original_theme)
                except Exception as e:
                    logger.error(f"Failed to revert to original theme: {e}")
        self.window.destroy()
