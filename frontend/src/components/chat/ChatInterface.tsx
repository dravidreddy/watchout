'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, MapPin, Plane, Hotel, Utensils, Save, CheckCircle, Sparkles, Image as ImageIcon } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import type { Components } from 'react-markdown';
import DOMPurify from 'dompurify';
import rehypeSanitize from 'rehype-sanitize';
import { useChatStore, ChatMessage } from '@/lib/store';
import { streamRequest, StreamEvent, api, ApiError, analyzeScreenshot } from '@/lib/api';
import { RestaurantCard, AttractionCard, Restaurant } from './ChatMessageComponents';
import { DestinationSuggestionCards, DestinationSuggestion } from './DestinationSuggestionCards';
import { toast } from 'sonner';

/**
 * XSS-safe markdown renderer for AI-generated content.
 *
 * Strategy:
 * 1. DOMPurify strips any script tags, javascript: hrefs and event handlers
 *    that an LLM might embed in Markdown (prompt-injection vector).
 * 2. react-markdown component overrides ensure anchor tags always open in a
 *    new tab with rel="noopener noreferrer" and never execute inline JS.
 */
const SAFE_MD_COMPONENTS: Components = {
    // Never render raw <script> or <style> blocks
    script: () => null,
    style: () => null,
    // Force all links to open safely in a new tab
    a: ({ href, children, ...props }) => {
        const safeHref = href && !/^javascript:/i.test(href) ? href : '#';
        return (
            <a
                href={safeHref}
                target="_blank"
                rel="noopener noreferrer"
                {...props}
            >
                {children}
            </a>
        );
    },
};

function SafeMarkdown({ content }: { content: string }) {
    // DOMPurify is only available in the browser (no SSR window)
    const clean = typeof window !== 'undefined'
        ? DOMPurify.sanitize(content, {
            USE_PROFILES: { html: true },
            FORBID_TAGS: ['script', 'style', 'iframe', 'form', 'input', 'button'],
            FORBID_ATTR: ['onerror', 'onload', 'onclick', 'onmouseover', 'data-*'],
        })
        : content;
    return <ReactMarkdown rehypePlugins={[rehypeSanitize]} components={SAFE_MD_COMPONENTS}>{clean}</ReactMarkdown>;
}

interface ChatInterfaceProps {
    tripId?: string;
}

// Dynamic Greetings based on time of day
const getGreeting = () => {
    const hour = new Date().getHours();
    const greetings = [
        "Ready to explore the world? 🌍",
        "Where to next? ✈️",
        "Let's plan your dream trip! ✨",
        "Adventure awaits! 🏔️"
    ];

    let timeGreeting = "Good morning";
    if (hour >= 12 && hour < 17) timeGreeting = "Good afternoon";
    if (hour >= 17) timeGreeting = "Good evening";

    const randomSplash = greetings[Math.floor(Math.random() * greetings.length)];

    return `${timeGreeting}! ${randomSplash}\n\nI'm your AI travel buddy. Tell me about your dream destination, budget, or vibe, and I'll handle the rest!`;
};

