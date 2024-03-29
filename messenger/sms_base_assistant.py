import logging
from dotenv import load_dotenv
from langchain import hub
from langchain.prompts import PromptTemplate, SystemMessagePromptTemplate
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchRun, Tool
from langchain_community.utilities import GoogleSearchAPIWrapper
from FUBHandler.fub_api_handler import FUBApiHandler
from langchain.globals import set_verbose, set_debug
import os
import json
from main.models import TextCode, OpenAIPrompt
from googleAPI.googleAPI import GoogleAPI
from icecream import ic

# import pyowm
# from pyowm.owm import OWM
# from pyowm.commons import cityidregistry
# from langchain.utilities.openweathermap import OpenWeatherMapAPIWrapper

logger = logging.getLogger(__name__)


class SMSAIBaseAssistant:
    def __init__(self, temperature, model_name):
        load_dotenv()
        set_verbose(os.getenv('LLM_VERBOSE'))
        set_debug(os.getenv('LLM_DEBUG'))
        self.model_name = model_name
        self.model_temp = temperature
        self.fub_handler = FUBApiHandler(os.getenv('FUB_API_URL'), os.getenv('FUB_API_KEY'),
                                         os.getenv('FUB_X_SYSTEM'), os.getenv('FUB_X_SYSTEM_KEY'))
        self.google_cse_id = os.getenv("GOOGLE_EVH_CSE_ID")
        self.google_api = GoogleAPI()
        self.property_search = GoogleSearchAPIWrapper(google_cse_id=self.google_cse_id)
        self.general_search = DuckDuckGoSearchRun()
        # self.weather = OpenWeatherMapAPIWrapper()
        self.llm = ChatOpenAI(temperature=self.model_temp, model=self.model_name)

    def setup_agent(self, chat_history, msg_user):
        self.msg_user = msg_user
        self.chat_history = chat_history
        self.sys_msg = self.get_ai_instructions()
        self.conversational_agent = self.initialize_conversational_agent()

    def process_and_update_user_name(self, input):
        update_data = {}
        logger.info(f"IN process_and_update_user_name: {input}")
        parts = input.split()
        first_name = parts[0] if parts else None
        last_name = parts[1] if len(parts) > 1 else None
        if self.msg_user:
            # Update the msg_user object with new names
            if first_name:
                self.msg_user.firstname = first_name
                update_data['firstName'] = self.msg_user.firstname
            if last_name:
                self.msg_user.lastname = last_name
                update_data['lastName'] = self.msg_user.lastname
            # Save the updated user record
            self.msg_user.save()
            self.fub_handler.update_person(self.msg_user.fubId, update_data)
        else:
            logger.error("No user record is associated with this instance.")

        return (f"User name updated to {first_name} {last_name}")

    def process_and_update_user_email(self, input):
        update_data = {}
        logger.info(f"IN process_and_update_user_email: {input}")
        email = input
        if self.msg_user:
            # Update the msg_user object with new names
            if email:
                self.msg_user.email = email
                update_data['email'] = self.msg_user.email
            self.msg_user.save()
            self.fub_handler.update_person(self.msg_user.fubId, update_data)
        else:
            logger.error("No user record is associated with this instance.")

        return (f"User email updated to {email}")

    def post_alert_to_textdawg_ws(self, msg):
        logger.info(f"post_alert_to_textdawg_ws->msg=({msg}")
        if self.msg_user:
            fubId = self.msg_user.fubId
            fuburl = f'https://trustworthyagents.followupboss.com/2/people/view/{fubId}'
            msg = f"{msg}\n{fuburl}"
            logger.info(f"post_alert_to_textdawg_ws->updated_msg=({msg})")

        if hasattr(self.google_api, 'is_initialized') and self.google_api.is_initialized:
            self.google_api.post_message_to_agent_workspace(msg)
        else:
            logger.error("Error: google_api is not an instance of GoogleAPI or not properly initialized")

        return (f"Notice posted to textDawg Workspace")

    def property_results(self, query):
        logger.info(f"property_results->query=({query}")
        return self.property_search.results(query, 8)

    def search_results(self, query):
        return self.general_search.run(query, 8)

    # def weather_results(self, query):
    #     return self.weather.run(query)

    def get_text_code(self, input=""):
        r = TextCode.objects.filter(textcode=input).first()
        if r:
            return {'textcode': r.textcode, 'link': r.link, 'property_address': r.property_address,
                    'instructions': r.instructions}
        else:
            return {'textcode': '', 'link': '', 'property_address': '', 'instructions': ''}

    def get_userinfo_string(self):
        name = "the person"
        if not self.msg_user.firstname:
            nameStr = "NAME:  UNKNOWN - Ask at the first opportunity"
            phoneStr = f"PHONE:  {self.msg_user.phone_number}"
        else:
            name = self.msg_user.firstname
            nameStr = f"NAME: {self.msg_user.firstname} {self.msg_user.lastname}"
            phoneStr = f"PHONE: {self.msg_user.phone_number}"

        if not self.msg_user.email:
            emailStr = f"EMAIL: UNKNOWN Ask, but only if appropriate for contact or ESPECIALLY to set an appointment"
        else:
            emailStr = f"EMAIL: {self.msg_user.email}"

        sms_userinfo = f"Information about the person you are texting with:\n{nameStr}\n{phoneStr}\n{emailStr}\n"
        return (sms_userinfo)

    def get_ai_instructions(self):
        sms_userinfo = self.get_userinfo_string()
        active_prompt = OpenAIPrompt.get_active_prompt("SMS-TextCode-Base-Prompt")
        if active_prompt:
            formatted_prompt = active_prompt.prompt_text.replace("{SMS-UserInfo}", sms_userinfo)
            return (formatted_prompt)  # Use the active prompt
        else:
            return ("")

    def process_response(self, response):
        # Check if response is a string
        if isinstance(response, str):
            try:
                # Try parsing the string as JSON
                parsed_json = json.loads(response)
                return parsed_json  # Return the parsed JSON object
            except json.JSONDecodeError:
                # Parsing failed, so it's a plain string
                response = {'response': response}
                return response
        elif isinstance(response, dict):
            return response
        else:
            # The response is neither a string nor a dictionary
            return response

    def initialize_conversational_agent(self):

        post_alert_to_textdawg_ws = Tool(
            name="post_alert_to_textdawg_ws",
            description="Useful to alert agents that a person wants a call or contact",
            func=self.post_alert_to_textdawg_ws
        )
        process_and_update_user_name = Tool(
            name="process_and_update_user_name",
            description="Useful when you get a new or different name from the person you are chatting with",
            func=self.process_and_update_user_name
        )
        process_and_update_user_email = Tool(
            name="process_and_update_user_email",
            description="Useful when you get a new or different email from the person you are chatting with",
            func=self.process_and_update_user_email
        )
        property_search = Tool(
            name="property_search",
            description="Useful for ALL property searches",
            func=self.property_results
        )

        general_search = Tool(
            name="general_search",
            description="useful for when you need to answer questions about current events in the 757 area. You should ask targeted questions",
            func=self.search_results
        )

        text_tool = Tool(
            name='text_tool',
            func=self.get_text_code,
            description="Useful when the user enters a single word, that is not a name and may be a text code. Input should be a text code. Make sure you return the link and any other useful information"
        )

        # weather_tool = Tool(
        #     name='return current weather for location',
        #     func=self.weather_results,
        #     description="Useful when the user asks for the weather - if the state isn't provided, use 'VA' "
        # )

        tools = [property_search, text_tool, general_search,
                 process_and_update_user_name, process_and_update_user_email,
                 post_alert_to_textdawg_ws]

        sysPrompt = SystemMessagePromptTemplate(
            prompt=PromptTemplate(input_variables=[], template=self.sys_msg))

        tprompt = hub.pull("hwchase17/openai-tools-agent")
        for i, message in enumerate(tprompt.messages):
            if isinstance(message, SystemMessagePromptTemplate):
                tprompt.messages[i] = sysPrompt
                break

        agent = create_openai_tools_agent(self.llm, tools, tprompt)
        # Create an agent executor by passing in the agent and tools
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=os.getenv('LLM_VERBOSE'),debug=os.getenv('LLM_DEBUG'))

        return agent_executor

    def respond_to_input(self, user_input):
        response = self.conversational_agent.invoke(
            {"input": user_input, "chat_history":self.chat_history.messages})

        return self.process_response(response)
