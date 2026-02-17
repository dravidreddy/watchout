'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Home, Briefcase, Compass, User, HelpCircle, Plus } from 'lucide-react';
import { motion } from 'framer-motion';

const navItems = [
    { name: 'Home', href: '/home', icon: Home },
    { name: 'Trips', href: '/trips', icon: Briefcase },
    { name: 'Explore', href: '/explore', icon: Compass },
    { name: 'Profile', href: '/profile', icon: User },
];

const bottomItems = [
    { name: 'Support', href: '/support', icon: HelpCircle },
];

export function Sidebar() {
    const pathname = usePathname();

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
                        className="font-medium"
                        style={{
                            color: isActive ? 'var(--accent-dark)' : 'var(--text-primary)'
                        }}
                    >
                        {item.name}
                    </span>
                    {isActive && (
                        <motion.div
                            layoutId="activeSidebar"
                            className="ml-auto w-1.5 h-1.5 rounded-full"
                            style={{ background: 'var(--accent)' }}
                        />
                    )}
                </motion.div>
            </Link>
        );
    };

    return (
        <aside
            className="hidden md:flex flex-col w-64 h-screen fixed left-0 top-0 z-30"
            style={{
                background: 'var(--bg-secondary)',
                borderRight: '1px solid rgba(0,0,0,0.05)'
            }}
        >
            {/* Logo */}
            <div className="p-6 pb-4">
                <Link href="/home" className="flex items-center gap-3">
                    <div
                        className="w-10 h-10 rounded-xl flex items-center justify-center text-white font-bold text-lg"
                        style={{
                            background: 'linear-gradient(135deg, #0891B2 0%, #06B6D4 100%)'
                        }}
                    >
                        B
                    </div>
                    <div>
                        <h1 className="font-semibold" style={{ color: 'var(--text-primary)' }}>
                            Bharat Voyager
                        </h1>
                        <p className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
                            AI Travel Planner
                        </p>
                    </div>
                </Link>
            </div>

            {/* New Trip Button */}
            <div className="px-4 mb-6">
                <Link href="/chat">
                    <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        className="w-full flex items-center justify-center gap-2 py-3 rounded-xl text-white font-medium"
                        style={{
                            background: 'linear-gradient(135deg, #0891B2 0%, #06B6D4 100%)',
                            boxShadow: '0 4px 12px rgba(8, 145, 178, 0.3)'
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
                <div className="pt-4" style={{ borderTop: '1px solid rgba(0,0,0,0.05)' }}>
                    {bottomItems.map((item) => (
                        <NavLink key={item.name} item={item} />
                    ))}
                </div>
            </div>
        </aside>
    );
}

export default Sidebar;
