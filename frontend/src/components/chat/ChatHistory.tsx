'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageSquare, Trash2, Save, Share2, Clock, MoreVertical, X, Plane, Plus } from 'lucide-react';
import { api } from '@/lib/api';
import { toast } from 'sonner';
import { useDragResize } from '@/hooks/useDragResize';

interface Conversation {
    trip_id: string;
    _id?: string;
    title?: string;
    last_message?: {
        role?: string;
        content?: string;
        created_at?: string;
    };
    created_at: string;
    updated_at: string;
    is_trip?: boolean;
}

interface ChatHistoryProps {
    onSelectConversation: (tripId: string) => void;
    currentTripId?: string;
    isOpen: boolean;
    onClose: () => void;
    onNewChat?: () => void;
}

export function ChatHistory({ onSelectConversation, currentTripId, isOpen, onClose, onNewChat }: ChatHistoryProps) {
    const [conversations, setConversations] = useState<Conversation[]>([]);
    const [loading, setLoading] = useState(false);
    const [activeMenu, setActiveMenu] = useState<string | null>(null);
    const [savingIds, setSavingIds] = useState<Set<string>>(new Set());
    const [deleteTarget, setDeleteTarget] = useState<string | null>(null);
    const menuRef = useRef<HTMLDivElement>(null);
    const { panelWidth, handleProps, isDragging } = useDragResize({
        edge: 'left',
        initialWidth: 320,
        minWidth: 240,
        maxWidth: 520,
        storageKey: 'chat-history-width',
    });

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

    const getConversationId = (convo: Conversation) => convo.trip_id || convo._id || "";

    const handleSaveAsTrip = async (tripId: string) => {
        setSavingIds(prev => new Set(prev).add(tripId));
        try {
            await api.saveConversationAsTrip(tripId);
            toast.success('Saved as trip! View it in your Trips page.');
            // Update local state to reflect is_trip = true
            setConversations(prev =>
                prev.map(c => getConversationId(c) === tripId ? { ...c, is_trip: true } : c)
            );
        } catch (error) {
            toast.error('Failed to save as trip');
        } finally {
            setSavingIds(prev => {
                const next = new Set(prev);
                next.delete(tripId);
                return next;
            });
            setActiveMenu(null);
        }
    };

    const handleDelete = (tripId: string) => {
        setDeleteTarget(tripId);
        setActiveMenu(null);
    };

    const confirmDelete = async () => {
        if (!deleteTarget) return;
        try {
            await api.deleteConversation(deleteTarget);
            toast.success('Conversation deleted');
            setConversations(prev => prev.filter(c => getConversationId(c) !== deleteTarget));
        } catch {
            toast.error('Failed to delete conversation');
        } finally {
            setDeleteTarget(null);
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

    // Close menu when clicking outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (activeMenu && menuRef.current && !menuRef.current.contains(event.target as Node)) {
                setActiveMenu(null);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, [activeMenu]);

    return (
        <>
            <AnimatePresence>
                {isOpen && (
                    <>
                        {/* Click-outside backdrop for the sidebar */}
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="fixed inset-0 z-30 bg-black/20 backdrop-blur-sm"
                            onClick={onClose}
                            aria-hidden="true"
                        />

                        <motion.div
                            initial={{ x: '100%' }}
                            animate={{ x: 0 }}
                            exit={{ x: '100%' }}
                            transition={{ type: 'spring', bounce: 0, duration: 0.3 }}
                            drag="x"
                            dragConstraints={{ left: 0, right: 0 }}
                            dragElastic={{ left: 0, right: 1 }}
                            onDragEnd={(e, info) => {
                                if (info.offset.x > 100 || info.velocity.x > 500) {
                                    onClose();
                                }
                            }}
                            className="fixed inset-y-0 right-0 shadow-xl z-40 flex flex-col"
                            style={{
                                width: panelWidth,
                                background: 'var(--bg-secondary)',
                                borderLeft: '1px solid rgba(0,0,0,0.05)'
                            }}
                        >
                            {/* Drag-to-resize handle — left edge */}
                            <div
                                {...handleProps}
                                className="absolute top-0 left-0 w-[5px] h-full z-50 group cursor-col-resize flex items-center justify-center"
                                style={{ touchAction: 'none' }}
                                // Don't let drag events bubble to Framer's drag handler
                                onPointerDown={(e) => e.stopPropagation()}
                            >
                                <div
                                    className={`w-[3px] h-12 rounded-full transition-all duration-150 ${isDragging ? 'opacity-100 scale-y-110' : 'opacity-0 group-hover:opacity-100'
                                        }`}
                                    style={{ background: 'var(--accent)' }}
                                />
                            </div>
                            {/* Header */}
                            <div className="p-4 flex items-center justify-between" style={{ borderBottom: '1px solid rgba(0,0,0,0.05)' }}>
                                <h2 className="font-semibold text-lg flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                                    <MessageSquare className="w-5 h-5" />
                                    Chat History
                                </h2>
                                <div className="flex items-center gap-1">
                                    {onNewChat && (
                                        <button
                                            onClick={() => {
                                                onNewChat();
                                                onClose();
                                            }}
                                            className="p-1.5 hover:bg-black/5 rounded-lg transition-colors flex items-center"
                                            style={{ color: 'var(--accent)' }}
                                            title="New Chat"
                                        >
                                            <Plus className="w-5 h-5" />
                                        </button>
                                    )}
                                    <button
                                        onClick={onClose}
                                        className="p-1.5 hover:bg-black/5 rounded-lg transition-colors"
                                        style={{ color: 'var(--text-secondary)' }}
                                        title="Close"
                                    >
                                        <X className="w-5 h-5" />
                                    </button>
                                </div>
                            </div>

                            {/* Conversations List */}
                            <div
                                className="flex-1 overflow-y-auto"
                                role="region"
                                aria-label="Recent conversations"
                                aria-live="polite"
                                aria-atomic="true"
                            >
                                {loading ? (
                                    <div className="p-4 text-center" style={{ color: 'var(--text-tertiary)' }} aria-busy="true">Loading...</div>
                                ) : conversations.length === 0 ? (
                                    <div className="p-4 text-center" style={{ color: 'var(--text-tertiary)' }}>
                                        <MessageSquare className="w-12 h-12 mx-auto mb-2 opacity-50" aria-hidden="true" />
                                        <p>No conversations yet</p>
                                        <button
                                            onClick={onClose}
                                            className="mt-4 px-4 py-2 rounded-xl text-sm font-medium text-white transition-all hover:opacity-90"
                                            style={{ background: 'var(--accent)' }}
                                        >
                                            Start your first trip ✨
                                        </button>
                                    </div>
                                ) : (
                                    conversations.map((convo, idx) => {
                                        const convoId = getConversationId(convo);
                                        return (
                                            <div
                                                key={convoId || `chat-${idx}`}
                                                className={`p-3 border-b hover:bg-black/5 cursor-pointer transition-colors ${currentTripId === convoId ? 'bg-accent/10 border-l-4 border-l-accent' : ''
                                                    }`}
                                                style={{ borderColor: 'rgba(0,0,0,0.05)' }}
                                                onClick={() => onSelectConversation(convoId)}
                                            >
                                                <div className="flex items-start justify-between gap-2">
                                                    <div className="flex-1 min-w-0">
                                                        <div className="flex items-center gap-1.5">
                                                            <h3 className="font-medium text-sm line-clamp-1" style={{ color: 'var(--text-primary)' }}>
                                                                {convo.title || 'Untitled Chat'}
                                                            </h3>
                                                            {convo.is_trip && (
                                                                <span className="flex-shrink-0 inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full text-[10px] font-semibold bg-indigo-100 text-indigo-700">
                                                                    <Plane className="w-2.5 h-2.5" />
                                                                    Trip
                                                                </span>
                                                            )}
                                                        </div>
                                                        <p className="text-xs line-clamp-2 mt-1" style={{ color: 'var(--text-secondary)' }}>
                                                            {convo.last_message?.content || 'No messages'}
                                                        </p>
                                                        <div className="flex items-center gap-1 mt-1 text-xs" style={{ color: 'var(--text-tertiary)' }}>
                                                            <Clock className="w-3 h-3" />
                                                            {formatTime(convo.updated_at)}
                                                        </div>
                                                    </div>

                                                    {/* Actions Menu */}
                                                    <div className="relative" ref={activeMenu === convoId ? menuRef : null}>
                                                        <button
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                setActiveMenu(activeMenu === convoId ? null : convoId);
                                                            }}
                                                            className="p-1 hover:bg-black/5 rounded transition-colors"
                                                            style={{ color: 'var(--text-secondary)' }}
                                                        >
                                                            <MoreVertical className="w-4 h-4" />
                                                        </button>

                                                        {activeMenu === convoId && (
                                                            <div className="absolute right-0 top-8 rounded-lg shadow-lg py-1 z-10 w-44" style={{ background: 'var(--bg-secondary)', border: '1px solid rgba(0,0,0,0.05)' }}>
                                                                {!convo.is_trip ? (
                                                                    <button
                                                                        onClick={(e) => {
                                                                            e.stopPropagation();
                                                                            handleSaveAsTrip(convoId);
                                                                        }}
                                                                        disabled={savingIds.has(convoId)}
                                                                        className="w-full px-3 py-2 text-left text-sm hover:bg-black/5 flex items-center gap-2 disabled:opacity-50"
                                                                        style={{ color: 'var(--text-primary)' }}
                                                                    >
                                                                        <Save className="w-4 h-4 text-indigo-600" />
                                                                        {savingIds.has(convoId) ? 'Saving...' : 'Save as Trip'}
                                                                    </button>
                                                                ) : (
                                                                    <div className="w-full px-3 py-2 text-left text-sm flex items-center gap-2 text-indigo-600 cursor-default">
                                                                        <Plane className="w-4 h-4" />
                                                                        Saved as Trip ✓
                                                                    </div>
                                                                )}
                                                                <button
                                                                    onClick={(e) => {
                                                                        e.stopPropagation();
                                                                        handleShare(convoId);
                                                                        setActiveMenu(null);
                                                                    }}
                                                                    className="w-full px-3 py-2 text-left text-sm hover:bg-black/5 flex items-center gap-2"
                                                                    style={{ color: 'var(--text-primary)' }}
                                                                >
                                                                    <Share2 className="w-4 h-4" />
                                                                    Share
                                                                </button>
                                                                <button
                                                                    onClick={(e) => {
                                                                        e.stopPropagation();
                                                                        handleDelete(convoId);
                                                                        setActiveMenu(null);
                                                                    }}
                                                                    className="w-full px-3 py-2 text-left text-sm hover:bg-red-50/50 flex items-center gap-2 text-red-600"
                                                                >
                                                                    <Trash2 className="w-4 h-4" />
                                                                    Delete
                                                                </button>
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        );
                                    })
                                )}
                            </div>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>

            {/* In-app Delete Confirmation Modal */}
            <AnimatePresence>
                {deleteTarget && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 z-[200] flex items-center justify-center p-4"
                        style={{ background: 'rgba(0,0,0,0.55)', backdropFilter: 'blur(4px)' }}
                        onClick={() => setDeleteTarget(null)}
                    >
                        <motion.div
                            initial={{ scale: 0.92, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.92, opacity: 0 }}
                            transition={{ type: 'spring', bounce: 0.2, duration: 0.25 }}
                            className="rounded-2xl p-6 w-full max-w-sm shadow-2xl flex flex-col gap-4"
                            style={{ background: 'var(--bg-secondary)', border: '1px solid rgba(128,128,128,0.15)' }}
                            onClick={(e) => e.stopPropagation()}
                        >
                            <div className="flex items-center gap-3">
                                <div className="p-2.5 rounded-xl bg-red-500/10">
                                    <Trash2 className="w-5 h-5 text-red-500" />
                                </div>
                                <div>
                                    <h3 className="font-semibold" style={{ color: 'var(--text-primary)' }}>Delete conversation?</h3>
                                    <p className="text-sm mt-0.5" style={{ color: 'var(--text-secondary)' }}>This can&apos;t be undone.</p>
                                </div>
                            </div>
                            <div className="flex gap-2 mt-1">
                                <button
                                    onClick={() => setDeleteTarget(null)}
                                    className="flex-1 px-4 py-2.5 rounded-xl text-sm font-medium transition-all hover:opacity-80"
                                    style={{ background: 'var(--bg-primary)', color: 'var(--text-secondary)', border: '1px solid rgba(128,128,128,0.15)' }}
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={confirmDelete}
                                    className="flex-1 px-4 py-2.5 rounded-xl text-sm font-semibold text-white bg-red-500 hover:bg-red-600 transition-all"
                                >
                                    Delete
                                </button>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </>
    );
}


