'use client';

import { X } from 'lucide-react';

interface PermissionDialogProps {
    title: string;
    message: string;
    icon?: React.ReactNode;
    privacyNote?: string;
    onAccept: () => void;
    onDeny: () => void;
    onClose?: () => void;
}

export function PermissionDialog({
    title,
    message,
    icon,
    privacyNote = "🔒 Your data is never stored or shared with third parties",
    onAccept,
    onDeny,
    onClose
}: PermissionDialogProps) {
    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
            <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 max-w-md w-full shadow-2xl animate-slide-up">
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                        {icon && (
                            <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900/30 rounded-full flex items-center justify-center">
                                {icon}
                            </div>
                        )}
                        <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
                            {title}
                        </h3>
                    </div>
                    {onClose && (
                        <button
                            onClick={onClose}
                            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                            aria-label="Close"
                        >
                            <X className="w-5 h-5" />
                        </button>
                    )}
                </div>

                {/* Message */}
                <p className="text-gray-600 dark:text-gray-300 mb-6 leading-relaxed">
                    {message}
                </p>

                {/* Actions */}
                <div className="flex gap-3">
                    <button
                        onClick={onDeny}
                        className="flex-1 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50 font-medium transition-all"
                    >
                        Not Now
                    </button>
                    <button
                        onClick={onAccept}
                        className="flex-1 px-4 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl hover:opacity-90 font-medium transition-all shadow-lg shadow-purple-500/30"
                    >
                        Allow Access
                    </button>
                </div>

                {/* Privacy Note */}
                {privacyNote && (
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-4 text-center">
                        {privacyNote}
                    </p>
                )}
            </div>
        </div>
    );
}
