import React, { createContext, useContext, useReducer } from 'react';
import type { ReactNode } from 'react';
import type { Message, ChatContextType } from '../types';

// Action types
type ChatAction =
  | { type: 'ADD_MESSAGE'; payload: Message }
  | { type: 'CLEAR_MESSAGES' }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_CONVERSATION_ID'; payload: string | null };

// Initial state
interface ChatState {
  messages: Message[];
  isLoading: boolean;
  conversationId: string | null;
}

const initialState: ChatState = {
  messages: [],
  isLoading: false,
  conversationId: null,
};

// Reducer
const chatReducer = (state: ChatState, action: ChatAction): ChatState => {
  switch (action.type) {
    case 'ADD_MESSAGE':
      return {
        ...state,
        messages: [...state.messages, action.payload],
      };
    case 'CLEAR_MESSAGES':
      return {
        ...state,
        messages: [],
        conversationId: null,
      };
    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.payload,
      };
    case 'SET_CONVERSATION_ID':
      return {
        ...state,
        conversationId: action.payload,
      };
    default:
      return state;
  }
};

// Context
const ChatContext = createContext<ChatContextType | undefined>(undefined);

// Provider component
interface ChatProviderProps {
  children: ReactNode;
}

export const ChatProvider: React.FC<ChatProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(chatReducer, initialState);

  const addMessage = (message: Message) => {
    dispatch({ type: 'ADD_MESSAGE', payload: message });
  };

  const clearMessages = () => {
    dispatch({ type: 'CLEAR_MESSAGES' });
  };

  const setIsLoading = (loading: boolean) => {
    dispatch({ type: 'SET_LOADING', payload: loading });
  };

  const setConversationId = (id: string | null) => {
    dispatch({ type: 'SET_CONVERSATION_ID', payload: id });
  };

  const value: ChatContextType = {
    messages: state.messages,
    addMessage,
    clearMessages,
    isLoading: state.isLoading,
    setIsLoading,
    conversationId: state.conversationId,
    setConversationId,
  };

  return (
    <ChatContext.Provider value={value}>
      {children}
    </ChatContext.Provider>
  );
};

// Custom hook
export const useChat = (): ChatContextType => {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};