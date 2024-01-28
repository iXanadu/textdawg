import requests
import logging
from urllib.parse import urlencode, urljoin
import csv

logger = logging.getLogger(__name__)

class FUBApiHandler:
    def __init__(self, api_url, api_key,x_system, x_system_key):
        """
        Initialize the API handler with API URL and key.
        :param api_url: Base URL of the API.
        :param api_key: API key for authorization.
        ;param x_system: FUB's System Name
        ;param x_system_key: FUB's System Key
        """
        logging.info(f"{api_url,api_key}")
        self.base_url = api_url.rstrip('/') + '/'  # Ensure trailing slash
        self.api_key = api_key
        self.x_system = x_system
        self.x_system_key = x_system_key
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Basic {self.api_key}',
            'X-System': self.x_system,
            'X-System-Key': x_system_key,
            'Accept': 'application/json'
        })
    def _generate_url(self, path):
        """
        Generate the full URL for an API request.
        :param path: API endpoint path.
        :return: Full URL.
        """
        return urljoin(self.base_url, path.lstrip('/'))

    def _make_request(self, method, path, query_params=None, data=None):
        """
        Make an HTTP request to the API.
        :param method: HTTP method (GET, POST, PUT).
        :param path: API endpoint path.
        :param query_params: Parameters to be sent in the query string.
        :param data: Data to be sent in the body of the request.
        :return: JSON response from the API or None in case of failure.
        """
        url = self._generate_url(path)
        try:
            response = self.session.request(method, url, params=query_params, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as err:
            logging.error(f"Request Error ({method} {url}): {err}")
            return None

    # Example of a refactored method with comments
    def get_people(self, id=0, email='', phone_number='', limit=10, offset=0, sort='created', fields='allFields',
                   include_trash=False, include_unclaimed=False):
        """
        Retrieve a list of people or a specific person by ID.
        :param id: ID of a specific person (optional).
        :param email: Filter by email (optional).
        :param phone_number: Filter by phone number (optional).
        :param limit: Limit the number of results.
        :param offset: Offset for pagination.
        :param sort: Sorting order.
        :param fields: Fields to include in the response.
        :param include_trash: Include trashed records if True.
        :param include_unclaimed: Include unclaimed records if True.
        :return: JSON response containing people data.
        """
        path = '/v1/people'
        query_params = {
            'email': email,
            'phone': phone_number,
            'sort': sort,
            'limit': limit,
            'offset': offset,
            'fields': fields,
            'includeTrash': str(include_trash).lower(),
            'includeUnclaimed': str(include_unclaimed).lower()
        }

        if id:
            path += f"/{id}"
            query_params = {}  # No additional query params needed for specific person

        return self._make_request('GET', path, query_params)

    def get_fubid_with_phone(self, phone_number, fields='firstName,lastName', limit=1, offset=0, sort='created',
                             include_trash=False, include_unclaimed=False):
        """
        Retrieve the first person's ID matching a given phone number.
        :param phone_number: Phone number to search for.
        :param fields: Fields to include in the response.
        :param limit: Limit the number of results (defaults to 1).
        :param offset: Offset for pagination.
        :param sort: Sorting order.
        :param include_trash: Include trashed records if True.
        :param include_unclaimed: Include unclaimed records if True.
        :return: ID of the person or 0 if not found.
        """
        response = self.get_people(phone_number=phone_number, fields=fields, limit=limit, offset=offset, sort=sort,
                                   include_trash=include_trash, include_unclaimed=include_unclaimed)

        if response and response.get('_metadata', {}).get('total', 0) > 0:
            return response['people'][0]['id']
        return 0

    def add_update_fub_contact(self, fubId, phone_number, query):
        """
        Add or update a FUB contact.
        :param fubId: ID of the contact in FUB.
        :param phone_number: Phone number of the contact.
        :param query: Query string or message associated with the contact.
        :return: ID of the updated or added person.
        """
        description = f"User texted {query}"
        payload = {
            "person": {
                "contacted": False,
                "phones": [{"isPrimary": True, "value": phone_number, "type": "mobile"}],
                "tags": ["textDawg Lead", query],
                "stage": "Lead",
                "id": fubId
            },
            "type": "Inquiry",
            "message": "Text Code Submitted",
            "description": description,
            "source": "textDawg",
            "system": "textDawg"
        }

        fub_response = self.add_lead(payload)
        return fub_response.get('id', 0) if fub_response else 0

    def log_fub_text_message(self, incoming, fubID, to_phone, from_phone, message):
        """
        Log a text message in FUB.
        :param incoming: Boolean indicating if the message is incoming.
        :param fubID: ID of the person associated with the message in FUB.
        :param to_phone: Phone number of the receiver.
        :param from_phone: Phone number of the sender.
        :param message: Text of the message.
        """
        path = '/v1/textMessages'
        label = f"Incoming text from {from_phone} => {to_phone}" if incoming else f"Outgoing text from {from_phone} => {to_phone}"
        payload = {
            "isIncoming": incoming,
            "personId": fubID,
            "message": message,
            "toNumber": to_phone,
            "fromNumber": from_phone,
            "externalLabel": label
        }

        self._make_request('POST', path, data=payload)

    def get_contact_from_fub(self, fubId=0, phone_number='', fields='firstName,lastName,emails,phones', limit=1,
                             offset=0, sort='created',
                             include_trash=False, include_unclaimed=False):
        """
        Retrieve contact information from FUB.
        :param fubId: ID of the contact in FUB.
        :param phone_number: Phone number of the contact.
        :param fields: Fields to include in the response.
        :param limit: Limit the number of results.
        :param offset: Offset for pagination.
        :param sort: Sorting order.
        :param include_trash: Include trashed records if True.
        :param include_unclaimed: Include unclaimed records if True.
        :return: Contact information or False if not found.
        """
        path = f'/v1/people/{fubId}' if fubId else '/v1/people'
        query_params = {
            'phone': phone_number,
            'sort': sort,
            'limit': limit,
            'offset': offset,
            'fields': fields,
            'includeTrash': str(include_trash).lower(),
            'includeUnclaimed': str(include_unclaimed).lower()
        }

        response = self._make_request('GET', path, query_params=query_params)
        if response and response.get('_metadata', {}).get('total', 0) > 0:
            person = {"fubId": response['people'][0]['id']}
            for field in fields.split(','):
                person[field] = response['people'][0].get(field, None)
            return person

        return False

    def old_get_text_messages(self, id):
        path = f'/v1/textMessages?personId={id}'
        return (self._make_request('GET', path))

    def get_text_messages(self, id):
        base_path = f'/v1/textMessages?personId={id}'
        next_path = base_path  # Start with the base path

        all_text_messages = []
        print(f"Outside while, next_path is: {next_path}")
        while next_path:
            # Make an API request using your _make_request method with the current path
            print(f"PATH:{next_path}")
            response = self._make_request('GET', next_path)
            print(response)
            if response is None:
                break

            # Extract the 'textmessages' list from the response and extend the list
            text_messages = response.get('textmessages', [])
            all_text_messages.extend(text_messages)

            # Check if there is a 'nextLink' in the metadata to determine if there are more pages
            next_path = response['_metadata'].get('nextLink')

        # Create a request structure with 'textmessages' as an item containing all text messages
        request_structure = {
            'textmessages': all_text_messages
        }

        return request_structure

    def get_bulk_text_messages(self):

        path = f'/v1/people'
        query_params = {
            'sort': 'created',
            'limit': '100',
            'offset': 3000,
            'fields': 'firstName,lastName,stage,source',
            'source': 'explorevirginiahomes.com',
            'includeTrash': 'false',
            'includeUnclaimed': 'false'
        }

        response = self._make_request('GET', path, query_params=query_params)
        csv_file_path = 'textmessages.csv'
        columns_to_include = ['id', 'created', 'updated', 'personId', 'status', 'message', 'fromNumber', 'toNumber',
                              'sent']
        with open(csv_file_path, mode='w', newline='') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=columns_to_include)
            writer.writeheader()
            for person in response['people']:
                person_id = person['id']
                text_messages_response = self.get_text_messages(person_id)
                text_messages = text_messages_response.get('textmessages', [])

                # Write the data rows for text messages
                for message in text_messages:
                    row = {col: message[col] for col in columns_to_include}
                    writer.writerow(row)

        return f'CSV file saved to {csv_file_path}'

    def update_person(self, person_id, update_data):
        payload = {}

        # Add firstName and lastName to payload if they exist and are not empty
        if 'firstName' in update_data and update_data['firstName']:
            payload['firstName'] = update_data['firstName']
        if 'lastName' in update_data and update_data['lastName']:
            payload['lastName'] = update_data['lastName']

        # Handle emails separately
        if 'email' in update_data and update_data['email']:
            payload['emails'] = [{
                "isPrimary": True,
                "value": update_data['email'],
                "type": "home"
            }]

        # Check if the payload is empty
        if not payload:
            logger.error("FUB-update_person called without data")
            return None

        path = f'/v1/people/{person_id}'
        return self._make_request('PUT', path, data=payload)

    def add_lead(self, update_data):
        """
        Add a lead to FUB.
        :param update_data: Data for the lead to be added.
        :return: JSON response from the API.
        """
        path = '/v1/events'
        return self._make_request('POST', path, data=update_data)

        # ... additional CRUD methods as needed ...

