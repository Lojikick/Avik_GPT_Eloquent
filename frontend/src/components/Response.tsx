'use client'
import React, { useState } from 'react';
import { Message } from '@/types/message'

interface ResponseProps {
    message : Message;
}

const Response: React.FC <ResponseProps> = ({ message }) => {
    return (
        <div>
            <p>{message.content}</p>
        </div>

    );
}

export default Response;