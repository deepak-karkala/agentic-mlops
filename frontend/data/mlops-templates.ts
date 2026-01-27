import { StreamingState, ReasonCard, StreamEvent } from "@/hooks/useStreamingEvents";
import { EnhancedMessage } from "@/types/enhanced-chat";

export interface MlopsTemplate {
  id: string;
  name: string;
  headline: string;
  summary: string;
  tags: string[];
  techStack: string[];
  heroStats: { label: string; value: string }[];
  highlights: string[];
  userPrompt: string;
  systemIntro: string;
  planNodes: string[];
  graphType?: string;
  workflowState: StreamingState;
  messages: EnhancedMessage[];
}

function buildStreamingState(
  id: string,
  planNodes: string[],
  reasonCards: ReasonCard[],
): StreamingState {
  const events: StreamEvent[] = [];
  const now = Date.now();

  planNodes.forEach((nodeId, index) => {
    const baseTimestamp = new Date(now - (planNodes.length - index) * 60000)
      .toISOString();
    const completionTimestamp = new Date(now - (planNodes.length - index - 0.5) * 60000)
      .toISOString();

    events.push(
      {
        type: "node-start",
        decision_set_id: id,
        timestamp: baseTimestamp,
        data: { node: nodeId },
      },
      {
        type: "node-complete",
        decision_set_id: id,
        timestamp: completionTimestamp,
        data: { node: nodeId },
      },
    );
  });

  return {
    isConnected: true,
    isConnecting: false,
    events,
    reasonCards,
    workflowProgress: {
      current_node: undefined,
      nodes_completed: planNodes,
      nodes_remaining: [],
      progress_percentage: 100,
      status: "completed",
      estimated_time_remaining_ms: 0,
    },
    currentNode: null,
    codeArtifacts: [],
    repositoryZip: null,
    error: null,
    connectionError: false,
    hitlState: {
      isActive: false,
      questions: [],
      smartDefaults: {},
      timeoutSeconds: 0,
      node: null,
      isAutoApproving: false,
    },
  };
}

function buildReasonCards(
  templateId: string,
  planNodes: string[],
  descriptions: Array<Pick<ReasonCard, "agent" | "reasoning" | "decision" | "inputs" | "outputs" | "alternatives_considered" | "priority" | "category" | "confidence">>,
): ReasonCard[] {
  return planNodes.map((node, index) => {
    const descriptor = descriptions[Math.min(index, descriptions.length - 1)];
    return {
      agent: descriptor.agent,
      node,
      decision_set_id: templateId,
      timestamp: new Date(Date.now() - (planNodes.length - index) * 45000).toISOString(),
      duration_ms: 15000 + index * 2500,
      reasoning: descriptor.reasoning,
      decision: descriptor.decision,
      confidence: descriptor.confidence,
      inputs: descriptor.inputs,
      outputs: descriptor.outputs,
      alternatives_considered: descriptor.alternatives_considered,
      category: descriptor.category,
      priority: descriptor.priority,
      references: [],
    };
  });
}

function buildMessages(templateId: string, systemIntro: string, userPrompt: string, summary: string): EnhancedMessage[] {
  const createdAt = new Date();
  return [
    {
      id: `${templateId}-user`,
      role: "user",
      content: userPrompt,
      timestamp: createdAt,
    },
    {
      id: `${templateId}-assistant-intro`,
      role: "assistant",
      content: systemIntro,
      timestamp: new Date(createdAt.getTime() + 5000),
    },
    {
      id: `${templateId}-assistant-summary`,
      role: "assistant",
      content: summary,
      timestamp: new Date(createdAt.getTime() + 15000),
    },
  ];
}

const imageClassificationPlan = [
  "ingest_requirements",
  "define_success_metrics",
  "select_architecture",
  "design_training_pipeline",
  "plan_ops_and_monitoring",
];

