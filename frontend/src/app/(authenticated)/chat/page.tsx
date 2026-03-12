'use client';

import { useState, useRef, useEffect, useCallback, memo } from 'react';
import { Send, Loader2, ArrowLeft, Sparkles, MapPin, History, Image as ImageIcon, Pencil, Trash2 } from 'lucide-react';
import Link from 'next/link';
import { useChatStore, ChatMessage, useMoodStore } from '@/lib/store';
import { streamRequest, StreamEvent, api, analyzeScreenshot } from '@/lib/api';
import { useAuth } from '@/components/auth/AuthProvider';
import { useRouter, useSearchParams } from 'next/navigation';
import { toast } from 'sonner';
import { ItineraryModal } from '@/components/chat/ItineraryModal';
import { ChatHistory } from '@/components/chat/ChatHistory';
import { ConfirmationCard } from '@/components/chat/ConfirmationCard';
import { MarkdownRenderer } from '@/components/chat/MarkdownRenderer';
import { normalizeItinerary } from '@/lib/itinerary';

const STREAM_ERROR_FALLBACK = 'Sorry, something went wrong while generating your plan. Please try again.';

const sanitizeStreamError = (value?: string): string => {
    const text = (value || '').trim();
    if (!text) return STREAM_ERROR_FALLBACK;

    const looksInternal = /traceback|exception|stack|line \d+|file\s+\"|sql|mongodb|fastapi/i.test(text);
    if (looksInternal) return STREAM_ERROR_FALLBACK;

    return text.length > 180 ? `${text.slice(0, 177)}...` : text;
};

