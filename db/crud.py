"""
Модуль для работы с базой данных VKinder.
Здесь находятся все функции, которые будет использовать бот
для сохранения и получения данных из нашей локальной БД.
"""

from typing import List, Optional

from sqlalchemy.exc import SQLAlchemyError

from db.models import User, Candidate, Photo
from db.database import SessionLocal


def get_or_create_user(
    vk_id: int,
    first_name: str,
    last_name: str,
    age: int,
    city: str,
    gender: int,
    photo_url: Optional[str] = None,
) -> Optional[User]:
    """
    Получает пользователя из БД по vk_id.
    Если его там нет — создаёт новую запись и возвращает её.

    Вызывается, когда пользователь впервые пишет боту.

    :param vk_id: ID пользователя ВКонтакте
    :param first_name: Имя
    :param last_name: Фамилия
    :param age: Возраст
    :param city: Город
    :param gender: Пол (1 = жен, 2 = муж)
    :param photo_url: Ссылка на фото аватарки пользователя
    :return: Объект User из базы данных или None, если произошла ошибка БД
    """
    with SessionLocal() as session:
        user = session.get(User, vk_id)
        if user:
            return user
        else:
            try:
                user = User(
                    vk_id=vk_id,
                    first_name=first_name,
                    last_name=last_name,
                    age=age,
                    city=city,
                    gender=gender,
                    photo_url=photo_url,
                )
                session.add(user)
                session.commit()
                return user
            except SQLAlchemyError as e:
                session.rollback()
                print(f"Ошибка при работе с БД: {e}")
                return None


def update_user_preferences(vk_id: int, search_gender: str) -> bool:
    """
    Обновляет предпочтения поиска пользователя (кого он ищет).

    :param vk_id: ID пользователя
    :param search_gender: 'man' или 'woman'
    :return: True при успехе, False если пользователь не найден или произошла ошибка
    """
    with SessionLocal() as session:
        try:
            user = session.get(User, vk_id)
            if not user:
                return False

            user.search_gender = search_gender  # type: ignore
            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Ошибка при обновлении предпочтений пользователя: {e}")
            return False


def save_candidate(
    vk_id: int, first_name: str, last_name: str, profile_link: str
) -> Optional[Candidate]:
    """
    Сохраняет кандидата для знакомств в БД.

    Вызывается после того, как бот получил данные о кандидате из VK API.
    Если кандидат с таким vk_id уже есть — просто возвращает существующего.

    :param vk_id: ID кандидата ВКонтакте
    :param first_name: Имя
    :param last_name: Фамилия
    :param profile_link: Ссылка на профиль
    :return: Объект Candidate из базы данных или None, если произошла ошибка БД
    """
    with SessionLocal() as session:
        candidate = session.get(Candidate, vk_id)
        if candidate:
            return candidate
        else:
            try:
                candidate = Candidate(
                    vk_id=vk_id,
                    first_name=first_name,
                    last_name=last_name,
                    profile_link=profile_link,
                )
                session.add(candidate)
                session.commit()
                return candidate
            except SQLAlchemyError as e:
                session.rollback()
                print(f"Ошибка при работе с БД: {e}")
                return None


def save_photo(candidate_vk_id: int, url: str, likes_count: int = 0) -> Optional[Photo]:
    """
    Сохраняет фотографию кандидата в БД.

    :param candidate_vk_id: ID кандидата, которому принадлежит фото
    :param url: Ссылка на изображение
    :param likes_count: Количество лайков на фото (для сортировки топ-3)
    :return: Объект Photo из базы данных или None, если произошла ошибка БД
    """
    with SessionLocal() as session:
        try:
            photo = Photo(
                candidate_vk_id=candidate_vk_id, url=url, likes_count=likes_count
            )
            session.add(photo)
            session.commit()
            return photo
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Ошибка при работе с БД: {e}")
            return None


def get_top_photos(candidate_vk_id: int, limit: int = 3) -> List[str]:
    """
    Возвращает топ-N фотографий кандидата, отсортированных по лайкам.

    Вызывается, когда боту нужно показать фото кандидата пользователю.

    :param candidate_vk_id: ID кандидата
    :param limit: Сколько фото вернуть (по умолчанию 3)
    :return: Список URL-адресов фотографий (строки)
    """
    with SessionLocal() as session:
        try:
            photo_urls_row = (
                session.query(Photo.url)
                .filter(Photo.candidate_vk_id == candidate_vk_id)
                .order_by(Photo.likes_count.desc())
                .limit(limit=limit)
                .all()
            )
            top_photos = [url[0] for url in photo_urls_row if url[0]]
            return top_photos
        except SQLAlchemyError as e:
            print(f"Ошибка при работе с БД: {e}")
            return []


def add_to_favorites(user_vk_id: int, candidate_vk_id: int) -> bool:
    """
    Добавляет кандидата в избранное пользователя.

    Вызывается, когда пользователь нажимает кнопку "Лайк" / "В избранное".

    :param user_vk_id: ID пользователя, который лайкает
    :param candidate_vk_id: ID кандидата, которого лайкнули
    :return: True - при успешном добавлении кандидата,
        False - если кандидат уже в избранном, или при ошибке
    """
    with SessionLocal() as session:
        try:
            user = session.get(User, user_vk_id)
            candidate = session.get(Candidate, candidate_vk_id)
            if user and candidate and candidate not in user.candidates:
                user.candidates.append(candidate)
                session.commit()
                return True
            else:
                return False
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Ошибка при работе с БД: {e}")
            return False


def get_favorites(user_vk_id: int) -> List[Candidate]:
    """
    Возвращает список всех кандидатов, которых пользователь добавил в избранное.

    Вызывается, когда пользователь нажимает кнопку "Мои симпатии".

    :param user_vk_id: ID пользователя
    :return: Список объектов Candidate
    """
    with SessionLocal() as session:
        try:
            user = session.get(User, user_vk_id)
            if user:
                return list(user.candidates)
            else:
                return []
        except SQLAlchemyError as e:
            print(f"Ошибка при работе с БД: {e}")
            return []


def add_to_blacklist(user_vk_id: int, candidate_vk_id: int) -> bool:
    """
    Добавляет кандидата в чёрный список пользователя.

    Вызывается, когда пользователь нажимает кнопку "Дизлайк" / "В чёрный список".

    :param user_vk_id: ID пользователя, который ставит дизлайк
    :param candidate_vk_id: ID кандидата, которому поставили дизлайк
    :return: True - при успешном добавлении кандидата в чёрный список,
        False - если кандидат уже в чёрном списке, или при ошибке
    """
    with SessionLocal() as session:
        try:
            user = session.get(User, user_vk_id)
            candidate = session.get(Candidate, candidate_vk_id)
            if user and candidate and candidate not in user.blocked_candidates:
                user.blocked_candidates.append(candidate)
                session.commit()
                return True
            else:
                return False
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Ошибка при работе с БД: {e}")
            return False


def get_blacklist(user_vk_id: int) -> List[int]:
    """
    Возвращает список vk_id всех кандидатов, которых пользователь
    добавил в чёрный список.

    Вызывается, когда бот фильтрует кандидатов для показа пользователю.

    :param user_vk_id: ID пользователя
    :return: Список vk_id кандидатов
    """
    with SessionLocal() as session:
        try:
            user = session.get(User, user_vk_id)
            if user:
                blocked_candidates_id = [c.vk_id for c in user.blocked_candidates]
                return blocked_candidates_id
            else:
                return []
        except SQLAlchemyError as e:
            print(f"Ошибка при работе с БД: {e}")
            return []
