import os
import requests
from dotenv import load_dotenv
load_dotenv()
token = os.getenv('VK_API_TOKEN')
user_id = '1,2'
def get_user_info(id_user):
    headers = {'Authorization': f'Bearer {token}'}
    params = {'fields': 'photo_200','v': '5.199','user_ids': f'{id_user}'}
    response = requests.get('https://api.vk.com/method/users.get', headers=headers, params=params)
    data = response.json()
    user_info = []
    for i in data['response']:
        user_info.append({'id': i['id'],'firstname': i['first_name'], 'lastname': i['last_name'], 'photo': i['photo_200']})
    return user_info

print(get_user_info(user_id))

