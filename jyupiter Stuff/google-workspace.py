from json import dumps
from httplib2 import Http


def main():
    """Google Chat incoming webhook quickstart."""
    url = 'https://chat.googleapis.com/v1/spaces/AAAAQJ_aXxA/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=MN4oAHYTGsgAH7zjUE3V9frhO4DlG9ce4xPZFtgXovE'
    app_message = {"text": "Hello from a Python script!"}
    message_headers = {"Content-Type": "application/json; charset=UTF-8"}
    http_obj = Http()
    response = http_obj.request(
        uri=url,
        method="POST",
        headers=message_headers,
        body=dumps(app_message),
    )
    print(response)


if __name__ == "__main__":
    main()
