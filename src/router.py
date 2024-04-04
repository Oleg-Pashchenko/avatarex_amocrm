from aiohttp import web

from src.methods import *
from src.methods.add_tokens import add_tokens_handler

app = web.Application()
app.router.add_post("/create-tokens/", create_tokens_handler)
app.router.add_post("/add-tokens/", add_tokens_handler)
app.router.add_post("/move-deal/", move_deal_handler)
app.router.add_post("/get-fields/", get_fields_handler)
app.router.add_post('/fill-field/', fill_fields_handler)
app.router.add_post('/get-account-info/', get_account_info_handler)
app.router.add_post('/send-message/', send_message_handler)
app.router.add_post('/get-messages/', get_messages_handler)
app.router.add_post('/clear-fields/', clear_fields_handler)