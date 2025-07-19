/**
 * WhatsApp-like theme constants and utilities
 */

export const whatsappColors = {
  // Primary WhatsApp green
  primary: {
    50: '#f0f9f0',
    100: '#dcf4dc',
    200: '#bae8ba',
    300: '#8dd88d',
    400: '#5cb85c',
    500: '#128c7e', // Main WhatsApp green
    600: '#0d7377',
    700: '#0a5d61',
    800: '#08494c',
    900: '#063d40',
  },
  
  // Secondary colors
  secondary: {
    50: '#f8f9fa',
    100: '#e9ecef',
    200: '#dee2e6',
    300: '#ced4da',
    400: '#adb5bd',
    500: '#6c757d',
    600: '#495057',
    700: '#343a40',
    800: '#212529',
    900: '#1a1d20',
  },
  
  // User message bubble (WhatsApp blue-green)
  userBubble: {
    bg: '#dcf8c6',
    text: '#303030',
    border: '#b8e6b8',
  },
  
  // Bot message bubble (white)
  botBubble: {
    bg: '#ffffff',
    text: '#303030',
    border: '#e5e5e5',
  },
  
  // Chat background
  chatBg: '#e5ddd5',
  
  // Status colors
  status: {
    online: '#25d366',
    offline: '#8696a0',
    typing: '#667781',
    sent: '#667781',
    delivered: '#4fc3f7',
    read: '#53bdeb',
  },
  
  // Input area
  input: {
    bg: '#f0f0f0',
    border: '#d1d7db',
    focus: '#128c7e',
    placeholder: '#8696a0',
  },
};

export const whatsappShadows = {
  sm: '0 1px 3px rgba(0, 0, 0, 0.1)',
  md: '0 4px 6px rgba(0, 0, 0, 0.1)',
  lg: '0 10px 15px rgba(0, 0, 0, 0.1)',
  bubble: '0 1px 2px rgba(0, 0, 0, 0.1)',
  card: '0 2px 8px rgba(0, 0, 0, 0.1)',
};

export const whatsappSpacing = {
  messagePadding: '8px 12px',
  bubbleSpacing: '2px',
  sectionSpacing: '16px',
  inputPadding: '12px 16px',
};

export const whatsappBorderRadius = {
  sm: '4px',
  md: '8px',
  lg: '12px',
  bubble: '18px',
  card: '10px',
};

export const whatsappFonts = {
  primary: 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  arabic: 'Tahoma, Arial, sans-serif',
  mono: 'SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace',
};

export const whatsappAnimations = {
  messageSlideIn: 'slideInMessage 0.3s ease-out',
  fadeIn: 'fadeIn 0.2s ease-in-out',
  bounce: 'bounce 0.5s ease-in-out',
  typing: 'typing 1.4s infinite',
};

/**
 * Get message bubble classes based on sender
 */
export const getMessageBubbleClasses = (isUser: boolean, hasUnits: boolean = false): string => {
  const baseClasses = 'px-3 py-2 rounded-2xl max-w-xs lg:max-w-md xl:max-w-lg relative';
  
  if (isUser) {
    return `${baseClasses} bg-green-100 text-gray-800 ml-auto border border-green-200 ${hasUnits ? 'max-w-none' : ''}`;
  }
  
  return `${baseClasses} bg-white text-gray-800 mr-auto border border-gray-200 shadow-sm ${hasUnits ? 'max-w-none' : ''}`;
};

/**
 * Get message tail classes
 */
export const getMessageTailClasses = (isUser: boolean): string => {
  return isUser 
    ? 'absolute -right-2 top-4 w-0 h-0 border-l-8 border-l-green-100 border-t-8 border-t-transparent border-b-8 border-b-transparent'
    : 'absolute -left-2 top-4 w-0 h-0 border-r-8 border-r-white border-t-8 border-t-transparent border-b-8 border-b-transparent';
};

/**
 * Get typing indicator classes
 */
export const getTypingIndicatorClasses = (): string => {
  return 'flex items-center space-x-1 text-gray-500 px-3 py-2';
};

/**
 * Get header classes
 */
export const getHeaderClasses = (): string => {
  return 'bg-white border-b border-gray-200 shadow-sm sticky top-0 z-10';
};

/**
 * Get chat background classes
 */
export const getChatBackgroundClasses = (): string => {
  return 'bg-gray-50 min-h-screen';
};

/**
 * Get input area classes
 */
export const getInputAreaClasses = (): string => {
  return 'sticky bottom-0 bg-white border-t border-gray-200 p-4 shadow-lg';
};