export default function ChatPage() {
    const { user } = useAuth();
    const { currentMood } = useMoodStore();
    const router = useRouter();
    const searchParams = useSearchParams();
    const [input, setInput] = useState('');
    const [savedTripId, setSavedTripId] = useState<string | null>(null);
    const [showItineraryModal, setShowItineraryModal] = useState(false);
    const [showChatHistory, setShowChatHistory] = useState(false);
    const [pendingConfirmation, setPendingConfirmation] = useState<Record<string, any> | null>(null);
    const messagesContainerRef = useRef<HTMLDivElement>(null);
    const shouldAutoScrollRef = useRef(true);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const hasGreeted = useRef(false);
    const isExplicitNewChat = useRef(false);

    const {
        messages,
        isStreaming,
        currentStatus,
        activeTripId,
        addMessage,
        appendToLastMessage,
        setStreaming,
        setAgentStatus,
        setExtractedItinerary,
        extractedItinerary,
        weatherData,
        setMessages,
        setActiveTripId,
        isUploadingImage,
        isVerifyingLocation,
        extractedLocation,
        setUploadingImage,
        setExtractedLocation,
        setVerifyingLocation
    } = useChatStore();

    useEffect(() => {
        const container = messagesContainerRef.current;
        if (!container) return;

        if (shouldAutoScrollRef.current || isStreaming) {
            container.scrollTo({
                top: container.scrollHeight,
                behavior: isStreaming ? 'auto' : 'smooth',
            });
        }
    }, [messages, isStreaming]);

    const handleMessagesScroll = () => {
        const container = messagesContainerRef.current;
        if (!container) return;
        const distanceFromBottom = container.scrollHeight - container.scrollTop - container.clientHeight;
        shouldAutoScrollRef.current = distanceFromBottom < 120;
    };

    // Open Chat History on hard refresh if no chat is active
    useEffect(() => {
        if (!hasGreeted.current && messages.length === 0 && !isExplicitNewChat.current && !searchParams.get('trip_id')) {
            // Delay slightly to avoid unmounted flicker
            hasGreeted.current = true;
            const timer = setTimeout(() => setShowChatHistory(true), 100);
            return () => clearTimeout(timer);
        }
    }, [messages.length, searchParams]);

    // Handle URL query params
    useEffect(() => {
        const isNew = searchParams.get('new') === 'true';
        const urlTripId = searchParams.get('trip_id');
        const queryParam = searchParams.get('q');

        if (isNew) {
            isExplicitNewChat.current = true;

            // Close any open sidebars
            setShowChatHistory(false);

            // Clear all chat store state
            setActiveTripId(null);
            setMessages([]);
            setExtractedItinerary(null);
            setSavedTripId(null);
            setInput('');

            // Remove the query param from the URL without triggering a reload
            router.replace('/chat');
        } else if (queryParam && messages.length === 0) {
            // Auto-send the query from the home search bar (C6)
            isExplicitNewChat.current = true;
            setShowChatHistory(false);
            setInput(queryParam);
            router.replace('/chat');
            const t = setTimeout(() => sendMessage(queryParam), 400);
            return () => clearTimeout(t);
        } else if (urlTripId && urlTripId !== activeTripId) {
            // User navigated directly to a specific chat
            handleSelectConversation(urlTripId).then(() => {
                // Optionally remove the query param 
                router.replace('/chat');
            });
        }
    }, [searchParams, router, setActiveTripId, setMessages, setExtractedItinerary, activeTripId]);

    // ... (keep existing useEffects) ...

    const handleSelectConversation = async (tripId: string) => {
        try {
            // Close sidebar on mobile
            if (window.innerWidth < 768) {
                setShowChatHistory(false);
            }

            // If clicking the current trip, just close
            if (tripId === activeTripId) {
                return;
            }

            // Set loading state if needed?

            // Fetch full trip details including messages
            const trip = await api.getTrip(tripId);

            // Update store
            setActiveTripId(tripId);

            const messages = await api.getTripMessages(tripId);

            // Transform to ChatMessage format
            const chatMessages = messages.map((msg: any) => ({
                id: msg._id || Date.now().toString(),
                role: msg.role,
                content: typeof msg.content === 'string' ? msg.content : '',
                timestamp: new Date(msg.created_at)
            }));

            setMessages(chatMessages);

            // If the trip has an itinerary, load it too
            if (trip.itinerary) {
                setExtractedItinerary(normalizeItinerary(trip.itinerary));
            } else {
                setExtractedItinerary(null);
            }

        } catch (error) {
            console.error('Failed to load conversation:', error);
            toast.error('Failed to load conversation');
        }
    };

    const handleNewChat = () => {
        // Clear all state to start a fresh chat
        setActiveTripId(null);
        setMessages([]);
        setExtractedItinerary(null);
        setSavedTripId(null);
        setInput('');
        setShowChatHistory(false);
    };

    const sendMessage = async (text: string) => {
        if (!text.trim() || isStreaming) return;

        const userMessage = text.trim();
        const now = Date.now();
        const userMessageId = `${now}-user`;
        const assistantMessageId = `${now}-assistant`;
        setInput('');
        shouldAutoScrollRef.current = true;
        setPendingConfirmation(null);

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
            status: 'pending'
        });

        setStreaming(true);

        // Build profile context from user preferences + current mood
        const profileContext = {
            name: user?.name,
            travel_style: user?.preferences?.travel_style,
            budget_range: user?.preferences?.budget_range,
            food_preferences: user?.preferences?.food_preferences,
            interests: user?.preferences?.interests,
            current_mood: currentMood ?? user?.preferences?.current_mood,
            travel_vibe: user?.preferences?.travel_vibe,
        };
        // Remove null/undefined fields
        const cleanProfile = Object.fromEntries(
            Object.entries(profileContext).filter(([, v]) => v != null && v !== '')
        );

        try {
            await streamRequest('/chat/stream', {
                message: userMessage,
                trip_id: activeTripId,
                trip_context: { preferences: cleanProfile }
            }, (event: StreamEvent) => {
                switch (event.type) {
                    case 'token':
                        if (event.content) {
                            appendToLastMessage(event.content);
                        }
                        break;
                    case 'status':
                        setAgentStatus(event.agent || '', event.status || '');
                        break;
                    case 'itinerary':
                        if (event.itinerary) {
                            setExtractedItinerary(normalizeItinerary(event.itinerary));
                        }
                        break;
                    case 'data':
                        if (event.data_type === 'weather' && event.data) {
                            useChatStore.getState().setWeatherData(event.data);
                        } else if (event.data_type === 'itinerary' && event.data) {
                            const normalized = normalizeItinerary(event.data);
                            setExtractedItinerary(normalized);
                            // Auto-open the itinerary panel as soon as it's ready
                            setSavedTripId(activeTripId || '');
                            setShowItineraryModal(true);
                        } else if (event.data_type === 'confirmation_required' && event.data) {
                            // Phase 4: show confirmation card
                            setPendingConfirmation(event.data as Record<string, any>);
                        }
                        break;
                    case 'tool_start':
                        setAgentStatus('Assistant', 'Working on your plan...');
                        break;
                    case 'tool_end':
                        break;
                    case 'done':
                        setAgentStatus('', '');
                        if (event.trip_id) {
                            useChatStore.getState().setActiveTripId(event.trip_id);
                        }
                        break;
                    case 'cancelled':
                        appendToLastMessage('\n\nRequest cancelled.');
                        toast.error('The current request was cancelled.');
                        break;
                    case 'error':
                        appendToLastMessage(`\n\n⚠️ ${sanitizeStreamError(event.error)}`);
                        toast.error(sanitizeStreamError(event.error));
                        break;
                }
            }, undefined, 0);
        } catch (error: any) {
            console.error('Chat error:', error);
            const fallbackErrorText = '\n\n⚠️ Failed to complete the response. Please retry.';
            useChatStore.setState((state) => {
                const target = state.messages.find((m) => m.id === assistantMessageId);
                if (!target) return state;
                if (target.content?.trim()) {
                    return {
                        messages: state.messages.map((m) =>
                            m.id === assistantMessageId ? { ...m, content: `${m.content}${fallbackErrorText}` } : m
                        ),
                    };
                }
                return {
                    messages: state.messages.filter((m) => m.id !== assistantMessageId),
                };
            });

            if (error?.status === 403 || error?.message?.toLowerCase().includes('limit')) {
                toast.error('Free tier limit reached. Redirecting to plans...');
                setTimeout(() => router.push('/plans'), 2000);
            } else {
                toast.error('Failed to send message. Please try again.');
            }
        } finally {
            setStreaming(false);
            setAgentStatus('', '');
        }
    };

    const handleDeleteMessage = useCallback((id: string) => {
        setMessages((prev) => prev.filter((m) => m.id !== id));
    }, [setMessages]);

    const handleEditMessage = useCallback((id: string, content: string) => {
        setMessages((prev) => prev.map((m) => (m.id === id ? { ...m, content } : m)));
    }, [setMessages]);

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
        await sendMessage(input);
    };

    const handleQuickAction = (label: string) => {
        let text = "";
        switch (label) {
            case 'Refine': text = "Can you refine the itinerary to be more relaxed?"; break;
            case 'Add city': text = "I want to add another city to this trip."; break;
            case 'Optimize': text = "Optimize the route for less travel time."; break;
            case 'Budget': text = "Can you give me a budget estimate for this?"; break;
            default: text = label;
        }
        sendMessage(text);
    };

    // Quick actions
    const quickActions = [
        { label: 'Refine', icon: '✏️' },
        { label: 'Add city', icon: '📍' },
        { label: 'Optimize', icon: '⚡' },
        { label: 'Budget', icon: '💰' },
    ];

    return (
        <div className="flex flex-col h-[calc(100dvh-5rem)] md:h-[calc(100vh-4rem)] overflow-hidden lg:flex-row relative">
            {/* Verification Modal */}
            {isVerifyingLocation && extractedLocation && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in zoom-in-95 duration-200">
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
                                    sendMessage(`Please plan a trip for me visiting: ${extractedLocation}`);
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

            <ChatHistory
                isOpen={showChatHistory}
                onClose={() => setShowChatHistory(false)}
                onSelectConversation={handleSelectConversation}
                onNewChat={handleNewChat}
                currentTripId={activeTripId || undefined}
            />

            {/* Chat Section — full width, centered content */}
            <div className="flex flex-col flex-1" style={{ borderColor: 'rgba(0,0,0,0.05)' }}>
                {/* Header */}
                <header
                    className="flex items-center justify-between px-4 py-3"
                    style={{
                        background: 'var(--bg-secondary)',
                        borderBottom: '1px solid rgba(0,0,0,0.05)'
                    }}
                >
                    <div className="flex items-center gap-3">
                        <Link href="/home" className="md:hidden p-2 -ml-2 rounded-lg hover:bg-black/5">
                            <ArrowLeft className="w-5 h-5" style={{ color: 'var(--text-secondary)' }} />
                        </Link>
                        <div>
                            <h1 className="font-semibold" style={{ color: 'var(--text-primary)' }}>
                                Plan Your Trip
                            </h1>
                            <p className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
                                AI-powered planning
                            </p>
                        </div>
                    </div>
                    {!showChatHistory && (
                        <button
                            onClick={() => setShowChatHistory(!showChatHistory)}
                            className="p-2 rounded-lg transition-colors hover:bg-black/5 z-50"
                            title="Chat History"
                        >
                            <History className="w-5 h-5" />
                        </button>
                    )}
                </header>

                {/* ... (rest of the component) ... */}

                {/* AI Status Bar */}
                {currentStatus && (
                    <div className="ai-status-bar animate-fade-in">
                        <Loader2 className="w-4 h-4 animate-spin" style={{ color: 'var(--accent)' }} />
                        <span className="ai-status-text">{currentStatus}</span>
                    </div>
                )}

                {/* Messages */}
                <div
                    ref={messagesContainerRef}
                    onScroll={handleMessagesScroll}
                    className="flex-1 overflow-y-auto py-6"
                    style={{ background: 'var(--bg-primary)' }}
                >
                    <div className="mx-auto max-w-4xl w-full px-6 space-y-4">
                        {messages.map((message, index) => (
                            <MessageBubble
                                key={message.id}
                                message={message}
                                tripId={activeTripId}
                                groupedWithPrevious={index > 0 && messages[index - 1]?.role === message.role}
                                onDelete={handleDeleteMessage}
                                onEdit={handleEditMessage}
                                isPending={isStreaming && index === messages.length - 1 && message.role === 'assistant' && !message.content.trim()}
                            />
                        ))}

                        {/* Phase 4: Confirmation Card */}
                        {pendingConfirmation && !isStreaming && (
                            <div className="flex justify-start">
                                <ConfirmationCard
                                    data={pendingConfirmation}
                                    onConfirm={() => {
                                        setPendingConfirmation(null);
                                        sendMessage('Yes, everything looks perfect. Please generate my itinerary!');
                                    }}
                                    onEdit={() => {
                                        setPendingConfirmation(null);
                                        setInput('I\'d like to change ');
                                    }}
                                />
                            </div>
                        )}
                    </div>
                </div>

                {/* Floating Island Input Section */}
                <div className="mx-auto max-w-4xl w-full px-6 pb-6">
                    {/* Quick Actions */}
                    <div className="flex gap-2 pb-2 overflow-x-auto hide-scrollbar">
                        {quickActions.map((action) => (
                            <button
                                key={action.label}
                                onClick={() => handleQuickAction(action.label)}
                                className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm whitespace-nowrap transition-all hover:scale-105"
                                style={{
                                    background: 'var(--bg-secondary)',
                                    color: 'var(--text-secondary)',
                                    border: '1px solid rgba(128,128,128,0.15)'
                                }}
                            >
                                <span>{action.icon}</span>
                                <span>{action.label}</span>
                            </button>
                        ))}
                    </div>

                    {/* Input form — floating island */}
                    <form
                        onSubmit={handleSubmit}
                        className="flex items-center gap-2 px-3 py-2.5 rounded-2xl"
                        style={{
                            background: 'var(--bg-secondary)',
                            border: '1px solid rgba(128,128,128,0.18)',
                            boxShadow: '0 8px 32px rgba(0,0,0,0.22), 0 2px 8px rgba(0,0,0,0.12)'
                        }}
                    >
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Tell me about your dream trip..."
                            disabled={isStreaming}
                            className="flex-1 px-3 py-1.5 bg-transparent outline-none text-sm"
                            style={{ color: 'var(--text-primary)' }}
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
                            className="p-2 rounded-xl text-purple-500 bg-purple-500/10 hover:bg-purple-500/20 transition-all disabled:opacity-50 flex-shrink-0"
                        >
                            {isUploadingImage ? <Loader2 className="w-5 h-5 animate-spin" /> : <ImageIcon className="w-5 h-5" />}
                        </button>
                        <button
                            type="submit"
                            disabled={isStreaming || !input.trim()}
                            className="p-2 rounded-xl text-white transition-all disabled:opacity-50 hover:scale-105 flex-shrink-0"
                            style={{ background: 'var(--accent)' }}
                        >
                            {isStreaming ? (
                                <Loader2 className="w-5 h-5 animate-spin" />
                            ) : (
                                <Send className="w-5 h-5" />
                            )}
                        </button>
                    </form>
                </div>
            </div>{/* end Chat Section */}

            {/* Itinerary Modal — show as soon as the itinerary is generated */}
            {(savedTripId || extractedItinerary) && (
                <ItineraryModal
                    isOpen={showItineraryModal}
                    onClose={() => setShowItineraryModal(false)}
                    itinerary={extractedItinerary}
                    weatherData={weatherData}
                    tripId={savedTripId || activeTripId || ''}
                />
            )}

            {/* View Itinerary Button — show whenever there's an itinerary */}
            {(savedTripId || extractedItinerary) && !showItineraryModal && (
                <button
                    onClick={() => setShowItineraryModal(true)}
                    className="fixed bottom-6 right-6 btn btn-primary shadow-lg flex items-center gap-2 z-40 animate-bounce-in"
                >
                    <MapPin className="w-4 h-4" />
                    View Itinerary
                </button>
            )}
        </div>
    );
}

