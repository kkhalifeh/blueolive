import React from 'react';

interface TypingIndicatorProps {
  isVisible?: boolean;
}

export const TypingIndicator: React.FC<TypingIndicatorProps> = ({ isVisible = false }) => {
  return (
    <div 
      className="typing-indicator" 
      id="typingIndicator"
      style={{ display: isVisible ? 'block' : 'none' }}
    >
      <span className="dot"></span>
      <span className="dot"></span>
      <span className="dot"></span>
    </div>
  );
};