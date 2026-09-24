import io
import requests
import os
from pathlib import Path
from random import randrange
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from db.crud import (
    add_to_blacklist,
    add_to_favorites,
    get_blacklist,
    get_favorites,
    get_top_photos,
    get_or_create_user,
    save_candidate,
    save_photo,
    update_user_preferences,
)
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("VK_API_TOKEN_BOT")

vk_session = vk_api.VkApi(token=token)
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session)


def get_user_info(user_id):
    user_info = vk.users.get(
        fields="photo_200,home_town,sex,bdate",
        user_ids=user_id,
    )

    data = {
        "id": user_info[0].get("id"),
        "age": str(user_info[0].get("bdate")),
        "photo": user_info[0].get("photo_200"),
        "town": user_info[0].get("home_town"),
        "gender": user_info[0].get("sex"),
        "first_name": user_info[0].get("first_name"),
        "last_name": user_info[0].get("last_name"),
    }
    return data


def keyboard_default():
    path = Path(__file__).parent / "keyboard.json"
    return path.read_text(encoding="utf-8")


def keyboard_like():
    path = Path(__file__).parent / "keyboard_like.json"
    return path.read_text(encoding="utf-8")


def send_photo(image_url, user_id, message):
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        photo = vk_api.upload.VkUpload(vk_session).photo_messages(
            photos=io.BytesIO(response.content)
        )[0]
        attachment = f"photo{photo['owner_id']}_{photo['id']}"
        vk.messages.send(
            user_id=user_id,
            attachment=attachment,
            message=message,
            random_id=randrange(10**7),
        )
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при скачивании фото: {e}")

    except vk_api.exceptions.ApiError as e:
        print(f"Ошибка API ВКонтакте: {e}")


def write_msg(user_id, message, keyboard=""):
    if keyboard:
        vk.messages.send(
            user_id=user_id,
            message=message,
            keyboard=keyboard,
            random_id=randrange(10**7),
        )
    else:
        vk.messages.send(user_id=user_id, message=message, random_id=randrange(10**7))


def get_vk_users(offset=0, sex=1, count=10):
    data_users = []
    token_user = os.getenv("USER_TOKEN")
    headers = {"Authorization": f"Bearer {token_user}"}

    params = {
        "fields": "id,first_name,last_name,bdate,photo_200",
        "v": "5.199",
        "count": count,
        "sex": sex,
        "offset": offset,
        "has_photo": 1,
    }
    try:
        response = requests.get(
            "https://api.vk.com/method/users.search", headers=headers, params=params
        )
        response.raise_for_status()
        data = response.json()
        if "error" in data:
            print(f"Ошибка VK API: {data['error']}")
            return []
        data_response = data["response"]["items"]
        for user in data_response:
            profile_link = f"https://vk.com/id{user.get('id')}"
            data_users.append(
                {
                    "id": user.get("id"),
                    "age": user.get("bdate"),
                    "photo": user.get("photo_200"),
                    "first_name": user.get("first_name"),
                    "last_name": user.get("last_name"),
                    "profile_link": profile_link,
                }
            )
        return data_users
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса VK: {e}")
        return []


def get_full_photo_candidate(owner_id):
    photos_data = []
    token_user = os.getenv("USER_TOKEN")
    headers = {"Authorization": f"Bearer {token_user}"}
    params = {
        "owner_id": owner_id,
        "album_id": "profile",
        "extended": 1,
        "photo_sizes": 1,
        "count": 3,
        "v": "5.199",
    }
    try:
        response = requests.get(
            "https://api.vk.com/method/photos.get", params=params, headers=headers
        )
        response.raise_for_status()
        response_data = response.json()
        if "error" in response_data:
            print(f"Ошибка VK API: {response_data['error']}")
            return []
        for photo in response_data["response"]["items"]:
            if not photo.get("sizes"):
                continue
            best_size = max(photo["sizes"], key=lambda s: s["width"] * s["height"])
            photo_url = best_size["url"]
            likes_count = photo.get("likes", {}).get("count", 0)
            photos_data.append({"url": photo_url, "likes": likes_count})
        return photos_data
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при получении фотографий: {e}")
        return []


