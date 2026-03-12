'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

interface UseDragResizeOptions {
    /** Which edge is being dragged — 'right' for left panels, 'left' for right panels */
    edge: 'right' | 'left';
    initialWidth: number;
    minWidth?: number;
    maxWidth?: number;
    /** Optional key to persist width in localStorage */
    storageKey?: string;
}

/**
 * Adds a drag-to-resize handle to a panel.
 * Returns:
 *   - `panelWidth`  – current width in px (use as style.width)
 *   - `handleProps` – spread onto the drag-handle div
 *   - `isDragging`  – true while actively resizing (cursor override)
 */
export function useDragResize({
    edge,
    initialWidth,
    minWidth = 180,
    maxWidth = 520,
    storageKey,
}: UseDragResizeOptions) {
    const [panelWidth, setPanelWidth] = useState<number>(() => {
        if (storageKey && typeof window !== 'undefined') {
            const stored = localStorage.getItem(storageKey);
            if (stored) return Math.min(maxWidth, Math.max(minWidth, Number(stored)));
        }
        return initialWidth;
    });

    const [isDragging, setIsDragging] = useState(false);
    const startXRef = useRef(0);
    const startWidthRef = useRef(0);

    const onMouseMove = useCallback(
        (e: MouseEvent) => {
            const delta = edge === 'right'
                ? e.clientX - startXRef.current
                : startXRef.current - e.clientX;
            const next = Math.min(maxWidth, Math.max(minWidth, startWidthRef.current + delta));
            setPanelWidth(next);
        },
        [edge, minWidth, maxWidth],
    );

    const onMouseUp = useCallback(() => {
        setIsDragging(false);
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
        window.removeEventListener('mousemove', onMouseMove);
    }, [onMouseMove]);

    const onMouseDown = useCallback(
        (e: React.MouseEvent) => {
            e.preventDefault();
            startXRef.current = e.clientX;
            startWidthRef.current = panelWidth;
            setIsDragging(true);
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
            window.addEventListener('mousemove', onMouseMove);
            window.addEventListener('mouseup', onMouseUp, { once: true });
        },
        [panelWidth, onMouseMove, onMouseUp],
    );

    // Persist to localStorage whenever width settles
    useEffect(() => {
        if (storageKey && !isDragging) {
            localStorage.setItem(storageKey, String(panelWidth));
        }
    }, [panelWidth, isDragging, storageKey]);

    const handleProps = {
        onMouseDown,
        role: 'separator' as const,
        'aria-label': 'Resize panel',
        'aria-orientation': 'vertical' as const,
        title: 'Drag to resize',
    };

    return { panelWidth, handleProps, isDragging };
}
