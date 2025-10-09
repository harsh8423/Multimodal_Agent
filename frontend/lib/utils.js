import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Utility function to merge Tailwind CSS classes
 */
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

/**
 * Format timestamp for display
 */
export function formatTime(timestamp) {
  if (typeof timestamp === 'string') {
    timestamp = new Date(timestamp);
  }
  
  return new Intl.DateTimeFormat('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  }).format(timestamp);
}

/**
 * Format date for display
 */
export function formatDate(timestamp) {
  if (typeof timestamp === 'string') {
    timestamp = new Date(timestamp);
  }
  
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(timestamp);
}

/**
 * Truncate text to specified length
 */
export function truncateText(text, maxLength = 100) {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
}

/**
 * Get log level color
 */
export function getLogLevelColor(level) {
  switch (level) {
    case 'error':
      return 'text-red-600 bg-red-50 border-red-200';
    case 'warning':
      return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    case 'info':
    default:
      return 'text-blue-600 bg-blue-50 border-blue-200';
  }
}

/**
 * Get agent color
 */
export function getAgentColor(agent) {
  switch (agent) {
    case 'research_agent':
      return 'text-purple-600 bg-purple-50 border-purple-200';
    case 'asset_agent':
      return 'text-green-600 bg-green-50 border-green-200';
    case 'social_media_manager':
      return 'text-indigo-600 bg-indigo-50 border-indigo-200';
    default:
      return 'text-gray-600 bg-gray-50 border-gray-200';
  }
}

/**
 * Debounce function
 */
export function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

/**
 * Generate random ID
 */
export function generateId() {
  return Math.random().toString(36).substring(2, 15);
}

/**
 * Check if message contains code
 */
export function containsCode(text) {
  return /```[\s\S]*```|`[^`]+`/.test(text);
}

/**
 * Extract code blocks from text
 */
export function extractCodeBlocks(text) {
  const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
  const inlineCodeRegex = /`([^`]+)`/g;
  
  const blocks = [];
  let match;
  
  // Extract code blocks
  while ((match = codeBlockRegex.exec(text)) !== null) {
    blocks.push({
      type: 'block',
      language: match[1] || 'text',
      code: match[2].trim()
    });
  }
  
  // Extract inline code
  while ((match = inlineCodeRegex.exec(text)) !== null) {
    blocks.push({
      type: 'inline',
      code: match[1]
    });
  }
  
  return blocks;
}

/**
 * Animate number
 */
export function animateNumber(element, start, end, duration = 1000) {
  const startTime = performance.now();
  
  function updateNumber(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    
    const current = Math.floor(start + (end - start) * progress);
    element.textContent = current;
    
    if (progress < 1) {
      requestAnimationFrame(updateNumber);
    }
  }
  
  requestAnimationFrame(updateNumber);
}

/**
 * Copy text to clipboard
 */
export async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (err) {
    console.error('Failed to copy text: ', err);
    return false;
  }
}

/**
 * Download file
 */
export function downloadFile(content, filename, contentType = 'text/plain') {
  const blob = new Blob([content], { type: contentType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Parse file size
 */
export function parseFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Validate email
 */
export function isValidEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Generate avatar initials
 */
export function getInitials(name) {
  if (!name) return '?';
  
  const words = name.trim().split(' ');
  if (words.length === 1) {
    return words[0].charAt(0).toUpperCase();
  }
  
  return (words[0].charAt(0) + words[words.length - 1].charAt(0)).toUpperCase();
}

/**
 * Get random avatar color
 */
export function getAvatarColor(name) {
  const colors = [
    'bg-red-500',
    'bg-blue-500',
    'bg-green-500',
    'bg-yellow-500',
    'bg-purple-500',
    'bg-pink-500',
    'bg-indigo-500',
    'bg-teal-500'
  ];
  
  if (!name) return colors[0];
  
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  
  return colors[Math.abs(hash) % colors.length];
}