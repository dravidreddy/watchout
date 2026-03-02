'use client';

import { motion, Variants } from 'framer-motion';
import { Plane, Compass, Sparkles, MapPin, Wallet, Zap, ArrowRight, Star } from 'lucide-react';
import { useAuth } from '@/components/auth/AuthProvider';

export function LoginPage() {
    const { login, isLoading } = useAuth();

    // Smooth animation variants
    const fadeUp: Variants = {
        hidden: { opacity: 0, y: 30 },
        visible: { opacity: 1, y: 0, transition: { duration: 0.8, ease: [0.16, 1, 0.3, 1] } }
    };

    const staggerContainer: Variants = {
        hidden: { opacity: 0 },
        visible: {
            opacity: 1,
            transition: { staggerChildren: 0.15, delayChildren: 0.2 }
        }
    };

    return (
        <div className="min-h-screen bg-black text-white overflow-hidden selection:bg-accent selection:text-white">

            {/* Ambient Background Glows */}
            <div className="fixed inset-0 z-0 pointer-events-none">
                <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-accent/20 rounded-full blur-[120px]" />
                <div className="absolute top-[40%] right-[-10%] w-[30%] h-[50%] bg-indigo-600/10 rounded-full blur-[120px]" />
            </div>

            {/* Navbar */}
            <nav className="relative z-50 flex items-center justify-between px-6 py-6 md:px-12 max-w-7xl mx-auto">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-gradient-to-br from-accent to-indigo-600 shadow-[0_0_20px_rgba(8,145,178,0.3)]">
                        <Plane className="w-5 h-5 text-white" />
                    </div>
                    <span className="font-bold text-xl tracking-tight">Watchout.</span>
                </div>
                <button
                    onClick={login}
                    disabled={isLoading}
                    className="px-5 py-2.5 text-sm font-medium rounded-full glass hover:bg-white/10 transition-colors border-white/10"
                >
                    Sign In
                </button>
            </nav>

            <main className="relative z-10">
                {/* Hero Section */}
                <section className="pt-20 pb-32 px-6 md:px-12 max-w-7xl mx-auto flex flex-col items-center text-center">
                    <motion.div
                        initial="hidden"
                        animate="visible"
                        variants={staggerContainer}
                        className="max-w-4xl flex flex-col items-center"
                    >
                        <motion.div variants={fadeUp} className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-white/10 bg-white/5 backdrop-blur-md mb-8">
                            <Sparkles className="w-4 h-4 text-accent" />
                            <span className="text-xs font-medium tracking-wide text-gray-300 uppercase">Watchout AI 2.0 is live</span>
                        </motion.div>

                        <motion.h1 variants={fadeUp} className="text-6xl md:text-8xl font-bold tracking-tighter leading-[1.1] mb-6">
                            The World,<br />
                            <span className="text-transparent bg-clip-text bg-gradient-to-r from-white via-gray-200 to-gray-500">
                                Curated by AI.
                            </span>
                        </motion.h1>

                        <motion.p variants={fadeUp} className="text-lg md:text-xl text-gray-400 max-w-2xl mb-10 leading-relaxed font-light">
                            Experience travel planning that feels like magic. Watchout analyzes your vibe to build the perfect, hyper-personalized itinerary in seconds.
                        </motion.p>

                        <motion.div variants={fadeUp} className="flex flex-col sm:flex-row gap-4 w-full sm:w-auto">
                            <button
                                onClick={login}
                                disabled={isLoading}
                                className="group relative inline-flex items-center justify-center gap-3 px-8 py-4 bg-white text-black font-semibold rounded-full overflow-hidden transition-transform hover:scale-105 active:scale-95"
                            >
                                <span className="absolute inset-0 w-full h-full bg-gradient-to-r from-accent/0 via-accent/10 to-accent/0 group-hover:animate-shimmer" />
                                <span className="relative flex items-center gap-2">
                                    {isLoading ? 'Connecting...' : 'Start Your Journey'}
                                    <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                                </span>
                            </button>
                        </motion.div>
                    </motion.div>
                </section>

                {/* Interface Showcase Showcase (3D Angled) */}
                <section className="relative w-full max-w-5xl mx-auto px-6 pb-32 perspective-1000">
                    <motion.div
                        initial={{ opacity: 0, y: 100, rotateX: 20 }}
                        whileInView={{ opacity: 1, y: 0, rotateX: 0 }}
                        viewport={{ once: true, margin: "-100px" }}
                        transition={{ duration: 1, ease: "easeOut" }}
                        className="relative rounded-2xl border border-white/10 bg-[#0A0A0A]/80 backdrop-blur-2xl shadow-[0_0_100px_rgba(8,145,178,0.15)] overflow-hidden"
                    >
                        {/* Fake Browser header */}
                        <div className="flex items-center gap-2 px-4 py-3 border-b border-white/5 bg-white/5">
                            <div className="w-3 h-3 rounded-full bg-white/20" />
                            <div className="w-3 h-3 rounded-full bg-white/20" />
                            <div className="w-3 h-3 rounded-full bg-white/20" />
                        </div>
                        {/* Fake Chat UI */}
                        <div className="p-8 flex flex-col gap-6">
                            <div className="flex gap-4 max-w-lg">
                                <div className="w-8 h-8 rounded-full bg-accent/20 flex items-center justify-center shrink-0">
                                    <Sparkles className="w-4 h-4 text-accent" />
                                </div>
                                <div className="p-4 rounded-2xl rounded-tl-sm bg-white/5 border border-white/10 text-sm text-gray-300 leading-relaxed">
                                    I've analyzed your preference for minimalist architecture and quiet evenings. I've curated a 5-day itinerary in Kyoto, avoiding major tourist traps and focusing on serene Zen gardens and private tea ceremonies. Shall we review the route?
                                </div>
                            </div>
                            <div className="flex gap-4 max-w-sm self-end flex-row-reverse">
                                <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center shrink-0">
                                    <div className="w-4 h-4 bg-white/40 rounded-full" />
                                </div>
                                <div className="p-4 rounded-2xl rounded-tr-sm bg-white text-black font-medium text-sm leading-relaxed">
                                    This looks incredible. Can we keep the daily budget under $150?
                                </div>
                            </div>

                            {/* Floating Itinerary Card Overlay */}
                            <div className="absolute bottom-8 right-8 p-4 rounded-xl border border-white/10 bg-black/60 backdrop-blur-xl shadow-2xl flex items-center gap-4 animate-float">
                                <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-accent to-indigo-600 flex items-center justify-center">
                                    <MapPin className="w-6 h-6 text-white" />
                                </div>
                                <div>
                                    <p className="text-sm font-semibold text-white">Route Optimized</p>
                                    <p className="text-xs text-accent">Saved 2h 15m travel time</p>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                </section>

                {/* Bento Grid Features */}
                <section className="px-6 md:px-12 max-w-7xl mx-auto pb-40">
                    <motion.div
                        initial="hidden"
                        whileInView="visible"
                        viewport={{ once: true, margin: "-100px" }}
                        variants={staggerContainer}
                        className="grid grid-cols-1 md:grid-cols-3 gap-6"
                    >
                        {/* Large Card */}
                        <motion.div variants={fadeUp} className="md:col-span-2 group relative p-8 rounded-3xl border border-white/10 bg-[#0A0A0A] overflow-hidden">
                            <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                            <Wallet className="w-8 h-8 text-accent mb-6" />
                            <h3 className="text-2xl font-bold mb-3">Live Infinite Budgeting</h3>
                            <p className="text-gray-400 leading-relaxed max-w-md">Our AI dynamically reallocates your budget in real-time. Splurge on a Michelin dinner, and Watchout instantly finds cheaper transport tomorrow to keep you perfectly balanced.</p>
                        </motion.div>

                        {/* Tall Card */}
                        <motion.div variants={fadeUp} className="group relative p-8 rounded-3xl border border-white/10 bg-[#0A0A0A] overflow-hidden flex flex-col justify-between">
                            <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/10 rounded-full blur-[50px] group-hover:bg-indigo-500/20 transition-colors duration-500" />
                            <Compass className="w-8 h-8 text-indigo-400 mb-6" />
                            <div>
                                <h3 className="text-2xl font-bold mb-3">Vibe Matching</h3>
                                <p className="text-gray-400 leading-relaxed">Tell us your mood. We match you with destinations that resonate with your exact emotional frequency.</p>
                            </div>
                        </motion.div>

                        {/* Bottom Small Card 1 */}
                        <motion.div variants={fadeUp} className="group p-8 rounded-3xl border border-white/10 bg-[#0A0A0A] relative overflow-hidden">
                            <div className="absolute inset-0 bg-gradient-to-t from-accent/5 to-transparent" />
                            <Zap className="w-8 h-8 text-yellow-400 mb-6" />
                            <h3 className="text-xl font-bold mb-2">Lightning Fast</h3>
                            <p className="text-gray-400 text-sm">Complex 14-day itineraries generated in milliseconds.</p>
                        </motion.div>

                        {/* Bottom Small Card 2 */}
                        <motion.div variants={fadeUp} className="md:col-span-2 group p-8 rounded-3xl border border-white/10 bg-[#0A0A0A] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
                            <div>
                                <Star className="w-8 h-8 text-white mb-6" />
                                <h3 className="text-2xl font-bold mb-2">Ready to redefine travel?</h3>
                                <p className="text-gray-400">Join the elite network of modern explorers.</p>
                            </div>
                            <button
                                onClick={login}
                                className="px-6 py-3 rounded-full bg-white/10 hover:bg-white/20 border border-white/10 font-medium transition-colors whitespace-nowrap"
                            >
                                Authenticate
                            </button>
                        </motion.div>

                    </motion.div>
                </section>

                {/* Footer */}
                <footer className="border-t border-white/10 py-12 text-center">
                    <p className="text-gray-500 text-sm">© {new Date().getFullYear()} Watchout. Curated by Intelligence.</p>
                </footer>
            </main>
        </div>
    );
}

export default LoginPage;
