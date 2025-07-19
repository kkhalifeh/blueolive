import React from 'react';
import type { Message } from '../types';
import { parseAndRenderLinks } from '../utils/linkParser';

interface MessageBubbleProps {
  message: Message;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const { content, isUser } = message;

  // Parse content to handle markdown links
  const renderContent = () => {
    // Split by newlines first to preserve line breaks
    const lines = content.split('\n');
    
    return lines.map((line, index) => {
      const parsedLine = parseAndRenderLinks(line);
      
      return (
        <React.Fragment key={`line-${index}`}>
          {parsedLine}
          {index < lines.length - 1 && <br />}
        </React.Fragment>
      );
    });
  };

  return (
    <div className={`message ${isUser ? 'user-message' : 'bot-message'}`}>
      {renderContent()}
    </div>
  );
};