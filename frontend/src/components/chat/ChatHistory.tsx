'use client';

import { useState, useEffect } from 'react';
import { MessageSquare, Trash2, Save, Share2, Clock, MoreVertical, X } from 'lucide-react';
import { api } from '@/lib/api';
import { toast } from 'sonner';

interface Conversation {
    trip_id: string;
    title?: string;
    messages: any[];
    created_at: string;
    updated_at: string;
}

interface ChatHistoryProps {
    onSelectConversation: (tripId: string) => void;
    currentTripId?: string;
    isOpen: boolean;
    onClose: () => void;
}

export function ChatHistory({ onSelectConversation, currentTripId, isOpen, onClose }: ChatHistoryProps) {
    const [conversations, setConversations] = useState<Conversation[]>([]);
    const [loading, setLoading] = useState(false);
    const [activeMenu, setActiveMenu] = useState<string | null>(null);

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

    const handleDelete = async (tripId: string) => {
        if (!confirm('Delete this conversation?')) return;

        try {
            await api.deleteConversation(tripId);
            toast.success('Conversation deleted');
            setConversations(prev => prev.filter(c => c.trip_id !== tripId));
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
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        return date.toLocaleDateString();
    };

    useEffect(() => {
        if (isOpen) {
            loadConversations();
        }
    }, [isOpen]);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-y-0 right-0 w-80 bg-white border-l border-gray-200 shadow-xl z-40 flex flex-col">
            {/* Header */}
            <div className="p-4 border-b border-gray-200 flex items-center justify-between">
                <h2 className="font-semibold text-lg flex items-center gap-2">
                    <MessageSquare className="w-5 h-5" />
                    Chat History
                </h2>
                <button
                    onClick={onClose}
                    className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
                >
                    <X className="w-5 h-5" />
                </button>
            </div>

            {/* Conversations List */}
            <div className="flex-1 overflow-y-auto">
                {loading ? (
                    <div className="p-4 text-center text-gray-500">Loading...</div>
                ) : conversations.length === 0 ? (
                    <div className="p-4 text-center text-gray-500">
                        <MessageSquare className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                        <p>No conversations yet</p>
                    </div>
                ) : (
                    conversations.map(convo => (
                        <div
                            key={convo.trip_id}
                            className={`p-3 border-b border-gray-100 hover:bg-gray-50 cursor-pointer transition-colors ${currentTripId === convo.trip_id ? 'bg-accent/10 border-l-4 border-l-accent' : ''
                                }`}
                            onClick={() => onSelectConversation(convo.trip_id)}
                        >
                            <div className="flex items-start justify-between gap-2">
                                <div className="flex-1 min-w-0">
                                    <h3 className="font-medium text-sm line-clamp-1">
                                        {convo.title || 'Untitled Chat'}
                                    </h3>
                                    <p className="text-xs text-gray-500 line-clamp-2 mt-1">
                                        {convo.messages[convo.messages.length - 1]?.content || 'No messages'}
                                    </p>
                                    <div className="flex items-center gap-1 mt-1 text-xs text-gray-400">
                                        <Clock className="w-3 h-3" />
                                        {formatTime(convo.updated_at)}
                                    </div>
                                </div>

                                {/* Actions Menu */}
                                <div className="relative">
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            setActiveMenu(activeMenu === convo.trip_id ? null : convo.trip_id);
                                        }}
                                        className="p-1 hover:bg-gray-200 rounded transition-colors"
                                    >
                                        <MoreVertical className="w-4 h-4" />
                                    </button>

                                    {activeMenu === convo.trip_id && (
                                        <div className="absolute right-0 top-8 bg-white border border-gray-200 rounded-lg shadow-lg py-1 z-10 w-40">
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    // TODO: Open save dialog
                                                    setActiveMenu(null);
                                                }}
                                                className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2"
                                            >
                                                <Save className="w-4 h-4" />
                                                Save as Trip
                                            </button>
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    handleShare(convo.trip_id);
                                                    setActiveMenu(null);
                                                }}
                                                className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2"
                                            >
                                                <Share2 className="w-4 h-4" />
                                                Share
                                            </button>
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    handleDelete(convo.trip_id);
                                                    setActiveMenu(null);
                                                }}
                                                className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2 text-red-600"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                                Delete
                                            </button>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
