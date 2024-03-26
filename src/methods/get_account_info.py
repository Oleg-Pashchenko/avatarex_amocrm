import asyncio
import time
import requests
from aiohttp import web
from pydantic import BaseModel

import requests


def get_pipelines_info(host, headers):
    response = requests.get(f"{host}ajax/v1/pipelines/list", headers=headers).json()
    print(response)
    response = response["response"]["pipelines"]
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
    response = requests.get(f"{host}api/v4/leads/custom_fields", headers=headers).json()
    print(response)
    response = response["_embedded"]["custom_fields"]
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

amo_host = 'https://bukhonin1991.amocrm.ru/'
headers = {'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6ImYxYmM3ZmNhMzgyMDc5NjA1NjIzZTNmNTBkNDVlZTE2ZTA0ZDIyM2I2NzQyMjNjODRlNzQ3YmFhMGM2ZGVmMTJmM2MzMDY2ZTY1MDEwNGQyIn0.eyJhdWQiOiIyMmRkMzc0Mi0yMzc2LTRmMDctYTg5Ni00ZDI2ODRkNzdjOTkiLCJqdGkiOiJmMWJjN2ZjYTM4MjA3OTYwNTYyM2UzZjUwZDQ1ZWUxNmUwNGQyMjNiNjc0MjIzYzg0ZTc0N2JhYTBjNmRlZjEyZjNjMzA2NmU2NTAxMDRkMiIsImlhdCI6MTcxMTM1MTM4MCwibmJmIjoxNzExMzUxMzgwLCJleHAiOjE3MTE0MzYzOTgsInN1YiI6IjkxMjU4NTAiLCJncmFudF90eXBlIjoiIiwiYWNjb3VudF9pZCI6MzA3OTU1MjYsImJhc2VfZG9tYWluIjoiYW1vY3JtLnJ1IiwidmVyc2lvbiI6Miwic2NvcGVzIjpbInB1c2hfbm90aWZpY2F0aW9ucyIsImNybSIsIm5vdGlmaWNhdGlvbnMiXSwiaGFzaF91dWlkIjpudWxsfQ.Qim6qDDzrgNTFsOxDShsKSx9aUvFDsc7F1txqMYtEFImxy5LAEqnlUkIVXhNu_Plgm9efyfG5dnQzNmvRbm345V1ByAhffphxIFvziZzhk3qn3XVV8Fag1u06Lgggpcxf5ksqoHDgGvZQzaB5KXi0DvhB-7d3h8AEgOh4tHleWPdyip5wmICx34LzqfgvWNjvKmd5yPNYOTj0AltZTF4m2LVnCMltB-IwUxZYj759poK2SzuiWK0WxOA3zhiKb4WpUuKkCf3z7sTSOR_nxaOKgudyh0VmSFNylSDeSO6WxRTwnEwsXEG9oCoMLpVkVcKZf9iAzTYyWSA7OF3EmIP3w', 'X-Requested-With': 'XMLHttpRequest'}
# print(asyncio.run(get_custom_fields(amo_host, headers)))
