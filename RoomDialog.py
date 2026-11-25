import tkinter as tk
from tkinter import ttk, messagebox

try:
    from config.prices import REPAIR_CLASSES
except ImportError:
    REPAIR_CLASSES = ["Эконом", "Комфорт", "Люкс"]

class RoomDialog:
    def __init__(self, parent, title, region, room=None):
        self.result = None
        self.region = region
        self.room = room

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("440x360")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel)

        self._build_ui()
        self.dialog.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 440) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 360) // 2
        self.dialog.geometry(f"+{max(0, x)}+{max(0, y)}")
        self.name_entry.focus_set()
        self.name_entry.select_range(0, tk.END)

    def _build_ui(self):
        main = ttk.Frame(self.dialog, padding="18")
        main.pack(fill=tk.BOTH, expand=True)

        tk.Label(main, text=self.dialog.title(), font=("Arial", 13, "bold"), fg="#2c3e50").pack()
        tk.Label(main, text=f"Проект: {self.region}", font=("Arial", 9), fg="#7f8c8d").pack(pady=(0, 12))

        form = ttk.LabelFrame(main, text="Параметры помещения", padding="12")
        form.pack(fill=tk.BOTH, expand=True)
        form.columnconfigure(1, weight=1)

        # 1. Название
        ttk.Label(form, text="Название помещения:").grid(row=0, column=0, sticky=tk.W, pady=6, padx=(0, 10))
        self.name_var = tk.StringVar(value=getattr(self.room, "name", "Комната"))
        self.name_entry = ttk.Entry(form, textvariable=self.name_var, font=("Arial", 10))
        self.name_entry.grid(row=0, column=1, sticky=tk.EW, pady=6)

        # 2. Площадь пола
        ttk.Label(form, text="Площадь пола (м²):").grid(row=1, column=0, sticky=tk.W, pady=6, padx=(0, 10))
        self.floor_var = tk.StringVar(value=str(getattr(self.room, "floor_area", 15.0)))
        self.floor_entry = ttk.Entry(form, textvariable=self.floor_var, font=("Arial", 10))
        self.floor_entry.grid(row=1, column=1, sticky=tk.EW, pady=6)

        # 3. Площадь стен
        ttk.Label(form, text="Площадь стен (м²):").grid(row=2, column=0, sticky=tk.W, pady=6, padx=(0, 10))
        self.wall_var = tk.StringVar(value=str(getattr(self.room, "wall_area", 35.0)))
        self.wall_entry = ttk.Entry(form, textvariable=self.wall_var, font=("Arial", 10))
        self.wall_entry.grid(row=2, column=1, sticky=tk.EW, pady=6)

        # 4. Класс ремонта
        ttk.Label(form, text="Класс ремонта:").grid(row=3, column=0, sticky=tk.W, pady=6, padx=(0, 10))
        self.class_var = tk.StringVar(value=getattr(self.room, "repair_class", "Комфорт"))
        self.class_combo = ttk.Combobox(form, textvariable=self.class_var, values=REPAIR_CLASSES, state="readonly", font=("Arial", 10))
        self.class_combo.grid(row=3, column=1, sticky=tk.EW, pady=6)

        # Стрелки вверх/вниз для быстрого шага 0.5
        for ent in (self.floor_entry, self.wall_entry):
            ent.bind("<Up>", lambda e, w=ent: self._step(w, 0.5))
            ent.bind("<Down>", lambda e, w=ent: self._step(w, -0.5))

        # Кнопки внизу
        btns = ttk.Frame(main)
        btns.pack(pady=(14, 0))
        tk.Button(btns, text="Сохранить", width=15, bg="#27ae60", fg="white", font=("Arial", 10, "bold"), command=self.save).pack(side=tk.LEFT, padx=8)
        tk.Button(btns, text="Отмена", width=12, bg="#e74c3c", fg="white", font=("Arial", 10, "bold"), command=self.cancel).pack(side=tk.LEFT, padx=8)

        self.dialog.bind("<Return>", lambda e: self.save())
        self.dialog.bind("<Escape>", lambda e: self.cancel())

    def _step(self, widget, delta):
        try:
            val = float(widget.get().replace(",", ".") or 0)
            val = max(0.0, round(val + delta, 2))
            widget.delete(0, tk.END)
            widget.insert(0, str(val))
        except ValueError:
            pass
        return "break"

    def save(self):
        name = self.name_var.get().strip() or "Помещение"
        try:
            floor = float(self.floor_var.get().replace(",", "."))
            wall = float(self.wall_var.get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректные числа для площадей!", parent=self.dialog)
            return
        if floor <= 0 or wall < 0:
            messagebox.showerror("Ошибка", "Площадь пола должна быть больше 0!", parent=self.dialog)
            return
        self.result = {
            "name": name,
            "floor": round(floor, 2),
            "wall": round(wall, 2),
            "class": self.class_var.get()
        }
        self.dialog.destroy()

    def cancel(self):
        self.result = None
        self.dialog.destroy()
