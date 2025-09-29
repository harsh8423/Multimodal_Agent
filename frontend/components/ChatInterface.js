import React, { useState, useEffect, useRef } from 'react';
import { 
  Send, 
  AlertCircle,
  CheckCircle,
  X,
  Loader2,
  Sparkles,
  Plus,
  MessageSquare,
  Trash2,
  User,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  ChevronDown,
  Settings,
  BarChart3
} from 'lucide-react';
import Message from '@/components/Message';
import ChatInput from '@/components/ChatInput';
// LogPanel removed; logs are not persisted or displayed
import GoogleSignIn from '@/components/GoogleSignIn';
import { cn, formatTime } from '@/lib/utils';
import ChatHistory from '@/components/ChatHistory';
import AssetDragDrop from '@/components/AssetDragDrop';
import { MultimodalAgentClient } from '@/lib/websocket-client';
import { authService } from '@/lib/auth';
import { uploadToCloudinary } from '@/lib/cloudinary';
import { useRouter } from 'next/navigation';

const ChatInterface = ({ user: userProp }) => {
  const [messages, setMessages] = useState([]);
  // Logs removed; use nanoStream only
  const [inputMessage, setInputMessage] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectionError, setConnectionError] = useState(null);
  const [selectedMedia, setSelectedMedia] = useState(null); // { type: 'image'|'video', file, preview, name, size }
  const [isTyping, setIsTyping] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [chatId, setChatId] = useState(null);
  const [isSending, setIsSending] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [chats, setChats] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [nanoStream, setNanoStream] = useState([]); // rolling tiny status lines
  const [nanoExpanded, setNanoExpanded] = useState(false);
  const [showAssetManager, setShowAssetManager] = useState(false);
  const [attachedAssets, setAttachedAssets] = useState([]);
  const [browseAssetMode, setBrowseAssetMode] = useState(false);
  const router = useRouter();

  const clientRef = useRef(null);
  const API_BASE_URL = typeof window !== 'undefined' ? (process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000') : '';
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const imageInputRef = useRef(null);
  const videoInputRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    const token = authService.token;
    const wsClient = new MultimodalAgentClient(typeof window !== 'undefined' ? (process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws') : '');
    clientRef.current = wsClient;

    const loadChatHistory = async () => {
      if (!authService.token) return;
      try {
        const res = await fetch(`${API_BASE_URL}/chats/history?token=${authService.token}`);
        if (res.ok) {
          const data = await res.json();
          setChats(Array.isArray(data) ? data : []);
        }
      } catch (e) {
        // ignore
      }
    };

    const loadChatMessages = async (chatIdToLoad) => {
      if (!authService.token || !chatIdToLoad) return;
      try {
        const res = await fetch(`${API_BASE_URL}/chats/${chatIdToLoad}/messages?token=${authService.token}`);
        if (res.ok) {
          const data = await res.json();
          const mapped = data.map((m, idx) => ({
            id: Date.now() + idx,
            content: m.content,
            role: m.role,
            agent: m.agent,
            timestamp: m.timestamp,
            isStreaming: false,
            mediaUrl: m.metadata?.media_url || null,
            mediaType: m.metadata?.media_type || null
          }));
          setMessages(mapped);
        }
      } catch (e) {
        // ignore
      }
    };

    const connect = async () => {
      setIsConnecting(true);
      setConnectionError(null);
      try {
        await wsClient.connect(token);
      } catch (err) {
        setConnectionError(err?.message || 'Failed to connect');
        setIsConnecting(false);
        setIsConnected(false);
        return;
      }

      wsClient.on('auth_success', async (data) => {
        setIsConnecting(false);
        setIsConnected(true);
        setSessionId(data.session_id);
        setChatId(data.chat_id || null);
        await loadChatHistory();
        if (data.chat_id) {
          await loadChatMessages(data.chat_id);
        }
      });

      wsClient.on('disconnected', () => {
        setIsConnected(false);
        setSessionId(null);
      });

      wsClient.on('auth_error', (data) => {
        setConnectionError(data?.message || 'Authentication error');
        setIsConnecting(false);
        setIsConnected(false);
      });

      wsClient.on('chat_message', (data) => {
        if (!data || typeof data.text !== 'string') return;
        const agent = data.agent_required ? (data.agent_name || 'assistant') : 'orchestrator';
        const msg = {
          id: Date.now() + Math.random(),
          content: data.text,
          role: 'assistant',
          agent,
          timestamp: new Date().toISOString(),
          isStreaming: false,
          mediaUrl: null, // Assistant messages don't have media
          mediaType: null
        };
        setMessages(prev => [...prev, msg]);
        setIsTyping(false);
        setIsSending(false);
      });

      wsClient.on('chat_created', async (data) => {
        setChatId(data.chat_id);
        setChats(prev => [{ chat_id: data.chat_id, title: 'New Chat', last_active: new Date().toISOString(), message_count: 0 }, ...prev.filter(c => c.chat_id !== data.chat_id)]);
        setNanoStream([]);
        setNanoExpanded(false);
        await loadChatMessages(data.chat_id);
      });

      wsClient.on('chat_switched', async (data) => {
        setChatId(data.chat_id);
        
        // Load chat details to get the proper title
        try {
          const res = await fetch(`${API_BASE_URL}/chats/${data.chat_id}/details?token=${authService.token}`);
          if (res.ok) {
            const chatDetails = await res.json();
            setChats(prev => [{ 
              chat_id: data.chat_id, 
              title: chatDetails.title || 'Untitled Chat', 
              last_active: chatDetails.last_active || new Date().toISOString(), 
              message_count: chatDetails.message_count || 0 
            }, ...prev.filter(c => c.chat_id !== data.chat_id)]);
          } else {
            // Fallback if details fetch fails
            setChats(prev => [{ chat_id: data.chat_id, title: 'Untitled Chat', last_active: new Date().toISOString(), message_count: 0 }, ...prev.filter(c => c.chat_id !== data.chat_id)]);
          }
        } catch (error) {
          console.error('Failed to load chat details:', error);
          // Fallback if details fetch fails
          setChats(prev => [{ chat_id: data.chat_id, title: 'Untitled Chat', last_active: new Date().toISOString(), message_count: 0 }, ...prev.filter(c => c.chat_id !== data.chat_id)]);
        }
        
        setNanoStream([]);
        setNanoExpanded(false);
        await loadChatMessages(data.chat_id);
      });

      wsClient.on('title_updated', (data) => {
        console.log('Received title update:', data);
        setChats(prev => prev.map(chat => 
          chat.chat_id === data.chat_id 
            ? { ...chat, title: data.title }
            : chat
        ));
      });

      // 'log' event removed; we only handle nano_message now
      wsClient.on('nano_message', (nm) => {
        setNanoStream(prev => {
          const next = [...prev, { id: Date.now() + Math.random(), agent: nm.agent, text: nm.message, ts: nm.timestamp || new Date().toISOString() }];
          // keep only last 12 nano lines
          return next.slice(-12);
        });
      });

      setTimeout(() => {
        if (!clientRef.current?.getCurrentChatId()) {
          try { wsClient.createNewChat('New chat'); } catch {}
        }
      }, 50);
    };

    connect();

    return () => {
      try { wsClient.disconnect(); } catch {}
    };
  }, []);

  const handleAssetDrop = (assetData) => {
    setAttachedAssets(prev => [...prev, assetData]);
  };

  const handleRemoveAsset = (index) => {
    setAttachedAssets(prev => prev.filter((_, i) => i !== index));
  };

  const handleSendMessage = async (text) => {
    const message = (typeof text === 'string' ? text : inputMessage).trim();
    if (!message || message.length === 0 || !isConnected || isSending) {
      return;
    }

    setIsSending(true);
    setInputMessage('');

    // If media selected, upload to Cloudinary first (unsigned)
    let metadata = null;
    let mediaUrl = null;
    let mediaType = null;
    
    if (selectedMedia && selectedMedia.file) {
      const uploadAgent = selectedMedia.type === 'video' ? 'client-video' : 'client-image';
      setNanoStream(prev => [...prev, { id: Date.now() + Math.random(), agent: uploadAgent, text: 'Uploading media…', ts: new Date().toISOString() }].slice(-12));
      try {
        const result = await uploadToCloudinary(selectedMedia.file, { resourceType: selectedMedia.type });
        metadata = {
          media_url: result.secure_url || result.url,
          media_type: selectedMedia.type,
          public_id: result.public_id,
          resource_type: result.resource_type,
          bytes: result.bytes,
          width: result.width,
          height: result.height,
          duration: result.duration
        };
        mediaUrl = result.secure_url || result.url;
        mediaType = selectedMedia.type;
        setNanoStream(prev => [...prev, { id: Date.now() + Math.random(), agent: uploadAgent, text: 'Upload complete', ts: new Date().toISOString() }].slice(-12));
      } catch (err) {
        setNanoStream(prev => [...prev, { id: Date.now() + Math.random(), agent: uploadAgent, text: `Upload failed: ${err.message || err}`, ts: new Date().toISOString() }].slice(-12));
      }
    }

    // Prepare asset data for the message
    let assetMetadata = null;
    if (attachedAssets.length > 0) {
      assetMetadata = {
        assets: attachedAssets.map(asset => ({
          type: asset.type,
          id: asset.asset.id,
          name: asset.type === 'brands' ? asset.asset.name : 
                asset.type === 'competitors' ? `${asset.asset.username} - ${asset.asset.platform}` :
                asset.asset.title || asset.asset.name,
          data: asset.asset
        }))
      };
    }

    const newMessage = {
      id: Date.now(),
      content: message,
      role: 'user',
      timestamp: new Date().toISOString(),
      isStreaming: false,
      mediaUrl,
      mediaType,
      attachedAssets: attachedAssets.length > 0 ? attachedAssets : null
    };
    setMessages(prev => [...prev, newMessage]);
    setIsTyping(true);

    try {
      // Combine metadata with asset data
      const combinedMetadata = {
        ...metadata,
        ...assetMetadata
      };
      clientRef.current?.sendMessage(message, null, chatId, combinedMetadata);
    } catch (err) {
      setConnectionError(err?.message || 'Failed to send message');
      setIsTyping(false);
      setIsSending(false);
      return;
    }
    // Clear selected media and assets after sending
    if (selectedMedia) {
      setSelectedMedia(null);
      if (imageInputRef.current) imageInputRef.current.value = '';
      if (videoInputRef.current) videoInputRef.current.value = '';
    }
    setAttachedAssets([]);
  };

  // handled inside ChatInput
  const handleKeyPress = () => {};

  const handleCreateChat = async () => {
    try {
      // Prefer REST creation to ensure new chat even when one is active
      if (!authService.token) throw new Error('Not authenticated');
      const res = await fetch(`${API_BASE_URL}/chats/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: authService.token, title: 'New Chat' })
      });
      if (!res.ok) throw new Error('Failed to create chat');
      const data = await res.json();
      const newId = data.chat_id;
      if (newId) {
        setChats(prev => [{ chat_id: newId, title: data.title || 'New Chat', last_active: new Date().toISOString(), message_count: 0 }, ...prev]);
        setChatId(newId);
        try { clientRef.current?.switchToChat(newId); } catch {}
      }
    } catch (e) {
      setConnectionError(e?.message || 'Failed to create chat');
    }
  };

  const handleSelectChat = async (chat) => {
    try {
      clientRef.current?.switchToChat(chat.chat_id);
    } catch (e) {
      setConnectionError(e?.message || 'Failed to switch chat');
    }
  };

  const handleDeleteChat = async (chatIdToDelete) => {
    if (!window.confirm('Are you sure you want to delete this chat?')) {
      return;
    }
    setChats(prev => prev.filter(chat => chat.chat_id !== chatIdToDelete));
    if (chatIdToDelete === chatId) {
      const remainingChats = chats.filter(chat => chat.chat_id !== chatIdToDelete);
      if (remainingChats.length > 0) handleSelectChat(remainingChats[0]);
      else handleCreateChat();
    }
  };

  const handleImageInputChange = (e) => {
    const file = e.target.files && e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      setSelectedMedia({
        type: 'image',
        file,
        preview: event.target.result,
        name: file.name,
        size: file.size
      });
    };
    reader.readAsDataURL(file);
  };

  const handleVideoInputChange = (e) => {
    const file = e.target.files && e.target.files[0];
    if (!file) return;
    const objectUrl = URL.createObjectURL(file);
    setSelectedMedia({
      type: 'video',
      file,
      preview: objectUrl,
      name: file.name,
      size: file.size
    });
  };

  const handleRemoveMedia = () => {
    if (selectedMedia && selectedMedia.type === 'video' && selectedMedia.preview) {
      try { URL.revokeObjectURL(selectedMedia.preview); } catch {}
    }
    setSelectedMedia(null);
    if (imageInputRef.current) imageInputRef.current.value = '';
    if (videoInputRef.current) videoInputRef.current.value = '';
  };

  // Logs removed

  const user = userProp || authService.user || { name: 'User', email: '' };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Left Sidebar */}
      <div className={cn(
        "bg-white text-gray-900 flex flex-col transition-all duration-300 border-r border-gray-200",
        sidebarCollapsed ? "w-16" : "w-80"
      )}>
        {/* Sidebar Header - User Section */}
        <div className="p-3 border-b border-gray-200">
          <div className="flex items-center justify-between">
            {!sidebarCollapsed && (
              <div className="flex items-center gap-3">
                {!authService.isAuthenticated() ? (
                  <div className="w-full">
                    <GoogleSignIn onSignIn={(ud, token) => {
                      try {
                        authService.saveToStorage(ud, token);
                        try { clientRef.current?.disconnect(); } catch {}
                        setTimeout(() => {
                          window.location.reload();
                        }, 100);
                      } catch {}
                    }} />
                  </div>
                ) : (
                  <>
                    <div className="w-8 h-8 bg-gray-700 rounded-full flex items-center justify-center text-white">
                      <User className="w-4 h-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-gray-900 truncate">
                        {user.name}
                      </div>
                      <div className="text-xs text-gray-500 truncate">
                        {user.email}
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => {
                          // TODO: Add settings functionality
                          console.log('Settings clicked');
                        }}
                        className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                        title="Settings"
                      >
                        <Settings className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => {
                          authService.logout?.();
                          try { clientRef.current?.disconnect(); } catch {}
                          window.location.reload();
                        }}
                        className="p-2 hover:bg-red-100 rounded-lg transition-colors"
                        title="Sign out"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  </>
                )}
              </div>
            )}
            <button
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              {sidebarCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
            </button>
          </div>
          {!sidebarCollapsed && (
            <div className="mt-3 space-y-3">
              {/* New Chat Button */}
              <button
                onClick={handleCreateChat}
                className="w-full p-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg flex items-center gap-3 transition-colors"
              >
                <Plus className="w-4 h-4" />
                <span>New Chat</span>
              </button>
              
              {/* Go To Assets Button */}
              <button
                onClick={() => router.push('/asset-manager')}
                className="w-full p-3 bg-gray-100 hover:bg-gray-200 text-gray-900 rounded-lg flex items-center gap-3 transition-colors"
              >
                <BarChart3 className="w-4 h-4" />
                <span>Go To Assets</span>
              </button>
              
              {/* Browse Asset Toggle */}
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">Browse Asset</span>
                <button
                  onClick={() => setBrowseAssetMode(!browseAssetMode)}
                  className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                    browseAssetMode ? 'bg-blue-600' : 'bg-gray-300'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      browseAssetMode ? 'translate-x-4' : 'translate-x-0.5'
                    }`}
                  />
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Content Area - Chat History or Asset Manager */}
        <div className="flex-1 overflow-y-auto">
          {!sidebarCollapsed && (
            browseAssetMode ? (
              <AssetDragDrop
                isOpen={true}
                onClose={() => setBrowseAssetMode(false)}
                onAssetDrop={handleAssetDrop}
                embedded={true}
              />
            ) : (
              <ChatHistory
                token={authService.token}
                selectedChatId={chatId}
                onSelectChat={handleSelectChat}
                onCreateChat={handleCreateChat}
                onChatsChange={setChats}
              />
            )
          )}
        </div>

      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Chat Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between max-w-4xl mx-auto">
            <div className="flex items-center gap-3">
              <h2 className="text-lg font-semibold text-gray-900">
                {chats.find(c => c.chat_id === chatId)?.title || 'Chat'}
              </h2>
              {sessionId && (
                <span className="text-xs bg-gray-200 text-gray-800 px-2 py-1 rounded-full">
                  Connected
                </span>
              )}
            </div>
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <CheckCircle className="w-4 h-4 text-gray-700" />
                <span>{isConnected ? 'Online' : (isConnecting ? 'Connecting...' : 'Offline')}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto bg-gray-50">
          {connectionError && (
            <div className="max-w-4xl mx-auto px-6 py-4">
              <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                <AlertCircle className="w-5 h-5 flex-shrink-0" />
                <span className="text-sm">{connectionError}</span>
                <button
                  onClick={() => setConnectionError(null)}
                  className="ml-auto p-1 hover:bg-red-100 rounded"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {messages.length === 0 && !connectionError && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center max-w-2xl px-6">
                <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-500 rounded-2xl flex items-center justify-center mx-auto mb-6">
                  <Sparkles className="w-8 h-8 text-white" />
                </div>
                <h2 className="text-3xl font-bold text-gray-900 mb-4">
                  How can I help you today?
                </h2>
                <p className="text-gray-600 mb-8">
                  Ask me anything or start a conversation
                </p>
              </div>
            </div>
          )}

          <div className="pb-24">
            {messages.map((message) => (
              <Message
                key={message.id}
                message={message.content}
                isUser={message.role === 'user'}
                agent={message.agent}
                timestamp={null}
                isStreaming={false}
                mediaUrl={message.mediaUrl}
                mediaType={message.mediaType}
              />
            ))}

            {isTyping && (
              <div className="flex gap-4 max-w-4xl mx-auto px-6 py-4">
                <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center text-white text-sm font-medium flex-shrink-0">
                  AI
                </div>
                <div className="bg-white border border-gray-200 rounded-2xl p-4">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Media Preview */}
        {selectedMedia && (
          <div className="bg-white border-t border-gray-200 px-6 py-3">
            <div className="max-w-4xl mx-auto">
              <div className="flex items-center gap-3 p-3 bg-gray-50 border border-gray-200 rounded-lg">
                {selectedMedia.type === 'image' ? (
                  <img
                    src={selectedMedia.preview}
                    alt="Preview"
                    className="w-10 h-10 object-cover rounded"
                  />
                ) : (
                  <video
                    src={selectedMedia.preview}
                    className="w-16 h-10 rounded object-cover"
                    controls
                  />
                )}
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">{selectedMedia.name}</p>
                  <p className="text-xs text-gray-500">
                    {(selectedMedia.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
                <button
                  onClick={handleRemoveMedia}
                  className="p-1 text-gray-400 hover:text-red-500 rounded transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Revamped Input Area - centered within chat area only */}
        <div className="bg-transparent px-6 py-0">
          <div className="max-w-4xl mx-auto">
            <ChatInput
              onSendMessage={handleSendMessage}
              onFileAttach={(type) => {
                if (type === 'image') {
                  imageInputRef.current?.click();
                } else if (type === 'video') {
                  videoInputRef.current?.click();
                }
              }}
              onVoiceRecord={(active) => {
                // placeholder for voice recording integration
                console.log('Voice recording', active ? 'started' : 'stopped');
              }}
              onImagePaste={(file) => {
                if (!file) return;
                const reader = new FileReader();
                reader.onload = (event) => {
                  setSelectedMedia({
                    type: 'image',
                    file,
                    preview: event.target.result,
                    name: file.name,
                    size: file.size
                  });
                };
                reader.readAsDataURL(file);
              }}
              onAssetDrop={handleAssetDrop}
              attachedAssets={attachedAssets}
              onRemoveAsset={handleRemoveAsset}
              placeholder="Message the agent..."
              disabled={!isConnected || isSending}
              isStreaming={isTyping || isSending}
              onStopStreaming={() => {
                setIsTyping(false);
                setIsSending(false);
              }}
              maxRows={4}
              nanoStream={nanoStream}
              nanoExpanded={nanoExpanded}
              onNanoToggle={() => setNanoExpanded(v => !v)}
            />
          </div>
        </div>
        <input
          ref={imageInputRef}
          type="file"
          accept="image/*"
          onChange={handleImageInputChange}
          className="hidden"
        />
        <input
          ref={videoInputRef}
          type="file"
          accept="video/*"
          onChange={handleVideoInputChange}
          className="hidden"
        />
      </div>

    </div>
  );
};

export default ChatInterface;