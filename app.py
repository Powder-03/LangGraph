# sales_agent.py
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from langgraph.graph import StateGraph, END, START
from langchain_openai import AzureChatOpenAI
from langchain.schema import HumanMessage, AIMessage
import json

class SalesFramework(Enum):
    BANT = "BANT"
    SPIN = "SPIN" 
    MEDDIC = "MEDDIC"

class SalesState(BaseModel):
    messages: List = []
    tenant_id: str = ""
    tenant_config: dict = {}
    customer_name: Optional[str] = None
    company: Optional[str] = None
    industry: Optional[str] = None
    qualification_score: int = 50
    questions_asked: List[str] = []
    customer_responses: List[str] = []
    framework: Optional[SalesFramework] = None
    budget_qualified: bool = False
    authority_qualified: bool = False
    need_qualified: bool = False
    timeline_qualified: bool = False
    needs_identified: List[str] = []
    next_action: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True

class Config:
    pass

class SalesAgent:
    def __init__(self, config: Config):
        self.llm = AzureChatOpenAI(
            azure_endpoint="https://techpath-openai.openai.azure.com/",
            azure_deployment="gpt-4o-mini",
            api_version="2023-05-15",
            api_key="Dq3wQKHHTMRA8hsft58neKBWBz5Cuz6VHUQXu9gJ9SMOd5aarJdJQQJ99BAACYeBjFXJ3w3AAABACOGRUhK",
            temperature=0.7
        )
        
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(SalesState)
        
        # Add nodes
        workflow.add_node("analyze_context", self.analyze_context)
        workflow.add_node("select_framework", self.select_framework)
        workflow.add_node("generate_question", self.generate_question)
        workflow.add_node("evaluate_response", self.evaluate_response)
        workflow.add_node("make_decision", self.make_decision)
        workflow.add_node("handle_objection", self.handle_objection)
        workflow.add_node("schedule_meeting", self.schedule_meeting)
        workflow.add_node("generate_payment", self.generate_payment)
        workflow.add_node("send_follow_up", self.send_follow_up)
        
        # Add edges
        workflow.add_edge(START, "analyze_context")
        workflow.add_edge("analyze_context", "select_framework")
        workflow.add_edge("select_framework", "generate_question")
        workflow.add_edge("generate_question", "evaluate_response")
        
        # Conditional edges
        workflow.add_conditional_edges(
            "evaluate_response",
            self.route_conversation,
            {
                "continue": "make_decision",
                "objection": "handle_objection",
                "qualified": "make_decision"
            }
        )
        
        workflow.add_conditional_edges(
            "make_decision",
            self.decide_next_action,
            {
                "continue_questions": "generate_question",
                "schedule_demo": "schedule_meeting",
                "generate_payment": "generate_payment",
                "follow_up": "send_follow_up",
                "end": END
            }
        )
        
        workflow.add_edge("handle_objection", "generate_question")
        workflow.add_edge("schedule_meeting", END)
        workflow.add_edge("generate_payment", END)
        workflow.add_edge("send_follow_up", END)
        
        return workflow.compile()
    
    def analyze_context(self, state: SalesState) -> SalesState:
        """Analyze customer message and extract context"""
        latest_message = state.messages[-1].content if state.messages else ""
        
        analysis_prompt = f"""
        Analyze this customer message and extract relevant information:
        Message: {latest_message}
        
        Extract:
        1. Customer name (if mentioned)
        2. Company name (if mentioned)  
        3. Industry (if mentioned or can be inferred)
        4. Contact information (email, phone if mentioned)
        5. Any budget indicators
        6. Decision-making authority indicators
        7. Needs or pain points mentioned
        8. Timeline indicators
        
        Return as JSON format.
        """
        
        response = self.llm.invoke([HumanMessage(content=analysis_prompt)])
        
        try:
            analysis = json.loads(response.content)
            
            # Update state with extracted information
            if analysis.get("customer_name"):
                state.customer_name = analysis["customer_name"]
            if analysis.get("company"):
                state.company = analysis["company"]
            if analysis.get("industry"):
                state.industry = analysis["industry"]
            if analysis.get("budget_info"):
                state.budget_qualified = True
            if analysis.get("authority_info"):
                state.authority_qualified = True
            if analysis.get("needs"):
                state.need_qualified = True
            if analysis.get("timeline"):
                state.timeline_qualified = True
                
        except json.JSONDecodeError:
            pass  # Continue with existing state
        
        return state
    
    def select_framework(self, state: SalesState) -> SalesState:
        """Select appropriate sales framework based on context"""
        tenant_config = state.tenant_config
        
        # Default framework selection logic
        if state.industry in ["technology", "saas", "enterprise"]:
            state.framework = SalesFramework.MEDDIC
        elif state.industry in ["healthcare", "finance"]:
            state.framework = SalesFramework.BANT
        else:
            state.framework = SalesFramework.SPIN
        
        # Override with tenant configuration
        if tenant_config.get("preferred_framework"):
            state.framework = SalesFramework(tenant_config["preferred_framework"])
        
        return state
    
    def generate_question(self, state: SalesState) -> SalesState:
        """Generate next sales question based on framework and context"""
        framework_questions = self._get_framework_questions(state.framework)
        
        # Filter out already asked questions
        available_questions = [
            q for q in framework_questions 
            if q not in state.questions_asked
        ]
        
        if not available_questions:
            state.next_action = "make_decision"
            return state
        
        # Select most appropriate question
        context = {
            "customer_name": state.customer_name,
            "company": state.company,
            "industry": state.industry,
            "previous_responses": state.customer_responses[-3:],
            "qualification_status": {
                "budget": state.budget_qualified,
                "authority": state.authority_qualified,
                "need": state.need_qualified,
                "timeline": state.timeline_qualified
            }
        }
        
        question_prompt = f"""
        Based on the following context, select and personalize the most appropriate next question:
        
        Context: {json.dumps(context, indent=2)}
        Framework: {state.framework}
        Available Questions: {available_questions[:3]}  # Show top 3
        
        Return:
        1. Selected question (personalized)
        2. Reasoning for selection
        3. Expected information to gather
        
        Format as JSON.
        """
        
        response = self.llm.invoke([HumanMessage(content=question_prompt)])
        
        try:
            question_data = json.loads(response.content)
            next_question = question_data.get("selected_question", available_questions[0])
            
            # Add to conversation
            state.messages.append(AIMessage(content=next_question))
            state.questions_asked.append(next_question)
            
        except json.JSONDecodeError:
            # Fallback to first available question
            next_question = available_questions[0]
            state.messages.append(AIMessage(content=next_question))
            state.questions_asked.append(next_question)
        
        return state
    
    def evaluate_response(self, state: SalesState) -> SalesState:
        """Evaluate customer response and update qualification score"""
        if not state.messages:
            return state
            
        latest_response = state.messages[-1].content
        state.customer_responses.append(latest_response)
        
        # Evaluate response against framework criteria
        evaluation_prompt = f"""
        Evaluate this customer response against {state.framework} framework:
        
        Response: {latest_response}
        Framework: {state.framework}
        
        Analyze:
        1. Information quality (0-100)
        2. Buying intent (0-100)
        3. Qualification level (0-100)
        4. Any objections identified
        5. Next recommended action
        
        Return as JSON.
        """
        
        response = self.llm.invoke([HumanMessage(content=evaluation_prompt)])
        
        try:
            evaluation = json.loads(response.content)
            
            # Update qualification score
            info_quality = evaluation.get("information_quality", 50)
            buying_intent = evaluation.get("buying_intent", 50)
            qualification_level = evaluation.get("qualification_level", 50)
            
            # Calculate weighted score
            new_score = (info_quality * 0.3 + buying_intent * 0.4 + qualification_level * 0.3)
            state.qualification_score = int((state.qualification_score + new_score) / 2)
            
        except json.JSONDecodeError:
            state.qualification_score += 10  # Default increment
        
        return state
    
    def route_conversation(self, state: SalesState) -> str:
        """Route conversation based on customer response"""
        latest_response = state.messages[-1].content.lower()
        
        # Check for objections
        objection_keywords = ["too expensive", "not interested", "not now", "budget", "think about it"]
        if any(keyword in latest_response for keyword in objection_keywords):
            return "objection"
        
        # Check if well qualified
        if state.qualification_score >= 80:
            return "qualified"
            
        return "continue"
    
    def make_decision(self, state: SalesState) -> SalesState:
        """Make decision on next action based on qualification score"""
        score = state.qualification_score
        questions_count = len(state.questions_asked)
        
        if score >= 85 and state.budget_qualified and state.authority_qualified:
            if state.tenant_config.get("payment_enabled"):
                state.next_action = "generate_payment"
            else:
                state.next_action = "schedule_demo"
        elif score >= 70:
            state.next_action = "schedule_demo"
        elif questions_count >= 10:
            state.next_action = "follow_up"
        else:
            state.next_action = "continue_questions"
        
        return state
    
    def decide_next_action(self, state: SalesState) -> str:
        """Conditional edge function for decision routing"""
        return state.next_action or "end"
    
    def handle_objection(self, state: SalesState) -> SalesState:
        """Handle customer objections"""
        objection = state.messages[-1].content
        
        objection_prompt = f"""
        Handle this customer objection professionally:
        Objection: {objection}
        Product/Service: {state.tenant_config.get('product_description', 'our solution')}
        
        Provide:
        1. Acknowledgment of concern
        2. Relevant counter-argument or clarification
        3. Question to continue conversation
        
        Keep response under 100 words.
        """
        
        response = self.llm.invoke([HumanMessage(content=objection_prompt)])
        state.messages.append(AIMessage(content=response.content))
        
        return state
    
    def schedule_meeting(self, state: SalesState) -> SalesState:
        """Schedule demo/meeting"""
        calendar_link = state.tenant_config.get("calendar_link", "https://calendly.com/demo")
        
        message = f"""Great! Based on our conversation, I'd love to show you a personalized demo.
        
You can book a convenient time here: {calendar_link}

Or would you prefer if I send you some specific times that work for your schedule?"""
        
        state.messages.append(AIMessage(content=message))
        state.next_action = "scheduled"
        
        return state
    
    def generate_payment(self, state: SalesState) -> SalesState:
        """Generate payment link"""
        # This would integrate with actual payment processor
        payment_link = f"https://pay.stripe.com/demo-link/{state.tenant_id}"
        
        message = f"""Perfect! You're all set to get started.
        
Here's your secure payment link: {payment_link}

Once payment is processed, you'll receive immediate access along with onboarding instructions.

Any questions about the process?"""
        
        state.messages.append(AIMessage(content=message))
        state.next_action = "payment_sent"
        
        return state
    
    def send_follow_up(self, state: SalesState) -> SalesState:
        """Send follow-up message"""
        message = f"""Thank you for your time today! 

Based on our conversation, I'll send you:
📧 Information about {', '.join(state.needs_identified) if state.needs_identified else 'our solution'}
📅 Some times for a follow-up call next week
💡 A case study from a similar {state.industry or 'company'} 

Is there anything specific you'd like me to include?"""
        
        state.messages.append(AIMessage(content=message))
        state.next_action = "follow_up_sent"
        
        return state
    
    def _get_framework_questions(self, framework: SalesFramework) -> List[str]:
        """Get questions for specific framework"""
        questions = {
            SalesFramework.BANT: [
                "What budget range are you working with for this type of solution?",
                "Who else would be involved in making this decision?", 
                "What specific challenges are you looking to solve?",
                "When are you hoping to have a solution in place?",
                "What's driving the urgency for this project?"
            ],
            SalesFramework.SPIN: [
                "Can you tell me about your current process for [relevant area]?",
                "What challenges are you experiencing with your current approach?",
                "How is this challenge affecting your team's productivity?",
                "What would solving this problem mean for your business?",
                "How are you currently handling this situation?"
            ],
            SalesFramework.MEDDIC: [
                "What metrics are you using to measure success in this area?",
                "Who has the final decision-making authority for this purchase?",
                "What criteria will you use to evaluate potential solutions?",
                "Can you walk me through your decision-making process?",
                "What's the biggest pain point you're trying to address?"
            ]
        }
        
        return questions.get(framework, questions[SalesFramework.BANT])
    
    def run_conversation(self, initial_message: str, tenant_config: Dict) -> Dict[str, Any]:
        """Run complete conversation flow"""
        initial_state = SalesState(
            messages=[HumanMessage(content=initial_message)],
            tenant_id=tenant_config["tenant_id"],
            tenant_config=tenant_config
        )
        
        final_state = self.graph.invoke(initial_state)
        
        return {
            "messages": [{"role": "ai" if isinstance(msg, AIMessage) else "human", 
                         "content": msg.content} for msg in final_state.messages],
            "qualification_score": final_state.qualification_score,
            "next_action": final_state.next_action,
            "customer_info": {
                "name": final_state.customer_name,
                "company": final_state.company,
                "industry": final_state.industry
            }
        }

# Example Usage
if __name__ == "__main__":
    config = Config()
    agent = SalesAgent(config)
    
    tenant_config = {
        "tenant_id": "demo_company",
        "industry": "technology",
        "preferred_framework": "MEDDIC",
        "payment_enabled": True,
        "calendar_link": "https://calendly.com/demo-company",
        "product_description": "AI-powered sales automation platform"
    }
    
    result = agent.run_conversation(
        "Hi, I'm interested in learning more about your sales automation platform.",
        tenant_config
    )
    
    print(json.dumps(result, indent=2))