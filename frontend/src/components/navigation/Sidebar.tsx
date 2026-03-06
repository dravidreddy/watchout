'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Home, Briefcase, Compass, User, HelpCircle, Plus, MessageSquarePlus } from 'lucide-react';
import { motion } from 'framer-motion';
import { useAppStore } from '@/lib/appStore';
import { useDragResize } from '@/hooks/useDragResize';

const navItems = [
    { name: 'Home', href: '/home', icon: Home },
    { name: 'Chat', href: '/chat', icon: MessageSquarePlus },
    { name: 'Trips', href: '/trips', icon: Briefcase },
    { name: 'Explore', href: '/explore', icon: Compass },
    { name: 'Profile', href: '/profile', icon: User },
];

const bottomItems = [
    { name: 'Support', href: '/support', icon: HelpCircle },
];

export function Sidebar() {
    const pathname = usePathname();
    const { isSidebarOpen } = useAppStore();
    const { panelWidth, handleProps, isDragging } = useDragResize({
        edge: 'right',
        initialWidth: 256,
        minWidth: 180,
        maxWidth: 400,
        storageKey: 'sidebar-width',
    });

    const NavLink = ({ item }: { item: typeof navItems[0] }) => {
        const isActive = pathname === item.href || pathname.startsWith(item.href + '/');

        return (
            <Link href={item.href}>
                <motion.div
                    whileHover={{ x: 4 }}
                    className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all cursor-pointer ${isActive
                        ? 'bg-[var(--accent-50)]'
                        : 'hover:bg-[var(--bg-tertiary)]'
                        }`}
                >
                    <item.icon
                        className="w-5 h-5"
                        style={{
                            color: isActive ? 'var(--accent)' : 'var(--text-secondary)'
                        }}
                    />
                    <span
                        className="font-medium truncate"
                        style={{
                            color: isActive ? 'var(--accent-dark)' : 'var(--text-primary)'
                        }}
                    >
                        {item.name}
                    </span>
                    {isActive && (
                        <motion.div
                            layoutId="activeSidebar"
                            className="ml-auto w-1.5 h-1.5 rounded-full flex-shrink-0"
                            style={{ background: 'var(--accent)' }}
                        />
                    )}
                </motion.div>
            </Link>
        );
    };

    return (
        <aside
            className={`hidden md:flex flex-col h-screen fixed left-0 top-0 z-30 transition-transform duration-300 ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
                }`}
            style={{
                width: panelWidth,
                background: 'var(--bg-secondary)',
                borderRight: '1px solid var(--border-subtle)'
            }}
        >
            {/* Logo */}
            <div className="p-6 pb-4">
                <Link href="/home" className="flex items-center gap-3">
                    <div
                        className="w-10 h-10 rounded-xl flex items-center justify-center text-white font-bold text-lg shadow-[0_0_20px_rgba(8,145,178,0.3)]"
                        style={{
                            background: 'linear-gradient(135deg, #0891B2 0%, #4F46E5 100%)'
                        }}
                    >
                        W
                    </div>
                    <div>
                        <h1 className="font-semibold" style={{ color: 'var(--text-primary)' }}>
                            Watchout
                        </h1>
                        <p className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
                            AI Travel Planner
                        </p>
                    </div>
                </Link>
            </div>

            {/* New Trip Button */}
            <div className="px-4 mb-6">
                <Link href="/chat?new=true">
                    <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        className="w-full flex items-center justify-center gap-2 py-3 rounded-xl text-white font-medium"
                        style={{
                            background: 'linear-gradient(135deg, #0891B2 0%, #4F46E5 100%)',
                            boxShadow: '0 4px 20px rgba(8, 145, 178, 0.3)'
                        }}
                    >
                        <Plus className="w-5 h-5" />
                        New Trip
                    </motion.button>
                </Link>
            </div>

            {/* Navigation */}
            <nav className="flex-1 px-3">
                <div className="space-y-1">
                    {navItems.map((item) => (
                        <NavLink key={item.name} item={item} />
                    ))}
                </div>
            </nav>

            {/* Bottom Items */}
            <div className="px-3 pb-6 mt-auto">
                <div className="pt-4" style={{ borderTop: '1px solid var(--border-subtle)' }}>
                    {bottomItems.map((item) => (
                        <NavLink key={item.name} item={item} />
                    ))}
                </div>
            </div>

            {/* Drag handle — sits on the right edge */}
            <div
                {...handleProps}
                className={`absolute top-0 right-0 w-[5px] h-full z-50 group cursor-col-resize flex items-center justify-center`}
                style={{ touchAction: 'none' }}
            >
                {/* Visual pill that appears on hover / while dragging */}
                <div
                    className={`w-[3px] h-12 rounded-full transition-all duration-150 ${isDragging
                            ? 'opacity-100 scale-y-110'
                            : 'opacity-0 group-hover:opacity-100'
                        }`}
                    style={{ background: 'var(--accent)' }}
                />
            </div>
        </aside>
    );
}

export default Sidebar;
