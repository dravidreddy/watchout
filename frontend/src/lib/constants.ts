// Shared constants for consistent user preference options across the app.

export const TRAVEL_STYLES = [
    'Adventure',
    'Relaxation',
    'Cultural',
    'Family',
    'Budget',
    'Luxury',
] as const;

export const BUDGET_RANGES = ['Budget', 'Mid-range', 'Luxury'] as const;

export const LANGUAGES = ['English', 'Hindi', 'Spanish', 'French', 'German'] as const;

export type TravelStyle = (typeof TRAVEL_STYLES)[number];
export type BudgetRange = (typeof BUDGET_RANGES)[number];
export type Language = (typeof LANGUAGES)[number];
