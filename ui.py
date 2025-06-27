import tkinter as tk
from tkinter import ttk, messagebox
from models import Uniterm, CombinedUniterm
from service import UnitermService

class UnitermApp:
    
    def __init__(self, root: tk.Tk, service: UnitermService):
        self.root = root
        self.service = service
        
        self.uniterm1 = Uniterm()
        self.uniterm2 = Uniterm()
        self.combination_mode = None
        self.save_name = tk.StringVar()

        self.uniterm1_canvas = None
        self.uniterm2_canvas = None
        self.combination_canvas = None
        self.replace_left_btn = None
        self.replace_right_btn = None
        self.left_panel = None
        self.save_name_entry = None
        
        self._setup_window()
        self._apply_styles()
        self._create_widgets()
        self.refresh_list()

    def _setup_window(self):
        self.root.title("Projekt MASI")
        self.root.geometry("850x750")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        self.service.db_manager.close()
        self.root.destroy()

    def _apply_styles(self):
        s = ttk.Style()
        s.theme_use('clam')
        bg_app, bg_panel, text_color = '#f0f0f0', '#ffffff', '#333333'
        accent_blue, accent_blue_hover = '#007bff', '#0056b3'
        s.configure('.', font=('Segoe UI', 9))
        s.configure('TFrame', background=bg_app)
        s.configure('TLabelframe', background=bg_panel, bordercolor='#dcdcdc', relief='solid', borderwidth=1)
        s.configure('TLabelframe.Label', background=bg_panel, foreground=text_color, font=('Segoe UI', 10, 'bold'))
        s.configure('TButton', background=accent_blue, foreground='white', borderwidth=0, focusthickness=0, relief='flat', padding=(10, 5))
        s.map('TButton', background=[('active', accent_blue_hover), ('pressed', accent_blue)])
        s.configure('TEntry', fieldbackground='white', bordercolor='#dcdcdc', relief='solid', borderwidth=1, padding=3)
        s.configure('TLabel', background=bg_app, foreground=text_color)
        s.configure('TRadiobutton', background=bg_panel, foreground=text_color)

    def _create_widgets(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=3)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)

        self._create_saved_list_panel(main_frame)
        self._create_uniterm_frame(main_frame, row=0, uniterm_id=1, title=" Uniterm I")
        self._create_uniterm_frame(main_frame, row=1, uniterm_id=2, title=" Uniterm II")
        self._create_combination_panel(main_frame)
        self._create_bottom_bar(main_frame)

        self.root.after(100, self._sync_and_redraw)

    def _create_saved_list_panel(self, parent):
        list_frame = ttk.Frame(parent)
        list_frame.grid(row=0, column=0, rowspan=3, sticky="nsew", padx=(0, 10), pady=5)
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)

        self.left_panel = tk.Listbox(list_frame, bg='#ffffff', fg='#333333', selectbackground='#007bff', selectforeground='white', borderwidth=1, relief='solid', highlightthickness=0)
        self.left_panel.grid(row=0, column=0, sticky="nsew")

        btn_frame = ttk.Frame(list_frame)
        btn_frame.grid(row=1, column=0, sticky="ew", pady=(5,0))
        btn_frame.columnconfigure((0,1,2), weight=1)
        
        ttk.Button(btn_frame, text="Załaduj", command=self.load_selected_uniterm).grid(row=0, column=0, padx=2, sticky="ew")
        ttk.Button(btn_frame, text="Usuń", command=self.delete_selected_uniterm).grid(row=0, column=1, padx=2, sticky="ew")
        ttk.Button(btn_frame, text="Odśwież", command=self.refresh_list).grid(row=0, column=2, padx=2, sticky="ew")

    def _create_uniterm_frame(self, parent, row, uniterm_id, title):
        frame = ttk.LabelFrame(parent, text=title, padding=10)
        frame.grid(row=row, column=1, sticky="nsew", pady=5)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        
        canvas = tk.Canvas(frame, height=70, bg="white", highlightbackground="lightgrey", highlightthickness=1)
        canvas.grid(row=0, column=0, sticky="nsew")
        canvas.bind("<Configure>", lambda e, c=canvas, u_id=uniterm_id: self._draw_uniterm_graphic(c, u_id))
        
        if uniterm_id == 1: self.uniterm1_canvas = canvas
        else: self.uniterm2_canvas = canvas

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=1, column=0, sticky="e", pady=(5, 0))
        ttk.Button(btn_frame, text="Wyczyść", command=lambda u_id=uniterm_id: self.clear_uniterm(u_id)).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Edytuj/Dodaj", command=lambda u_id=uniterm_id: self.open_edit_dialog(u_id)).pack(side=tk.LEFT, padx=2)

    def _create_combination_panel(self, parent):
        frame = ttk.LabelFrame(parent, text=" Uniterm III (Kombinacja)", padding=10)
        frame.grid(row=2, column=1, sticky="nsew", pady=5)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=0, column=0, sticky="ew")
        self.replace_left_btn = ttk.Button(btn_frame, text="Zamień A", command=self.combine_replace_left, state=tk.DISABLED)
        self.replace_left_btn.pack(side=tk.LEFT)
        self.replace_right_btn = ttk.Button(btn_frame, text="Zamień B", command=self.combine_replace_right, state=tk.DISABLED)
        self.replace_right_btn.pack(side=tk.RIGHT)

        self.combination_canvas = tk.Canvas(frame, height=70, bg="white", highlightbackground="lightgrey", highlightthickness=1)
        self.combination_canvas.grid(row=1, column=0, sticky="nsew", pady=(5,0))
        self.combination_canvas.bind("<Configure>", lambda e: self._draw_combination_graphic())

    def _create_bottom_bar(self, parent):
        bottom_frame = ttk.Frame(parent, padding=(0, 10))
        bottom_frame.grid(row=3, column=1, sticky="se", pady=5)
        ttk.Label(bottom_frame, text="Nazwa zapisu:").pack(side=tk.LEFT, padx=(0, 5))
        self.save_name_entry = ttk.Entry(bottom_frame, width=20, textvariable=self.save_name)
        self.save_name_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="Zapisz", command=self.save_uniterm).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="Wyczyść wszystko", command=self.clear_all).pack(side=tk.LEFT, padx=5)
    
    def _draw_uniterm_graphic(self, canvas, uniterm_id):
        canvas.delete("all")
        width, height = canvas.winfo_width(), canvas.winfo_height()
        if width < 10 or height < 10: return

        draw_width = max(min(width * 0.8, 500), 150)
        offset_x = (width - draw_width) / 2
        
        uniterm = self.uniterm1 if uniterm_id == 1 else self.uniterm2
        
        if uniterm_id == 1:
            y = height * 0.4
            start_x, end_x = offset_x, offset_x + draw_width
            canvas.create_line(start_x, y, end_x, y, width=2)
            canvas.create_line(start_x, y - 8, start_x, y + 8, width=2)
            canvas.create_line(end_x, y - 8, end_x, y + 8, width=2)
            
            texts = { (start_x + draw_width * 0.25, y + 20): uniterm.val_a,
                      (start_x + draw_width * 0.75, y + 20): uniterm.val_b }
            if uniterm.is_complete():
                texts[(start_x + draw_width * 0.5, y + 20)] = (uniterm.separator, "black", "bold")
        else:
            y = height * 0.4
            bbox = (offset_x, y - height * 0.2, offset_x + draw_width, y + height * 0.2)
            canvas.create_arc(bbox, start=0, extent=180, style=tk.ARC, width=2)
            
            center_x = offset_x + draw_width / 2
            texts = { (center_x - draw_width * 0.25, y + 20): uniterm.val_a,
                      (center_x + draw_width * 0.25, y + 20): uniterm.val_b }
            if uniterm.is_complete():
                texts[(center_x, y + 20)] = (uniterm.separator, "black", "bold")
        
        self._draw_text_on_canvas(canvas, texts)

    def _draw_combination_graphic(self):
        canvas = self.combination_canvas
        canvas.delete("all")
        width, height = canvas.winfo_width(), canvas.winfo_height()
        if width < 10 or height < 10: return

        draw_width = max(min(width * 0.8, 500), 150)
        offset_x = (width - draw_width) / 2
        line_y = height * 0.3
        start_x, end_x = offset_x, offset_x + draw_width

        canvas.create_line(start_x, line_y, end_x, line_y, width=2)
        canvas.create_line(start_x, line_y - 8, start_x, line_y + 8, width=2)
        canvas.create_line(end_x, line_y - 8, end_x, line_y + 8, width=2)

        text_a_pos_x = start_x + draw_width * 0.25
        text_b_pos_x = start_x + draw_width * 0.75
        
        base_texts = {}
        if self.combination_mode != 'replace_left':
            base_texts[(text_a_pos_x, line_y + 15)] = self.uniterm1.val_a
        if self.combination_mode != 'replace_right':
            base_texts[(text_b_pos_x, line_y + 15)] = self.uniterm1.val_b
        if self.uniterm1.is_complete():
             base_texts[(start_x + draw_width * 0.5, line_y + 15)] = (self.uniterm1.separator, "blue", "bold")
        self._draw_text_on_canvas(canvas, base_texts)

        if self.combination_mode == 'replace_left':
            self._draw_nested_arc_below(canvas, text_a_pos_x, line_y, height, draw_width * 0.4)
        elif self.combination_mode == 'replace_right':
            self._draw_nested_arc_below(canvas, text_b_pos_x, line_y, height, draw_width * 0.4)

    def _draw_nested_arc_below(self, canvas, center_x, line_y, canvas_height, arc_width):
        arc_height = canvas_height * 0.2
        gap = 5
        bbox = (center_x - arc_width / 2, line_y + gap, center_x + arc_width / 2, line_y + arc_height + gap)
        canvas.create_arc(bbox, start=0, extent=180, style=tk.ARC, width=2, outline="black")

        text_y = line_y + arc_height * 0.7 + gap
        arc_texts = {
            (center_x - arc_width * 0.25, text_y): self.uniterm2.val_a,
            (center_x + arc_width * 0.25, text_y): self.uniterm2.val_b,
        }
        if self.uniterm2.is_complete():
            arc_texts[(center_x, text_y)] = (self.uniterm2.separator, "red", "bold")
        self._draw_text_on_canvas(canvas, arc_texts)

    def _draw_text_on_canvas(self, canvas, texts_map, font_size=9):
        for pos, content in texts_map.items():
            if not content: continue
            text, color, weight = (content[0], content[1], content[2]) if isinstance(content, tuple) else (content, "black", "normal")
            canvas.create_text(pos[0], pos[1], text=text, fill=color, font=("Arial", font_size, weight), anchor="center")
    
    def refresh_list(self):
        self.left_panel.delete(0, tk.END)
        names = self.service.get_all_saved_names()
        for name in names:
            self.left_panel.insert(tk.END, name)
        print("Lista została odświeżona.")

    def open_edit_dialog(self, uniterm_id):
        current_uniterm = self.uniterm1 if uniterm_id == 1 else self.uniterm2
        dialog = UnitermDialog(self.root, f"Edycja Uniterm {uniterm_id}", current_uniterm)
        result = dialog.show()

        if result:
            if uniterm_id == 1:
                self.uniterm1 = result
            else:
                self.uniterm2 = result
            self._sync_and_redraw()

    def load_selected_uniterm(self):
        selected_indices = self.left_panel.curselection()
        if not selected_indices:
            self._show_message("Informacja", "Nie wybrano elementu do załadowania.", "info")
            return
        
        name = self.left_panel.get(selected_indices[0])
        loaded_data = self.service.load_uniterm(name)

        if loaded_data:
            self.uniterm1 = loaded_data.base_uniterm
            self.uniterm2 = loaded_data.nested_uniterm
            self.combination_mode = loaded_data.combination_mode
            self.save_name.set(loaded_data.name)
            self._sync_and_redraw()
            self._show_message("Sukces", f"Załadowano '{name}'.", "info")
        else:
            self._show_message("Błąd", f"Nie udało się załadować '{name}'.", "error")
    
    def save_uniterm(self):
        combined_uniterm = CombinedUniterm(
            name=self.save_name.get().strip(),
            base_uniterm=self.uniterm1,
            nested_uniterm=self.uniterm2,
            combination_mode=self.combination_mode
        )

        if not combined_uniterm.is_valid_for_save():
            self._show_message("Walidacja nieudana", "Wszystkie pola (Nazwa, Uniterm I, Uniterm II) muszą być wypełnione.", "warning")
            return

        if self._ask_yes_no("Potwierdzenie zapisu", f"Czy na pewno chcesz zapisać uniterm o nazwie '{combined_uniterm.name}'?"):
            if self.service.save_uniterm(combined_uniterm):
                self._show_message("Sukces", f"Zapisano '{combined_uniterm.name}'.", "info")
                self.refresh_list()
            else:
                 self._show_message("Błąd", f"Nie udało się zapisać '{combined_uniterm.name}'.\nSprawdź, czy nazwa nie jest już zajęta.", "error")

    def delete_selected_uniterm(self):
        selected_indices = self.left_panel.curselection()
        if not selected_indices:
            self._show_message("Informacja", "Nie wybrano elementu do usunięcia.", "info")
            return

        name = self.left_panel.get(selected_indices[0])
        if self._ask_yes_no("Potwierdzenie usunięcia", f"Czy na pewno chcesz usunąć '{name}'?"):
            if self.service.delete_uniterm(name):
                self._show_message("Sukces", f"Usunięto '{name}'.", "info")
                self.refresh_list()
            else:
                self._show_message("Błąd", f"Nie udało się usunąć '{name}'.", "error")
    
    def combine_replace_left(self):
        self.combination_mode = 'replace_left'
        self._sync_and_redraw()

    def combine_replace_right(self):
        self.combination_mode = 'replace_right'
        self._sync_and_redraw()

    def clear_uniterm(self, uniterm_id):
        if uniterm_id == 1:
            self.uniterm1 = Uniterm()
            self.combination_mode = None
        else:
            self.uniterm2 = Uniterm()
        self._sync_and_redraw()

    def clear_all(self):
        self.uniterm1 = Uniterm()
        self.uniterm2 = Uniterm()
        self.combination_mode = None
        self.save_name.set("")
        self._sync_and_redraw()

    def _sync_and_redraw(self):
        can_combine = self.uniterm1.is_complete() and self.uniterm2.is_complete()
        new_state = tk.NORMAL if can_combine else tk.DISABLED
        self.replace_left_btn.config(state=new_state)
        self.replace_right_btn.config(state=new_state)

        if not self.uniterm1.is_complete():
            self.combination_mode = None

        self._draw_uniterm_graphic(self.uniterm1_canvas, 1)
        self._draw_uniterm_graphic(self.uniterm2_canvas, 2)
        self._draw_combination_graphic()

    def _show_message(self, title, message, msg_type):
        self.root.update_idletasks()
        
        temp_root = tk.Toplevel(self.root)
        temp_root.withdraw()
        
        x = self.root.winfo_x() + self.root.winfo_width() // 2
        y = self.root.winfo_y() + self.root.winfo_height() // 2
        temp_root.geometry(f"+{x}+{y}")
        
        temp_root.destroy()
        
        if msg_type == "info":
            messagebox.showinfo(title, message, parent=self.root)
        elif msg_type == "warning":
            messagebox.showwarning(title, message, parent=self.root)
        elif msg_type == "error":
            messagebox.showerror(title, message, parent=self.root)

    def _ask_yes_no(self, title, message):
        return messagebox.askyesno(title, message, parent=self.root)


