'use client';

import { useRef, useEffect, useState, useCallback } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { useChatStore, RouteStop } from '@/lib/store';
import { Map as MapIcon, X } from 'lucide-react';
import * as turf from '@turf/turf';

const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN || '';

const DAY_COLORS = [
    '#8B5CF6', // purple
    '#3B82F6', // blue
    '#10B981', // emerald
    '#F59E0B', // amber
    '#EF4444', // red
    '#EC4899', // pink
    '#06B6D4', // cyan
    '#84CC16', // lime
];

const MARKER_DIMENSION = 32;

const createRouteMarkerElement = (label: string | number, color: string): HTMLDivElement => {
    const wrapper = document.createElement('div');
    wrapper.className = 'route-map-marker';

    const bubble = document.createElement('div');
    bubble.style.width = `${MARKER_DIMENSION}px`;
    bubble.style.height = `${MARKER_DIMENSION}px`;
    bubble.style.background = color;
    bubble.style.border = '3px solid white';
    bubble.style.borderRadius = '50%';
    bubble.style.display = 'flex';
    bubble.style.alignItems = 'center';
    bubble.style.justifyContent = 'center';
    bubble.style.fontSize = '14px';
    bubble.style.fontWeight = '700';
    bubble.style.color = 'white';
    bubble.style.boxShadow = '0 2px 8px rgba(0,0,0,0.4)';
    bubble.style.cursor = 'pointer';
    bubble.style.transition = 'transform 0.2s';
    bubble.textContent = String(label);

    wrapper.appendChild(bubble);
    return wrapper;
};

const createStopPopupContent = (stop: RouteStop, color: string): HTMLDivElement => {
    const root = document.createElement('div');
    root.style.padding = '8px';
    root.style.fontFamily = 'system-ui';
    root.style.maxWidth = '200px';

    const title = document.createElement('div');
    title.style.fontWeight = '600';
    title.style.fontSize = '14px';
    title.textContent = stop.name || 'Stop';
    root.appendChild(title);

    if (stop.city) {
        const city = document.createElement('div');
        city.style.fontSize = '12px';
        city.style.color = '#888';
        city.style.marginTop = '2px';
        city.textContent = `📍 ${stop.city}`;
        root.appendChild(city);
    }

    if (stop.day) {
        const day = document.createElement('div');
        day.style.fontSize = '11px';
        day.style.color = color;
        day.style.marginTop = '4px';
        day.style.fontWeight = '600';
        day.textContent = `Day ${stop.day}`;
        root.appendChild(day);
    }

    return root;
};

const createTravelMarkerElement = (): HTMLDivElement => {
    const wrapper = document.createElement('div');
    const dot = document.createElement('div');
    dot.style.width = '20px';
    dot.style.height = '20px';
    dot.style.background = '#8B5CF6';
    dot.style.border = '3px solid white';
    dot.style.borderRadius = '50%';
    dot.style.boxShadow = '0 0 12px rgba(139, 92, 246, 0.6), 0 0 24px rgba(139, 92, 246, 0.3)';
    dot.style.animation = 'pulse-glow 1.5s ease-in-out infinite';
    wrapper.appendChild(dot);
    return wrapper;
};

