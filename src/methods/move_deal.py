import asyncio
import time

import aiohttp
from aiohttp import web
from pydantic import BaseModel, ValidationError


class AmocrmMoveError(Exception):
    pass


async def move_deal(host, headers, deal_id: int, pipeline_to_set_id: int, status_to_set_id: int):
    async with aiohttp.ClientSession() as session:
        response = await session.post(url=f'{host}ajax/leads/detail/',
                                      headers=headers,
                                      proxy=f'http://odpashitmo:W7XKeLNJjC@149.126.218.163:50100',
                                      data={
                                          'ID': deal_id,
                                          'lead[STATUS]': status_to_set_id,
                                          'lead[PIPELINE_ID]': pipeline_to_set_id
                                      })
        if response.status != 200:
            raise AmocrmMoveError("Перемещение сделки не удалось!")


class MoveDealData(BaseModel):
    amo_host: str
    headers: dict
    deal_id: int
    pipeline_id_to_set: int
    status_id_to_set: int


async def move_deal_handler(request):
    start_time = time.time()
    try:
        data = await request.json()
        print(data)
        validated_data = MoveDealData(**data)
        await move_deal(
            deal_id=validated_data.deal_id,
            pipeline_to_set_id=validated_data.pipeline_id_to_set,
            status_to_set_id=validated_data.status_id_to_set, host=validated_data.amo_host,
            headers=validated_data.headers)
        return web.json_response({
            'status': True,
            'answer': "Сделка успешно перенесена!",
            'execution_time': round(time.time() - start_time, 2)
        })

    except (ValidationError, ConnectionError, Exception, AmocrmMoveError) as e:
        return web.json_response({
            'status': False,
            'answer': f'{type(e).__name__}: {e}',
            'execution_time': round(time.time() - start_time, 2)
        })
