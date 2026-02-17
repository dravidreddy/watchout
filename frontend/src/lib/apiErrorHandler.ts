export const getFriendlyErrorMessage = (error: any): string => {
    if (typeof error === 'string') return error;

    // Handle Network Errors
    if (error.name === 'AbortError') {
        return 'Request timed out. Please check your internet connection and try again.';
    }

    if (error.message === 'Failed to fetch' || error.message?.includes('NetworkError')) {
        return 'Unable to connect to the server. Please check if you are online.';
    }

    // Handle ApiError (defined in api.ts)
    if (error.status) {
        switch (error.status) {
            case 400:
                return error.message || 'The request was invalid. Please check your input.';
            case 401:
                return 'Your session has expired. Please login again.';
            case 403:
                return "You don't have permission to perform this action.";
            case 404:
                return 'The requested resource was not found.';
            case 429:
                return 'Too many requests. Please slow down and try again later.';
            case 500:
                return 'Something went wrong on our end. We are working to fix it.';
            case 503:
                return 'Server is temporarily down for maintenance. Please try again in a few minutes.';
            default:
                return error.message || 'An unexpected error occurred.';
        }
    }

    return error.message || 'An unexpected error occurred. Please try again.';
};