export default function RouteMap() {
    const mapContainer = useRef<HTMLDivElement>(null);
    const mapRef = useRef<mapboxgl.Map | null>(null);
    const markersRef = useRef<mapboxgl.Marker[]>([]);
    const animFrameRef = useRef<number>(0);
    const travelMarkerRef = useRef<mapboxgl.Marker | null>(null);

    const {
        routeData,
        routeStops,
        selectedDay,
        showMap,
        extractedItinerary,
        setSelectedDay,
        setShowMap,
    } = useChatStore();

    const [mapLoaded, setMapLoaded] = useState(false);
    const [isAnimating, setIsAnimating] = useState(false);

    // ── Initialize map ──────────────────────────────────────────────
    useEffect(() => {
        if (!mapContainer.current || mapRef.current || !MAPBOX_TOKEN) return;

        mapboxgl.accessToken = MAPBOX_TOKEN;

        const map = new mapboxgl.Map({
            container: mapContainer.current,
            style: 'mapbox://styles/mapbox/dark-v11',
            center: [78.9629, 20.5937], // India center
            zoom: 4.5,
            attributionControl: false,
            pitch: 0,
        });

        map.addControl(new mapboxgl.NavigationControl({ showCompass: false }), 'bottom-right');

        map.on('load', () => {
            setMapLoaded(true);
        });

        mapRef.current = map;

        return () => {
            cancelAnimationFrame(animFrameRef.current);
            map.remove();
            mapRef.current = null;
        };
    }, []);

    // ── Parse itinerary into stops ──────────────────────────────────
    useEffect(() => {
        if (!extractedItinerary) return;

        const itinerary = extractedItinerary?.raw_plan || extractedItinerary?.itinerary || extractedItinerary;
        const days = itinerary?.days || [];
        const stops: RouteStop[] = [];

        for (const day of days) {
            const dayNum = day.day_number || day.day || 0;
            const city = day.city || '';

            const activities = day.activities || day.stops || [];
            for (const act of activities) {
                if (act.latitude && act.longitude) {
                    stops.push({
                        name: act.name || act.title || city,
                        city,
                        lat: act.latitude,
                        lng: act.longitude,
                        day: dayNum,
                        type: 'activity',
                    });
                }
            }

            // If no geocoded activities, use the city name as a stop
            if (stops.filter(s => s.day === dayNum).length === 0 && city) {
                stops.push({
                    name: city,
                    city,
                    lat: 0,
                    lng: 0,
                    day: dayNum,
                    type: 'pitstop',
                });
            }
        }

        if (stops.length > 0) {
            useChatStore.getState().setRouteStops(stops);
        }
    }, [extractedItinerary]);

    // ── Draw route & markers ────────────────────────────────────────
    useEffect(() => {
        const map = mapRef.current;
        if (!map || !mapLoaded) return;

        // Clear existing markers
        markersRef.current.forEach(m => m.remove());
        markersRef.current = [];

        // Remove existing route layers/sources
        if (map.getLayer('route-line')) map.removeLayer('route-line');
        if (map.getLayer('route-line-bg')) map.removeLayer('route-line-bg');
        if (map.getSource('route')) map.removeSource('route');

        // Filter stops by selected day (0 = all days)
        const filteredStops = selectedDay === 0
            ? routeStops
            : routeStops.filter(s => s.day === selectedDay);

        const validStops = filteredStops.filter(s => s.lat !== 0 && s.lng !== 0);

        if (validStops.length === 0 && !routeData) return;

        // Add markers for stops
        for (let i = 0; i < validStops.length; i++) {
            const stop = validStops[i];
            const dayIdx = (stop.day || 1) - 1;
            const color = DAY_COLORS[dayIdx % DAY_COLORS.length];

            const markerLabel = i === 0 ? '🚩' : (i === validStops.length - 1 ? '🏁' : (stop.day || i + 1));
            const el = createRouteMarkerElement(markerLabel, color);
            const popup = new mapboxgl.Popup({ offset: 20, closeButton: false })
                .setDOMContent(createStopPopupContent(stop, color));

            const marker = new mapboxgl.Marker(el)
                .setLngLat([stop.lng, stop.lat])
                .setPopup(popup)
                .addTo(map);

            markersRef.current.push(marker);
        }

        // Draw route polyline
        if (routeData?.geometry?.coordinates?.length) {
            map.addSource('route', {
                type: 'geojson',
                data: {
                    type: 'Feature',
                    properties: {},
                    geometry: routeData.geometry as any,
                },
            });

            // Background line (wider, for glow effect)
            map.addLayer({
                id: 'route-line-bg',
                type: 'line',
                source: 'route',
                paint: {
                    'line-color': '#8B5CF6',
                    'line-width': 8,
                    'line-opacity': 0.3,
                    'line-blur': 3,
                },
            });

            // Main route line
            map.addLayer({
                id: 'route-line',
                type: 'line',
                source: 'route',
                paint: {
                    'line-color': '#8B5CF6',
                    'line-width': 4,
                    'line-opacity': 0.9,
                },
                layout: {
                    'line-cap': 'round',
                    'line-join': 'round',
                },
            });
        }

        // Fit bounds
        const allCoords: [number, number][] = [];
        validStops.forEach(s => allCoords.push([s.lng, s.lat]));
        if (routeData?.geometry?.coordinates) {
            allCoords.push(...routeData.geometry.coordinates);
        }

        if (allCoords.length > 1) {
            const bounds = new mapboxgl.LngLatBounds();
            allCoords.forEach(c => bounds.extend(c));
            map.fitBounds(bounds, { padding: 60, maxZoom: 12, duration: 1500 });
        } else if (allCoords.length === 1) {
            map.flyTo({ center: allCoords[0], zoom: 10, duration: 1500 });
        }

    }, [routeData, routeStops, selectedDay, mapLoaded]);

    // ── Animate traveling marker ────────────────────────────────────
    const startAnimation = useCallback(() => {
        const map = mapRef.current;
        if (!map || !routeData?.geometry?.coordinates || routeData.geometry.coordinates.length < 2) return;

        setIsAnimating(true);

        // Remove previous travel marker
        travelMarkerRef.current?.remove();

        const el = createTravelMarkerElement();

        const line = turf.lineString(routeData.geometry.coordinates);
        const totalLength = turf.length(line, { units: 'kilometers' });

        const travelMarker = new mapboxgl.Marker(el)
            .setLngLat(routeData.geometry.coordinates[0] as [number, number])
            .addTo(map);
        travelMarkerRef.current = travelMarker;

        const duration = 6000; // 6 seconds total animation
        const start = performance.now();

        function animate(now: number) {
            const elapsed = now - start;
            const t = Math.min(elapsed / duration, 1);

            // Ease-in-out
            const eased = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
            const distance = eased * totalLength;

            const point = turf.along(line, distance, { units: 'kilometers' });
            const coords = point.geometry.coordinates as [number, number];
            travelMarker.setLngLat(coords);

            if (t < 1) {
                animFrameRef.current = requestAnimationFrame(animate);
            } else {
                setIsAnimating(false);
            }
        }

        animFrameRef.current = requestAnimationFrame(animate);
    }, [routeData]);

    // Auto-start animation when route data arrives
    useEffect(() => {
        if (routeData?.geometry?.coordinates?.length && mapLoaded) {
            // Small delay so the map finishes fitting bounds first
            const timer = setTimeout(() => startAnimation(), 2000);
            return () => clearTimeout(timer);
        }
    }, [routeData, mapLoaded, startAnimation]);

    // ── Get unique days from stops ──────────────────────────────────
    const uniqueDays = Array.from(new Set(routeStops.map(s => s.day).filter(Boolean))).sort() as number[];

    if (!showMap) return null;

    return (
        <div className="route-map-panel">
            {/* Header */}
            <div className="route-map-header">
                <div className="flex items-center gap-2">
                    <MapIcon className="w-4 h-4" style={{ color: 'var(--accent)' }} />
                    <span className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>
                        Trip Route
                    </span>
                    {routeData && (
                        <span className="text-xs px-2 py-0.5 rounded-full" style={{ background: 'var(--accent-50)', color: 'var(--accent)' }}>
                            {routeData.distance_km ? `${routeData.distance_km} km` : `${routeStops.length} stops`}
                        </span>
                    )}
                </div>
                <button
                    onClick={() => setShowMap(false)}
                    className="p-1.5 rounded-lg transition-colors hover:bg-black/10"
                    title="Close map"
                >
                    <X className="w-4 h-4" style={{ color: 'var(--text-tertiary)' }} />
                </button>
            </div>

            {/* Day Selector */}
            {uniqueDays.length > 1 && (
                <div className="route-map-days">
                    <button
                        onClick={() => setSelectedDay(0)}
                        className={`route-day-tab ${selectedDay === 0 ? 'active' : ''}`}
                    >
                        All
                    </button>
                    {uniqueDays.map(day => (
                        <button
                            key={day}
                            onClick={() => setSelectedDay(day)}
                            className={`route-day-tab ${selectedDay === day ? 'active' : ''}`}
                            style={selectedDay === day ? { background: DAY_COLORS[(day - 1) % DAY_COLORS.length], color: 'white' } : {}}
                        >
                            Day {day}
                        </button>
                    ))}
                </div>
            )}

            {/* Map Container */}
            <div className="route-map-container">
                <div ref={mapContainer} className="route-map-canvas" />

                {/* Replay button */}
                {routeData && !isAnimating && (
                    <button
                        onClick={startAnimation}
                        className="route-map-replay"
                        title="Replay animation"
                    >
                        ▶ Replay
                    </button>
                )}

                {/* Loading state */}
                {!routeData && routeStops.length === 0 && (
                    <div className="route-map-loading">
                        <div className="route-map-loading-pulse" />
                        <span>Waiting for route data…</span>
                    </div>
                )}
            </div>
        </div>
    );
}
