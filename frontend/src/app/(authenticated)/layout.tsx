'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/components/auth/AuthProvider';
import { BottomNav } from '@/components/navigation/BottomNav';
import { Sidebar } from '@/components/navigation/Sidebar';
import { TopBar } from '@/components/navigation/TopBar';
import { useAppStore } from '@/lib/appStore';

export default function AuthenticatedLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const { isAuthenticated, isLoading } = useAuth();
    const router = useRouter();
    const { isSidebarOpen } = useAppStore();

    useEffect(() => {
        if (!isLoading && !isAuthenticated) {
            router.push('/');
        }
    }, [isAuthenticated, isLoading, router]);

    if (isLoading) {
        return (
            <div
                className="min-h-screen flex items-center justify-center"
                style={{ background: 'var(--bg-primary)' }}
            >
                <div className="flex flex-col items-center gap-4">
                    <div
                        className="w-12 h-12 rounded-xl animate-pulse-soft flex items-center justify-center text-white font-bold text-xl"
                        style={{ background: 'var(--accent)' }}
                    >
                        B
                    </div>
                    <p style={{ color: 'var(--text-tertiary)' }}>Loading...</p>
                </div>
            </div>
        );
    }

    if (!isAuthenticated) {
        return null;
    }

    return (
        <div
            className="min-h-screen"
            style={{ background: 'var(--bg-primary)' }}
        >
            {/* Desktop Navigation */}
            <Sidebar />
            <TopBar />

            {/* Main content area */}
            <main className={`pb-20 md:pb-0 md:pt-16 transition-all duration-300 ${isSidebarOpen ? 'md:pl-64' : 'md:pl-0'}`}>
                {children}
            </main>

            {/* Mobile Navigation */}
            <BottomNav />
        </div>
    );
}
