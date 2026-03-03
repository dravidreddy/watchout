export interface NormalizedItineraryStop {
    time?: string;
    name: string;
    description?: string;
    duration_minutes?: number;
    category?: string;
    estimated_cost?: number;
    tips?: string;
}

export interface NormalizedItineraryDay {
    day_number: number;
    city: string;
    theme?: string;
    notes?: string;
    stops: NormalizedItineraryStop[];
}

export interface NormalizedItinerary {
    title?: string;
    cities?: string[];
    start_date?: string;
    num_days?: number;
    num_travelers?: number;
    budget_total?: number;
    summary?: string;
    days: NormalizedItineraryDay[];
    [key: string]: unknown;
}

function toPositiveInt(value: unknown): number | undefined {
    const n = Number(value);
    if (!Number.isFinite(n) || n <= 0) return undefined;
    return Math.round(n);
}

function toNonNegativeInt(value: unknown): number | undefined {
    const n = Number(value);
    if (!Number.isFinite(n) || n < 0) return undefined;
    return Math.round(n);
}

function toStringOrUndefined(value: unknown): string | undefined {
    if (typeof value !== 'string') return undefined;
    const trimmed = value.trim();
    return trimmed ? trimmed : undefined;
}

function normalizeStop(raw: any): NormalizedItineraryStop | null {
    if (!raw || typeof raw !== 'object') return null;
    const name = toStringOrUndefined(raw.name);
    if (!name) return null;

    return {
        name,
        time: toStringOrUndefined(raw.time) || toStringOrUndefined(raw.arrival_time) || toStringOrUndefined(raw.departure_time),
        description: toStringOrUndefined(raw.description),
        duration_minutes: toNonNegativeInt(raw.duration_minutes),
        category: toStringOrUndefined(raw.category),
        estimated_cost: toNonNegativeInt(raw.estimated_cost),
        tips: toStringOrUndefined(raw.tips),
    };
}

function normalizeDay(raw: any, index: number): NormalizedItineraryDay {
    const rawStops = Array.isArray(raw?.stops) ? raw.stops : Array.isArray(raw?.activities) ? raw.activities : [];
    const stops = rawStops
        .map((s: any) => normalizeStop(s))
        .filter((s: NormalizedItineraryStop | null): s is NormalizedItineraryStop => Boolean(s));

    return {
        day_number: toPositiveInt(raw?.day_number) || (index + 1),
        city: toStringOrUndefined(raw?.city) || toStringOrUndefined(raw?.destination) || 'Destination',
        theme: toStringOrUndefined(raw?.theme),
        notes: toStringOrUndefined(raw?.notes),
        stops,
    };
}

function normalizeBudget(raw: any): number | undefined {
    return toNonNegativeInt(raw?.budget_total)
        || toNonNegativeInt(raw?.total_estimated_budget)
        || toNonNegativeInt(raw?.total_estimated_cost);
}

export function normalizeItinerary(raw: any): NormalizedItinerary | null {
    if (!raw || typeof raw !== 'object') return null;

    const daysRaw = Array.isArray(raw.days) ? raw.days : [];
    const normalizedDays = daysRaw.map((d: any, index: number) => normalizeDay(d, index));

    // De-duplicate accidental repeated days while preserving order.
    const seen = new Set<string>();
    const uniqueDays: NormalizedItineraryDay[] = [];
    for (const day of normalizedDays) {
        const key = `${day.day_number}:${day.city.toLowerCase()}`;
        if (seen.has(key)) continue;
        seen.add(key);
        uniqueDays.push(day);
    }

    const resequencedDays = uniqueDays.map((d, index) => ({ ...d, day_number: index + 1 }));

    return {
        ...raw,
        title: toStringOrUndefined(raw.title),
        cities: Array.isArray(raw.cities) ? raw.cities.filter((c: any) => typeof c === 'string' && c.trim()) : undefined,
        start_date: toStringOrUndefined(raw.start_date),
        num_days: toPositiveInt(raw.num_days) || resequencedDays.length,
        num_travelers: toPositiveInt(raw.num_travelers),
        budget_total: normalizeBudget(raw),
        summary: toStringOrUndefined(raw.summary),
        days: resequencedDays,
    };
}
