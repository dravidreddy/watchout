import { useState, useCallback } from 'react';

export interface LocationPermissionState {
    status: 'prompt' | 'granted' | 'denied' | 'unavailable';
    coordinates: { lat: number; lng: number } | null;
    error: string | null;
}

export function useLocationPermission() {
    const [state, setState] = useState<LocationPermissionState>({
        status: 'prompt',
        coordinates: null,
        error: null
    });

    const requestPermission = useCallback(async (): Promise<boolean> => {
        try {
            // Check if geolocation is available
            if (!navigator.geolocation) {
                setState({
                    status: 'unavailable',
                    coordinates: null,
                    error: 'Geolocation is not supported by your browser'
                });
                return false;
            }

            // Request permission
            const position = await new Promise<GeolocationPosition>((resolve, reject) => {
                navigator.geolocation.getCurrentPosition(resolve, reject, {
                    timeout: 5000,
                    enableHighAccuracy: false,
                    maximumAge: 60000 // Use cached position if less than 1 minute old
                });
            });

            setState({
                status: 'granted',
                coordinates: {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                },
                error: null
            });

            return true;
        } catch (error: any) {
            if (error.code === 1) {
                // User denied permission (PERMISSION_DENIED)
                setState({
                    status: 'denied',
                    coordinates: null,
                    error: 'Location access was denied'
                });
            } else if (error.code === 2) {
                // Position unavailable (POSITION_UNAVAILABLE)
                setState({
                    status: 'denied',
                    coordinates: null,
                    error: 'Location information is unavailable'
                });
            } else if (error.code === 3) {
                // Timeout (TIMEOUT)
                setState({
                    status: 'denied',
                    coordinates: null,
                    error: 'Location request timed out'
                });
            } else {
                setState({
                    status: 'denied',
                    coordinates: null,
                    error: error.message || 'Failed to get location'
                });
            }

            return false;
        }
    }, []);

    const reset = useCallback(() => {
        setState({
            status: 'prompt',
            coordinates: null,
            error: null
        });
    }, []);

    return {
        ...state,
        requestPermission,
        reset
    };
}
