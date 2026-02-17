'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Search, Bell, ChevronDown, Settings, LogOut, User } from 'lucide-react';
import { useAuth } from '@/components/auth/AuthProvider';

export function TopBar() {
    const { user, logout } = useAuth();
    const [showUserMenu, setShowUserMenu] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');

    return (
        <header
            className="hidden md:flex items-center justify-between h-16 px-6 fixed top-0 right-0 z-20"
            style={{
                left: '256px', // Sidebar width
                background: 'var(--bg-primary)',
                borderBottom: '1px solid rgba(0,0,0,0.05)'
            }}
        >
            {/* Search Bar */}
            <div className="flex-1 max-w-xl">
                <div className="relative">
                    <Search
                        className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5"
                        style={{ color: 'var(--text-tertiary)' }}
                    />
                    <input
                        type="text"
                        placeholder="Search trips, destinations, or ask AI..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-10 pr-4 py-2.5 rounded-xl transition-all"
                        style={{
                            background: 'var(--bg-secondary)',
                            border: '1px solid rgba(0,0,0,0.05)',
                            color: 'var(--text-primary)'
                        }}
                    />
                </div>
            </div>

            {/* Right Section */}
            <div className="flex items-center gap-4 ml-6">
                {/* Notifications */}
                <button
                    className="relative p-2 rounded-lg transition-colors hover:bg-[var(--bg-tertiary)]"
                >
                    <Bell className="w-5 h-5" style={{ color: 'var(--text-secondary)' }} />
                    <span
                        className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full"
                        style={{ background: 'var(--error)' }}
                    />
                </button>

                {/* User Menu */}
                <div className="relative">
                    <button
                        onClick={() => setShowUserMenu(!showUserMenu)}
                        className="flex items-center gap-3 p-1.5 pr-3 rounded-xl transition-colors hover:bg-[var(--bg-tertiary)]"
                    >
                        {user?.photo_url ? (
                            <img
                                src={user.photo_url}
                                alt={user?.name || 'User'}
                                className="w-8 h-8 rounded-lg object-cover"
                            />
                        ) : (
                            <div
                                className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-sm font-medium"
                                style={{ background: 'var(--accent)' }}
                            >
                                {user?.name?.[0] || user?.email?.[0] || '?'}
                            </div>
                        )}
                        <span
                            className="font-medium text-sm hidden lg:block"
                            style={{ color: 'var(--text-primary)' }}
                        >
                            {user?.name?.split(' ')[0] || 'User'}
                        </span>
                        <ChevronDown
                            className={`w-4 h-4 transition-transform duration-200 ${showUserMenu ? 'rotate-180' : ''}`}
                            style={{ color: 'var(--text-tertiary)' }}
                        />
                    </button>

                    {showUserMenu && (
                        <>
                            {/* Backdrop */}
                            <div
                                className="fixed inset-0 z-10"
                                onClick={() => setShowUserMenu(false)}
                            />

                            {/* Dropdown */}
                            <div
                                className="absolute right-0 top-full mt-2 w-56 py-2 rounded-xl z-20 animate-scale-in"
                                style={{
                                    background: 'var(--bg-secondary)',
                                    boxShadow: 'var(--shadow-xl)'
                                }}
                            >
                                <div className="px-4 py-2 mb-1" style={{ borderBottom: '1px solid rgba(0,0,0,0.05)' }}>
                                    <p className="font-medium" style={{ color: 'var(--text-primary)' }}>
                                        {user?.name || 'Traveler'}
                                    </p>
                                    <p className="text-sm" style={{ color: 'var(--text-tertiary)' }}>
                                        {user?.email}
                                    </p>
                                </div>


                                <Link
                                    href="/profile"
                                    onClick={() => setShowUserMenu(false)}
                                    className="flex items-center gap-3 px-4 py-2.5 transition-colors hover:bg-[var(--bg-tertiary)]"
                                >
                                    <User className="w-4 h-4" style={{ color: 'var(--text-secondary)' }} />
                                    <span style={{ color: 'var(--text-primary)' }}>Profile</span>
                                </Link>

                                <Link
                                    href="/settings"
                                    onClick={() => setShowUserMenu(false)}
                                    className="flex items-center gap-3 px-4 py-2.5 transition-colors hover:bg-[var(--bg-tertiary)]"
                                >
                                    <Settings className="w-4 h-4" style={{ color: 'var(--text-secondary)' }} />
                                    <span style={{ color: 'var(--text-primary)' }}>Settings</span>
                                </Link>

                                <div style={{ borderTop: '1px solid rgba(0,0,0,0.05)', marginTop: '0.5rem', paddingTop: '0.5rem' }}>
                                    <button
                                        onClick={() => {
                                            setShowUserMenu(false);
                                            logout();
                                        }}
                                        className="flex items-center gap-3 px-4 py-2.5 w-full transition-colors hover:bg-red-50"
                                    >
                                        <LogOut className="w-4 h-4" style={{ color: 'var(--error)' }} />
                                        <span style={{ color: 'var(--error)' }}>Sign Out</span>
                                    </button>
                                </div>
                            </div>
                        </>
                    )}
                </div>
            </div>
        </header>
    );
}

export default TopBar;
