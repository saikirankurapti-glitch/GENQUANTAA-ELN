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
  async sendChatMessage(payload: ChatRequestPayload): Promise<ChatResponsePayload> {
    const response = await apiClient.post('/ai/chat', {
      message: payload.message,
      feature: payload.feature || 'qa',
      provider: payload.provider || 'groq',
      model_name: payload.model_name || 'llama-3.3-70b-versatile',
      conversation_id: payload.conversation_id,
    });
    return response.data;
  },

  async ask(prompt: string, feature: string = 'copilot'): Promise<{ response: string }> {
    const resp = await this.sendChatMessage({
      message: prompt,
      feature,
    });
    return { response: resp.content || '' };
  },

  async generateSOP(title: string, domain: string = 'General'): Promise<{ content: string }> {
    const prompt = `Generate a rigorous 5-step Standard Operating Procedure (SOP) protocol for an experiment titled: "${title}" in the domain of ${domain}. Return numbered steps only.`;
    const resp = await this.sendChatMessage({
      message: prompt,
      feature: 'protocol_generator',
    });
    return { content: resp.content || '' };
  },

  async summarizeExperiment(experimentId: string, objective: string, results: string): Promise<{ summary: string }> {
    const prompt = `Summarize this scientific experiment in 2 concise executive paragraphs. Objective: ${objective}. Results: ${results}.`;
    const resp = await this.sendChatMessage({
      message: prompt,
      feature: 'summarize',
    });
    return { summary: resp.content || '' };
  }
};
