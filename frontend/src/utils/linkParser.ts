/**
 * Utility to parse markdown links and convert them to clickable HTML elements
 */

import React from 'react';

export interface ParsedContent {
  type: 'text' | 'link';
  content: string;
  url?: string;
  key: string;
}

/**
 * Parses text content to find markdown links [text](url) and returns
 * an array of text and link segments for rendering
 */
export function parseLinksInText(text: string): ParsedContent[] {
  if (!text) return [];
  
  // Regex to match markdown links: [text](url)
  const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
  const segments: ParsedContent[] = [];
  let lastIndex = 0;
  let match;
  let keyCounter = 0;

  while ((match = linkRegex.exec(text)) !== null) {
    const [fullMatch, linkText, url] = match;
    const matchStart = match.index;
    
    // Add text before the link
    if (matchStart > lastIndex) {
      const textBefore = text.slice(lastIndex, matchStart);
      if (textBefore) {
        segments.push({
          type: 'text',
          content: textBefore,
          key: `text-${keyCounter++}`
        });
      }
    }
    
    // Add the link
    segments.push({
      type: 'link',
      content: linkText,
      url: url,
      key: `link-${keyCounter++}`
    });
    
    lastIndex = matchStart + fullMatch.length;
  }
  
  // Add remaining text after the last link
  if (lastIndex < text.length) {
    const remainingText = text.slice(lastIndex);
    if (remainingText) {
      segments.push({
        type: 'text',
        content: remainingText,
        key: `text-${keyCounter++}`
      });
    }
  }
  
  // If no links were found, return the original text as a single segment
  if (segments.length === 0) {
    segments.push({
      type: 'text',
      content: text,
      key: 'text-0'
    });
  }
  
  return segments;
}

/**
 * Renders parsed content segments as React elements
 */
export function renderParsedContent(segments: ParsedContent[]): React.ReactNode[] {
  return segments.map(segment => {
    if (segment.type === 'link' && segment.url) {
      return React.createElement(
        'a',
        {
          key: segment.key,
          href: segment.url,
          target: '_blank',
          rel: 'noopener noreferrer',
          style: {
            color: '#1e90ff',
            textDecoration: 'underline',
            cursor: 'pointer'
          }
        },
        segment.content
      );
    } else {
      return segment.content;
    }
  });
}

/**
 * Convenience function to parse and render text with clickable links
 */
export function parseAndRenderLinks(text: string): React.ReactNode[] {
  const segments = parseLinksInText(text);
  return renderParsedContent(segments);
}