const imageClassificationDescriptions = [
  {
    agent: "requirements_planner",
    reasoning:
      "Analyzed FMCG retail requirements to determine dataset composition, labeling expectations, and target KPIs for shelf image classification.",
    decision:
      "Confirmed need for 500k labeled product images with SKU metadata and established 92% accuracy KPI with monthly drift reporting.",
    confidence: 0.92,
    inputs: {
      industry: "FMCG Retail",
      data_sources: ["Shelf cameras", "Product master data"],
      constraints: ["Edge-friendly inference", "Weekly re-training window"],
    },
    outputs: {
      success_metrics: {
        accuracy: "92%",
        latency: "< 500ms",
        drift_alerts: "Monthly",
      },
      compliance: ["GDPR", "SOC2"],
    },
    alternatives_considered: [
      "Use manual audits only (too slow)",
      "Apply traditional CV feature engineering (insufficient accuracy)",
    ],
    priority: "high",
    category: "requirements",
  },
  {
    agent: "metrics_designer",
    reasoning:
      "Mapped business KPIs to ML metrics, balancing shelf availability detection with misclassification penalties for premium SKUs.",
    decision: "Adopt macro F1 as leading indicator with SKU-level confusion analytics dashboard.",
    confidence: 0.88,
    inputs: {
      kpis: ["Shelf availability", "Brand compliance"],
      penalties: ["Premium SKU false negatives"],
    },
    outputs: {
      metrics: ["Macro F1", "SKU-level recall"],
      monitoring: ["Label drift", "Data freshness"],
    },
    alternatives_considered: ["Use accuracy only"],
    priority: "medium",
    category: "metrics",
  },
  {
    agent: "architecture_selector",
    reasoning:
      "Compared PyTorch ImageNet fine-tuning on Vertex AI with alternative managed services for rapid iteration and cost control.",
    decision:
      "Choose PyTorch with Vertex AI Workbench, leveraging Google Cloud Storage and Vertex Pipelines for managed orchestration.",
    confidence: 0.9,
    inputs: {
      frameworks: ["PyTorch", "TensorFlow"],
      deployment_targets: ["Vertex AI Endpoints", "Edge TPU"],
    },
    outputs: {
      selected_stack: ["PyTorch", "Vertex AI", "BigQuery"],
      deployment: "Vertex AI Endpoint with autoscaling",
    },
    alternatives_considered: ["SageMaker (lacked GCP integration)", "Custom Kubernetes (longer setup)", "On-prem GPUs"],
    priority: "high",
    category: "architecture",
  },
  {
    agent: "pipeline_builder",
    reasoning:
      "Outlined orchestration for data prep, labeling QA, transfer learning, and evaluation using Kubeflow-compatible pipelines.",
    decision:
      "Implement Vertex Pipelines with data validation via Great Expectations and automated model registry promotion gates.",
    confidence: 0.86,
    inputs: {
      orchestration: "Vertex Pipelines",
      validation: ["Great Expectations"],
      storage: "GCS",
    },
    outputs: {
      pipeline_steps: [
        "Data ingestion",
        "Label QA",
        "Model fine-tuning",
        "Batch evaluation",
        "Model registry promotion",
      ],
      automation: "GitHub Actions triggering pipeline runs",
    },
    alternatives_considered: ["Manual notebook workflow"],
    priority: "medium",
    category: "pipeline",
  },
  {
    agent: "mlops_planner",
    reasoning:
      "Completed ops design covering monitoring, CI/CD, cost visibility, and drift response with integrated alerts to retail ops team.",
    decision:
      "Deploy Vertex Model Monitoring with BigQuery log sinks, integrate PagerDuty alerts, and schedule monthly human-in-the-loop audit.",
    confidence: 0.89,
    inputs: {
      monitoring_tools: ["Vertex Model Monitoring", "BigQuery"],
      alerting: ["PagerDuty"],
    },
    outputs: {
      observability: ["Cloud Monitoring dashboards", "Cost Explorer reports"],
      hitl: "Monthly audit workflow in AppSheet",
    },
    alternatives_considered: ["Custom Prometheus stack"],
    priority: "medium",
    category: "operations",
  },
];

const imageClassificationReasonCards = buildReasonCards(
  "template-image-classification",
  imageClassificationPlan,
  imageClassificationDescriptions,
);

