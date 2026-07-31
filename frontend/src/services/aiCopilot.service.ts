import { apiClient } from './apiClient';

export interface ChatRequestPayload {
  message: string;
  feature?: string;
  provider?: string;
  model_name?: string;
  conversation_id?: string;
}

export interface ChatResponsePayload {
  conversation_id: string;
  message_id: string;
  role: string;
  content: string;
  model_name: string;
  provider: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  latency_ms: number;
  citations: Array<{
    document_id: string;
    title: string;
    source_type: string;
    relevance_score: number;
    excerpt: string;
  }>;
}

export const aiCopilotService = {
  async sendChatMessage(payload: ChatRequestPayload) {
    const response = await apiClient.post('/ai/chat', {
      message: payload.message,
      feature: payload.feature || 'qa',
      provider: payload.provider || 'groq',
      model_name: payload.model_name || 'llama-3.3-70b-versatile',
      conversation_id: payload.conversation_id,
    });
    return response.data;
  },
};
