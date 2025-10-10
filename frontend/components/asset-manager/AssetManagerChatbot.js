'use client';

import { useState, useEffect, useRef } from 'react';
import { assetManagerAPI } from '@/lib/api/assetManager';

const AssetManagerChatbot = ({ selectedBrand, onDataUpdate }) => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isConnected, setIsConnected] = useState(true); // Always connected for HTTP
  const [isTyping, setIsTyping] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [isMaximized, setIsMaximized] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Initialize with greeting message
    const greetingMessage = selectedBrand 
      ? `Hello! I'm ready to help you manage assets for ${selectedBrand.name}. I can assist you with creating, updating, and managing brands, competitors, templates, and help with data scraping. What would you like to do?`
      : "Hello! I'm ready to help you manage your assets. I can assist you with creating, updating, and managing brands, competitors, templates, and help with data scraping. What would you like to do?";
    
    setMessages([{
      id: Date.now(),
      text: greetingMessage,
      sender: 'agent',
      timestamp: new Date(),
      type: 'text'
    }]);
  }, [selectedBrand]);

  // Removed WebSocket initialization - using HTTP instead

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage = {
      id: Date.now(),
      text: inputMessage,
      sender: 'user',
      timestamp: new Date(),
      type: 'text'
    };

    setMessages(prev => [...prev, userMessage]);
    const currentMessage = inputMessage;
    setInputMessage('');
    setIsTyping(true);

    try {
      // Prepare chat history for the API call
      const chatHistory = messages.map(msg => ({
        sender: msg.sender,
        text: msg.text
      }));

      // Send message via HTTP API
      const response = await assetManagerAPI.sendMessage(
        currentMessage,
        chatHistory,
        selectedBrand
      );

      if (response.success) {
        const agentMessage = {
          id: Date.now() + 1,
          text: response.response,
          sender: 'agent',
          timestamp: new Date(),
          type: 'text'
        };
        setMessages(prev => [...prev, agentMessage]);
      } else {
        throw new Error(response.error || 'Unknown error');
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        text: `Failed to send message: ${error.message}. Please try again.`,
        sender: 'system',
        timestamp: new Date(),
        type: 'error'
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const quickActions = [
    {
      text: "Create a new brand",
      prompt: "I want to create a new brand. Can you help me set it up?",
      icon: "🏢"
    },
    {
      text: "Add a competitor",
      prompt: "I need to add a new competitor to track. Can you help me?",
      icon: "👥"
    },
    {
      text: "Create a template",
      prompt: "I want to create a new content template. Can you guide me?",
      icon: "📝"
    },
    {
      text: "Scrape competitor data",
      prompt: "Can you help me scrape data from my competitors?",
      icon: "🔍"
    },
    {
      text: "Show my assets overview",
      prompt: "Can you show me an overview of all my brands, competitors, and templates?",
      icon: "📊"
    },
    {
      text: "Update existing asset",
      prompt: "I want to update one of my existing assets. Can you help me?",
      icon: "✏️"
    }
  ];

  const handleQuickAction = (prompt) => {
    setInputMessage(prompt);
    inputRef.current?.focus();
  };

  return (
    <div className={`fixed bottom-4 right-4 z-50 transition-all duration-300 ease-in-out ${
      isMinimized 
        ? 'w-80 h-16' 
        : isMaximized 
          ? 'w-96 h-[calc(100vh-2rem)]' 
          : 'w-80 h-[500px]'
    }`}>
      <div className="bg-white rounded-xl shadow-2xl border border-gray-200 flex flex-col h-full overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-white rounded-t-xl">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-blue-700 rounded-full flex items-center justify-center">
              <span className="text-white font-bold text-sm">AI</span>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-900">AI Assistant</h3>
              <div className="flex items-center space-x-2">
                <div className="w-1.5 h-1.5 rounded-full bg-green-500"></div>
                <span className="text-xs text-gray-500">
                  Online
                </span>
              </div>
            </div>
          </div>
          <div className="flex items-center space-x-1">
            <button
              onClick={() => onDataUpdate && onDataUpdate()}
              className="p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-all duration-200"
              title="Refresh data"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
            <button
              onClick={() => setIsMaximized(!isMaximized)}
              className="p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-all duration-200"
              title={isMaximized ? "Restore" : "Maximize"}
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                {isMaximized ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 9V4.5M9 9H4.5M9 9L3.5 3.5M15 9v4.5M15 9h4.5M15 9l5.5-5.5M9 15v4.5M9 15H4.5M9 15l-5.5 5.5M15 15h4.5M15 15v4.5m0-4.5l5.5 5.5" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                )}
              </svg>
            </button>
            <button
              onClick={() => setIsMinimized(!isMinimized)}
              className="p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-all duration-200"
              title={isMinimized ? "Expand" : "Minimize"}
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                {isMinimized ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                )}
              </svg>
            </button>
          </div>
        </div>

        {/* Messages */}
        {!isMinimized && (
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {messages.length === 0 && (
              <div className="text-center py-6 animate-fade-in">
                <div className="w-12 h-12 bg-gradient-to-r from-blue-600 to-blue-700 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-white text-lg">AI</span>
                </div>
                <h3 className="text-base font-semibold text-gray-900 mb-2">AI Assistant</h3>
                <p className="text-gray-600 mb-4 text-sm">I'm here to help you manage your assets.</p>
                
                {/* Quick Actions */}
                <div className="space-y-2">
                  {quickActions.map((action, index) => (
                    <button
                      key={index}
                      onClick={() => handleQuickAction(action.prompt)}
                      className="w-full p-2.5 text-left bg-gray-50 hover:bg-blue-50 rounded-lg border border-gray-200 hover:border-blue-300 transition-all duration-200 group"
                    >
                      <div className="flex items-center space-x-2">
                        <span className="text-sm group-hover:scale-110 transition-transform duration-200">{action.icon}</span>
                        <span className="text-xs font-medium text-gray-900">{action.text}</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`}
              >
                <div
                  className={`max-w-xs px-3 py-2 rounded-lg text-sm ${
                    message.sender === 'user'
                      ? 'bg-blue-600 text-white'
                      : message.sender === 'system'
                      ? 'bg-gray-100 text-gray-700 border border-gray-200'
                      : 'bg-gray-50 text-gray-900 border border-gray-200'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{message.text}</p>
                  <p className="text-xs opacity-70 mt-1">
                    {message.timestamp.toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))}

            {isTyping && (
              <div className="flex justify-start animate-fade-in">
                <div className="bg-gray-50 border border-gray-200 rounded-lg px-3 py-2">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}

        {/* Input */}
        {!isMinimized && (
          <div className="p-4 border-t border-gray-200 bg-white rounded-b-xl">
            <div className="flex space-x-2">
              <div className="flex-1 relative">
                <textarea
                  ref={inputRef}
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Type a message..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none text-sm"
                  rows={1}
                  style={{ minHeight: '36px', maxHeight: '100px' }}
                  disabled={isTyping}
                />
              </div>
              <button
                onClick={handleSendMessage}
                disabled={!inputMessage.trim() || isTyping}
                className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </button>
            </div>
            
            {/* Connection Status */}
            {isTyping && (
              <div className="mt-2 text-xs text-gray-500 flex items-center space-x-1">
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
                <span>AI is thinking...</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default AssetManagerChatbot;