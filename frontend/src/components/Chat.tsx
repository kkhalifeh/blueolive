import React, { useEffect, useRef, useState } from 'react';
import { useChat } from '../contexts/ChatContext';
import { MessageBubble } from './MessageBubble';
import { TypingIndicator } from './TypingIndicator';
import { ChatInput } from './ChatInput';
import { chatApi } from '../services/api';
import type { Message } from '../types';
import { detectLanguage } from '../utils/language';
import { splitBotMessage, type MessageChunk } from '../utils/messageSplitter';

export const Chat: React.FC = () => {
  const { 
    messages, 
    addMessage, 
    isLoading, 
    setIsLoading, 
    conversationId, 
    setConversationId 
  } = useChat();
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [pendingChunks, setPendingChunks] = useState<MessageChunk[]>([]);
  const [isDisplayingChunks, setIsDisplayingChunks] = useState(false);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading, isDisplayingChunks]);

  // Process pending message chunks
  useEffect(() => {
    if (pendingChunks.length > 0 && !isDisplayingChunks) {
      setIsDisplayingChunks(true);
      displayMessageChunks(pendingChunks);
    }
  }, [pendingChunks, isDisplayingChunks]);

  const displayMessageChunks = async (chunks: MessageChunk[]) => {
    for (let i = 0; i < chunks.length; i++) {
      const chunk = chunks[i];
      
      // Wait for the specified delay
      if (chunk.delay > 0) {
        await new Promise(resolve => setTimeout(resolve, chunk.delay));
      }
      
      // Show typing indicator for a moment before each message (except the first)
      if (i > 0) {
        setIsLoading(true);
        await new Promise(resolve => setTimeout(resolve, 500));
        setIsLoading(false);
      }
      
      // Add the message chunk
      const chunkMessage: Message = {
        id: `${Date.now()}-chunk-${i}`,
        content: chunk.content,
        isUser: false,
        timestamp: new Date(),
        language: detectLanguage(chunk.content),
      };
      
      addMessage(chunkMessage);
      
      // Brief pause between messages
      if (i < chunks.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 200));
      }
    }
    
    setPendingChunks([]);
    setIsDisplayingChunks(false);
  };

  const handleSendMessage = async (messageText: string) => {
    if (!messageText.trim()) return;

    const language = detectLanguage(messageText);
    
    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      content: messageText,
      isUser: true,
      timestamp: new Date(),
      language,
    };
    
    addMessage(userMessage);
    setIsLoading(true);

    try {
      // Send message to API
      const response = await chatApi.sendMessage({
        message: messageText,
        conversation_id: conversationId || undefined,
      });

      // Update conversation ID if this is the first message
      if (!conversationId && response.conversation_id) {
        setConversationId(response.conversation_id);
      }

      // Split the bot response into chunks
      const chunks = splitBotMessage(response.bot_response);
      
      // If there's only one chunk or it's short, display immediately
      if (chunks.length === 1 && chunks[0].content.length < 200) {
        const botMessage: Message = {
          id: (Date.now() + 1).toString(),
          content: response.bot_response,
          isUser: false,
          timestamp: new Date(),
          language: detectLanguage(response.bot_response),
        };
        
        addMessage(botMessage);
        setIsLoading(false);
      } else {
        // Display chunks sequentially
        setIsLoading(false);
        setPendingChunks(chunks);
      }
      
    } catch (error) {
      console.error('Error sending message:', error);
      
      // Add error message
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: language === 'ar' 
          ? 'عذراً، حدث خطأ. يرجى المحاولة مرة أخرى.'
          : 'Sorry, an error occurred. Please try again.',
        isUser: false,
        timestamp: new Date(),
        language,
      };
      
      addMessage(errorMessage);
      setIsLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Chat Container */}
      <div className="chat-container" id="chatContainer">
        {messages.length === 0 && (
          <div className="message bot-message">
            This is BlueOlive Real Estate AI Assistant 🏠 Start with a simple "Hello" or "Hi"
          </div>
        )}
        
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Typing Indicator */}
      <TypingIndicator isVisible={isLoading} />

      {/* Input Area */}
      <ChatInput 
        onSendMessage={handleSendMessage} 
        disabled={isLoading || isDisplayingChunks}
        placeholder="Type your message..."
      />
    </div>
  );
};