export function ChatInterface({ tripId }: ChatInterfaceProps) {
    const [input, setInput] = useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const [statusVisible, setStatusVisible] = useState(false);
    const abortControllerRef = useRef<AbortController | null>(null);
    const [isSavedAsTrip, setIsSavedAsTrip] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const {
        messages,
        isStreaming,
        currentAgent,
        currentStatus,
        isUploadingImage,
        isVerifyingLocation,
        extractedLocation,
        addMessage,
        appendToLastMessage,
        setStreaming,
        setAgentStatus,
        updateLastMessageData,
        setUploadingImage,
        setExtractedLocation,
        setVerifyingLocation
    } = useChatStore();

    // Local state to hold temporary data for the *current* streaming message
    const [currentStreamData, setCurrentStreamData] = useState<{
        restaurants?: Restaurant[];
        itinerary?: any;
        destination_suggestions?: DestinationSuggestion[];
    }>({});

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, currentStreamData]);

    useEffect(() => {
        setStatusVisible(Boolean(currentStatus));
    }, [currentStatus]);

    // Initial Greeting
    useEffect(() => {
        if (messages.length === 0) {
            addMessage({
                id: 'greeting',
                role: 'assistant',
                content: getGreeting(),
                timestamp: new Date()
            });
        }
    }, [messages.length, addMessage]);

    const handleStop = () => {
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
            abortControllerRef.current = null;
        }
        setStreaming(false);
        setAgentStatus('', '');
        appendToLastMessage('\n\n_[Stream stopped]_');
    };

    const handleSaveAsTrip = async () => {
        if (!tripId || isSavedAsTrip || isSaving) return;
        setIsSaving(true);
        try {
            await api.saveConversationAsTrip(tripId);
            setIsSavedAsTrip(true);
            toast.success('Saved as trip! View it on your Trips page.');
        } catch (error) {
            toast.error('Failed to save as trip. Please try again.');
        } finally {
            setIsSaving(false);
        }
    };

    const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        e.target.value = ''; // allow uploading the same file again

        setUploadingImage(true);
        toast.info("Analyzing screenshot...", { duration: 5000 });

        try {
            const bitmap = await createImageBitmap(file);
            const canvas = document.createElement('canvas');
            const MAX_WIDTH = 1024;
            const MAX_HEIGHT = 1024;
            let width = bitmap.width;
            let height = bitmap.height;

            if (width > height) {
                if (width > MAX_WIDTH) { height *= MAX_WIDTH / width; width = MAX_WIDTH; }
            } else {
                if (height > MAX_HEIGHT) { width *= MAX_HEIGHT / height; height = MAX_HEIGHT; }
            }
            canvas.width = width;
            canvas.height = height;
            const ctx = canvas.getContext('2d');
            ctx?.drawImage(bitmap, 0, 0, width, height);

            const base64Url = canvas.toDataURL('image/jpeg', 0.8);

            const data = await analyzeScreenshot(base64Url);

            if (data.detected_location && data.status === "success") {
                toast.success("Location identified!");
                setExtractedLocation(data.detected_location);
                setVerifyingLocation(true);
            } else {
                toast.error("Vision AI could not identify a specific location in this image.");
            }
        } catch (error: any) {
            toast.error(error.friendlyMessage || "Failed to analyze image");
            console.error("Screenshot analysis error:", error);
        } finally {
            setUploadingImage(false);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isStreaming) return;

        const userMessage = input.trim();
        setInput('');
        setCurrentStreamData({}); // Reset stream data

        const userMessageId = Date.now().toString();
        const assistantMessageId = (Date.now() + 1).toString();

        addMessage({
            id: userMessageId,
            role: 'user',
            content: userMessage,
            timestamp: new Date()
        });

        addMessage({
            id: assistantMessageId,
            role: 'assistant',
            content: '',
            timestamp: new Date(),
            // Optimistic UI state
            status: 'pending'
        });

        setStreaming(true);
        setStatusVisible(true);
        setAgentStatus('System', 'Connecting... 🔄');
        abortControllerRef.current = new AbortController();

        try {
            await streamRequest(
                '/chat/stream',
                { message: userMessage, trip_id: tripId },
                (event: StreamEvent) => {
                    switch (event.type) {
                        case 'token':
                            if (event.content) {
                                appendToLastMessage(event.content);
                            }
                            break;
                        case 'status':
                            setAgentStatus(event.agent || '', event.status || '');
                            break;
                        case 'data':
                            if (event.data_type === 'restaurants' && Array.isArray(event.data)) {
                                updateLastMessageData({ restaurants: event.data });
                                setCurrentStreamData(prev => ({
                                    ...prev,
                                    restaurants: event.data as Restaurant[]
                                }));
                            }
                            if (event.data_type === 'destination_suggestions' && Array.isArray(event.data)) {
                                updateLastMessageData({ destination_suggestions: event.data });
                                setCurrentStreamData(prev => ({
                                    ...prev,
                                    destination_suggestions: event.data as DestinationSuggestion[]
                                }));
                            }
                            break;
                        case 'done':
                            setAgentStatus('', '');
                            break;
                        case 'cancelled':
                            appendToLastMessage('\n\n_[Request cancelled]_');
                            break;
                        case 'error':
                            appendToLastMessage(`\n\n⚠️ Error: ${event.error}`);
                            setAgentStatus('', '');
                            break;
                    }
                },
                abortControllerRef.current?.signal,
                3 // maxRetries
            );
        } catch (error: any) {
            setAgentStatus('', '');
            if (error instanceof ApiError) {
                if (error.status === 422) {
                    // FE3: surface 422 field-level validation errors explicitly
                    let detail = 'Your message was rejected by the server.';
                    try { detail = JSON.parse(error.message)?.[0]?.msg ?? detail; } catch { /* ignore */ }
                    toast.error(`Validation error: ${detail}`);
                    appendToLastMessage(`\n\n⚠️ ${detail}`);
                } else {
                    appendToLastMessage(`\n\n⚠️ Error: ${error.friendlyMessage || error.message}`);
                    toast.error(error.friendlyMessage || 'Server error');
                }
            } else if (error instanceof Error && error.name !== 'AbortError') {
                appendToLastMessage('\n\n⚠️ Connection lost. Could not recover stream after retries.');
                toast.error('Network error during generation');
            }
        } finally {
            setStreaming(false);
            setAgentStatus('', '');
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
        <div className="flex flex-col h-full bg-slate-900 relative overflow-hidden">
            {/* Background enhancement */}
            <div className="absolute inset-0 bg-gradient-to-br from-indigo-900/20 via-purple-900/20 to-slate-900/50 pointer-events-none" />

            {/* Verification Modal */}
            {isVerifyingLocation && extractedLocation && (
                <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in zoom-in-95 duration-200">
                    <div className="bg-slate-800 border border-white/10 p-6 rounded-2xl max-w-sm w-full shadow-2xl flex flex-col gap-4">
                        <div className="flex items-start gap-3 text-purple-200">
                            <Sparkles className="w-5 h-5 flex-shrink-0 mt-0.5" />
                            <div>
                                <h3 className="font-semibold text-white">Location Detected</h3>
                                <p className="text-sm opacity-80 mt-1">We found <strong className="text-white">{extractedLocation}</strong> in your screenshot.</p>
                            </div>
                        </div>
                        <div className="flex flex-col gap-2 mt-2">
                            <button
                                onClick={() => {
                                    setVerifyingLocation(false);
                                    setInput(`Please plan a trip for me visiting: ${extractedLocation}`);
                                    setTimeout(() => {
                                        const syntheticEvent = { preventDefault: () => { } } as React.FormEvent;
                                        handleSubmit(syntheticEvent);
                                    }, 100);
                                }}
                                className="w-full px-4 py-2.5 bg-purple-600 hover:bg-purple-500 rounded-xl text-white font-medium transition-colors"
                            >
                                Confirm & Plan Trip
                            </button>
                            <button
                                onClick={() => {
                                    setVerifyingLocation(false);
                                    setInput(extractedLocation || '');
                                }}
                                className="w-full px-4 py-2.5 bg-white/5 hover:bg-white/10 rounded-xl text-white transition-colors"
                            >
                                No, Let Me Edit
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Save as Trip Button - shown when there's an active conversation */}
            {tripId && (
                <div className="absolute top-3 right-4 z-20">
                    <button
                        onClick={handleSaveAsTrip}
                        disabled={isSavedAsTrip || isSaving}
                        aria-label={isSavedAsTrip ? 'Conversation saved as trip' : 'Save conversation as trip'}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium transition-all duration-200 ${isSavedAsTrip
                            ? 'bg-green-500/20 text-green-400 border border-green-500/30 cursor-default'
                            : 'bg-white/10 hover:bg-white/20 text-white/70 hover:text-white border border-white/10'
                            }`}
                    >
                        {isSaving ? (
                            <Loader2 className="w-3 h-3 animate-spin" />
                        ) : isSavedAsTrip ? (
                            <CheckCircle className="w-3 h-3" />
                        ) : (
                            <Save className="w-3 h-3" />
                        )}
                        {isSavedAsTrip ? 'Saved as Trip' : isSaving ? 'Saving...' : 'Save as Trip'}
                    </button>
                </div>
            )}

            {/* Status Bar */}
            <div className={`absolute top-0 left-0 right-0 z-10 transform transition-all duration-300 ${statusVisible ? 'translate-y-0 opacity-100' : '-translate-y-full opacity-0'}`}>
                <div className="bg-slate-800/90 backdrop-blur-md border-b border-white/5 py-2 px-4 flex items-center justify-center gap-2 text-xs text-purple-200">
                    {currentAgent && getAgentIcon(currentAgent)}
                    <span className="font-medium">{currentAgent}</span>
                    <span className="opacity-70 mx-1">•</span>
                    <span>{currentStatus}</span>
                    <Loader2 className="w-3 h-3 animate-spin ml-1 opacity-70" />
                </div>
            </div>

            {/* Messages — role=log + aria-live lets screen readers announce new AI tokens */}
            <div
                role="log"
                aria-live="polite"
                aria-label="Chat messages"
                className="flex-1 overflow-y-auto p-4 space-y-6 chat-container relative z-0"
            >
                {/* FE5: Empty state — shown only when the only message is the initial greeting */}
                {messages.length === 1 && messages[0].id === 'greeting' && (
                    <div className="flex flex-col items-center justify-center h-full gap-6 pb-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                        <div className="flex items-center gap-2 text-purple-300/70 text-sm">
                            <Sparkles className="w-4 h-4" />
                            <span>Try one of these to get started</span>
                        </div>
                        <div className="flex flex-col gap-2 w-full max-w-sm">
                            {[
                                'Plan a 5-day trip to Goa on ₹30,000',
                                'Best places to visit in Rajasthan in December',
                                'Suggest a solo backpacking route through Northeast India',
                            ].map((suggestion) => (
                                <button
                                    key={suggestion}
                                    onClick={() => {
                                        setInput(suggestion);
                                        // Wait a tick for state to update, then submit
                                        setTimeout(() => {
                                            const syntheticEvent = { preventDefault: () => { } } as React.FormEvent;
                                            handleSubmit(syntheticEvent);
                                        }, 10);
                                    }}
                                    className="text-left px-4 py-3 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 hover:border-purple-500/30 text-white/70 hover:text-white text-sm transition-all duration-200"
                                >
                                    {suggestion}
                                </button>
                            ))}
                        </div>
                    </div>
                )}
                {messages.map((message, idx) => (
                    <div key={message.id}>
                        <MessageBubble message={message} onPickDestination={(city) => {
                            setInput(city);
                            setTimeout(() => {
                                const syntheticEvent = { preventDefault: () => { } } as React.FormEvent;
                                handleSubmit(syntheticEvent);
                            }, 10);
                        }} />
                    </div>
                ))}

                {isStreaming && (
                    <div className="flex justify-start ml-2">
                        <span className="animate-pulse text-purple-400 text-xs">●</span>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <form onSubmit={handleSubmit} className="p-4 border-t border-white/5 bg-slate-900/50 backdrop-blur-md relative z-10">
                <div className="flex gap-2 max-w-4xl mx-auto">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Type your travel dreams..."
                        aria-label="Type your travel message"
                        disabled={isStreaming}
                        className="flex-1 px-5 py-3.5 bg-white/5 border border-white/10 rounded-2xl text-white placeholder-white/30 focus:outline-none focus:ring-1 focus:ring-purple-500/50 focus:bg-white/10 transition-all font-light"
                    />

                    <input
                        type="file"
                        accept="image/png, image/jpeg, image/jpg, image/webp"
                        className="hidden"
                        ref={fileInputRef}
                        onChange={handleImageUpload}
                    />
                    <button
                        type="button"
                        onClick={() => fileInputRef.current?.click()}
                        disabled={isStreaming || isUploadingImage}
                        title="Upload Screenshot"
                        className="px-4 py-3.5 bg-purple-500/10 hover:bg-purple-500/20 border border-purple-500/30 rounded-2xl text-purple-400 transition-all flex items-center justify-center disabled:opacity-50 hover:scale-105"
                    >
                        {isUploadingImage ? <Loader2 className="w-5 h-5 animate-spin" /> : <ImageIcon className="w-5 h-5" />}
                    </button>

                    {isStreaming ? (
                        <button
                            type="button"
                            onClick={handleStop}
                            className="px-6 py-3.5 bg-red-500/10 hover:bg-red-500/20 border border-red-500/50 rounded-2xl text-red-400 transition-all flex items-center gap-2"
                        >
                            <span className="text-xs font-bold uppercase tracking-wider">Stop</span>
                        </button>
                    ) : (
                        <button
                            type="submit"
                            disabled={!input.trim()}
                            aria-label="Send message"
                            className="px-5 py-3.5 bg-white text-slate-900 rounded-2xl font-medium hover:bg-purple-50 hover:scale-105 disabled:opacity-50 disabled:scale-100 disabled:hover:bg-white transition-all duration-200"
                        >
                            <Send className="w-5 h-5" aria-hidden="true" />
                        </button>
                    )}
                </div>
            </form>
        </div>
    );
}

function MessageBubble({ message, onPickDestination }: { message: ChatMessage; onPickDestination?: (city: string) => void }) {
    const isUser = message.role === 'user';
    const hasContent = message.content && message.content.trim().length > 0;
    const hasData = !!message.data;

    if (!hasContent && !hasData && !isUser) return null;

    return (
        <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} group`}>
            {/* Avatar for assistant */}
            {!isUser && (
                <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-purple-500 to-indigo-500 flex items-center justify-center flex-shrink-0 mr-3 mt-1 shadow-lg shadow-purple-500/20">
                    <Plane className="w-4 h-4 text-white" />
                </div>
            )}

            <div className="flex flex-col gap-1 max-w-[85%] sm:max-w-[75%]">
                <div
                    className={`px-5 py-3.5 rounded-2xl shadow-sm flex flex-col gap-3 ${isUser
                        ? 'bg-white text-slate-900 rounded-tr-sm'
                        : 'bg-white/5 border border-white/5 text-slate-200 rounded-tl-sm backdrop-blur-sm'
                        }`}
                >
                    {hasContent && (
                        <div className="prose prose-invert prose-sm max-w-none prose-p:leading-relaxed prose-headings:text-purple-200 prose-strong:text-purple-100 prose-ul:my-2 prose-li:my-0.5">
                            {/* SafeMarkdown sanitizes AI output via DOMPurify before rendering — XSS fix S3 */}
                            <SafeMarkdown content={message.content} />
                        </div>
                    )}

                    {/* Rich Data UI Rendering directly from message properties */}
                    {!isUser && message.data && (message.data as any).restaurants && (
                        <div className="flex flex-wrap gap-2 animate-in fade-in slide-in-from-bottom-2">
                            {(message.data as any).restaurants.slice(0, 3).map((r: Restaurant, i: number) => (
                                <RestaurantCard key={`saved-${message.id}-${i}`} restaurant={r} />
                            ))}
                        </div>
                    )}
                    {/* Destination suggestion cards */}
                    {!isUser && message.data && (message.data as any).destination_suggestions && (
                        <DestinationSuggestionCards
                            suggestions={(message.data as any).destination_suggestions as DestinationSuggestion[]}
                            onPick={(city) => onPickDestination?.(city)}
                        />
                    )}
                </div>
                {/* FE4: AI disclaimer — surfaced beneath every assistant reply */}
                {!isUser && (
                    <p className="text-white/25 text-[10px] px-1 leading-tight">
                        AI responses may be inaccurate. Verify important travel details independently.
                    </p>
                )}
            </div>
        </div>
    );
}

export default ChatInterface;

