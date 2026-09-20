import json
import os
from pathlib import Path
from random import randrange
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from dotenv import load_dotenv
load_dotenv()
token = os.getenv('VK_API_TOKEN')

# def get_user_info(id_user):
#     headers = {'Authorization': f'Bearer {token}'}
#     params = {'fields': 'photo_200','v': '5.199','user_ids': f'{id_user}'}
#     response = requests.get('https://api.vk.com/method/users.get', headers=headers, params=params)
#     data = response.json()
#     user_info = []
#     for i in data['response']:
#         user_info.append({'id': i['id'],'firstname': i['first_name'], 'lastname': i['last_name'], 'photo': i['photo_200']})
#     return user_info

vk = vk_api.VkApi(token=token)
longpoll = VkLongPoll(vk)

def write_msg(user_id, message):
    path = Path('keyboard.json')
    content = path.read_text(encoding='utf-8')
    vk.method('messages.send', {'user_id': user_id, 'message': message, 'keyboard': content,'inline': False, 'random_id': randrange(10 ** 7)})


def start_bot():
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            if event.to_me:
                request = event.text

                if request == "привет":
                    write_msg(event.user_id, f"Хай, {event.user_id}")
                elif request == "пока":
                    write_msg(event.user_id, "Пока((")
                else:
                    write_msg(event.user_id, "Не поняла вашего ответа...")
start_bot()