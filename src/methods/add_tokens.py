import asyncio
import time

import aiohttp
import requests
from aiohttp import web

from pydantic import BaseModel


class AuthError(Exception):
    pass


class AddTokensData(BaseModel):
    amo_host: str
    client_id: str
    client_secret: str
    refresh_token: str


async def add_tokens_handler(request):
    """
    Создает access_token, refresh_token, amojo_id, chat_token каждые 10 минут
    """
    start_time = time.time()
    try:
        data = AddTokensData(**await request.json())
        access_token, refresh_token = _create_tokens(data)
        headers = {"Authorization": f'Bearer {data.access_token}'}
        return web.json_response({
            'status': True, 'answer': {
                'headers': headers,
                'access_token': access_token,
                'refresh_token': refresh_token,
                'amojo_id': await create_amojo_id(data.amo_host, headers),
                'chat_token': await create_chat_token(data.amo_host, headers)
            },
            'execution_time': round(time.time() - start_time, 2)
        })
    except AuthError as e:
        return web.json_response(
            {'status': False, 'answer': f'{e}', 'execution_time': round(time.time() - start_time, 2)},
            status=403)

    except Exception as e:
        return web.json_response(
            {'status': False, 'answer': f'{e}', 'execution_time': round(time.time() - start_time, 2)},
            status=400)


async def create_amojo_id(host, headers):
    url = f"{host}api/v4/account?with=amojo_id"
    print(url)
    print(headers)
    async with aiohttp.ClientSession() as session:
        response = await session.get(url, headers=headers,
                                     )
        data = await response.json()
        return data["amojo_id"]


async def create_chat_token(host, headers):
    url = f"{host}ajax/v1/chats/session"
    headers['X-Requested-With'] = 'XMLHttpRequest'
    payload = {"request[chats][session][action]": "create"}
    async with aiohttp.ClientSession() as session:
        response = await session.post(url=url, headers=headers, data=payload,

                                      )
        data = await response.json()
        return data["response"]["chats"]["session"]["access_token"]


async def create_tokens(host, access_token, refresh_token):
    cookies, csrf_token, headers = await _create_session(host)
    headers['access_token'] = access_token
    headers['refresh_token'] = refresh_token
    headers['HOST'] = host.replace('https://', '').replace('/', '')
    print(headers)
    return access_token, refresh_token, headers


async def _create_session(host):
    async with aiohttp.ClientSession() as session:
        async with session.get(host,

                               ) as response:
            cookies = response.cookies
            csrf_token = cookies.get("csrf_token").value
            headers = {
                "Accept": "application/json",
                "X-Requested-With": "XMLHttpRequest",
                "Cookie": f'session_id={cookies.get("session_id").value}; csrf_token={csrf_token};',
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
            }
        return cookies, csrf_token, headers


def _create_tokens(data: AddTokensData):
    print(data)
    response = requests.post(f'{data.amo_host}oauth2/access_token', data={
        'client_id': data.client_id,
        'client_secret': data.client_secret,
        'refresh_token': data.refresh_token,
        'grant_type': 'refresh_token'
    })
    return response.json()['access_token'], response.json()['refresh_token']


access_token, refresh_token = _create_tokens(AddTokensData(
    client_id='4d7d3597-1dc1-4d11-91ef-3ea04b2bae33',
    client_secret='v6DPpRMednQad8zOsOsRw2jVIZdShRps5vmylAllc36BVwb82oqYr88POzZUVw7e',
    refresh_token='def502003c0c1d01755dc834fcf55d78c25070c071a06a908c4324ea9fdc15d1fbbd3c4dce0a84eda2655024cb3f3cae496877cb907d2e878da8b53ce9a43da8c3b3ab1f552f35f785af39a765d570f2ef791f506a75344a481c1005190d3481062d492e58d3ce6cc65870094024933c8ae5eb630d326bc003913412ed28871705a750eb38d14c1e9a0a556965dee9eddd90be1e8f1e78c5d19ade91ae4e21c1347a96d276f017003fe425174965ae635a6be02e5a101c529e45195a944aa21faffe92755a2b38b67c5ad0f904e0f8e035bfd0dcd321cc6604406e8beb7be052a94723a50d5d83c011157792c951bab9238c45b3054319678be1de1f4af33c5dc83950a98023044b48cae1df752fdd6dab325e597deb8badc40d5b9d2fdbad1ebe3b0ea5e59408a450fa2fb9268ffec8c8ff212df13d97b9a61aea844c4a63d4b960f352ae1194b829e05fae205a8b5179257219e656f64ab0b5b591229cfc96e3672b67c6bf8ff639335da2400954a9441ff4934b3eab42ee40df117a7ff84764445e915d18785d522e443d60d9334f80a55c5d886712c38c00cc34b9e0ce778c419cfc8c44760d35eef0c6081f70fc5908ce9574997128afac96d5896429755c67f4d9554923e88eae8c97ee2843496c976c29cad795',
    amo_host='https://olegback2003.amocrm.ru/'
))