const imageClassificationTemplate: MlopsTemplate = {
  id: "template-image-classification",
  name: "FMCG Shelf Image Classification",
  headline: "PyTorch on GCP for retail shelf intelligence",
  summary:
    "Delivers an end-to-end computer vision pipeline on Google Cloud using Vertex AI, automating deployment, monitoring, and compliance checks for 500k+ product images.",
  tags: ["Computer Vision", "Retail", "PyTorch"],
  techStack: ["PyTorch", "Vertex AI", "BigQuery", "Great Expectations"],
  heroStats: [
    { label: "Accuracy", value: "92% target" },
    { label: "Retrain cadence", value: "Weekly" },
    { label: "Latency", value: "<500ms" },
  ],
  highlights: [
    "Automated Vertex Pipelines with governance gates",
    "Realtime Vertex Endpoint deployment with autoscaling",
    "Retail-friendly dashboards for SKU-level performance",
  ],
  userPrompt:
    "Design an MLOps system for a FMCG retail shelf image classification project using PyTorch on Google Cloud. We need weekly retraining, SKU-level metrics, and enterprise monitoring.",
  systemIntro:
    "Here’s a pre-built workflow showcasing how our agents design a PyTorch-based retail image classification platform on Google Cloud.",
  planNodes: imageClassificationPlan,
  graphType: "retail_image_classification",
  workflowState: buildStreamingState(
    "template-image-classification",
    imageClassificationPlan,
    imageClassificationReasonCards,
  ),
  messages: buildMessages(
    "template-image-classification",
    "The agents analyzed the FMCG retail requirements and proposed a production-ready MLOps architecture on Google Cloud.",
    "Design an MLOps system for a FMCG retail image classification workload using PyTorch on GCP.",
    "✅ Architecture finalized: Vertex Pipelines orchestrate PyTorch fine-tuning, Vertex Endpoints serve models with autoscaling, and monitoring hooks into BigQuery + PagerDuty for drift alerts.",
  ),
};

const recommenderPlan = [
  "collect_requirements",
  "model_strategy",
  "data_platform_design",
  "deployment_blueprint",
  "monitoring_and_governance",
];

const recommenderDescriptions = [
  {
    agent: "planner",
    reasoning:
      "Reviewed e-commerce goals focusing on personalized journeys, cross-sell uplift, and AWS-native tooling preferences.",
    decision:
      "Prioritized hybrid collaborative filtering with contextual bandits for promotions while honoring regional data residency rules.",
    confidence: 0.87,
    inputs: {
      revenue_targets: "Increase AOV by 12%",
      traffic_profile: "10M MAU",
      constraints: ["GDPR", "Multi-region latency <200ms"],
    },
    outputs: {
      initial_scope: ["Product feed", "User events", "Campaign metadata"],
      personas: ["Frequent shopper", "Occasional visitor"],
    },
    alternatives_considered: [
      "Content-based recommendations only",
      "Manual merchandising rules",
    ],
    priority: "high",
    category: "requirements",
  },
  {
    agent: "architecture_selector",
    reasoning:
      "Evaluated Amazon Personalize vs custom SageMaker pipelines considering need for exploration policies and hybrid embeddings.",
    decision:
      "Adopt SageMaker feature store + custom ranking model with Amazon Personalize for cold-start acceleration.",
    confidence: 0.83,
    inputs: {
      services: ["Amazon Personalize", "SageMaker"],
      data: ["EventBridge", "Glue"],
    },
    outputs: {
      stack: ["SageMaker Feature Store", "Kinesis Data Firehose", "Lambda"],
      exploration_policy: "Contextual epsilon-greedy",
    },
    alternatives_considered: ["Fully custom on Kubernetes"],
    priority: "high",
    category: "architecture",
  },
  {
    agent: "data_engineer",
    reasoning:
      "Outlined streaming ingestion with Glue ETL jobs, partitioned S3 lake, and feature store synchronization.",
    decision:
      "Implement Kinesis -> S3 raw zone -> Glue curated zone with automated feature pipelines into SageMaker Feature Store.",
    confidence: 0.85,
    inputs: {
      ingestion: ["Kinesis Data Streams"],
      storage: "S3 multi-region",
    },
    outputs: {
      pipelines: [
        "Clickstream processing",
        "Catalog enrichment",
        "Campaign performance",
      ],
      governance: ["Glue Data Catalog", "Lake Formation"],
    },
    alternatives_considered: ["Batch-only ingestion"],
    priority: "medium",
    category: "data_platform",
  },
  {
    agent: "deployment_strategist",
    reasoning:
      "Compared Lambda-based real-time inference with ECS/Fargate for scaling personalized recommendations during flash sales.",
    decision:
      "Deploy inference on Amazon ECS with Application Load Balancer + DynamoDB cache, fallback Lambda for low-traffic regions.",
    confidence: 0.82,
    inputs: {
      traffic_spikes: "Black Friday x8 baseline",
      latency_goal: "<150ms",
    },
    outputs: {
      deployment: ["ECS Fargate", "AWS App Runner for preview"],
      ci_cd: "CodePipeline with Canary deployments",
    },
    alternatives_considered: ["Lambda-only", "Self-managed EC2"],
    priority: "medium",
    category: "deployment",
  },
  {
    agent: "governance_lead",
    reasoning:
      "Finalized observability with CloudWatch Anomaly Detection, bias tracking, and customer data safeguards for compliance.",
    decision:
      "Enable Amazon SageMaker Model Monitor, integrate AWS Config rules, and surface fairness dashboards via QuickSight.",
    confidence: 0.88,
    inputs: {
      monitoring: ["Model Monitor", "CloudWatch"],
      compliance: ["GDPR", "CCPA"],
    },
    outputs: {
      alerts: ["PagerDuty", "Slack"],
      documentation: "Automated runbooks in Confluence",
    },
    alternatives_considered: ["Manual spreadsheet tracking"],
    priority: "high",
    category: "operations",
  },
];

