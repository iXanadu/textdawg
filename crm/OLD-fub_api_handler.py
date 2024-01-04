import requests
import logging
from urllib.parse import urlencode, urlunparse
import json

class FUBApiHandler:
    def __init__(self, api_url, api_key):
        self.base_url = api_url
        self.api_key = api_key

    def _generate_url(self, path, query_params):
        query_string = urlencode(query_params)
        url = urlunparse(('https', self.base_url, path, '', query_string, ''))
        return url

    def _make_request(self, method, path, query_params=None, data=None):
        url = self._generate_url(path, query_params or {})
        headers = { 'X-System': 'Trustworthy-Agents-Group-TextDawg',
                    'X-System-Key': 'e837cee25caa37d1fbcb15b9b2f40df4',
                   "accept": "application/json",
                   'Authorization': f'Basic {self.api_key}'}
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                headers["content-type"] = "application/json"
                response = requests.post(url, json=data, headers=headers)
                headers.__delitem__("content-type")
            elif method == 'PUT':
                headers["content-type"] = "application/json"
                response = requests.put(url, json=data, headers=headers)
                headers.__delitem__("content-type")
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as errh:
            logging.error(f"HTTP Error: {errh} for URL: {url}")
            return None
        except requests.exceptions.ConnectionError as errc:
            logging.error(f"Error Connecting: {errc}")
            return None
        except requests.exceptions.Timeout as errt:
            logging.error(f"Timeout Error: {errt}")
            return None
        except requests.exceptions.RequestException as err:
            logging.error(f"Make Request Error: {err}")
            return None

    def get_people(self, id=0, email='', phone_number='', limit=10, offset=0, sort='created', fields='allFields',
                   include_trash=False, include_unclaimed=False):
        path = '/v1/people'
        query_params = {
            'sort': sort,
            'limit': limit,
            'offset': offset,
            'fields': fields,
            'includeTrash': str(include_trash).lower(),
            'includeUnclaimed': str(include_unclaimed).lower()
        }
        if id:
            path += "/" + str(id)
        else:
            if email != '':
                query_params['email'] = email
            if phone_number != '':
                query_params['phone'] = phone_number

        return self._make_request('GET', path, query_params=query_params)

    def get_fubid_with_phone(self, phone_number='', fields='firstName,lastName', limit=1, offset=0, sort='created',
                   include_trash=False, include_unclaimed=False):
        path = '/v1/people'
        query_params = {
            'phone': phone_number,
            'sort': sort,
            'limit': limit,
            'offset': offset,
            'fields': fields,
            'includeTrash': str(include_trash).lower(),
            'includeUnclaimed': str(include_unclaimed).lower()
        }

        response =  self._make_request('GET', path, query_params=query_params)

        total_value = response['_metadata']['total']
        if total_value > 0:
            person_id = response['people'][0]['id']
        else:
            person_id = 0

        return person_id

    def add_update_fub_contact(self, fubId, phone_number, query):
        description = "User texted " + query
        payload = {
            "person": {
                "contacted": False,
                "phones": [
                    {
                        "isPrimary": True,
                        "value": phone_number,
                        "type": "mobile"
                    }
                ],
                "tags": ["textDawg Lead", query],
                "stage": "Lead"
            },
            "type": "Inquiry",
            "message": "Text Code Submitted",
            "description": description,
            "source": "textDawg",
            "system": "textDawg"
        }
        payload["person"]["id"] = fubId
        fub_response = None
        if payload:
            fub_response = self.add_lead(payload)

        if fub_response:
            person_id = fub_response['id']
        else:
            person_id = 0

        return person_id


    def log_fub_text_message(self,incoming, fubID,to_phone,from_phone,message):
        path = '/v1/textMessages'
        if incoming:
            label = f"Incoming text from {from_phone} => {to_phone}"
        else:
            label = f"Outgoing text from {from_phone} => {to_phone}"
        payload = {
            "isIncoming": incoming,
            "personId": fubID,
            "message": message,
            "toNumber": to_phone,
            "fromNumber": from_phone,
            "externalLabel": label
        }
        if payload:
            fub_response = self._make_request('POST', path, data=payload)


    def get_contact_from_fub(self, fubId=0, phone_number='',fields='firstName,lastName,emails,phones', limit=1, offset=0, sort='created',
                   include_trash=False, include_unclaimed=False):
        path = '/v1/people'
        if fubId:
            path += f"/{fubId}"

        query_params = {
            'phone': phone_number,
            'sort': sort,
            'limit': limit,
            'offset': offset,
            'fields': fields,
            'includeTrash': str(include_trash).lower(),
            'includeUnclaimed': str(include_unclaimed).lower()
        }

        response =  self._make_request('GET', path, query_params=query_params)

        total_value = response['_metadata']['total']
        person = {
            "fubId": 0,
        }

        if total_value > 0:
            person["fubId"] = response['people'][0]['id']
            field_list = fields.split(',')
            for field in field_list:
                person[field] = response['people'][0][field]
        else:
            person = False

        return person

    def update_person(self, person_id, update_data):
        path = f'/v1/people/{person_id}'
        return self._make_request('PUT', path, data=update_data)

    def add_lead(self, update_data):
        path = f'/v1/events'
        return self._make_request('POST', path, data=update_data)

    # Additional CRUD methods can be added here

