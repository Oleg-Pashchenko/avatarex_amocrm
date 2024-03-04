from aiohttp import web
from pydantic import BaseModel
import time
import aiohttp


async def get_custom_fields_async(host, headers):
    url = f"{host}api/v4/leads/custom_fields"
    async with aiohttp.ClientSession() as session:
        response = await session.get(url, headers=headers, proxy=f'http://odpashitmo:W7XKeLNJjC@149.126.218.163:50100')
        data = await response.json()
        return [
            {
                'id': f["id"],
                'name': f["name"],
                'type': f["type"],
                'active_value': None,
                'possible_values': [
                    {'id': v['id'], 'value': v['value'], 'sort': v['sort']}
                    for v in (f.get("enums") or [])
                ],
            }
            for f in data['_embedded']['custom_fields'] if f["type"] != "tracking_data"
        ]


async def get_fields_by_deal_id(host, headers, deal_id):
    url = f"{host}api/v4/leads/{deal_id}"
    fields = []
    async with aiohttp.ClientSession() as session:
        response = await session.get(url, headers=headers, proxy=f'http://odpashitmo:W7XKeLNJjC@149.126.218.163:50100')
        response = await response.json()
        try:
            for f in response["custom_fields_values"]:
                fields.append(
                    {
                        "id": f["field_id"],
                        "name": f["field_name"],
                        "type": f["field_type"],
                        "active_value": f["values"][0]["value"],
                        "possible_values": None,
                    }
                )
        except:
            pass
    all_fields = await get_custom_fields_async(host, headers)
    return {'fields': fields, 'all_fields': all_fields}


class GetFieldsData(BaseModel):
    lead_id: int
    amo_host: str
    headers: dict


async def get_fields_handler(request):
    start_time = time.time()
    try:
        data = GetFieldsData(**await request.json())
        return web.json_response({

            'status': True, 'answer': await get_fields_by_deal_id(data.amo_host, data.headers, data.lead_id),
            'execution_time': round(time.time() - start_time, 2),
        }, status=200)

    except Exception as e:
        return web.json_response(
            {'status': False, 'answer': f"{e}", 'execution_time': round(time.time() - start_time, 2),
             }, status=400
        )
