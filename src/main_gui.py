from SettingsDialog import SettingsDialog
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from models.project import Project
from models.room import Room
from config.prices import PRICES

try:
    from RoomDialog import RoomDialog
except ImportError:
    from dialogs.room_dialog import RoomDialog

class RemontAppGUI:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.callbacks = {}
        self.current_project = None
        self._build_ui()
        self.refresh_project_list()

    def set_callbacks(self, callbacks):
        self.callbacks = callbacks

    def _build_ui(self):
        toolbar = ttk.Frame(self.parent, padding="8")
        toolbar.pack(fill=tk.X)

        ttk.Button(toolbar, text="Новый объект", command=self.create_project_ui).pack(side=tk.LEFT, padx=4)
        ttk.Button(toolbar, text="Удалить объект", command=self.delete_project_ui).pack(side=tk.LEFT, padx=4)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8)
        ttk.Button(toolbar, text="Сохранить всё", command=self.save_ui).pack(side=tk.LEFT, padx=4)
        ttk.Button(toolbar, text="Экспорт в Excel", command=lambda: self.app.on_export_requested("excel")).pack(side=tk.LEFT, padx=4)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8)
        ttk.Button(toolbar, text="Настройки и цены", command=self.open_settings_ui).pack(side=tk.LEFT, padx=4)
        ttk.Button(toolbar, text="О программе", command=self.show_about_ui).pack(side=tk.RIGHT, padx=4)

        paned = ttk.PanedWindow(self.parent, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        left_frame = ttk.LabelFrame(paned, text="Объекты / Квартиры", padding="8")
        paned.add(left_frame, weight=1)

        self.proj_listbox = tk.Listbox(left_frame, font=("Arial", 10), activestyle="none")
        self.proj_listbox.pack(fill=tk.BOTH, expand=True)
        self.proj_listbox.bind("<<ListboxSelect>>", self._on_proj_select)

        right_frame = ttk.LabelFrame(paned, text="Помещения и расчет стоимости", padding="8")
        paned.add(right_frame, weight=3)

        self.proj_header = tk.Label(right_frame, text="Выберите или создайте объект слева", font=("Arial", 12, "bold"), fg="#2c3e50")
        self.proj_header.pack(anchor=tk.W, pady=(0, 8))

        room_btns = ttk.Frame(right_frame)
        room_btns.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(room_btns, text="Добавить помещение", command=self.add_room_ui).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(room_btns, text="Редактировать", command=self.edit_room_ui).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(room_btns, text="Удалить помещение", command=self.delete_room_ui).pack(side=tk.LEFT)

        cols = ("name", "floor", "wall", "total", "rclass", "cost")
        self.tree = ttk.Treeview(right_frame, columns=cols, show="headings", height=12)
        for col, title, w, anc in [
            ("name", "Помещение", 160, tk.W),
            ("floor", "Пол (м2)", 80, tk.CENTER),
            ("wall", "Стены (м2)", 80, tk.CENTER),
            ("total", "Привед. S (м2)", 100, tk.CENTER),
            ("rclass", "Класс ремонта", 110, tk.CENTER),
            ("cost", "Стоимость (руб.)", 130, tk.E)
        ]:
            self.tree.heading(col, text=title)
            self.tree.column(col, width=w, anchor=anc)

        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<Double-1>", lambda e: self.edit_room_ui())

        summary_frame = ttk.Frame(right_frame, padding="10")
        summary_frame.pack(fill=tk.X)
        self.prices_lbl = tk.Label(summary_frame, text="", font=("Arial", 9), fg="#7f8c8d")
        self.prices_lbl.pack(side=tk.LEFT)
        self.total_label = tk.Label(summary_frame, text="ИТОГО ПО ОБЪЕКТУ: 0.00 руб.", font=("Arial", 13, "bold"), fg="#27ae60")
        self.total_label.pack(side=tk.RIGHT)

        
        self.prices_lbl.config(text=f"Ставки: Эконом = {PRICES['Эконом']:.0f} руб/м2 | Комфорт = {PRICES['Комфорт']:.0f} руб/м2 | Люкс = {PRICES['Люкс']:.0f} руб/м2")

    def refresh_project_list(self):
        self.proj_listbox.delete(0, tk.END)
        self.projects_cache = self.app.project_manager.get_all_projects()
        for p in self.projects_cache:
            self.proj_listbox.insert(tk.END, f"{p.name} ({p.region}) — {p.total_cost:,.0f} руб.")
        if self.projects_cache and not self.current_project:
            self.proj_listbox.selection_set(0)
            self.load_project(self.projects_cache[0])

    def _on_proj_select(self, event):
        sel = self.proj_listbox.curselection()
        if sel:
            self.load_project(self.projects_cache[sel[0]])

    def load_project(self, project):
        self.current_project = project
        self.app.current_project = project
        self.app.cost_calculator.calculate_project(project)
        self.proj_header.config(text=f"Объект: {project.name}  |  Регион: {project.region}")

        for item in self.tree.get_children():
            self.tree.delete(item)

        for r in project.rooms:
            self.tree.insert("", tk.END, iid=r.id, values=(
                r.name, f"{r.floor_area:.1f}", f"{r.wall_area:.1f}",
                f"{r.total_area:.1f}", r.repair_class, f"{r.cost:,.2f}"
            ))
        self.total_label.config(text=f"ИТОГО ПО ОБЪЕКТУ: {project.total_cost:,.2f} руб.")

    def create_project_ui(self):
        name = simpledialog.askstring("Новый объект", "Введите название объекта (например, ул. Ленина 15):", parent=self.parent)
        if not name:
            return
        proj = Project(name=name.strip(), region="г. Брянск")
        self.app.project_manager.add_project(proj)
        self.save_ui(silent=True)
        self.refresh_project_list()
        self.load_project(proj)

    def delete_project_ui(self):
        if not self.current_project:
            return
        if messagebox.askyesno("Удаление", f"Удалить объект '{self.current_project.name}'?"):
            self.app.project_manager.delete_project(self.current_project.id)
            self.current_project = None
            self.save_ui(silent=True)
            self.refresh_project_list()

    def add_room_ui(self):
        if not self.current_project:
            messagebox.showwarning("Внимание", "Сначала создайте или выберите объект слева!")
            return
        dlg = RoomDialog(self.parent, "Добавить помещение", self.current_project.region)
        self.parent.wait_window(dlg.dialog)
        if dlg.result:
            r = Room(
                name=dlg.result["name"],
                floor_area=dlg.result["floor"],
                wall_area=dlg.result["wall"],
                repair_class=dlg.result["class"]
            )
            self.current_project.add_room(r)
            self.app.cost_calculator.calculate_project(self.current_project)
            self.save_ui(silent=True)
            self.load_project(self.current_project)
            self.refresh_project_list()

    def edit_room_ui(self):
        if not self.current_project:
            return
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Подсказка", "Выберите помещение в таблице для редактирования")
            return
        room_id = next(iter(sel))
        room = next((r for r in self.current_project.rooms if str(r.id) == str(room_id)), None)
        if not room:
            return
        dlg = RoomDialog(self.parent, "Редактировать помещение", self.current_project.region, room=room)
        self.parent.wait_window(dlg.dialog)
        if dlg.result:
            room.name = dlg.result["name"]
            room.floor_area = dlg.result["floor"]
            room.wall_area = dlg.result["wall"]
            room.repair_class = dlg.result["class"]
            self.app.cost_calculator.calculate_project(self.current_project)
            self.save_ui(silent=True)
            self.load_project(self.current_project)
            self.refresh_project_list()

    def delete_room_ui(self):
        if not self.current_project:
            return
        sel = self.tree.selection()
        if not sel:
            return
        room_id = next(iter(sel))
        self.current_project.remove_room(room_id)
        self.app.cost_calculator.calculate_project(self.current_project)
        self.save_ui(silent=True)
        self.load_project(self.current_project)
        self.refresh_project_list()

    def save_ui(self, silent=False):
        data = self.app.project_manager.to_dict()
        self.app.data_manager.save_projects(data)
        if not silent:
            messagebox.showinfo("Сохранено", "Все объекты и расчеты успешно сохранены!")

    def open_settings_ui(self):
        dlg = SettingsDialog(self.parent, self.current_project)
        self.parent.wait_window(dlg.dialog)
        if dlg.saved:
            self.prices_lbl.config(text=f"Ставки: Эконом = {PRICES['Эконом']:.0f} руб/м2 | Комфорт = {PRICES['Комфорт']:.0f} руб/м2 | Люкс = {PRICES['Люкс']:.0f} руб/м2")
            if self.current_project:
                self.app.cost_calculator.calculate_project(self.current_project)
                self.save_ui(silent=True)
                self.load_project(self.current_project)
            self.refresh_project_list()

    def show_about_ui(self):
        about_text = (
            "RemontCalc v1.1\n"
            "Калькулятор первичного расчёта стоимости ремонта помещений\n\n"
            "Возможности:\n"
            "• Учёт объектов и детализация по помещениям\n"
            "• Расчёт по приведённой площади (пол + стены × 0.5)\n"
            "• Настройка ставок по классам ремонта и регионам\n"
            "• Автосохранение в JSON и экспорт сметы в Excel (.xlsx)\n\n"
            "Разработчик: Мастер-отделочник / Инженер-наладчик (г. Брянск)\n"
            "Телефон: +7 910 335-04-36\n"
            "Email: ra-108@mail.ru\n"
            "Лицензия: MIT (Open Source)"
        )
        messagebox.showinfo("О программе RemontCalc", about_text, parent=self.parent)
