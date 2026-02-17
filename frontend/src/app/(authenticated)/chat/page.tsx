'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, ArrowLeft, Sparkles, MapPin, Route, Cloud, CheckCircle, History } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import Link from 'next/link';
import { useChatStore, ChatMessage } from '@/lib/store';
import { streamRequest, StreamEvent, api } from '@/lib/api';
import { useAuth } from '@/components/auth/AuthProvider';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { ItineraryModal } from '@/components/chat/ItineraryModal';
import { ChatHistory } from '@/components/chat/ChatHistory';

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
    const router = useRouter();
    const [input, setInput] = useState('');
    const [currentStage, setCurrentStage] = useState<string | null>(null);
    const [isSaving, setIsSaving] = useState(false);
    const [savedTripId, setSavedTripId] = useState<string | null>(null);
    const [showItineraryModal, setShowItineraryModal] = useState(false);
    const [showChatHistory, setShowChatHistory] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const hasGreeted = useRef(false);
    const hasAutoSaved = useRef(false);

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
    } = useChatStore();

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    // Auto-save when itinerary is received
    useEffect(() => {
        const autoSaveTrip = async () => {
            if (!extractedItinerary || !extractedItinerary.days || extractedItinerary.days.length === 0 || hasAutoSaved.current) {
                return;
            }

            hasAutoSaved.current = true;
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
                    itinerary: {
                        days: extractedItinerary.days,
                        total_estimated_cost: extractedItinerary.budget_total
                    }
                };

                const response = await api.createTrip(tripData);
                setSavedTripId(response.trip_id);
                console.log('Trip auto-saved:', response.trip_id);

                // Show modal after successful save
                setShowItineraryModal(true);
                toast.success('Trip saved successfully!');
            } catch (error) {
                console.error('Failed to auto-save trip:', error);
                toast.error('Failed to save trip. You can try again later.');
                hasAutoSaved.current = false; // Reset so user can retry
            } finally {
                setIsSaving(false);
            }
        };

        autoSaveTrip();
    }, [extractedItinerary]);

    // Add greeting only once
    // Add greeting only once
    useEffect(() => {
        if (hasGreeted.current) return;

        const hasGreeting = messages.some(m => m.id === 'greeting');
        if (!hasGreeting && messages.length === 0) {
            hasGreeted.current = true;
            addMessage({
                id: 'greeting',
                role: 'assistant',
                content: `Hey there! 🌴✨

I'm your AI travel companion. Let's plan an amazing trip together!

**Where would you like to go?** Tell me about your dream destination and how many days you have.`,
                timestamp: new Date()
            });
        }
    }, [messages, addMessage]);

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

        try {
            await streamRequest('/chat/stream', {
                message: userMessage,
                trip_id: useChatStore.getState().activeTripId
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
        } catch (error) {
            console.error('Chat error:', error);
            // Remove the empty assistant message on error
            useChatStore.setState(state => ({
                messages: state.messages.filter(m => m.id !== (Date.now() + 1).toString())
            }));
            toast.error('Failed to send message. Please try again.');
        } finally {
            setStreaming(false);
            setAgentStatus('', '');
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
        } catch (error) {
            console.error('Failed to save trip:', error);
            toast.error('Failed to save trip. Please try again.');
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
        <div className="flex flex-col h-[calc(100vh-4rem)] md:h-screen md:flex-row">
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
                        className={`p-2 rounded-lg transition-colors ${showChatHistory ? 'bg-accent text-white' : 'hover:bg-black/5'}`}
                        title="Chat History"
                    >
                        <History className="w-5 h-5" />
                    </button>
                </header>

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
                        <MessageBubble key={message.id} message={message} />
                    ))}
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

            {/* Itinerary Modal */}
            {savedTripId && (
                <ItineraryModal
                    isOpen={showItineraryModal}
                    onClose={() => setShowItineraryModal(false)}
                    itinerary={extractedItinerary}
                    tripId={savedTripId}
                />
            )}

            {/* View Itinerary Button (only show if trip is saved) */}
            {savedTripId && !showItineraryModal && (
                <button
                    onClick={() => setShowItineraryModal(true)}
                    className="fixed bottom-6 right-6 btn btn-primary shadow-lg flex items-center gap-2 z-40"
                >
                    <MapPin className="w-4 h-4" />
                    View Itinerary
                </button>
            )}
        </div>
    );
}

function MessageBubble({ message }: { message: ChatMessage }) {
    const isUser = message.role === 'user';

    return (
        <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} animate-slide-in-up`}>
            {!isUser && (
                <div
                    className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 mr-2"
                    style={{ background: 'var(--accent-50)' }}
                >
                    <Sparkles className="w-4 h-4" style={{ color: 'var(--accent)' }} />
                </div>
            )}
            <div
                className={`max-w-[80%] px-4 py-3 rounded-2xl ${isUser ? 'rounded-br-sm' : 'rounded-bl-sm'
                    }`}
                style={{
                    background: isUser ? 'var(--accent)' : 'var(--bg-secondary)',
                    color: isUser ? 'white' : 'var(--text-primary)',
                    boxShadow: 'var(--shadow-sm)'
                }}
            >
                <div className={`prose prose-sm max-w-none ${isUser ? 'text-white' : 'prose-travel'}`}>
                    <ReactMarkdown>{message.content || '...'}</ReactMarkdown>
                </div>
            </div>
        </div>
    );
}
