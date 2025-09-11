# Issue #10: LLM Transformation Plan - From Hard-coded Rules to Agentic Intelligence

## Overview

Transform the current multi-agent system from hard-coded heuristics to true LLM-powered reasoning using OpenAI API. This will create a genuinely agentic MLOps planning system that can reason through complex requirements and constraints.

## Current State Analysis

### What Works Well (Keep)
✅ **Agent Framework**: Base classes, reason cards, state management  
✅ **Workflow Orchestration**: LangGraph sequential execution  
✅ **Pattern Library**: MLOps capability patterns in `mlops_patterns.py`  
✅ **Test Infrastructure**: Comprehensive test suite  
✅ **Transparency Model**: Reason cards for decision tracking  

### What Needs Transformation (Change)
❌ **Hard-coded Agent Logic**: All decision-making uses fixed rules  
❌ **Missing Early-Stage Agents**: intake_extract, coverage_check, adaptive_questions are stubs  
❌ **No LLM Integration**: No OpenAI API integration  
❌ **Static Constraint Parsing**: Basic keyword extraction instead of NLP  

## Proposed Architecture Changes

### 1. OpenAI Integration Layer

**New Module**: `libs/llm_client.py`
```python
class OpenAIClient:
    - Handle API calls with retry logic
    - Support multiple models (gpt-4, gpt-3.5-turbo)
    - Rate limiting and error handling
    - Token usage tracking
    - Streaming support for real-time responses

class BaseLLMAgent(BaseMLOpsAgent):
    - Extends current BaseMLOpsAgent
    - Adds LLM call capabilities
    - Prompt template management
    - Response parsing and validation
```

### 2. Formal Constraint Schema

**Enhanced**: `libs/constraint_schema.py`
```python
class ConstraintSchema(BaseModel):
    # Core Requirements
    project_description: str
    budget_band: Literal["startup", "growth", "enterprise"]
    deployment_preference: Literal["serverless", "containers", "kubernetes", "managed"]
    
    # Workload Characteristics  
    workload_types: List[WorkloadType]
    expected_throughput: Literal["low", "medium", "high", "very_high"]
    latency_requirements: Optional[int]  # milliseconds
    
    # Data & Compliance
    data_classification: Literal["public", "internal", "sensitive", "restricted"]
    compliance_requirements: List[str]
    regions: List[str]
    
    # Technical Requirements
    availability_target: Optional[float]  # 99.0, 99.9, 99.99
    scalability_requirements: Optional[str]
    integration_requirements: List[str]
    
    # Team & Operational
    team_expertise: List[str]
    operational_preferences: List[str]
    
    # Meta
    confidence_score: float = 0.0
    missing_fields: List[str] = []
    ambiguous_fields: List[str] = []
```

## Agent Transformation Details

### 3. Early-Stage Agents (New LLM Implementation)

#### 3.1 IntakeExtractAgent
**Purpose**: Parse natural language input into structured ConstraintSchema

**LLM Approach**:
```python
class IntakeExtractAgent(BaseLLMAgent):
    system_prompt = """
    You are an expert MLOps requirements analyst. Parse user input into structured constraints.
    
    Extract information for:
    - Budget constraints and organizational size
    - Technical preferences (serverless, containers, etc.)
    - Workload characteristics (batch, real-time, etc.)
    - Data classification and compliance needs
    - Performance requirements (latency, throughput)
    - Team capabilities and preferences
    
    Be conservative - only extract what you're confident about.
    Flag ambiguous or missing information clearly.
    """
    
    async def execute(self, state, trigger):
        user_input = extract_user_message(state)
        
        response = await self.llm_client.complete(
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Parse this MLOps request: {user_input}"}
            ],
            response_format=ConstraintSchema
        )
        
        return AgentOutput(
            success=True,
            reason_card=self.create_reason_card(...),
            state_updates={"constraints": response.constraints}
        )
```

#### 3.2 CoverageCheckAgent  
**Purpose**: Analyze constraint completeness and compute coverage score

**LLM Approach**:
```python
class CoverageCheckAgent(BaseLLMAgent):
    system_prompt = """
    You are an MLOps requirements completeness analyzer.
    
    Given extracted constraints, evaluate:
    1. Coverage score (0.0-1.0) based on how complete the requirements are
    2. Critical missing fields that would impact system design
    3. Ambiguous fields that need clarification
    4. Minimum viable threshold (typically 0.7) for proceeding
    
    Consider these dimensions:
    - Technical requirements (budget, deployment, workload)
    - Performance requirements (latency, throughput, availability)  
    - Compliance and security requirements
    - Operational requirements (team skills, maintenance)
    """
```

