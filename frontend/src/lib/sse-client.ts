/**
 * Resilient SSE Client with automatic reconnection and Last-Event-ID support
 * 
 * Features:
 * - Automatic reconnection with exponential backoff
 * - Last-Event-ID tracking for resuming streams
 * - Heartbeat detection (ignores SSE comment lines)
 * - Connection status callbacks
 */

export interface SSEClientOptions {
    maxReconnectAttempts?: number;
    maxReconnectDelay?: number;
    onConnectionChange?: (status: 'connecting' | 'connected' | 'disconnected' | 'error') => void;
}

export class ResilientSSEClient {
    private eventSource: EventSource | null = null;
    private lastEventId: number = 0;
    private reconnectAttempts = 0;
    private options: SSEClientOptions;
    private url: string = '';
    private onEventCallback: ((event: any) => void) | null = null;
    private onErrorCallback: ((error: any) => void) | null = null;
    private reconnectTimeout: NodeJS.Timeout | null = null;

    constructor(options: SSEClientOptions = {}) {
        this.options = {
            maxReconnectAttempts: 5,
            maxReconnectDelay: 30000, // 30 seconds
            ...options
        };
    }

    /**
     * Connect to SSE endpoint with automatic reconnection
     */
    connect(
        url: string,
        onEvent: (event: any) => void,
        onError?: (error: any) => void
    ): void {
        this.url = url;
        this.onEventCallback = onEvent;
        this.onErrorCallback = onError ?? null;

        this.options.onConnectionChange?.('connecting');

        // Append Last-Event-ID to URL for resumption
        const urlWithId = this.lastEventId > 0
            ? `${url}${url.includes('?') ? '&' : '?'}lastEventId=${this.lastEventId}`
            : url;

        try {
            this.eventSource = new EventSource(urlWithId);

            this.eventSource.addEventListener('open', () => {
                console.log('SSE connection established');
                this.options.onConnectionChange?.('connected');
                this.reconnectAttempts = 0; // Reset on successful connection
            });

            this.eventSource.addEventListener('message', (e: MessageEvent) => {
                // Track event ID for resumption
                if (e.lastEventId) {
                    const eventId = parseInt(e.lastEventId, 10);
                    if (!isNaN(eventId)) {
                        this.lastEventId = eventId;
                    }
                }

                try {
                    const event = JSON.parse(e.data);
                    this.onEventCallback?.(event);
                } catch (err) {
                    console.error('Failed to parse SSE message:', err);
                }
            });

            this.eventSource.addEventListener('error', (e) => {
                console.error('SSE error', e);
                this.options.onConnectionChange?.('error');

                // EventSource automatically attempts to reconnect for network errors
                // But we need to handle it ourselves for 5xx errors
                if (this.eventSource?.readyState === EventSource.CLOSED) {
                    this.handleReconnection();
                }
            });

        } catch (error) {
            console.error('Failed to create EventSource:', error);
            this.handleReconnection();
        }
    }

    /**
     * Handle reconnection with exponential backoff
     */
    private handleReconnection(): void {
        if (this.reconnectAttempts >= (this.options.maxReconnectAttempts || 5)) {
            console.error('Max reconnection attempts reached');
            this.options.onConnectionChange?.('disconnected');
            this.onErrorCallback?.({
                message: `Failed to reconnect after ${this.reconnectAttempts} attempts`,
                canRetry: false
            });
            return;
        }

        // Exponential backoff: 1s, 2s, 4s, 8s, 16s, max 30s
        const delay = Math.min(
            1000 * Math.pow(2, this.reconnectAttempts),
            this.options.maxReconnectDelay || 30000
        );

        this.reconnectAttempts++;

        console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})...`);
        this.options.onConnectionChange?.('disconnected');

        this.reconnectTimeout = setTimeout(() => {
            if (this.url && this.onEventCallback) {
                console.log('Attempting to reconnect...');
                this.connect(this.url, this.onEventCallback, this.onErrorCallback ?? undefined);
            }
        }, delay);
    }

    /**
     * Manually disconnect and clean up
     */
    disconnect(): void {
        if (this.reconnectTimeout) {
            clearTimeout(this.reconnectTimeout);
            this.reconnectTimeout = null;
        }

        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }

        this.options.onConnectionChange?.('disconnected');
    }

    /**
     * Get current connection status
     */
    get status(): 'connecting' | 'connected' | 'disconnected' {
        if (!this.eventSource) return 'disconnected';

        switch (this.eventSource.readyState) {
            case EventSource.CONNECTING:
                return 'connecting';
            case EventSource.OPEN:
                return 'connected';
            case EventSource.CLOSED:
            default:
                return 'disconnected';
        }
    }

    /**
     * Reset the client (clear event ID tracking)
     */
    reset(): void {
        this.lastEventId = 0;
        this.reconnectAttempts = 0;
    }
}
