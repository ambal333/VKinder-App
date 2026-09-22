import io
import requests
import os
from pathlib import Path
from random import randrange
import vk_api
from vk_api.upload import VkUpload
from vk_api.longpoll import VkLongPoll, VkEventType
from db.crud import add_to_blacklist,add_to_favorites,get_blacklist,get_favorites,get_top_photos,get_or_create_user,save_candidate,save_photo
from dotenv import load_dotenv
load_dotenv()
token = os.getenv('VK_API_TOKEN')

vk_session = vk_api.VkApi(token=token)
vk = vk_session.get_api()
upload = vk_api.upload.VkUpload(vk_session)
longpoll = VkLongPoll(vk_session)

def get_user_info(user_id):
    user_info = vk.users.get(fields='photo_200,home_town,sex,bdate',user_ids=user_id,)
    data = {'id': user_info[0].get('id'), 'age': user_info[0].get('bdate'),
            'photo': user_info[0].get('photo_200'),'town': user_info[0].get('home_town'),
            'gender': user_info[0].get('sex'), 'first_name': user_info[0].get('first_name'),'last_name': user_info[0].get('last_name')}
    return data

def keyboard_1():
    path = Path(__file__).parent / 'keyboard.json'
    content = path.read_text(encoding='utf-8')
    return content
def send_photo(image_url,user_id,message):
    try:
        response = requests.get(image_url)
        response.raise_for_status()  # Проверка на ошибки загрузки
        photo = upload.photo_messages(photos=io.BytesIO(response.content))[0]
        attachment = f"photo{photo['owner_id']}_{photo['id']}"
        vk.messages.send(
            user_id=user_id,
            attachment=attachment,
            message=message,
            random_id=randrange(10 ** 7)
        )
        # print("Фото успешно отправлено!")

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при скачивании фото: {e}")
    except vk_api.exceptions.ApiError as e:
        print(f"Ошибка API ВКонтакте: {e}")
def write_msg(user_id, message,keyboard=''):
    if keyboard:
        vk.messages.send(user_id=user_id,message=message,keyboard=keyboard,
                         random_id=randrange(10 ** 7))
    else:
        vk.messages.send(user_id=user_id, message=message, random_id=randrange(10 ** 7))


def start_bot():
    user_states = {}
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            if event.to_me:
                user_id = event.user_id # vk_id пользователя
                request = event.text.lower().strip()
                vk_data = get_user_info(user_id) # данные из vk_api
                get_or_create_user(vk_data['id'],vk_data['first_name'],vk_data['last_name'],vk_data['age'],vk_data['town'],vk_data['gender'])
                user_info = get_or_create_user(vk_data['id'],vk_data['first_name'],vk_data['last_name'],vk_data['age'],vk_data['town'],vk_data['gender']) # данные из бд
                photo = save_photo(user_id, vk_data['photo'])
                if user_id in user_states:
                    if user_states[user_id] == 'waiting_for_gender':
                        if request in ['девушки', 'девушку', 'ж', 'женщин', 'женщину', 'женщины']:
                            user_info['opposite_sex'] = 'girl'
                            del user_states[user_id]
                            write_msg(user_id, "Ваша анкета создана:")
                            send_photo(photo, user_id, f'{user_info.first_name} {user_info.last_name}, {user_info.age}, {user_info.city}')
                        elif request in ['мужчину', 'м', 'мужчина', 'парни', 'парня', 'мужчины']:
                            user_info['opposite_sex'] = 'man'
                            del user_states[user_id]
                            write_msg(user_id, "Ваша анкета создана:")
                            send_photo(photo, user_id, f'{user_info.first_name} {user_info.last_name}, {user_info.age}, {user_info.city}')
                        continue
                if request == "начать":
                    write_msg(user_id, f"{user_info.first_name} выбери нужный пункт", keyboard_1())
                elif request == "моя анкета":
                    if user_info.get('opposite_sex') is None:
                        write_msg(user_id, "Сначала нужно создать анкету", keyboard_1())
                    else:
                        write_msg(user_id, "Ваша анкета: ", keyboard_1())
                        send_photo(photo, user_id,
                                   f'{user_info.first_name},{user_info.last_name} {user_info.age},{user_info.city}')
                elif request == "создать анкету":
                    if user_info.get('opposite_sex') is None:
                        write_msg(user_id, "Кто вам нравится? ", keyboard_1())
                        user_states[user_id] = 'waiting_for_gender'
                    else:
                        write_msg(user_id, "У вас уже создана анкета", keyboard_1())
                elif request == "я больше не хочу никого искать":
                    write_msg(user_id, "Хорошо, можете пока написать тому, кто вам понравился", keyboard_1())
                else:
                    write_msg(user_id, "Не поняла вашего ответа...", keyboard_1())