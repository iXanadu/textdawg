import requests

url = "https://api.followupboss.com/v1/textMessages"

payload = {
    "isIncoming": False,
    "personId": 14479,
    "message": "Got your message - standby for a response",
    "toNumber": "7576202239",
    "fromNumber": "7577528095",
    "externalLabel": "from TextDawg"
}
headers = {
    "accept": "application/json",
    "X-System": "Trustworthy-Agents-Group-TextDawg",
    "X-System-Key": "e837cee25caa37d1fbcb15b9b2f40df4",
    "content-type": "application/json",
    "authorization": "Basic ZmthXzB2QmFtZjRkWm8xa1gzMVJBaXI0ZnRVNGMyQjJVMnNLY3o6"
}

response = requests.post(url, json=payload, headers=headers)

print(response.text)