class UnitermDialog:
    def __init__(self, parent, title, current_uniterm: Uniterm):
        self.parent = parent
        self.result: Uniterm | None = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x280")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.val_a = tk.StringVar(value=current_uniterm.val_a)
        self.val_b = tk.StringVar(value=current_uniterm.val_b)
        self.separator = tk.StringVar(value=current_uniterm.separator)

        self._center_window()
        self._create_widgets()
        self._validate_on_the_fly()

    def _center_window(self):
        self.dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

    def _create_widgets(self):
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Wartość A:").pack(anchor='w')
        entry_a = ttk.Entry(main_frame, width=40, textvariable=self.val_a)
        entry_a.pack(fill='x', pady=(0, 10))
        entry_a.bind("<KeyRelease>", self._validate_on_the_fly)

        ttk.Label(main_frame, text="Separator:").pack(anchor='w')
        sep_frame = ttk.Frame(main_frame)
        sep_frame.pack(fill='x', pady=(0, 10))
        for sep in [":", ";", ","]:
            ttk.Radiobutton(sep_frame, text=sep, variable=self.separator, value=sep).pack(side='left', padx=(0,10))

        ttk.Label(main_frame, text="Wartość B:").pack(anchor='w')
        entry_b = ttk.Entry(main_frame, width=40, textvariable=self.val_b)
        entry_b.pack(fill='x', pady=(0, 20))
        entry_b.bind("<KeyRelease>", self._validate_on_the_fly)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x', side='bottom')
        ttk.Button(btn_frame, text="Anuluj", command=self.cancel).pack(side='right', padx=(10, 0))
        self.ok_button = ttk.Button(btn_frame, text="OK", command=self.ok)
        self.ok_button.pack(side='right')

    def _validate_on_the_fly(self, event=None):
        is_valid = self.val_a.get().strip() and self.val_b.get().strip()
        self.ok_button.config(state=tk.NORMAL if is_valid else tk.DISABLED)

    def ok(self):
        self.result = Uniterm(
            val_a=self.val_a.get().strip(),
            val_b=self.val_b.get().strip(),
            separator=self.separator.get()
        )
        self.dialog.destroy()

    def cancel(self):
        self.result = None
        self.dialog.destroy()

    def show(self) -> Uniterm | None:
        self.dialog.wait_window()
        return self.result