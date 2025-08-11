'use client'
import React, { useState } from 'react';
import { Message } from '@/types/message';

interface PromptProps {
    message: Message;
}

const Prompt: React.FC<PromptProps> = ({ message }) => {
  return (
    <div>
      <div>
        <p>{message.content}</p>
        {/* <span>{new Date(message.timestamp).toLocaleTimeString()}</span> */}
      </div>
    </div>
  );
};


export default Prompt;