def show_candidate(user_id, candidate):
    candidate_vk_id = candidate["id"]
    bd_candidate = save_candidate(
        candidate_vk_id,
        candidate["first_name"],
        candidate["last_name"],
        candidate["profile_link"],
    )
    if not bd_candidate:
        write_msg(user_id, "Не удалось загрузить анкету.", keyboard_default())
        return False
    top_photos = get_top_photos(candidate_vk_id, limit=3)
    if not top_photos:
        photo_url_list = get_full_photo_candidate(candidate_vk_id)
        seen_urls = set()
        for photo in photo_url_list:
            url = photo.get("url")
            if not url:
                continue
            if url in seen_urls:
                continue
            seen_urls.add(url)
            save_photo(candidate_vk_id, url, photo.get("likes", 0))
        top_photos = get_top_photos(candidate_vk_id, limit=3)
    if not top_photos:
        write_msg(user_id, "У кандидата нет доступных фотографий.", keyboard_like())
        return False
    unique_photos = list(dict.fromkeys(top_photos))

    message = f"{candidate['first_name']} {candidate['last_name']} {candidate['profile_link']}"
    for photo_url in unique_photos[:3]:
        send_photo(photo_url, user_id, message)

    write_msg(user_id, "Что сделать с этой анкетой?", keyboard_like())
    return True


