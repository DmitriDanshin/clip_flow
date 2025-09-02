import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import List, Callable
from loguru import logger
from src.ports.ui_port import UIPort


class TkinterUIAdapter(UIPort):
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Clip Flow")
        self.root.geometry("400x600")
        self.root.configure(bg="white")

        self.history_listbox = None
        self.search_var = None
        self.search_entry = None

        self._copy_callback: Callable[[int], None] | None = None
        self._search_callback: Callable[[str], None] | None = None
        self._clear_callback: Callable[[], None] | None = None

        self._current_items: List[str] = []

        self._setup_ui()
        self._setup_window_close()
        logger.debug("TkinterUIAdapter initialized.")

    def show_history(self, items: List[str]) -> None:
        def update_ui():
            current_selection = self.history_listbox.curselection()
            self.history_listbox.delete(0, tk.END)
            self._current_items = items.copy()

            for item in items:
                preview = item.replace("\n", " ").replace("\r", " ")
                if len(preview) > 50:
                    preview = preview[:47] + "..."
                self.history_listbox.insert(tk.END, preview)

            if len(items) > 0 and not self.search_var.get() and not current_selection:
                self.history_listbox.selection_set(0)
                self.history_listbox.activate(0)
            elif current_selection and len(items) > 0:
                index = min(current_selection[0], len(items) - 1)
                self.history_listbox.selection_set(index)
                self.history_listbox.activate(index)

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

        self.history_listbox = tk.Listbox(
            listbox_frame,
            font=("Consolas", 10),
            bg="white",
            fg="black",
            selectbackground="#0078d4",
            selectforeground="white",
        )
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

    def _setup_window_close(self):
        def on_closing():
            logger.info("Window close event detected.")
            self.root.destroy()

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

        current = self.history_listbox.curselection()
        if current:
            index = current[0]
            if index > 0:
                self.history_listbox.selection_clear(0, tk.END)
                self.history_listbox.selection_set(index - 1)
                self.history_listbox.activate(index - 1)
                self.history_listbox.see(index - 1)
        return "break"

    def _navigate_down(self, event):
        if self.search_var.get():
            return "break"

        current = self.history_listbox.curselection()
        size = self.history_listbox.size()
        if current and size > 0:
            index = current[0]
            if index < size - 1:
                self.history_listbox.selection_clear(0, tk.END)
                self.history_listbox.selection_set(index + 1)
                self.history_listbox.activate(index + 1)
                self.history_listbox.see(index + 1)
        return "break"

    def _on_double_click(self, event=None):
        self._copy_selected()

    def _copy_selected(self, event=None):
        selection = self.history_listbox.curselection()
        if not selection:
            self.show_message("Please select an item to copy.", "warning")
            return

        if self._copy_callback:
            self._copy_callback(selection[0])

    def _view_full_text(self):
        selection = self.history_listbox.curselection()
        if not selection:
            self.show_message("Please select an item to view.", "warning")
            return

        index = selection[0]
        if index >= len(self._current_items):
            return

        item = self._current_items[index]

        popup = tk.Toplevel(self.root)
        popup.title("Full Text")
        popup.geometry("500x400")
        popup.configure(bg="white")

        frame = ttk.Frame(popup, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        text_widget = scrolledtext.ScrolledText(
            frame, wrap=tk.WORD, font=("Consolas", 10), bg="white", fg="black"
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
