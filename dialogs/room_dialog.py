
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Any, Dict
import re
import traceback

# Конфигурация классов ремонта
try:
    from config import REPAIR_CLASSES
except ImportError:
    REPAIR_CLASSES = ["Эконом", "Комфорт", "Люкс"]


class RoomDialog:
    """✅ Диалог добавления/редактирования помещения с полной функциональностью"""
    
    def __init__(self, parent, title: str, region: str, room: Optional[Any] = None):
        self.result: Optional[Dict[str, Any]] = None
        self.region = region
        self.room = room
        self.parent_ref = parent
        self.widgets_order = []
        
        # Создание диалога
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("480x420")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel)
        
        # Инициализация
        self.setup_validator()
        self.setup_dialog()
        self.dialog.after(50, self.center_dialog)
        self.dialog.after(100, self.set_initial_focus)
    
    # --------------------------------------
    # ✅ ВАЛИДАТОР (исправленный)
    # --------------------------------------
    def setup_validator(self):
        """Настройка валидатора для числовых полей"""
        pattern = r'^-?\d*\.?\d*$'
        
        def validate_action(text: str) -> bool:
            """Проверка формата числа"""
            return not text or re.match(pattern, text) is not None
        
        def validate_proposed(new_text: str, index: str, char: str) -> str:
            """Валидация нового текста"""
            if validate_action(new_text):
                return True
            self.dialog.bell()
            return ""  # ✅ Возвращаем пустую строку для блокировки
        
        self.vcmd_number = (
            self.dialog.register(validate_proposed),
            '%P', '%i', '%S'
        )
    
    # --------------------------------------
    # ✅ ОСНОВНОЙ ИНТЕРФЕЙС
    # --------------------------------------
    def setup_dialog(self):
        """Создание интерфейса"""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.create_header(main_frame)
        
        form_frame = ttk.LabelFrame(main_frame, text="📋 Параметры помещения", padding="15")
        form_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        form_frame.columnconfigure(1, weight=1)
        
        self.create_name_field(form_frame, 0)
        self.create_floor_field(form_frame, 1)
        self.create_wall_field(form_frame, 2)
        self.create_class_field(form_frame, 3)
        self.create_help_text(form_frame, 4)
        
        self.create_button_frame(main_frame)
        self.setup_navigation()
    
    def create_header(self, parent):
        """Заголовок диалога"""
        title_frame = tk.Frame(parent)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(title_frame, text=self.dialog.title(), 
                font=("Arial", 14, "bold"), fg="#2c3e50").pack(pady=(0, 5))
        tk.Label(title_frame, text=f"📍 Проект: {self.region}", 
                font=("Arial", 9), fg="#7f8c8d").pack()
    
    # --------------------------------------
    # ✅ ПОЛЯ ВВОДА (исправленные)
    # --------------------------------------
    def create_name_field(self, parent, row: int):
        """Поле названия (первое в навигации)"""
        tk.Label(parent, text="🏠 Название помещения:", 
                font=("Arial", 10, "bold"), anchor=tk.W)\
            .grid(row=row, column=0, sticky=tk.W, pady=8, padx=(0, 10))
        
        self.name_var = tk.StringVar()
        
        # ✅ Безопасная загрузка значения
        if self.room and hasattr(self.room, 'name'):
            try:
                value = str(self.room.name).strip()
                self.name_var.set(value if value else "Без названия")
            except:
                self.name_var.set("Без названия")
        else:
            # ✅ Безопасное получение счетчика
            app = self.get_parent_app()
            count = 0
            if app and hasattr(app, 'room_manager'):
                try:
                    if hasattr(app.room_manager, 'rooms'):
                        count = len(app.room_manager.rooms)
                    else:
                        count = 0
                except:
                    count = 0
            self.name_var.set(f"Помещение {count + 1}")
        
        self.name_entry = tk.Entry(
            parent, textvariable=self.name_var, width=28,
            font=("Arial", 10), relief=tk.SUNKEN, bd=1,
            highlightthickness=1, highlightcolor="#3498db", insertwidth=2
        )
        self.name_entry.grid(row=row, column=1, sticky=tk.EW, pady=8, padx=(0, 10))
        
        # ✅ Настройка событий
        self.setup_entry_bindings(self.name_entry)
    
    def create_floor_field(self, parent, row: int):
        """Поле площади пола (второе в навигации)"""
        tk.Label(parent, text="📐 Площадь пола (м²):", 
                font=("Arial", 10, "bold"), anchor=tk.W)\
            .grid(row=row, column=0, sticky=tk.W, pady=8, padx=(0, 10))
        
        default = 15.0
        if self.room and hasattr(self.room, 'floor_area'):
            try:
                val = float(self.room.floor_area)
                default = max(0.1, min(1000, val))
            except:
                default = 15.0
        
        self.floor_var = tk.DoubleVar(value=default)
        self.floor_entry = tk.Entry(
            parent, textvariable=self.floor_var, width=28,
            font=("Arial", 10), relief=tk.SUNKEN, bd=1,
            validate='key', validatecommand=self.vcmd_number,
            highlightthickness=1, highlightcolor="#27ae60", insertwidth=2
        )
        self.floor_entry.grid(row=row, column=1, sticky=tk.EW, pady=8, padx=(0, 10))
        
        self.setup_entry_bindings(self.floor_entry, is_number=True)
    
    def create_wall_field(self, parent, row: int):
        """Поле площади стен (третье в навигации)"""
        tk.Label(parent, text="📏 Площадь стен (м²):", 
                font=("Arial", 10, "bold"), anchor=tk.W)\
            .grid(row=row, column=0, sticky=tk.W, pady=8, padx=(0, 10))
        
        default = 25.0
        if self.room and hasattr(self.room, 'wall_area'):
            try:
                val = float(self.room.wall_area)
                default = max(0.0, min(500, val))
            except:
                default = 25.0
        
        self.wall_var = tk.DoubleVar(value=default)
        self.wall_entry = tk.Entry(
            parent, textvariable=self.wall_var, width=28,
            font=("Arial", 10), relief=tk.SUNKEN, bd=1,
            validate='key', validatecommand=self.vcmd_number,
            highlightthickness=1, highlightcolor="#e67e22", insertwidth=2
        )
        self.wall_entry.grid(row=row, column=1, sticky=tk.EW, pady=8, padx=(0, 10))
        
        self.setup_entry_bindings(self.wall_entry, is_number=True)
    
    def create_class_field(self, parent, row: int):
        """Combobox класса (четвертое в навигации)"""
        tk.Label(parent, text="⭐ Класс ремонта:", 
                font=("Arial", 10, "bold"), anchor=tk.W)\
            .grid(row=row, column=0, sticky=tk.W, pady=8, padx=(0, 10))
        
        default_class = "Комфорт"
        if self.room and hasattr(self.room, 'repair_class'):
            rc = str(self.room.repair_class).strip()
            for cls in REPAIR_CLASSES:
                if rc.upper() == cls.upper():
                    default_class = cls
                    break
        
        self.class_var = tk.StringVar(value=default_class)
        self.class_combo = ttk.Combobox(
            parent, textvariable=self.class_var, values=REPAIR_CLASSES,
            state="readonly", width=25, font=("Arial", 10), justify=tk.CENTER
        )
        self.class_combo.grid(row=row, column=1, sticky=tk.W, pady=8, padx=(0, 10))
        
        self.setup_combo_bindings(self.class_combo)
    
    def create_help_text(self, parent, row: int):
        """Подсказка по расчету"""
        help_text = (
            "💡 Расчет стоимости:\n"
            "• Пол: полная стоимость\n"
            "• Стены: коэффициент ×0.5\n"
            "• Общая = пол + (стены × 0.5)"
        )
        tk.Label(parent, text=help_text, 
                font=("Arial", 8), fg="#7f8c8d", justify=tk.LEFT,
                relief=tk.SUNKEN, bd=1, anchor=tk.W, padx=5, pady=5, wraplength=400)\
            .grid(row=row, column=0, columnspan=2, sticky=tk.W+tk.E, pady=(15, 0))
    
    def create_button_frame(self, parent):
        """Кнопки (пятый и шестой элементы)"""
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(pady=15, fill=tk.X)
        
        container = tk.Frame(btn_frame)
        container.pack(expand=True)
        
        self.save_btn = tk.Button(
            container, text="💾 Сохранить изменения", width=18, height=2,
            bg="#27ae60", fg="white", font=("Arial", 10, "bold"),
            relief=tk.RAISED, bd=2, activebackground="#2ecc71",
            cursor="hand2", command=self.save
        )
        self.save_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        self.cancel_btn = tk.Button(
            container, text="❌ Отмена", width=12, height=2,
            bg="#e74c3c", fg="white", font=("Arial", 10, "bold"),
            relief=tk.RAISED, bd=2, activebackground="#c0392b",
            cursor="hand2", command=self.cancel
        )
        self.cancel_btn.pack(side=tk.LEFT)
        
        self.setup_button_bindings()
        
        # Глобальные клавиши
        self.dialog.bind('', self.on_global_return)
        self.dialog.bind('', lambda e: self.cancel())
    
    # --------------------------------------
    # ✅ BINDINGS (ПОЛНЫЕ И ПРАВИЛЬНЫЕ)
    # --------------------------------------
    def setup_entry_bindings(self, entry_widget: tk.Entry, is_number: bool = False):
        """Настройка событий для Entry"""
        # Навигация
        entry_widget.bind('', self.navigate_tab)
        entry_widget.bind('', self.navigate_shift_tab)
        entry_widget.bind('', lambda e: self.focus_next(entry_widget))
        
        # Фокус и выделение
        entry_widget.bind('', lambda e: self.select_all_text(entry_widget))
        entry_widget.bind('', lambda e: self.select_all_text(entry_widget) or "break")
        entry_widget.bind('', lambda e: self.select_all_text(entry_widget) or "break")
        
        # Для числовых полей
        if is_number:
            entry_widget.bind('', self.on_number_key_press)
            entry_widget.bind('', lambda e: self.increment_number(entry_widget, 0.5))
            entry_widget.bind('', lambda e: self.increment_number(entry_widget, -0.5))
    
    def setup_combo_bindings(self, combo_widget: ttk.Combobox):
        """Настройка событий для Combobox"""
        combo_widget.bind('<>', self.on_class_selected)
        combo_widget.bind('', self.navigate_tab)
        combo_widget.bind('', self.navigate_shift_tab)
        combo_widget.bind('', lambda e: self.save())
        combo_widget.bind('', lambda e: combo_widget.event_generate(''))
    
    def setup_button_bindings(self):
        """Настройка событий для кнопок"""
        # Save
        self.save_btn.bind('', lambda e: self.save())
        self.save_btn.bind('', lambda e: self.save())
        self.save_btn.bind('', self.navigate_tab)
        self.save_btn.bind('', self.navigate_shift_tab)
        
        # Cancel
        self.cancel_btn.bind('', lambda e: self.cancel())
        self.cancel_btn.bind('', lambda e: self.cancel())
        self.cancel_btn.bind('', lambda e: self.cancel())
        self.cancel_btn.bind('', self.navigate_shift_tab)
    
    def setup_navigation(self):
        """Инициализация порядка навигации"""
        self.widgets_order = []
        for attr in ['name_entry', 'floor_entry', 'wall_entry', 'class_combo', 'save_btn', 'cancel_btn']:
            if hasattr(self, attr):
                self.widgets_order.append(getattr(self, attr))
        
        print(f"✅ Навигация: {len(self.widgets_order)} элементов")
    
    # --------------------------------------
    # ✅ НАВИГАЦИЯ (ПОЛНАЯ)
    # --------------------------------------
    def navigate_tab(self, event):
        self.focus_next(event.widget)
        return "break"
    
    def navigate_shift_tab(self, event):
        self.focus_previous(event.widget)
        return "break"
    
    def focus_next(self, current_widget):
        """Переход к следующему"""
        try:
            idx = self.widgets_order.index(current_widget)
            next_widget = self.widgets_order[(idx + 1) % len(self.widgets_order)]
            next_widget.focus_set()
            
            if isinstance(next_widget, tk.Entry):
                self.select_all_text(next_widget)
            elif isinstance(next_widget, ttk.Combobox):
                next_widget.event_generate('')
        except (ValueError, IndexError):
            if self.widgets_order:
                self.widgets_order[0].focus_set()
    
    def focus_previous(self, current_widget):
        """Переход к предыдущему"""
        try:
            idx = self.widgets_order.index(current_widget)
            prev_widget = self.widgets_order[(idx - 1) % len(self.widgets_order)]
            prev_widget.focus_set()
            
            if isinstance(prev_widget, tk.Entry):
                self.select_all_text(prev_widget)
        except (ValueError, IndexError):
            if self.widgets_order:
                self.widgets_order[-1].focus_set()
    
    def on_global_return(self, event):
        """Глобальный Enter"""
        widget = event.widget
        if widget == self.save_btn:
            self.save()
        elif widget == self.cancel_btn:
            self.cancel()
        else:
            self.focus_next(widget)
        return "break"
    
    # --------------------------------------
    # ✅ ЧИСЛОВЫЕ ПОЛЯ
    # --------------------------------------
    def on_number_key_press(self, event):
        """Фильтрация числового ввода"""
        char = event.char
        keysym = event.keysym
        
        allowed_keys = {'BackSpace', 'Delete', 'Left', 'Right', 'Home', 'End', 
                       'Tab', 'Return', 'Up', 'Down', 'Escape'}
        
        if keysym in allowed_keys:
            return None
        
        if char and char.isdigit():
            return None
        
        if char in ['.', ','] and event.widget.get().count('.') == 0:
            return None
        
        if char == '-' and event.widget.icursor() == 0:
            return None
        
        # Блокируем все остальное
        self.dialog.bell()
        return "break"
    
    def increment_number(self, entry_widget: tk.Entry, delta: float):
        """Инкремент чисел стрелками"""
        try:
            val = float(entry_widget.get() or 0)
            new_val = round(val + delta, 2)
            
            # Ограничения
            if entry_widget == self.floor_entry:
                new_val = max(0.1, min(1000, new_val))
            elif entry_widget == self.wall_entry:
                new_val = max(0.0, min(500, new_val))
            
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, str(new_val))
            return "break"
        except:
            return "break"
    
    # --------------------------------------
    # ✅ СОХРАНЕНИЕ (ПОЛНОЕ)
    # --------------------------------------
    def save(self, event=None):
        """Сохранение с полной валидацией"""
        try:
            # Получение данных
            name = self.name_var.get().strip()
            try:
                floor = float(self.floor_entry.get())
                wall = float(self.wall_entry.get())
            except ValueError:
                messagebox.showerror("Ошибка", "Введите корректные числа для площадей", parent=self.dialog)
                return False
            
            repair_class = self.class_var.get()
            
            # Валидация
            if repair_class not in REPAIR_CLASSES:
                messagebox.showerror("Ошибка", "Выберите класс ремонта", parent=self.dialog)
                return False
            
            if floor < 0.1 or floor > 1000:
                messagebox.showerror("Ошибка", "Площадь пола: 0.1-1000 м²", parent=self.dialog)
                return False
            
            if wall < 0 or wall > 500:
                messagebox.showerror("Ошибка", "Площадь стен: 0-500 м²", parent=self.dialog)
                return False
            
            # Автогенерация имени
            if not name:
                app = self.get_parent_app()
                count = len(getattr(app, 'room_manager', type('obj', (), {'rooms': []})()).rooms) if app else 0
                name = f"Помещение {count + 1}"
            
            # Результат
            total_area = floor + wall * 0.5
            self.result = {
                'name': name,
                'floor': round(floor, 2),
                'wall': round(wall, 2),
                'class': repair_class,
                'total_area': round(total_area, 2)
            }
            
            # Закрытие
            self.dialog.quit()
            self.dialog.destroy()
            
            # Подтверждение
            action = "обновлено" if self.room else "добавлено"
            messagebox.showinfo("Успех", f"Помещение '{name}' {action}!\nПлощадь: {total_area:.1f} м²")
            return True
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка сохранения:\n{str(e)}", parent=self.dialog)
            print(f"Save error: {traceback.format_exc()}")
            return False
    
    def cancel(self, event=None):
        """Отмена"""
        self.result = None
        self.dialog.quit()
        self.dialog.destroy()
    
    # --------------------------------------
    # ✅ ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # --------------------------------------
    def get_parent_app(self):
        """Поиск родительского приложения"""
        current = self.parent_ref
        visited = set()
        while current and id(current) not in visited:
            visited.add(id(current))
            if hasattr(current, 'room_manager') and hasattr(current, 'current_project'):
                return current
            try:
                current = current.master
            except:
                break
        return None
    
    def center_dialog(self):
        """Центрирование"""
        self.dialog.update_idletasks()
        sw, sh = self.dialog.winfo_screenwidth(), self.dialog.winfo_screenheight()
        ww, wh = self.dialog.winfo_width(), self.dialog.winfo_height()
        x, y = (sw - ww) // 2, (sh - wh) // 2
        self.dialog.geometry(f"+{x}+{y}")
    
    def set_initial_focus(self):
        """Фокус на первое поле"""
        if hasattr(self, 'name_entry'):
            self.name_entry.focus_set()
            self.select_all_text(self.name_entry)
    
    def select_all_text(self, entry_widget: tk.Entry):
        """Выделение текста"""
        try:
            entry_widget.select_range(0, tk.END)
            return "break"
        except:
            pass
    
    def on_class_selected(self, event=None):
        """Автосохранение при выборе класса"""
        selected = self.class_var.get()
        if selected in REPAIR_CLASSES:
            self.dialog.after(200, self.save)
    
    def highlight_button(self, button: tk.Button, btn_type: str):
        """Подсветка кнопки"""
        try:
            original_bg = "#27ae60" if btn_type == "save" else "#e74c3c"
            button.configure(relief=tk.SUNKEN, bg="#2ecc71" if btn_type == "save" else "#e74c3c")
            self.dialog.after(100, lambda: button.configure(relief=tk.RAISED, bg=original_bg))
        except:
            pass


