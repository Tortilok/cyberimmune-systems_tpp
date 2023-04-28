import requests


dataset = [
    {
        "case": {
            "login": "login",
            "password": "password_hash",
            "license": "c0pIa2poM284LC5zZGZsa1iHhcMDwZinSlA/fUI2dFg="
        },
        "expected": 200
    },
    {
        "case": {
            "logn": "login",
            "password": "password_hash",
            "license": "c0pIa2poM284LC5zZGZsa1iHhcMDwZinSlA/fUI2dFg="
        },
        "expected": 400
    },
    {
        "case": {
            "login": "login",
            "password": "password_hash"
        },
        "expected": 400
    },
    {
        "case": {
            "login": "login",
            "password": "dasd",
            "license": "c0pIa2poM284LC5zZGZsa1iHhcMDwZinSlA/fUI2dFg="
        },
        "expected": 403
    },
    {
        "case": {
            "login": "login",
            "password": "password_hash",
            "license": "FnSlA/fUI2dFg="
        },
        "expected": 403
    },
]


print('Simple test')
print('')
counter = len(dataset)
URL = 'http://127.0.0.1:8000'
for data in dataset:
    response = requests.post(f'{URL}/sensors', json=data['case'])
    print(response.json(), '-', response.status_code, end=' ')
    if response.status_code == data['expected']:
        print('OK!')
        continue

    print('ERROR!')
    counter -= 1

print('-'*5, 'TOTAL', '-'*5)
print(f'{counter} / {len(dataset)} - {counter / len(dataset) * 100}%')
print('-'*17)