const MessageBubble = memo(function MessageBubble({
    message,
    tripId,
    groupedWithPrevious = false,
    onDelete,
    onEdit,
    isPending = false
}: {
    message: ChatMessage;
    tripId?: string | null;
    groupedWithPrevious?: boolean;
    onDelete?: (id: string) => void;
    onEdit?: (id: string, newContent: string) => void;
    isPending?: boolean;
}) {
    const isUser = message.role === 'user';
    const [hovered, setHovered] = useState(false);
    const [editing, setEditing] = useState(false);
    const [editText, setEditText] = useState(message.content || '');
    const [saving, setSaving] = useState(false);

    const handleDelete = async () => {
        if (!tripId || !message.id) return;
        if (!confirm('Delete this message?')) return;
        try {
            await api.deleteMessage(tripId, message.id);
            onDelete?.(message.id);
            toast.success('Message deleted');
        } catch {
            toast.error('Failed to delete message');
        }
    };

    const handleSaveEdit = async () => {
        if (!tripId || !message.id || !editText.trim()) return;
        setSaving(true);
        try {
            await api.editMessage(tripId, message.id, editText.trim());
            onEdit?.(message.id, editText.trim());
            setEditing(false);
            toast.success('Message updated');
        } catch {
            toast.error('Failed to update message');
        } finally {
            setSaving(false);
        }
    };

    return (
        <div
            className={`flex ${isUser ? 'justify-end' : 'justify-start'} animate-slide-in-up group ${groupedWithPrevious ? 'mt-1' : ''}`}
            onMouseEnter={() => setHovered(true)}
            onMouseLeave={() => setHovered(false)}
        >
            {!isUser && !groupedWithPrevious && (
                <div
                    className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 mr-2 mt-1"
                    style={{ background: 'var(--accent-50)' }}
                >
                    <Sparkles className="w-4 h-4" style={{ color: 'var(--accent)' }} />
                </div>
            )}
            {!isUser && groupedWithPrevious && <div className="w-8 mr-2" aria-hidden="true" />}

            <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} max-w-[80%]`}>
                <div
                    className={`px-4 py-3 rounded-2xl ${isUser ? 'rounded-br-sm' : 'rounded-bl-sm'}`}
                    style={{
                        background: isUser ? 'var(--accent)' : 'var(--bg-secondary)',
                        color: isUser ? 'white' : 'var(--text-primary)',
                        boxShadow: 'var(--shadow-sm)'
                    }}
                >
                    {editing ? (
                        <div className="flex flex-col gap-2 min-w-[200px]">
                            <textarea
                                autoFocus
                                value={editText}
                                onChange={e => setEditText(e.target.value)}
                                className="w-full bg-white/10 text-white rounded-lg px-3 py-2 resize-none text-sm outline-none border border-white/20 focus:border-white/50"
                                rows={3}
                                onKeyDown={e => {
                                    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSaveEdit(); }
                                    if (e.key === 'Escape') setEditing(false);
                                }}
                            />
                            <div className="flex gap-2 justify-end">
                                <button
                                    onClick={() => setEditing(false)}
                                    className="px-3 py-1 text-xs rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
                                >Cancel</button>
                                <button
                                    onClick={handleSaveEdit}
                                    disabled={saving || !editText.trim()}
                                    className="px-3 py-1 text-xs rounded-lg bg-white text-accent font-medium hover:bg-white/90 transition-colors disabled:opacity-50"
                                >
                                    {saving ? 'Saving…' : 'Save'}
                                </button>
                            </div>
                        </div>
                    ) : (
                        <div className={`prose prose-sm max-w-none ${isUser ? 'text-white' : 'prose-travel'}`}>
                            {isPending ? (
                                <div className="flex items-center gap-2 text-sm opacity-80 not-prose">
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    <span>Thinking...</span>
                                </div>
                            ) : (
                                <MarkdownRenderer
                                    content={message.content || '...'}
                                    coerceStructuredContent={!isUser}
                                />
                            )}
                        </div>
                    )}
                </div>

                {/* Hover action bar — only for persisted messages (MongoDB ObjectId = 24 hex chars) */}
                {!editing && hovered && tripId && message.id && /^[a-f\d]{24}$/i.test(message.id) && (
                    <div className={`flex items-center gap-1 mt-1 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
                        {isUser && (
                            <button
                                onClick={() => { setEditText(message.content || ''); setEditing(true); }}
                                title="Edit message"
                                className="p-1.5 rounded-lg hover:bg-black/10 transition-colors text-gray-400 hover:text-blue-500"
                            >
                                <Pencil className="w-3.5 h-3.5" />
                            </button>
                        )}
                        <button
                            onClick={handleDelete}
                            title="Delete message"
                            className="p-1.5 rounded-lg hover:bg-black/10 transition-colors text-gray-400 hover:text-red-500"
                        >
                            <Trash2 className="w-3.5 h-3.5" />
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
});

MessageBubble.displayName = 'MessageBubble';

