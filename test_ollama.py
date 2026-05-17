import urllib.request, json

data = json.dumps({
    'model':'qwen3.5:9b',
    'messages':[
        {'role':'system','content':'You must respond with valid JSON that matches this schema: {"greeting": {"type":"string"}}'},
        {'role':'user','content':'Say hello.'}
    ],
    'stream':False,
    'options':{'num_predict':500}
}).encode()
req = urllib.request.Request('http://estimator-ollama:11434/api/chat', data=data, headers={'Content-Type':'application/json'})
r = urllib.request.urlopen(req, timeout=30)
body = json.loads(r.read().decode())
print('content:', repr(body['message']['content']))
print('thinking:', repr(body['message'].get('thinking','(none)')))
print('eval_count:', body.get('eval_count'))
