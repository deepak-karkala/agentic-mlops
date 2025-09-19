export type WorkflowNodeMetadata = {
  label: string;
  description?: string;
};

export const WORKFLOW_NODE_METADATA: Record<string, WorkflowNodeMetadata> = {
  intake_extract: {
    label: "Constraint Intake",
    description: "Structure the user's request into actionable requirements.",
  },
  coverage_check: {
    label: "Coverage Analysis",
    description: "Identify gaps and missing critical fields.",
  },
  adaptive_questions: {
    label: "Adaptive Questions",
    description: "Generate targeted follow-up prompts for clarification.",
  },
  hitl_gate_input: {
    label: "Input Review Gate",
    description: "Validate constraints with human-in-the-loop checkpoints.",
  },
  hitl_gate_user: {
    label: "Input Review Gate",
    description: "Collect user responses or auto-approve defaults.",
  },
  gate_hitl: {
    label: "Human Review Gate",
    description: "Pause the workflow for human approval when required.",
  },
  planner: {
    label: "Architecture Planner",
    description: "Assemble an end-to-end MLOps reference design.",
  },
  critic_tech: {
    label: "Technical Critic",
    description: "Stress-test feasibility and technical soundness.",
  },
  critic_cost: {
    label: "Cost Critic",
    description: "Validate alignment with budget and resource targets.",
  },
  policy_eval: {
    label: "Policy Engine",
    description: "Run compliance and policy safeguard checks.",
  },
  hitl_gate_final: {
    label: "Final Approval Gate",
    description: "Confirm readiness before code generation.",
  },
  codegen: {
    label: "Code Generation",
    description: "Synthesize infrastructure and application assets.",
  },
  validators: {
    label: "Validation Suite",
    description: "Run static validation on generated artifacts.",
  },
  rationale_compile: {
    label: "Rationale Builder",
    description: "Summarize agent reasoning for sharing and audits.",
  },
  diff_and_persist: {
    label: "Persist & Diff",
    description: "Store artifacts and produce change summaries.",
  },
  call_llm: {
    label: "LLM Responder",
    description: "Return thin-slice response for development testing.",
  },
  coverage_check_enhanced: {
    label: "Coverage Analysis",
    description: "Enhanced coverage evaluation with iterative updates.",
  },
  intake_extract_enhanced: {
    label: "Constraint Intake",
    description: "Enhanced intake with user feedback merging.",
  },
};

const HUMANIZE_REGEX = /[_-]+/g;

export function getWorkflowNodeLabel(nodeId: string): string {
  const metadata = WORKFLOW_NODE_METADATA[nodeId];
  if (metadata) {
    return metadata.label;
  }
  return nodeId.replace(HUMANIZE_REGEX, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function getWorkflowNodeDescription(nodeId: string): string | undefined {
  return WORKFLOW_NODE_METADATA[nodeId]?.description;
}
