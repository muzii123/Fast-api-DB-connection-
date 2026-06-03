import urllib.request, urllib.parse, json

def req(method, url, data=None):
    if data is not None:
        data = json.dumps(data).encode()
        headers = {'Content-Type': 'application/json'}
    else:
        headers = {}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode()
            print(method, url, resp.status)
            if body:
                try:
                    print(json.dumps(json.loads(body), indent=2))
                except Exception:
                    print(body)
            return body
    except Exception as e:
        print(method, url, 'ERROR', e)
        return None

base = 'http://127.0.0.1:8000'

print('Creating product...')
req('POST', f'{base}/product?price=100&discount=10')

print('\nCreating cart...')
req('POST', f'{base}/cart', {"user_id": 1})

print('\nAdding item...')
req('POST', f'{base}/cart/add', {"cart_id": 1, "product_id": 1, "quantity": 2})

print('\nRemoving item id 1...')
req('DELETE', f'{base}/cart/remove/1')
