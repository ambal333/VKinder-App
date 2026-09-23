"""
Точка входа в приложение VKinder.
Запускает инициализацию базы данных и стартует бота.
"""

from db.database import init_db
from vk_bot.vk_get_info_photo_user import start_bot
from vk_bot.vk_get_info_photo_user import keyboard_default,keyboard_like

def main():
    print("🚀 Запуск VKinder...")

    # 1. Инициализация базы данных
    init_db()
    print("✅ База данных успешно инициализирована!")

    # 2. Запуск бота
    print("🤖 Запуск бота...")
    keyboard_default()
    keyboard_like()
    start_bot()


if __name__ == "__main__":
    main()
