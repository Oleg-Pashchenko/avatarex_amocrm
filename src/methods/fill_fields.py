import time

from aiohttp import web
from pydantic import BaseModel
import aiohttp


async def set_field_by_id(field_id: int, value, pipeline_id, deal_id, host, headers):
    url = f"{host}ajax/leads/detail/"
    data = {
        f"CFV[{field_id}]": value,
        "lead[STATUS]": "",
        "lead[PIPELINE_ID]": pipeline_id,
        "ID": deal_id,
    }
    async with aiohttp.ClientSession() as session:
        response = await session.post(url, headers=headers, data=data, proxy=f'http://odpashitmo:W7XKeLNJjC@149.126.218.163:50100')
        return await response.json()


class FillFieldsData(BaseModel):
    lead_id: int
    field_id: int
    pipeline_id: int
    value: str
    host: str
    headers: dict


async def fill_fields_handler(request):
    start_time = time.time()
    try:
        data = FillFieldsData(**await request.json())

        response = await set_field_by_id(
            deal_id=data.lead_id,
            field_id=data.field_id,
            pipeline_id=data.pipeline_id,
            value=data.value,
            host=data.host,
            headers=data.headers
        )
        return web.json_response({'status': True, 'answer': response,
                                  'execution_time': round(time.time() - start_time, 2)}, status=200)

    except Exception as e:
        return web.json_response(
            {'status': False, 'answer': f'{e}', 'execution_time': round(time.time() - start_time, 2)},
            status=400)
