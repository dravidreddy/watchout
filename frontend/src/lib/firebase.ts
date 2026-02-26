'use client';

import { initializeApp, getApps, FirebaseApp } from 'firebase/app';
import {
    getAuth,
    signInWithPopup,
    GoogleAuthProvider,
    signOut as firebaseSignOut,
    onAuthStateChanged,
    User,
    Auth
} from 'firebase/auth';

const firebaseConfig = {
    apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY || (process.env.NEXT_PUBLIC_DEV_BYPASS ? "mock-api-key" : undefined),
    authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN || "mock-auth-domain",
    projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID || "mock-project-id",
    storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
    messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
    appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID
};

const isMockMode = firebaseConfig.apiKey === "mock-api-key";

// Initialize Firebase only on the client side
let app: FirebaseApp | undefined;
let auth: Auth | undefined;
let googleProvider: GoogleAuthProvider | undefined;

function getFirebaseApp(): FirebaseApp {
    if (isMockMode) {
        throw new Error("Cannot get Firebase App in Mock Mode");
    }
    if (!app) {
        app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0];
    }
    return app;
}

function getFirebaseAuth(): Auth {
    if (isMockMode) {
        throw new Error("Cannot get Firebase Auth in Mock Mode");
    }
    if (!auth) {
        auth = getAuth(getFirebaseApp());
    }
    return auth;
}

function getGoogleProvider(): GoogleAuthProvider {
    if (isMockMode) {
        throw new Error("Cannot get Google Provider in Mock Mode");
    }
    if (!googleProvider) {
        googleProvider = new GoogleAuthProvider();
    }
    return googleProvider;
}

export async function signInWithGoogle(): Promise<User | null> {
    if (isMockMode) {
        console.warn("Google Sign-In disabled in Mock Mode");
        return null;
    }
    try {
        const result = await signInWithPopup(getFirebaseAuth(), getGoogleProvider());
        return result.user;
    } catch (error) {
        console.error('Google sign-in error:', error);
        return null;
    }
}

export async function signOut(): Promise<void> {
    if (isMockMode) {
        // Mock sign out
        return;
    }
    try {
        await firebaseSignOut(getFirebaseAuth());
    } catch (error) {
        console.error('Sign-out error:', error);
    }
}

export function onAuthChange(callback: (user: User | null) => void) {
    if (isMockMode) {
        // Immediately return null user (since we rely on Dev Bypass)
        // Set a small timeout to simulate async init
        setTimeout(() => callback(null), 0);
        return () => { }; // No-op unsubscribe
    }
    return onAuthStateChanged(getFirebaseAuth(), callback);
}

export async function getIdToken(): Promise<string | null> {
    if (isMockMode) {
        return "mock-firebase-token";
    }
    try {
        const authInstance = getFirebaseAuth();
        const user = authInstance.currentUser;
        if (!user) return null;

        // Force refresh if token is about to expire (handled by Firebase automatically, 
        // but we can force it if needed)
        return await user.getIdToken();
    } catch (error) {
        console.error('Get token error:', error);
        return null;
    }
}

export { getFirebaseAuth as auth };
