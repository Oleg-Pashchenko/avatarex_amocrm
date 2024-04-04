import time

from aiohttp import web
from pydantic import BaseModel
import aiohttp


async def clear_field_by_id(field_id, pipeline_id, deal_id, host, headers):
    url = f"{host}ajax/leads/detail/"
    data = {
        f"CFV[{field_id}]": "",
        "lead[STATUS]": "",
        "lead[PIPELINE_ID]": pipeline_id,
        "ID": deal_id,
    }
    async with aiohttp.ClientSession() as session:
        response = await session.post(url, headers=headers, data=data, )
        return await response.json()


class ClearFieldsData(BaseModel):
    host: str
    pipeline_id: int
    headers: dict
    lead_id: int
    fields: list


async def clear_fields_handler(request):
    start_time = time.time()
    try:
        data = ClearFieldsData(**await request.json())

        for field in data.fields:
            await clear_field_by_id(field, data.pipeline_id, data.lead_id, data.host, data.headers)

        return web.json_response({'status': True, 'answer': "Поля успешно очищены!",
                                  'execution_time': round(time.time() - start_time, 2)}, status=200)

    except Exception as e:
        return web.json_response(
            {'status': False, 'answer': f'{e}', 'execution_time': round(time.time() - start_time, 2)},
            status=400)
