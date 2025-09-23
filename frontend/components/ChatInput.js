import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, 
  Paperclip, 
  Mic, 
  MicOff, 
  StopCircle,
  Plus,
  Image,
  FileText,
  Video,
  Zap,
  ChevronUp,
  ChevronDown
} from 'lucide-react';
import { cn } from '@/lib/utils';

const ChatInput = ({ 
  onSendMessage, 
  onFileAttach, 
  onVoiceRecord,
  onImagePaste = () => {},
  placeholder = "Type your message...",
  disabled = false,
  isStreaming = false,
  onStopStreaming,
  maxRows = 4,
  nanoStream = [],
  nanoExpanded = false,
  onNanoToggle = () => {}
}) => {
  const [message, setMessage] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [showAttachments, setShowAttachments] = useState(false);
  const textareaRef = useRef(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      const scrollHeight = textareaRef.current.scrollHeight;
      const lineHeight = parseInt(getComputedStyle(textareaRef.current).lineHeight || '20', 10);
      const maxHeight = lineHeight * maxRows;
      textareaRef.current.style.height = `${Math.min(scrollHeight, maxHeight)}px`;
    }
  }, [message, maxRows]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim() && !disabled && onSendMessage) {
      onSendMessage(message.trim());
      setMessage('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const toggleRecording = () => {
    if (isRecording) {
      setIsRecording(false);
      onVoiceRecord?.(false);
    } else {
      setIsRecording(true);
      onVoiceRecord?.(true);
    }
  };

  const attachmentOptions = [
    { icon: Image, label: 'Image', action: () => onFileAttach?.('image') },
    { icon: Video, label: 'Video', action: () => onFileAttach?.('video') },
    { icon: FileText, label: 'Document', action: () => onFileAttach?.('document') },
    { icon: Paperclip, label: 'File', action: () => onFileAttach?.('file') },
  ];

  const handlePaste = (e) => {
    if (!e.clipboardData || disabled) return;
    const files = e.clipboardData.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (file && file.type && file.type.startsWith('image/')) {
        e.preventDefault();
        onImagePaste?.(file);
      }
    }
  };

  return (
    <>
      <div className="w-full sticky bottom-0 z-20 p-4 sm:p-6">
        <div className="max-w-4xl mx-auto">
          {showAttachments && (
            <div className="mb-3 flex justify-center">
              <div className="bg-white/90 backdrop-blur-md border border-gray-200/80 rounded-2xl shadow-xl p-3">
                <div className="flex items-center gap-2">
                  {attachmentOptions.map((option, index) => (
                    <button
                      key={index}
                      onClick={() => {
                        option.action();
                        setShowAttachments(false);
                      }}
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

          <div className="relative">
            {/* Nano message bar - integrated with input */}
            {nanoStream.length > 0 && (
              <div className="relative">
                {/* Nano message bar */}
                <div className="flex items-center px-3 py-2 text-[11px] font-mono text-gray-600 bg-white/90 backdrop-blur-md border border-gray-200/80 rounded-t-3xl border-b-0">
                  <button
                    type="button"
                    className="mr-2 p-0.5 text-gray-500 hover:text-gray-700"
                    onClick={onNanoToggle}
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
            
            <div className={cn(
              "bg-white/90 backdrop-blur-md border border-gray-200/80 shadow-2xl overflow-hidden transition-all duration-300 hover:shadow-3xl hover:border-gray-300/80",
              nanoStream.length > 0 ? "rounded-b-3xl" : "rounded-3xl"
            )}>
              <form onSubmit={handleSubmit} className="flex items-end gap-3 p-4">
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
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    onKeyDown={handleKeyDown}
                  onPaste={handlePaste}
                    placeholder={placeholder}
                    disabled={disabled}
                    rows={1}
                    className="w-full resize-none bg-transparent text-gray-900 placeholder-gray-500 border-none outline-none text-base leading-6 py-3 px-1 max-h-32 scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-transparent"
                  />
                  {message.length > 0 && (
                    <div className="absolute bottom-1 right-2 text-xs text-gray-400">
                      {message.length}
                    </div>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={toggleRecording}
                    className={cn(
                      "flex-shrink-0 p-3 rounded-2xl transition-all duration-200 hover:scale-105",
                      isRecording 
                        ? "bg-red-500 text-white shadow-lg shadow-red-500/25 animate-pulse" 
                        : "bg-gray-100 text-gray-600 hover:bg-gray-200 hover:text-gray-800"
                    )}
                    title={isRecording ? "Stop recording" : "Start voice recording"}
                  >
                    {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
                  </button>

                  {isStreaming ? (
                    <button
                      type="button"
                      onClick={onStopStreaming}
                      className="flex-shrink-0 p-3 bg-red-500 text-white rounded-2xl shadow-lg shadow-red-500/25 hover:bg-red-600 transition-all duration-200 hover:scale-105"
                      title="Stop generation"
                    >
                      <StopCircle className="w-5 h-5" />
                    </button>
                  ) : (
                    <button
                      type="submit"
                      disabled={!message.trim() || disabled}
                      className={cn(
                        "flex-shrink-0 p-3 rounded-2xl transition-all duration-200 hover:scale-105",
                        message.trim() && !disabled
                          ? "bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-lg shadow-indigo-500/25 hover:shadow-xl hover:shadow-indigo-500/30" 
                          : "bg-gray-100 text-gray-400 cursor-not-allowed"
                      )}
                      title="Send message"
                    >
                      <Send className="w-5 h-5" />
                    </button>
                  )}
                </div>
              </form>

              <div className="px-4 pb-3">
                <div className="flex items-center justify-between text-xs text-gray-500">
                  <div className="flex items-center gap-4">
                    <span className="flex items-center gap-1">
                      <Zap className="w-3 h-3" />
                      Press Enter to send, Shift+Enter for new line
                    </span>
                  </div>
                  {isStreaming && (
                    <div className="flex items-center gap-2 text-indigo-600">
                      <div className="w-2 h-2 bg-indigo-500 rounded-full animate-pulse"></div>
                      <span className="font-medium">AI is thinking...</span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="absolute inset-0 -z-10 bg-gradient-to-r from-indigo-500/10 via-purple-500/10 to-pink-500/10 rounded-3xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
          </div>

          {isRecording && (
            <div className="mt-3 flex justify-center">
              <div className="bg-red-500/90 backdrop-blur-md text-white px-6 py-3 rounded-2xl shadow-xl">
                <div className="flex items-center gap-3">
                  <div className="w-3 h-3 bg-white rounded-full animate-pulse"></div>
                  <span className="text-sm font-medium">Recording... Click mic to stop</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="h-6 sm:h-8"></div>
    </>
  );
};

export default ChatInput;

