
import json

json = json.loads(open ('groups.json').read())
print(json)
for r in json:
    print("az group delete --yes --no-wait -n %s" % (r['name']))