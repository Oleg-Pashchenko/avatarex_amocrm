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
        print(data)
        access_token, refresh_token = _create_tokens(data)
        headers = {"Authorization": f'Bearer {access_token}'}
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
    print(response.json())
    return response.json()['access_token'], response.json()['refresh_token']



