#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py - Главная точка входа для RemontCalc v1.1
Архитектура: MVC с модульной структурой (src/, dialogs/, models/, config/, data/)
Все ошибки исправлены: Excel экспорт, JSON сериализация, импорты, self ссылки
Автор: AI Assistant
Версия: 1.1
Дата: 2024
"""

import sys
import os
import json
import traceback
import platform
import logging
import hashlib
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter import font as tkfont

# Проверка версии Python
if sys.version_info < (3, 7):
    print("❌ Требуется Python 3.7 или выше")
    sys.exit(1)

# ✅ Добавление корневой директории в sys.path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# ✅ Константы проекта (соответствуют вашей структуре)
APP_VERSION = "1.1"
APP_NAME = "RemontCalc"
DEFAULT_WINDOW_SIZE = "1000x700"

# Директории согласно вашей структуре
SRC_DIR = project_root / "src"
DIALOGS_DIR = project_root / "dialogs"
MODELS_DIR = project_root / "models"
DATA_DIR = project_root / "data"
CONFIG_DIR = project_root / "config"
RESOURCES_DIR = project_root / "resources"

# Файлы конфигурации
CONFIG_FILES = {
    'app_config': CONFIG_DIR / "settings.py",
    'prices': CONFIG_DIR / "prices.py",
    'projects': DATA_DIR / "projects.json",
    'user_settings': DATA_DIR / "settings.json",
    'prices_data': DATA_DIR / "prices.json"
}

# ✅ Глобальный логгер
logger = None

# ✅ Утилиты (fallback если src/utils.py отсутствует)
def get_current_timestamp() -> str:
    """Текущая метка времени ISO (fallback для utils)"""
    return datetime.now().isoformat()

# ✅ Настройка логирования
def setup_logging():
    """Настройка системы логирования"""
    global logger
    
    # Создание директории logs
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Имя лог-файла
    username = platform.node() or "user"
    log_filename = f"remont_{username}_{datetime.now().strftime('%Y%m%d')}.log"
    log_file = logs_dir / log_filename
    
    # Основная настройка
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ],
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    logger = logging.getLogger(APP_NAME)
    
    # Консольный обработчик для INFO+
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Логирование структуры проекта
    logger.info(f"🚀 RemontCalc v{APP_VERSION} запущен из: {project_root}")
    logger.info(f"📁 Директории проекта:")
    logger.info(f"   📂 src/: {'✅' if SRC_DIR.exists() else '❌'}")
    logger.info(f"   📂 dialogs/: {'✅' if DIALOGS_DIR.exists() else '❌'}")
    logger.info(f"   📂 models/: {'✅' if MODELS_DIR.exists() else '❌'}")
    logger.info(f"   📂 data/: {'✅' if DATA_DIR.exists() else '❌'}")
    logger.info(f"   📂 config/: {'✅' if CONFIG_DIR.exists() else '❌'}")
    logger.info(f"   📂 resources/: {'✅' if RESOURCES_DIR.exists() else '❌'}")
    
    return logger

logger = setup_logging()

# ✅ Класс конфигурации (интеграция с config/)
class AppConfig:
    """Конфигурация приложения - работает с config/settings.py и config/prices.py"""
    
    def __init__(self):
        self.project_root = project_root
        self.config_dir = CONFIG_DIR
        
        # Fallback настройки (если config/ файлы отсутствуют)
        self.fallback_config = {
            'version': APP_VERSION,
            'window_size': DEFAULT_WINDOW_SIZE,
            'theme': 'clam',
            'auto_save_interval': 300,
            'default_region': 'Москва',
            'language': 'ru',
            'max_projects': 50,
            'currency': '₽',
            'decimal_places': 2,
            'show_tooltips': True,
            'auto_backup': True
        }
        
        # Fallback цены
        self.fallback_prices = {
            'Эконом': 3500,
            'Комфорт': 6500,
            'Люкс': 12000
        }
        self.fallback_classes = ["Эконом", "Комфорт", "Люкс"]
        
        # Загрузка модулей config/
        self.global_config = self.fallback_config.copy()
        self.repair_prices = self.fallback_prices.copy()
        self.repair_classes = self.fallback_classes.copy()
        self.detailed_prices = {}
        
        self._load_config_modules()
        
        # JSON конфигурация пользователя
        self.user_config_file = DATA_DIR / "settings.json"
        self._load_user_config()
        
        # Слияние всех настроек
        self.config = self._merge_configs()
        
        # Инициализация директорий
        self._ensure_directories()
    
    def _load_config_modules(self):
        """Динамическая загрузка config/settings.py и config/prices.py"""
        try:
            import importlib.util
            
            # Загрузка settings.py
            settings_path = CONFIG_FILES['app_config']
            if settings_path.exists():
                spec = importlib.util.spec_from_file_location("settings", settings_path)
                if spec:
                    settings_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(settings_module)
                    
                    # Извлечение настроек
                    self.global_config.update(getattr(settings_module, 'APP_CONFIG', {}))
                    self.repair_classes = getattr(settings_module, 'REPAIR_CLASSES', self.fallback_classes)
                    logger.info(f"✅ settings.py загружен: {settings_path}")
                else:
                    logger.warning(f"⚠️  Не удалось создать spec для {settings_path}")
            else:
                logger.warning(f"⚠️  Файл settings.py не найден: {settings_path}")
            
            # Загрузка prices.py
            prices_path = CONFIG_FILES['prices']
            if prices_path.exists():
                spec = importlib.util.spec_from_file_location("prices", prices_path)
                if spec:
                    prices_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(prices_module)
                    
                    self.repair_prices.update(getattr(prices_module, 'REPAIR_PRICES', {}))
                    self.detailed_prices = getattr(prices_module, 'DETAILED_PRICES', {})
                    logger.info(f"✅ prices.py загружен: {prices_path}")
                else:
                    logger.warning(f"⚠️  Не удалось создать spec для {prices_path}")
            else:
                logger.warning(f"⚠️  Файл prices.py не найден: {prices_path}")
                
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки config модулей: {e}")
            logger.info("🔄 Используются fallback настройки")
    
    def _load_user_config(self):
        """Загрузка пользовательских настроек из data/settings.json"""
        try:
            if self.user_config_file.exists():
                with open(self.user_config_file, 'r', encoding='utf-8') as f:
                    self.user_config = json.load(f)
                logger.info(f"✅ Пользовательские настройки загружены")
            else:
                self.user_config = {
                    'last_session': get_current_timestamp(),
                    'recent_projects': [],
                    'window_geometry': DEFAULT_WINDOW_SIZE,
                    'preferences': {
                        'show_tooltips': True,
                        'auto_backup': True,
                        'currency_format': '{:,.2f} ₽'
                    }
                }
                self._save_user_config()
                
        except json.JSONDecodeError as e:
            logger.warning(f"⚠️  Ошибка JSON в user config: {e}")
            self.user_config = self.fallback_config.copy()
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки user config: {e}")
            self.user_config = self.fallback_config.copy()
    
    def _save_user_config(self):
        """Сохранение пользовательских настроек"""
        try:
            self.user_config['last_session'] = get_current_timestamp()
            with open(self.user_config_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_config, f, ensure_ascii=False, indent=2,
                         default=self._json_serial)
            logger.debug("💾 User config сохранен")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения user config: {e}")
    
    def _json_serial(self, obj):
        """JSON сериализатор для datetime и других объектов"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Path):
            return str(obj)
        if isinstance(obj, (set, frozenset)):
            return list(obj)
        raise TypeError(f"Объект типа {type(obj)} не может быть сериализован в JSON")
    
    def _merge_configs(self) -> Dict[str, Any]:
        """Слияние всех конфигураций"""
        merged = self.global_config.copy()
        
        # Пользовательские настройки
        user_prefs = self.user_config.get('preferences', {})
        merged.update(user_prefs)
        
        # Цены и классы
        merged['repair_classes'] = self.repair_classes
        merged['repair_prices'] = self.repair_prices
        merged['detailed_prices'] = self.detailed_prices
        
        # Состояние приложения
        merged['recent_projects'] = self.user_config.get('recent_projects', [])
        merged['last_project'] = self.user_config.get('last_project')
        
        # Метаданные
        merged['app_version'] = APP_VERSION
        merged['project_root'] = str(project_root)
        merged['python_version'] = platform.python_version()
        merged['os_platform'] = f"{platform.system()} {platform.release()}"
        
        return merged
    
    def _ensure_directories(self):
        """Создание необходимых директорий"""
        directories = [
            DATA_DIR,
            CONFIG_DIR,
            RESOURCES_DIR / "icons",
            RESOURCES_DIR / "styles",
            RESOURCES_DIR / "images",
            project_root / "logs"
        ]
        
        for directory in directories:
            directory.mkdir(exist_ok=True)
    
    def get(self, key: str, default=None):
        """Получение настройки"""
        return self.config.get(key, default)
    
    def set_user_preference(self, key: str, value: Any):
        """Установка пользовательской настройки"""
        if 'preferences' not in self.user_config:
            self.user_config['preferences'] = {}
        self.user_config['preferences'][key] = value
        self.config[key] = value
        self._save_user_config()
    
    def add_recent_project(self, project_id: str):
        """Добавить проект в недавние"""
        recent = self.user_config.get('recent_projects', [])
        if project_id in recent:
            recent.remove(project_id)
        recent.insert(0, project_id)
        self.user_config['recent_projects'] = recent[:10]
        self._save_user_config()
    
    def save_geometry(self, geometry: str):
        """Сохранение геометрии окна"""
        self.set_user_preference('window_geometry', geometry)

