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
            access = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6ImNjM2FiYWZiZjdhYjQxNWM4ZmUwNDNiNmU5ZmU2ZjMyOTQ4MDY5Y2IyOTkxNzRjNjlmYjAzYzg2MGUwNWZkZjliYTMzZmQ4MGE5NWM3NDI5In0.eyJhdWQiOiJjODE1NWI1NS1mYzg5LTQ2MDItOWY1Ny0yZDFiZTBjMGVjNDciLCJqdGkiOiJjYzNhYmFmYmY3YWI0MTVjOGZlMDQzYjZlOWZlNmYzMjk0ODA2OWNiMjk5MTc0YzY5ZmIwM2M4NjBlMDVmZGY5YmEzM2ZkODBhOTVjNzQyOSIsImlhdCI6MTcxMTMwODQ5MSwibmJmIjoxNzExMzA4NDkxLCJleHAiOjE3MTEzOTQ4NDMsInN1YiI6IjEwODQ1NzIyIiwiZ3JhbnRfdHlwZSI6IiIsImFjY291bnRfaWQiOjMxNjU1Mjg2LCJiYXNlX2RvbWFpbiI6ImFtb2NybS5ydSIsInZlcnNpb24iOjIsInNjb3BlcyI6WyJwdXNoX25vdGlmaWNhdGlvbnMiLCJjcm0iLCJub3RpZmljYXRpb25zIl0sImhhc2hfdXVpZCI6bnVsbH0.XA46YHmF5us7xCnJmTID1XAVogm1ugSFnzUeBjt4qUYuuYWJuMfP1WBhIJoAzPH5Y2cqHKom5Yrcka4wKnmbgFMIjFe6Hyw8fF8e0bFPUZa60HNdXerT1TgLCRmAgMwJV7SuJhfwJjqAPB9Y2aYLcwrwm-0qgd-NAOa4fH8rC22zYi74HfqAWiAuqYAJW4vUdT42ScHmAERwEla_1TBR2-VeHQmLYZ5qkYYprfuiGC6tevaVM47RxgdNdPr0MOn84qvf5jDXRr7wnHz7IqDM1bP6Q0zNlqsw2UngX4VUnhN2VHvjX9RcXJGEHXAWnqqONqpdkGZx0JDzjd4V1F_g7g'
            refresh = 'def502002b3ee86cea4e49caaf6235392b1e94fb951e7a9b0db363dc603d24be94f02e1085780832f80fa2b52e2411f94f011f57c7c5b3e1562e098dba941663c0641dfb72910e7b8284c26bc480fb3537286b59afcdfd12121b4d0686f7e558777ed0f68c5ca912c2baab4e315923943eb9828918f7b7bb3d5517765c2ab9890e52acbf9cebdff6d03d1874fd70ee526bb2d9fa8052a37a0a1c08d3e5f39fe6082c501e4d7c6a4ca7a22c7821b6341aec0da02d650edfb18f2f8a1e3fe2b1d0b28c95e722e515c1d61459ba4101e43193b7917c11c76fda01e415ee4235c5a5ccee3f8a35bfd57abfa609cd5ffbde4677f72cb345c0151e23170466abf00a27579f79a0beac5eab799d48095afcda863d5fb6346e9ff1043367fd020c1ab40e6c2b29f68c5c15e1152b5c6206a5aace6017e5607d16d1a2d269975a0511a003d0938bb4d9226175b1088d6496c64f61fe634522a0ac566e963d4593701c2f16edb6291bba9d907e53999cedfac05d5bf79a656559657f08677be47c86212e2c7e66ff3b63409e5ce519991ca12ad7513586940b9b566da27b7cf2e572f61ca0ec18711141e581e5568c119ed7b07482cdcdb4bd9ccf43230a4347395f572cad66b4adb80128679397401c49486295f33a83702d18e394'
            headers = {
                'Accept': '/',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'User-Agent': 'PostmanRuntime/7.31.0',
                'Authorization': headers['Authorization'],
                'Host': host.replace('https://', '').replace('/', '')
            }
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
                print(t)
                if 'Salesbot' in t['last_message']['author']:
                    continue

                if int(time.time()) - t['last_message']['last_message_at'] > 60 * 60 * 24:
                    continue

                chat_id, message, pipeline_id, lead_id, status_id = (
                    t["chat_id"], t["last_message"]["text"], int(t["entity"]["pipeline_id"]),
                    int(t["entity"]["id"]), int(t["entity"]["status_id"])
                )

                url = f"{amojo_host}messages/{amo_hash}/merge?stand=v16&offset=0&limit=20&chat_id%5B%5D={chat_id}&get_tags=true&lang=ru"
                r = await session.get(url, headers={"X-Auth-Token": chat_token})

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
        print(e)
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
