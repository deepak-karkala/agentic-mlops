# Landing Page Redesign Plan

## Overview
- Deliver a modern landing experience that demonstrates value instantly while preserving the existing live chat workflow.
- Introduce a curated template library for fast demos, mirroring the dual-panel reasoning view without waiting on the full LangGraph run.

## Experience Goals
- Highlight the product’s purpose with a hero banner describing the agentic MLOps platform, key benefits, and primary calls to action.
- Provide three ready-to-explore MLOps blueprints: FMCG image classification (PyTorch + GCP), e-commerce recommender (AWS), and RAG-based GenAI with LangGraph.
- Keep the chat/workflow experience recognizable by reusing the current two-panel layout when previewing templates.
- Allow users to exit a template preview easily and re-engage the live workflow with their own prompt.

## Layout Structure
1. **Hero Section**
   - Gradient background, concise headline, supporting copy, and dual CTA buttons ("Start a custom design", "Explore templates").
   - Optional badge or stat row (e.g., "Agents orchestrated", "Deployable blueprints").
2. **Template Gallery**
   - Responsive three-card grid displaying template name, industry, stack badges, short summary, and a "Preview workflow" button.
   - Hover states with subtle motion and depth to match modern AI UIs.
3. **Workflow & Chat Section**
   - Existing `EnhancedChatInterface` anchored below the gallery.
   - Default empty state offers usage tips; selecting a template injects a static workflow preview within this section.

## State Management
- Introduce a `LandingExperience` component to coordinate page-level state: `{ mode: "idle" | "template" | "live"; activeTemplateId?: string; }`.
- Template selection sets `mode` to `"template"`, passes static data into the workflow preview, and disables the live input.
- "Back to templates" resets to `mode: "idle"`.
- "Run live" switches to `"live"` mode, pre-filling the chat input with the template prompt and handing control back to the existing async flow.

## Template Data Model
Create `frontend/data/mlops-templates.ts` holding metadata and precomputed workflow artifacts.

```ts
export interface MlopsTemplate {
  id: string;
  name: string;
  headline: string;
  summary: string;
  tags: string[];
  techStack: string[];
  heroStats: { label: string; value: string }[];
  userPrompt: string;
  systemIntro: string;
  planNodes: string[];
  timeline: TimelineNode[];
  workflowProgress: WorkflowProgress;
  reasonCards: ReasonCard[];
  messages: EnhancedMessage[];
  artifacts?: Array<{ title: string; content: string }>;
}
```

Populate the three templates with:
- Human-readable agent reasoning (`ReasonCard.reasoning`, `decision`, `inputs`, `outputs`, `alternatives_considered`).
- Matching timeline and workflow progress snapshots (e.g., all nodes marked completed, progress 100%).
- Prefilled chat transcript in `messages` (system intro explaining the template plus assistant summary).

## Component Updates
- **`frontend/app/page.tsx`**: replace the simple layout with `LandingExperience`, composing hero, gallery, and chat sections.
- **Hero UI**: Optional helper components in `frontend/components/landing/` (`hero.tsx`, `cta-buttons.tsx`).
- **Template Gallery**: add `TemplateCard.tsx` and `TemplateStats.tsx` under `frontend/components/templates/`.
- **Template Preview**: create `TemplateShowcase.tsx` that renders the static workflow visualization, summary sidebar, and action buttons.

## Chat & Workflow Integration
- Extend `EnhancedChatInterface` to accept optional props:
  - `prefillMessages?: EnhancedMessage[]`
  - `prefillDecisionSetId?: string`
  - `staticWorkflowState?: StreamingState`
  - Callbacks: `onExitTemplate`, `onRunLive`
- When `staticWorkflowState` exists, bypass live polling and pass data into `WorkflowVisualization`.

### Workflow Components
- Update `WorkflowVisualization` and `WorkflowContainer` to accept `staticState?: StreamingState`. If provided, skip `useStreamingEvents` and feed the supplied events/reason cards directly.
- Ensure `WorkflowStatusPanel` can consume precomputed `TimelineNode[]` without relying on live updates.

## Styling & Polish
- Add gradient helpers or background utilities in `frontend/app/globals.css` or extend Tailwind config.
- Use Tailwind’s responsive utilities (`md:`/`lg:`/`xl:`) to maintain balance on tablets and desktops.
- Apply transition classes for hover/focus states (`transition`, `duration-200`, `hover:-translate-y-1`, `hover:shadow-lg`).
- Mirror leading AI products by adopting clean typography, muted backgrounds, rounded containers, and subtle badges.

## Accessibility & Responsiveness
- Provide ARIA labels for CTA buttons and template actions.
- Ensure keyboard navigation works across cards and preview controls.
- When in template mode, keep focus management intuitive (focus the preview container, return focus to the triggering card when closing).

## Content & QA Considerations
- Validate that template reasoning text, inputs, and outputs are accurate representations of expected agent behavior.
- Coordinate with product/design for final copy and asset selection (icons, illustrations if desired).
- After implementation, test across breakpoints and browsers; run Playwright smoke test on landing flow if available.

## Implementation Sequence
1. Scaffold template data and new components in isolation with mock content.
2. Adapt `WorkflowVisualization`/`WorkflowContainer` to support static state.
3. Refactor `EnhancedChatInterface` to support prefilled template mode while preserving live behavior.
4. Compose final landing page layout with hero + gallery + chat.
5. Polish styling, animations, and accessibility.
6. Validate interactions, including switching between template and live modes.

## Future Enhancements
- Add more templates with filtering (industry, modality, cloud).
- Embed quick video walkthrough or interactive guided tour alongside the gallery.
- Surface deployment instructions or downloadable artifacts per template.
