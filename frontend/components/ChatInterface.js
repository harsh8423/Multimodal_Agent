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
  BarChart3,
  ListTodo,
  Mic,
  StopCircle,
  Zap,
  Play,
  Circle,
  XCircle,
  Image,
  FileText,
  Video,
  Paperclip,
  Building2,
  Users
} from 'lucide-react';
import Message from '@/components/Message';
import ChatInput from '@/components/ChatInput';
// LogPanel removed; logs are not persisted or displayed
import GoogleSignIn from '@/components/GoogleSignIn';
import { cn, formatTime } from '@/lib/utils';
import ChatHistory from '@/components/ChatHistory';
import AssetDragDrop from '@/components/AssetDragDrop';
import TodoList from '@/components/TodoList';
import { MultimodalAgentClient } from '@/lib/websocket-client';
import { authService } from '@/lib/auth';
import { uploadToCloudinary } from '@/lib/cloudinary';
import { todoAPI } from '@/lib/api/todos';
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
  const [sidebarWidth, setSidebarWidth] = useState(320); // Default width in pixels
  const [isResizing, setIsResizing] = useState(false);
  const [showTodos, setShowTodos] = useState(false);
  const [todos, setTodos] = useState([]);
  const [todosLoading, setTodosLoading] = useState(false);
  const [activeTodo, setActiveTodo] = useState(null);
  const [todoExpanded, setTodoExpanded] = useState(false);
  const [showAttachments, setShowAttachments] = useState(false);
  const router = useRouter();

  const clientRef = useRef(null);
  const API_BASE_URL = typeof window !== 'undefined' ? (process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000') : '';
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const textareaRef = useRef(null);
  const imageInputRef = useRef(null);
  const videoInputRef = useRef(null);
  const sidebarRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-resize textarea functionality
  const autoResizeTextarea = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      const scrollHeight = textareaRef.current.scrollHeight;
      const maxHeight = 150; // 100px max height
      textareaRef.current.style.height = `${Math.min(scrollHeight, maxHeight)}px`;
    }
  };

  // Handle textarea input changes
  const handleTextareaChange = (e) => {
    autoResizeTextarea();
  };

  // Handle keydown events for Enter/Shift+Enter
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      const message = e.target.value?.trim();
      if (message && isConnected && !isSending && handleSendMessage) {
        handleSendMessage(message);
        e.target.value = '';
        autoResizeTextarea(); // Reset height after sending
      }
    }
  };

  // Load todos when chat changes
  useEffect(() => {
    if (chatId && authService.token) {
      loadTodos();
    }
  }, [chatId]);

  // Set up periodic refresh for todos to keep them updated
  useEffect(() => {
    if (!chatId || !authService.token) return;

    const interval = setInterval(() => {
      loadTodos();
    }, 3000); // Refresh every 3 seconds

    return () => clearInterval(interval);
  }, [chatId, authService.token]);

  const loadTodos = async () => {
    if (!chatId || !authService.token) return;
    
    // Prevent concurrent calls
    if (todosLoading) return;
    
    setTodosLoading(true);
    try {
      const todosData = await todoAPI.getChatTodos(chatId, authService.token);
      setTodos(todosData);
      
      // Find the most recent active todo
      const activeTodos = todosData.filter(todo => 
        todo.status === 'active' && 
        todo.tasks.some(task => task.status !== 'done' && task.status !== 'completed')
      );
      
      if (activeTodos.length > 0) {
        // Sort by updated_at to get the most recent
        const mostRecentTodo = activeTodos.sort((a, b) => 
          new Date(b.updated_at) - new Date(a.updated_at)
        )[0];
        setActiveTodo(mostRecentTodo);
      } else {
        setActiveTodo(null);
      }
    } catch (error) {
      console.error('Failed to load todos:', error);
      setTodos([]);
      setActiveTodo(null);
    } finally {
      setTodosLoading(false);
    }
  };

  const refreshTodos = () => {
    loadTodos();
  };

  const attachmentOptions = [
    { icon: Image, label: 'Image', action: () => {
      if (imageInputRef.current) {
        imageInputRef.current.click();
      }
      setShowAttachments(false);
    }},
    { icon: Video, label: 'Video', action: () => {
      if (videoInputRef.current) {
        videoInputRef.current.click();
      }
      setShowAttachments(false);
    }},
    { icon: FileText, label: 'Document', action: () => {
      // TODO: Implement document upload
      console.log('Document upload not implemented yet');
      setShowAttachments(false);
    }},
    { icon: Paperclip, label: 'File', action: () => {
      // TODO: Implement file upload
      console.log('File upload not implemented yet');
      setShowAttachments(false);
    }},
  ];

  useEffect(() => {
    // Prevent multiple WebSocket connections
    if (clientRef.current) {
      console.log('WebSocket client already exists, skipping creation');
      return;
    }
    
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
            mediaType: m.metadata?.media_type || null,
            metadata: m.metadata || null
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
        const agent = data.agent_required ? (data.agent_name || 'assistant') : 'social_media_manager';
        const msg = {
          id: Date.now() + Math.random(),
          content: data.text,
          role: 'assistant',
          agent,
          timestamp: new Date().toISOString(),
          isStreaming: false,
          mediaUrl: null, // Assistant messages don't have media
          mediaType: null,
          metadata: data.metadata || null
        };
        setMessages(prev => [...prev, msg]);
        setIsTyping(false);
        setIsSending(false);
        
        // Handle todo creation
        if (data.metadata && data.metadata.message_type === 'todo_created') {
          const todoData = data.metadata.todo_data;
          if (todoData) {
            setActiveTodo(todoData);
            // Refresh todos to get updated list
            refreshTodos();
          }
        }
      });


      // Handle agent notifications
      wsClient.on('agent_notification', (data) => {
        console.log('Agent notification received:', data);
        const msg = {
          id: Date.now() + Math.random(),
          content: data.message,
          role: 'assistant',
          agent: data.agent_name || 'social_media_manager',
          timestamp: new Date().toISOString(),
          isStreaming: false,
          mediaUrl: null,
          mediaType: null,
          isNotification: true,
          notificationType: data.notification_type || 'info'
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
        setActiveTodo(null); // Clear active todo for new chat
        setTodoExpanded(false);
        await loadChatMessages(data.chat_id);
        // Note: loadTodos() will be called automatically by useEffect when chatId changes
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
        setTodoExpanded(false);
        await loadChatMessages(data.chat_id);
        // Note: loadTodos() will be called automatically by useEffect when chatId changes
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
      try { 
        if (clientRef.current) {
          clientRef.current.disconnect(); 
          clientRef.current = null;
        }
      } catch {}
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

    // Create chat if none exists
    if (!chatId) {
      await handleCreateChat();
      // Wait a bit for chat creation to complete
      await new Promise(resolve => setTimeout(resolve, 100));
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

  // Sidebar resize handlers
  const handleMouseDown = (e) => {
    e.preventDefault();
    setIsResizing(true);
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  const handleMouseMove = (e) => {
    const newWidth = e.clientX;
    const minWidth = 250;
    const maxWidth = 600;
    console.log('Resizing sidebar to:', newWidth); // Debug log
    if (newWidth >= minWidth && newWidth <= maxWidth) {
      setSidebarWidth(newWidth);
    }
  };

  const handleMouseUp = () => {
    setIsResizing(false);
    document.removeEventListener('mousemove', handleMouseMove);
    document.removeEventListener('mouseup', handleMouseUp);
  };


  // Cleanup resize listeners on unmount
  useEffect(() => {
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, []);

  // Logs removed

  const user = userProp || authService.user || { name: 'User', email: '' };

  return (
    <div className={cn("flex h-screen bg-gray-50", isResizing && "select-none")}>
      {/* Left Sidebar */}
      <div 
        ref={sidebarRef}
        className={cn(
          "bg-white text-gray-900 flex flex-col transition-all duration-300 border-r border-gray-200 relative",
          sidebarCollapsed ? "w-16" : ""
        )}
        style={!sidebarCollapsed ? { width: `${sidebarWidth}px` } : {}}
      >
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
                className="w-full p-3 hover:bg-gray-100 text-gray-900 rounded-lg flex items-center gap-3 transition-colors"
              >
                <Plus className="w-4 h-4" />
                <span className="text-sm font-medium">New Chat</span>
              </button>
              
              {/* Go To Assets Button */}
              <button
                onClick={() => router.push('/asset-manager')}
                className="w-full p-3 hover:bg-gray-100 text-gray-900 rounded-lg flex items-center gap-3 transition-colors"
              >
                <BarChart3 className="w-4 h-4" />
                <span className="text-sm font-medium">Go To Assets</span>
              </button>
              
              {/* Todo Lists Button */}
              <button
                onClick={() => setShowTodos(!showTodos)}
                className={cn(
                  "w-full p-3 hover:bg-gray-100 text-gray-900 rounded-lg flex items-center gap-3 transition-colors",
                  showTodos && "bg-blue-50 text-blue-700"
                )}
              >
                <ListTodo className="w-4 h-4" />
                <span className="text-sm font-medium">Todo Lists</span>
                {todos.length > 0 && (
                  <span className="ml-auto text-xs bg-blue-100 text-blue-600 px-2 py-1 rounded-full">
                    {todos.length}
                  </span>
                )}
              </button>
              
              {/* Browse Asset Toggle */}
              <div className="flex items-center justify-between p-3 hover:bg-gray-100 rounded-lg transition-colors">
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

        {/* Content Area - Chat History, Asset Manager, or Todo Lists */}
        <div className="flex-1 overflow-y-auto">
          {!sidebarCollapsed && (
            showTodos ? (
              <div className="p-4">
                <TodoList
                  chatId={chatId}
                  todos={todos}
                  onRefresh={refreshTodos}
                />
              </div>
            ) : browseAssetMode ? (
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

        {/* Resize Handle */}
        {!sidebarCollapsed && (
          <div
            className={cn(
              "absolute top-0 right-0 w-1 h-full cursor-col-resize bg-transparent hover:bg-blue-400 transition-colors z-10 group",
              isResizing && "bg-blue-500"
            )}
            onMouseDown={handleMouseDown}
          >
            {/* Visual indicator */}
            <div className="absolute top-1/2 -translate-y-1/2 -right-1 w-3 h-8 bg-gray-300 hover:bg-blue-400 rounded-r-sm opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
              <div className="w-0.5 h-4 bg-white rounded-full" />
            </div>
          </div>
        )}

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

          <div className="pb-24 mb-16">
            {messages.map((message, index) => (
              <Message
                key={message.id}
                message={message.content}
                isUser={message.role === 'user'}
                agent={message.agent}
                timestamp={null}
                mediaUrl={message.mediaUrl}
                mediaType={message.mediaType}
                isNotification={message.isNotification}
                notificationType={message.notificationType}
                metadata={message.metadata}
                // Show overlay only on the last message
                showChatInputOverlay={index === messages.length - 1}
                activeTodo={activeTodo}
                todoExpanded={todoExpanded}
                onTodoToggle={() => setTodoExpanded(v => !v)}
                nanoStream={nanoStream}
                nanoExpanded={nanoExpanded}
                onNanoToggle={() => setNanoExpanded(v => !v)}
                // Input box props
                onSendMessage={handleSendMessage}
                placeholder="Message the agent..."
                disabled={!isConnected || isSending}
                // isStreaming={message.role !== 'user' && (isTyping || isSending)}
                onStopStreaming={() => {
                  setIsTyping(false);
                  setIsSending(false);
                }}
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

        {/* ChatInput Overlay - Fixed at bottom, centered within chat area */}
        {authService.isAuthenticated() && (
          <div className="fixed bottom-0 z-50 bg-transparent" style={{
            left: sidebarCollapsed ? '64px' : `${sidebarWidth}px`,
            right: '0',
            width: `calc(100vw - ${sidebarCollapsed ? '64px' : `${sidebarWidth}px`})`
          }}>
          <div className="max-w-4xl mx-auto px-6 pb-4">
            {/* Attachment Options */}
            {showAttachments && (
              <div className="mb-3 flex justify-center">
                <div className="bg-white/90 backdrop-blur-md border border-gray-200/80 rounded-2xl shadow-xl p-3">
                  <div className="flex items-center gap-2">
                    {attachmentOptions.map((option, index) => (
                      <button
                        key={index}
                        onClick={option.action}
                        className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-100/80 rounded-xl transition-all duration-200"
                      >
                        <option.icon className="w-4 h-4" />
                        {option.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Todo Display - integrated with input */}
            {activeTodo && (
                <div className="relative flex justify-center">
                  {/* Todo Header Bar */}
                  <div className={cn(
                    "flex items-center px-3 py-2 text-[11px] font-mono text-gray-600 bg-white/90 backdrop-blur-md border border-gray-200/60 border-b-0 w-[80%]",
                    nanoStream.length > 0 ? "rounded-t-3xl" : "rounded-t-3xl"
                  )}>
                    <button
                      type="button"
                      className="mr-2 p-0.5 text-gray-500 hover:text-gray-700"
                      onClick={() => setTodoExpanded(v => !v)}
                      title={todoExpanded ? 'Hide details' : 'Show details'}
                    >
                      {todoExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronUp className="w-3 h-3" />}
                    </button>
                    
                    <div className="flex items-center gap-2 min-w-0 flex-1">
                      <span className="text-gray-800 font-semibold">
                        {activeTodo.tasks.filter(task => task.status === 'done' || task.status === 'completed').length} of {activeTodo.tasks.length} To-dos
                      </span>
                      {activeTodo.tasks.find(task => task.status === 'in-progress') && (
                        <span className="truncate text-gray-500">
                          {activeTodo.tasks.find(task => task.status === 'in-progress').title}
                        </span>
                      )}
                    </div>
                    
                    {/* Progress indicator */}
                    <div className="flex items-center gap-1 ml-2">
                      <div className="w-8 h-1 bg-gray-200 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-gradient-to-r from-blue-500 to-purple-600 transition-all duration-300"
                          style={{ 
                            width: `${activeTodo.tasks.length > 0 ? (activeTodo.tasks.filter(task => task.status === 'done' || task.status === 'completed').length / activeTodo.tasks.length) * 100 : 0}%` 
                          }}
                        />
                      </div>
                    </div>
                  </div>

                  {/* Expanded Todo List */}
                  {todoExpanded && (
                    <div className="absolute bottom-full mb-1 left-1/2 transform -translate-x-1/2 w-[80%] rounded-t-md border border-gray-200 bg-white shadow-lg overflow-hidden">
                      <div className="max-h-60 overflow-y-auto py-1">
                        {/* Todo Title */}
                        <div className="px-3 py-2 border-b border-gray-100">
                          <h3 className="text-sm font-semibold text-gray-900">{activeTodo.title}</h3>
                        </div>
                        
                        {/* Tasks List */}
                        {activeTodo.tasks.map((task) => {
                          const isActive = task.status === 'in-progress';
                          
                          const getStatusIcon = (status, isActive = false) => {
                            if (isActive) {
                              return <div className="w-3 h-3 rounded-full bg-blue-500 flex items-center justify-center">
                                <Play className="w-2 h-2 text-white" />
                              </div>;
                            }
                            
                            switch (status) {
                              case 'done':
                              case 'completed':
                                return <div className="w-3 h-3 rounded-full bg-green-500 flex items-center justify-center">
                                  <CheckCircle className="w-2 h-2 text-white" />
                                </div>;
                              case 'in-progress':
                                return <div className="w-3 h-3 rounded-full bg-blue-500 flex items-center justify-center">
                                  <Play className="w-2 h-2 text-white" />
                                </div>;
                              case 'pending':
                                return <Circle className="w-3 h-3 text-gray-400" />;
                              default:
                                return <XCircle className="w-3 h-3 text-red-500" />;
                            }
                          };

                          const getStatusColor = (status) => {
                            switch (status) {
                              case 'done':
                              case 'completed':
                                return 'text-gray-500 line-through';
                              case 'in-progress':
                                return 'text-blue-600';
                              case 'pending':
                                return 'text-gray-500';
                              default:
                                return 'text-red-600';
                            }
                          };
                          
                          return (
                            <div key={task.step_num} className="px-3 py-1.5 text-[11px] font-mono">
                              <div className="flex items-center gap-2">
                                {/* Status Icon */}
                                <div className="flex-shrink-0">
                                  {getStatusIcon(task.status, isActive)}
                                </div>
                                
                                {/* Task Content */}
                                <div className="min-w-0 flex-1">
                                  <div className={cn(
                                    "truncate",
                                    getStatusColor(task.status),
                                    isActive && "font-semibold"
                                  )}>
                                    {task.title}
                                  </div>
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Nano message bar - integrated with input */}
              {nanoStream.length > 0 && (
                <div className="relative">
                  {/* Nano message bar */}
                  <div className="flex items-center px-3 py-2 text-[11px] font-mono text-gray-600 bg-white/90 backdrop-blur-md border border-gray-200/80 rounded-t-3xl border-b-0">
                    <button
                      type="button"
                      className="mr-2 p-0.5 text-gray-500 hover:text-gray-700"
                      onClick={() => setNanoExpanded(v => !v)}
                      title={nanoExpanded ? 'Hide details' : 'Show details'}
                    >
                      {nanoExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronUp className="w-3 h-3" />}
                    </button>
                    <div className="flex items-center gap-2 min-w-0 flex-1">
                      <span className="text-gray-800">{nanoStream[nanoStream.length - 1].agent}</span>
                      <span className="truncate text-gray-500">{nanoStream[nanoStream.length - 1].text}</span>
                    </div>
                  </div>

                  {/* Dropdown list: opens upward */}
                  {nanoExpanded && (
                    <div className="absolute bottom-full mb-1 left-0 right-0 rounded-lg border border-gray-200 bg-white shadow-lg overflow-hidden">
                      <div className="max-h-40 overflow-y-auto py-1">
                        {[...nanoStream].reverse().map(n => (
                          <div key={n.id} className="px-3 py-1.5 text-[11px] font-mono text-gray-700 flex items-center gap-2">
                            <span className="text-gray-800">{n.agent}</span>
                            <span className="truncate text-gray-500">{n.text}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Attached Assets */}
              {attachedAssets.length > 0 && (
                <div className="px-4 pt-3 pb-2">
                  <div className="flex flex-wrap gap-2">
                    {attachedAssets.map((assetData, index) => {
                      const getAssetIcon = (type) => {
                        switch (type) {
                          case 'brands': return Building2;
                          case 'competitors': return Users;
                          case 'templates': return FileText;
                          default: return FileText;
                        }
                      };
                      
                      const getAssetDisplayName = (asset, type) => {
                        switch (type) {
                          case 'brands':
                            return asset.name || 'Unnamed Brand';
                          case 'competitors':
                            const username = asset.username || asset.name || 'Unknown';
                            const platform = asset.platform || 'Unknown Platform';
                            return `${username} - ${platform}`;
                          case 'templates':
                            return asset.title || asset.name || 'Unnamed Template';
                          default:
                            return asset.name || asset.title || 'Unnamed Asset';
                        }
                      };
                      
                      const IconComponent = getAssetIcon(assetData.type);
                      return (
                        <div
                          key={index}
                          className="flex items-center gap-2 px-3 py-1.5 bg-blue-50 border border-blue-200 rounded-lg text-sm"
                        >
                          <IconComponent className="w-4 h-4 text-blue-600" />
                          <span className="text-blue-800 font-medium">
                            {getAssetDisplayName(assetData.asset, assetData.type)}
                          </span>
                          <button
                            onClick={() => handleRemoveAsset(index)}
                            className="p-0.5 hover:bg-blue-100 rounded transition-colors"
                          >
                            <X className="w-3 h-3 text-blue-600" />
                          </button>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Input Box */}
              <div 
                className={cn(
                  "bg-white/90 backdrop-blur-md border border-gray-200/80 shadow-2xl overflow-hidden transition-all duration-300 hover:shadow-3xl hover:border-gray-300/80",
                  nanoStream.length > 0 ? "rounded-b-3xl" : "rounded-3xl"
                )}
                onDragOver={(e) => {
                  e.preventDefault();
                  e.dataTransfer.dropEffect = 'copy';
                }}
                onDrop={(e) => {
                  e.preventDefault();
                  try {
                    const assetData = JSON.parse(e.dataTransfer.getData('application/json'));
                    if (assetData && assetData.type && assetData.asset) {
                      handleAssetDrop(assetData);
                    }
                  } catch (error) {
                    console.error('Failed to parse dropped asset data:', error);
                  }
                }}
              >
                <form onSubmit={(e) => {
                  e.preventDefault();
                  const message = e.target.message?.value?.trim();
                  if (message && isConnected && !isSending && handleSendMessage) {
                    handleSendMessage(message);
                    e.target.message.value = '';
                    autoResizeTextarea(); // Reset height after sending
                  }
                }} className="flex items-center gap-3 p-4">
                  <button
                    type="button"
                    onClick={() => setShowAttachments(!showAttachments)}
                    className={cn(
                      "flex-shrink-0 p-3 rounded-2xl transition-all duration-200 hover:scale-105",
                      showAttachments 
                        ? "bg-indigo-500 text-white shadow-lg shadow-indigo-500/25" 
                        : "bg-gray-100 text-gray-600 hover:bg-gray-200 hover:text-gray-800"
                    )}
                    title="Attach files"
                  >
                    <Plus className={cn("w-5 h-5 transition-transform duration-200", showAttachments && "rotate-45")} />
                  </button>

                  <div className="flex-1 relative">
                    <textarea
                      ref={textareaRef}
                      name="message"
                      placeholder="Message the agent..."
                      disabled={!isConnected || isSending}
                      rows={1}
                      onChange={handleTextareaChange}
                      onKeyDown={handleKeyDown}
                      className="w-full resize-none bg-transparent text-gray-900 placeholder-gray-500 border-none outline-none focus:outline-none focus:ring-0 focus:border-none text-base leading-6 py-3 px-1 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-transparent"
                      style={{ minHeight: '24px', maxHeight: '100px' }}
                    />
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      className="flex-shrink-0 p-3 rounded-2xl transition-all duration-200 hover:scale-105 bg-gray-100 text-gray-600 hover:bg-gray-200 hover:text-gray-800"
                      title="Start voice recording"
                    >
                      <Mic className="w-5 h-5" />
                    </button>

                    {isTyping || isSending ? (
                      <button
                        type="button"
                        onClick={() => {
                setIsTyping(false);
                setIsSending(false);
              }}
                        className="flex-shrink-0 p-3 bg-red-500 text-white rounded-2xl shadow-lg shadow-red-500/25 hover:bg-red-600 transition-all duration-200 hover:scale-105"
                        title="Stop generation"
                      >
                        <StopCircle className="w-5 h-5" />
                      </button>
                    ) : (
                      <button
                        type="submit"
                        disabled={!isConnected || isSending}
                        className="flex-shrink-0 p-3 rounded-2xl transition-all duration-200 hover:scale-105 bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-lg shadow-indigo-500/25 hover:shadow-xl hover:shadow-indigo-500/30"
                        title="Send message"
                      >
                        <Send className="w-5 h-5" />
                      </button>
                    )}
          </div>
                </form>
              </div>
            </div>
          </div>
        )}
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