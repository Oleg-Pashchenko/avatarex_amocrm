import json

f = json.load(open('test.json', 'r'))
for t in f["_embedded"]["talks"]:
    if 'wazzup' in t['chat_source']:
        print(t['last_message'])