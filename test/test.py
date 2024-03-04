import json

f = json.load(open('test.json', 'r'))
for t in f["_embedded"]["talks"]:
    print(t)