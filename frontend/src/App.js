import React, { useState, useEffect, useCallback } from 'react';
import { AlertCircle, Wifi, WifiOff } from 'lucide-react';
import api from './services/api';
import { useWebSocket } from './hooks/useWebSocket';
import ConversationList from './components/ConversationList';
import ChatView from './components/ChatView';
import './App.css';

const AGENT_ID = 'agent_1'; // In production, this would come from auth

function App() {
      const [conversations, setConversations] = useState([]);
      const [selectedConversation, setSelectedConversation] = useState(null);
      const [messages, setMessages] = useState([]);
      const [loading, setLoading] = useState(true);
      const [error, setError] = useState(null);
      const [isAssigning, setIsAssigning] = useState(false);
      const [loadingMessages, setLoadingMessages] = useState(false);

      // WebSocket connection
      const { isConnected, messages: wsMessages } = useWebSocket(AGENT_ID);

      // Fetch all conversations
      const fetchConversations = useCallback(async () => {
            try {
                  setLoading(true);
                  setError(null);
                  const response = await api.getConversations();
                  setConversations(response.data);
            } catch (err) {
                  console.error('Error fetching conversations:', err);
                  setError('Failed to load conversations');
            } finally {
                  setLoading(false);
            }
      }, []);

      // Fetch conversation details
      const fetchConversationMessages = useCallback(async (channel, userId) => {
            try {
                  setLoadingMessages(true);
                  const response = await api.getConversation(channel, userId);
                  setMessages(response.data.messages || []);
            } catch (err) {
                  console.error('Error fetching messages:', err);
                  setError('Failed to load conversation');
            } finally {
                  setLoadingMessages(false);
            }
      }, []);

      // Initialize on mount
      useEffect(() => {
            fetchConversations();
      }, [fetchConversations]);

      // Fetch messages when conversation is selected
      useEffect(() => {
            if (selectedConversation) {
                  fetchConversationMessages(selectedConversation.channel, selectedConversation.user_id);
            }
      }, [selectedConversation, fetchConversationMessages]);

      // Handle WebSocket messages
      useEffect(() => {
            if (wsMessages.length === 0) return;

            const lastMessage = wsMessages[0];

            if (lastMessage.type === 'new_message' || lastMessage.type === 'message_sent') {
                  // Add message if it's from current conversation
                  if (
                        selectedConversation &&
                        selectedConversation.channel === lastMessage.channel &&
                        selectedConversation.user_id === lastMessage.user_id
                  ) {
                        const newMsg = {
                              message_id: `msg_${Date.now()}`,
                              text: lastMessage.text,
                              timestamp: lastMessage.timestamp,
                              user_name: lastMessage.user_name || lastMessage.agent_id,
                              metadata: lastMessage.agent_id ? { agent_id: lastMessage.agent_id } : {}
                        };
                        setMessages(prev => [...prev, newMsg]);
                  }
            } else if (lastMessage.type === 'conversation_assigned') {
                  // Update conversation assignment
                  setConversations(prev =>
                        prev.map(c =>
                              c.channel === lastMessage.channel && c.user_id === lastMessage.user_id
                                    ? { ...c, assigned_to: lastMessage.agent_id, status: 'HUMAN_ACTIVE' }
                                    : c
                        )
                  );
            }
      }, [wsMessages, selectedConversation]);

      // Handle assume conversation
      const handleAssume = async (conversation) => {
            try {
                  setIsAssigning(true);
                  await api.assumeConversation(conversation.channel, conversation.user_id, AGENT_ID);

                  // Update local state
                  setConversations(prev =>
                        prev.map(c =>
                              c.channel === conversation.channel && c.user_id === conversation.user_id
                                    ? { ...c, assigned_to: AGENT_ID, status: 'HUMAN_ACTIVE' }
                                    : c
                        )
                  );

                  // Select the conversation
                  setSelectedConversation({ ...conversation, assigned_to: AGENT_ID, status: 'HUMAN_ACTIVE' });
            } catch (err) {
                  console.error('Error assuming conversation:', err);
                  setError('Failed to assume conversation');
            } finally {
                  setIsAssigning(false);
            }
      };

      // Handle send message
      const handleSendMessage = async (text) => {
            if (!selectedConversation) return;

            try {
                  await api.sendMessage(
                        selectedConversation.channel,
                        selectedConversation.user_id,
                        text,
                        AGENT_ID
                  );

                  // Add message to local state
                  const newMsg = {
                        message_id: `msg_${Date.now()}`,
                        text,
                        timestamp: new Date().toISOString(),
                        user_name: `Agent: ${AGENT_ID}`,
                        metadata: { agent_id: AGENT_ID }
                  };
                  setMessages(prev => [...prev, newMsg]);
            } catch (err) {
                  console.error('Error sending message:', err);
                  setError('Failed to send message');
            }
      };

      return (
            <div className="flex h-screen bg-gray-100">
                  {/* Sidebar */}
                  <div className="w-96 border-r border-gray-300 bg-white flex flex-col">
                        <ConversationList
                              conversations={conversations}
                              selectedConversation={selectedConversation}
                              onSelectConversation={setSelectedConversation}
                              onAssume={handleAssume}
                              isAssigning={isAssigning}
                              agentId={AGENT_ID}
                        />
                  </div>

                  {/* Main content */}
                  <div className="flex-1 flex flex-col">
                        {/* Top bar */}
                        <div className="bg-white border-b border-gray-200 p-4 flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                    <h1 className="text-xl font-bold text-gray-900">Handoff Dashboard</h1>
                              </div>

                              <div className="flex items-center gap-4">
                                    {/* WebSocket status */}
                                    <div className="flex items-center gap-2">
                                          {isConnected ? (
                                                <>
                                                      <Wifi size={18} className="text-green-500" />
                                                      <span className="text-sm text-gray-600">Connected</span>
                                                </>
                                          ) : (
                                                <>
                                                      <WifiOff size={18} className="text-red-500" />
                                                      <span className="text-sm text-gray-600">Disconnected</span>
                                                </>
                                          )}
                                    </div>

                                    {/* Conversation count */}
                                    <div className="text-sm text-gray-600">
                                          {conversations.length} conversation{conversations.length !== 1 ? 's' : ''}
                                    </div>
                              </div>
                        </div>

                        {/* Error banner */}
                        {error && (
                              <div className="bg-red-50 border-b border-red-200 p-4 flex items-center gap-2">
                                    <AlertCircle size={20} className="text-red-500" />
                                    <span className="text-sm text-red-700">{error}</span>
                                    <button
                                          onClick={() => setError(null)}
                                          className="ml-auto text-red-600 hover:text-red-700"
                                    >
                                          ✕
                                    </button>
                              </div>
                        )}

                        {/* Chat view */}
                        <ChatView
                              conversation={selectedConversation}
                              messages={messages}
                              onSendMessage={handleSendMessage}
                              isLoading={loadingMessages}
                        />
                  </div>
            </div>
      );
}

export default App;
