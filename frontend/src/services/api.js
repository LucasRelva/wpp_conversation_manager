import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
});

export const api = {
      // Conversations
      getConversations: () => client.get('/conversations'),
      getConversation: (channel, userId) => client.get(`/conversations/${channel}/${userId}`),

      // Assume (assign agent)
      assumeConversation: (channel, userId, agentId) =>
            client.post(`/conversations/${channel}/${userId}/assume`, { agent_id: agentId }),

      // Send message
      sendMessage: (channel, userId, text, agentId = 'agent_1') =>
            client.post(`/conversations/${channel}/${userId}/message`, { text }, {
                  params: { agent_id: agentId }
            }),

      // Close conversation
      closeConversation: (channel, userId, message = null) =>
            client.post(`/conversations/${channel}/${userId}/close`, { message }),

      // Get handoff queue
      getHandoffQueue: () => client.get('/handoff-queue'),

      // List available channels
      listChannels: () => client.get('/channels'),
};

export default api;
