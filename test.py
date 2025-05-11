import tkinter as tk
from tkinter import ttk
from tkinter import (
    messagebox,
)  # Keep messagebox for potential future use, though not directly fixing the display error


class DataDocApp:
    def __init__(self, master):
        self.master = master
        master.title("Data Documentation Assistant")
        master.geometry("500x450")  # Adjusted size for better layout
        master.configure(bg="#f3f4f6")  # Light gray background

        # Style configuration
        self.style = ttk.Style()
        # Check if a theme can be applied, otherwise it might raise errors in some environments
        try:
            self.style.theme_use("clam")  # A slightly more modern theme
        except tk.TclError:
            # Fallback if 'clam' theme is not available or causes issues
            # Default theme will be used
            print(
                "Warning: 'clam' theme not available or failed to apply. Using default theme."
            )

        self.style.configure("TFrame", background="#f3f4f6")
        self.style.configure("TLabel", background="#f3f4f6", font=("Inter", 10))
        self.style.configure("Header.TLabel", font=("Inter", 18, "bold"))
        self.style.configure("SubHeader.TLabel", font=("Inter", 10))
        self.style.configure("Error.TLabel", foreground="red", font=("Inter", 9))
        self.style.configure(
            "SelectedInfo.TLabel", font=("Inter", 9), foreground="#374151"
        )  # Gray text

        self.style.configure(
            "TCheckbutton", background="#f3f4f6", font=("Inter", 12), padding=5
        )
        self.style.map(
            "TCheckbutton",
            background=[("active", "#e5e7eb")],  # Lighter gray on hover
            indicatorcolor=[
                ("selected", "#3b82f6"),
                ("!selected", "white"),
            ],  # Blue tick, white box
            indicatormargin=[("!selected", 2), ("selected", 2)],
        )

        self.style.configure(
            "TButton", font=("Inter", 12, "bold"), padding=(10, 5), borderwidth=0
        )
        self.style.map(
            "TButton",
            background=[
                ("!disabled", "#3b82f6"),
                ("disabled", "#9ca3af"),
                ("active", "#2563eb"),
            ],
            foreground=[("!disabled", "white"), ("disabled", "#e5e7eb")],
            relief=[("pressed", "sunken"), ("!pressed", "raised")],
        )

        self.requests = []
        self.current_frame = None

        self.show_selection_page()

    def clear_frame(self):
        """Clears the current frame."""
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = ttk.Frame(self.master, padding="20 20 20 20")
        self.current_frame.pack(expand=True, fill=tk.BOTH)

    def show_selection_page(self):
        """Displays the item selection page."""
        self.clear_frame()
        self.master.title("Data Documentation Setup")

        # --- Main Container for Centering ---
        center_container = ttk.Frame(self.current_frame)
        center_container.pack(expand=True)

        # --- Title and Subtitle ---
        title_label = ttk.Label(
            center_container, text="Data Documentation Assistant", style="Header.TLabel"
        )
        title_label.pack(pady=(0, 5))

        subtitle_label = ttk.Label(
            center_container,
            text="Select the items you want to be documented.",
            style="SubHeader.TLabel",
        )
        subtitle_label.pack(pady=(0, 20))

        # --- Checkbox Variables ---
        self.measure_var = tk.BooleanVar()
        self.column_var = tk.BooleanVar()
        self.table_var = tk.BooleanVar()

        # --- Checkboxes ---
        # To make checkboxes look more like the HTML, we'll use a frame for each
        # and style them to have a border and background.

        # checkbox_frame_style = {"padding": 10, "borderwidth":1, "relief":"solid"} # This variable was defined but not used
        self.style.configure(
            "Checkbox.TFrame", background="#f8fafc", bordercolor="#d1d5db"
        )  # Light background, gray border

        # Measures Checkbox
        measure_frame = ttk.Frame(center_container, style="Checkbox.TFrame", padding=10)
        measure_frame.pack(fill=tk.X, pady=5)
        measure_check = ttk.Checkbutton(
            measure_frame,
            text="Measures",
            variable=self.measure_var,
            command=self.update_next_button_state,
        )
        measure_check.pack(side=tk.LEFT, padx=5)

        # Columns Checkbox
        column_frame = ttk.Frame(center_container, style="Checkbox.TFrame", padding=10)
        column_frame.pack(fill=tk.X, pady=5)
        column_check = ttk.Checkbutton(
            column_frame,
            text="Columns",
            variable=self.column_var,
            command=self.update_next_button_state,
        )
        column_check.pack(side=tk.LEFT, padx=5)

        # Tables Checkbox
        table_frame = ttk.Frame(center_container, style="Checkbox.TFrame", padding=10)
        table_frame.pack(fill=tk.X, pady=5)
        table_check = ttk.Checkbutton(
            table_frame,
            text="Tables",
            variable=self.table_var,
            command=self.update_next_button_state,
        )
        table_check.pack(side=tk.LEFT, padx=5)

        # --- Error Message Label ---
        self.error_label = ttk.Label(center_container, text="", style="Error.TLabel")
        self.error_label.pack(pady=(10, 0))

        # --- Next Button ---
        self.next_button = ttk.Button(
            center_container,
            text="Next",
            command=self.process_selections,
            state=tk.DISABLED,
        )
        self.next_button.pack(pady=(20, 0), fill=tk.X, ipady=5)

        self.update_next_button_state()  # Initial state check

    def update_next_button_state(self):
        """Enables or disables the Next button based on selections."""
        if (
            hasattr(self, "next_button") and self.next_button.winfo_exists()
        ):  # Check if button exists
            if self.measure_var.get() or self.column_var.get() or self.table_var.get():
                self.next_button.config(state=tk.NORMAL)
                if hasattr(self, "error_label") and self.error_label.winfo_exists():
                    self.error_label.config(text="")  # Clear error message
            else:
                self.next_button.config(state=tk.DISABLED)

    def process_selections(self):
        """Processes the selections and moves to the under construction page."""
        self.requests = []
        if self.measure_var.get():
            self.requests.append("measure description")
        if self.column_var.get():
            self.requests.append("column description")
        if self.table_var.get():
            self.requests.append("table description")

        if not self.requests:
            if hasattr(self, "error_label") and self.error_label.winfo_exists():
                self.error_label.config(text="Please select at least one item.")
            return

        print("Selected Requests:", self.requests)  # For debugging/logging
        self.show_under_construction_page()

    def show_under_construction_page(self):
        """Displays the under construction page."""
        self.clear_frame()
        self.master.title("Under Construction")

        # --- Main Container for Centering ---
        center_container = ttk.Frame(self.current_frame)
        center_container.pack(expand=True)

        # --- Icon (Placeholder - Tkinter doesn't have easy SVG support like HTML) ---
        # For simplicity, we'll use text or a simple character.
        # You could use a PIL/Pillow image if you want to include an actual icon.
        icon_label = ttk.Label(
            center_container, text="⚠️", font=("Inter", 48), foreground="#f59e0b"
        )  # Yellow warning
        icon_label.pack(pady=(0, 10))

        # --- Title ---
        title_label = ttk.Label(
            center_container, text="Under Construction!", style="Header.TLabel"
        )
        title_label.pack(pady=(10, 5))

        # --- Message ---
        message_label = ttk.Label(
            center_container,
            text="This section is currently being developed. Please check back later.",
            wraplength=300,
            justify=tk.CENTER,
            style="SubHeader.TLabel",
        )
        message_label.pack(pady=(0, 15))

        # --- Selected Items Info ---
        if self.requests:
            selected_text = "You selected: " + ", ".join(
                [r.replace(" description", "") for r in self.requests]
            )
        else:
            selected_text = "No items were selected."
        selected_info_label = ttk.Label(
            center_container, text=selected_text, style="SelectedInfo.TLabel"
        )
        selected_info_label.pack(pady=(0, 20))

        # --- Back Button ---
        back_button = ttk.Button(
            center_container, text="Back to Selection", command=self.show_selection_page
        )
        back_button.pack(pady=(10, 0), fill=tk.X, ipady=5)


if __name__ == "__main__":
    try:
        root = tk.Tk()
        # It's good practice to set a minsize for the window
        root.minsize(400, 350)
        app = DataDocApp(root)
        root.mainloop()
    except tk.TclError as e:
        # This error typically means there's no display server available
        # (e.g., running in a headless environment or $DISPLAY is not set)
        if "no display name" in str(e) or "couldn't connect to display" in str(e):
            print(
                "--------------------------------------------------------------------"
            )
            print("ERROR: Tkinter GUI could not be displayed.")
            print("This application requires a graphical environment (display server).")
            print("If you are running this in a headless environment (e.g., a server")
            print("without a monitor or via SSH without X11 forwarding), the GUI")
            print("cannot be shown.")
            print("Original error:", e)
            print(
                "--------------------------------------------------------------------"
            )
        else:
            # Re-raise other TclErrors that are not related to display
            raise
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        # Potentially log the full traceback here for debugging
        import traceback

        traceback.print_exc()
