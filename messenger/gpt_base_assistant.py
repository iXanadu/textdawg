from dotenv import load_dotenv
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain.chat_models import ChatOpenAI
from langchain.tools import DuckDuckGoSearchRun, Tool
from langchain.agents import initialize_agent, AgentType
from langchain.utilities import GoogleSearchAPIWrapper
from langchain.globals import set_verbose, set_debug
import os
import textwrap
import json

class GPTAIBaseAssistant:
    def __init__(self, temperature, model_name):
        load_dotenv()
        set_verbose(True)
        set_debug(True)
        self.model_name = model_name
        self.model_temp = temperature
        google_cse_id = os.getenv("GOOGLE_UNLIMITED_CSE_ID")
        self.web_search = GoogleSearchAPIWrapper(google_cse_id=google_cse_id)
        # self.general_search = DuckDuckGoSearchRun()
        self.llm = ChatOpenAI(temperature=self.model_temp, model=self.model_name)

    def setup_agent(self, memory):
        self.memory = memory
        self.conversational_agent = self.initialize_conversational_agent()


    def search_results(self, query):
        try:
            return self.web_search.results(str(query), 8)
        except Exception as e:
            print(f"An error occurred: {e}")


    def get_ai_instructions(self):
        ai_instructions = """

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

        web_search = Tool(
            name="general Search",
            description="useful for when you need to answer questions about current events",
            func=self.search_results
        )


        # answer_schema = ResponseSchema(name="output", description="The Assistants final answer")
        # response_schemas = [answer_schema]
        # output_parser = StructuredOutputParser.from_response_schemas(response_schemas)

        tools = [web_search]
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
        # # NOTE - we never got format instructions to work without throwing an error, yet we get formated data back
        # # format_instructions = output_parser.get_format_instructions()
        # new_prompt = template.format(instructions=self.get_ai_instructions(), conversation_section=self.memory,
        #                              format_instructions="")
        # agent.agent.llm_chain.prompt.messages[0].prompt.template = new_prompt

        return agent

    def respond_to_input(self, user_input):
        response = self.conversational_agent(user_input)
        return self.process_response(response)

