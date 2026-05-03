import React, { useEffect, useState, useRef } from 'react';
import { MessageCircle, MessageSquare, Clock, CheckCircle, AlertCircle, Settings } from 'lucide-react';
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

const getStatusColor = (status) => {
  const colors = {
    BOT_ACTIVE: 'bg-blue-100 text-blue-800',
    HUMAN_HANDOFF: 'bg-yellow-100 text-yellow-800',
    HUMAN_ACTIVE: 'bg-green-100 text-green-800',
    CLOSED: 'bg-gray-100 text-gray-800'
  };
  return colors[status] || 'bg-gray-100 text-gray-800';
};

const ConversationList = ({ 
  conversations, 
  selectedConversation, 
  onSelectConversation,
  onAssume,
  isAssigning,
  agentId 
}) => {
  const [filter, setFilter] = useState('all'); // all, waiting, active

  const filteredConversations = conversations.filter(conv => {
    if (filter === 'waiting') return conv.status === 'HUMAN_HANDOFF';
    if (filter === 'active') return conv.status === 'HUMAN_ACTIVE';
    return true;
  });

  const groupedByStatus = {
    waiting: filteredConversations.filter(c => c.status === 'HUMAN_HANDOFF'),
    active: filteredConversations.filter(c => c.status === 'HUMAN_ACTIVE'),
    other: filteredConversations.filter(c => c.status !== 'HUMAN_HANDOFF' && c.status !== 'HUMAN_ACTIVE')
  };

  return (
    <div className="w-full h-full bg-white border-r border-gray-200 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Conversations</h1>
        
        {/* Filter tabs */}
        <div className="flex gap-2">
          {[
            { id: 'all', label: 'All', icon: MessageCircle },
            { id: 'waiting', label: 'Waiting', icon: Clock },
            { id: 'active', label: 'Active', icon: MessageSquare }
          ].map(tab => {
            const Icon = tab.icon;
            const count = groupedByStatus[tab.id === 'all' ? 'waiting' : tab.id].length;
            return (
              <button
                key={tab.id}
                onClick={() => setFilter(tab.id)}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg transition ${
                  filter === tab.id
                    ? 'bg-blue-100 text-blue-700'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <Icon size={16} />
                <span className="text-sm font-medium">{tab.label}</span>
                {count > 0 && (
                  <span className="bg-red-500 text-white text-xs rounded-full px-2 py-0.5">
                    {count}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Conversations list */}
      <div className="flex-1 overflow-y-auto scrollbar-hide">
        {filteredConversations.length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            <MessageCircle size={32} className="mx-auto mb-2 opacity-50" />
            <p>No conversations</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {filteredConversations.map(conv => (
              <div
                key={`${conv.channel}-${conv.user_id}`}
                className={`p-4 cursor-pointer transition hover:bg-gray-50 ${
                  selectedConversation?.channel === conv.channel &&
                  selectedConversation?.user_id === conv.user_id
                    ? 'bg-blue-50 border-l-4 border-blue-500'
                    : ''
                }`}
                onClick={() => onSelectConversation(conv)}
              >
                <div className="flex items-start gap-3">
                  {/* Channel icon */}
                  <div className="text-2xl mt-1">{getChannelIcon(conv.channel)}</div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <h3 className="font-semibold text-gray-900 truncate">{conv.name}</h3>
                      <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(conv.status)}`}>
                        {conv.status.replace(/_/g, ' ')}
                      </span>
                    </div>

                    <p className="text-sm text-gray-600 truncate mb-2">{conv.last_message}</p>

                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span>{conv.message_count} messages</span>
                      {conv.assigned_to ? (
                        <span className="text-green-600 font-medium">→ {conv.assigned_to}</span>
                      ) : conv.status === 'HUMAN_HANDOFF' && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onAssume(conv);
                          }}
                          disabled={isAssigning}
                          className="text-blue-600 hover:text-blue-700 font-medium disabled:opacity-50"
                        >
                          {isAssigning ? 'Assuming...' : 'Assume'}
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200 bg-gray-50">
        <div className="text-sm text-gray-600">
          <p className="font-medium">Agent: <span className="text-gray-900">{agentId}</span></p>
        </div>
      </div>
    </div>
  );
};

export default ConversationList;
