'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, MapPin, Plane, Hotel, Utensils } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
// Removed: import { motion, AnimatePresence } from 'framer-motion';
import { useChatStore, ChatMessage } from '@/lib/store';
import { streamRequest, StreamEvent } from '@/lib/api';

interface ChatInterfaceProps {
    tripId?: string;
}

export function ChatInterface({ tripId }: ChatInterfaceProps) {
    const [input, setInput] = useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const [statusVisible, setStatusVisible] = useState(false);
    const abortControllerRef = useRef<AbortController | null>(null);

    const {
        messages,
        isStreaming,
        currentAgent,
        currentStatus,
        addMessage,
        appendToLastMessage,
        setStreaming,
        setAgentStatus
    } = useChatStore();

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    // Toggle status bar visibility
    useEffect(() => {
        setStatusVisible(Boolean(currentStatus));
    }, [currentStatus]);

    // Add greeting on first load
    useEffect(() => {
        if (messages.length === 0) {
            addMessage({
                id: 'greeting',
                role: 'assistant',
                content: `Hey there, fellow traveler! 🌴✈️

I'm your AI travel buddy, and I'm super excited to help you plan an amazing trip!

Where are you dreaming of going? And how many days do you have for this adventure?`,
                timestamp: new Date()
            });
        }
    }, []);

    const handleStop = () => {
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
            abortControllerRef.current = null;
        }
        setStreaming(false);
        setAgentStatus('', '');
        appendToLastMessage('\n\n_[Stream stopped by user]_');
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isStreaming) return;

        const userMessage = input.trim();
        setInput('');

        // Add user message
        addMessage({
            id: Date.now().toString(),
            role: 'user',
            content: userMessage,
            timestamp: new Date()
        });

        // Add empty assistant message for streaming
        addMessage({
            id: (Date.now() + 1).toString(),
            role: 'assistant',
            content: '',
            timestamp: new Date()
        });

        setStreaming(true);

        // Create abort controller for this request
        abortControllerRef.current = new AbortController();

        try {
            await streamRequest('/chat/stream', { message: userMessage, trip_id: tripId }, (event: StreamEvent) => {
                switch (event.type) {
                    case 'token':
                        if (event.content) {
                            appendToLastMessage(event.content);
                        }
                        break;
                    case 'status':
                        setAgentStatus(event.agent || '', event.status || '');
                        break;
                    case 'done':
                        setAgentStatus('', '');
                        break;
                    case 'cancelled':
                        appendToLastMessage('\n\n_[Previous request cancelled]_');
                        break;
                    case 'error':
                        appendToLastMessage(`\n\n⚠️ Error: ${event.error}`);
                        break;
                }
            });
        } catch (error) {
            if (error instanceof Error && error.name !== 'AbortError') {
                appendToLastMessage('\n\n⚠️ Something went wrong. Please try again.');
            }
        } finally {
            setStreaming(false);
            abortControllerRef.current = null;
        }
    };

    const getAgentIcon = (agent: string) => {
        switch (agent) {
            case 'Route': return <MapPin className="w-4 h-4" />;
            case 'Transport': return <Plane className="w-4 h-4" />;
            case 'Stay': return <Hotel className="w-4 h-4" />;
            case 'Food': return <Utensils className="w-4 h-4" />;
            default: return null;
        }
    };

    return (
        <div className="flex flex-col h-full bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
            {/* Status Bar - CSS animations instead of Framer Motion */}
            {currentStatus && (
                <div className={`status-bar ${statusVisible ? 'visible' : ''} px-4 py-2 bg-purple-500/20 border-b border-purple-500/30 flex items-center gap-2`}>
                    {getAgentIcon(currentAgent)}
                    <span className="text-purple-200 text-sm">{currentStatus}</span>
                    <Loader2 className="w-4 h-4 animate-spin ml-auto text-purple-400" />
                </div>
            )}

            {/* Messages - with chat-container for smooth scroll */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 chat-container">
                {messages.map((message) => (
                    <MessageBubble key={message.id} message={message} />
                ))}
                {isStreaming && (
                    <div className="flex justify-start">
                        <div className="bg-white/10 px-4 py-3 rounded-2xl border border-white/10">
                            <div className="typing-indicator">
                                <span />
                                <span />
                                <span />
                            </div>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <form onSubmit={handleSubmit} className="p-4 border-t border-white/10">
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Tell me about your dream trip..."
                        disabled={isStreaming}
                        className="flex-1 px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                    />

                    {/* Show Stop button when streaming, Send button otherwise */}
                    {isStreaming ? (
                        <button
                            type="button"
                            onClick={handleStop}
                            className="px-6 py-3 bg-red-500 hover:bg-red-600 rounded-xl text-white font-medium transition-all flex items-center gap-2"
                        >
                            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                <rect x="6" y="6" width="8" height="8" />
                            </svg>
                            Stop
                        </button>
                    ) : (
                        <button
                            type="submit"
                            disabled={!input.trim()}
                            className="px-4 py-3 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl text-white font-medium hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                        >
                            <Send className="w-5 h-5" />
                        </button>
                    )}
                </div>
            </form>
        </div>
    );
}

// MessageBubble with Intersection Observer instead of Framer Motion
function MessageBubble({ message }: { message: ChatMessage }) {
    const [isVisible, setIsVisible] = useState(false);
    const ref = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const observer = new IntersectionObserver(
            ([entry]) => {
                if (entry.isIntersecting) {
                    setIsVisible(true);
                    observer.disconnect();
                }
            },
            { threshold: 0.1 }
        );

        if (ref.current) {
            observer.observe(ref.current);
        }

        return () => observer.disconnect();
    }, []);

    const isUser = message.role === 'user';

    return (
        <div
            ref={ref}
            className={`message-bubble ${isVisible ? 'visible' : ''} ${isUser ? 'user' : 'assistant'} flex ${isUser ? 'justify-end' : 'justify-start'}`}
        >
            <div
                className={`max-w-[80%] px-4 py-3 rounded-2xl ${isUser
                    ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white'
                    : 'bg-white/10 text-white border border-white/10'
                    }`}
            >
                <div className="prose prose-invert prose-sm max-w-none">
                    <ReactMarkdown>{message.content || '...'}</ReactMarkdown>
                </div>
            </div>
        </div>
    );
}

export default ChatInterface;
