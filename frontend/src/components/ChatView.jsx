import React, { useEffect, useState, useRef } from 'react';
import { Send, MoreVertical } from 'lucide-react';
import api from '../services/api';

const getChannelIcon = (channel) => {
  const icons = {
    whatsapp: '💬',
    telegram: '✈️',
    webchat: '💻',
    mock: '🧪'
  };
  return icons[channel] || '📱';
};

const ChatView = ({ conversation, messages, onSendMessage, onCloseConversation, isLoading }) => {
  const [inputValue, setInputValue] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [showMenu, setShowMenu] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    setIsSending(true);
    try {
      await onSendMessage(inputValue);
      setInputValue('');
    } finally {
      setIsSending(false);
    }
  };

  if (!conversation) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="text-6xl mb-4">💬</div>
          <p className="text-gray-500 text-lg">Select a conversation to start chatting</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-white">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-cyan-50 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="text-3xl">{getChannelIcon(conversation.channel)}</div>
          <div>
            <h2 className="text-lg font-bold text-gray-900">{conversation.name}</h2>
            <p className="text-sm text-gray-600">{conversation.channel.toUpperCase()}</p>
          </div>
        </div>

        <div className="relative">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="p-2 hover:bg-blue-100 rounded-lg transition"
          >
            <MoreVertical size={20} className="text-gray-600" />
          </button>

          {showMenu && (
            <div className="absolute right-0 mt-2 bg-white border border-gray-200 rounded-lg shadow-lg z-10">
              <button
                onClick={async () => {
                  await api.closeConversation(conversation.channel, conversation.user_id);
                  setShowMenu(false);
                  onCloseConversation(conversation);
                }}
                className="w-full px-4 py-2 text-left hover:bg-red-50 text-red-600"
              >
                Close Conversation
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-hide bg-gray-50">
        {isLoading && messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-gray-400">Loading messages...</div>
          </div>
        ) : messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-gray-400">No messages yet</div>
          </div>
        ) : (
          messages.map((msg, idx) => {
            const isAgent = msg.metadata?.agent_id || msg.user_name?.includes('Agent');

            return (
              <div
                key={msg.message_id || `${msg.timestamp || 'no-ts'}-${idx}`}
                className={`flex ${isAgent ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                    isAgent
                      ? 'bg-blue-500 text-white rounded-br-none'
                      : 'bg-white text-gray-900 border border-gray-200 rounded-bl-none'
                  }`}
                >
                  {!isAgent && conversation.status === 'HUMAN_ACTIVE' && (
                    <p className="text-xs font-semibold text-gray-500 mb-1">{msg.user_name}</p>
                  )}
                  <p className="text-sm break-words">{msg.text}</p>
                  <p className={`text-xs mt-1 ${isAgent ? 'text-blue-100' : 'text-gray-500'}`}>
                    {msg.timestamp
                      ? new Date(msg.timestamp).toLocaleTimeString()
                      : ''}
                  </p>
                </div>
              </div>
            );
          })
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      {conversation && (
        <div className="p-4 border-t border-gray-200 bg-white">
          <div className="flex gap-2">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              placeholder="Type a message..."
              disabled={isSending}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            />
            <button
              onClick={handleSendMessage}
              disabled={isSending || !inputValue.trim()}
              className="bg-blue-500 hover:bg-blue-600 disabled:opacity-50 text-white px-4 py-2 rounded-lg transition flex items-center gap-2"
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatView;
