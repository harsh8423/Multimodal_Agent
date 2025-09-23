import React, { useState, useEffect } from 'react';
import { MessageSquare, Plus, RefreshCw, MoreVertical } from 'lucide-react';
import { cn } from '@/lib/utils';

const ChatHistory = ({ 
  token,
  selectedChatId = null,
  onSelectChat,
  onCreateChat,
  onChatsChange
}) => {
  const [chats, setChats] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [activeDropdown, setActiveDropdown] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [renameChat, setRenameChat] = useState(null);
  const [newTitle, setNewTitle] = useState('');
  const [renaming, setRenaming] = useState(false);
  const API_BASE_URL = typeof window !== 'undefined' ? (process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000') : '';

  const fetchChatHistory = async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/chats/history?token=${token}`);
      if (!response.ok) throw new Error('Failed to fetch chat history');
      const data = await response.json();
      setChats(Array.isArray(data) ? data : []);
      if (onChatsChange) onChatsChange(Array.isArray(data) ? data : []);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchChatHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchChatHistory();
    setRefreshing(false);
  };

  const handleCreate = async () => {
    if (onCreateChat) await onCreateChat();
    await fetchChatHistory();
  };

  const handleDropdownClick = (e, chatId) => {
    e.stopPropagation();
    setActiveDropdown(activeDropdown === chatId ? null : chatId);
  };

  const handleMenuAction = (action, chat) => {
    setActiveDropdown(null);
    
    if (action === 'delete') {
      setDeleteConfirm(chat);
    } else if (action === 'rename') {
      setRenameChat(chat);
      setNewTitle(chat.title || 'Untitled Chat');
    } else {
      // Placeholder for other actions
      console.log(`${action} action for chat:`, chat);
    }
  };

  const handleDeleteChat = async (chat) => {
    if (!token) return;
    
    setDeleting(true);
    try {
      const response = await fetch(`${API_BASE_URL}/chats/${chat.chat_id}?token=${token}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to delete chat');
      }

      // Remove the deleted chat from the local state
      setChats(prevChats => prevChats.filter(c => c.chat_id !== chat.chat_id));
      
      // Update parent component if callback provided
      if (onChatsChange) {
        const updatedChats = chats.filter(c => c.chat_id !== chat.chat_id);
        onChatsChange(updatedChats);
      }

      // If the deleted chat was selected, clear the selection
      if (selectedChatId === chat.chat_id && onSelectChat) {
        onSelectChat(null);
      }

    } catch (error) {
      console.error('Error deleting chat:', error);
      setError(error.message);
    } finally {
      setDeleting(false);
      setDeleteConfirm(null);
    }
  };

  const cancelDelete = () => {
    setDeleteConfirm(null);
  };

  const handleRenameChat = async () => {
    if (!token || !renameChat || !newTitle.trim()) return;
    
    setRenaming(true);
    try {
      const response = await fetch(`${API_BASE_URL}/chats/${renameChat.chat_id}/title?token=${token}&title=${encodeURIComponent(newTitle.trim())}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        let errorMessage = 'Failed to rename chat';
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorData.message || errorMessage;
        } catch (e) {
          // If response is not JSON, use status text
          errorMessage = response.statusText || errorMessage;
        }
        throw new Error(errorMessage);
      }

      // Update the chat in the local state
      setChats(prevChats => prevChats.map(c => 
        c.chat_id === renameChat.chat_id 
          ? { ...c, title: newTitle.trim() }
          : c
      ));
      
      // Update parent component if callback provided
      if (onChatsChange) {
        const updatedChats = chats.map(c => 
          c.chat_id === renameChat.chat_id 
            ? { ...c, title: newTitle.trim() }
            : c
        );
        onChatsChange(updatedChats);
      }

    } catch (error) {
      console.error('Error renaming chat:', error);
      setError(error.message);
    } finally {
      setRenaming(false);
      setRenameChat(null);
      setNewTitle('');
    }
  };

  const cancelRename = () => {
    setRenameChat(null);
    setNewTitle('');
  };

  return (
    <div 
      className="flex-1 overflow-y-auto bg-white border-r border-gray-200"
      onClick={() => setActiveDropdown(null)}
    >
      <div className="p-4">
        {/* Header Section */}
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-gray-700" />
            <h2 className="text-lg font-semibold text-gray-900">Chats</h2>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className={cn(
                "p-2 rounded-lg border border-gray-200 bg-white hover:bg-gray-50 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed",
                "focus:outline-none focus:ring-2 focus:ring-gray-300 focus:ring-offset-1"
              )}
              title="Refresh chats"
            >
              <RefreshCw className={cn("w-4 h-4 text-gray-600", refreshing && "animate-spin")} />
            </button>
            <button
              onClick={handleCreate}
              className={cn(
                "p-2 rounded-lg bg-black text-white hover:bg-gray-800 transition-all duration-200",
                "focus:outline-none focus:ring-2 focus:ring-gray-300 focus:ring-offset-1",
                "shadow-sm hover:shadow-md"
              )}
              title="Start new chat"
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Content Section */}
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="flex flex-col items-center gap-2">
              <div className="w-6 h-6 border-2 border-gray-300 border-t-gray-600 rounded-full animate-spin"></div>
              <p className="text-xs text-gray-500">Loading chats...</p>
            </div>
          </div>
        ) : error ? (
          <div className="p-4 text-center">
            <div className="w-10 h-10 mx-auto mb-3 bg-red-50 rounded-full flex items-center justify-center">
              <MessageSquare className="w-5 h-5 text-red-500" />
            </div>
            <p className="text-xs text-red-600 font-medium mb-1">Failed to load chats</p>
            <p className="text-xs text-red-500">{error}</p>
          </div>
        ) : chats.length === 0 ? (
          <div className="text-center py-8">
            <div className="w-12 h-12 mx-auto mb-3 bg-gray-50 rounded-full flex items-center justify-center">
              <MessageSquare className="w-6 h-6 text-gray-400" />
            </div>
            <h3 className="text-xs font-medium text-gray-900 mb-1">No conversations yet</h3>
            <p className="text-xs text-gray-500">Start a new chat to begin</p>
          </div>
        ) : (
          <div className="space-y-1">
            {chats.map(chat => (
              <div
                key={chat.chat_id}
                className={cn(
                  "group relative p-2 rounded-lg cursor-pointer transition-all duration-200",
                  "hover:bg-gray-50",
                  selectedChatId === chat.chat_id 
                    ? "bg-black text-white" 
                    : "text-gray-900"
                )}
                onClick={() => onSelectChat && onSelectChat(chat)}
              >
                <div className="flex items-center gap-2 relative">
                  {/* Left hover dot */}
                  <div className={cn(
                    "w-1.5 h-1.5 rounded-full transition-opacity duration-200 absolute -left-1",
                    selectedChatId === chat.chat_id 
                      ? "bg-white opacity-100" 
                      : "bg-gray-400 opacity-0 group-hover:opacity-100"
                  )} />
                  
                  <div className="flex-1 min-w-0 pl-2">
                    <h4 className={cn(
                      "font-medium text-xs truncate",
                      selectedChatId === chat.chat_id ? "text-white" : "text-gray-900"
                    )}>
                      {chat.title || 'Untitled Chat'}
                    </h4>
                  </div>
                  
                  {/* Three dots menu */}
                  <div className="relative">
                    <button
                      onClick={(e) => handleDropdownClick(e, chat.chat_id)}
                      className={cn(
                        "p-1 rounded transition-opacity duration-200 hover:bg-gray-200",
                        "opacity-0 group-hover:opacity-100",
                        selectedChatId === chat.chat_id && "hover:bg-white/20",
                        activeDropdown === chat.chat_id && "opacity-100"
                      )}
                    >
                      <MoreVertical className={cn(
                        "w-3 h-3",
                        selectedChatId === chat.chat_id ? "text-white" : "text-gray-600"
                      )} />
                    </button>
                    
                    {/* Dropdown menu */}
                    {activeDropdown === chat.chat_id && (
                      <div className="absolute right-0 top-full mt-1 w-32 bg-white border border-gray-200 rounded-lg shadow-lg z-10">
                        <div className="py-1">
                          <button
                            onClick={() => handleMenuAction('share', chat)}
                            className="w-full px-3 py-1.5 text-left text-xs text-gray-700 hover:bg-gray-50 transition-colors"
                          >
                            Share
                          </button>
                          <button
                            onClick={() => handleMenuAction('rename', chat)}
                            className="w-full px-3 py-1.5 text-left text-xs text-gray-700 hover:bg-gray-50 transition-colors"
                          >
                            Rename
                          </button>
                          <button
                            onClick={() => handleMenuAction('delete', chat)}
                            className="w-full px-3 py-1.5 text-left text-xs text-red-600 hover:bg-red-50 transition-colors"
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Delete Confirmation Dialog */}
      {deleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-sm w-full mx-4 shadow-xl">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Delete Chat</h3>
            <p className="text-sm text-gray-600 mb-6">
              Are you sure you want to delete "{deleteConfirm.title || 'Untitled Chat'}"? This action cannot be undone.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={cancelDelete}
                disabled={deleting}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-lg hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDeleteChat(deleteConfirm)}
                disabled={deleting}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-lg hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {deleting ? (
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    Deleting...
                  </div>
                ) : (
                  'Delete'
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Rename Chat Dialog */}
      {renameChat && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-sm w-full mx-4 shadow-xl">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Rename Chat</h3>
            <p className="text-sm text-gray-600 mb-4">
              Enter a new name for "{renameChat.title || 'Untitled Chat'}"
            </p>
            <input
              type="text"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  handleRenameChat();
                }
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-300 focus:border-transparent"
              placeholder="Enter chat title"
              disabled={renaming}
              autoFocus
            />
            <div className="flex gap-3 justify-end mt-6">
              <button
                onClick={cancelRename}
                disabled={renaming}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-lg hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Cancel
              </button>
              <button
                onClick={handleRenameChat}
                disabled={renaming || !newTitle.trim()}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {renaming ? (
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    Renaming...
                  </div>
                ) : (
                  'Rename'
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatHistory;