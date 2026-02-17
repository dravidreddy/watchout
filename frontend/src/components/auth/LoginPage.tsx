'use client';

import { motion } from 'framer-motion';
import { Plane, MapPin, Calendar, Users } from 'lucide-react';
import { useAuth } from '@/components/auth/AuthProvider';

export function LoginPage() {
    const { login, isLoading } = useAuth();

    const handleLogin = async () => {
        await login();
    };


    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4">
            {/* Animated Background */}
            <div className="absolute inset-0 overflow-hidden">
                <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob" />
                <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-pink-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000" />
                <div className="absolute top-1/2 left-1/2 w-80 h-80 bg-yellow-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-4000" />
            </div>

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="relative z-10 max-w-md w-full"
            >
                {/* Logo */}
                <div className="text-center mb-8">
                    <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ delay: 0.2, type: 'spring' }}
                        className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-purple-500 to-pink-500 mb-4"
                    >
                        <Plane className="w-10 h-10 text-white" />
                    </motion.div>
                    <h1 className="text-4xl font-bold text-white mb-2">Watchout</h1>
                    <p className="text-purple-200">Your AI Travel Companion</p>
                </div>

                {/* Features */}
                <div className="space-y-3 mb-8">
                    {[
                        { icon: MapPin, text: 'Personalized Itineraries' },
                        { icon: Calendar, text: 'Smart Day Planning' },
                        { icon: Users, text: 'Group Trip Support' }
                    ].map((feature, i) => (
                        <motion.div
                            key={i}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.3 + i * 0.1 }}
                            className="flex items-center gap-3 text-white/80"
                        >
                            <feature.icon className="w-5 h-5 text-purple-400" />
                            <span>{feature.text}</span>
                        </motion.div>
                    ))}
                </div>

                {/* Login Button */}
                <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={handleLogin}
                    disabled={isLoading}
                    className="w-full py-4 px-6 bg-white text-slate-900 rounded-2xl font-semibold flex items-center justify-center gap-3 hover:bg-white/90 transition-colors disabled:opacity-50"
                >
                    <svg className="w-5 h-5" viewBox="0 0 24 24">
                        <path
                            fill="currentColor"
                            d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                        />
                        <path
                            fill="currentColor"
                            d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                        />
                        <path
                            fill="currentColor"
                            d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                        />
                        <path
                            fill="currentColor"
                            d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                        />
                    </svg>
                    Continue with Google
                </motion.button>

                {/* Dev Login Button Removed */}

                <p className="text-center text-white/50 text-sm mt-6">
                    By continuing, you agree to our Terms of Service
                </p>
            </motion.div>
        </div>
    );
}

export default LoginPage;
