'use client';

import React from 'react';
import { AlertTriangle, X } from 'lucide-react';

interface DeleteConfirmDialogProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: () => void;
    tripCount: number;
    isDeleting?: boolean;
}

export const DeleteConfirmDialog: React.FC<DeleteConfirmDialogProps> = ({
    isOpen,
    onClose,
    onConfirm,
    tripCount,
    isDeleting = false
}) => {
    if (!isOpen) return null;

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
            style={{ background: 'rgba(0, 0, 0, 0.5)' }}
            onClick={onClose}
        >
            <div
                className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Icon */}
                <div className="flex items-center justify-center w-12 h-12 rounded-full bg-red-100 mb-4">
                    <AlertTriangle className="w-6 h-6 text-red-600" />
                </div>

                {/* Title */}
                <h2 className="text-xl font-bold mb-2" style={{ color: 'var(--text-primary)' }}>
                    Delete {tripCount === 1 ? 'Trip' : `${tripCount} Trips`}?
                </h2>

                {/* Description */}
                <p className="text-sm mb-6" style={{ color: 'var(--text-secondary)' }}>
                    {tripCount === 1
                        ? 'This action cannot be undone. The trip and all its details will be permanently deleted.'
                        : `This action cannot be undone. All ${tripCount} selected trips and their details will be permanently deleted.`}
                </p>

                {/* Actions */}
                <div className="flex gap-3">
                    <button
                        onClick={onClose}
                        disabled={isDeleting}
                        className="flex-1 btn btn-secondary"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={onConfirm}
                        disabled={isDeleting}
                        className="flex-1 bg-red-600 text-white px-4 py-2 rounded-xl font-medium hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isDeleting ? 'Deleting...' : 'Delete'}
                    </button>
                </div>
            </div>
        </div>
    );
};