const recommenderReasonCards = buildReasonCards(
  "template-ecommerce-recommender",
  recommenderPlan,
  recommenderDescriptions,
);

const recommenderTemplate: MlopsTemplate = {
  id: "template-ecommerce-recommender",
  name: "E-commerce Recommendation Engine",
  headline: "Personalized journeys on AWS",
  summary:
    "Blends Amazon Personalize with custom SageMaker ranking services, backed by streaming data pipelines and full-stack observability.",
  tags: ["Recommender", "AWS", "Personalization"],
  techStack: ["SageMaker", "Amazon Personalize", "Kinesis", "Glue", "ECS"],
  heroStats: [
    { label: "AOV uplift", value: "+12%" },
    { label: "Regions", value: "3" },
    { label: "Latency", value: "<150ms" },
  ],
  highlights: [
    "Hybrid Amazon Personalize + SageMaker architecture",
    "Streaming feature pipelines with Lake Formation governance",
    "CloudWatch + Model Monitor for bias and drift insights",
  ],
  userPrompt:
    "Design an AWS-native recommendation system that uses Amazon Personalize and SageMaker with streaming data ingestion and enterprise monitoring.",
  systemIntro:
    "This pre-built workflow highlights how our agents craft an AWS personalization platform with streaming features and rigorous governance.",
  planNodes: recommenderPlan,
  graphType: "aws_recommender_system",
  workflowState: buildStreamingState(
    "template-ecommerce-recommender",
    recommenderPlan,
    recommenderReasonCards,
  ),
  messages: buildMessages(
    "template-ecommerce-recommender",
    "Agents leveraged AWS-native tooling to architect a scalable recommender with streaming features and tight governance controls.",
    "Design an AWS-native recommendation engine combining Amazon Personalize and SageMaker with streaming pipelines and monitoring.",
    "✅ Solution ready: SageMaker Feature Store feeds hybrid ranking models, ECS powers realtime inference, and Model Monitor guards bias across regions.",
  ),
};

const ragPlan = [
  "scope_understanding",
  "corpus_ingestion",
  "retriever_blueprint",
  "orchestration_design",
  "governance_strategy",
];

