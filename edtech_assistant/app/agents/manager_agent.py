# FILE: app/agents/manager_agent.py

from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

# Corrected imports for the new langchain-ollama package and JSON parsing
from langchain_ollama.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from app.core.rag_service import RAGService
from app.core.models import AgentLog


# Define the structured output we want. The parser will use this.
class RouterQuery(BaseModel):
    """Route a user query to the most appropriate tool."""
    topic: str = Field(..., description="The category of the user's query. Can be one of 'EdTech' or 'General'.")

class ManagerAgent:
    def __init__(self, rag_service_instance: RAGService):
        self.rag_service = rag_service_instance

        # --- Create the Router Chain using JSON Mode ---

        # 1. Instantiate the model and tell it to use JSON mode
        self.llm = ChatOllama(model="llama3", format="json", temperature=0)
        
        # 2. Instantiate a parser that will read the JSON from the model's output
        #    and convert it into our RouterQuery object.
        parser = JsonOutputParser(pydantic_object=RouterQuery)

        # 3. Create a prompt that explicitly tells the model how to format its output
        router_prompt_template = """You are an expert at routing a user's question.
        You must format your output as a JSON object with a single key 'topic'.
        The possible values for 'topic' are 'EdTech' or 'General'.

        'EdTech' is for questions about specific educational topics like Python or Large Language Models.
        'General' is for all other questions, including greetings or general knowledge.

        User's question:
        {question}

        {format_instructions}
        """
        prompt = ChatPromptTemplate.from_template(
            template=router_prompt_template,
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )
        
        # 4. Create the final chain by piping the components together
        self.router_chain = prompt | self.llm | parser

    def log_action(self, db: Session, conv_id: int, query: str, response: str, agent_name: str, outcome: str):
        log_entry = AgentLog(
            conversation_id=conv_id, agent_name=agent_name, user_query=query,
            agent_response=response, outcome=outcome
        )
        db.add(log_entry)
        db.commit()

    def process_query(self, query: str, db: Session, conversation_id: int) -> str:
        print(f"Manager Agent processing query: {query}")
        
        # The output of this chain is now a dictionary, not a Pydantic object
        routing_decision = self.router_chain.invoke({"question": query})
        topic = routing_decision.get("topic")
        print(f"Routing decision: The topic is '{topic}'")

        if topic == "EdTech":
            print("Directing to RAG Service.")
            response = self.rag_service.query(query)
            self.log_action(db, conversation_id, query, response, "RAGService", "Provided RAG-based explanation.")
            return response
        else: # Covers "General" and any unexpected outputs
            print("Directing to General LLM.")
            # Use a different LLM instance for general chat that ISN'T in JSON mode
            general_llm = ChatOllama(model="llama3", temperature=0.2)
            response = general_llm.invoke(query).content
            self.log_action(db, conversation_id, query, response, "GeneralLLM", "Provided general knowledge answer.")
            return response