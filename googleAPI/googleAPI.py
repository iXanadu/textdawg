from dotenv import load_dotenv
from json import dumps
from httplib2 import Http

class GoogleAPI:

    def __init__(self):
        load_dotenv()
        self.is_initialized = True

    def post_message_to_agent_workspace(self,message):
        url = 'https://chat.googleapis.com/v1/spaces/AAAAQJ_aXxA/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=MN4oAHYTGsgAH7zjUE3V9frhO4DlG9ce4xPZFtgXovE'
        app_message = {"text": message}
        message_headers = {"Content-Type": "application/json; charset=UTF-8"}
        http_obj = Http()
        response = http_obj.request(
            uri=url,
            method="POST",
            headers=message_headers,
            body=dumps(app_message),
        )