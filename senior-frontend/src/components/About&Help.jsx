import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  BadgeInfo,
  CircleHelp,
  Menu,
  ShieldCheck,
  Sparkles,
  Store,
  Wallet,
} from "lucide-react";
import AuthService from "../services/authService";
import SidebarNav from "./SidebarNav";

const HOW_IT_WORKS = [
  {
    title: "Search once",
    description: "Enter a product name or URL and we start checking supported stores.",
    icon: Sparkles,
  },
  {
    title: "Compare clearly",
    description: "We align item price, shipping, and delivery in one consistent view.",
    icon: Wallet,
  },
  {
    title: "Pick confidently",
    description: "Results are ranked so you can quickly spot value, speed, and trust.",
    icon: ShieldCheck,
  },
];

const FAQ_ITEMS = [
  {
    question: "How long does a search usually take?",
    answer: "Most searches finish in under a minute. Timing depends on store response speed and product availability.",
  },
  {
    question: "Do prices include shipping?",
    answer: "Yes. We show item price, shipping fee, and total cost when data is available from the store.",
  },
  {
    question: "Why do some stores not show results?",
    answer: "A store may have no matching product, temporary issues, or limited data for that item.",
  },
  {
    question: "Can I trust seller ratings and rankings?",
    answer: "Rankings combine pricing, delivery, and store quality signals to give a balanced recommendation.",
  },
];

const AboutHelp = () => {
  const navigate = useNavigate();
  const currentUser = AuthService.getUser();
  const username = currentUser?.username || currentUser?.name || "User";
  const profileInitial = username.trim().charAt(0).toUpperCase() || "U";

  const [isDesktopSidebarOpen, setIsDesktopSidebarOpen] = useState(true);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    if (!AuthService.isAuthenticated()) {
      navigate("/login");
      return;
    }

    const handleResize = () => {
      if (window.innerWidth >= 768) {
        setIsMobileMenuOpen(false);
      }
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [navigate]);

  const handleLogout = async () => {
    await AuthService.logout();
    navigate("/login");
  };

  return (
    <div className="min-h-screen bg-slate-900 text-white font-sans flex overflow-hidden relative selection:bg-indigo-500 selection:text-white">
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-[-10%] left-[-10%] w-[800px] h-[800px] bg-blue-600/10 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[600px] h-[600px] bg-indigo-600/10 rounded-full blur-[120px]" />
      </div>

      <SidebarNav
        activeTab="about"
        onLogout={handleLogout}
        isDesktopSidebarOpen={isDesktopSidebarOpen}
        setIsDesktopSidebarOpen={setIsDesktopSidebarOpen}
        isMobileMenuOpen={isMobileMenuOpen}
        setIsMobileMenuOpen={setIsMobileMenuOpen}
      />

      <main className="flex-1 relative z-10 overflow-y-auto h-screen">
        <header className="h-20 flex items-center justify-between px-4 md:px-8 border-b border-white/5 bg-slate-900/20 backdrop-blur-md sticky top-0 z-30">
          <div className="flex items-center gap-4 min-w-0">
            <button
              onClick={() => setIsMobileMenuOpen(true)}
              className="md:hidden p-2 text-slate-400 hover:text-white"
            >
              <Menu className="w-6 h-6" />
            </button>
            <h1 className="text-lg md:text-xl font-medium text-slate-200 truncate">
              <span className="text-white font-bold">About & Help</span>
            </h1>
          </div>

          <div
            className="w-9 h-9 rounded-full bg-gradient-to-r from-emerald-400 to-teal-500 border-2 border-slate-800 shadow-lg flex items-center justify-center text-sm font-bold text-slate-950"
            title={username}
          >
            {profileInitial}
          </div>
        </header>

        <div className="p-4 md:p-8 max-w-6xl mx-auto space-y-6 pb-20">
          <section className="rounded-3xl border border-white/10 bg-white/5 backdrop-blur-md p-6 md:p-8 space-y-4">
            <div className="flex items-center gap-3">
              <BadgeInfo className="w-6 h-6 text-blue-300" />
              <h2 className="text-2xl md:text-3xl font-bold">What PriceTracker Does</h2>
            </div>
            <p className="text-slate-300 leading-relaxed max-w-3xl">
              PriceTracker helps you compare product offers across multiple stores in one place. Our goal is to save
              you time and reduce guesswork by showing price, delivery, and trust-related details in a clear format.
            </p>
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-400/30 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-200">
              <Store className="w-4 h-4" />
              Comparison-focused shopping assistant
            </div>
          </section>

          <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {HOW_IT_WORKS.map((step) => {
              const Icon = step.icon;

              return (
                <article
                  key={step.title}
                  className="rounded-2xl border border-white/10 bg-white/5 p-5 hover:bg-white/[0.07] transition-colors"
                >
                  <Icon className="w-6 h-6 text-blue-300 mb-3" />
                  <h3 className="text-lg font-bold mb-2">{step.title}</h3>
                  <p className="text-sm text-slate-300 leading-relaxed">{step.description}</p>
                </article>
              );
            })}
          </section>

          <section className="rounded-3xl border border-white/10 bg-white/5 p-5 md:p-7 space-y-5">
            <div className="flex items-center gap-2">
              <CircleHelp className="w-5 h-5 text-indigo-300" />
              <h3 className="text-xl font-bold">Frequently Asked Questions</h3>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 md:gap-4">
              {FAQ_ITEMS.map((item) => (
                <div key={item.question} className="rounded-xl border border-white/10 bg-slate-900/40 p-4">
                  <p className="font-semibold text-white text-sm md:text-base">{item.question}</p>
                  <p className="text-sm text-slate-300 mt-2 leading-relaxed">{item.answer}</p>
                </div>
              ))}
            </div>
          </section>
        </div>
      </main>
    </div>
  );
};

export default AboutHelp;