#### 3.3 AdaptiveQuestionsAgent
**Purpose**: Generate targeted follow-up questions iteratively

**LLM Approach**:
```python
class AdaptiveQuestionsAgent(BaseLLMAgent):
    system_prompt = """
    You are an expert MLOps consultant conducting a requirements interview.
    
    Given current constraints and coverage analysis:
    1. Generate 1-3 high-impact clarification questions
    2. Prioritize questions that most affect architecture decisions
    3. Use natural, conversational language
    4. Stop when coverage score > 0.75 or after 3 rounds
    
    Focus on critical unknowns:
    - Budget constraints if unclear
    - Performance requirements if missing
    - Data sensitivity if unspecified
    - Team capabilities for complex deployments
    """
    
    # Implements iterative questioning loop
    async def execute_until_threshold(self, state, threshold=0.75):
        rounds = 0
        while rounds < 3:
            coverage = state.get("coverage_score", 0.0)
            if coverage >= threshold:
                break
                
            questions = await self.generate_questions(state)
            # Present questions to user, collect responses
            # Update constraints based on responses
            rounds += 1
```

### 4. Core Planning Agents (LLM Transformation)

#### 4.1 PlannerAgent (LLM-based)
**Current**: Hard-coded scoring algorithm  
**New**: LLM reasoning with pattern library context

```python
class PlannerAgent(BaseLLMAgent):
    system_prompt = """
    You are a senior MLOps architect with deep expertise in cloud platforms and ML systems.
    
    Given user constraints, select the optimal MLOps architecture pattern.
    
    Available patterns: {pattern_library}
    
    Reasoning process:
    1. Analyze user requirements comprehensively
    2. Evaluate each pattern against requirements
    3. Consider trade-offs: cost, complexity, performance, maintainability
    4. Recommend best-fit pattern with confidence score
    5. Explain selection rationale clearly
    
    Be thorough but decisive. Consider both immediate needs and future scalability.
    """
    
    async def execute(self, state, trigger):
        constraints = state.get("constraints")
        patterns = self.get_pattern_library()
        
        response = await self.llm_client.complete(
            messages=[
                {"role": "system", "content": self.system_prompt.format(pattern_library=patterns)},
                {"role": "user", "content": f"Select optimal pattern for: {constraints}"}
            ],
            response_format=PlannerResponse  # Structured output
        )
        
        return AgentOutput(
            success=True,
            reason_card=self.create_reason_card(
                candidates=response.candidates_considered,
                choice=response.selected_choice,
                confidence=response.confidence
            ),
            state_updates={"plan": response.plan}
        )
```

#### 4.2 TechCriticAgent (LLM-based)
**Current**: Hard-coded risk categories  
**New**: LLM technical analysis

```python
class TechCriticAgent(BaseLLMAgent):
    system_prompt = """
    You are a senior technical architect specializing in distributed systems and MLOps.
    
    Analyze the proposed MLOps architecture for:
    
    Technical Feasibility:
    - Architectural soundness and best practices
    - Performance bottlenecks and scaling limits
    - Single points of failure and failure domains
    - Service coupling and dependency risks
    
    Implementation Risks:
    - Technology complexity vs team capabilities
    - Operational overhead and maintenance burden
    - Integration challenges and compatibility
    - Security vulnerabilities and attack vectors
    
    Provide specific, actionable recommendations for risk mitigation.
    Be thorough but focus on highest-impact concerns.
    """
```

#### 4.3 CostCriticAgent (LLM-based)
**Current**: Hard-coded cost tables  
**New**: LLM cost analysis with current pricing

```python
class CostCriticAgent(BaseLLMAgent):
    system_prompt = """
    You are a cloud cost optimization expert with deep knowledge of AWS pricing.
    
    Analyze the proposed architecture for cost implications:
    
    Cost Estimation:
    - Service-by-service monthly cost breakdown
    - Usage pattern assumptions and validation
    - Cost scaling characteristics with growth
    - Hidden costs and pricing gotchas
    
    Budget Analysis:
    - Fit within specified budget constraints
    - Cost optimization opportunities
    - Reserved instance vs on-demand trade-offs
    - Alternative configurations for cost reduction
    
    Reference current AWS pricing and provide confidence intervals.
    Focus on major cost drivers and optimization opportunities.
    """
```

#### 4.4 PolicyEngineAgent (LLM-based)
**Current**: Hard-coded policy rules  
**New**: LLM governance analysis

