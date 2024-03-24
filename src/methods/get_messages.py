import asyncio
import json
import time

import aiohttp
from aiohttp import web
from pydantic import BaseModel


async def get_unanswered_messages(host: str, headers: dict, pipeline_id: int, stage_ids: list[int], amo_hash: str,
                                  chat_token: str):
    amojo_host = 'https://amojo.amocrm.ru/' if 'amocrm' in host else 'https://amojo.kommo.com/'
    try:
        if not stage_ids:
            return []

        url = f"{host}ajax/v4/inbox/list"

        if 'Authorization' in headers.keys():
            headers = {
                'Accept': '/',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'User-Agent': 'PostmanRuntime/7.31.0',
                'Authorization': headers['Authorization'],
                'Host': host.replace('https://', '').replace('/', '')
            }
        print(headers)
        params = {
            "limit": 100,
            "order[sort_by]": "last_message_at",
            "order[sort_type]": "desc",
            "filter[is_read][]": "false",
            'filter[status][]': 'opened',
            **{f"filter[pipe][{pipeline_id}][{index}]": param for index, param in enumerate(stage_ids)}
        }

        async with aiohttp.ClientSession() as session:
            talks = await session.get(url=url, headers=headers, params=params, )
            print(talks.status)
            talks = await talks.json()
            print(talks)
            response = []
            await asyncio.sleep(1)

            for t in talks["_embedded"]["talks"]:
                if 'Salesbot' in t['last_message']['author']:
                    continue

                if int(time.time()) - t['last_message']['last_message_at'] > 60 * 60 * 24:
                    continue

                chat_id, message, pipeline_id, lead_id, status_id = (
                    t["chat_id"], t["last_message"]["text"], int(t["entity"]["pipeline_id"]),
                    int(t["entity"]["id"]), int(t["entity"]["status_id"])
                )

                url = f"{amojo_host}messages/{amo_hash}/merge?stand=v16&offset=0&limit=20&chat_id%5B%5D={chat_id}&get_tags=true&lang=ru"
                r = await session.get(url,  headers={"X-Auth-Token": chat_token})

                try:
                    messages_history = await r.json()
                    if message == "🔊":
                        message = messages_history["message_list"][0]["message"]["attachment"]["media"]
                    response.append(
                        {
                            'id': messages_history["message_list"][0]['id'],
                            'chat_id': chat_id,
                            'answer': message,
                            'pipeline_id': pipeline_id,
                            'lead_id': lead_id,
                            'status_id': status_id,
                            'messages_history': json.dumps(messages_history)
                        }

                    )
                except Exception:
                    pass  # Ignore if user deleted the message

        return response
    except Exception as e:
        return []


class GetMessagesData(BaseModel):
    amo_host: str
    amojo_hash: str
    chat_token: str
    pipeline_id: int
    stage_ids: list[int]
    headers: dict


async def get_messages_handler(request):
    start_time = time.time()
    try:
        data = GetMessagesData(**await request.json())
        return web.json_response(
            {
                'status': True,
                'answer': await get_unanswered_messages(data.amo_host, data.headers, data.pipeline_id,
                                                        data.stage_ids, data.amojo_hash, data.chat_token),
                'execution_time': round(time.time() - start_time, 2)
            },
            status=200)

    except Exception as e:
        return web.json_response(
            {'status': False, 'answer': f"{e}", 'execution_time': round(time.time() - start_time, 2),
             }, status=400
        )


headers = {'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6IjFiNDdlZDRlOTU5ZjYwNDRiOTBmYWUxYWMxZmFiZjUyYjliNWJmMTNlZWEzZmI3MjAwZmRlOTU1MTAwYWE2YjJmZGRlZmYxNjg2ZjdiZGIwIn0.eyJhdWQiOiI4MDM2MDg5My1kNDViLTRiMzYtOTYyMi02MWU2OWQ0N2FlMjQiLCJqdGkiOiIxYjQ3ZWQ0ZTk1OWY2MDQ0YjkwZmFlMWFjMWZhYmY1MmI5YjViZjEzZWVhM2ZiNzIwMGZkZTk1NTEwMGFhNmIyZmRkZWZmMTY4NmY3YmRiMCIsImlhdCI6MTcxMTEyNTYzMCwibmJmIjoxNzExMTI1NjMwLCJleHAiOjE3MTEyMTIwMzAsInN1YiI6IjEwODQxMzIyIiwiZ3JhbnRfdHlwZSI6IiIsImFjY291bnRfaWQiOjMxNjUyMjY2LCJiYXNlX2RvbWFpbiI6ImFtb2NybS5ydSIsInZlcnNpb24iOjIsInNjb3BlcyI6WyJwdXNoX25vdGlmaWNhdGlvbnMiLCJjcm0iLCJub3RpZmljYXRpb25zIl0sImhhc2hfdXVpZCI6ImQ0NmUzZjg2LTliMzUtNDA1Ni04M2FlLWIxMjkwZWVlOWIzYyJ9.WhAflPz9xUX5j8HvhrPt_qXDa9cvcneLkKuNBdIDA-dPGy4mSVM6iUoSEPbTXeibW9xssSZQf78NiIbufhJwgzzlxIU2EzUMlhoDXQxZj9UKTIs8vpPxxVCfAAwvu8HfbYRqQUafLXIlgZD5iyk7ulftMUNSyxzkz-Q1cy0ENtIl8R4FM3BS7O2MzzFFYRBt-9X89_xhe1ObPSDKdbBlHXh31UDnl5XU5y33WHEgVv3yTce1oFWsVUQglJrOnt2K8UoheayRzk6-krZejZT4BGzsdydJVczted-kji8-FXGRUtSHWMohSUGggcWcotKEpQD55gv-58ATmqUFUmu0Cg', 'X-Requested-With': 'XMLHttpRequest'}
print(asyncio.run(get_unanswered_messages(
    host='https://olegpashchenkosyncer.amocrm.ru/',
    headers=headers,
    pipeline_id=7962174,
    stage_ids=[65366830],
    amo_hash='f1197894-9b50-452f-bc64-adbdb4f8221e',
    chat_token='20975f25-1b8b-48d3-af08-b08a48324c65'
)))