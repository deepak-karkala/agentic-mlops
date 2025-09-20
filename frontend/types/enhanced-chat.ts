import { Message, ChatState } from "./chat";

export interface EnhancedMessage extends Message {
  decisionSetId?: string;
  jobId?: string;
  jobStatus?: string;
  isStreamingActive?: boolean;
}

export interface EnhancedChatState extends Omit<ChatState, "messages"> {
  messages: EnhancedMessage[];
  currentDecisionSetId?: string;
}
