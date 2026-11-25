import tkinter as tk
from tkinter import ttk, messagebox
from config.prices import PRICES, REGIONS, REGION_COEFFICIENTS

class SettingsDialog:
    def __init__(self, parent, current_project=None):
        self.saved = False
        self.current_project = current_project

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Настройки цен и региона")
        self.dialog.geometry("420x350")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)

        main = ttk.Frame(self.dialog, padding="18")
        main.pack(fill=tk.BOTH, expand=True)

        tk.Label(main, text="Настройки ставок и проекта", font=("Arial", 13, "bold"), fg="#2c3e50").pack(pady=(0, 12))

        form = ttk.LabelFrame(main, text="Базовые ставки (руб. за 1 м² привед. площади)", padding="12")
        form.pack(fill=tk.X, pady=(0, 10))
        form.columnconfigure(1, weight=1)

        self.vars = {}
        for idx, cls in enumerate(("Эконом", "Комфорт", "Люкс")):
            ttk.Label(form, text=f"Класс «{cls}»:").grid(row=idx, column=0, sticky=tk.W, pady=5, padx=(0, 10))
            v = tk.StringVar(value=str(PRICES.get(cls, 5000.0)))
            self.vars[cls] = v
            ttk.Entry(form, textvariable=v, font=("Arial", 10)).grid(row=idx, column=1, sticky=tk.EW, pady=5)

        if self.current_project:
            reg_frame = ttk.LabelFrame(main, text="Регион текущего объекта", padding="10")
            reg_frame.pack(fill=tk.X, pady=(0, 10))
            reg_frame.columnconfigure(1, weight=1)
            ttk.Label(reg_frame, text="Регион:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
            self.reg_var = tk.StringVar(value=self.current_project.region)
            ttk.Combobox(reg_frame, textvariable=self.reg_var, values=REGIONS, state="readonly").grid(row=0, column=1, sticky=tk.EW)

        btns = ttk.Frame(main)
        btns.pack(pady=(8, 0))
        tk.Button(btns, text="Применить", width=15, bg="#27ae60", fg="white", font=("Arial", 10, "bold"), command=self.apply).pack(side=tk.LEFT, padx=8)
        tk.Button(btns, text="Отмена", width=12, bg="#e74c3c", fg="white", font=("Arial", 10, "bold"), command=self.dialog.destroy).pack(side=tk.LEFT, padx=8)

    def apply(self):
        try:
            new_prices = {k: float(v.get().replace(",", ".")) for k, v in self.vars.items()}
            if any(val <= 0 for val in new_prices.values()):
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Ставки должны быть положительными числами!", parent=self.dialog)
            return

        PRICES.update(new_prices)
        with open("config/prices.py", "w", encoding="utf-8") as f:
            f.write(f"REPAIR_CLASSES = {list(PRICES.keys())!r}\nPRICES = {PRICES!r}\nREGIONS = {REGIONS!r}\nREGION_COEFFICIENTS = {REGION_COEFFICIENTS!r}\n")

        if self.current_project and hasattr(self, "reg_var"):
            self.current_project.region = self.reg_var.get()

        self.saved = True
        self.dialog.destroy()