const ragDescriptions = [
  {
    agent: "requirements_analyst",
    reasoning:
      "Identified core objectives for internal knowledge RAG assistant, emphasizing SOC2 compliance and granular source attribution.",
    decision:
      "Prioritize high-confidence retrieval with role-aware access policies and audit logging across document lifecycle.",
    confidence: 0.91,
    inputs: {
      document_types: ["Sales playbooks", "Architecture RFCs", "Policies"],
      compliance: ["SOC2", "ISO 27001"],
    },
    outputs: {
      user_segments: ["Support", "Sales Engineers", "Leadership"],
      success_metrics: ["First response accuracy", "Citation usage"],
    },
    alternatives_considered: ["Open internet search"],
    priority: "high",
    category: "requirements",
  },
  {
    agent: "data_curator",
    reasoning:
      "Evaluated ingestion options for 10k+ PDFs, Confluence spaces, and GitHub markdown ensuring metadata normalization for retrieval.",
    decision:
      "Adopt LangSmith ingestion flows with chunking at 800 tokens, metadata embeddings, and versioned storage in S3 + DynamoDB index.",
    confidence: 0.9,
    inputs: {
      volume: "10k docs",
      sources: ["GitHub", "Confluence", "SharePoint"],
    },
    outputs: {
      processing: ["LangChain Document Loaders"],
      storage: ["S3", "DynamoDB"],
    },
    alternatives_considered: ["Manual uploads"],
    priority: "medium",
    category: "data",
  },
  {
    agent: "retrieval_architect",
    reasoning:
      "Balanced retrieval quality with latency by comparing hybrid search (BM25 + embeddings) against vector-only approaches.",
    decision:
      "Implement hybrid retriever using OpenSearch vector engine + text ranking reranker, caching frequent corpora queries in Redis.",
    confidence: 0.88,
    inputs: {
      similarity: "Hybrid BM25 + cosine",
      cache: "Redis 6",
    },
    outputs: {
      retriever: {
        primary: "OpenSearch vector",
        reranker: "Cohere Rerank",
      },
      chunking: "800 token overlap 80",
    },
    alternatives_considered: ["Pure vector search", "Weaviate"],
    priority: "high",
    category: "retrieval",
  },
  {
    agent: "orchestration_designer",
    reasoning:
      "Mapped LangGraph workflow for query parsing, retrieval, critique loop, HITL escalation, and streaming responses via SSE.",
    decision:
      "Deploy LangGraph agents orchestrated in FastAPI worker, use Anthropic Claude for critique + generation, and SSE streaming to frontend reason cards.",
    confidence: 0.9,
    inputs: {
      orchestration: "LangGraph",
      llms: ["Claude Sonnet", "GPT-4"],
    },
    outputs: {
      workflow: [
        "Intent classification",
        "Retriever call",
        "Critic agent",
        "Response composer",
      ],
      observability: "LangSmith tracing + OpenTelemetry",
    },
    alternatives_considered: ["Simple chain without critique"],
    priority: "high",
    category: "orchestration",
  },
  {
    agent: "governance_officer",
    reasoning:
      "Codified policy posture with redaction, usage analytics, and escalation workflows for low-confidence answers.",
    decision:
      "Enable policy engine gating responses under 0.7 confidence, surface audit trail in Honeycomb, and ship alert to Slack via PagerDuty webhook.",
    confidence: 0.87,
    inputs: {
      policies: ["PII redaction", "Role-based access"],
      alerts: ["Slack", "PagerDuty"],
    },
    outputs: {
      thresholds: { confidence: 0.7, auto_escalate: true },
      logging: ["CloudWatch", "Honeycomb"],
    },
    alternatives_considered: ["Allow all responses"],
    priority: "high",
    category: "governance",
  },
];

const ragReasonCards = buildReasonCards(
  "template-rag-genai",
  ragPlan,
  ragDescriptions,
);

const ragTemplate: MlopsTemplate = {
  id: "template-rag-genai",
  name: "Enterprise RAG Knowledge Assistant",
  headline: "LangGraph-powered GenAI for internal docs",
  summary:
    "Demonstrates a secure RAG workflow with LangGraph orchestration, hybrid retrieval, and compliance-guarded response streaming.",
  tags: ["GenAI", "LangGraph", "RAG"],
  techStack: ["LangGraph", "OpenSearch", "Claude", "LangSmith", "Redis"],
  heroStats: [
    { label: "Confidence threshold", value: "0.70" },
    { label: "Documents", value: "10k+" },
    { label: "Response time", value: "<4s" },
  ],
  highlights: [
    "Hybrid BM25 + vector retrieval with reranking",
    "LangGraph agents orchestrating critique and HITL gates",
    "Streaming SSE updates with audit-friendly logging",
  ],
  userPrompt:
    "Design a LangGraph-based RAG assistant that chats with internal company docs, enforces policy checks, and streams reasoning to the UI.",
  systemIntro:
    "Preview how the platform assembles a secure LangGraph RAG stack with hybrid retrieval and policy-aware answers.",
  planNodes: ragPlan,
  graphType: "enterprise_rag",
  workflowState: buildStreamingState(
    "template-rag-genai",
    ragPlan,
    ragReasonCards,
  ),
  messages: buildMessages(
    "template-rag-genai",
    "Agents orchestrated LangGraph nodes with hybrid retrieval, critique, and compliance gates to power an internal knowledge assistant.",
    "Design a LangGraph-based RAG assistant for company documents with policy enforcement and streaming updates.",
    "✅ Finalized approach: LangGraph orchestrates intent, retrieval, and critique agents; OpenSearch hybrid index powers retrieval; responses stream via SSE with policy guardrails.",
  ),
};

export const MLOPS_TEMPLATES: MlopsTemplate[] = [
  imageClassificationTemplate,
  recommenderTemplate,
  ragTemplate,
];

export function getTemplateById(id: string): MlopsTemplate | undefined {
  return MLOPS_TEMPLATES.find((template) => template.id === id);
}
