import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Загружаем переменные из файла .env
load_dotenv()

# Проверяем наличие всех необходимых переменных окружения
try:
    DB_HOST = os.environ["DB_HOST"]
    DB_PORT = os.environ["DB_PORT"]
    DB_NAME = os.environ["DB_NAME"]
    DB_USER = os.environ["DB_USER"]
    DB_PASSWORD = os.environ["DB_PASSWORD"]
except KeyError as e:
    missing_var = e.args[0]
    raise SystemExit(
        f"❌ КРИТИЧЕСКАЯ ОШИБКА: Отсутствует переменная окружения '{missing_var}' в файле .env. "
        "Без доступа к базе данных запуск приложения невозможен."
    )

# Формируем строку подключения (DSN - Data Source Name)
DSN = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Создаем движок (engine) для подключения к БД
engine = create_engine(DSN)

# Создаем фабрику сессий.
# autocommit=False и autoflush=False - безопасные настройки по умолчанию
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Инициализирует базу данных: создает все таблицы, описанные в models.py,
    если их еще не существует.
    """
    # Импортируем Base здесь, чтобы избежать циклических импортов
    # и не выполнять импорт при простой загрузке модуля
    from db.models import Base

    # Создаем таблицы (безопасно, так как в SQL у нас есть IF NOT EXISTS)
    Base.metadata.create_all(bind=engine)
