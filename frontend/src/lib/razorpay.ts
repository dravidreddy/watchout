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

export interface PaymentError {
    message: string;
    code: 'SDK_LOAD_FAILED' | 'ORDER_CREATION_FAILED' | 'VERIFICATION_FAILED' | 'CHECKOUT_DISMISSED';
    recoverable: boolean;
}

interface CheckoutOptions {
    planId: string;
    amount: number;
    email: string;
    name: string;
    onSuccess: (tier: string) => void;
    onError: (error: PaymentError) => void;
}

export const openCheckout = async (options: CheckoutOptions) => {
    const isLoaded = await loadRazorpay();
    if (!isLoaded) {
        options.onError({
            message: 'Failed to load payment gateway. Please check your internet connection and try again.',
            code: 'SDK_LOAD_FAILED',
            recoverable: true,
        });
        return;
    }

    try {
        const order = await api.createOrder(options.planId);

        const rzpOptions = {
            key: process.env.NEXT_PUBLIC_RAZORPAY_KEY_ID || 'rzp_test_dummy_id',
            amount: order.amount,
            currency: order.currency,
            name: 'Watchout',
            description: `Upgrade to ${options.planId}`,
            order_id: order.order_id,
            handler: async (response: any) => {
                try {
                    const result = await api.verifyPayment({
                        ...response,
                        plan_id: options.planId
                    });
                    if (result.status === 'success' || result.status === 'processing') {
                        options.onSuccess(result.tier || options.planId);
                    } else {
                        options.onError({
                            message: 'Payment verification failed. Your payment may still be processing — please wait a few minutes before retrying.',
                            code: 'VERIFICATION_FAILED',
                            recoverable: false,
                        });
                    }
                } catch (e) {
                    options.onError({
                        message: 'We could not verify your payment right now. If you were charged, your subscription will be activated automatically within a few minutes.',
                        code: 'VERIFICATION_FAILED',
                        recoverable: false,
                    });
                }
            },
            modal: {
                ondismiss: () => {
                    options.onError({
                        message: 'Payment was cancelled. You can try again anytime.',
                        code: 'CHECKOUT_DISMISSED',
                        recoverable: true,
                    });
                }
            },
            prefill: {
                email: options.email,
                name: options.name
            },
            theme: {
                color: '#667eea'
            }
        };

        const rzp = new (window as any).Razorpay(rzpOptions);
        rzp.open();
    } catch (error) {
        options.onError({
            message: 'Could not create a payment order. Please try again later.',
            code: 'ORDER_CREATION_FAILED',
            recoverable: true,
        });
    }
};
