import React from "react";
import { useNavigate } from "react-router-dom";
import { Home, History, User, Info, LogOut, Zap, ChevronRight, X } from "lucide-react";

const SidebarNav = ({
  activeTab,
  onLogout,
  isDesktopSidebarOpen,
  setIsDesktopSidebarOpen,
  isMobileMenuOpen,
  setIsMobileMenuOpen,
}) => {
  const navigate = useNavigate();

  const handleNavigate = (path) => {
    setIsMobileMenuOpen(false);
    navigate(path);
  };

  return (
    <>
      {isMobileMenuOpen && (
        <div
          className="fixed inset-0 bg-slate-900/80 backdrop-blur-sm z-40 md:hidden"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      <aside
        className={`
          fixed md:static inset-y-0 left-0 z-50
          bg-slate-900/50 backdrop-blur-xl border-r border-white/5
          transition-all duration-300 ease-in-out flex flex-col
          ${isMobileMenuOpen ? "translate-x-0 w-64" : "-translate-x-full md:translate-x-0"}
          ${isDesktopSidebarOpen ? "md:w-64" : "md:w-20"}
        `}
      >
        <button
          onClick={() => setIsMobileMenuOpen(false)}
          className="absolute top-4 right-4 p-2 text-slate-400 hover:text-white md:hidden"
        >
          <X className="w-6 h-6" />
        </button>

        <button
          onClick={() => setIsDesktopSidebarOpen(!isDesktopSidebarOpen)}
          className="hidden md:flex absolute -right-3 top-24 bg-blue-600 rounded-full p-1 border border-slate-900 text-white shadow-lg hover:bg-blue-500 transition-colors z-50"
        >
          <ChevronRight
            className={`w-4 h-4 transition-transform ${isDesktopSidebarOpen ? "rotate-180" : ""}`}
          />
        </button>

        <div className="h-20 flex items-center justify-center border-b border-white/5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-linear-to-tr from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20 shrink-0">
              <Zap className="w-6 h-6 text-white" />
            </div>
            <span
              className={`font-bold text-lg tracking-tight transition-opacity duration-200 ${
                !isDesktopSidebarOpen && "md:opacity-0 md:hidden"
              }`}
            >
              PriceTracker
            </span>
          </div>
        </div>

        <nav className="flex-1 py-8 px-4 space-y-2 overflow-y-auto">
          <NavItem
            icon={Home}
            label="Home"
            active={activeTab === "home"}
            onClick={() => handleNavigate("/home")}
            showLabel={isDesktopSidebarOpen}
          />
          <NavItem
            icon={History}
            label="Search History"
            active={activeTab === "history"}
            onClick={() => handleNavigate("/search-history")}
            showLabel={isDesktopSidebarOpen}
          />
          <NavItem
            icon={User}
            label="My Account"
            active={activeTab === "account"}
            onClick={() => handleNavigate("/account")}
            showLabel={isDesktopSidebarOpen}
          />
          <NavItem
            icon={Info}
            label="About & Help"
            active={activeTab === "about"}
            onClick={() => handleNavigate("/about-help")}
            showLabel={isDesktopSidebarOpen}
          />
        </nav>

        <div className="p-4 border-t border-white/5">
          <button
            onClick={onLogout}
            className={`flex items-center gap-3 w-full p-3 rounded-xl hover:bg-red-500/10 text-slate-400 hover:text-red-400 transition-all ${
              !isDesktopSidebarOpen && "md:justify-center"
            }`}
            title="Sign Out"
          >
            <LogOut className="w-5 h-5 shrink-0" />
            <span
              className={`font-medium text-sm whitespace-nowrap transition-all ${
                !isDesktopSidebarOpen && "md:hidden"
              }`}
            >
              Sign Out
            </span>
          </button>
        </div>
      </aside>
    </>
  );
};

const NavItem = ({ icon: Icon, label, active, onClick, showLabel }) => (
  <button
    onClick={onClick}
    className={`w-full flex items-center gap-4 p-3 rounded-xl transition-all duration-200 group relative
      ${active ? "bg-blue-600 text-white shadow-lg shadow-blue-600/20" : "text-slate-400 hover:bg-white/5 hover:text-white"}
      ${!showLabel ? "md:justify-center" : ""}
    `}
    title={!showLabel ? label : ""}
  >
    <Icon className={`w-5 h-5 shrink-0 ${active ? "text-white" : "text-slate-400 group-hover:text-white"}`} />
    <span
      className={`font-medium text-sm whitespace-nowrap transition-all ${
        !showLabel && "md:hidden"
      }`}
    >
      {label}
    </span>
    {active && showLabel && (
      <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-white/20 rounded-r-full"></div>
    )}
  </button>
);

export default SidebarNav;