```python
class PolicyEngineAgent(BaseLLMAgent):
    system_prompt = """
    You are a cloud governance and compliance expert.
    
    Evaluate the proposed architecture against organizational policies:
    
    Compliance Analysis:
    - Data classification and protection requirements
    - Regional restrictions and data sovereignty
    - Industry compliance standards (SOX, HIPAA, GDPR)
    - Security controls and access management
    
    Operational Policies:
    - Budget and cost governance
    - Technology standards and approved services
    - Deployment and change management policies
    - Monitoring and alerting requirements
    
    Provide pass/warn/fail assessments with clear explanations.
    Suggest policy-compliant alternatives for any violations.
    """
```

## Implementation Plan

### Phase 1: Infrastructure Setup
1. **OpenAI Integration** (`libs/llm_client.py`)
   - API client with retry logic
   - Base LLM agent class
   - Response parsing utilities

2. **Constraint Schema** (`libs/constraint_schema.py`)
   - Formal Pydantic models
   - Validation logic
   - Coverage scoring utilities

### Phase 2: Early-Stage Agents
3. **IntakeExtractAgent** - Natural language → ConstraintSchema
4. **CoverageCheckAgent** - Coverage analysis and scoring  
5. **AdaptiveQuestionsAgent** - Iterative question generation

### Phase 3: Core Agent Transformation
6. **PlannerAgent** - LLM pattern selection
7. **TechCriticAgent** - LLM technical analysis
8. **CostCriticAgent** - LLM cost estimation
9. **PolicyEngineAgent** - LLM governance validation

### Phase 4: Integration & Testing
10. **Graph Integration** - Update LangGraph workflow
11. **Prompt Engineering** - Optimize system prompts
12. **Test Suite Updates** - Comprehensive LLM agent testing
13. **Error Handling** - Robust LLM failure scenarios

## Key Design Decisions

### LLM Model Selection
- **Primary**: GPT-4 for complex reasoning tasks
- **Secondary**: GPT-3.5-turbo for simpler extraction tasks
- **Streaming**: Real-time response streaming for better UX

### Prompt Strategy  
- **System Prompts**: Role-specific expertise and instructions
- **Few-shot Examples**: Include example inputs/outputs for consistency
- **Structured Output**: Use JSON schema for reliable parsing
- **Chain-of-Thought**: Encourage step-by-step reasoning

### Error Handling
- **LLM Failures**: Graceful degradation to simpler models
- **Rate Limiting**: Exponential backoff and queuing
- **Invalid Responses**: Retry with refined prompts
- **Timeout Handling**: Fallback to cached/default responses

### Cost Management
- **Token Optimization**: Efficient prompt design
- **Model Selection**: Appropriate model for task complexity  
- **Caching**: Cache responses for identical inputs
- **Monitoring**: Track usage and costs per agent

## Expected Benefits

### 1. True Agentic Behavior
- Agents can reason through novel scenarios
- Adaptive to changing requirements and constraints
- Learning from patterns in successful deployments

### 2. Improved Accuracy
- LLM reasoning handles edge cases better than rules
- Natural language understanding for complex requirements
- Context-aware decision making

### 3. Enhanced User Experience  
- Natural conversation flow with adaptive questions
- Detailed explanations for all recommendations
- Iterative refinement based on user feedback

### 4. Maintainability
- No hard-coded rules to maintain
- Prompt updates instead of code changes
- Easier to add new capabilities and constraints

## Success Metrics

- **Constraint Extraction Accuracy**: >90% correct field extraction
- **Coverage Completeness**: Average >80% coverage after adaptive questions
- **Pattern Selection Quality**: User satisfaction with recommendations
- **Response Time**: <30 seconds for complete planning workflow
- **Cost Accuracy**: Cost estimates within 20% of actual deployment costs

## Risk Mitigation

### LLM Reliability
- **Validation**: Parse and validate all LLM responses
- **Fallbacks**: Graceful degradation to simpler approaches
- **Monitoring**: Track response quality and user corrections

### Cost Control
- **Budgets**: Set monthly OpenAI API spending limits
- **Optimization**: Use cheaper models where appropriate
- **Caching**: Reduce redundant API calls

### Quality Assurance
- **Testing**: Comprehensive test cases for all agent types
- **Human Review**: Sample output reviews for quality
- **Feedback Loops**: Learn from user corrections and preferences

Would you like me to proceed with this transformation plan? I can start with Phase 1 (OpenAI Integration) and then move through each phase systematically.