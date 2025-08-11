# models.py
from langgraph.graph import MessagesState
from typing import Dict, List, Optional, Any
from enum import Enum

class SalesFramework(str, Enum):
    BANT = "BANT"
    SPIN = "SPIN"
    MEDDIC = "MEDDIC"
    CHANT = "CHANT"

class ConversationStage(str, Enum):
    GREETING = "greeting"
    DISCOVERY = "discovery"
    QUALIFICATION = "qualification"
    OBJECTION_HANDLING = "objection_handling"
    CLOSING = "closing"
    FOLLOW_UP = "follow_up"

class SalesState(MessagesState):
    # Customer Data
    customer_name: Optional[str] = None
    company: Optional[str] = None
    industry: Optional[str] = None
    contact_info: Dict[str, str] = {}
    
    # Sales Qualification
    budget_qualified: bool = False
    authority_qualified: bool = False
    need_qualified: bool = False
    timeline_qualified: bool = False
    
    # SPIN Data
    situation_data: Dict[str, Any] = {}
    problems_identified: List[str] = []
    implications_explored: List[str] = []
    needs_payoff: List[str] = []
    
    # Conversation Management
    framework: SalesFramework = SalesFramework.BANT
    stage: ConversationStage = ConversationStage.GREETING
    qualification_score: int = 0
    questions_asked: List[str] = []
    customer_responses: List[str] = []
    
    # Configuration
    tenant_id: str
    tenant_config: Dict[str, Any] = {}
    
    # Actions
    next_action: Optional[str] = None
    integration_data: Dict[str, Any] = {}