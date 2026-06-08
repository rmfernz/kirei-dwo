import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
from datetime import datetime, timedelta
import calendar
import json
import os
import ctypes
from typing import Dict, Optional

from PIL import Image, ImageTk


class ProductivityApp(tk.Tk):

    # --- kirei version 1.1.0
    # --- inspired by rico's notion dashboard
    # --- AI-assisted, human-programmed
    # --- Features: Notebooks, Weekly Tracker, Calendar, Schedule Grid, To-Do List, Clock, Import/Export, Autosave

    # ==========================================================
    #    1. Config and Initialization
    # ==========================================================

    def __init__(self):
        super().__init__()

        self.title("kirei")
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self._configure_window_geometry()
        self._force_dark_title_bar()

        self.BG_ROOT = '#1E1E1E'
        self.BG_CARD = '#282828'
        self.BG_ACCENT = '#3A3A3A'
        self.FG_LIGHT = '#F8F8F8'
        self.ACCENT_COLOR = '#5C6BC0'
        self.configure(bg=self.BG_ROOT)

        self._init_data_structures()
        self._init_styles()
        self.load_data()
        self._setup_main_layout()
        self._setup_global_keybindings()
        self.show_home_view()
        self.update_clock()
        self._autosave()

    def _configure_window_geometry(self):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.geometry(f"{int(screen_width * 0.8)}x{int(screen_height * 0.8)}")
        self.state('zoomed')

    def _force_dark_title_bar(self):
        try:
            self.update()
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            value = ctypes.c_int(2)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(value), ctypes.sizeof(value))
        except Exception:
            pass

    def _init_data_structures(self):
        self.notebooks: Dict[int, Dict] = {}
        self.active_notebook_id: Optional[int] = None
        self.note_images_cache = []

        self.nb_view_year = datetime.now().year
        self.nb_view_month = datetime.now().month
        self.nb_selected_date = datetime.now().strftime("%Y-%m-%d")

        self.weekly_todos = {day: [] for day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']}
        self.calendar_tasks = {}
        self.schedule_grid_vars = []

        self.header_image_path = ""
        self.header_image_frame = None
        self.header_photo_image = None
        self.profile_image_path = ""
        self.profile_photo_image = None
        self.user_quote_var = tk.StringVar(value="Type a quote or name here...")

    def _init_styles(self):
        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        self.style.configure('DarkFrame.TFrame', background=self.BG_ROOT)
        self.style.configure('DarkLabel.TLabel', background=self.BG_ROOT, foreground=self.FG_LIGHT)
        self.style.configure('DarkCard.TFrame', background=self.BG_CARD)
        self.style.configure('DarkGridContainer.TFrame', background=self.BG_ACCENT)
        self.style.configure('DarkHeading.TLabel', background=self.BG_ACCENT, foreground=self.FG_LIGHT)

        self.style.configure('DarkEntry.TEntry', fieldbackground=self.BG_CARD, foreground=self.FG_LIGHT,
                             bordercolor=self.BG_ACCENT)
        self.style.configure('QuoteEntry.TEntry', fieldbackground=self.BG_ROOT, foreground='#AAAAAA',
                             bordercolor=self.BG_ROOT, lightcolor=self.BG_ROOT, darkcolor=self.BG_ROOT, borderwidth=0)

        self.style.configure('Sidebar.TButton', background=self.BG_ROOT, foreground=self.FG_LIGHT, padding=[10, 5],
                             font=('Arial', 10), relief='flat')
        self.style.map('Sidebar.TButton', background=[('active', self.BG_ACCENT)], foreground=[('active', '#FFFFFF')])

        self.style.configure('Active.Sidebar.TButton', background=self.ACCENT_COLOR, foreground='#FFFFFF',
                             font=('Arial', 10, 'bold'), relief='flat')
        self.style.map('Active.Sidebar.TButton', background=[('active', self.BG_ACCENT)])

        self.style.configure('Action.TButton', background=self.ACCENT_COLOR, foreground='#FFFFFF', padding=[10, 5],
                             font=('Arial', 10, 'bold'), relief='flat')
        self.style.map('Action.TButton', background=[('active', '#4856A3')])

        self.style.configure('Square.Action.TButton', background=self.ACCENT_COLOR, foreground='#FFFFFF',
                             padding=[0, 2], font=('Arial', 12, 'bold'), anchor='center', relief='flat')
        self.style.map('Square.Action.TButton', background=[('active', '#4856A3')])

    # ==========================================================
    #    2. Persistence
    # ==========================================================

    def _autosave(self):
        self.save_data()
        self.after(300000, self._autosave)  # every 5 minutes

    def save_data(self):
        self._save_current_notebook_content()
        schedule_data = [[var.get() for var in row] for row in self.schedule_grid_vars]
        data = {
            "notebooks": self.notebooks,
            "weekly_todos": self.weekly_todos,
            "calendar_tasks": self.calendar_tasks,
            "schedule_grid": schedule_data,
            "profile_image_path": self.profile_image_path,
            "header_image_path": self.header_image_path,
            "quote": self.user_quote_var.get()
        }
        try:
            with open("kikai_data.json", "w", encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Failed to save data: {e}")

    def load_data(self):
        default_schedule_needed = True
        if os.path.exists("kikai_data.json"):
            try:
                with open("kikai_data.json", "r", encoding='utf-8') as f:
                    data = json.load(f)
                self.notebooks = {int(k): v for k, v in data.get("notebooks", {}).items()}
                self.weekly_todos = data.get("weekly_todos", self.weekly_todos)
                self.calendar_tasks = data.get("calendar_tasks", {})
                self.profile_image_path = data.get("profile_image_path", "")
                self.header_image_path = data.get("header_image_path", "")
                self.user_quote_var.set(data.get("quote", "Type a quote or name here..."))
                saved_schedule = data.get("schedule_grid", [])
                if saved_schedule:
                    self.schedule_grid_vars = [[tk.StringVar(value=val) for val in row] for row in saved_schedule]
                    default_schedule_needed = False
            except Exception as e:
                print(f"Error loading data: {e}")
        if default_schedule_needed:
            self._initialize_default_schedule()

    def _initialize_default_schedule(self):
        times = [
            "7:00 AM - 8:10 AM", "8:10 AM - 9:20 AM", "9:20 AM - 10:30 AM",
            "10:30 AM - 11:40 AM", "11:40 AM - 12:50 PM", "12:50 PM - 2:00 PM",
            "2:00 PM - 3:10 PM", "3:10 PM - 4:20 PM", "4:20 PM - 5:30 PM"
        ]
        self.schedule_grid_vars = [[tk.StringVar(self) for _ in range(8)] for _ in range(9)]
        for i, time_str in enumerate(times):
            self.schedule_grid_vars[i][0].set(time_str)

    def import_data_from_file(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json"), ("All files", "*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.notebooks = {int(k): v for k, v in data.get("notebooks", {}).items()}
            self.weekly_todos = data.get("weekly_todos", {day: [] for day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']})
            self.calendar_tasks = data.get("calendar_tasks", {})
            self.profile_image_path = data.get("profile_image_path", "")
            self.header_image_path = data.get("header_image_path", "")
            self.user_quote_var.set(data.get("quote", "Type a quote or name here..."))
            saved_schedule = data.get("schedule_grid", [])
            if saved_schedule:
                self.schedule_grid_vars = [[tk.StringVar(value=val) for val in row] for row in saved_schedule]
            else:
                self._initialize_default_schedule()
            self.show_home_view()
            self._draw_schedule_grid()
            self.update_personal_header()
            self.update_profile_picture()
            self._show_notification_popup("Data imported successfully!")
        except Exception as e:
            self._show_notification_popup(f"Import failed: {e}", is_error=True)

    def export_data_to_file(self):
        self._save_current_notebook_content()
        path = filedialog.asksaveasfilename(initialfile="kikai_backup", defaultextension=".json",
                                            filetypes=[("JSON", "*.json"), ("All files", "*.*")])
        if path:
            try:
                schedule_data = [[var.get() for var in row] for row in self.schedule_grid_vars]
                data = {
                    "notebooks": self.notebooks,
                    "weekly_todos": self.weekly_todos,
                    "calendar_tasks": self.calendar_tasks,
                    "schedule_grid": schedule_data,
                    "profile_image_path": self.profile_image_path,
                    "header_image_path": self.header_image_path,
                    "quote": self.user_quote_var.get()
                }
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
                self._show_notification_popup("Exported successfully!")
            except Exception as e:
                self._show_notification_popup(f"Export failed: {e}", is_error=True)

    def on_close(self):
        self.save_data()
        self.destroy()

    # ==========================================================
    #    3. Main Layout and Navigation
    # ==========================================================

    def _setup_main_layout(self):
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.top_bar = ttk.Frame(self, style='DarkFrame.TFrame', height=60)
        self.top_bar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(15, 0))
        ttk.Label(self.top_bar, text="kirei", font=('Arial', 18, 'bold'),
                  style='DarkLabel.TLabel', foreground=self.FG_LIGHT).pack(side='left')

        self.sidebar = ttk.Frame(self, width=200, relief='flat', style='DarkFrame.TFrame')
        self.sidebar.grid(row=1, column=0, sticky="ns", pady=(20, 0))

        self.main_container = ttk.Frame(self, padding="20 20 20 20", style='DarkFrame.TFrame')
        self.main_container.grid(row=1, column=1, sticky="nsew")

        self.canvas = tk.Canvas(self.main_container, highlightthickness=0, bg=self.BG_ROOT)
        self.canvas.pack(side="left", fill="both", expand=True)

        self.content_frame = ttk.Frame(self.canvas, style='DarkFrame.TFrame')
        self.canvas_window = self.canvas.create_window((0, 0), window=self.content_frame, anchor="nw", width=950)

        self.canvas.bind('<Configure>', self._on_canvas_configure)
        self.content_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self.due_tasks_frame = ttk.Frame(self.sidebar, style='DarkFrame.TFrame')
        self.home_view_frame = ttk.Frame(self.content_frame, style='DarkFrame.TFrame')
        self.dedicated_notebook_frame = ttk.Frame(self.content_frame, style='DarkFrame.TFrame')

        self.setup_sidebar()
        self.setup_home_view_content()
        self.setup_dedicated_notebook_editor()

    def show_home_view(self):
        self._save_current_notebook_content()
        self.dedicated_notebook_frame.pack_forget()
        self.home_view_frame.pack(fill='both', expand=True)
        self.active_notebook_id = None
        self.update_sidebar_list()
        self.update_notebook_grid()
        self.update_personal_header()
        self.update_weekly_due_tasks_sidebar()

    def show_notebook_view(self, nb_id):
        self._save_current_notebook_content()
        self.home_view_frame.pack_forget()
        self.dedicated_notebook_frame.pack(fill='both', expand=True)
        self.active_notebook_id = nb_id
        now = datetime.now()
        self.nb_view_year = now.year
        self.nb_view_month = now.month
        self.nb_selected_date = now.strftime("%Y-%m-%d")
        self.update_notebook_editor_view()
        self.update_sidebar_list()

    # ==========================================================
    #    4. Sidebar
    # ==========================================================

    def setup_sidebar(self):
        clock_frame = ttk.Frame(self.sidebar, style='DarkFrame.TFrame', padding="10 5")
        clock_frame.pack(fill='x')
        self.time_label = ttk.Label(clock_frame, text="00:00:00 PM", font=('Arial', 14),
                                    style='DarkLabel.TLabel', foreground=self.ACCENT_COLOR)
        self.time_label.pack(fill='x', anchor='center')
        self.date_label = ttk.Label(clock_frame, text="Day, Month 00", font=('Arial', 9),
                                    style='DarkLabel.TLabel', foreground='#AAAAAA')
        self.date_label.pack(fill='x', anchor='center', pady=(0, 10))

        self.due_tasks_frame.pack(fill='x', pady=(10, 5))
        self.update_weekly_due_tasks_sidebar()

        ttk.Label(self.sidebar, text="▼ Notebooks", font=('Arial', 10, 'bold'),
                  padding="10 5 10 5", style='DarkLabel.TLabel').pack(fill='x', pady=(20, 5))

        self.notebook_list_frame = ttk.Frame(self.sidebar, style='DarkFrame.TFrame')
        self.notebook_list_frame.pack(fill='both', expand=True, padx=5)

        ttk.Button(self.sidebar, text="📥 Import Data", command=self.import_data_from_file,
                   style='Sidebar.TButton').pack(pady=(10, 2), padx=10, fill='x')
        ttk.Button(self.sidebar, text="📤 Export Data", command=self.export_data_to_file,
                   style='Sidebar.TButton').pack(pady=(2, 10), padx=10, fill='x')
        self.update_sidebar_list()

    def update_clock(self):
        if hasattr(self, 'time_label') and self.time_label.winfo_exists():
            now = datetime.now()
            self.time_label.config(text=now.strftime("%I:%M:%S %p"))
            self.date_label.config(text=now.strftime("%a, %b %d"))
        self.after(1000, self.update_clock)

    def update_sidebar_list(self):
        for widget in self.notebook_list_frame.winfo_children():
            widget.destroy()
        for nb_id, nb_data in self.notebooks.items():
            style_name = 'Active.Sidebar.TButton' if nb_id == self.active_notebook_id else 'Sidebar.TButton'
            ttk.Button(self.notebook_list_frame, text=nb_data['title'],
                       command=lambda id=nb_id: self.show_notebook_view(id),
                       style=style_name).pack(fill='x', padx=5, pady=2)

    def update_weekly_due_tasks_sidebar(self):
        for widget in self.due_tasks_frame.winfo_children():
            widget.destroy()

        combined_tasks = []
        for date_key in self._get_current_week_dates():
            for task in self.get_all_tasks_for_date(date_key):
                if not task.get('done', False):
                    date_obj = datetime.strptime(date_key, "%Y-%m-%d").date()
                    priority_val = self.get_priority_value(task.get('priority', 'Low'))
                    source_label = "Cal" if task['source_type'] == 'calendar' else "NB"
                    combined_tasks.append((date_obj, priority_val, task, source_label))

        combined_tasks.sort(key=lambda x: (x[0], x[1]))

        ttk.Label(self.due_tasks_frame, text="▼ This Week's Tasks", font=('Arial', 10, 'bold'),
                  padding="10 5 10 5", style='DarkLabel.TLabel').pack(fill='x', pady=(0, 5))

        if not combined_tasks:
            ttk.Label(self.due_tasks_frame, text="No active tasks this week.", font=('Arial', 9),
                      padding="10 0 10 5", foreground='#AAAAAA', style='DarkFrame.TFrame').pack(fill='x')
            return

        for date_obj, _, task, source in combined_tasks[:10]:
            priority_color = self._get_priority_color(task.get('priority', 'Low'))
            display_text = f"{date_obj.strftime('%a')}: {task['text']}"
            if len(display_text) > 25:
                display_text = display_text[:25] + "..."
            frame = ttk.Frame(self.due_tasks_frame, style='DarkFrame.TFrame')
            frame.pack(fill='x', padx=10, pady=1)
            ttk.Label(frame, text="•", style='DarkLabel.TLabel', foreground=priority_color,
                      font=('Arial', 12, 'bold')).pack(side='left', padx=(0, 5))
            ttk.Label(frame, text=display_text, style='DarkLabel.TLabel', font=('Arial', 9)).pack(side='left', fill='x')
            if source == "NB":
                ttk.Label(frame, text="📓", font=('Arial', 8), style='DarkLabel.TLabel').pack(side='right')

        if len(combined_tasks) > 10:
            ttk.Label(self.due_tasks_frame, text=f"+ {len(combined_tasks) - 10} more...",
                      font=('Arial', 8, 'italic'), foreground='#AAAAAA',
                      style='DarkFrame.TFrame').pack(fill='x', padx=10)

    # ==========================================================
    #    5. Home Dashboard
    # ==========================================================

    def setup_home_view_content(self):
        self.setup_personal_header(self.home_view_frame)
        self.setup_profile_picture(self.home_view_frame)
        self.setup_quote_section()

        self.dashboard_container = ttk.Frame(self.home_view_frame, style='DarkFrame.TFrame')
        self.dashboard_container.pack(fill='both', expand=True, pady=(0, 20))
        self.dashboard_container.grid_columnconfigure(0, weight=2)
        self.dashboard_container.grid_columnconfigure(1, weight=1)

        self.left_col_frame = ttk.Frame(self.dashboard_container, style='DarkFrame.TFrame', padding=(0, 0, 20, 0))
        self.left_col_frame.grid(row=0, column=0, sticky='nsew')

        self.notebook_grid_frame = ttk.Frame(self.left_col_frame, style='DarkFrame.TFrame')
        self.notebook_grid_frame.pack(fill='x', pady=(0, 30))
        header_row = ttk.Frame(self.notebook_grid_frame, style='DarkFrame.TFrame')
        header_row.pack(fill='x', pady=(0, 15))
        ttk.Label(header_row, text="Notebooks", font=('Arial', 16, 'bold'), style='DarkLabel.TLabel').pack(side='left')
        ttk.Button(header_row, text="+", command=self.add_notebook, width=3,
                   style='Square.Action.TButton').pack(side='left', padx=15)
        self.notebook_cards_frame = ttk.Frame(self.notebook_grid_frame, style='DarkFrame.TFrame')
        self.notebook_cards_frame.pack(fill='x')
        self.update_notebook_grid()

        self.setup_schedule_grid(self.left_col_frame)

        self.right_col_frame = ttk.Frame(self.dashboard_container, style='DarkFrame.TFrame')
        self.right_col_frame.grid(row=0, column=1, sticky='nsew', padx=(20, 120))
        self.setup_calendar(self.right_col_frame)
        self.setup_weekly_tracker(self.right_col_frame)

    def setup_personal_header(self, parent_frame):
        self.header_image_frame = ttk.Frame(parent_frame, style='DarkFrame.TFrame')
        self.header_image_frame.pack(fill='x', pady=(0, 110))
        self.image_display_control_frame = ttk.Frame(self.header_image_frame, style='DarkCard.TFrame', height=220)
        self.image_display_control_frame.pack(fill='x')
        self.image_display_control_frame.pack_propagate(False)
        self.image_display_control_frame.bind('<Configure>', self._on_header_resize)
        self.update_personal_header()

    def _on_header_resize(self, event):
        if hasattr(self, '_header_timer'):
            self.after_cancel(self._header_timer)
        self._header_timer = self.after(100, self.update_personal_header)

    def update_personal_header(self):
        if not self.header_image_frame:
            return
        for w in self.image_display_control_frame.winfo_children():
            w.destroy()
        inner = tk.Frame(self.image_display_control_frame, bg=self.BG_CARD)
        inner.pack(fill='both', expand=True)
        if self.header_image_path:
            self._display_resized_image(self.header_image_path, inner, self.image_display_control_frame, is_header=True)
        else:
            lbl = ttk.Label(inner, text="Click to Upload Header", font=('Arial', 14, 'bold'),
                            background=self.BG_ACCENT, foreground='#FFF', anchor='center')
            lbl.pack(expand=True, fill='both')
            lbl.bind("<Button-1>", lambda e: self.upload_header_image())

    def setup_profile_picture(self, parent_frame):
        SIZE = 200
        self.profile_display_frame = tk.Frame(parent_frame, bg=self.BG_CARD, bd=0, relief='flat',
                                              width=SIZE, height=SIZE)
        self.profile_display_frame.place(x=50, y=100)
        self.profile_display_frame.lift()
        self.profile_display_frame.pack_propagate(False)
        self.update_profile_picture()

    def update_profile_picture(self):
        if not self.profile_display_frame:
            return
        for w in self.profile_display_frame.winfo_children():
            w.destroy()
        inner = tk.Frame(self.profile_display_frame, bg=self.BG_CARD)
        inner.pack(fill='both', expand=True)
        inner.bind("<Button-1>", lambda e: self.upload_profile_image())
        inner.bind("<Button-3>", self.show_profile_context_menu)
        if self.profile_image_path:
            self._display_resized_image(self.profile_image_path, inner, self.profile_display_frame, is_profile=True)
        else:
            lbl = ttk.Label(inner, text="👤", font=('Arial', 36), background=self.BG_ACCENT,
                            foreground='#FFF', anchor='center')
            lbl.pack(expand=True, fill='both')
            lbl.bind("<Button-1>", lambda e: self.upload_profile_image())
            lbl.bind("<Button-3>", self.show_profile_context_menu)

    def _display_resized_image(self, path, parent_widget, sizing_widget, is_header=False, is_profile=False):
        try:
            W = sizing_widget.winfo_width()
            H = sizing_widget.winfo_height()
            if W < 50: W = self.winfo_screenwidth() if is_header else 200
            if H < 50: H = 220 if is_header else 200

            img = Image.open(path)
            if is_profile:
                ratio = max(W / img.width, H / img.height)
                img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.Resampling.LANCZOS)
                x, y = img.width // 2, img.height // 2
                img = img.crop((x - W // 2, y - H // 2, x + W // 2, y + H // 2))
            else:
                img_ratio = img.width / img.height
                frame_ratio = W / H
                if frame_ratio > img_ratio:
                    new_w, new_h = W, int(W / img_ratio)
                else:
                    new_h, new_w = H, int(H * img_ratio)
                img = img.resize((int(new_w), int(new_h)), Image.Resampling.LANCZOS)
                x, y = (new_w - W) // 2, (new_h - H) // 2
                img = img.crop((x, y, x + W, y + H))

            photo = ImageTk.PhotoImage(img)
            lbl = tk.Label(parent_widget, image=photo, bg=self.BG_ACCENT if is_header else self.BG_CARD)
            lbl.image = photo
            if is_header: self.header_photo_image = photo
            if is_profile: self.profile_photo_image = photo
            lbl.pack(expand=True, fill='both')
            if is_header:
                lbl.bind("<Button-1>", lambda e: self.upload_header_image())
            if is_profile:
                lbl.bind("<Button-1>", lambda e: self.upload_profile_image())
                lbl.bind("<Button-3>", self.show_profile_context_menu)
        except Exception:
            if is_header: self.header_image_path = ""
            if is_profile: self.profile_image_path = ""

    def upload_header_image(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg")])
        if path:
            self.header_image_path = path
            self.update_personal_header()

    def upload_profile_image(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg")])
        if path:
            self.profile_image_path = path
            self.update_profile_picture()

    def show_profile_context_menu(self, event):
        menu = tk.Menu(self, tearoff=0, bg=self.BG_ACCENT, fg=self.FG_LIGHT)
        if self.profile_image_path:
            menu.add_command(label="Remove Profile Picture", command=self.remove_profile_image)
        else:
            menu.add_command(label="Upload Profile Picture", command=self.upload_profile_image)
        menu.tk_popup(event.x_root, event.y_root)

    def remove_profile_image(self):
        self.profile_image_path = ""
        self.profile_photo_image = None
        self.update_profile_picture()

    def setup_quote_section(self):
        quote_frame = ttk.Frame(self.home_view_frame, style='DarkFrame.TFrame')
        quote_frame.pack(fill='x', pady=(0, 30))
        ttk.Entry(quote_frame, textvariable=self.user_quote_var, font=('Arial', 36, 'italic', 'bold'),
                  style='QuoteEntry.TEntry').pack(fill='x')

    def update_notebook_grid(self):
        for w in self.notebook_cards_frame.winfo_children():
            w.destroy()
        for i, (nb_id, nb_data) in enumerate(self.notebooks.items()):
            col, row = i % 6, i // 6
            self._create_notebook_card(self.notebook_cards_frame, nb_data['title'], col,
                                       lambda id=nb_id: self.show_notebook_view(id), nb_id, row)

    def _create_notebook_card(self, parent, title, col, command, nb_id, row):
        thumb = self.notebooks.get(nb_id, {}).get('thumbnail_path', '')
        if thumb:
            container = ttk.Frame(parent, width=120, height=100, style='DarkCard.TFrame')
            container.pack_propagate(False)
            container.grid(row=row, column=col, padx=5, pady=5)
            btn = tk.Button(container, command=command, bg=self.BG_CARD, activebackground=self.BG_ACCENT, bd=0)
            btn.pack(fill='both', expand=True)
            try:
                img = Image.open(thumb)
                scale = max(120 / img.width, 75 / img.height)
                img = img.resize((int(img.width * scale), int(img.height * scale)), Image.Resampling.LANCZOS)
                x, y = img.width // 2, img.height // 2
                img = img.crop((x - 60, y - 37, x + 60, y + 38))
                btn.photo = ImageTk.PhotoImage(img)
                btn.config(image=btn.photo, text=title, compound='top', fg=self.FG_LIGHT, font=('Arial', 9, 'bold'))
            except Exception:
                btn.config(text=title, fg=self.FG_LIGHT)
            btn.bind("<Button-3>", lambda e: self._show_nb_context(e, nb_id, title))
        else:
            btn = tk.Button(parent, text=title, command=command, bg=self.BG_CARD, fg=self.FG_LIGHT,
                            width=12, height=5, relief='flat', font=('Arial', 12, 'bold'), wraplength=100)
            btn.grid(row=row, column=col, padx=5, pady=5)
            btn.bind("<Enter>", lambda e: btn.config(bg=self.BG_ACCENT))
            btn.bind("<Leave>", lambda e: btn.config(bg=self.BG_CARD))
            btn.bind("<Button-3>", lambda e: self._show_nb_context(e, nb_id, title))

    def _show_nb_context(self, event, nb_id, title):
        m = tk.Menu(self, tearoff=0, bg=self.BG_ACCENT, fg='#FFF')
        m.add_command(label="Open", command=lambda: self.show_notebook_view(nb_id))
        m.add_command(label="Rename", command=lambda: self.rename_notebook(nb_id))
        m.add_command(label="Change Thumbnail", command=lambda: self.change_notebook_thumbnail(nb_id))
        m.add_command(label="Remove Thumbnail", command=lambda: self.remove_notebook_thumbnail(nb_id))
        m.add_separator()
        m.add_command(label="Delete", command=lambda: self.delete_notebook(nb_id))
        m.tk_popup(event.x_root, event.y_root)

    # ==========================================================
    #    Schedule Grid
    # ==========================================================

    def setup_schedule_grid(self, parent):
        ttk.Label(parent, text="Schedule", font=('Arial', 16, 'bold', 'italic'),
                  style='DarkLabel.TLabel').pack(anchor='w', pady=(0, 15))
        f = ttk.Frame(parent, style='DarkFrame.TFrame')
        f.pack(fill='x', pady=(0, 40))
        self.schedule_grid_frame = ttk.Frame(f, style='DarkGridContainer.TFrame')
        self.schedule_grid_frame.pack(side='top', anchor='w')
        btns = ttk.Frame(f, style='DarkFrame.TFrame')
        btns.pack(side='top', fill='x', pady=5)
        ttk.Button(btns, text="+ Row", command=self.add_schedule_row, style='Action.TButton').pack(side='left', padx=(0, 5))
        ttk.Button(btns, text="- Row", command=self.remove_schedule_row, style='Action.TButton').pack(side='left')
        self._draw_schedule_grid()

    def _draw_schedule_grid(self):
        for w in self.schedule_grid_frame.winfo_children():
            w.destroy()
        for c, h in enumerate(['Time', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']):
            ttk.Label(self.schedule_grid_frame, text=h, background=self.BG_ACCENT, foreground='#FFF',
                      width=10, anchor='center').grid(row=0, column=c, sticky='nsew', padx=1, pady=1)
        for r in range(len(self.schedule_grid_vars)):
            for c in range(8):
                if c == 0:
                    ttk.Entry(self.schedule_grid_frame, textvariable=self.schedule_grid_vars[r][c],
                              style='DarkEntry.TEntry', width=20, justify='center').grid(
                                  row=r + 1, column=c, sticky='nsew', padx=1, pady=1)
                else:
                    t = tk.Text(self.schedule_grid_frame, height=5, width=12, bg=self.BG_CARD, fg=self.FG_LIGHT, bd=0)
                    t.grid(row=r + 1, column=c, sticky='nsew', padx=1, pady=1)
                    t.insert('1.0', self.schedule_grid_vars[r][c].get())
                    t.bind('<FocusOut>', lambda e, rr=r, cc=c: self.schedule_grid_vars[rr][cc].set(e.widget.get('1.0', 'end-1c')))

    def add_schedule_row(self):
        v = [tk.StringVar() for _ in range(8)]
        v[0].set(f"Time {len(self.schedule_grid_vars) + 1}")
        self.schedule_grid_vars.append(v)
        self._draw_schedule_grid()

    def remove_schedule_row(self):
        if len(self.schedule_grid_vars) > 1:
            self.schedule_grid_vars.pop()
            self._draw_schedule_grid()

    # ==========================================================
    #    Weekly Tracker
    # ==========================================================

    def setup_weekly_tracker(self, parent):
        ttk.Label(parent, text="To-Do-List", font=('Arial', 16, 'bold', 'italic'),
                  style='DarkLabel.TLabel').pack(anchor='w', pady=(0, 15))
        cont = ttk.Frame(parent, style='DarkFrame.TFrame')
        cont.pack(fill='both', expand=True, pady=10)
        cont.grid_columnconfigure(0, weight=1)
        cont.grid_columnconfigure(1, weight=1)

        daily = ttk.Frame(cont, style='DarkFrame.TFrame')
        daily.pack(fill='both', expand=True)

        self.day_widgets = {}
        for i, d in enumerate(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']):
            r, c = i // 2, i % 2
            f = ttk.Frame(daily, style='DarkCard.TFrame', padding=5)
            f.grid(row=r, column=c, sticky='nsew', padx=2, pady=2)
            daily.grid_columnconfigure(c, weight=1)
            ttk.Label(f, text=f"▼ {d}", font=('Arial', 10, 'bold'), style='DarkLabel.TLabel',
                      background=self.BG_ACCENT).pack(fill='x')
            list_f = ttk.Frame(f, style='DarkCard.TFrame')
            list_f.pack(fill='both', expand=True)
            entry = ttk.Entry(f, style='DarkEntry.TEntry')
            entry.pack(fill='x')
            entry.bind('<Return>', lambda e, day=d, ent=entry: self.add_todo(day, ent))
            self.day_widgets[d] = {'container': list_f}

        self.update_weekly_tracker()

    def add_todo(self, day, entry):
        if entry.get().strip():
            self.weekly_todos[day].append({'text': entry.get().strip(), 'done': False})
            entry.delete(0, tk.END)
            self.update_weekly_tracker()

    def update_weekly_tracker(self):
        for d, w in self.day_widgets.items():
            for c in w['container'].winfo_children():
                c.destroy()
            for i, todo in enumerate(self.weekly_todos[d]):
                var = tk.BooleanVar(value=todo['done'])
                def tog(dy=d, idx=i, v=var): self.weekly_todos[dy][idx]['done'] = v.get()
                cb = tk.Checkbutton(w['container'], text=todo['text'], variable=var, command=tog,
                                    bg=self.BG_CARD, fg=self.FG_LIGHT, selectcolor=self.BG_CARD,
                                    activebackground=self.BG_CARD, activeforeground=self.FG_LIGHT,
                                    bd=0, wraplength=120, justify='left', anchor='w')
                cb.pack(fill='x')
                cb.bind("<Button-3>", lambda e, dy=d, idx=i: self._del_todo(e, dy, idx))

    def _del_todo(self, e, day, idx):
        m = tk.Menu(self, tearoff=0, bg=self.BG_ACCENT, fg='#FFF')
        m.add_command(label="Delete", command=lambda: [self.weekly_todos[day].pop(idx), self.update_weekly_tracker()])
        m.tk_popup(e.x_root, e.y_root)

    # ==========================================================
    #    Calendar
    # ==========================================================

    def setup_calendar(self, parent):
        ttk.Label(parent, text="Calendar", font=('Arial', 16, 'bold', 'italic'),
                  style='DarkLabel.TLabel').pack(anchor='w', pady=(0, 15))
        nav = ttk.Frame(parent, style='DarkFrame.TFrame')
        nav.pack(fill='x')
        self.month_label = ttk.Label(nav, font=('Arial', 14, 'bold'), style='DarkLabel.TLabel', background=self.BG_ROOT)
        self.month_label.pack(side='left')
        ttk.Button(nav, text=">", command=lambda: self.change_month(1), style='Sidebar.TButton').pack(side='right')
        ttk.Button(nav, text="<", command=lambda: self.change_month(-1), style='Sidebar.TButton').pack(side='right')
        self.cal_grid_frame = ttk.Frame(parent, style='DarkGridContainer.TFrame')
        self.cal_grid_frame.pack(fill='x', pady=5)
        now = datetime.now()
        self.current_year, self.current_month = now.year, now.month
        self.update_calendar_view()

    def change_month(self, d):
        self.current_month += d
        if self.current_month > 12:
            self.current_month = 1
            self.current_year += 1
        elif self.current_month < 1:
            self.current_month = 12
            self.current_year -= 1
        self.update_calendar_view()
        self.update_weekly_due_tasks_sidebar()

    def update_calendar_view(self):
        for w in self.cal_grid_frame.winfo_children():
            w.destroy()
        self.month_label.config(text=f"{calendar.month_name[self.current_month]} {self.current_year}")
        for i, d in enumerate(calendar.day_abbr):
            ttk.Label(self.cal_grid_frame, text=d, background=self.BG_ACCENT, foreground='#FFF',
                      anchor='center').grid(row=0, column=i, sticky='nsew', padx=1, pady=1)
            self.cal_grid_frame.grid_columnconfigure(i, weight=1)
        now = datetime.now()
        for i, week in enumerate(calendar.monthcalendar(self.current_year, self.current_month)):
            for j, day in enumerate(week):
                f = tk.Frame(self.cal_grid_frame, height=80, bg=self.BG_CARD)
                f.grid_propagate(False)
                f.grid(row=i + 1, column=j, sticky='nsew', padx=1, pady=1)
                if day != 0:
                    is_today = (day == now.day and self.current_month == now.month and self.current_year == now.year)
                    bg, fg = (self.ACCENT_COLOR, '#FFF') if is_today else (self.BG_CARD, self.FG_LIGHT)
                    btn = tk.Button(f, text=str(day), bg=bg, fg=fg, relief='flat', bd=0,
                                    activebackground=self.BG_ACCENT, font=('Arial', 10, 'bold'), anchor='nw',
                                    command=lambda d=day: self.manage_day_tasks(d))
                    btn.pack(side='top', fill='x')
                    d_str = self.get_date_string(day)
                    active = [t for t in self.get_all_tasks_for_date(d_str) if not t.get('done')]
                    if active:
                        p_val = max(self.get_priority_value(t.get('priority', 'Low')) for t in active)
                        color = {1: '#81C784', 2: '#FFB300', 3: '#E57373'}.get(p_val, '#FFF')
                        tk.Label(f, text=f"• {len(active)}", font=('Arial', 8, 'bold'),
                                 bg=self.BG_CARD, fg=color, anchor='nw').pack(fill='x', padx=2)

    def _refresh_calendar_ui(self, refresh_fn):
        """Helper to refresh calendar popup, calendar view, and sidebar together."""
        refresh_fn()
        self.update_calendar_view()
        self.update_weekly_due_tasks_sidebar()

    def manage_day_tasks(self, day):
        d_str = self.get_date_string(day)
        if d_str not in self.calendar_tasks:
            self.calendar_tasks[d_str] = []

        popup = tk.Toplevel(self, bg=self.BG_ROOT)
        popup.title(f"Tasks: {d_str}")
        popup.geometry(f"800x700+{self.winfo_x() + 100}+{self.winfo_y() + 50}")

        cont = ttk.Frame(popup, style='DarkFrame.TFrame', padding=15)
        cont.pack(fill='both', expand=True)

        cv = tk.Canvas(cont, bg=self.BG_CARD, highlightthickness=0)
        cv.pack(side='left', fill='both', expand=True)
        list_f = ttk.Frame(cv, style='DarkCard.TFrame')
        cv.create_window((0, 0), window=list_f, anchor='nw', width=750)
        list_f.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))

        def refresh():
            for w in list_f.winfo_children():
                w.destroy()
            tasks = self.get_all_tasks_for_date(d_str)
            tasks.sort(key=lambda x: self.get_priority_value(x.get('priority', 'Low')))
            if not tasks:
                ttk.Label(list_f, text="No tasks.", style='DarkLabel.TLabel', background=self.BG_CARD).pack(pady=10)
            for t in tasks:
                row = ttk.Frame(list_f, style='DarkCard.TFrame')
                row.pack(fill='x', pady=2)
                var = tk.BooleanVar(value=t.get('done', False))

                def toggle(v=var, task=t):
                    if task['source_type'] == 'calendar':
                        self.calendar_tasks[task['source_id']][task['index']]['done'] = v.get()
                    else:
                        self.notebooks[task['source_id']]['tasks'][task['index']]['done'] = v.get()
                    self._refresh_calendar_ui(refresh)

                ttk.Checkbutton(row, variable=var, command=toggle, style='DarkLabel.TLabel').pack(side='left')
                txt = t['text']
                if t['source_type'] == 'notebook':
                    txt += f" (NB: {t['notebook_title']})"
                fg = '#888' if t.get('done') else self.FG_LIGHT
                info = ttk.Frame(row, style='DarkCard.TFrame')
                info.pack(side='left', padx=5)
                ttk.Label(info, text=txt, style='DarkLabel.TLabel', background=self.BG_CARD,
                          foreground=fg, wraplength=550).pack(anchor='w')
                p_color = self._get_priority_color(t.get('priority', 'Low'))
                ttk.Label(info, text=f"Priority: {t.get('priority', 'Low')}", font=('Arial', 8),
                          foreground=p_color, background=self.BG_CARD).pack(anchor='w')

                def delete_task(task=t):
                    if task['source_type'] == 'calendar':
                        del self.calendar_tasks[task['source_id']][task['index']]
                    else:
                        del self.notebooks[task['source_id']]['tasks'][task['index']]
                    self._refresh_calendar_ui(refresh)

                tk.Button(row, text="×", command=delete_task, bg=self.BG_CARD, fg='#E57373', bd=0,
                          font=('Arial', 10, 'bold')).pack(side='left', padx=10, anchor='center')
                if t['source_type'] == 'notebook':
                    ttk.Label(row, text="📓", style='DarkLabel.TLabel', background=self.BG_CARD).pack(side='right')

                def show_context_menu(e, task=t):
                    m = tk.Menu(popup, tearoff=0, bg=self.BG_ACCENT, fg='#FFF')
                    p_menu = tk.Menu(m, tearoff=0, bg=self.BG_ACCENT, fg='#FFF')

                    def set_prio(new_p):
                        if task['source_type'] == 'calendar':
                            self.calendar_tasks[task['source_id']][task['index']]['priority'] = new_p
                        else:
                            self.notebooks[task['source_id']]['tasks'][task['index']]['priority'] = new_p
                        self._refresh_calendar_ui(refresh)

                    p_menu.add_command(label="High", command=lambda: set_prio('High'))
                    p_menu.add_command(label="Medium", command=lambda: set_prio('Medium'))
                    p_menu.add_command(label="Low", command=lambda: set_prio('Low'))
                    m.add_cascade(label="Change Priority", menu=p_menu)
                    m.add_separator()
                    m.add_command(label="Delete", command=lambda: delete_task(task))
                    m.tk_popup(e.x_root, e.y_root)

                row.bind("<Button-3>", show_context_menu)
            list_f.update_idletasks()
            cv.config(scrollregion=cv.bbox("all"))

        refresh()

        add_f = ttk.Frame(cont, style='DarkFrame.TFrame')
        add_f.pack(fill='x', pady=10)
        t_var = tk.StringVar()
        d_var = tk.StringVar(value=d_str)
        p_var = tk.StringVar(value='Medium')

        ttk.Label(add_f, text="Task", style='DarkLabel.TLabel').pack(anchor='w')
        ttk.Entry(add_f, textvariable=t_var, style='DarkEntry.TEntry').pack(fill='x', pady=2)
        ttk.Label(add_f, text="Date (YYYY-MM-DD)", style='DarkLabel.TLabel').pack(anchor='w')
        ttk.Entry(add_f, textvariable=d_var, style='DarkEntry.TEntry').pack(fill='x', pady=2)
        ttk.Label(add_f, text="Priority", style='DarkLabel.TLabel').pack(anchor='w')
        ttk.Combobox(add_f, textvariable=p_var, values=['Low', 'Medium', 'High'], state='readonly').pack(fill='x', pady=2)

        def add():
            txt, date_val = t_var.get().strip(), d_var.get().strip()
            if txt:
                if date_val not in self.calendar_tasks:
                    self.calendar_tasks[date_val] = []
                self.calendar_tasks[date_val].append({'text': txt, 'priority': p_var.get(), 'done': False})
                t_var.set("")
                if date_val == d_str:
                    refresh()
                self.update_calendar_view()
                self.update_weekly_due_tasks_sidebar()

        ttk.Button(add_f, text="+", command=add, style='Action.TButton').pack(fill='x', pady=10)
        ttk.Button(cont, text="Close", command=popup.destroy, style='Sidebar.TButton').pack(pady=10)

    # ==========================================================
    #    6. Notebook Editor
    # ==========================================================

    def setup_dedicated_notebook_editor(self):
        editor = self.dedicated_notebook_frame

        nav = ttk.Frame(editor, style='DarkFrame.TFrame')
        nav.pack(fill='x', pady=(0, 10))
        ttk.Button(nav, text="← Back", command=self.show_home_view, style='Sidebar.TButton').pack(side='left')

        controls = ttk.Frame(nav, style='DarkFrame.TFrame')
        controls.pack(side='right')
        ttk.Button(controls, text="📥 Import", command=self.import_note_from_file, style='Sidebar.TButton').pack(side='left', padx=5)
        ttk.Button(controls, text="📤 Export", command=self.export_note_to_file, style='Sidebar.TButton').pack(side='left', padx=5)

        self.notebook_header_frame = ttk.Frame(editor, style='DarkFrame.TFrame', height=180)
        self.notebook_header_frame.pack(fill='x', pady=(0, 20))
        self.notebook_header_frame.pack_propagate(False)
        self.notebook_header_label = ttk.Label(self.notebook_header_frame, background=self.BG_ACCENT, anchor='center')
        self.notebook_header_label.pack(fill='both', expand=True)
        self.notebook_header_frame.bind('<Configure>', self._on_notebook_header_resize)

        self.notebook_title_var = tk.StringVar()
        self.notebook_title_entry = ttk.Entry(editor, textvariable=self.notebook_title_var,
                                              font=('Arial', 24, 'bold'), style='DarkEntry.TEntry')
        self.notebook_title_entry.pack(fill='x', pady=10)
        self.notebook_title_var.trace_add("write", self._on_title_change)

        split = ttk.Frame(editor, style='DarkFrame.TFrame')
        split.pack(fill='both', expand=True)
        split.grid_columnconfigure(0, weight=3)
        split.grid_columnconfigure(1, weight=1)
        split.grid_rowconfigure(0, weight=1)

        self.notebook_text = scrolledtext.ScrolledText(split, bg=self.BG_CARD, fg=self.FG_LIGHT,
                                                       borderwidth=0, font=('Arial', 12))
        self.notebook_text.grid(row=0, column=0, sticky='nsew', padx=(0, 20))
        self.notebook_text.bind("<Tab>", self._handle_tab_indent)

        bottom_bar = ttk.Frame(split, style='DarkFrame.TFrame')
        bottom_bar.grid(row=1, column=0, sticky='ew', padx=(0, 20), pady=(5, 0))
        ttk.Button(bottom_bar, text="📷 Insert Image", command=self.insert_image_to_note,
                   style='Action.TButton').pack(side='left')

        self.nb_right_panel = ttk.Frame(split, style='DarkCard.TFrame', padding=10)
        self.nb_right_panel.grid(row=0, column=1, rowspan=2, sticky='nsew')
        self._setup_notebook_right_panel()

        self.image_display_frame = ttk.Frame(editor, style='DarkFrame.TFrame')
        self.image_display_frame.pack(fill='x', pady=10)
        ttk.Button(self.image_display_frame, text="Set Thumbnail",
                   command=self.set_notebook_thumbnail_from_file, style='Action.TButton').pack(side='right')

    def _setup_notebook_right_panel(self):
        cal_nav = ttk.Frame(self.nb_right_panel, style='DarkCard.TFrame')
        cal_nav.pack(fill='x', pady=(0, 5))
        self.nb_month_lbl = ttk.Label(cal_nav, text="Month Year", font=('Arial', 10, 'bold'),
                                      style='DarkLabel.TLabel', background=self.BG_CARD)
        self.nb_month_lbl.pack(side='left')
        ttk.Button(cal_nav, text=">", command=lambda: self.change_nb_month(1), style='Sidebar.TButton', width=2).pack(side='right')
        ttk.Button(cal_nav, text="<", command=lambda: self.change_nb_month(-1), style='Sidebar.TButton', width=2).pack(side='right')

        self.nb_cal_grid = ttk.Frame(self.nb_right_panel, style='DarkCard.TFrame')
        self.nb_cal_grid.pack(fill='x', pady=(0, 10))

        self.nb_sel_date_lbl = ttk.Label(self.nb_right_panel, text="Selected: ", font=('Arial', 10, 'bold'),
                                         style='DarkLabel.TLabel', background=self.BG_CARD, foreground=self.ACCENT_COLOR)
        self.nb_sel_date_lbl.pack(anchor='w')

        self.nb_task_canvas = tk.Canvas(self.nb_right_panel, bg=self.BG_CARD, highlightthickness=0, height=200)
        self.nb_task_canvas.pack(fill='both', expand=True, pady=5)
        self.nb_task_list_frame = ttk.Frame(self.nb_task_canvas, style='DarkCard.TFrame')
        self.nb_task_canvas.create_window((0, 0), window=self.nb_task_list_frame, anchor='nw', width=250)
        self.nb_task_list_frame.bind("<Configure>",
                                     lambda e: self.nb_task_canvas.configure(scrollregion=self.nb_task_canvas.bbox("all")))

        input_f = ttk.Frame(self.nb_right_panel, style='DarkCard.TFrame')
        input_f.pack(fill='x', pady=5)
        self.nb_task_entry = ttk.Entry(input_f, style='DarkEntry.TEntry')
        self.nb_task_entry.pack(fill='x', pady=2)

        priority_row = ttk.Frame(input_f, style='DarkCard.TFrame')
        priority_row.pack(fill='x', pady=2)
        ttk.Label(priority_row, text="Priority:", style='DarkLabel.TLabel').pack(side='left')
        self.nb_task_priority_var = tk.StringVar(value="Medium")
        self.nb_task_priority_combo = ttk.Combobox(priority_row, textvariable=self.nb_task_priority_var,
                                                   values=["Low", "Medium", "High"], state="readonly", width=10)
        self.nb_task_priority_combo.pack(side='left', padx=5)
        ttk.Button(input_f, text="+ Add to Date", command=self.add_task_to_notebook_date,
                   style='Action.TButton').pack(fill='x', pady=(5, 0))

    def update_notebook_editor_view(self):
        nb = self.notebooks.get(self.active_notebook_id, {'title': '', 'content': '', 'tasks': []})
        self.notebook_title_var.set(nb['title'])
        self.notebook_text.delete('1.0', tk.END)
        self.notebook_text.insert(tk.END, nb.get('content', ''))
        self._render_note_images()
        path = nb.get('thumbnail_path', '')
        if path:
            self.notebook_header_frame.pack(before=self.notebook_title_entry, fill='x', pady=(0, 20))
            self.after(20, self._refresh_notebook_header_image)
        else:
            self.notebook_header_frame.pack_forget()
        self.update_notebook_calendar_view()

    def _save_current_notebook_content(self):
        if self.active_notebook_id in self.notebooks:
            if hasattr(self, 'notebook_text') and self.notebook_text.winfo_exists():
                self.notebooks[self.active_notebook_id]['content'] = self.notebook_text.get('1.0', tk.END).strip()
                self.notebooks[self.active_notebook_id]['title'] = self.notebook_title_var.get()

    def add_notebook(self):
        new_id = max(self.notebooks.keys()) + 1 if self.notebooks else 1
        self.notebooks[new_id] = {'title': f"Untitled Notebook {new_id}", 'content': "",
                                  'thumbnail_path': "", 'images': [], 'tasks': []}
        self.update_sidebar_list()
        self.update_notebook_grid()
        self.show_notebook_view(new_id)

    def rename_notebook(self, nb_id):
        popup = tk.Toplevel(self, bg=self.BG_CARD)
        popup.title("Rename")
        popup.geometry(f"300x150+{self.winfo_x() + 200}+{self.winfo_y() + 200}")
        content = ttk.Frame(popup, style='DarkFrame.TFrame', padding=15)
        content.pack(fill='both', expand=True)
        var = tk.StringVar(value=self.notebooks[nb_id]['title'])
        ttk.Entry(content, textvariable=var, style='DarkEntry.TEntry').pack(fill='x', pady=10)

        def save():
            if var.get().strip():
                self.notebooks[nb_id]['title'] = var.get().strip()
                self.update_sidebar_list()
                self.update_notebook_grid()
                popup.destroy()

        ttk.Button(content, text="Save", command=save, style='Action.TButton').pack()

    def delete_notebook(self, nb_id):
        if nb_id in self.notebooks:
            del self.notebooks[nb_id]
            if self.active_notebook_id == nb_id:
                self.show_home_view()
            else:
                self.update_sidebar_list()
                self.update_notebook_grid()

    def import_note_from_file(self):
        path = filedialog.askopenfilename(filetypes=[("Text", "*.txt"), ("Markdown", "*.md"), ("All", "*.*")])
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self.notebook_text.delete('1.0', tk.END)
                    self.notebook_text.insert('1.0', f.read())
            except Exception as e:
                self._show_notification_popup(f"Error: {e}", is_error=True)

    def export_note_to_file(self):
        name = self.notebook_title_var.get().replace(" ", "_")
        path = filedialog.asksaveasfilename(initialfile=name, defaultextension=".txt")
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(self.notebook_text.get('1.0', tk.END))
            except Exception as e:
                self._show_notification_popup(f"Error: {e}", is_error=True)

    def insert_image_to_note(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.gif")])
        if path:
            self.notebook_text.insert(tk.INSERT, f"\n[IMG:{path}]\n")
            self._render_note_images()

    def _render_note_images(self):
        self.note_images_cache = []
        self.notebook_text.tag_config("hidden_marker", elide=True)
        start_index = "1.0"
        while True:
            match_len = tk.IntVar()
            index = self.notebook_text.search(r"\[IMG:.*?\]", start_index, stopindex=tk.END, regexp=True, count=match_len)
            if not index:
                break
            end_index = f"{index}+{match_len.get()}c"
            marker_text = self.notebook_text.get(index, end_index)
            try:
                path = marker_text[5:-1]
                if os.path.exists(path):
                    img = Image.open(path)
                    if img.width > 600:
                        img = img.resize((600, int(img.height * 600 / img.width)), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    self.note_images_cache.append(photo)
                    if "rendered_image" not in self.notebook_text.tag_names(index):
                        self.notebook_text.image_create(end_index, image=photo, padx=10, pady=10)
                        self.notebook_text.tag_add("rendered_image", index, end_index)
                        self.notebook_text.tag_add("hidden_marker", index, end_index)
            except Exception as e:
                print(f"Error rendering inline image: {e}")
            start_index = end_index

    def _on_notebook_header_resize(self, event):
        if hasattr(self, '_nb_header_timer'):
            self.after_cancel(self._nb_header_timer)
        self._nb_header_timer = self.after(100, self._refresh_notebook_header_image)

    def _refresh_notebook_header_image(self):
        if not self.active_notebook_id or self.active_notebook_id not in self.notebooks:
            return
        path = self.notebooks[self.active_notebook_id].get('thumbnail_path', '')
        if not path:
            return
        try:
            W = self.notebook_header_frame.winfo_width()
            H = self.notebook_header_frame.winfo_height()
            if W < 50: W = self.winfo_screenwidth()
            if H < 50: H = 180
            img = Image.open(path)
            img_ratio = img.width / img.height
            frame_ratio = W / H
            if frame_ratio > img_ratio:
                new_w, new_h = W, int(W / img_ratio)
            else:
                new_h, new_w = H, int(H * img_ratio)
            img = img.resize((int(new_w), int(new_h)), Image.Resampling.LANCZOS)
            x, y = (new_w - W) // 2, (new_h - H) // 2
            img = img.crop((x, y, x + W, y + H))
            self.notebook_header_label.img = ImageTk.PhotoImage(img)
            self.notebook_header_label.config(image=self.notebook_header_label.img)
        except Exception as e:
            print(f"NB Header Error: {e}")

    def change_notebook_thumbnail(self, nb_id):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.gif")])
        if path:
            self.notebooks[nb_id]['thumbnail_path'] = path
            self.update_notebook_grid()

    def remove_notebook_thumbnail(self, nb_id):
        if nb_id in self.notebooks:
            self.notebooks[nb_id]['thumbnail_path'] = ''
            self.update_notebook_grid()

    def set_notebook_thumbnail_from_file(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg")])
        if path and self.active_notebook_id:
            self.notebooks[self.active_notebook_id]['thumbnail_path'] = path
            self.update_notebook_editor_view()

    def _on_title_change(self, *args):
        if self.active_notebook_id in self.notebooks:
            self.notebooks[self.active_notebook_id]['title'] = self.notebook_title_var.get()
            self.update_sidebar_list()

    def change_nb_month(self, delta):
        self.nb_view_month += delta
        if self.nb_view_month > 12:
            self.nb_view_month = 1
            self.nb_view_year += 1
        elif self.nb_view_month < 1:
            self.nb_view_month = 12
            self.nb_view_year -= 1
        self.update_notebook_calendar_view()

    def update_notebook_calendar_view(self):
        for w in self.nb_cal_grid.winfo_children():
            w.destroy()
        self.nb_month_lbl.config(text=f"{calendar.month_name[self.nb_view_month]} {self.nb_view_year}")
        for i, d in enumerate(calendar.day_abbr):
            ttk.Label(self.nb_cal_grid, text=d[0], font=('Arial', 8, 'bold'), background=self.BG_CARD,
                      foreground='#888', anchor='center').grid(row=0, column=i, sticky='nsew', padx=1)
            self.nb_cal_grid.grid_columnconfigure(i, weight=1)

        nb_tasks = self.notebooks[self.active_notebook_id].get('tasks', [])
        task_dates = {t['due_date'] for t in nb_tasks if not t.get('done')}

        for r, week in enumerate(calendar.monthcalendar(self.nb_view_year, self.nb_view_month)):
            for c, day in enumerate(week):
                if day == 0:
                    continue
                d_str = f"{self.nb_view_year}-{self.nb_view_month:02d}-{day:02d}"
                bg = self.BG_CARD
                fg = self.FG_LIGHT
                if d_str == self.nb_selected_date:
                    bg, fg = self.ACCENT_COLOR, '#FFF'
                elif d_str in task_dates:
                    fg = '#E57373'
                btn = tk.Button(self.nb_cal_grid, text=str(day), bg=bg, fg=fg, bd=0, relief='flat',
                                activebackground=self.BG_ACCENT, command=lambda d=d_str: self.select_notebook_date(d))
                btn.grid(row=r + 1, column=c, sticky='nsew', padx=1, pady=1)

        self.nb_sel_date_lbl.config(text=f"Selected: {self.nb_selected_date}")
        self._draw_notebook_task_list()

    def select_notebook_date(self, date_str):
        self.nb_selected_date = date_str
        self.update_notebook_calendar_view()

    def _draw_notebook_task_list(self):
        for w in self.nb_task_list_frame.winfo_children():
            w.destroy()
        if self.active_notebook_id not in self.notebooks:
            return
        all_tasks = self.notebooks[self.active_notebook_id].get('tasks', [])
        tasks_for_date = [t for t in all_tasks if t.get('due_date') == self.nb_selected_date]
        if not tasks_for_date:
            ttk.Label(self.nb_task_list_frame, text="No tasks for this day.", style='DarkLabel.TLabel',
                      foreground='#888', background=self.BG_CARD).pack(pady=5)
        for t in tasks_for_date:
            f = ttk.Frame(self.nb_task_list_frame, style='DarkCard.TFrame')
            f.pack(fill='x', pady=1)
            var = tk.BooleanVar(value=t.get('done', False))
            real_idx = all_tasks.index(t)

            def toggle(idx=real_idx, v=var):
                self.notebooks[self.active_notebook_id]['tasks'][idx]['done'] = v.get()
                self._draw_notebook_task_list()
                self.update_notebook_calendar_view()
                self.update_weekly_due_tasks_sidebar()

            ttk.Label(f, text="•", foreground=self._get_priority_color(t.get('priority', 'Low')),
                      background=self.BG_CARD, font=('Arial', 14, 'bold')).pack(side='left', padx=(0, 2))
            ttk.Checkbutton(f, variable=var, command=toggle, style='DarkLabel.TLabel').pack(side='left')
            fg = '#888' if t.get('done') else self.FG_LIGHT
            font = ('Arial', 9, 'overstrike') if t.get('done') else ('Arial', 9)
            ttk.Label(f, text=t['text'], font=font, foreground=fg, background=self.BG_CARD,
                      wraplength=180).pack(side='left', fill='x', expand=True)

            def delete(idx=real_idx):
                del self.notebooks[self.active_notebook_id]['tasks'][idx]
                self._draw_notebook_task_list()
                self.update_notebook_calendar_view()
                self.update_weekly_due_tasks_sidebar()

            tk.Button(f, text="×", command=delete, bg=self.BG_CARD, fg='#E57373', bd=0,
                      font=('Arial', 10)).pack(side='right')

        self.nb_task_canvas.update_idletasks()
        self.nb_task_canvas.config(scrollregion=self.nb_task_canvas.bbox("all"))

    def add_task_to_notebook_date(self):
        txt = self.nb_task_entry.get().strip()
        if txt:
            self.notebooks[self.active_notebook_id]['tasks'].append(
                {'text': txt, 'due_date': self.nb_selected_date, 'done': False,
                 'priority': self.nb_task_priority_var.get()})
            self.nb_task_entry.delete(0, tk.END)
            self._draw_notebook_task_list()
            self.update_notebook_calendar_view()
            self.update_weekly_due_tasks_sidebar()

    # ==========================================================
    #    7. QoL
    # ==========================================================

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _setup_global_keybindings(self):
        self.bind_all("<Control-BackSpace>", self._handle_ctrl_backspace)

    def _handle_ctrl_backspace(self, event):
        widget = event.widget
        if isinstance(widget, (tk.Entry, ttk.Entry)):
            cursor_pos = widget.index(tk.INSERT)
            text = widget.get()[:cursor_pos]
            if not text:
                return "break"
            if text[-1].isspace():
                i = len(text) - 1
                while i >= 0 and text[i].isspace(): i -= 1
                new_pos = i + 1
            else:
                i = len(text) - 1
                while i >= 0 and not text[i].isspace(): i -= 1
                new_pos = i + 1
            widget.delete(new_pos, tk.INSERT)
            return "break"
        elif isinstance(widget, tk.Text):
            widget.delete("insert - 1c wordstart", "insert")
            return "break"

    def _handle_tab_indent(self, event):
        event.widget.insert(tk.INSERT, "    ")
        return "break"

    def _show_notification_popup(self, message, is_error=False):
        popup = tk.Toplevel(self, bg=self.BG_CARD)
        popup.title("Notification")
        popup.geometry(f"300x100+{self.winfo_x() + 300}+{self.winfo_y() + 300}")
        bg = '#A30000' if is_error else self.BG_ACCENT
        ttk.Label(popup, text=message, background=bg, foreground='#FFF', padding=15).pack(pady=10)
        self.after(2000, popup.destroy)

    def _get_priority_color(self, p):
        return {'High': '#E57373', 'Medium': '#FFB300', 'Low': '#81C784'}.get(p, self.FG_LIGHT)

    def get_priority_value(self, p):
        return {'Low': 1, 'Medium': 2, 'High': 3}.get(p, 0)

    def get_date_string(self, d):
        return f"{self.current_year}-{self.current_month:02d}-{d:02d}"

    def get_all_tasks_for_date(self, date_str):
        all_tasks = []
        for i, task in enumerate(self.calendar_tasks.get(date_str, [])):
            t = task.copy()
            t.update({'source_type': 'calendar', 'source_id': date_str, 'index': i, 'display_date': date_str})
            all_tasks.append(t)
        for nb_id, nb_data in self.notebooks.items():
            for i, task in enumerate(nb_data.get('tasks', [])):
                if task.get('due_date') == date_str:
                    t = task.copy()
                    t.update({'source_type': 'notebook', 'source_id': nb_id, 'index': i,
                              'notebook_title': nb_data['title'], 'display_date': date_str})
                    all_tasks.append(t)
        return all_tasks

    def _get_current_week_dates(self):
        today = datetime.now().date()
        start = today - timedelta(days=today.weekday())
        return [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]


if __name__ == "__main__":
    app = ProductivityApp()
    app.mainloop()