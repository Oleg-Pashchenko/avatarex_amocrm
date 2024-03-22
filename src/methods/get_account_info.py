import time
import requests
from aiohttp import web
from pydantic import BaseModel

import requests


def get_pipelines_info(host, headers):
    response = requests.get(f"{host}ajax/v1/pipelines/list", headers=headers).json()["response"]["pipelines"]
    print(response.text)
    return [
        {
            'id': p["id"],
            'name': p["name"],
            'sort': p["sort"],
            'statuses': [
                {'id': s['id'], 'sort': s['sort'], 'name': s['name']}
                for s in p["statuses"].values()
            ]
        }
        for p in response.values()
    ]


def get_custom_fields(host, headers):
    response = requests.get(f"{host}api/v4/leads/custom_fields", headers=headers).json()["_embedded"]["custom_fields"]
    print(response.text)
    return [
        {
            'id': f['id'],
            'name': f['name'],
            'type': f['type'],
            'active_value': None,
            'possible_values': [
                {'id': v['id'], 'value': v['value'], 'sort': v['sort']}
                for v in (f["enums"] or [])
            ],
            'sort': f['sort']
        }
        for f in response if f["type"] != "tracking_data"
    ]


class SyncAvatarexData(BaseModel):
    amo_host: str
    headers: dict


async def get_account_info_handler(request):
    start_time = time.time()
    try:
        data = SyncAvatarexData(**await request.json())

        return web.json_response({
            'status': True,
            'answer': {
                'pipelines': get_pipelines_info(data.amo_host, data.headers),
                'fields': get_custom_fields(data.amo_host, data.headers)
            },
            'execution_time': round(time.time() - start_time, 2)
        })

    except Exception as e:
        return web.json_response(
            {'status': False, 'answer': f'{e}', 'execution_time': round(time.time() - start_time, 2)},
            status=400)
