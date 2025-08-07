from sqlalchemy.orm import Session
from app.core.models import AgentLog
from app.agents.expert_agents import ConceptExplainerAgent, PracticeQuestionAgent, CodeDebuggerAgent

class ManagerAgent:
    def __init__(self):
        self.concept_explainer = ConceptExplainerAgent()
        # We can add other agents here as we build them
        # self.practice_agent = PracticeQuestionAgent()
        # self.code_agent = CodeDebuggerAgent()

    def log_action(self, db: Session, conv_id: int, query: str, response: str, agent_name: str, outcome: str):
        log_entry = AgentLog(
            conversation_id=conv_id,
            agent_name=agent_name,
            user_query=query,
            agent_response=response,
            outcome=outcome
        )
        db.add(log_entry)
        db.commit()

    def process_query(self, query: str, db: Session, conversation_id: int) -> str:
        """
        The manager agent decides which expert agent to call based on the user's query.
        """
        # Log the manager's initial processing
        self.log_action(db, conversation_id, query, "", "ManagerAgent", "Received and routing query.")

        # Simple keyword-based routing for now
        if "explain" in query.lower() or "what is" in query.lower():
            response = self.concept_explainer.explain_concept(query)
            # Log the expert agent's action
            self.log_action(db, conversation_id, query, response, "ConceptExplainerAgent", "Provided explanation.")
            return response
        else:
            response = "I'm not sure how to handle that yet. Try asking me to 'explain' a concept."
            # Log the fallback action
            self.log_action(db, conversation_id, query, response, "ManagerAgent", "Could not route query.")
            return response