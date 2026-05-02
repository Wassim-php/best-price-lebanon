import React, { useState, useEffect } from "react";
import { useNavigate, Link, useLocation } from "react-router-dom";
import { 
  Search, History,
  TrendingUp, Package, ChevronRight, Menu, Loader2, AlertCircle, Check, Medal
} from "lucide-react";
import ProductService from "../services/productService";
import AuthService from "../services/authService";
import HistoryService, { mapSearchDetailsToComparisonResults, normalizeSearchHistory } from "../services/historyService";
import SidebarNav from "./SidebarNav";

const SIMPLE_LOADING_MESSAGES = [
  "Analyzing your query",
  "Searching stores",
  "Comparing prices and delivery",
  "Preparing your results",
];

const getResultKey = (item) => {
  if (!item) return "";
  return [
    item.product?.url,
    item.product?.title,
    item.source,
    item.pricing?.total_price,
  ].filter(Boolean).join("|");
};

const HomePage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const currentUser = AuthService.getUser();
  const username = currentUser?.username || currentUser?.name || "User";
  const profileInitial = username.trim().charAt(0).toUpperCase() || "U";
  const [searchQuery, setSearchQuery] = useState("");
  
  // State for Desktop (Wide vs Slim)
  const [isDesktopSidebarOpen, setIsDesktopSidebarOpen] = useState(true);
  
  // State for Mobile (Open vs Closed)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // Comparison Results States
  const [comparisonResults, setComparisonResults] = useState(null);
  const [isLoadingComparison, setIsLoadingComparison] = useState(false);
  const [comparisonError, setComparisonError] = useState("");
  const [expandedRecommendations, setExpandedRecommendations] = useState({});
  const [recentSearches, setRecentSearches] = useState([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [isClearingHistory, setIsClearingHistory] = useState(false);
  const [handledNavigationSearchId, setHandledNavigationSearchId] = useState(null);
  const [loadingMessageIndex, setLoadingMessageIndex] = useState(0);

  useEffect(() => {
    if (!isLoadingComparison) {
      setLoadingMessageIndex(0);
      return undefined;
    }

    const intervalId = window.setInterval(() => {
      setLoadingMessageIndex((currentIndex) => (currentIndex + 1) % SIMPLE_LOADING_MESSAGES.length);
    }, 7000);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [isLoadingComparison]);

  const handleRecentSearchClick = async (searchItem) => {
    if (!searchItem?.id) {
      setSearchQuery(searchItem?.query || "");
      return;
    }

    setSearchQuery(searchItem.query || "");
    setComparisonError("");
    setIsLoadingComparison(true);

    try {
      const details = await HistoryService.getSearchDetails(searchItem.id);
      setComparisonResults(mapSearchDetailsToComparisonResults(details));
    } catch (error) {
      setComparisonError(error.message || "Failed to load this search details.");
    } finally {
      setIsLoadingComparison(false);
    }
  };

  const handleClearHistory = async () => {
    const confirmed = window.confirm("Are you sure you want to clear your search history?");
    if (!confirmed) return;

    setIsClearingHistory(true);
    try {
      await HistoryService.clearHistory();
      setRecentSearches([]);
      setComparisonResults(null);
      setComparisonError("");
    } catch (error) {
      setComparisonError(error.message || "Failed to clear search history.");
    } finally {
      setIsClearingHistory(false);
    }
  };

  // Close mobile menu automatically when screen resizes to desktop
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 768) {
        setIsMobileMenuOpen(false);
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  useEffect(() => {
    let isMounted = true;

    const loadSearchHistory = async () => {
      setIsLoadingHistory(true);
      try {
        const historyResponse = await HistoryService.getUserSearchHistory();
        if (isMounted) {
          setRecentSearches(normalizeSearchHistory(historyResponse).slice(0, 3));
        }
      } catch (_error) {
        if (isMounted) {
          setRecentSearches([]);
        }
      } finally {
        if (isMounted) {
          setIsLoadingHistory(false);
        }
      }
    };

    loadSearchHistory();

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    const selectedSearchId = location.state?.historySearchId;
    const selectedQuery = location.state?.historyQuery;

    if (!selectedSearchId || selectedSearchId === handledNavigationSearchId) {
      return;
    }

    const loadSelectedSearchDetails = async () => {
      setHandledNavigationSearchId(selectedSearchId);
      setSearchQuery(selectedQuery || "");
      setComparisonError("");
      setIsLoadingComparison(true);

      try {
        const details = await HistoryService.getSearchDetails(selectedSearchId);
        setComparisonResults(mapSearchDetailsToComparisonResults(details));
      } catch (error) {
        setComparisonError(error.message || "Failed to load this search details.");
      } finally {
        setIsLoadingComparison(false);
        navigate(location.pathname, { replace: true, state: null });
      }
    };

    loadSelectedSearchDetails();
  }, [location, handledNavigationSearchId, navigate]);

  const handleLogout = async () => {
    await AuthService.logout();
    navigate("/login");
  };

  const toggleRecommendation = (key) => {
    setExpandedRecommendations((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) {
      setComparisonError("Please enter a product name or URL");
      return;
    }

    setIsLoadingComparison(true);
    setComparisonError("");
    setComparisonResults(null);

    try {
      const results = await ProductService.compare({ query: searchQuery });
      setComparisonResults(results);
    } catch (error) {
      setComparisonError(error.message || "Failed to compare products. Please try again.");
    } finally {
      setIsLoadingComparison(false);
    }
  };

  // --- MOCK DATA ---
  const trendingItems = [
    { id: 1, name: "iPhone 15 Pro", price: "$999", change: "-12%", vendor: "Ishtari" },
    { id: 2, name: "Sony WH-1000XM5", price: "$348", change: "-5%", vendor: "Amazon" },
    { id: 3, name: "MacBook Air M2", price: "$1050", change: "+2%", vendor: "Makhsoom" },
  ];

  const renderProductCard = (product, cardKey, options = {}) => {
    const isExpanded = !!expandedRecommendations[cardKey];
    const rankingBadges = options.rankingBadges || [];

    return (
      <div
        key={cardKey}
        className="bg-white/5 border border-white/10 rounded-2xl p-5 backdrop-blur-md hover:bg-white/[0.07] transition-all hover:shadow-lg hover:shadow-blue-500/10 group cursor-pointer"
      >
        {rankingBadges.length > 0 && (
          <div className="mb-4 flex flex-wrap gap-2">
            {rankingBadges.map((badge) => (
              <span
                key={badge.label}
                className="inline-flex items-center gap-1 rounded-full bg-amber-400/10 px-3 py-1 text-xs font-bold text-amber-300 border border-amber-400/20"
              >
                <Medal className="w-3.5 h-3.5" />
                {badge.label}: {badge.value}
              </span>
            ))}
          </div>
        )}

        <div className="flex gap-4">
          <div className="w-20 h-20 rounded-xl bg-slate-800/50 flex-shrink-0 overflow-hidden flex items-center justify-center border border-white/5">
            {product.product?.image_url ? (
              <img
                src={product.product.image_url}
                alt={product.product.title}
                className="w-full h-full object-cover"
              />
            ) : (
              <Package className="w-8 h-8 text-slate-600" />
            )}
          </div>

          <div className="flex-1 flex flex-col justify-between min-w-0">
            <div>
              <h5 className="font-bold text-white group-hover:text-blue-300 transition-colors line-clamp-2 text-sm">
                {product.product?.title}
              </h5>
              <p className="text-xs text-slate-400 mt-1">
                {product.source} • {product.store_rating}⭐
              </p>
            </div>

            <div className="flex items-end justify-between gap-2">
              <div>
                <p className="text-emerald-400 text-lg font-bold">${product.pricing?.total_price}</p>
                <p className="text-xs text-slate-400">{product.delivery_days}d delivery</p>
              </div>
              <div className="bg-white/10 px-2 py-1 rounded text-xs font-semibold text-slate-300">
                {product.score?.toFixed(1)}/10
              </div>
            </div>
          </div>
        </div>

        <div className="mt-4 flex items-center gap-3">
          <button
            type="button"
            onClick={() => toggleRecommendation(cardKey)}
            className="flex-1 bg-white/10 hover:bg-white/15 text-white text-sm font-semibold py-2 rounded-lg transition-colors"
          >
            {isExpanded ? "Hide Details" : "View Details"}
          </button>
          <Link
            to={product.product?.url || "#"}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 text-center bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold py-2 rounded-lg transition-colors"
          >
            Go to Store
          </Link>
        </div>

        {isExpanded && (
          <div className="mt-4 p-4 rounded-xl bg-slate-900/60 border border-white/10 space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-400">Item Price</span>
              <span className="text-white font-medium">${product.pricing?.item_price ?? "N/A"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Shipping</span>
              <span className="text-white font-medium">${product.pricing?.shipping_fee ?? 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Delivery Time</span>
              <span className="text-white font-medium">{product.pricing?.delivery_time || product.pricing?.breakdown?.delivery_time || "N/A"}</span>
            </div>
            <div className="grid grid-cols-3 gap-2 mt-2">
              <div className="rounded-lg bg-white/5 p-2 text-center">
                <p className="text-[11px] text-slate-400">Price</p>
                <p className="text-indigo-400 font-bold">{product.score_breakdown?.price_score?.toFixed(1) ?? "N/A"}</p>
              </div>
              <div className="rounded-lg bg-white/5 p-2 text-center">
                <p className="text-[11px] text-slate-400">Delivery</p>
                <p className="text-blue-400 font-bold">{product.score_breakdown?.delivery_score?.toFixed(1) ?? "N/A"}</p>
              </div>
              <div className="rounded-lg bg-white/5 p-2 text-center">
                <p className="text-[11px] text-slate-400">Trust</p>
                <p className="text-emerald-400 font-bold">{product.score_breakdown?.trust_score?.toFixed(1) ?? "N/A"}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-slate-900 text-white font-sans flex overflow-hidden relative selection:bg-indigo-500 selection:text-white">
      
      {/* --- BACKGROUND ATMOSPHERE --- */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-[-10%] left-[-10%] w-[800px] h-[800px] bg-blue-600/10 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[600px] h-[600px] bg-indigo-600/10 rounded-full blur-[120px]" />
      </div>

      {/* --- MOBILE OVERLAY BACKDROP --- */}
      <SidebarNav
        activeTab="home"
        onLogout={handleLogout}
        isDesktopSidebarOpen={isDesktopSidebarOpen}
        setIsDesktopSidebarOpen={setIsDesktopSidebarOpen}
        isMobileMenuOpen={isMobileMenuOpen}
        setIsMobileMenuOpen={setIsMobileMenuOpen}
      />

      {/* --- MAIN CONTENT --- */}
      <main className="flex-1 relative z-10 overflow-y-auto h-screen">
        
        {/* Top Header */}
        <header className="h-20 flex items-center justify-between px-4 md:px-8 border-b border-white/5 bg-slate-900/20 backdrop-blur-md sticky top-0 z-30">
          
          {/* Mobile Menu Trigger & Welcome Text */}
          <div className="flex items-center gap-4">
            <button 
              onClick={() => setIsMobileMenuOpen(true)}
              className="md:hidden p-2 text-slate-400 hover:text-white"
            >
              <Menu className="w-6 h-6" />
            </button>
            <h1 className="text-lg md:text-xl font-medium text-slate-200 truncate">
              Hello, <span className="text-white font-bold">{username}</span>
            </h1>
          </div>

          <div className="flex items-center gap-4">
            <div
              className="w-9 h-9 rounded-full bg-gradient-to-r from-emerald-400 to-teal-500 border-2 border-slate-800 shadow-lg flex items-center justify-center text-sm font-bold text-slate-950"
              title={username}
            >
              {profileInitial}
            </div>
          </div>
        </header>

        <div className="p-4 md:p-8 max-w-6xl mx-auto space-y-12 pb-20">

          {/* 1. HERO SEARCH SECTION */}
          <div className="text-center space-y-6 mt-6 md:mt-10 animate-fade-in-up">
            <h2 className="text-3xl md:text-5xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-b from-white to-slate-400 px-2">
              Compare Prices Across Lebanon
            </h2>
            <p className="text-slate-400 text-base md:text-lg max-w-2xl mx-auto px-4">
              One search. 11+ stores. Best delivery times.
            </p>

            {/* THE GLOWING SEARCH BAR */}
            <form onSubmit={handleSearch} className="max-w-3xl mx-auto relative group z-20 px-2">
              <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl blur opacity-25 group-hover:opacity-40 transition duration-500"></div>
              <div className="relative flex items-center bg-slate-800/80 backdrop-blur-xl border border-white/10 rounded-2xl p-2 shadow-2xl transition-transform group-hover:scale-[1.01]">
                <Search className="w-5 h-5 md:w-6 md:h-6 text-slate-400 ml-2 md:ml-4 flex-shrink-0" />
                <input 
                  type="text" 
                  placeholder="Link or 'iPhone 15'..." 
                  className="w-full bg-transparent border-none outline-none text-white text-base md:text-lg px-2 md:px-4 py-2 md:py-3 placeholder-slate-500 min-w-0"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
                <button 
                  type="submit"
                  disabled={isLoadingComparison}
                  className="bg-blue-600 hover:bg-blue-500 disabled:bg-blue-700/60 disabled:cursor-not-allowed text-white px-4 md:px-8 py-2 md:py-3 rounded-xl font-bold transition-all shadow-lg hover:shadow-blue-500/25 text-sm md:text-base whitespace-nowrap"
                >
                  {isLoadingComparison ? "Searching..." : "Search"}
                </button>
              </div>
            </form>
          </div>

          {/* COMPARISON RESULTS SECTION */}
          {isLoadingComparison && (
            <div className="py-12">
              <div className="mx-auto max-w-xl rounded-2xl border border-white/10 bg-white/5 p-6 text-center backdrop-blur-sm">
                <Loader2 className="w-9 h-9 animate-spin text-blue-400 mx-auto" />
                <p className="mt-4 text-base md:text-lg font-semibold text-white">
                  {SIMPLE_LOADING_MESSAGES[loadingMessageIndex]}
                </p>
                <div className="mt-2 flex items-center justify-center gap-1" aria-hidden="true">
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-300 animate-pulse" />
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-300 animate-pulse [animation-delay:200ms]" />
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-300 animate-pulse [animation-delay:400ms]" />
                </div>
                <p className="mt-2 text-sm text-slate-400">This can take up to 60 seconds depending on store response time.</p>
              </div>
            </div>
          )}

          {comparisonError && (
            <div className="bg-red-500/10 border border-red-500/50 rounded-2xl p-4 md:p-6 flex items-start gap-4 backdrop-blur-sm">
              <AlertCircle className="w-6 h-6 text-red-400 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="text-red-300 font-bold mb-1">Search Error</h3>
                <p className="text-red-200 text-sm">{comparisonError}</p>
              </div>
            </div>
          )}

          {comparisonResults && comparisonResults.results && comparisonResults.results.length > 0 && (
            <div className="space-y-8 animate-fade-in-up">
              <div className="text-center space-y-2 mb-8">
                <h3 className="text-2xl md:text-3xl font-bold">Search Results for "<span className="text-blue-400">{searchQuery}</span>"</h3>
                <p className="text-slate-400 text-sm">
                  Found {comparisonResults.results.length} option{comparisonResults.results.length !== 1 ? 's' : ''} • 
                  Best price: <span className="text-emerald-400 font-semibold">${comparisonResults.metadata?.min_price || 'N/A'}</span>
                </p>
              </div>

              {/* BEST DEAL - Featured Product */}
              {(() => {
                const sortedResults = [...comparisonResults.results].sort((a, b) => (b.score || 0) - (a.score || 0));
                const bestDeal = sortedResults[0];
                const byPrice = [...sortedResults].sort((a, b) => (a.pricing?.total_price || Infinity) - (b.pricing?.total_price || Infinity))[0];
                const byDelivery = [...sortedResults].sort((a, b) => (a.delivery_days || Infinity) - (b.delivery_days || Infinity))[0];
                const byReliability = [...sortedResults].sort((a, b) => (b.store_rating || 0) - (a.store_rating || 0))[0];
                const rankingSelections = [
                  { label: "Best Price", item: byPrice, value: byPrice?.pricing?.total_price ? `$${byPrice.pricing.total_price}` : "N/A" },
                  { label: "Best Delivery", item: byDelivery, value: byDelivery?.delivery_days ? `${byDelivery.delivery_days} days` : "N/A" },
                  { label: "Best Reliability", item: byReliability, value: byReliability?.store_rating ? `${byReliability.store_rating}/5` : "N/A" },
                ].filter((selection) => selection.item);
                const rankedProducts = rankingSelections.reduce((acc, selection) => {
                  const key = getResultKey(selection.item);
                  if (!key) return acc;

                  const existing = acc.find((rankedProduct) => rankedProduct.key === key);
                  if (existing) {
                    existing.rankingBadges.push({ label: selection.label, value: selection.value });
                  } else {
                    acc.push({
                      key,
                      item: selection.item,
                      rankingBadges: [{ label: selection.label, value: selection.value }],
                    });
                  }

                  return acc;
                }, []);
                const topProductKeys = new Set([
                  getResultKey(bestDeal),
                  ...rankedProducts.map((rankedProduct) => rankedProduct.key),
                ].filter(Boolean));
                const recommendations = sortedResults.filter((product) => !topProductKeys.has(getResultKey(product)));

                return (
                  <>
                    {/* Featured Card */}
                    <div className="relative">
                      <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-3xl blur-xl opacity-20"></div>
                      <div className="relative bg-gradient-to-br from-blue-600/20 to-indigo-600/20 border-2 border-blue-500/30 rounded-3xl p-6 md:p-8 backdrop-blur-md hover:border-blue-500/50 transition-all">
                        <div className="flex items-center gap-3 mb-4">
                          <span className="px-3 py-1 bg-blue-600 text-white text-xs font-bold rounded-full">⭐ BEST DEAL</span>
                          <span className="text-sm text-slate-300">Score: <span className="text-blue-400 font-bold">{bestDeal.score?.toFixed(1)}/10</span></span>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8">
                          {/* Product Image & Info */}
                          <div className="md:col-span-1 flex flex-col items-center justify-start">
                            <div className="w-full aspect-square bg-slate-800/50 rounded-2xl overflow-hidden mb-4 flex items-center justify-center border border-white/10">
                              {bestDeal.product?.image_url ? (
                                <img 
                                  src={bestDeal.product.image_url} 
                                  alt={bestDeal.product.title}
                                  className="w-full h-full object-cover hover:scale-110 transition-transform duration-300"
                                />
                              ) : (
                                <Package className="w-16 h-16 text-slate-600" />
                              )}
                            </div>
                            <div className="w-full space-y-2 text-sm">
                              {bestDeal.product?.in_stock && (
                                <div className="flex items-center gap-2 text-emerald-400">
                                  <Check className="w-4 h-4" />
                                  <span className="font-semibold">In Stock</span>
                                </div>
                              )}
                              <div className="text-slate-400">
                                <p className="text-xs">Store Rating</p>
                                <p className="text-white font-bold">⭐ {bestDeal.store_rating}/5</p>
                              </div>
                            </div>
                          </div>

                          {/* Product Details & Pricing */}
                          <div className="md:col-span-2 space-y-4">
                            <div>
                              <h3 className="text-2xl md:text-3xl font-bold text-white mb-2 line-clamp-2">
                                {bestDeal.product?.title}
                              </h3>
                              <p className="text-slate-400 text-sm line-clamp-2">From: <span className="text-blue-300 font-semibold capitalize">{bestDeal.source}</span></p>
                            </div>

                            {/* Pricing Breakdown */}
                            <div className="bg-slate-900/50 rounded-2xl p-4 space-y-2 border border-white/5">
                              <div className="flex justify-between items-center">
                                <span className="text-slate-400">Item Price:</span>
                                <span className="text-white font-bold">${bestDeal.pricing?.item_price}</span>
                              </div>
                              {bestDeal.pricing?.shipping_fee > 0 && (
                                <div className="flex justify-between items-center">
                                  <span className="text-slate-400">Shipping:</span>
                                  <span className="text-white font-bold">${bestDeal.pricing.shipping_fee}</span>
                                </div>
                              )}
                              <div className="border-t border-white/10 pt-2 flex justify-between items-center">
                                <span className="text-emerald-400 font-bold">Total Price:</span>
                                <span className="text-emerald-400 text-2xl font-bold">${bestDeal.pricing?.total_price}</span>
                              </div>
                            </div>

                            {/* Score Details */}
                            <div className="grid grid-cols-3 gap-3">
                              <div className="bg-white/5 rounded-xl p-3 text-center border border-white/5">
                                <p className="text-xs text-slate-400 mb-1">Price</p>
                                <p className="text-indigo-400 font-bold">{bestDeal.score_breakdown?.price_score?.toFixed(1)}</p>
                              </div>
                              <div className="bg-white/5 rounded-xl p-3 text-center border border-white/5">
                                <p className="text-xs text-slate-400 mb-1">Delivery</p>
                                <p className="text-blue-400 font-bold">{bestDeal.score_breakdown?.delivery_score?.toFixed(1)}</p>
                              </div>
                              <div className="bg-white/5 rounded-xl p-3 text-center border border-white/5">
                                <p className="text-xs text-slate-400 mb-1">Trust</p>
                                <p className="text-emerald-400 font-bold">{bestDeal.score_breakdown?.trust_score?.toFixed(1)}</p>
                              </div>
                            </div>

                            {/* Delivery Info */}
                            <div className="bg-white/5 rounded-xl p-4 border border-white/5 space-y-2">
                              <p className="text-sm text-slate-300">
                                <span className="font-semibold">📦 Delivery:</span> {bestDeal.delivery_days} business days
                              </p>
                              {bestDeal.pricing?.delivery_time && (
                                <p className="text-sm text-slate-300">
                                  <span className="font-semibold">⏱️ Time:</span> {bestDeal.pricing.delivery_time}
                                </p>
                              )}
                            </div>

                            {/* Action Button */}
                            <Link
                              to={bestDeal.product?.url || "#"}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="block w-full text-center bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 rounded-xl transition-all shadow-lg hover:shadow-blue-500/25"
                            >
                              View on Store →
                            </Link>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* RANKINGS */}
                    <div className="space-y-4 mt-8">
                      <h4 className="text-xl font-bold text-white">Top Rankings</h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {rankedProducts.map((rankedProduct) => (
                          renderProductCard(
                            rankedProduct.item,
                            `ranking-${rankedProduct.key}`,
                            { rankingBadges: rankedProduct.rankingBadges }
                          )
                        ))}
                      </div>
                    </div>

                    {/* RECOMMENDATIONS */}
                    {recommendations.length > 0 && (
                      <div className="space-y-4 mt-8">
                        <h4 className="text-xl font-bold text-white">Other Options</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {recommendations.map((product, idx) => (
                            renderProductCard(product, `recommendation-${getResultKey(product) || idx}`)
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                );
              })()}

              {/* Metadata Info */}
              {comparisonResults.metadata && (
                <div className="bg-white/5 border border-white/10 rounded-xl p-4 text-sm text-slate-400 space-y-1">
                  <p>📊 Checked {comparisonResults.metadata.sites_checked} stores • {comparisonResults.metadata.sites_succeeded} found results</p>
                  {comparisonResults.metadata.search_id && (
                    <p className="text-xs text-slate-500">Search ID: #{comparisonResults.metadata.search_id}</p>
                  )}
                </div>
              )}
            </div>
          )}

          {comparisonResults && (!comparisonResults.results || comparisonResults.results.length === 0) && (
            <div className="text-center py-12">
              <Package className="w-16 h-16 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-400 text-lg">No products found for your search.</p>
              <p className="text-slate-500 text-sm mt-2">Try a different search or check back later.</p>
            </div>
          )}

          {/* 2. DASHBOARD WIDGETS */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            {/* Widget: Trending */}
            <div className="md:col-span-2 bg-white/5 border border-white/10 rounded-3xl p-5 md:p-6 backdrop-blur-md hover:bg-white/[0.07] transition-colors">
              <div className="flex items-center justify-between mb-6">
                <h3 className="flex items-center gap-2 text-lg font-bold">
                  <TrendingUp className="w-5 h-5 text-emerald-400" /> Trending Deals
                </h3>
                <button className="text-xs font-bold text-slate-400 hover:text-white uppercase tracking-wider">View All</button>
              </div>
              <div className="space-y-4">
                {trendingItems.map((item) => (
                  <div key={item.id} className="flex items-center justify-between p-4 bg-white/5 rounded-2xl hover:bg-white/10 transition-colors cursor-pointer group border border-transparent hover:border-white/5">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-slate-700 rounded-xl flex items-center justify-center text-slate-400 group-hover:text-white transition-colors shadow-inner flex-shrink-0">
                        <Package className="w-6 h-6" />
                      </div>
                      <div className="min-w-0">
                        <h4 className="font-bold text-white group-hover:text-blue-300 transition-colors truncate">{item.name}</h4>
                        <p className="text-xs text-slate-400">{item.vendor}</p>
                      </div>
                    </div>
                    <div className="text-right flex-shrink-0 pl-2">
                      <p className="font-bold text-lg">{item.price}</p>
                      <span className="text-xs font-bold text-emerald-400 bg-emerald-400/10 px-2 py-1 rounded-md">{item.change}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Widget: Recent History */}
            <div className="bg-white/5 border border-white/10 rounded-3xl p-5 md:p-6 backdrop-blur-md flex flex-col hover:bg-white/[0.07] transition-colors">
              <h3 className="flex items-center gap-2 text-lg font-bold mb-6">
                <History className="w-5 h-5 text-blue-400" /> Recent Searches
              </h3>
              <div className="flex-1 space-y-3">
                {isLoadingHistory && (
                  <div className="flex items-center gap-2 text-slate-400 p-3">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span className="text-sm">Loading recent searches...</span>
                  </div>
                )}

                {!isLoadingHistory && recentSearches.length === 0 && (
                  <div className="p-3 rounded-xl text-slate-400 text-sm bg-white/5 border border-white/5">
                    No recent searches yet.
                  </div>
                )}

                {!isLoadingHistory && recentSearches.map((item, i) => (
                  <button
                    type="button"
                    key={`${item.id || item.query}-${i}`}
                    onClick={() => handleRecentSearchClick(item)}
                    className="w-full flex items-center justify-between p-3 rounded-xl hover:bg-white/5 cursor-pointer text-slate-300 hover:text-white transition-colors group"
                  >
                    <div className="min-w-0 text-left">
                      <span className="truncate block">{item.query}</span>
                      {item.minPrice != null && (
                        <span className="text-xs text-emerald-400">Best ${item.minPrice}</span>
                      )}
                    </div>
                    <ChevronRight className="w-4 h-4 text-slate-500 group-hover:translate-x-1 transition-transform flex-shrink-0" />
                  </button>
                ))}
              </div>
              <div className="mt-4 grid grid-cols-2 gap-2">
                <button
                  onClick={() => navigate("/search-history")}
                  className="py-3 rounded-xl border border-white/10 hover:bg-white/5 text-sm font-bold text-slate-300 transition-colors"
                >
                  View Full History
                </button>
                <button
                  onClick={handleClearHistory}
                  disabled={isClearingHistory || isLoadingHistory || recentSearches.length === 0}
                  className="py-3 rounded-xl border border-red-400/30 bg-red-500/5 hover:bg-red-500/10 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-bold text-red-300 transition-colors"
                >
                  {isClearingHistory ? "Clearing..." : "Clear History"}
                </button>
              </div>
            </div>

          </div>

        </div>
      </main>
    </div>
  );
};

export default HomePage;
