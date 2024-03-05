import asyncio
import time

import aiohttp
from aiohttp import web

from pydantic import BaseModel


class AuthError(Exception):
    pass


class CreateTokensData(BaseModel):
    amo_host: str
    amo_password: str
    amo_email: str


async def create_tokens_handler(request):
    """
    Создает access_token, refresh_token, amojo_id, chat_token каждые 10 минут
    """
    start_time = time.time()
    try:
        data = CreateTokensData(**await request.json())
        acc_token, refr_token, headers = await create_tokens(data.amo_host, data.amo_email, data.amo_password)
        if acc_token is None:
            raise AuthError("Некорректные данные для входа!")

        return web.json_response({
            'status': True, 'answer': {
                'headers': headers,
                'access_token': acc_token,
                'refresh_token': refr_token,
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
    async with aiohttp.ClientSession() as session:
        response = await session.get(url, headers=headers, 
                                     )
        data = await response.json()
        return data["amojo_id"]


async def create_chat_token(host, headers):
    url = f"{host}ajax/v1/chats/session"
    payload = {"request[chats][session][action]": "create"}
    async with aiohttp.ClientSession() as session:
        response = await session.post(url=url, headers=headers, data=payload,
                                      
                                      )
        data = await response.json()
        return data["response"]["chats"]["session"]["access_token"]


async def create_tokens(host, login, password):
    cookies, csrf_token, headers = await _create_session(host)
    url = f"{host}oauth2/authorize"
    payload = {
        "csrf_token": csrf_token,
        "username": login,
        "password": password
    }
    async with aiohttp.ClientSession(cookies=cookies) as session:
        async with session.post(
                url=url, data=payload, headers=headers,
                
        ) as response:
            if response.status != 200:
                print('error')
                return None, None  # TODO: оповестить об ошибке
            cookies = response.cookies
            access_token = cookies.get("access_token").value
            refresh_token = cookies.get("refresh_token").value
            headers['access_token'] = access_token
            headers['refresh_token'] = refresh_token
            headers['HOST'] = host.replace('https://', '').replace('/', '')

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

