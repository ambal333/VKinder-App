"""
Точка входа в приложение VKinder.
Запускает инициализацию базы данных и стартует бота.
"""

from db.database import init_db
# from vk_bot import run_bot

def main():
    print("🚀 Запуск VKinder...")
    
    # 1. Инициализация базы данных
    init_db()
    print("✅ База данных успешно инициализирована!")
    
    # 2. Запуск бота
    print("🤖 Запуск бота...")
    # run_bot() 

if __name__ == "__main__":
    main()