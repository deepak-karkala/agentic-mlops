"""
LLM-Powered PolicyEngineAgent - Intelligent governance and compliance validation

Transforms policy validation from hard-coded rules to LLM reasoning.
Uses GPT-4 to analyze compliance, governance, and organizational policy alignment.
"""

from __future__ import annotations

from typing import Type, Dict, Any, List
import json
import logging

from .llm_agent_base import BaseLLMAgent, MLOpsExecutionContext
from .agent_framework import AgentType, MLOpsWorkflowState
from .agent_output_schemas import PolicyEngineOutput

logger = logging.getLogger(__name__)


class LLMPolicyEngineAgent(BaseLLMAgent):
    """
    LLM-powered policy engine and governance validation agent.

    Uses GPT-4 expertise to analyze proposed architectures against organizational
    policies, regulatory requirements, and governance frameworks.
    """

    SYSTEM_PROMPT = """
You are a senior cloud governance expert and compliance specialist with deep expertise in organizational policy frameworks, regulatory compliance, and enterprise risk management.

Your role is to evaluate proposed MLOps architectures against comprehensive policy requirements, ensuring organizational compliance, regulatory alignment, and governance best practices.

## Expertise Areas

### Regulatory Compliance
- Deep knowledge of major compliance frameworks (GDPR, HIPAA, SOX, PCI-DSS, ISO 27001)
- Understanding of data sovereignty, cross-border data transfer regulations
- Experience with industry-specific compliance requirements (financial, healthcare, government)
- Knowledge of privacy regulations and data protection requirements

### Cloud Governance Frameworks
- Experience with enterprise cloud governance models and policies
- Understanding of security controls, access management, and identity governance
- Knowledge of data governance frameworks and data lifecycle management
- Experience with risk management and audit readiness requirements

### Organizational Policy Assessment
- Understanding of technology standards and approved service catalogs
- Experience with budget and cost governance frameworks
- Knowledge of operational policies and change management requirements
- Understanding of business continuity and disaster recovery policy requirements

### Security and Risk Assessment
- Deep understanding of security frameworks and control requirements
- Experience with threat modeling and risk assessment methodologies
- Knowledge of security architecture patterns and defense-in-depth strategies
- Understanding of incident response and security operations requirements

## Policy Evaluation Framework

### Compliance Assessment Categories

**Data Protection and Privacy**:
- Data classification alignment with organizational standards
- Personal data handling and privacy protection requirements
- Data retention policies and lifecycle management
- Cross-border data transfer compliance and data sovereignty

**Security and Access Control**:
- Identity and access management (IAM) policy compliance
- Network security and segmentation requirements
- Encryption requirements for data at rest and in transit
- Security monitoring and incident response capabilities

**Financial and Budget Governance**:
- Budget approval workflows and spending authorization limits
- Cost allocation and chargeback policy compliance
- Reserved capacity and procurement policy alignment
- Financial reporting and audit trail requirements

**Operational Governance**:
- Change management and deployment approval processes
- Service level agreement (SLA) and availability requirements
- Business continuity and disaster recovery policy compliance
- Vendor management and third-party service approval

**Technology Standards**:
- Approved technology stack and service catalog compliance
- Architecture review and approval process requirements
- Development and deployment pipeline standards
- Documentation and knowledge management requirements

### Compliance Scoring and Risk Assessment

**Policy Compliance Levels**:
- **Pass**: Full compliance with all applicable policies and regulations
- **Warn**: Minor policy deviations that can be addressed through controls or exceptions
- **Fail**: Significant policy violations that must be resolved before implementation

**Risk Severity Assessment**:
- **Critical**: Policy violations with potential legal or business impact
- **High**: Significant governance deviations requiring management attention
- **Medium**: Policy gaps that should be addressed for optimal compliance
- **Low**: Minor deviations or documentation requirements

### Regulatory Requirement Analysis

**GDPR Compliance Assessment**:
- Lawful basis for data processing and consent mechanisms
- Data subject rights implementation (access, rectification, erasure)
- Data protection by design and default principles
- Cross-border data transfer safeguards and adequacy decisions

**HIPAA Compliance Assessment** (Healthcare):
- Protected health information (PHI) handling and safeguards
- Administrative, physical, and technical safeguards implementation
- Business associate agreements and third-party compliance
- Audit logging and access monitoring requirements

**SOX Compliance Assessment** (Financial):
- Internal controls over financial reporting (ICFR)
- Data integrity and change management controls
- Access controls and segregation of duties
- Audit trail and evidence preservation requirements

**PCI-DSS Compliance Assessment** (Payment Processing):
- Cardholder data environment (CDE) security requirements
- Network segmentation and access control requirements
- Encryption and tokenization of sensitive payment data
- Regular security testing and monitoring requirements

## Analysis Guidelines

### Context-Aware Policy Assessment

**Data Classification Integration**:
- **Public Data**: Minimal policy restrictions, focus on operational governance
- **Internal Data**: Standard organizational policies and access controls
- **Sensitive Data**: Enhanced security controls and compliance requirements
- **Restricted Data**: Maximum security measures and regulatory compliance

**Industry-Specific Considerations**:
- **Healthcare**: HIPAA, FDA regulations, patient privacy requirements
- **Financial**: SOX, PCI-DSS, financial reporting and audit requirements
- **Government**: FedRAMP, security clearance, data sovereignty requirements
- **Retail**: PCI-DSS, customer data protection, seasonal compliance considerations

**Organization Size Considerations**:
- **Startup**: Focus on essential compliance, scalable governance frameworks
- **Growth**: Balance compliance requirements with operational efficiency
- **Enterprise**: Comprehensive governance frameworks and audit readiness

### Policy Gap Analysis and Remediation

**Gap Identification Process**:
1. Map architecture components to applicable policies
2. Identify specific policy requirements and control objectives
3. Assess current architecture compliance against each requirement
4. Classify gaps by severity and implementation complexity
5. Recommend specific remediation actions and timelines

**Remediation Prioritization**:
- Critical gaps that block implementation or create legal risk
- High-impact gaps that significantly improve compliance posture
- Cost-effective gaps that provide broad compliance benefits
- Documentation and process gaps that improve audit readiness

### Governance Integration

**Approval Workflow Requirements**:
- Architecture review board approval for significant technology decisions
- Security team approval for systems handling sensitive data
- Compliance team sign-off for regulated data processing
- Budget approval for cost commitments above organizational thresholds

**Ongoing Compliance Monitoring**:
- Continuous compliance monitoring and alerting requirements
- Regular policy compliance reviews and attestation processes
- Incident response procedures for policy violations
- Policy update communication and implementation processes

## Response Format

Your policy assessment must be comprehensive, specific, and actionable, providing clear guidance for achieving and maintaining compliance.

Focus on policy requirements that meaningfully impact the proposed architecture and provide practical remediation strategies.
"""

    def __init__(self):
        super().__init__(
            agent_type=AgentType.POLICY_ENGINE,
            name="LLM Policy Engine",
            description="LLM-powered governance and compliance validation",
            system_prompt=self.SYSTEM_PROMPT,
            # model will be read from OPENAI_MODEL environment variable
        )

    async def get_structured_output_type(self) -> Type[PolicyEngineOutput]:
        """Return the expected output schema for this agent."""
        return PolicyEngineOutput

    def build_user_prompt(self, context: MLOpsExecutionContext) -> str:
        """
        Build comprehensive user prompt with full project context.
        """
        # Get all available context
        plan = context.get_current_plan()
        if not plan:
            return (
                "ERROR: No plan found in context. PlannerAgent must be executed first."
            )

        constraints_summary = (
            context.constraints.to_context_string()
            if context.constraints
            else "No constraints available"
        )
        context_summary = context.build_context_summary()

        # Get technical and cost analysis context
        tech_analysis = context.get_technical_analysis()
        cost_analysis = context.get_cost_analysis()

        analysis_context = ""
        if tech_analysis or cost_analysis:
            analysis_context = "## Previous Analysis Context\n"
            if tech_analysis:
                analysis_context += f"""
**Technical Analysis Summary**:
- Feasibility Score: {tech_analysis.get("overall_feasibility_score", "N/A")}
- Security Concerns: {len(tech_analysis.get("security_concerns", []))} identified
- Operational Complexity: {tech_analysis.get("operational_complexity", "Not specified")}
"""
            if cost_analysis:
                analysis_context += f"""
**Cost Analysis Summary**:
- Monthly Cost: ${cost_analysis.get("estimated_monthly_cost", "N/A")}
- Budget Compliance: {cost_analysis.get("budget_compliance_status", "Unknown")}
- Cost Confidence: {cost_analysis.get("cost_confidence", "N/A")}
"""

        # Get previous policy analysis if this is a refinement
        previous_outputs = context.get_previous_agent_outputs()
        refinement_context = ""
        if self.agent_type.value in previous_outputs:
            refinement_context = f"""
## Previous Policy Analysis
A previous policy analysis was conducted. Please consider refining or updating that analysis:
{json.dumps(previous_outputs[self.agent_type.value], indent=2)}
"""

        return f"""
Please perform a comprehensive policy and governance compliance analysis of the proposed MLOps architecture.

## Project Context
{context_summary}

## Current Constraints
{constraints_summary}

## Proposed Architecture Plan
```json
{json.dumps(plan, indent=2)}
```

{analysis_context}

{refinement_context}

## Policy Analysis Request

Please conduct a thorough governance and compliance analysis focusing on:

### 1. Overall Compliance Assessment
- Overall policy compliance status (pass/warn/fail)
- Compliance score across all relevant policy domains
- High-level summary of compliance posture

### 2. Regulatory Compliance Analysis
Based on data classification and compliance requirements, assess:

**Data Protection and Privacy**:
- GDPR compliance (if handling EU personal data)
- Data classification handling alignment
- Cross-border data transfer compliance
- Data retention and lifecycle management

**Industry-Specific Regulations**:
- HIPAA (if healthcare data is involved)
- SOX (if financial reporting is involved)
- PCI-DSS (if payment data is processed)
- Other relevant industry standards

### 3. Security Policy Compliance
- Identity and access management (IAM) alignment
- Network security and segmentation requirements
- Encryption requirements for data at rest and in transit
- Security monitoring and incident response capabilities

### 4. Operational Governance
- Budget and financial governance compliance
- Change management and deployment approval processes
- Business continuity and disaster recovery requirements
- Vendor management and third-party service policies

### 5. Technology Standards Compliance
- Approved technology stack and service catalog alignment
- Architecture review and approval process requirements
- Development and deployment pipeline standards
- Documentation and audit trail requirements

### 6. Risk Assessment and Mitigation
- Critical policy violations that must be addressed
- Compliance risks and their business impact
- Required risk mitigation strategies and controls
- Escalation requirements for management attention

### 7. Governance Framework Integration
- Required approvals and stakeholder sign-offs
- Ongoing monitoring and compliance maintenance
- Policy exception handling and documentation
- Change management for policy updates

## Analysis Context Considerations

**Data Classification Focus**: 
- Public: Minimal governance, operational focus
- Internal: Standard organizational policies
- Sensitive: Enhanced controls and compliance
- Restricted: Maximum security and regulatory compliance

**Budget Band Governance**:
- Startup: Essential compliance, streamlined approvals
- Growth: Balanced governance and operational efficiency
- Enterprise: Comprehensive frameworks and audit readiness

**Compliance Requirements Integration**:
Focus analysis on the specific compliance requirements identified in the constraints, with particular attention to data handling and regulatory obligations.

## Expected Deliverables

Provide a comprehensive PolicyEngineOutput including:
- Overall compliance status and confidence score
- Detailed rule-by-rule compliance evaluation
- Critical violations requiring immediate attention
- Policy warnings and recommendations
- Compliance gap analysis and remediation guidance
- Required approvals and stakeholder notifications
- Governance framework integration requirements
- Ongoing monitoring and maintenance recommendations

Be thorough but practical - focus on policy requirements that meaningfully impact the proposed architecture and provide actionable compliance guidance.
"""

    async def extract_state_updates(
        self, llm_response: PolicyEngineOutput, current_state: MLOpsWorkflowState
    ) -> Dict[str, Any]:
        """
        Extract state updates from policy engine output.
        """
        # Build comprehensive policy analysis
        policy_analysis = {
            "overall_compliance_status": llm_response.overall_compliance_status,
            "compliance_score": llm_response.compliance_score,
            "policy_assessment_summary": llm_response.policy_assessment_summary,
            "policy_rule_results": llm_response.policy_rule_results,
            "critical_violations": llm_response.critical_violations,
            "warnings": llm_response.warnings,
            "security_compliance": llm_response.security_compliance,
            "data_governance_compliance": llm_response.data_governance_compliance,
            "operational_compliance": llm_response.operational_compliance,
            "financial_compliance": llm_response.financial_compliance,
            "regulatory_requirements": llm_response.regulatory_requirements,
            "compliance_gaps": llm_response.compliance_gaps,
            "audit_readiness": llm_response.audit_readiness,
            "compliance_risks": llm_response.compliance_risks,
            "risk_mitigation_requirements": llm_response.risk_mitigation_requirements,
            "escalation_required": llm_response.escalation_required,
            "immediate_actions_required": llm_response.immediate_actions_required,
            "recommended_policy_adjustments": llm_response.recommended_policy_adjustments,
            "alternative_approaches": llm_response.alternative_approaches,
            "governance_controls_needed": llm_response.governance_controls_needed,
            "monitoring_requirements": llm_response.monitoring_requirements,
            "documentation_requirements": llm_response.documentation_requirements,
            "stakeholder_notifications": llm_response.stakeholder_notifications,
            "approval_requirements": llm_response.approval_requirements,
            "change_management_needs": llm_response.change_management_needs,
            "policies_evaluated": llm_response.policies_evaluated,
            "policy_exceptions_needed": llm_response.policy_exceptions_needed,
            "policy_review_recommendations": llm_response.policy_review_recommendations,
            "assessment_confidence": llm_response.assessment_confidence,
            "assessment_limitations": llm_response.assessment_limitations,
            "agent_version": "llm_1.0",
        }

        return {
            # Store the complete policy analysis
            "policy_validation": policy_analysis,
            # Store key metrics for easy access
            "overall_compliance_status": llm_response.overall_compliance_status,
            "compliance_score": llm_response.compliance_score,
            "escalation_required": llm_response.escalation_required,
            # Update agent outputs
            "agent_outputs": {
                **current_state.get("agent_outputs", {}),
                self.agent_type.value: llm_response.model_dump(),
            },
        }

    def get_required_predecessor_agents(self) -> List[str]:
        """Policy validation requires a complete analysis chain."""
        return [
            AgentType.PLANNER.value
            # TechCritic and CostCritic are optional but beneficial for context
        ]

    async def build_next_agent_context(
        self, llm_response: PolicyEngineOutput
    ) -> Dict[str, Any]:
        """Build context for workflow completion."""
        return {
            "from_agent": self.agent_type.value,
            "policy_analysis_complete": True,
            "compliance_status": llm_response.overall_compliance_status,
            "compliance_score": llm_response.compliance_score,
            "critical_violations_count": len(llm_response.critical_violations),
            "warnings_count": len(llm_response.warnings),
            "escalation_required": llm_response.escalation_required,
            "audit_readiness": llm_response.audit_readiness,
            "summary": f"Policy analysis complete: {llm_response.overall_compliance_status} compliance ({llm_response.compliance_score:.1%}), {len(llm_response.critical_violations)} critical violations, escalation {'required' if llm_response.escalation_required else 'not required'}",
        }

    async def build_mock_response(
        self, context: MLOpsExecutionContext, state: MLOpsWorkflowState
    ) -> PolicyEngineOutput:
        """Return deterministic policy evaluation for mock mode."""
        return PolicyEngineOutput(
            overall_compliance_status="pass",
            compliance_score=0.9,
            policy_assessment_summary="Baseline controls satisfied with minor governance recommendations.",
            policy_rule_results=[
                {"rule": "budget_limit", "status": "pass", "details": "Projected spend within approved band"},
                {"rule": "security_baseline", "status": "pass", "details": "Encryption and IAM controls configured"},
                {"rule": "data_governance", "status": "warn", "details": "Document data retention timeline"},
            ],
            critical_violations=[],
            warnings=["Consider multi-region backup for higher resilience"],
            security_compliance={
                "status": "compliant",
                "score": 0.85,
                "gaps": ["Enforce MFA for all IAM users", "Publish incident response plan"],
            },
            data_governance_compliance={
                "status": "compliant",
                "score": 0.9,
                "gaps": ["Finalize data retention policy", "Classify sensitive datasets"],
            },
            operational_compliance={
                "status": "compliant",
                "score": 0.95,
                "gaps": ["Schedule disaster recovery test"]
            },
            financial_compliance={
                "status": "compliant",
                "score": 1.0,
                "gaps": [],
            },
            regulatory_requirements=[
                {"regulation": "SOX", "status": "not_applicable", "reason": "No financial reporting"},
                {"regulation": "GDPR", "status": "needs_review", "reason": "Potential EU personal data"},
            ],
            compliance_gaps=["Document data classification", "Implement cross-region backup"],
            audit_readiness="needs_work",
            compliance_risks=["Data loss", "Privacy violation"],
            risk_mitigation_requirements=[
                "Add cross-region backup plan",
                "Publish data lifecycle SOP",
            ],
            escalation_required=False,
            immediate_actions_required=["Configure cost anomaly alerts"],
            recommended_policy_adjustments=["Add data classification policy"],
            alternative_approaches=[
                {
                    "approach": "Enhanced security",
                    "details": "Enable organization-wide MFA and log archive",
                    "impact": "Improved security posture",
                }
            ],
            governance_controls_needed=["Quarterly access reviews", "Budget governance committee"],
            monitoring_requirements=["Compliance dashboards", "Policy breach alerts"],
            documentation_requirements=["Data handling SOP", "Security checklist"],
            stakeholder_notifications=["Security team", "Compliance officer"],
            approval_requirements=["Security sign-off prior to production"],
            change_management_needs=["Communicate new retention policy"],
            policies_evaluated=["security_baseline", "budget_policy", "data_governance"],
            policy_exceptions_needed=["Temporary relaxed logging in dev"],
            policy_review_recommendations=["Review data governance quarterly"],
            assessment_confidence=0.8,
            assessment_limitations=["Security penetration test pending", "Limited compliance evidence"],
        )


def create_llm_policy_engine_agent() -> LLMPolicyEngineAgent:
    """Factory function to create a configured LLMPolicyEngineAgent."""
    return LLMPolicyEngineAgent()
