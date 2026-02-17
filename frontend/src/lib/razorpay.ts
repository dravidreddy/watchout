import { api } from './api';

export const loadRazorpay = (): Promise<boolean> => {
    return new Promise((resolve) => {
        if (typeof window === 'undefined') return resolve(false);

        const script = document.createElement('script');
        script.src = 'https://checkout.razorpay.com/v1/checkout.js';
        script.async = true;
        script.onload = () => resolve(true);
        script.onerror = () => resolve(false);
        document.body.appendChild(script);
    });
};

interface CheckoutOptions {
    planId: string;
    amount: number;
    email: string;
    name: string;
    onSuccess: (tier: string) => void;
    onError: (error: string) => void;
}

export const openCheckout = async (options: CheckoutOptions) => {
    const isLoaded = await loadRazorpay();
    if (!isLoaded) {
        options.onError('Failed to load Razorpay SDK');
        return;
    }

    try {
        const order = await api.createOrder(options.amount);

        const rzpOptions = {
            key: process.env.NEXT_PUBLIC_RAZORPAY_KEY_ID || 'rzp_test_dummy_id',
            amount: order.amount,
            currency: order.currency,
            name: 'Bharat Voyager',
            description: `Upgrade to ${options.planId}`,
            order_id: order.id,
            handler: async (response: any) => {
                try {
                    const result = await api.verifyPayment({
                        ...response,
                        plan_id: options.planId
                    });
                    if (result.status === 'success') {
                        options.onSuccess(result.tier);
                    } else {
                        options.onError('Payment verification failed');
                    }
                } catch (e) {
                    options.onError('Verification failed');
                }
            },
            prefill: {
                name: options.name,
                email: options.email
            },
            theme: {
                color: '#0891B2'
            }
        };

        const rzp = new (window as any).Razorpay(rzpOptions);
        rzp.open();
    } catch (error) {
        options.onError('Failed to create order');
    }
};
