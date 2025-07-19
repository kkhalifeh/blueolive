/**
 * Utility to split bot responses into multiple human-like messages
 * Generic approach: splits on newlines and groups small consecutive lines
 */

export interface MessageChunk {
  content: string;
  delay: number; // delay in milliseconds before showing this chunk
}

export function splitBotMessage(content: string): MessageChunk[] {
  // If no newlines, return as single message
  if (!content.includes('\n')) {
    return [{
      content: content.trim(),
      delay: 0
    }];
  }
  
  // Split by newlines and filter empty lines
  const lines = content.split('\n')
    .map(line => line.trim())
    .filter(line => line.length > 0);
  
  // If only one line after filtering, return as single message
  if (lines.length <= 1) {
    return [{
      content: content.trim(),
      delay: 0
    }];
  }
  
  const chunks: MessageChunk[] = [];
  let currentChunk = '';
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    
    // If current chunk is getting long, or this line is long enough to be its own chunk
    if (currentChunk && (
      currentChunk.length > 150 || 
      line.length > 100 ||
      (currentChunk.length > 50 && line.length > 50)
    )) {
      // Save current chunk
      chunks.push({
        content: currentChunk.trim(),
        delay: chunks.length === 0 ? 0 : 400 + (chunks.length * 300)
      });
      currentChunk = line;
    } else {
      // Add to current chunk
      currentChunk += (currentChunk ? '\n' : '') + line;
    }
  }
  
  // Add final chunk
  if (currentChunk.trim()) {
    chunks.push({
      content: currentChunk.trim(),
      delay: chunks.length === 0 ? 0 : 400 + (chunks.length * 300)
    });
  }
  
  // If we still only have one chunk, but it's very long, split it more aggressively
  if (chunks.length === 1 && chunks[0].content.length > 400) {
    return splitLongChunk(chunks[0].content);
  }
  
  return chunks.length > 0 ? chunks : [{ content: content.trim(), delay: 0 }];
}

function splitLongChunk(content: string): MessageChunk[] {
  const chunks: MessageChunk[] = [];
  
  // Split on double newlines first, then single newlines, then sentences
  const doubleSplit = content.split('\n\n').filter(part => part.trim());
  
  for (const part of doubleSplit) {
    const trimmedPart = part.trim();
    
    if (trimmedPart.length > 300) {
      // Split further by single newlines
      const singleSplit = trimmedPart.split('\n').filter(line => line.trim());
      
      let currentChunk = '';
      for (const line of singleSplit) {
        if (currentChunk && (currentChunk + '\n' + line).length > 250) {
          chunks.push({
            content: currentChunk.trim(),
            delay: chunks.length === 0 ? 0 : 400 + (chunks.length * 300)
          });
          currentChunk = line;
        } else {
          currentChunk += (currentChunk ? '\n' : '') + line;
        }
      }
      
      if (currentChunk.trim()) {
        chunks.push({
          content: currentChunk.trim(),
          delay: chunks.length === 0 ? 0 : 400 + (chunks.length * 300)
        });
      }
    } else {
      chunks.push({
        content: trimmedPart,
        delay: chunks.length === 0 ? 0 : 400 + (chunks.length * 300)
      });
    }
  }
  
  return chunks.length > 0 ? chunks : [{ content: content.trim(), delay: 0 }];
}