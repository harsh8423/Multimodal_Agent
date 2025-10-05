import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import { 
  Copy, 
  Check, 
  User, 
  Bot, 
  Search, 
  FileImage, 
  Settings,
  Clock,
  Sparkles
} from 'lucide-react';
import { cn, formatTime, copyToClipboard, getAgentColor, getInitials, getAvatarColor } from '@/lib/utils';

const Message = ({ 
  message, 
  isUser = false, 
  agent = null, 
  timestamp = null, 
  showTimestamp = true,
  isStreaming = false,
  mediaUrl = null,
  mediaType = null,
  isFollowUpQuestion = false,
  followUpData = null,
  isNotification = false,
  notificationType = 'info',
  onFollowUpResponse = null
}) => {
  const [copied, setCopied] = React.useState(false);
  const [followUpResponse, setFollowUpResponse] = React.useState('');

  // Check if URL is a Cloudinary URL
  const isCloudinaryUrl = (url) => {
    return url && typeof url === 'string' && url.includes('cloudinary.com');
  };

  // Replace bare URLs in text with markdown links labeled "Link" while preserving existing links and code blocks
  const linkifyMessage = (input) => {
    if (!input || typeof input !== 'string') return input;
    // Split by inline and fenced code to avoid altering code contents
    const parts = input.split(/(```[\s\S]*?```|`[^`]*`)/g);
    const transformed = parts.map((chunk) => {
      const isCode = chunk.startsWith('```') || chunk.startsWith('`');
      if (isCode) return chunk;
      return chunk.replace(/https?:\/\/[\w\-._~:/?#\[\]@!$&'()*+,;=%]+/g, (url, offset, src) => {
        // If already part of markdown link pattern "](" just before the URL, skip
        const prev2 = src.slice(Math.max(0, offset - 2), offset);
        if (prev2 === "](") return url;
        return `[Link](${url})`;
      });
    });
    return transformed.join('');
  };

  const renderedMessage = linkifyMessage(message);

  const handleCopy = async () => {
    const success = await copyToClipboard(message);
    if (success) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const getMessageIcon = () => {
    if (isUser) return <User className="w-5 h-5" />;
    
    switch (agent) {
      case 'research_agent':
        return <Search className="w-5 h-5" />;
      case 'asset_agent':
        return <FileImage className="w-5 h-5" />;
      case 'orchestrator':
        return <Settings className="w-5 h-5" />;
      default:
        return <Sparkles className="w-5 h-5" />;
    }
  };

  const getAvatarStyle = () => {
    if (isUser) {
      return 'bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 ring-4 ring-white/20';
    }
    return 'bg-gradient-to-br from-emerald-400 via-cyan-500 to-blue-500 ring-4 ring-white/20';
  };

  const getAgentLabel = () => {
    switch (agent) {
      case 'research_agent':
        return 'Research Agent';
      case 'asset_agent':
        return 'Asset Agent';
      case 'orchestrator':
        return 'Orchestrator';
      default:
        return 'AI Assistant';
    }
  };

  // Extracted to avoid large inline object causing parser issues in some setups
  const markdownComponents = {
    ul: ({ children }) => (
      <ul className="space-y-2 list-none pl-0">{children}</ul>
    ),
    li: ({ children, ...props }) => {
      if (props.ordered !== undefined) {
        return <li className="ml-6 mb-2">{children}</li>;
      }
      return (
        <li className="flex items-start gap-3 ml-0 mb-2">
          <div className="w-2 h-2 bg-indigo-500 rounded-full mt-2.5 flex-shrink-0"></div>
          <div className="flex-1">{children}</div>
        </li>
      );
    },
    code({ node, inline, className, children, ...props }) {
      const match = /language-(\w+)/.exec(className || '');
      const language = match ? match[1] : '';
      if (!inline && language) {
        return (
          <div className="relative group/code my-6">
            <div className="absolute top-0 left-4 -translate-y-1/2 z-20">
              <span className="bg-gray-800 text-gray-300 px-3 py-1 text-xs font-medium rounded-full">
                {language}
              </span>
            </div>
            <div className="absolute top-3 right-3 z-20 opacity-0 group-hover/code:opacity-100 transition-opacity duration-200">
              <button
                onClick={() => copyToClipboard(String(children).replace(/\n$/, ''))}
                className="p-2 text-gray-400 hover:text-gray-200 hover:bg-gray-700 rounded-lg transition-colors duration-200"
                title="Copy code"
              >
                <Copy className="w-4 h-4" />
              </button>
            </div>
            <SyntaxHighlighter
              style={oneDark}
              language={language}
              PreTag="div"
              className="rounded-xl !mt-0 !mb-0 shadow-lg border border-gray-700 overflow-hidden"
              customStyle={{
                padding: '1.5rem',
                margin: 0,
                fontSize: '0.875rem',
                lineHeight: '1.5'
              }}
              {...props}
            >
              {String(children).replace(/\n$/, '')}
            </SyntaxHighlighter>
          </div>
        );
      }
      return (
        <code className="bg-purple-100 text-purple-800 px-2 py-1 rounded-md text-sm font-medium" {...props}>
          {children}
        </code>
      );
    },
    pre({ children }) {
      return <>{children}</>;
    },
    table({ children }) {
      return (
        <div className="my-6 overflow-hidden rounded-xl border border-gray-200 shadow-sm">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">{children}</table>
          </div>
        </div>
      );
    },
    th({ children }) {
      return (
        <th className="px-6 py-4 bg-gray-50 text-left text-sm font-semibold text-gray-900 uppercase tracking-wider">{children}</th>
      );
    },
    td({ children }) {
      return (
        <td className="px-6 py-4 text-sm text-gray-700 border-t border-gray-100">{children}</td>
      );
    },
    blockquote({ children }) {
      return (
        <div className="my-6 relative">
          <div className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-indigo-500 to-purple-500 rounded-full"></div>
          <blockquote className="bg-gradient-to-br from-indigo-50 via-white to-purple-50 border border-indigo-200/50 pl-8 pr-6 py-6 rounded-r-2xl shadow-sm">
            <div className="text-gray-700 font-medium">{children}</div>
          </blockquote>
        </div>
      );
    },
    h1: ({ children }) => (
      <h1 className="text-2xl font-bold text-gray-900 mb-4 pb-2 border-b border-gray-200">{children}</h1>
    ),
    h2: ({ children }) => (
      <h2 className="text-xl font-semibold text-gray-900 mb-3 mt-8">{children}</h2>
    ),
    h3: ({ children }) => (
      <h3 className="text-lg font-semibold text-gray-900 mb-2 mt-6">{children}</h3>
    )
  };

  return (
    <div className="w-full px-4 sm:px-6 lg:px-8 py-8">
      <div className="max-w-4xl mx-auto">
        {/* Message Header */}
        <div className="flex items-center justify-start mb-4">
          <div className="flex items-center gap-3 w-full">
            {/* Avatar */}
            {!isUser && (
              <div className={cn(
                "w-10 h-10 rounded-full flex items-center justify-center text-white shadow-xl",
                getAvatarStyle()
              )}>
                {getMessageIcon()}
              </div>
            )}

            {/* Names aligned: agent left, user right; no timestamp */}
            {!isUser && (
              <div className="flex flex-col">
                <span className="text-sm font-semibold text-gray-900">
                  {getAgentLabel()}
                </span>
              </div>
            )}

            {/* Streaming Indicator */}
            {isStreaming && (
              <div className="flex items-center gap-2 ml-4">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                </div>
                <span className="text-xs text-blue-500 font-medium">typing...</span>
              </div>
            )}
          </div>
        </div>

        {/* Message Body */}
        <div className="relative group">
          {/* Message Container */}
          <div className={cn(
            "relative transition-all duration-300",
            isUser 
              ? "rounded-2xl p-6 bg-gray-800 text-white max-w-[600px] ml-auto"
              : "p-4 border border-gray-200 rounded-xl bg-white"
          )}>
            
            {/* Copy Button */}
            <button
              onClick={handleCopy}
              className="absolute top-4 right-4 p-2 rounded-lg opacity-0 group-hover:opacity-100 transition-all duration-200 hover:bg-gray-100 z-10"
              title="Copy message"
            >
              {copied ? (
                <Check className="w-4 h-4 text-green-500" />
              ) : (
                <Copy className="w-4 h-4 text-gray-400 hover:text-gray-600" />
              )}
            </button>

            {/* Media Display */}
            {mediaUrl && isCloudinaryUrl(mediaUrl) && (
              <div className="mb-4">
                {mediaType === 'image' ? (
                  <img
                    src={mediaUrl}
                    alt="User uploaded image"
                    className="max-w-full h-auto rounded-lg shadow-md"
                    style={{ maxHeight: '400px' }}
                  />
                ) : mediaType === 'video' ? (
                  <video
                    src={mediaUrl}
                    controls
                    className="max-w-full h-auto rounded-lg shadow-md"
                    style={{ maxHeight: '400px' }}
                  >
                    Your browser does not support the video tag.
                  </video>
                ) : null}
              </div>
            )}

            {/* Message Content */}
           <div
            className={cn(
              // Base prose container (common)
              "prose prose-base max-w-none",

              // Theme: user vs non-user (agent)
              isUser
                ? // USER: inverted / dark text inside bubble
                   "prose-invert prose-p:text-gray-100 prose-headings:text-gray-100"
                : // AGENT: clean light-theme look with black text, no blur
                   "text-black prose-p:text-black prose-headings:text-gray-900 prose-a:text-gray-800 hover:prose-a:underline [--tw-prose-body:#111827] [--tw-prose-headings:#111827] [--tw-prose-links:#111827]",

              // Code & pre styles (respect theme)
              isUser
                ? "prose-code:bg-gray-700 prose-code:text-white prose-pre:bg-gray-900"
                : "prose-code:bg-gray-100 prose-code:text-black prose-pre:bg-white",

              // Shared readable text settings
              "prose-p:leading-relaxed prose-p:text-base",
              "prose-strong:text-gray-900 prose-strong:font-semibold",
              "prose-code:px-2 prose-code:py-1 prose-code:rounded prose-code:text-sm prose-code:font-medium",
              "prose-code:before:content-none prose-code:after:content-none",

              // List & table niceties
              "prose-ul:list-none prose-ul:pl-0 prose-li:pl-0 prose-li:relative prose-li:ml-6 prose-li:mb-2",
              "prose-ol:pl-0 prose-li:marker:text-indigo-500 prose-li:marker:font-semibold",
              "prose-table:border-collapse prose-th:bg-gray-50 prose-th:font-semibold prose-th:text-gray-900 prose-td:border-gray-200",

              // Ensure no blur/filter is applied here for agent (explicitly clear)
              // If any parent applied blur via `backdrop-filter`, these utilities help neutralize it.
              !isUser && "backdrop-blur-0 filter-none",

              // spacing resets
              "[&>*:first-child]:mt-0 [&>*:last-child]:mb-0"
            )}
          >

              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeHighlight]}
                components={markdownComponents}
              >
                {renderedMessage}
              </ReactMarkdown>
            </div>
          </div>
          
          {/* Message glow effect for AI responses */}
          {!isUser && (
            <div className=""></div>
          )}

          {/* Follow-up question display (no input field - user responds via regular chat input) */}
          {isFollowUpQuestion && followUpData && (
            <div className="mt-4 p-5 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl shadow-sm">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full flex items-center justify-center shadow-sm">
                  <span className="text-white text-sm font-semibold">?</span>
                </div>
                <span className="text-sm font-semibold text-blue-800">Follow-up Question</span>
              </div>
              
              {/* Display the question and context */}
              <div className="space-y-3">
                {followUpData.context && (
                  <div className="text-sm text-blue-800 bg-white/60 backdrop-blur-sm p-3 rounded-lg border border-blue-100">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="w-1.5 h-1.5 bg-blue-400 rounded-full"></div>
                      <span className="font-medium text-blue-700">Context</span>
                    </div>
                    <p className="text-blue-800 leading-relaxed">{followUpData.context}</p>
                  </div>
                )}
                
                <div className="text-sm text-blue-900 bg-white/40 backdrop-blur-sm p-3 rounded-lg border border-blue-100">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full"></div>
                    <span className="font-semibold text-blue-800">Question</span>
                  </div>
                  <p className="text-blue-900 leading-relaxed font-medium">{followUpData.question}</p>
                </div>
                
                {/* Quick options for simple yes/no or approve/disapprove questions */}
                {followUpData.options && followUpData.options.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-blue-200/60">
                    <p className="text-sm font-medium text-blue-700 mb-3 flex items-center gap-2">
                      <span className="w-1.5 h-1.5 bg-blue-400 rounded-full"></span>
                      Quick options (type in chat):
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {followUpData.options.map((option, index) => (
                        <span
                          key={index}
                          className="px-3 py-1.5 bg-white/80 backdrop-blur-sm border border-blue-200 rounded-lg text-sm text-blue-700 font-medium hover:bg-white hover:shadow-sm transition-all duration-200 cursor-pointer"
                        >
                          {option}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              
              <div className="mt-4 pt-3 border-t border-blue-200/60">
                <p className="text-xs text-blue-600 flex items-center gap-2">
                  <span className="w-1 h-1 bg-blue-400 rounded-full"></span>
                  💡 Respond to this question using the chat input below
                </p>
              </div>
            </div>
          )}

          {/* Notification styling */}
          {isNotification && (
            <div className={cn(
              "mt-2 px-3 py-2 rounded-md text-sm",
              notificationType === 'error' && "bg-red-50 text-red-700 border border-red-200",
              notificationType === 'warning' && "bg-yellow-50 text-yellow-700 border border-yellow-200",
              notificationType === 'success' && "bg-green-50 text-green-700 border border-green-200",
              notificationType === 'info' && "bg-blue-50 text-blue-700 border border-blue-200"
            )}>
              <div className="flex items-center gap-2">
                <div className={cn(
                  "w-2 h-2 rounded-full",
                  notificationType === 'error' && "bg-red-500",
                  notificationType === 'warning' && "bg-yellow-500",
                  notificationType === 'success' && "bg-green-500",
                  notificationType === 'info' && "bg-blue-500"
                )}></div>
                <span className="font-medium capitalize">{notificationType}</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Message;