# --------------------------------------
# ✅ ТЕСТОВЫЙ БЛОК (ПОЛНЫЙ)
# --------------------------------------
if __name__ == "__main__":
    def run_tests():
        """Запуск всех тестов"""
        root = tk.Tk()
        root.withdraw()
        
        print("🎯 RoomDialog v1.1 - Тестирование")
        print("=" * 50)
        
        class MockRoom:
            def __init__(self, name="Тест", floor=20.0, wall=30.0, repair_class="Люкс"):
                self.name = name
                self.floor_area = floor
                self.wall_area = wall
                self.repair_class = repair_class
        
        # Тест 1: Добавление
        print("\n1️⃣ Добавление:")
        dialog1 = RoomDialog(root, "➕ Добавить", "Москва")
        root.wait_window(dialog1.dialog)
        print(f"   Результат: {dialog1.result}")
        
        # Тест 2: Редактирование
        print("\n2️⃣ Редактирование:")
        room = MockRoom()
        dialog2 = RoomDialog(root, "✏️ Редактировать", "СПб", room)
        root.wait_window(dialog2.dialog)
        print(f"   Результат: {dialog2.result}")
        
        # Тест 3: Отмена
        print("\n3️⃣ Отмена:")
        dialog3 = RoomDialog(root, "🧪 Отмена", "Сочи")
        root.wait_window(dialog3.dialog)
        print(f"   Результат: {dialog3.result} (None = успех)")
        
        root.destroy()
        print("\n✅ Тестирование завершено!")
    
    run_tests()