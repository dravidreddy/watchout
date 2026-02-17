/**
 * Offline Database Layer using IndexedDB
 * Provides persistent storage for chat messages and trip data
 * Enables true offline functionality with background sync
 */

import { openDB, DBSchema, IDBPDatabase } from 'idb';

interface ChatDB extends DBSchema {
    messages: {
        key: string; // message ID
        value: {
            id: string;
            trip_id: string;
            role: 'user' | 'assistant';
            content: string;
            timestamp: number;
            synced: boolean;
        };
    };
    pending_messages: {
        key: string; // message ID
        value: {
            id: string;
            trip_id: string;
            content: string;
            timestamp: number;
            retries: number;
        };
    };
    trips: {
        key: string; // trip_id
        value: {
            trip_id: string;
            preferences: any;
            last_updated: number;
            itinerary?: any;
        };
    };
}

let db: IDBPDatabase<ChatDB> | null = null;

/**
 * Initialize IndexedDB connection
 */
export async function initDB(): Promise<IDBPDatabase<ChatDB>> {
    if (db) return db;

    db = await openDB<ChatDB>('bharat-voyager', 1, {
        upgrade(db) {
            // Create object stores
            if (!db.objectStoreNames.contains('messages')) {
                db.createObjectStore('messages', { keyPath: 'id' });
            }
            if (!db.objectStoreNames.contains('pending_messages')) {
                db.createObjectStore('pending_messages', { keyPath: 'id' });
            }
            if (!db.objectStoreNames.contains('trips')) {
                db.createObjectStore('trips', { keyPath: 'trip_id' });
            }
        },
    });

    return db;
}

/**
 * Save a chat message to IndexedDB
 * Automatically queues for sync if offline
 */
export async function saveChatMessage(
    tripId: string,
    role: 'user' | 'assistant',
    content: string
): Promise<string> {
    const database = await initDB();

    const messageId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const message = {
        id: messageId,
        trip_id: tripId,
        role,
        content,
        timestamp: Date.now(),
        synced: navigator.onLine,
    };

    await database.put('messages', message);

    // If offline and it's a user message, queue for sync
    if (!navigator.onLine && role === 'user') {
        await database.put('pending_messages', {
            id: messageId,
            trip_id: tripId,
            content,
            timestamp: Date.now(),
            retries: 0,
        });
    }

    return messageId;
}

/**
 * Get all messages for a trip
 */
export async function getChatHistory(tripId: string) {
    const database = await initDB();
    const allMessages = await database.getAll('messages');

    return allMessages
        .filter((msg) => msg.trip_id === tripId)
        .sort((a, b) => a.timestamp - b.timestamp);
}

/**
 * Sync pending messages when back online
 */
export async function syncPendingMessages(): Promise<{
    synced: number;
    failed: number;
}> {
    const database = await initDB();
    const pending = await database.getAll('pending_messages');

    let synced = 0;
    let failed = 0;

    for (const msg of pending) {
        try {
            const response = await fetch('/api/v1/chat/message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: msg.content,
                    trip_id: msg.trip_id,
                }),
            });

            if (response.ok) {
                // Success - remove from pending queue
                await database.delete('pending_messages', msg.id);

                // Mark original message as synced
                const originalMsg = await database.get('messages', msg.id);
                if (originalMsg) {
                    await database.put('messages', {
                        ...originalMsg,
                        synced: true,
                    });
                }

                synced++;
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (e) {
            // Still offline or error
            if (msg.retries < 3) {
                // Increment retry count
                await database.put('pending_messages', {
                    ...msg,
                    retries: msg.retries + 1,
                });
            } else {
                // Max retries reached - log and remove
                console.error(`Failed to sync message ${msg.id} after 3 retries`);
                await database.delete('pending_messages', msg.id);
            }
            failed++;
        }
    }

    return { synced, failed };
}

/**
 * Save trip data to IndexedDB
 */
export async function saveTripData(
    tripId: string,
    preferences: any,
    itinerary?: any
) {
    const database = await initDB();

    await database.put('trips', {
        trip_id: tripId,
        preferences,
        last_updated: Date.now(),
        itinerary,
    });
}

/**
 * Get trip data from IndexedDB
 */
export async function getTripData(tripId: string) {
    const database = await initDB();
    return await database.get('trips', tripId);
}

/**
 * Clear all data for a specific trip
 */
export async function clearTripData(tripId: string) {
    const database = await initDB();
    const tx = database.transaction(['messages', 'trips'], 'readwrite');

    // Delete all messages for this trip
    const messages = await tx.objectStore('messages').getAll();
    for (const msg of messages) {
        if (msg.trip_id === tripId) {
            await tx.objectStore('messages').delete(msg.id);
        }
    }

    // Delete trip data
    await tx.objectStore('trips').delete(tripId);

    await tx.done;
}

/**
 * Get database statistics
 */
export async function getDBStats() {
    const database = await initDB();

    const messages = await database.getAll('messages');
    const pendingMessages = await database.getAll('pending_messages');
    const trips = await database.getAll('trips');

    return {
        totalMessages: messages.length,
        pendingMessages: pendingMessages.length,
        trips: trips.length,
        unsynced: messages.filter((m) => !m.synced).length,
    };
}

/**
 * Clear all offline data (for logout/testing)
 */
export async function clearAllData() {
    const database = await initDB();

    await database.clear('messages');
    await database.clear('pending_messages');
    await database.clear('trips');
}