def start_bot():
    user_states = {}
    user_candidate = {}
    for event in longpoll.listen():
        if event.type != VkEventType.MESSAGE_NEW:
            continue
        if not event.to_me:
            continue
        user_id = event.user_id
        request = event.text.lower().strip()
        vk_data = get_user_info(user_id)
        user_info = get_or_create_user(
            vk_data["id"],
            vk_data["first_name"],
            vk_data["last_name"],
            vk_data["age"],
            vk_data["town"],
            vk_data["gender"],
            photo_url=vk_data["photo"],
        )
        photo = vk_data["photo"]
        if user_id in user_states:
            if user_states[user_id] == "waiting_for_gender":
                if request in [
                    "девушки",
                    "девушку",
                    "ж",
                ]:
                    update_user_preferences(user_id, "girl")
                    del user_states[user_id]
                    write_msg(user_id, "Ваша анкета создана!", keyboard_default())
                    send_photo(
                        photo,
                        user_id,
                        f"{vk_data['first_name']} {vk_data['last_name']},{vk_data['age']}, {vk_data['town']}",
                    )
                elif request in ["мужчину", "м", "мужчина", "парня"]:
                    update_user_preferences(user_id, "man")
                    del user_states[user_id]
                    write_msg(user_id, "Ваша анкета создана!", keyboard_default())
                    send_photo(
                        photo,
                        user_id,
                        f"{vk_data['first_name']} {vk_data['last_name']}, {vk_data['age']}, {vk_data['town']}",
                    )
                else:
                    write_msg(
                        user_id,
                        "Пожалуйста, выберите: девушки или мужчины.",
                        keyboard_default(),
                    )
                continue

        if user_id in user_candidate:
            state = user_candidate[user_id]
            if request == "лайк":
                candidates = state["candidates"]
                index = state["index"]
                if index < len(candidates):
                    candidate = candidates[index]
                    bd_candidate = save_candidate(
                        candidate.get("id"),
                        candidate.get("first_name"),
                        candidate.get("last_name"),
                        candidate.get("profile_link"),
                    )
                    if bd_candidate:
                        added = add_to_favorites(user_id, bd_candidate.vk_id)
                        if added:
                            write_msg(
                                user_id,
                                "Кандидат добавлен в избранное",
                                keyboard_like(),
                            )
                        else:
                            write_msg(
                                user_id,
                                "Этот кандидат уже в избранном.",
                                keyboard_like(),
                            )
                continue
            elif request == "следующая анкета":
                state["index"] += 1
                index = state["index"]
                candidates = state["candidates"]
                if index < len(candidates):
                    candidate = candidates[index]
                    show_candidate(user_id, candidate)
                    continue
                del user_candidate[user_id]
                write_msg(
                    user_id,
                    "Анкеты закончились. Попробуйте посмотреть позже.",
                    keyboard_default(),
                )
                continue

            elif request == "я больше не хочу никого искать":
                del user_candidate[user_id]
                write_msg(
                    user_id,
                    "Хорошо, можете пока написать тому, кто вам понравился.",
                    keyboard_default(),
                )
                continue
        if request == "начать":
            write_msg(
                user_id,
                f"{vk_data['first_name']}, выбери нужный пункт",
                keyboard_default(),
            )
        elif request == "моя анкета":
            if user_info.search_gender is None:
                write_msg(user_id, "Сначала нужно создать анкету.", keyboard_default())

            else:
                write_msg(user_id, "Ваша анкета:", keyboard_default())
                send_photo(
                    photo,
                    user_id,
                    f"{vk_data['first_name']}, {vk_data['last_name']} {vk_data['age']}, {vk_data['town']}",
                )

        elif request == "создать анкету":
            if user_info.search_gender is None:
                write_msg(user_id, "Кто вам нравится?", keyboard_default())
                user_states[user_id] = "waiting_for_gender"
            else:
                write_msg(user_id, "У вас уже создана анкета.", keyboard_default())
        elif request == "смотреть анкеты":
            if user_info.search_gender is None:
                write_msg(user_id, "Сначала создайте анкету.", keyboard_default())
                continue
            if user_info.search_gender == "girl":
                sex = 1
            elif user_info.search_gender == "man":
                sex = 2
            else:
                write_msg(
                    user_id, "Не удалось определить предпочтения.", keyboard_default()
                )
                continue
            candidates = get_vk_users(offset=0, sex=sex, count=10)
            if not candidates:
                write_msg(user_id, "Не удалось найти кандидатов.", keyboard_default())
                continue
            user_candidate[user_id] = {"candidates": candidates, "index": 0}

            show_candidate(user_id, candidates[0])
            continue
        elif request == "добавить в избранное":
            if user_id not in user_candidate:
                write_msg(
                    user_id, "Сначала начните просмотр анкет.", keyboard_default()
                )
                continue
            state = user_candidate[user_id]
            index = state["index"]
            candidates = state["candidates"]
            if index < len(candidates):
                candidate = candidates[index]
                bd_candidate = save_candidate(
                    candidate.get("id"),
                    candidate.get("first_name"),
                    candidate.get("last_name"),
                    candidate.get("profile_link"),
                )
                if bd_candidate:
                    added = add_to_favorites(user_id, bd_candidate.vk_id)
                    if added:
                        write_msg(
                            user_id, "Кандидат добавлен в избранное.", keyboard_like()
                        )
                    else:
                        write_msg(
                            user_id,
                            "Кандидат уже находится в избранном.",
                            keyboard_like(),
                        )
            continue
        elif request == "следующая анкета":
            write_msg(user_id, "Сначала нажмите «Смотреть анкеты».", keyboard_default())
            continue

        elif request == "мои симпатии":
            favorites = get_favorites(user_id)
            if not favorites:
                write_msg(user_id, "У вас пока нет симпатий.", keyboard_default())
            else:
                write_msg(
                    user_id, f"У вас {len(favorites)} симпатий.", keyboard_default()
                )
                for candidate in favorites:
                    top_photos = get_top_photos(candidate.vk_id, limit=3)
                    top_photos = list(dict.fromkeys(top_photos))
                    message = f"{candidate.first_name} {candidate.last_name} {candidate.profile_link}"

                    for photo_url in top_photos[:3]:
                        send_photo(photo_url, user_id, message)

        elif request == "я больше не хочу никого искать":
            if user_id in user_candidate:
                del user_candidate[user_id]
            write_msg(
                user_id,
                "Хорошо, можете пока написать тому, кто вам понравился.",
                keyboard_default(),
            )
        else:
            write_msg(user_id, "Не поняла вашего ответа...", keyboard_default())
