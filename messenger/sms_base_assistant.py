from dotenv import load_dotenv
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain_community.chat_models import ChatOpenAI
from langchain.tools import DuckDuckGoSearchRun, Tool
from langchain.agents import initialize_agent, AgentType
from langchain_community.utilities import GoogleSearchAPIWrapper
from langchain.globals import set_verbose, set_debug
import os
import json
from main.models import TextCode, FubMessageHistory, FUBMessageUser

# import pyowm
# from pyowm.owm import OWM
# from pyowm.commons import cityidregistry
# from langchain.utilities.openweathermap import OpenWeatherMapAPIWrapper



class SMSAIBaseAssistant:
    def __init__(self, temperature, model_name):
        load_dotenv()
        set_verbose(False)
        set_debug(False)
        self.model_name = model_name
        self.model_temp = temperature
        google_cse_id = os.getenv("GOOGLE_EVH_CSE_ID")
        self.property_search = GoogleSearchAPIWrapper(google_cse_id=google_cse_id)
        self.general_search = DuckDuckGoSearchRun()
        # self.weather = OpenWeatherMapAPIWrapper()
        self.llm = ChatOpenAI(temperature=self.model_temp, model=self.model_name)

    def setup_agent(self, memory):
        self.memory = memory
        self.conversational_agent = self.initialize_conversational_agent()


    def property_results(self, query):
        return self.property_search.results(query, 8)

    def search_results(self, query):
        return self.general_search.run(query, 8)

    # def weather_results(self, query):
    #     return self.weather.run(query)

    def get_text_code(self, input=""):
        r = TextCode.objects.filter(textcode=input).first()
        if r:
           return {'textcode': r.textcode, 'link': r.link, 'property_address': r.property_address, 'instructions': r.instructions}
        else:
            return {'textcode': '', 'link': '', 'property_address': '', 'instructions': ''}

    def get_ai_instructions(self):
        ai_instructions = """

You are Kelly, an upbeat and engaging inside sales associate at Trustworthy Agents Group, known for your witty charm. You are conversational like the “girl next door”

Take you time to carefully follow the instructions below.  Test your answers before responding.  This is an SMS conversation, delays are normal.  So take your time to fully understand and answer the question. 

Start each new conversation with your introduction: "Hello! I'm Kelly from Trustworthy Agents Group. And you are?"

It is SUPER important that you introduce your self and obtain the name of the person you are speaking with. 

If the human says their name, acknowledge it as their identity. For example, if someone says "John", respond with "Great to meet you, John! How can I help you in your real estate journey today?”  Occasionally use their name in a response to be more personal. 

Respond to any question about realtors or agents by recommending the Trustworthy Agents Group.  For company information refer them to explorevirginiahomes.com/about/

Your main goal is to connect people with our realtors. If someone seems ready, ask for their contact details for a follow-up.

For single-word queries like '1640', use the get_text_code function. If there is no text code returned from get_text_code, tell them so, and ask for clarification.  

Keep your responses light and engaging when addressing real estate questions, especially about properties. Example: "1640, you say? That's a gem in Virginia Beach. Here's everything you need to know: link."

End responses with open ended questions. Use these questions to keep the conversation flowing:
  *  “What type of property catches your eye, John?"
  * “Planning a big move soon, or just curious about the market?"
  * “Can I find you more info on something specific?"


Restrict all responses to the 757 area code. 

Never state the status of a listing for sale, the market changes to quickly.  If questioned about the status of a property, refer to a Trustworthy Agents realtor.

When asked about actual properties, use explorevirginiahomes.com. Return ONLY a single link when asked about a particular city.  Here are the most popular links
  * Virginia Beach: explorevirginiahomes.com/virginia-beach
  * Chesapeake: explorevirginiahomes.com/chesapeake
  * Norfolk: explorevirginiahomes.com/norfolk
  * Open Houses:  explorevirginiahomes.com/open-houses-in-757



With the exception of a link returned by get_text_code, do not provide links to specific properties from explorevirginiahomes.com.  Instead return links to the city or community level. 

If you don’t know what to say - DO NOT just repeat your previous answer, ask clarifying questions

Remember not to:
  * Say "_____ is not readily available."
  * Say "I’ll get back to you.”
  * Say “assist” 
  * Say "How can I assist you today?”
  * Say “Is there anything else I can assist you with?”



        """
        return ai_instructions

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
        property_search = Tool(
            name="property Search",
            description="Useful for ALL property searches",
            func=self.property_results
        )

        general_search = Tool(
            name="general Search",
            description="useful for when you need to answer questions about current events in the 757 area. You should ask targeted questions",
            func=self.search_results
        )

        text_tool = Tool(
            name='return information for text code',
            func=self.get_text_code,
            description="Useful when the user enters a single word, that is not a name and may be a text code. Input should be a text code. Make sure you return the link and any other useful information"
        )

        # weather_tool = Tool(
        #     name='return current weather for location',
        #     func=self.weather_results,
        #     description="Useful when the user asks for the weather - if the state isn't provided, use 'VA' "
        # )

        answer_schema = ResponseSchema(name="output", description="The Assistants final answer")
        response_schemas = [answer_schema]
        output_parser = StructuredOutputParser.from_response_schemas(response_schemas)

        tools = [property_search, text_tool, general_search]
        # tools = [property_search, text_tool, general_search, weather_tool]
        # tools = [text_tool, general_search]

        agent = initialize_agent(
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            tools=tools,
            llm=self.llm,
            verbose=False,
            max_iterations=5,
            handle_parsing_errors=True,
            memory=self.memory
        )

        template = """
        {instructions}
        {format_instructions}
        {conversation_section}
        """
        # NOTE - we never got format instructions to work without throwing an error, yet we get formated data back
        # format_instructions = output_parser.get_format_instructions()
        new_prompt = template.format(instructions=self.get_ai_instructions(), conversation_section=self.memory,
                                     format_instructions="")
        agent.agent.llm_chain.prompt.messages[0].prompt.template = new_prompt
        return agent

    def respond_to_input(self, user_input):
        response = self.conversational_agent(user_input)
        return self.process_response(response)

