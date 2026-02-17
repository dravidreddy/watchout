'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/components/auth/AuthProvider';
import LoginPage from '@/components/auth/LoginPage';

export default function Home() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      router.push('/home');
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
            className="w-16 h-16 rounded-2xl animate-pulse-soft flex items-center justify-center text-white font-bold text-2xl"
            style={{
              background: 'linear-gradient(135deg, #0891B2 0%, #06B6D4 100%)',
              boxShadow: '0 8px 32px rgba(8, 145, 178, 0.3)'
            }}
          >
            B
          </div>
          <h1 className="text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>
            Bharat Voyager
          </h1>
          <p className="text-sm" style={{ color: 'var(--text-tertiary)' }}>
            Loading...
          </p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  return null;
}