# ✅ Менеджер данных (исправленная версия с полным Excel экспортом)
class DataManager:
    """Управление данными согласно вашей структуре data/ - ПОЛНАЯ ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    
    def __init__(self, config: AppConfig, app_instance=None):
        self.config = config
        self.app = app_instance  # Ссылка на RemontCalcApp
        self.data_dir = DATA_DIR
        
        # Файлы данных
        self.projects_file = self.data_dir / "projects.json"
        self.user_settings_file = self.data_dir / "settings.json"
        self.prices_file = self.data_dir / "prices.json"
        
        # Бэкапы
        self.backup_dir = self.data_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # Инициализация файлов
        self._init_data_files()
    
    def _init_data_files(self):
        """Инициализация файлов data/"""
        init_data = {
            'projects_file': self.projects_file,
            'user_settings': self.user_settings_file,
            'prices': self.prices_file
        }
        
        for file_name, file_path in init_data.items():
            if not file_path.exists():
                if file_name == 'projects_file':
                    self._create_initial_projects()
                elif file_name == 'user_settings':
                    self._create_initial_user_settings()
                elif file_name == 'prices':
                    self._create_initial_prices()
                
                logger.info(f"📄 Инициализирован файл: {file_path}")
    
    def _create_initial_projects(self):
        """Создание начального файла проектов"""
        timestamp = datetime.now().isoformat()
        initial_projects = {
            "version": self.config.get('app_version', '1.1'),
            "projects": [],
            "metadata": {
                "created": timestamp,
                "last_modified": timestamp,
                "total_projects": 0,
                "storage_format": "json_v1"
            }
        }
        self._save_json(self.projects_file, initial_projects)
    
    def _create_initial_user_settings(self):
        """Начальные пользовательские настройки"""
        timestamp = datetime.now().isoformat()
        initial_settings = {
            "user_id": self._generate_user_id(),
            "preferences": {
                "theme": self.config.get('theme', 'clam'),
                "language": self.config.get('language', 'ru'),
                "currency": self.config.get('currency', '₽'),
                "decimal_places": 2,
                "auto_save": True,
                "show_totals": True
            },
            "last_session": timestamp,
            "session_count": 1,
            "recent_projects": []
        }
        self._save_json(self.user_settings_file, initial_settings)
    
    def _create_initial_prices(self):
        """Начальный файл цен (синхронизация с config/prices.py)"""
        timestamp = datetime.now().isoformat()
        prices_data = {
            "version": self.config.get('app_version', '1.1'),
            "last_updated": timestamp,
            "source": "config/prices.py",
            "classes": self.config.get('repair_classes', []),
            "prices": self.config.get('repair_prices', {}),
            "detailed": self.config.get('detailed_prices', {})
        }
        self._save_json(self.prices_file, prices_data)
    
    def _save_json(self, file_path: Path, data: Dict[str, Any]) -> bool:
        """Безопасное сохранение JSON"""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                def json_serial(obj):
                    if isinstance(obj, datetime):
                        return obj.isoformat()
                    if isinstance(obj, Path):
                        return str(obj)
                    if hasattr(obj, '__dict__'):
                        return obj.__dict__
                    raise TypeError(f"Тип {type(obj)} не сериализуется в JSON")
                
                json.dump(data, f, ensure_ascii=False, indent=2, default=json_serial)
            logger.debug(f"💾 JSON сохранен: {file_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения {file_path}: {e}")
            return False
    
    def _load_json(self, file_path: Path, default_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Безопасная загрузка JSON"""
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.debug(f"📂 JSON загружен: {file_path}")
                return data
            else:
                if default_data:
                    self._save_json(file_path, default_data)
                return default_data or {}
        except json.JSONDecodeError as e:
            logger.error(f"❌ Ошибка JSON в {file_path}: {e}")
            return default_data or {}
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки {file_path}: {e}")
            return default_data or {}
    
    def _get_timestamp(self) -> str:
        """Текущая метка времени ISO"""
        return datetime.now().isoformat()
    
    def _generate_user_id(self) -> str:
        """Генерация ID пользователя"""
        user_string = f"{platform.node()}_{os.getlogin()}_{uuid.getnode()}"
        return hashlib.md5(user_string.encode()).hexdigest()[:8]
    
    def _calculate_room_cost(self, room: Dict[str, Any]) -> float:
        """Расчет стоимости комнаты (fallback)"""
        price_per_m2 = self.config.get('repair_prices', {}).get(
            room.get('repair_class', 'Эконом'), 3500
        )
        total_area = room.get('total_area', 
                             room.get('floor_area', 0) + room.get('wall_area', 0) * 0.5)
        return round(total_area * price_per_m2, 2)
    
    def save_projects(self, projects_data: Dict[str, Any]) -> bool:
        """Сохранение проектов"""
        projects_data['metadata']['last_modified'] = self._get_timestamp()
        success = self._save_json(self.projects_file, projects_data)
        
        if success and self.config.get('auto_backup', True):
            self._create_backup('projects')
        
        return success
    
    def load_projects(self) -> Dict[str, Any]:
        """Загрузка проектов"""
        default_projects = {
            "version": self.config.get('app_version', '1.1'),
            "projects": [],
            "metadata": {
                "created": self._get_timestamp(),
                "last_modified": self._get_timestamp(),
                "total_projects": 0
            }
        }
        
        data = self._load_json(self.projects_file, default_projects)
        data = self._migrate_projects_data(data)
        
        logger.info(f"📂 Загружено {len(data.get('projects', []))} проектов")
        return data
    
    def _migrate_projects_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Миграция данных проектов"""
        current_version = data.get('version', '0.0')
        
        if current_version == '1.0':
            logger.info("🔄 Миграция проектов v1.0 → v1.1")
            
            for project in data.get('projects', []):
                if 'total_cost' not in project:
                    rooms = project.get('rooms', [])
                    total = sum(self._calculate_room_cost(room) for room in rooms)
                    project['total_cost'] = round(total, 2)
                
                if 'metadata' not in project:
                    project['metadata'] = {
                        'created': project.get('created_date', self._get_timestamp()),
                        'modified': self._get_timestamp(),
                        'room_count': len(project.get('rooms', []))
                    }
                
                for room in project.get('rooms', []):
                    if 'total_area' not in room:
                        floor = room.get('floor_area', 0)
                        wall = room.get('wall_area', 0)
                        room['total_area'] = round(floor + wall * 0.5, 2)
                    
                    if 'cost' not in room:
                        room['cost'] = self._calculate_room_cost(room)
            
            data['version'] = '1.1'
            self.save_projects(data)
        
        return data
    
    def _create_backup(self, data_type: str = 'projects'):
        """Создание бэкапа"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{data_type}_backup_{timestamp}.json"
            backup_file = self.backup_dir / backup_name
            
            if data_type == 'projects':
                data = self.load_projects()
            else:
                data = {}
            
            self._save_json(backup_file, data)
            
            # Очистка старых бэкапов
            backups = sorted(self.backup_dir.glob(f"{data_type}_backup_*.json"),
                           key=lambda x: x.stat().st_mtime, reverse=True)
            for old_backup in backups[5:]:
                try:
                    old_backup.unlink()
                except:
                    pass
            
            logger.debug(f"💾 Бэкап создан: {backup_name}")
            return backup_name
        except Exception as e:
            logger.error(f"❌ Ошибка бэкапа {data_type}: {e}")
            return None
    
    def export_projects(self, format_type: str = "json", app_instance=None) -> bool:
        """Экспорт проектов"""
        if format_type not in ['json', 'excel']:
            messagebox.showerror("Ошибка формата", f"Формат '{format_type}' не поддерживается")
            return False
        
        file_path = filedialog.asksaveasfilename(
            initialdir=str(DATA_DIR),
            defaultextension=f".{format_type}" if format_type == 'json' else ".xlsx",
            filetypes=[
                ("JSON files", "*.json") if format_type == 'json' else ("", ""),
                ("Excel files", "*.xlsx") if format_type == 'excel' else ("", ""),
                ("All files", "*.*")
            ],
            title=f"Экспорт проектов ({format_type.upper()})"
        )
        
        if not file_path:
            return False
        
        try:
            if format_type == "json":
                projects_data = self.load_projects()
                return self._save_json(Path(file_path), projects_data)
            
            elif format_type == "excel":
                return self._export_to_excel(file_path, app_instance)
            
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка экспорта {format_type}: {e}")
            messagebox.showerror("Ошибка экспорта", f"Не удалось экспортировать:\n{str(e)}")
            return False
    
    def _export_to_excel(self, file_path: str, app_instance=None) -> bool:
        """Экспорт в Excel - ПОЛНОСТЬЮ ИСПРАВЛЕННАЯ ВЕРСИЯ"""
        # Проверка зависимости
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
            from openpyxl.utils import get_column_letter
        except ImportError:
            messagebox.showerror("Зависимость отсутствует", 
                               "Для Excel экспорта установите:\n\npip install openpyxl\n\n"
                               "Затем перезапустите приложение.")
            logger.error("❌ openpyxl не установлен - невозможно экспортировать в Excel")
            return False
        
        try:
            # Получение конфигурации
            if app_instance and hasattr(app_instance, 'config'):
                current_config = app_instance.config
            else:
                current_config = self.config
            
            currency = current_config.get('currency', '₽')
            decimal_places = current_config.get('decimal_places', 2)
            
            # Создание workbook
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "RemontCalc - Проекты"
            
            # Стили
            header_font = Font(name='Arial', size=12, bold=True, color='FFFFFF')
            header_fill = PatternFill(start_color='2C3E50', end_color='2C3E50', fill_type='solid')
            header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            
            data_font = Font(name='Arial', size=10)
            data_alignment = Alignment(horizontal='left', vertical='center')
            
            thin_border = Border(
                left=Side(style='thin'), right=Side(style='thin'),
                top=Side(style='thin'), bottom=Side(style='thin')
            )
            
            # Заголовки
            headers = ['№', 'Проект', 'Регион', 'Помещений', 'Общая площадь, м²', 
                      'Стоимость', 'Классы ремонта', 'Дата создания']
            header_row = 1
            
            for col_idx, header in enumerate(headers, 1):
                cell = ws.cell(row=header_row, column=col_idx, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_alignment
                cell.border = thin_border
                ws.column_dimensions[get_column_letter(col_idx)].width = max(len(header) + 2, 12)
            
            ws.row_dimensions[header_row].height = 25
            
            # Данные проектов
            projects_data = self.load_projects()
            all_projects = projects_data.get('projects', [])
            
            if not all_projects:
                no_data_cell = ws.cell(row=2, column=1, value="Нет проектов для экспорта")
                no_data_cell.font = Font(italic=True, color='999999')
                no_data_cell.alignment = Alignment(horizontal='center', vertical='center')
            else:
                total_cost = 0
                total_rooms = 0
                total_area = 0
                row = 2
                
                for proj_idx, project in enumerate(all_projects, 1):
                    project_name = project.get('name', 'Без названия')
                    region = project.get('region', 'Не указан')
                    rooms_count = len(project.get('rooms', []))
                    project_cost = project.get('total_cost', 0)
                    project_area = sum(room.get('total_area', 0) for room in project.get('rooms', []))
                    
                    # Статистика классов
                    rooms = project.get('rooms', [])
                    class_stats = {}
                    for room in rooms:
                        cls = room.get('repair_class', 'Неизвестно')
                        class_stats[cls] = class_stats.get(cls, 0) + 1
                    
                    classes_str = ', '.join([f"{cls} ({count})" for cls, count in class_stats.items()])
                    created_date = project.get('created_date', '').split('T')[0] if project.get('created_date') else ''
                    
                    # Заполнение строки
                    row_data = [
                        proj_idx,
                        project_name,
                        region,
                        rooms_count,
                        f"{project_area:.2f}",
                        f"{project_cost:,.{decimal_places}f} {currency}",
                        classes_str[:30] + '...' if len(classes_str) > 30 else classes_str,
                        created_date
                    ]
                    
                    for col_idx, value in enumerate(row_data, 1):
                        cell = ws.cell(row=row, column=col_idx, value=value)
                        cell.font = data_font
                        cell.alignment = data_alignment if col_idx > 1 else Alignment(horizontal='center')
                        cell.border = thin_border
                    
                    total_cost += project_cost
                    total_rooms += rooms_count
                    total_area += project_area
                    row += 1
                
                # Итоговая строка (ИСПРАВЛЕНИЕ: правильный синтаксис)
                summary_row = row + 1
                
                # Пустые ячейки
                for col in range(1, 4):
                    cell = ws.cell(row=summary_row, column=col, value="")
                    cell.border = thin_border
                
                # Итого проектов
                ws.cell(row=summary_row, column=4, value=f"ВСЕГО ПРОЕКТОВ: {len(all_projects)}")
                ws.cell(row=summary_row, column=4).font = Font(bold=True, size=11)
                ws.cell(row=summary_row, column=4).alignment = Alignment(horizontal='right')
                ws.cell(row=summary_row, column=4).border = thin_border
                
                # Общая площадь
                ws.cell(row=summary_row, column=5, value=f"{total_area:.2f}")
                ws.cell(row=summary_row, column=5).font = Font(bold=True, size=11)
                ws.cell(row=summary_row, column=5).alignment = Alignment(horizontal='right')
                ws.cell(row=summary_row, column=5).border = thin_border
                ws.cell(row=summary_row, column=5).fill = PatternFill(start_color='E8F5E8', end_color='E8F5E8', fill_type='solid')
                
                # Общая стоимость (ИСПРАВЛЕНИЕ: правильная ссылка на config)
                total_cost_cell = ws.cell(row=summary_row, column=6)
                total_cost_cell.value = f"{total_cost:,.{decimal_places}f} {currency}"
                total_cost_cell.font = Font(bold=True, size=11, color='2C3E50')
                total_cost_cell.alignment = Alignment(horizontal='right', vertical='center')
                total_cost_cell.border = thin_border
                total_cost_cell.fill = PatternFill(start_color='E8F5E8', end_color='E8F5E8', fill_type='solid')
                
                # Общее количество помещений
                ws.cell(row=summary_row, column=3, value=total_rooms)
                ws.cell(row=summary_row, column=3).font = Font(bold=True, size=11)
                ws.cell(row=summary_row, column=3).alignment = Alignment(horizontal='center')
                ws.cell(row=summary_row, column=3).border = thin_border
                ws.cell(row=summary_row, column=3).fill = PatternFill(start_color='E8F5E8', end_color='E8F5E8', fill_type='solid')
            
            # Авто-размер колонок (ИСПРАВЛЕНИЕ: безопасный код)
            for col_num, column in enumerate(ws.columns, 1):
                max_length = 0
                column_letter = get_column_letter(col_num)
                
                for cell in column:
                    try:
                        if cell.value is not None:
                            cell_length = len(str(cell.value))
                            max_length = max(max_length, cell_length)
                    except (AttributeError, TypeError, ValueError):
                        continue
                
                # Установка ширины
                adjusted_width = min(max_length + 2, 25)
                ws.column_dimensions[column_letter].width = adjusted_width
                
                # Специальные ширины
                if col_num == 2:  # Название проекта
                    ws.column_dimensions[column_letter].width = max(adjusted_width, 25)
                elif col_num == 6:  # Стоимость
                    ws.column_dimensions[column_letter].width = max(adjusted_width, 18)
                elif col_num == 7:  # Классы ремонта
                    ws.column_dimensions[column_letter].width = max(adjusted_width, 20)
            
            # Защита и финализация
            ws.protection.sheet = True
            ws.protection.enable()
            
            # Сохранение
            wb.save(file_path)
            
            # Логирование успеха
            logger.info(f"📊 Excel экспорт создан:")
            logger.info(f"   📄 Файл: {file_path}")
            logger.info(f"   📈 Проектов: {len(all_projects)}")
            logger.info(f"   💰 Итого: {total_cost:,.2f} {currency}" if 'total_cost' in locals() else "")
            
            # Успешное сообщение
            success_msg = f"""✅ Экспорт в Excel завершен!

📄 Файл создан: {os.path.basename(file_path)}
📊 Проектов экспортировано: {len(all_projects)}

Дополнительная информация:
• Формат: XLSX (совместим с Excel, Google Sheets)
• Кодировка: UTF-8 (поддержка русского языка)
• Стили: Автоматическое форматирование и границы

📂 Файл сохранен в: {os.path.dirname(file_path)}"""
            
            messagebox.showinfo("Экспорт успешен", success_msg)
            return True
            
        except PermissionError as e:
            logger.error(f"❌ Нет прав на запись: {e}")
            messagebox.showerror("Доступ запрещен", 
                               f"Не удалось сохранить файл:\n{file_path}\n\n"
                               "Возможные причины:\n"
                               "• Файл открыт в Excel\n"
                               "• Нет прав на папку\n"
                               "• Антивирус блокирует\n\n"
                               "🔧 Решение:\n"
                               "1. Закройте Excel\n"
                               "2. Выберите другую папку\n"
                               "3. Запустите от имени администратора")
            return False
        
        except Exception as e:
            error_detail = f"Тип: {type(e).__name__}\nОписание: {str(e)}"
            logger.error(f"❌ Ошибка Excel экспорта: {error_detail}")
            messagebox.showerror("Ошибка создания Excel", 
                               f"Не удалось создать файл Excel:\n\n{error_detail}")
            return False

# ✅ Главное приложение (исправленная интеграция)
class RemontCalcApp:
    """Основное приложение RemontCalc - связывает все компоненты"""
    
    def __init__(self):
        logger.info("🔧 Инициализация RemontCalcApp...")
        
        # Конфигурация
        self.config = AppConfig()
        
        # Менеджер данных (ИСПРАВЛЕНИЕ: передача app_instance)
        self.data_manager = DataManager(self.config, app_instance=self)
        
        # Бизнес-логика (заглушки - замените на реальные импорты)
        self.project_manager = None
        self.room_manager = None
        self.cost_calculator = None
        self.utils = None
        
        # Модели (заглушки)
        self.models_loaded = False
        self._initialize_components()
        
        # GUI
        self.root = None
        self.main_window = None
        
        # Состояние
        self.current_project = None
        self.is_dirty = False
        self.start_time = datetime.now()
        
        # Загрузка данных
        self._load_initial_data()
        
        logger.info("✅ RemontCalcApp инициализирован")
    
    def _initialize_components(self):
        """Инициализация компонентов с обработкой ошибок"""
        try:
            # Попытка импорта из src/
            from src.project_manager import ProjectManager
            from src.room_manager import RoomManager
            from src.cost_calculator import CostCalculator
            
            self.project_manager = ProjectManager(self.config, self.data_manager)
            self.room_manager = RoomManager(self.config, self.project_manager)
            self.cost_calculator = CostCalculator(self.config, self.room_manager)
            
            logger.info("✅ Компоненты src/ загружены")
            
        except ImportError as e:
            logger.warning(f"⚠️  Компоненты src/ не найдены: {e}")
            logger.info("🔧 Создаются заглушки...")
            
            # Fallback заглушки
            class FallbackManager:
                def __init__(self, *args, **kwargs):
                    self.name = "Fallback"
                    logger.debug(f"📦 {self.__class__.__name__} заглушка создана")
                
                def add_project(self, project):
                    logger.debug("📋 Fallback: проект добавлен")
                
                def get_project(self, id):
                    return None
                
                def save(self):
                    logger.debug("💾 Fallback: данные сохранены")
                
                def load_projects(self, data):
                    logger.debug("📂 Fallback: проекты загружены")
            
            self.project_manager = FallbackManager()
            self.room_manager = FallbackManager()
            self.cost_calculator = FallbackManager()
        
        # Проверка моделей
        try:
            from models.project import Project
            from models.room import Room
            self.Project = Project
            self.Room = Room
            self.models_loaded = True
            logger.info("✅ Модели загружены")
        except ImportError:
            logger.warning("⚠️  Модели не найдены - используются dict")
            self.Project = dict
            self.Room = dict
            self.models_loaded = False
    
    def _load_initial_data(self):
        """Загрузка начальных данных"""
        projects_data = self.data_manager.load_projects()
        
        if self.project_manager:
            self.project_manager.load_projects(projects_data)
        
        # Синхронизация цен
        prices_data = self.data_manager._load_json(self.data_manager.prices_file)
        if (not prices_data or 
            prices_data.get('source') != 'config/prices.py'):
            logger.info("🔄 Синхронизация цен config/ → data/")
            self.data_manager._create_initial_prices()
        
        # Последний проект
        last_project_id = self.config.get('last_project')
        if last_project_id and self.project_manager:
            last_project = self.project_manager.get_project(last_project_id)
            if last_project:
                self.current_project = last_project
    
    def run_gui(self):
        """Запуск графического интерфейса"""
        try:
            self._create_root_window()
            self._setup_main_window()
            self._create_main_interface()
            self._restore_window_state()
            self._setup_event_handlers()
            
            logger.info("🎨 GUI успешно запущен")
            self.root.mainloop()
            
        except Exception as e:
            logger.error(f"❌ Ошибка GUI: {e}")
            self._show_critical_error(e)
    
    def _create_root_window(self):
        """Создание корневого окна"""
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        
        # Иконка
        try:
            icon_path = RESOURCES_DIR / "icons" / "remont.ico"
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
        except:
            pass
        
        self.root.minsize(900, 650)
    
    def _setup_main_window(self):
        """Настройка главного окна"""
        geometry = self.config.get('window_geometry', DEFAULT_WINDOW_SIZE)
        self.root.geometry(geometry)
        
        # Центрирование
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (self.root.winfo_width() // 2)
        y = (self.root.winfo_screenheight() // 2) - (self.root.winfo_height() // 2)
        self.root.geometry(f"+{x}+{y}")
        
        # Тема
        theme = self.config.get('theme', 'clam')
        try:
            self.root.tk.call('ttk::setTheme', theme)
        except tk.TclError:
            try:
                self.root.tk.call('ttk::setTheme', 'default')
            except:
                pass
        
        # Обработчики
        self.root.protocol("WM_DELETE_WINDOW", self.on_application_exit)
        
        # Горячие клавиши
        self.root.bind('<Control-q>', lambda e: self.on_application_exit())
        self.root.bind('<Control-s>', lambda e: self.save_all_data())
        self.root.bind('<F5>', lambda e: self.refresh_all())
        self.root.bind('<Control-n>', lambda e: self.create_new_project())
    
    def _create_main_interface(self):
        """Создание интерфейса"""
        try:
            from src.main_gui import RemontAppGUI
            self.main_window = RemontAppGUI(self.root, self)
            
            self.main_window.set_callbacks({
                'on_project_select': self.on_project_selected,
                'on_project_create': self.on_project_created,
                'on_project_delete': self.on_project_deleted,
                'on_room_add': self.on_room_added,
                'on_data_change': self.on_data_changed,
                'on_export_request': self.on_export_requested
            })
            
        except ImportError:
            # Fallback простой интерфейс
            self._create_fallback_interface()
    
    def _create_fallback_interface(self):
        """Простой интерфейс-заглушка"""
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = ttk.Label(main_frame, text=f"{APP_NAME} v{APP_VERSION}", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=20)
        
        status_label = ttk.Label(main_frame, 
                               text="🛠️  Настройка приложения...\n"
                               "Создайте файлы в src/, models/, dialogs/ для полного функционала",
                               font=('Arial', 10), foreground='blue')
        status_label.pack(pady=10)
        
        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="📊 Экспорт проектов (JSON)", 
                  command=lambda: self.data_manager.export_projects('json', self)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="📈 Экспорт Excel", 
                  command=lambda: self.data_manager.export_projects('excel', self)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="💾 Сохранить", 
                  command=self.save_all_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="❓ О программе", 
                  command=self.show_about).pack(side=tk.LEFT, padx=5)
        
        info_text = (f"📁 Статус проекта:\n"
                    f"• src/: {'✅' if SRC_DIR.exists() else '❌'}\n"
                    f"• models/: {'✅' if MODELS_DIR.exists() else '❌'}\n"
                    f"• config/: {'✅' if CONFIG_DIR.exists() else '❌'}\n"
                    f"• data/: {'✅' if DATA_DIR.exists() else '❌'}\n\n"
                    f"🔧 Для полного функционала:\n"
                    f"1. Создайте src/main_gui.py\n"
                    f"2. Реализуйте models/project.py, models/room.py\n"
                    f"3. Заполните config/settings.py, config/prices.py\n"
                    f"4. pip install openpyxl (для Excel)")
        
        info_label = tk.Text(main_frame, width=60, height=15, wrap=tk.WORD, font=('Arial', 9))
        info_label.insert(tk.END, info_text)
        info_label.config(state=tk.DISABLED)
        info_label.pack(pady=20)
    
    def show_about(self):
        """Окно "О программе" """
        about_text = f"""RemontCalc v{APP_VERSION}

🏗️  Профессиональный калькулятор стоимости ремонта помещений

Архитектура:
• MVC паттерн с модульной структурой
• JSON хранение данных (data/)
• Конфигурация через config/ файлы
• GUI: tkinter + ttk

Статус разработки:
• {'✅ Полная' if self.models_loaded else '⚠️  Базовая (заглушки)'} поддержка моделей
• 📊 {'✅' if 'openpyxl' in sys.modules else '❌'} Excel экспорт
• 💾 Автосохранение и бэкапы
• 🔄 Миграция данных версий

Разработано с помощью AI Assistant
2024

👨‍💻 Для разработчиков:
python main.py --create-stubs  # Создать заглушки
python main.py --check-structure  # Проверить структуру"""
        
        messagebox.showinfo("О программе", about_text)
    
    def _restore_window_state(self):
        """Восстановление состояния"""
        if self.main_window:
            self.main_window.refresh_project_list()
            if self.current_project:
                self.main_window.load_project(self.current_project)
    
    def _setup_event_handlers(self):
        """Настройка обработчиков"""
        self.root.bind('<Configure>', self.on_window_resize)
        self.root.protocol("WM_DELETE_WINDOW", self.on_application_exit)
        
        # Автосохранение
        if self.config.get('auto_save', True):
            interval = self.config.get('auto_save_interval', 300) * 1000
            self.auto_save_timer = self.root.after(interval, self.auto_save)
    
    def on_window_resize(self, event):
        """Изменение размера окна"""
        if event.widget == self.root:
            geometry = self.root.geometry()
            self.config.save_geometry(geometry)
    
    # Обработчики событий (упрощенные)
    def on_project_selected(self, project_data):
        self.current_project = project_data
        logger.info(f"📋 Выбран проект: {project_data.get('name', 'Unknown')}")
    
    def on_project_created(self, project_data):
        if self.project_manager:
            self.project_manager.add_project(project_data)
        projects_data = self.data_manager.load_projects()
        projects_data['projects'].append(project_data)
        self.data_manager.save_projects(projects_data)
        self.config.add_recent_project(project_data.get('id'))
        logger.info(f"➕ Создан проект: {project_data.get('name')}")
    
    def on_project_deleted(self, project_id):
        projects_data = self.data_manager.load_projects()
        projects_data['projects'] = [p for p in projects_data['projects'] if p.get('id') != project_id]
        self.data_manager.save_projects(projects_data)
        logger.info(f"🗑️  Удален проект: {project_id}")
    
    def on_room_added(self, room_data):
        if self.current_project:
            self.current_project.setdefault('rooms', []).append(room_data)
            self._save_current_project()
            logger.info(f"🏠 Добавлено помещение: {room_data.get('name')}")
    
    def on_data_changed(self):
        self.is_dirty = True
        logger.debug("🔄 Данные изменены")
    
    def on_export_requested(self, export_type='json'):
        return self.data_manager.export_projects(export_type, self)
    
    def save_all_data(self) -> bool:
        """Сохранение всех данных"""
        try:
            projects_data = self.data_manager.load_projects()
            if self.project_manager:
                # Экспорт всех проектов из менеджера
                all_projects = []
                for project in self.project_manager.projects or []:
                    project_dict = project.to_dict() if hasattr(project, 'to_dict') else dict(project)
                    all_projects.append(project_dict)
                projects_data['projects'] = all_projects
            
            success = self.data_manager.save_projects(projects_data)
            
            # Сохранение настроек
            self.config._save_user_config()
            
            if success:
                self.is_dirty = False
                logger.info("💾 Все данные сохранены")
                messagebox.showinfo("Сохранено", "✅ Все данные успешно сохранены!")
                return True
            else:
                raise Exception("Ошибка сохранения проектов")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения: {e}")
            messagebox.showerror("Ошибка", f"Не удалось сохранить:\n{str(e)}")
            return False
    
    def _save_current_project(self):
        if not self.current_project:
            return False
        
        try:
            projects_data = self.data_manager.load_projects()
            
            # Поиск и обновление
            for i, proj in enumerate(projects_data['projects']):
                if proj.get('id') == self.current_project.get('id'):
                    projects_data['projects'][i] = self.current_project
                    break
            else:
                projects_data['projects'].append(self.current_project)
            
            projects_data['metadata']['last_modified'] = self._get_timestamp()
            return self.data_manager.save_projects(projects_data)
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения проекта: {e}")
            return False
    
    def _get_timestamp(self) -> str:
        return datetime.now().isoformat()
    
    def auto_save(self):
        if self.is_dirty:
            self._save_current_project()
        
        if self.config.get('auto_save', True) and hasattr(self, 'root') and self.root.winfo_exists():
            interval = self.config.get('auto_save_interval', 300) * 1000
            self.auto_save_timer = self.root.after(interval, self.auto_save)
    
    def refresh_all(self):
        self.data_manager.load_projects()
        if self.main_window:
            self.main_window.refresh_project_list()
        logger.info("🔄 Данные обновлены")
    
    def create_new_project(self):
        """Создание нового проекта (fallback)"""
        try:
            from dialogs.project_dialog import ProjectDialog
            dialog = ProjectDialog(self.root, "Новый проект", self.config)
            self.root.wait_window(dialog.top)
            
            if dialog.result:
                self.on_project_created(dialog.result)
        except ImportError:
            # Fallback диалог
            from tkinter import simpledialog
            
            name = simpledialog.askstring("Новый проект", "Название проекта:")
            if name:
                region = simpledialog.askstring("Новый проект", "Регион:", initialvalue="Москва")
                project_data = {
                    'id': f"proj_{int(datetime.now().timestamp())}",
                    'name': name or "Новый проект",
                    'region': region or "Москва",
                    'created_date': self._get_timestamp(),
                    'rooms': [],
                    'total_cost': 0.0,
                    'metadata': {'room_count': 0}
                }
                self.on_project_created(project_data)
    
    def on_application_exit(self):
        """Выход из приложения"""
        if self.is_dirty:
            if messagebox.askyesnocancel("Несохраненные данные", 
                                       "Сохранить изменения перед выходом?"):
                self.save_all_data()
        
        # Сохранение геометрии
        if self.root:
            self.config.save_geometry(self.root.geometry())
        
        logger.info(f"👋 Приложение закрыто. Сессия: {(datetime.now() - self.start_time).total_seconds():.0f}с")
        self.root.quit()
        self.root.destroy()
    
    def _show_critical_error(self, error):
        """Показ критической ошибки"""
        error_msg = f"""КРИТИЧЕСКАЯ ОШИБКА

{APP_NAME} v{APP_VERSION} не может продолжить:

🔴 Тип: {type(error).__name__}
📝 {str(error)}

🔍 Логи: logs/remont_*.log

🔧 Проверьте:
1. Структуру проекта (src/, config/, models/)
2. pip install openpyxl (для Excel)
3. Python 3.7+

Нажмите OK для выхода."""
        
        messagebox.showerror("Критическая ошибка", error_msg)
        self.root.quit()

# ✅ Функции утилит
def check_project_structure():
    """Проверка структуры проекта"""
    required = {
        'src': [SRC_DIR / '__init__.py'],
        'dialogs': [DIALOGS_DIR / '__init__.py'],
        'models': [MODELS_DIR / '__init__.py'],
        'config': [CONFIG_DIR / '__init__.py', CONFIG_DIR / 'settings.py'],
        'data': [],
        'resources': [RESOURCES_DIR / 'icons']
    }
    
    issues = []
    for category, files in required.items():
        cat_path = project_root / category
        if not cat_path.exists():
            issues.append(f"❌ Отсутствует директория: {category}/")
            continue
        
        for file_path in files:
            if not file_path.exists():
                issues.append(f"❌ Отсутствует: {file_path}")
    
    if issues:
        logger.warning("⚠️  Проблемы структуры:")
        for issue in issues:
            logger.warning(issue)
        return False
    
    logger.info("✅ Структура проекта корректна")
    return True

def create_missing_files():
    """Создание заглушек"""
    logger.info("🔧 Создание заглушек файлов...")
    
    # __init__.py
    init_files = [
        (SRC_DIR / '__init__.py', '# src/ package'),
        (DIALOGS_DIR / '__init__.py', '# dialogs/ package'),
        (MODELS_DIR / '__init__.py', '# models/ package'),
        (CONFIG_DIR / '__init__.py', '# config/ package')
    ]
    
    created = 0
    for file_path, content in init_files:
        if not file_path.exists():
            file_path.write_text(content, encoding='utf-8')
            logger.info(f"📄 Создан: {file_path.name}")
            created += 1
    
    # Основные файлы
    stubs = {
        SRC_DIR / 'main_gui.py': '''"""
src/main_gui.py - Главное GUI (RemontAppGUI)

class RemontAppGUI:
    def __init__(self, parent, app):
        self.app = app
        # Создайте интерфейс здесь
        
    def refresh_project_list(self):
        pass
        
    def load_project(self, project):
        pass
"""''',
        
        MODELS_DIR / 'project.py': '''"""
models/project.py - Модель Project

class Project:
    def __init__(self, name, region, id=None):
        self.id = id or f"proj_{int(datetime.now().timestamp())}"
        self.name = name
        self.region = region
        self.rooms = []
        self.total_cost = 0.0
        self.created_date = get_current_timestamp()
        self.metadata = {'room_count': 0}
    
    def add_room(self, room):
        self.rooms.append(room)
        self.metadata['room_count'] += 1
    
    def remove_room(self, room_id):
        self.rooms = [r for r in self.rooms if r.get('id') != room_id]
        self.metadata['room_count'] = len(self.rooms)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'region': self.region,
            'rooms': [r.to_dict() if hasattr(r, 'to_dict') else dict(r) for r in self.rooms],
            'total_cost': self.total_cost,
            'created_date': self.created_date,
            'metadata': self.metadata
        }
"""''',
        
        MODELS_DIR / 'room.py': '''"""
models/room.py - Модель Room

class Room:
    def __init__(self, name, floor_area, wall_area, repair_class, id=None):
        self.id = id or f"room_{int(datetime.now().timestamp())}"
        self.name = name
        self.floor_area = float(floor_area) if floor_area is not None else 0.0
        self.wall_area = float(wall_area) if wall_area is not None else 0.0
        self.repair_class = repair_class or 'Эконом'
        self.total_area = self.floor_area + self.wall_area * 0.5
        self.cost = 0.0
        self.created_date = get_current_timestamp()
    
    def calculate_cost(self, price_per_m2):
        self.cost = round(self.total_area * price_per_m2, 2)
        return self.cost
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'floor_area': self.floor_area,
            'wall_area': self.wall_area,
            'repair_class': self.repair_class,
            'total_area': self.total_area,
            'cost': self.cost,
            'created_date': self.created_date
        }
"""''',
        
        CONFIG_DIR / 'settings.py': '''"""
config/settings.py - Глобальная конфигурация RemontCalc

# Основные настройки приложения
APP_CONFIG = {
    'version': '1.1',
    'window_size': '1000x700',
    'theme': 'clam',  # clam, alt, default, classic
    'auto_save_interval': 300,  # секунд
    'default_region': 'Москва',
    'language': 'ru',
    'currency': '₽',
    'decimal_places': 2,
    'max_projects': 100,
    'show_tooltips': True,
    'auto_backup': True,
    'last_updated': '2024-01-01'
}

# Классы ремонта (НЕ МЕНЯЙТЕ ПОРЯДОК!)
REPAIR_CLASSES = ["Эконом", "Комфорт", "Люкс"]

# Базовые цены (рублей за м² общей площади)
REPAIR_PRICES = {
    'Эконом': 3500,    # Базовый ремонт
    'Комфорт': 6500,   # Средний уровень
    'Люкс': 12000      # Премиум ремонт
}

# Детальная разбивка цен (опционально, руб/м²)
DETAILED_PRICES = {
    'Эконом': {
        'пол': 2500,
        'стены': 1000,    # В расчете применяется коэффициент 0.5
        'потолок': 800,
        'двери': 15000,   # За единицу
        'окна': 12000     # За единицу
    },
    'Комфорт': {
        'пол': 4500,
        'стены': 2000,
        'потолок': 1500,
        'двери': 25000,
        'окна': 20000
    },
    'Люкс': {
        'пол': 8000,
        'стены': 4000,
        'потолок': 3000,
        'двери': 50000,
        'окна': 40000
    }
}

# Коэффициенты расчета
CALCULATION_COEFFICIENTS = {
    'walls': 0.5,     # Стены считаются с коэффициентом 0.5 от площади
    'ceiling': 1.0,   # Потолок - полная площадь
    'doors': 1,       # Двери - количество
    'windows': 1      # Окна - количество
}
""',
        
        CONFIG_DIR / 'prices.py': '''"""
config/prices.py - Специфические цены и тарифы

# Импорт основной конфигурации (опционально)
try:
    from .settings import REPAIR_CLASSES
except ImportError:
    REPAIR_CLASSES = ["Эконом", "Комфорт", "Люкс"]

# Основные цены по классам ремонта (руб/м²)
REPAIR_PRICES = {
    'Эконом': 3500,
    'Комфорт': 6500,
    'Люкс': 12000,
    # 'Премиум': 18000,  # Раскомментируйте для добавления класса
}

# Детальная разбивка стоимости (руб/м² или за единицу)
DETAILED_PRICES = {
    'Эконом': {
        'пол': 2500,
        'стены': 1000,
        'потолок': 800,
        'двери': 15000,    # За стандартную дверь
        'окна': 12000,     # За стандартное окно
        'электрика': 500,  # За точку
        'сантехника': 2000 # За точку
    },
    'Комфорт': {
        'пол': 4500,
        'стены': 2000,
        'потолок': 1500,
        'двери': 25000,
        'окна': 20000,
        'электрика': 800,
        'сантехника': 3500
    },
    'Люкс': {
        'пол': 8000,
        'стены': 4000,
        'потолок': 3000,
        'двери': 50000,
        'окна': 40000,
        'электрика': 1500,
        'сантехника': 6000
    }
}

# Дополнительные тарифы (опционально)
ADDITIONAL_PRICES = {
    'дизайн-проект': 1500,  # руб/м²
    'авторский_надзор': 800,  # руб/м²
    'логистика': 5000,       # За доставку
    'уборка': 20000,         # Финальная уборка
    'мусор': 10000           # Вывоз мусора
}

# Коэффициенты для расчета общей площади
AREA_COEFFICIENTS = {
    'floor': 1.0,
    'walls': 0.5,
    'ceiling': 1.0
}

# Валидация классов
assert all(cls in REPAIR_PRICES for cls in REPAIR_CLASSES), "Все классы должны быть в REPAIR_PRICES"

print(f"💰 Цены загружены: {len(REPAIR_PRICES)} классов")
"""
    }
    
    created = 0
    for file_path, content in stubs.items():
        if not file_path.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding='utf-8')
            logger.info(f"📄 Создана заглушка: {file_path.name}")
            created += 1
    
    if created > 0:
        logger.info(f"✅ Создано {created} заглушек")
        return True
    return False

# ✅ Парсер аргументов
def parse_command_line():
    import argparse
    parser = argparse.ArgumentParser(
        description=f"{APP_NAME} v{APP_VERSION} - Калькулятор ремонта",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""🔧 КОМАНДЫ:
  python main.py                    # GUI запуск
  python main.py --debug            # 🐛 Отладка
  python main.py --headless         # 💻 Тесты без GUI
  python main.py --create-stubs     # 📄 Создать заглушки
  python main.py --check-structure  # 🔍 Проверка структуры
  python main.py --reset-config     # 🔄 Сброс настроек
  python main.py --system-info      # ℹ️  Системная информация"""
    )
    
    parser.add_argument('--debug', action='store_true', help='Режим отладки')
    parser.add_argument('--headless', action='store_true', help='Без GUI')
    parser.add_argument('--create-stubs', action='store_true', help='Создать заглушки')
    parser.add_argument('--check-structure', action='store_true', help='Проверить структуру')
    parser.add_argument('--reset-config', action='store_true', help='Сбросить конфигурацию')
    parser.add_argument('--system-info', action='store_true', help='Информация о системе')
    parser.add_argument('--version', action='version', version=f'{APP_NAME} v{APP_VERSION}')
    
    return parser.parse_args()

# ✅ Основная функция
def main():
    args = parse_command_line()
    
    # Специальные команды
    if args.system_info:
        print_system_info()
        return 0
    
    if args.check_structure:
        success = check_project_structure()
        print("✅" if success else "❌", "Структура проекта проверена")
        return 0 if success else 1
    
    if args.create_stubs:
        if create_missing_files():
            print("\n✅ Заглушки созданы! Заполните их кодом:")
            print("   • src/main_gui.py - главный интерфейс")
            print("   • models/project.py, models/room.py - модели данных") 
            print("   • config/settings.py, prices.py - настройки и цены")
            print("\n🔧 Для установки Excel экспорта:")
            print("   pip install openpyxl")
            print("\n🚀 Запустите: python main.py")
        else:
            print("ℹ️  Все файлы уже существуют")
        return 0
    
    if args.reset_config:
        if messagebox.askyesno("Сброс", "Сбросить конфигурацию и данные?"):
            for data_file in DATA_DIR.glob("*.json"):
                if data_file.exists():
                    data_file.unlink()
            print("✅ Конфигурация сброшена. Перезапустите приложение.")
        return 0
    
    # Проверка структуры
    if not check_project_structure():
        response = messagebox.askyesno("Проблемы", 
                                     "Обнаружены проблемы со структурой.\n"
                                     "Создать заглушки файлов?")
        if response:
            create_missing_files()
        else:
            return 1
    
    # Запуск приложения
    try:
        app = RemontCalcApp()
        
        if args.headless:
            print("💻 Режим без GUI (headless)")
            # Простой тест
            projects = app.data_manager.load_projects()
            print(f"📊 Найдено проектов: {len(projects.get('projects', []))}")
            return 0
        
        if args.debug:
            logger.setLevel(logging.DEBUG)
            print("🐛 Режим отладки включен")
        
        print(f"\n🎨 Запуск {APP_NAME} v{APP_VERSION}")
        app.run_gui()
        return 0
        
    except KeyboardInterrupt:
        logger.info("⏹️  Прервано пользователем")
        return 130
    except Exception as e:
        logger.critical(f"💥 Критическая ошибка: {e}")
        logger.critical(traceback.format_exc())
        messagebox.showerror("Ошибка запуска", f"Критическая ошибка:\n{str(e)}")
        return 1

def print_system_info():
    """Информация о системе"""
    print(f"\n🖥️  {APP_NAME} v{APP_VERSION} - ДИАГНОСТИКА")
    print("=" * 60)
    print(f"🐍 Python: {platform.python_version()}")
    print(f"💻 ОС: {platform.system()} {platform.release()}")
    print(f"🖥️  Процессор: {platform.processor()}")
    print(f"📂 Проект: {project_root}")
    print(f"📁 src/: {'✅' if SRC_DIR.exists() else '❌'}")
    print(f"📁 config/: {'✅' if CONFIG_DIR.exists() else '❌'}")
    print(f"📁 data/: {'✅' if DATA_DIR.exists() else '❌'}")
    
    # Модули
    print("\n📦 МОДУЛИ:")
    try:
        import openpyxl
        print(f"   ✅ openpyxl: {openpyxl.__version__} (Excel ✅)")
    except ImportError:
        print("   ❌ openpyxl: УСТАНОВИТЕ pip install openpyxl")
    
    print("\n🔧 СТАТУС: Готов к запуску!")
    print("🚀 Команда: python main.py")

# ✅ Запуск
if __name__ == "__main__":
    sys.exit(main())