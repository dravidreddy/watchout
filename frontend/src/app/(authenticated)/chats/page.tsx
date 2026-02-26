'use client';

import { useEffect, useState } from 'react';
import { MessageSquare, Clock, Trash2, Save, Share2, Plane, ChevronRight } from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { toast } from 'sonner';

interface Conversation {
    trip_id: string;
    _id?: string;
    title?: string;
    messages: any[];
    created_at: string;
    updated_at: string;
    is_trip?: boolean;
}

export default function ChatsPage() {
    const router = useRouter();
    const [conversations, setConversations] = useState<Conversation[]>([]);
    const [loading, setLoading] = useState(true);
    const [savingIds, setSavingIds] = useState<Set<string>>(new Set());

    const loadConversations = async () => {
        setLoading(true);
        try {
            const convos = await api.listConversations();
            setConversations(convos);
        } catch (error) {
            console.error('Failed to load conversations:', error);
            toast.error('Failed to load chat history');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadConversations();
    }, []);

    const handleSaveAsTrip = async (tripId: string) => {
        setSavingIds(prev => new Set(prev).add(tripId));
        try {
            await api.saveConversationAsTrip(tripId);
            toast.success('Saved as trip! View it in your Trips page.');
            setConversations(prev =>
                prev.map(c => (c.trip_id || c._id) === tripId ? { ...c, is_trip: true } : c)
            );
        } catch (error) {
            toast.error('Failed to save as trip');
        } finally {
            setSavingIds(prev => {
                const next = new Set(prev);
                next.delete(tripId);
                return next;
            });
        }
    };

    const handleDelete = async (tripId: string) => {
        if (!confirm('Delete this conversation?')) return;

        try {
            await api.deleteConversation(tripId);
            toast.success('Conversation deleted');
            setConversations(prev => prev.filter(c => (c.trip_id || c._id) !== tripId));
        } catch (error) {
            toast.error('Failed to delete conversation');
        }
    };

    const handleShare = async (tripId: string) => {
        try {
            const { sharing_url } = await api.shareConversation(tripId);
            await navigator.clipboard.writeText(sharing_url);
            toast.success('Link copied to clipboard!');
        } catch (error) {
            toast.error('Failed to share conversation');
        }
    };

    const formatTime = (dateStr: string) => {
        const date = new Date(dateStr);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffDays === 0) return 'Today at ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        if (diffDays === 1) return 'Yesterday';
        if (diffDays < 7) return `${diffDays} days ago`;
        return date.toLocaleDateString();
    };

    return (
        <div className="min-h-screen">
            {/* Header */}
            <header className="sticky top-0 z-30 glass px-4 py-4 md:px-8" style={{ borderBottom: '1px solid rgba(0,0,0,0.05)' }}>
                <div className="flex items-center justify-between max-w-4xl mx-auto">
                    <div>
                        <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>
                            Chats
                        </h1>
                        <p className="text-sm" style={{ color: 'var(--text-tertiary)' }}>
                            Your previous planning sessions
                        </p>
                    </div>
                </div>
            </header>

            <div className="px-4 md:px-8 py-6 max-w-4xl mx-auto pb-24">
                {loading ? (
                    <div className="space-y-4">
                        {[1, 2, 3, 4].map((i) => (
                            <div key={i} className="h-24 rounded-2xl animate-pulse bg-gray-100" />
                        ))}
                    </div>
                ) : conversations.length === 0 ? (
                    <div className="text-center py-20 px-4">
                        <MessageSquare className="w-16 h-16 mx-auto mb-4" style={{ color: 'var(--text-tertiary)' }} />
                        <h2 className="text-xl font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>No conversations yet</h2>
                        <p className="text-body mb-6" style={{ color: 'var(--text-secondary)' }}>
                            Start a new chat to begin planning your next adventure.
                        </p>
                        <Link href="/chat?new=true">
                            <button className="btn btn-primary">
                                Start a New Chat
                            </button>
                        </Link>
                    </div>
                ) : (
                    <div className="space-y-4">
                        {conversations.map((convo, idx) => (
                            <div
                                key={convo.trip_id || convo._id || `chat-${idx}`}
                                onClick={() => router.push(`/chat?trip_id=${convo.trip_id || convo._id}`)}
                                className="group rounded-2xl p-4 md:p-5 hover:shadow-md transition-all cursor-pointer relative overflow-hidden"
                                style={{
                                    background: 'var(--bg-secondary)',
                                    border: '1px solid rgba(0,0,0,0.05)'
                                }}
                            >
                                <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 mb-1 pointer-events-none">
                                            <h3 className="font-semibold text-lg line-clamp-1" style={{ color: 'var(--text-primary)' }}>
                                                {convo.title || 'Untitled Chat'}
                                            </h3>
                                            {convo.is_trip && (
                                                <span className="flex-shrink-0 inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-indigo-50 text-indigo-600">
                                                    <Plane className="w-3 h-3" />
                                                    Trip
                                                </span>
                                            )}
                                        </div>
                                        <p className="text-sm line-clamp-2 md:line-clamp-1 mb-3 pointer-events-none" style={{ color: 'var(--text-secondary)' }}>
                                            {convo.messages?.at(-1)?.content || 'No messages'}
                                        </p>
                                        <div className="flex items-center gap-2 text-xs font-medium pointer-events-none" style={{ color: 'var(--text-tertiary)' }}>
                                            <Clock className="w-3.5 h-3.5" />
                                            {formatTime(convo.updated_at)}
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-2 md:opacity-0 group-hover:opacity-100 transition-opacity justify-end border-t md:border-none pt-3 md:pt-0">
                                        {!convo.is_trip && (
                                            <button
                                                onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleSaveAsTrip(convo.trip_id || convo._id || ""); }}
                                                disabled={savingIds.has(convo.trip_id || convo._id || "")}
                                                className="p-2 rounded-xl text-indigo-600 hover:bg-indigo-50 transition-colors flex items-center gap-2 text-sm font-medium"
                                                title="Save as Trip"
                                            >
                                                <Save className="w-4 h-4" />
                                                <span className="md:hidden">Save</span>
                                            </button>
                                        )}
                                        <button
                                            onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleShare(convo.trip_id || convo._id || ""); }}
                                            className="p-2 rounded-xl text-gray-600 hover:bg-gray-100 transition-colors flex items-center gap-2 text-sm font-medium"
                                            title="Share"
                                        >
                                            <Share2 className="w-4 h-4" />
                                            <span className="md:hidden">Share</span>
                                        </button>
                                        <button
                                            onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleDelete(convo.trip_id || convo._id || ""); }}
                                            className="p-2 rounded-xl text-red-600 hover:bg-red-50 transition-colors flex items-center gap-2 text-sm font-medium"
                                            title="Delete"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                            <span className="md:hidden">Delete</span>
                                        </button>
                                        <div className="hidden md:flex ml-2 w-8 h-8 rounded-full bg-gray-50 items-center justify-center group-hover:bg-accent group-hover:text-white transition-colors pointer-events-none">
                                            <ChevronRight className="w-4 h-4" />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
