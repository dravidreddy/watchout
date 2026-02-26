'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { Send, Loader2, ArrowLeft, Sparkles, MapPin, Route, Cloud, CheckCircle, History, Image as ImageIcon, Pencil, Trash2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import Link from 'next/link';
import { useChatStore, ChatMessage, useMoodStore } from '@/lib/store';
import { streamRequest, StreamEvent, api, analyzeScreenshot } from '@/lib/api';
import { useAuth } from '@/components/auth/AuthProvider';
import { useRouter, useSearchParams } from 'next/navigation';
import { toast } from 'sonner';
import { ItineraryModal } from '@/components/chat/ItineraryModal';
import { ChatHistory } from '@/components/chat/ChatHistory';
import { ConfirmationCard } from '@/components/chat/ConfirmationCard';

// Streaming status stages
const streamingStages = [
    { id: 'clarify', label: 'Clarifying preferences', icon: Sparkles },
    { id: 'build', label: 'Building itinerary', icon: MapPin },
    { id: 'routes', label: 'Computing routes', icon: Route },
    { id: 'weather', label: 'Checking weather', icon: Cloud },
    { id: 'finalize', label: 'Finalizing', icon: CheckCircle },
];

export default function ChatPage() {
    const { user } = useAuth();
    const { currentMood } = useMoodStore();
    const router = useRouter();
    const searchParams = useSearchParams();
    const [input, setInput] = useState('');
    const [currentStage, setCurrentStage] = useState<string | null>(null);
    const [isSaving, setIsSaving] = useState(false);
    const [savedTripId, setSavedTripId] = useState<string | null>(null);
    const [showItineraryModal, setShowItineraryModal] = useState(false);
    const [showChatHistory, setShowChatHistory] = useState(false);
    const [pendingConfirmation, setPendingConfirmation] = useState<Record<string, any> | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const hasGreeted = useRef(false);
    const hasAutoSaved = useRef(false);
    const isExplicitNewChat = useRef(false);

    const {
        messages,
        isStreaming,
        currentAgent,
        currentStatus,
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
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    // Open Chat History on hard refresh if no chat is active
    useEffect(() => {
        if (!hasGreeted.current && messages.length === 0 && !isExplicitNewChat.current && !searchParams.get('trip_id')) {
            // Delay slightly to avoid unmounted flicker
            const timer = setTimeout(() => setShowChatHistory(true), 100);
            return () => clearTimeout(timer);
        }
    }, [messages.length, searchParams]);

    // Handle URL query params
    useEffect(() => {
        const isNew = searchParams.get('new') === 'true';
        const urlTripId = searchParams.get('trip_id');

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
        } else if (urlTripId && urlTripId !== useChatStore.getState().activeTripId) {
            // User navigated directly to a specific chat
            handleSelectConversation(urlTripId).then(() => {
                // Optionally remove the query param 
                router.replace('/chat');
            });
        }
    }, [searchParams, router, setActiveTripId, setMessages, setExtractedItinerary]);

    // ... (keep existing useEffects) ...

    const handleSelectConversation = async (tripId: string) => {
        try {
            // Close sidebar on mobile
            if (window.innerWidth < 768) {
                setShowChatHistory(false);
            }

            // If clicking the current trip, just close
            if (tripId === useChatStore.getState().activeTripId) {
                return;
            }

            // Set loading state if needed?

            // Fetch full trip details including messages
            const trip = await api.getTrip(tripId);

            // Update store
            setActiveTripId(tripId);

            // Load messages if they exist in the trip object (need to ensure backend returns them)
            // The current getTrip endpoint returns the Trip document. 
            // We might need to fetch messages separately if they aren't embedded.
            // For now, let's assume we need to fetch messages.
            // Wait, the backend getTrip doesn't return messages.
            // We need a way to get messages for a trip. 
            // Let's use listConversations to get the preview, but for full chat we need an endpoint.
            // Actually, we can just fetch the messages endpoint if it existed. 
            // Since it doesn't, let's look at the backend... 
            // The backend `get_trip` returns the trip doc. 
            // The `stream_chat` endpoint loads context from `db.messages`.
            // We need an endpoint to `GET /chat/messages/{trip_id}`.

            // TEMPORARY: Since we don't have a direct "get messages" endpoint, 
            // and `listConversations` only gives the last message,
            // we will need to implement a specialized endpoint or use what we have.
            // However, for now, let's try to fetch the trip and maybe the user can continue the chat.
            // But they won't see history. This is a blocker.

            // WAIT! The user asked to "show that chat history". 
            // I should assume I need to fetch it.
            // I'll add a call to `api.getTripMessages(tripId)` which I'll implement in api.ts next.

            const messages = await api.getTripMessages(tripId);

            // Transform to ChatMessage format
            const chatMessages = messages.map((msg: any) => ({
                id: msg._id || Date.now().toString(),
                role: msg.role,
                content: msg.content,
                timestamp: new Date(msg.created_at)
            }));

            setMessages(chatMessages);

            // If the trip has an itinerary, load it too
            if (trip.itinerary) {
                setExtractedItinerary(trip.itinerary);
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
        setInput('');

        addMessage({
            id: Date.now().toString(),
            role: 'user',
            content: userMessage,
            timestamp: new Date()
        });

        addMessage({
            id: (Date.now() + 1).toString(),
            role: 'assistant',
            content: '',
            timestamp: new Date()
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
                trip_id: useChatStore.getState().activeTripId,
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
                        // Map status to stage
                        if (event.status?.toLowerCase().includes('route')) {
                            setCurrentStage('routes');
                        } else if (event.status?.toLowerCase().includes('weather')) {
                            setCurrentStage('weather');
                        } else if (event.status?.toLowerCase().includes('hotels')) {
                            setCurrentStage('hotels');
                        } else if (event.status?.toLowerCase().includes('plan')) {
                            setCurrentStage('build');
                        }
                        break;
                    case 'itinerary':
                        if (event.itinerary) {
                            setExtractedItinerary(event.itinerary);
                        }
                        break;
                    case 'data':
                        if (event.data_type === 'weather' && event.data) {
                            useChatStore.getState().setWeatherData(event.data);
                        } else if (event.data_type === 'itinerary' && event.data) {
                            setExtractedItinerary(event.data);
                            // Auto-open the itinerary panel as soon as it's ready
                            setSavedTripId(useChatStore.getState().activeTripId || '');
                            setShowItineraryModal(true);
                        } else if (event.data_type === 'confirmation_required' && event.data) {
                            // Phase 4: show confirmation card
                            setPendingConfirmation(event.data as Record<string, any>);
                        }
                        break;
                    case 'tool_start':
                        // console.log('Tool started:', event.content);
                        break;
                    case 'done':
                        setAgentStatus('', '');
                        setCurrentStage(null);
                        if (event.trip_id) {
                            useChatStore.getState().setActiveTripId(event.trip_id);
                        }
                        break;
                    case 'error':
                        console.error('Stream error:', event.error);
                        break;
                }
            });
        } catch (error: any) {
            console.error('Chat error:', error);
            // Remove the empty assistant message on error
            useChatStore.setState(state => ({
                messages: state.messages.filter(m => m.id !== (Date.now() + 1).toString())
            }));

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

    const handleSaveTrip = async () => {
        setIsSaving(true);
        try {
            const tripData = {
                title: extractedItinerary?.title || "New Trip Plan",
                cities: extractedItinerary?.cities || ["Planned Destination"],
                num_days: extractedItinerary?.num_days || 5,
                num_travelers: extractedItinerary?.num_travelers || 1,
                start_date: extractedItinerary?.start_date,
                end_date: extractedItinerary?.end_date,
                budget_total: extractedItinerary?.budget_total,
                itinerary: extractedItinerary?.days ? {
                    days: extractedItinerary.days,
                    total_estimated_cost: extractedItinerary.budget_total
                } : undefined
            };

            const response = await api.createTrip(tripData);
            setSavedTripId(response.trip_id);

            toast.success('Trip saved! You can now export or share it.');
        } catch (error: any) {
            console.error('Failed to save trip:', error);
            if (error?.status === 403 || error?.message?.toLowerCase().includes('limit')) {
                toast.error('Free tier limit reached. Redirecting to plans...');
                setTimeout(() => router.push('/plans'), 2000);
            } else {
                toast.error('Failed to save trip. Please try again.');
            }
        } finally {
            setIsSaving(false);
        }
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
        <div className="flex flex-col h-[calc(100vh-4rem)] md:h-screen md:flex-row relative">
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
                currentTripId={useChatStore.getState().activeTripId || undefined}
            />

            {/* Chat Section */}
            <div className="flex flex-col flex-1 md:w-[40%] md:min-w-[400px] md:border-r" style={{ borderColor: 'rgba(0,0,0,0.05)' }}>
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
                    <button
                        onClick={() => setShowChatHistory(!showChatHistory)}
                        className={`p-2 rounded-lg transition-colors ${showChatHistory ? 'bg-accent text-white' : 'hover:bg-black/5'} z-50`}
                        title="Chat History"
                    >
                        <History className="w-5 h-5" />
                    </button>
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
                <div className="flex-1 overflow-y-auto p-4 space-y-4" style={{ background: 'var(--bg-primary)' }}>
                    {messages.map((message) => (
                        <MessageBubble
                            key={message.id}
                            message={message}
                            tripId={useChatStore.getState().activeTripId}
                            onDelete={(id) => setMessages(messages.filter(m => m.id !== id))}
                            onEdit={(id, content) => setMessages(messages.map(m => m.id === id ? { ...m, content } : m))}
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

                    <div ref={messagesEndRef} />
                </div>

                {/* Quick Actions */}
                <div className="flex gap-2 px-4 py-2 overflow-x-auto hide-scrollbar" style={{ borderTop: '1px solid rgba(0,0,0,0.05)' }}>
                    {quickActions.map((action) => (
                        <button
                            key={action.label}
                            onClick={() => handleQuickAction(action.label)}
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm whitespace-nowrap transition-colors hover:bg-black/5"
                            style={{
                                background: 'var(--bg-secondary)',
                                color: 'var(--text-secondary)',
                                border: '1px solid rgba(0,0,0,0.05)'
                            }}
                        >
                            <span>{action.icon}</span>
                            <span>{action.label}</span>
                        </button>
                    ))}
                </div>

                {/* Input */}
                <form
                    onSubmit={handleSubmit}
                    className="p-4"
                    style={{
                        background: 'var(--bg-secondary)',
                        borderTop: '1px solid rgba(0,0,0,0.05)'
                    }}
                >
                    <div className="flex items-center gap-2">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Tell me about your dream trip..."
                            disabled={isStreaming}
                            className="flex-1 px-4 py-3 rounded-xl transition-all"
                            style={{
                                background: 'var(--bg-primary)',
                                border: '1px solid rgba(0,0,0,0.05)',
                                color: 'var(--text-primary)'
                            }}
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
                            className="p-3 mr-1 rounded-xl text-purple-500 bg-purple-500/10 border border-purple-500/20 hover:bg-purple-500/20 transition-all disabled:opacity-50"
                        >
                            {isUploadingImage ? <Loader2 className="w-5 h-5 animate-spin" /> : <ImageIcon className="w-5 h-5" />}
                        </button>
                        <button
                            type="submit"
                            disabled={isStreaming || !input.trim()}
                            className="p-3 rounded-xl text-white transition-all disabled:opacity-50"
                            style={{
                                background: 'var(--accent)',
                            }}
                        >
                            {isStreaming ? (
                                <Loader2 className="w-5 h-5 animate-spin" />
                            ) : (
                                <Send className="w-5 h-5" />
                            )}
                        </button>
                    </div>
                </form>
            </div>

            {/* Itinerary Modal — show as soon as the itinerary is generated */}
            {(savedTripId || extractedItinerary) && (
                <ItineraryModal
                    isOpen={showItineraryModal}
                    onClose={() => setShowItineraryModal(false)}
                    itinerary={extractedItinerary}
                    weatherData={weatherData}
                    tripId={savedTripId || useChatStore.getState().activeTripId || ''}
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

function MessageBubble({ message, tripId, onDelete, onEdit }: {
    message: ChatMessage;
    tripId?: string | null;
    onDelete?: (id: string) => void;
    onEdit?: (id: string, newContent: string) => void;
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
            className={`flex ${isUser ? 'justify-end' : 'justify-start'} animate-slide-in-up group`}
            onMouseEnter={() => setHovered(true)}
            onMouseLeave={() => setHovered(false)}
        >
            {!isUser && (
                <div
                    className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 mr-2 mt-1"
                    style={{ background: 'var(--accent-50)' }}
                >
                    <Sparkles className="w-4 h-4" style={{ color: 'var(--accent)' }} />
                </div>
            )}

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
                            <ReactMarkdown>{message.content || '...'}</ReactMarkdown>
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
}

