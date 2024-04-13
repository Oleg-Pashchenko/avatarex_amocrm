import asyncio
import json
import time

import aiohttp
from aiohttp import web
from pydantic import BaseModel


async def send_message(host, hash, chat_token, message, chat_id):
    headers = {"X-Auth-Token": chat_token}
    amojo_host = 'https://amojo.amocrm.ru/' if 'amocrm' in host else 'https://amojo.kommo.com/'
    url = f"{amojo_host}v1/chats/{hash}/{chat_id}/messages?with_video=true&stand=v16"
    async with aiohttp.ClientSession() as session:
        response = await session.post(url=url,

                                      data=json.dumps({"text": message}), headers=headers)

        return (await response.json())['id']


class SendMessageData(BaseModel):
    amo_host: str
    amojo_hash: str
    chat_token: str
    message: str
    chat_id: str


async def send_message_handler(request):
    start_time = time.time()
    try:
        data = SendMessageData(**await request.json())
        return web.json_response({
            'status': True,
            'answer': await send_message(data.amo_host, data.amojo_hash, data.chat_token, data.message, data.chat_id),
            'execution_time': round(time.time() - start_time, 2)},
            status=200)

    except Exception as e:
        return web.json_response(
            {'status': False, 'answer': f"{e}", 'execution_time': round(time.time() - start_time, 2),
             }, status=400
        )
