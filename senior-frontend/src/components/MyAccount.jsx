import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  AlertCircle,
  Building2,
  CheckCircle,
  Eye,
  EyeOff,
  KeyRound,
  Loader2,
  MapPin,
  Menu,
  ShieldCheck,
  User,
} from "lucide-react";
import AuthService from "../services/authService";
import SidebarNav from "./SidebarNav";

const PasswordField = ({
  label,
  name,
  value,
  onChange,
  placeholder,
  visible,
  onToggle,
  error,
}) => (
  <div>
    <label className="block text-xs font-bold text-blue-200 uppercase tracking-wider mb-2 ml-1">
      {label}
    </label>
    <div className="relative group">
      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
        <KeyRound
          className={`h-4 w-4 ${
            error ? "text-red-400" : "text-blue-300"
          } group-focus-within:text-white transition-colors`}
        />
      </div>
      <input
        type={visible ? "text" : "password"}
        name={name}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className={`block w-full pl-10 pr-11 py-3 bg-slate-800/50 border rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-1 transition-all text-sm font-medium ${
          error
            ? "border-red-500/50 focus:border-red-500 focus:ring-red-500"
            : "border-slate-600 focus:border-blue-500 focus:ring-blue-500"
        }`}
      />
      <button
        type="button"
        onClick={onToggle}
        className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-white"
        aria-label={visible ? "Hide password" : "Show password"}
      >
        {visible ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
      </button>
    </div>
    {error && <p className="text-red-300 text-xs mt-1 ml-1 font-medium">{error}</p>}
  </div>
);

const StatusMessage = ({ type, message }) => {
  if (!message) return null;

  const isSuccess = type === "success";
  const Icon = isSuccess ? CheckCircle : AlertCircle;

  return (
    <div
      className={`rounded-xl border p-3 flex items-center gap-3 ${
        isSuccess
          ? "bg-emerald-500/10 border-emerald-500/40 text-emerald-200"
          : "bg-red-500/10 border-red-500/40 text-red-200"
      }`}
    >
      <Icon className={`w-5 h-5 ${isSuccess ? "text-emerald-400" : "text-red-400"}`} />
      <p className="text-sm font-medium">{message}</p>
    </div>
  );
};

const MyAccount = () => {
  const navigate = useNavigate();
  const currentUser = AuthService.getUser();
  const username = currentUser?.username || currentUser?.name || "User";
  const email = currentUser?.email || "No email saved";
  const profileInitial = username.trim().charAt(0).toUpperCase() || "U";
  const isGoogleAccount = currentUser?.authProvider === "google";

  const [isDesktopSidebarOpen, setIsDesktopSidebarOpen] = useState(true);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isInsideBeirut, setIsInsideBeirut] = useState(Boolean(currentUser?.location));
  const [locationStatus, setLocationStatus] = useState({ type: "", message: "" });
  const [isSavingLocation, setIsSavingLocation] = useState(false);
  const [passwordForm, setPasswordForm] = useState({
    oldPassword: "",
    newPassword: "",
    confirmPassword: "",
  });
  const [passwordErrors, setPasswordErrors] = useState({});
  const [passwordStatus, setPasswordStatus] = useState({ type: "", message: "" });
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [visiblePasswords, setVisiblePasswords] = useState({
    oldPassword: false,
    newPassword: false,
    confirmPassword: false,
  });

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

  const handleLocationSelect = async (nextLocation) => {
    if (isSavingLocation || nextLocation === isInsideBeirut) return;

    const previousLocation = isInsideBeirut;
    setIsInsideBeirut(nextLocation);
    setLocationStatus({ type: "", message: "" });
    setIsSavingLocation(true);

    try {
      const response = await AuthService.updateLocation(nextLocation);
      setIsInsideBeirut(Boolean(response?.location ?? nextLocation));
      setLocationStatus({
        type: "success",
        message: "Location updated successfully.",
      });
    } catch (error) {
      setIsInsideBeirut(previousLocation);
      setLocationStatus({
        type: "error",
        message: error.message || "Failed to update location.",
      });
    } finally {
      setIsSavingLocation(false);
    }
  };

  const handlePasswordChange = (event) => {
    const { name, value } = event.target;
    setPasswordForm((prev) => ({ ...prev, [name]: value }));
    setPasswordErrors((prev) => ({ ...prev, [name]: "" }));
    setPasswordStatus({ type: "", message: "" });
  };

  const validatePasswordForm = () => {
    const errors = {};

    if (!passwordForm.oldPassword) errors.oldPassword = "Current password is required.";
    if (!passwordForm.newPassword) {
      errors.newPassword = "New password is required.";
    } else if (passwordForm.newPassword.length < 8) {
      errors.newPassword = "New password must be at least 8 characters.";
    }
    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      errors.confirmPassword = "Passwords do not match.";
    }
    if (
      passwordForm.oldPassword &&
      passwordForm.newPassword &&
      passwordForm.oldPassword === passwordForm.newPassword
    ) {
      errors.newPassword = "Choose a password different from the current one.";
    }

    return errors;
  };

  const handlePasswordSubmit = async (event) => {
    event.preventDefault();
    if (isChangingPassword) return;

    const errors = validatePasswordForm();
    if (Object.keys(errors).length > 0) {
      setPasswordErrors(errors);
      return;
    }

    setIsChangingPassword(true);
    setPasswordStatus({ type: "", message: "" });

    try {
      await AuthService.changePassword(passwordForm.oldPassword, passwordForm.newPassword);
      setPasswordForm({ oldPassword: "", newPassword: "", confirmPassword: "" });
      setPasswordStatus({
        type: "success",
        message: "Password changed successfully.",
      });
    } catch (error) {
      setPasswordStatus({
        type: "error",
        message: error.message || "Failed to change password.",
      });
    } finally {
      setIsChangingPassword(false);
    }
  };

  const togglePasswordVisibility = (field) => {
    setVisiblePasswords((prev) => ({ ...prev, [field]: !prev[field] }));
  };

  return (
    <div className="min-h-screen bg-slate-900 text-white font-sans flex overflow-hidden relative selection:bg-indigo-500 selection:text-white">
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-[-10%] left-[-10%] w-[800px] h-[800px] bg-blue-600/10 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[600px] h-[600px] bg-indigo-600/10 rounded-full blur-[120px]" />
      </div>

      <SidebarNav
        activeTab="account"
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
              <span className="text-white font-bold">My Account</span>
            </h1>
          </div>

          <div
            className="w-9 h-9 rounded-full bg-gradient-to-r from-emerald-400 to-teal-500 border-2 border-slate-800 shadow-lg flex items-center justify-center text-sm font-bold text-slate-950"
            title={username}
          >
            {profileInitial}
          </div>
        </header>

        <div className="p-4 md:p-8 max-w-5xl mx-auto space-y-6 pb-20">
          <section className="bg-white/5 border border-white/10 rounded-3xl p-6 md:p-8 backdrop-blur-md">
            <div className="flex flex-col md:flex-row md:items-center gap-5">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-r from-emerald-400 to-teal-500 flex items-center justify-center text-2xl font-bold text-slate-950 shadow-lg">
                {profileInitial}
              </div>
              <div className="min-w-0">
                <p className="flex items-center gap-2 text-slate-400 text-sm font-semibold">
                  <User className="w-4 h-4 text-blue-300" />
                  Account details
                </p>
                <h2 className="text-2xl md:text-3xl font-bold text-white truncate">{username}</h2>
                <p className="text-slate-400 truncate">{email}</p>
              </div>
            </div>
          </section>

          <div className={`grid grid-cols-1 gap-6 ${isGoogleAccount ? "" : "lg:grid-cols-2"}`}>
            <section className="bg-white/5 border border-white/10 rounded-3xl p-6 md:p-8 backdrop-blur-md">
              <div className="flex items-start justify-between gap-4 mb-6">
                <div>
                  <h2 className="text-xl md:text-2xl font-bold text-white">Delivery Location</h2>
                  <p className="text-sm text-slate-400 mt-1">
                    Used for delivery price and timing during comparisons.
                  </p>
                </div>
                {isSavingLocation && <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => handleLocationSelect(true)}
                  disabled={isSavingLocation}
                  className={`rounded-2xl border p-4 text-left transition-all ${
                    isInsideBeirut
                      ? "bg-blue-600 border-blue-400 shadow-lg shadow-blue-900/30"
                      : "bg-slate-800/50 border-slate-600 hover:bg-slate-700/50"
                  } disabled:cursor-not-allowed disabled:opacity-70`}
                >
                  <Building2 className="w-6 h-6 mb-3 text-white" />
                  <span className="block text-sm font-bold text-white">Inside Beirut</span>
                  <span className="block text-xs text-blue-100/80 mt-1">Beirut delivery zone</span>
                </button>

                <button
                  type="button"
                  onClick={() => handleLocationSelect(false)}
                  disabled={isSavingLocation}
                  className={`rounded-2xl border p-4 text-left transition-all ${
                    !isInsideBeirut
                      ? "bg-indigo-600 border-indigo-400 shadow-lg shadow-indigo-900/30"
                      : "bg-slate-800/50 border-slate-600 hover:bg-slate-700/50"
                  } disabled:cursor-not-allowed disabled:opacity-70`}
                >
                  <MapPin className="w-6 h-6 mb-3 text-white" />
                  <span className="block text-sm font-bold text-white">Outside Beirut</span>
                  <span className="block text-xs text-indigo-100/80 mt-1">All other areas</span>
                </button>
              </div>

              <div className="mt-5">
                <StatusMessage type={locationStatus.type} message={locationStatus.message} />
              </div>
            </section>

            {!isGoogleAccount && (
              <section className="bg-white/5 border border-white/10 rounded-3xl p-6 md:p-8 backdrop-blur-md">
                <div className="flex items-start gap-3 mb-6">
                  <div className="w-10 h-10 rounded-xl bg-blue-500/15 flex items-center justify-center border border-blue-400/20">
                    <ShieldCheck className="w-5 h-5 text-blue-300" />
                  </div>
                  <div>
                    <h2 className="text-xl md:text-2xl font-bold text-white">Change Password</h2>
                    <p className="text-sm text-slate-400 mt-1">Enter your current password first.</p>
                  </div>
                </div>

                <form onSubmit={handlePasswordSubmit} className="space-y-5">
                  <StatusMessage type={passwordStatus.type} message={passwordStatus.message} />

                  <PasswordField
                    label="Current password"
                    name="oldPassword"
                    value={passwordForm.oldPassword}
                    onChange={handlePasswordChange}
                    placeholder="Current password"
                    visible={visiblePasswords.oldPassword}
                    onToggle={() => togglePasswordVisibility("oldPassword")}
                    error={passwordErrors.oldPassword}
                  />

                  <PasswordField
                    label="New password"
                    name="newPassword"
                    value={passwordForm.newPassword}
                    onChange={handlePasswordChange}
                    placeholder="New password"
                    visible={visiblePasswords.newPassword}
                    onToggle={() => togglePasswordVisibility("newPassword")}
                    error={passwordErrors.newPassword}
                  />

                  <PasswordField
                    label="Confirm new password"
                    name="confirmPassword"
                    value={passwordForm.confirmPassword}
                    onChange={handlePasswordChange}
                    placeholder="Confirm new password"
                    visible={visiblePasswords.confirmPassword}
                    onToggle={() => togglePasswordVisibility("confirmPassword")}
                    error={passwordErrors.confirmPassword}
                  />

                  <button
                    type="submit"
                    disabled={isChangingPassword}
                    className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-70 disabled:cursor-not-allowed text-white font-bold transition-colors shadow-lg shadow-blue-600/20"
                  >
                    {isChangingPassword && <Loader2 className="w-4 h-4 animate-spin" />}
                    {isChangingPassword ? "Updating..." : "Update Password"}
                  </button>
                </form>
              </section>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default MyAccount;
