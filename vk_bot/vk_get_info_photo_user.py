import io
import requests
import os
from pathlib import Path
from random import randrange
import vk_api
from vk_api.upload import VkUpload
from vk_api.longpoll import VkLongPoll, VkEventType
from db.crud import add_to_blacklist,add_to_favorites,get_blacklist,get_favorites,get_top_photos,get_or_create_user,save_candidate,save_photo,update_user_preferences
from dotenv import load_dotenv
load_dotenv()
token = os.getenv('VK_API_TOKEN_BOT')

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

def keyboard_default():
    path = Path(__file__).parent / 'keyboard.json'
    content = path.read_text(encoding='utf-8')
    return content

def keyboard_like():
    path = Path(__file__).parent / 'keyboard_like.json'
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
def get_vk_users(offset=0):
    data_users = []
    token_user = os.getenv('USER_TOKEN')
    headers = {'Authorization': f'Bearer {token_user}'}
    params = {'fields': 'id,first_name,last_name,bdate,photo_200','v': '5.199', 'count': 10, 'sex': 1, 'offset': offset, 'has_photo': 1}
    response = requests.get('https://api.vk.com/method/users.search',headers=headers,params=params)
    data_response = response.json()['response']['items']
    for i in data_response:
        profile_link = f"https://vk.com/id{i.get('id')}"
        data_users.append({'id': i.get('id'),'age': i.get('bdate'),'photo': i.get('photo_200'),
                           'first_name': i.get('first_name'),'last_name': i.get('last_name'),'profile_link': profile_link})
    return data_users

def start_bot():
    print(get_vk_users())
    user_states = {}
    user_couple = {}

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            if event.to_me:
                user_id = event.user_id # vk_id пользователя
                request = event.text.lower().strip()
                vk_data = get_user_info(user_id) # данные из vk_api
                user_info = get_or_create_user(vk_data['id'],vk_data['first_name'],vk_data['last_name'],19,vk_data['town'],vk_data['gender'], photo_url=vk_data['photo']) # данные из бд
                photo = vk_data['photo']
                if user_id in user_states:
                    if user_states[user_id] == 'waiting_for_gender':
                        if request in ['девушки', 'девушку', 'ж', 'женщин', 'женщину', 'женщины']:
                            update_user_preferences(user_id,'girl')
                            del user_states[user_id]
                            write_msg(user_id, "Ваша анкета создана:")
                            send_photo(photo, user_id, f'{user_info.first_name} {user_info.last_name}, {user_info.age}, {user_info.city}')
                        elif request in ['мужчину', 'м', 'мужчина', 'парни', 'парня', 'мужчины']:
                            update_user_preferences(user_id, 'man')
                            del user_states[user_id]
                            write_msg(user_id, "Ваша анкета создана:")
                            send_photo(photo, user_id, f'{user_info.first_name} {user_info.last_name}, {user_info.age}, {user_info.city}')
                        continue
                    elif user_id in user_couple and user_couple[user_id] == 'search_couple':
                        pass
                if request == "начать":
                    write_msg(user_id, f"{user_info.first_name} выбери нужный пункт", keyboard_default())
                elif request == "моя анкета":
                    if user_info.search_gender is None:
                        write_msg(user_id, "Сначала нужно создать анкету", keyboard_default())
                    else:
                        write_msg(user_id, "Ваша анкета: ", keyboard_default())
                        send_photo(photo, user_id,
                                   f'{user_info.first_name},{user_info.last_name} {user_info.age},{user_info.city}')
                elif request == "создать анкету":
                    if user_info.search_gender is None:
                        write_msg(user_id, "Кто вам нравится? ", keyboard_default())
                        user_states[user_id] = 'waiting_for_gender'
                    else:
                        write_msg(user_id, "У вас уже создана анкета", keyboard_default())
                elif request == 'найти пару':
                        pass

                elif request == 'добавить в избранное':
                    pass
                elif request == "я больше не хочу никого искать":
                    write_msg(user_id, "Хорошо, можете пока написать тому, кто вам понравился", keyboard_default())
                else:
                    write_msg(user_id, "Не поняла вашего ответа...", keyboard_default())