'use client';

import { useEffect } from 'react';
import { User } from 'firebase/auth';
import { onAuthChange, signInWithGoogle, signOut } from '@/lib/firebase';
import { useAuthStore } from '@/lib/store';
import { api } from '@/lib/api';

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const { setUser, setLoading } = useAuthStore();

    useEffect(() => {
        // Set loading to false after a timeout as fallback
        const timeout = setTimeout(() => {
            setLoading(false);
        }, 3000);

        const unsubscribe = onAuthChange(async (firebaseUser: User | null) => {
            clearTimeout(timeout);

            // Skip all auth syncing during E2E tests to rely purely on Zustand mock
            if (process.env.NEXT_PUBLIC_TEST_MODE === 'true') {
                setLoading(false);
                return;
            }

            if (firebaseUser) {
                try {
                    // Sync with backend
                    const dbUser = await api.login({
                        firebase_id: firebaseUser.uid,
                        email: firebaseUser.email || '',
                        name: firebaseUser.displayName || undefined,
                        photo_url: firebaseUser.photoURL || undefined
                    });
                    setUser(dbUser);
                } catch (error) {
                    console.error('Failed to sync user with backend:', error);
                    // Fallback to minimal data if backend fails
                    setUser({
                        _id: firebaseUser.uid,
                        firebase_id: firebaseUser.uid,
                        email: firebaseUser.email || '',
                        name: firebaseUser.displayName || undefined,
                        photo_url: firebaseUser.photoURL || undefined,
                        preferences: {} as any,
                        onboarding_completed: false,
                        subscription_tier: 'free'
                    });
                }
            } else {
                // Check if Dev Bypass is requested
                const isDevBypass = typeof window !== 'undefined' && localStorage.getItem('watchout_dev_bypass') === 'true';
                if (isDevBypass && process.env.NEXT_PUBLIC_ENV === 'development' && process.env.NEXT_PUBLIC_DEV_BYPASS) {
                    try {
                        const dbUser = await api.getProfile();
                        setUser(dbUser);
                    } catch (e) {
                        console.error('Dev bypass failed', e);
                        setUser(null);
                    }
                } else {
                    setUser(null);
                }
            }
            setLoading(false);
        });

        return () => {
            clearTimeout(timeout);
            unsubscribe();
        };
    }, [setUser, setLoading]);

    return <>{children}</>;
}

export function useAuth() {
    const { user, setUser, isLoading, isAuthenticated, logout: storeLogout } = useAuthStore();

    const login = async () => {
        const user = await signInWithGoogle();
        return user;
    };

    const logout = async () => {
        await signOut();
        if (typeof window !== 'undefined') localStorage.removeItem('watchout_dev_bypass');
        storeLogout();
    };

    const devLogin = () => {
        if (process.env.NEXT_PUBLIC_ENV === 'development') {
            localStorage.setItem('watchout_dev_bypass', 'true');
            window.location.reload();
        }
    };

    return {
        user,
        setUser,
        isLoading,
        isAuthenticated,
        login,
        logout,
        devLogin
    };
}
