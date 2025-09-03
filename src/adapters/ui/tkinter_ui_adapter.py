import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import List, Callable, Optional
from loguru import logger
from ttkthemes import ThemedTk
from src.ports.ui_port import UIPort
from src.ports.settings_port import SettingsPort
from src.adapters.ui.settings_window import SettingsWindow


class TkinterUIAdapter(UIPort):
    def __init__(self, settings_port: SettingsPort, theme=None):
        self.settings_port = settings_port
        self.settings_window = None
        
        # Use saved theme or default
        if theme is None:
            theme = self.settings_port.get_setting("theme", "arc")
        
        self.root = ThemedTk(theme=theme)
        self.root.title("Clip Flow")
        self.root.geometry("400x600")
        self.available_themes = self.root.get_themes()
        self.current_theme = theme

        self.history_listbox = None
        self.search_var = None
        self.search_entry = None

        self._copy_callback: Callable[[int], None] | None = None
        self._search_callback: Callable[[str], None] | None = None
        self._clear_callback: Callable[[], None] | None = None
        self._hide_callback: Optional[Callable[[], None]] = None

        self._current_items: List[str] = []
        self._is_hidden = False

        self._setup_ui()
        self._setup_window_close()
        logger.debug("TkinterUIAdapter initialized.")

    def show_history(self, items: List[str]) -> None:
        def update_ui():
            current_selection = self.history_listbox.selection()
            for item in self.history_listbox.get_children():
                self.history_listbox.delete(item)
            self._current_items = items.copy()

            for i, item in enumerate(items):
                preview = item.replace("\n", " ").replace("\r", " ")
                if len(preview) > 50:
                    preview = preview[:47] + "..."
                item_id = self.history_listbox.insert("", "end", text=str(i+1), values=(preview,))

            if len(items) > 0 and not self.search_var.get() and not current_selection:
                first_item = self.history_listbox.get_children()[0]
                self.history_listbox.selection_set(first_item)
                self.history_listbox.focus(first_item)
            elif current_selection and len(items) > 0:
                children = self.history_listbox.get_children()
                if children:
                    index = min(len(current_selection)-1, len(children) - 1)
                    item_to_select = children[index]
                    self.history_listbox.selection_set(item_to_select)
                    self.history_listbox.focus(item_to_select)

        if self.root and self.history_listbox:
            self.root.after(0, update_ui)

    def show_message(self, message: str, message_type: str = "info") -> None:
        def show_msg():
            if message_type == "info":
                messagebox.showinfo("Info", message)
            elif message_type == "warning":
                messagebox.showwarning("Warning", message)
            elif message_type == "error":
                messagebox.showerror("Error", message)
            else:
                messagebox.showinfo("Message", message)

        if self.root:
            self.root.after(0, show_msg)

    def run(self) -> None:
        logger.info("Starting Tkinter UI.")
        self.search_entry.focus_set()
        self.root.mainloop()

    def register_copy_callback(self, callback: Callable[[int], None]) -> None:
        self._copy_callback = callback

    def register_search_callback(self, callback: Callable[[str], None]) -> None:
        self._search_callback = callback

    def register_clear_callback(self, callback: Callable[[], None]) -> None:
        self._clear_callback = callback

    def register_hide_callback(self, callback: Callable[[], None]) -> None:
        self._hide_callback = callback

    def show_window(self) -> None:
        if self.root and self._is_hidden:
            self.root.deiconify()
            self.root.lift()
            self.root.attributes('-topmost', True)
            self.root.after_idle(lambda: self.root.attributes('-topmost', False))
            self.search_entry.focus_set()
            self._is_hidden = False
            logger.debug("Window shown")

    def hide_window(self) -> None:
        if self.root and not self._is_hidden:
            self.root.withdraw()
            self._is_hidden = True
            logger.debug("Window hidden to system tray")

    def shutdown(self) -> None:
        if self.root:
            self.root.destroy()

    def _setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        search_frame = ttk.Frame(main_frame)
        search_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        search_frame.columnconfigure(1, weight=1)

        ttk.Label(search_frame, text="🔍").grid(row=0, column=0, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.grid(row=0, column=1, sticky=(tk.W, tk.E))
        self.search_var.trace("w", self._on_search_change)

        self.search_entry.bind("<Key>", self._on_key_press)
        self.search_entry.bind("<Up>", self._navigate_up)
        self.search_entry.bind("<Down>", self._navigate_down)
        self.search_entry.bind("<Return>", self._copy_selected)

        history_frame = ttk.LabelFrame(
            main_frame, text="Clipboard History", padding="5"
        )
        history_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(0, weight=1)

        listbox_frame = ttk.Frame(history_frame)
        listbox_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        listbox_frame.columnconfigure(0, weight=1)
        listbox_frame.rowconfigure(0, weight=1)

        self.history_listbox = ttk.Treeview(
            listbox_frame,
            columns=("content",),
            show="tree headings",
            height=15
        )
        self.history_listbox.heading("#0", text="№")
        self.history_listbox.heading("content", text="Content")
        self.history_listbox.column("#0", width=40, minwidth=40)
        self.history_listbox.column("content", width=320, minwidth=200)
        self.history_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        scrollbar = ttk.Scrollbar(
            listbox_frame, orient=tk.VERTICAL, command=self.history_listbox.yview
        )
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.history_listbox.configure(yscrollcommand=scrollbar.set)

        self.history_listbox.bind("<Double-Button-1>", self._on_double_click)
        self.history_listbox.bind("<Return>", self._on_double_click)
        self.history_listbox.bind("<Button-3>", self._show_context_menu)

        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Copy", command=self._copy_selected)
        self.context_menu.add_command(
            label="View Full Text", command=self._view_full_text
        )

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))

        copy_btn = ttk.Button(
            button_frame, text="Copy Selected", command=self._copy_selected
        )
        copy_btn.pack(side=tk.LEFT, padx=(0, 5))

        view_btn = ttk.Button(
            button_frame, text="View Full Text", command=self._view_full_text
        )
        view_btn.pack(side=tk.LEFT)

        clear_btn = ttk.Button(
            button_frame, text="Clear History", command=self._clear_history
        )
        clear_btn.pack(side=tk.RIGHT)
        
        settings_btn = ttk.Button(
            button_frame, text="⚙️ Settings", command=self._open_settings
        )
        settings_btn.pack(side=tk.RIGHT, padx=(0, 5))

    def _setup_window_close(self):
        def on_closing():
            logger.info("Window close event detected. Hiding to system tray.")
            self.hide_window()
            if self._hide_callback:
                self._hide_callback()

        self.root.protocol("WM_DELETE_WINDOW", on_closing)

    def _on_search_change(self, *args):
        if self._search_callback:
            query = self.search_var.get()
            self._search_callback(query)

    def _on_key_press(self, event):
        if len(event.keysym) == 1 and event.keysym.isprintable():
            return
        if event.keysym in ["Up", "Down", "Return", "Tab"]:
            return

    def _navigate_up(self, event):
        if self.search_var.get():
            return "break"

        current = self.history_listbox.selection()
        if current:
            children = self.history_listbox.get_children()
            current_index = children.index(current[0])
            if current_index > 0:
                self.history_listbox.selection_remove(current[0])
                prev_item = children[current_index - 1]
                self.history_listbox.selection_set(prev_item)
                self.history_listbox.focus(prev_item)
                self.history_listbox.see(prev_item)
        return "break"

    def _navigate_down(self, event):
        if self.search_var.get():
            return "break"

        current = self.history_listbox.selection()
        if current:
            children = self.history_listbox.get_children()
            current_index = children.index(current[0])
            if current_index < len(children) - 1:
                self.history_listbox.selection_remove(current[0])
                next_item = children[current_index + 1]
                self.history_listbox.selection_set(next_item)
                self.history_listbox.focus(next_item)
                self.history_listbox.see(next_item)
        return "break"

    def _on_double_click(self, event=None):
        self._copy_selected()

    def _copy_selected(self, event=None):
        selection = self.history_listbox.selection()
        if not selection:
            self.show_message("Please select an item to copy.", "warning")
            return

        children = self.history_listbox.get_children()
        index = children.index(selection[0])
        
        if self._copy_callback:
            self._copy_callback(index)
            
        self.hide_window()
        if self._hide_callback:
            self._hide_callback()

    def _view_full_text(self):
        selection = self.history_listbox.selection()
        if not selection:
            self.show_message("Please select an item to view.", "warning")
            return

        children = self.history_listbox.get_children()
        index = children.index(selection[0])
        
        if index >= len(self._current_items):
            return

        item = self._current_items[index]

        popup = tk.Toplevel(self.root)
        popup.title("Full Text")
        popup.geometry("500x400")

        frame = ttk.Frame(popup, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        text_widget = scrolledtext.ScrolledText(
            frame, wrap=tk.WORD, font=("Consolas", 10)
        )
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert(tk.END, item)
        text_widget.config(state=tk.DISABLED)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        def copy_and_close():
            if self._copy_callback:
                self._copy_callback(index)
            popup.destroy()
            
            self.hide_window()
            if self._hide_callback:
                self._hide_callback()

        copy_popup_btn = ttk.Button(
            btn_frame, text="Copy to Clipboard", command=copy_and_close
        )
        copy_popup_btn.pack(side=tk.RIGHT)

    def _show_context_menu(self, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def _clear_history(self):
        if messagebox.askyesno(
            "Clear History", "Are you sure you want to clear all clipboard history?"
        ):
            if self._clear_callback:
                self._clear_callback()

    def _open_settings(self):
        # Always create a new settings window to ensure fresh values
        self.settings_window = SettingsWindow(
            self.root,
            self.settings_port,
            self._on_theme_change_from_settings
        )
        self.settings_window.show()
    
    def _on_theme_change_from_settings(self, new_theme: str):
        try:
            self.root.set_theme(new_theme)
            self.current_theme = new_theme
            logger.info(f"Theme changed to: {new_theme}")
        except Exception as e:
            logger.error(f"Failed to change theme to {new_theme}: {e}")
            raise e