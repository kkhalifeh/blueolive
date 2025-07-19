export interface Message {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
  language?: 'ar' | 'en';
}

export interface Unit {
  unit_id: number;
  project_id: number;
  unit_number: string | null;
  address: string;
  size_sqm: number;
  price_jod: number;
  bedrooms: number;
  bathrooms: number;
  floor_type: string | null;
  floor_number: number | null;
  description_ar: string;
  photos_urls: string[];
}

export interface ChatResponse {
  conversation_id: string;
  bot_response: string;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
}

export interface Customer {
  name?: string;
  email?: string;
  phone_number?: string;
  preferences?: {
    budget?: number;
    bedrooms?: number;
    location?: string;
    language?: 'ar' | 'en';
    units_shown?: number[];
  };
}

export interface ChatContextType {
  messages: Message[];
  addMessage: (message: Message) => void;
  clearMessages: () => void;
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
  conversationId: string | null;
  setConversationId: (id: string | null) => void;
}

export interface ApiError {
  message: string;
  status?: number;
}