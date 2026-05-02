import React, { useEffect, useRef, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Eye, EyeOff, Loader2, Lock, LogIn, Mail, TrendingDown } from "lucide-react";
import AuthService from "../services/authService";

const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || "";
const googleScriptSrc = "https://accounts.google.com/gsi/client";

let googleScriptPromise;
let initializedGoogleClientId = "";

const loadGoogleScript = () => {
  if (window.google?.accounts?.id) {
    return Promise.resolve();
  }

  if (googleScriptPromise) {
    return googleScriptPromise;
  }

  googleScriptPromise = new Promise((resolve, reject) => {
    const existingScript = document.querySelector(`script[src='${googleScriptSrc}']`);

    if (existingScript) {
      existingScript.addEventListener("load", resolve, { once: true });
      existingScript.addEventListener("error", reject, { once: true });
      return;
    }

    const script = document.createElement("script");
    script.src = googleScriptSrc;
    script.async = true;
    script.defer = true;
    script.onload = resolve;
    script.onerror = reject;
    document.body.appendChild(script);
  });

  return googleScriptPromise;
};

const GoogleMark = () => (
  <svg className="h-5 w-5" viewBox="0 0 24 24" aria-hidden="true">
    <path
      fill="#4285F4"
      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
    />
    <path
      fill="#34A853"
      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
    />
    <path
      fill="#FBBC05"
      d="M5.84 14.1c-.22-.66-.35-1.36-.35-2.1s.13-1.44.35-2.1V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l3.66-2.84z"
    />
    <path
      fill="#EA4335"
      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06L5.84 9.9C6.71 7.3 9.14 5.38 12 5.38z"
    />
  </svg>
);

const LoginSection = () => {
  const navigate = useNavigate();
  const googleButtonRef = useRef(null);

  const [credentials, setCredentials] = useState({
    username: "",
    password: "",
  });

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [googleReady, setGoogleReady] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  useEffect(() => {
    if (!googleClientId) return;

    let isMounted = true;

    const renderGoogleButton = async () => {
      try {
        await loadGoogleScript();
      } catch (_error) {
        if (isMounted) {
          setError("Could not load Google sign-in. Please try again later.");
        }
        return;
      }

      if (!isMounted || !window.google?.accounts?.id || !googleButtonRef.current) return;

      if (initializedGoogleClientId !== googleClientId) {
        window.google.accounts.id.initialize({
          client_id: googleClientId,
          callback: async (response) => {
            if (!response?.credential) {
              setError("Google did not return a sign-in credential.");
              return;
            }

            setGoogleLoading(true);
            setError("");

            try {
              await AuthService.googleLogin(response.credential);
              navigate("/home");
            } catch (err) {
              setError(err.message || "Google login failed. Please try again.");
            } finally {
              setGoogleLoading(false);
            }
          },
        });
        initializedGoogleClientId = googleClientId;
      }

      googleButtonRef.current.innerHTML = "";
      window.google.accounts.id.renderButton(googleButtonRef.current, {
        theme: "outline",
        size: "large",
        text: "continue_with",
        shape: "rectangular",
        width: googleButtonRef.current.offsetWidth || 320,
      });
      setGoogleReady(true);
    };

    renderGoogleButton();

    return () => {
      isMounted = false;
    };
  }, [navigate]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setCredentials({ ...credentials, [name]: value });
    if (error) setError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      await AuthService.login(credentials.username, credentials.password);
      navigate("/home");
    } catch (err) {
      const msg = err.error || "Invalid credentials. Please try again.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleMissingGoogleConfig = () => {
    setError("Google login needs VITE_GOOGLE_CLIENT_ID in awfarlak-react/.env.local, then restart npm run dev.");
  };

  return (
    // 1. BACKGROUND: Deep Professional Gradient (The "Trust" Vibe)
    <div className="min-h-screen w-full flex items-center justify-center bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 relative overflow-hidden font-sans">
      
      {/* 2. AMBIENT GLOW EFFECTS (Subtle background movement) */}
      <div className="absolute top-[-10%] left-[-10%] w-96 h-96 bg-blue-600/30 rounded-full blur-3xl opacity-50 pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-96 h-96 bg-indigo-600/30 rounded-full blur-3xl opacity-50 pointer-events-none" />

      {/* 3. THE GLASS CARD */}
      <div className="w-full max-w-md bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl shadow-2xl overflow-hidden z-10 mx-4">
        
        {/* Top Decorative Bar */}
        <div className="h-2 w-full bg-gradient-to-r from-blue-500 to-indigo-500" />

        <div className="p-8 md:p-10">
          
          {/* Header Section */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 mb-4 shadow-lg shadow-blue-500/30">
              <TrendingDown className="w-8 h-8 text-white" />
            </div>
            <h2 className="text-3xl font-bold text-white tracking-tight">Welcome Back</h2>
            <p className="text-blue-200 mt-2 text-sm">
              Sign in to track prices & deliveries
            </p>
          </div>

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            
            {/* Error Display */}
            {error && (
              <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-3 flex items-center gap-3 backdrop-blur-sm">
                <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                <p className="text-red-200 text-sm font-medium">{error}</p>
              </div>
            )}

            {/* Username Field */}
            <div>
              <label className="block text-xs font-bold text-blue-200 uppercase tracking-wider mb-2 ml-1">
                Username
              </label>
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-blue-300 group-focus-within:text-white transition-colors" />
                </div>
                <input
                  type="text"
                  name="username"
                  required
                  value={credentials.username}
                  onChange={handleChange}
                  className="block w-full pl-11 pr-4 py-3.5 bg-slate-800/50 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
                  placeholder="Enter your username"
                />
              </div>
            </div>

            {/* Password Field */}
            <div>
              <div className="flex items-center justify-between mb-2 ml-1">
                <label className="block text-xs font-bold text-blue-200 uppercase tracking-wider">
                  Password
                </label>
                <Link 
                  to="/forgot-password" 
                  className="text-xs font-bold text-blue-400 hover:text-blue-300 transition-colors"
                >
                  Forgot?
                </Link>
              </div>
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-blue-300 group-focus-within:text-white transition-colors" />
                </div>
                <input
                  type={showPassword ? "text" : "password"}
                  name="password"
                  required
                  value={credentials.password}
                  onChange={handleChange}
                  className="block w-full pl-11 pr-12 py-3.5 bg-slate-800/50 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-4 flex items-center text-slate-400 hover:text-white cursor-pointer transition-colors"
                >
                  {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className={`w-full relative flex justify-center items-center py-4 px-4 border border-transparent rounded-xl text-white font-bold text-md uppercase tracking-wide bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-slate-900 focus:ring-blue-500 transition-all shadow-lg shadow-blue-600/20 ${
                loading ? "opacity-70 cursor-not-allowed" : "hover:-translate-y-0.5"
              }`}
            >
              {loading ? (
                <Loader2 className="animate-spin h-5 w-5" />
              ) : (
                <>
                  Sign In to Platform
                  <LogIn className="ml-2 h-5 w-5" />
                </>
              )}
            </button>
          </form>

          <div className="my-7 flex items-center gap-3">
            <div className="h-px flex-1 bg-white/10" />
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">or</span>
            <div className="h-px flex-1 bg-white/10" />
          </div>

          <div className="space-y-4">
            {!googleClientId && (
              <button
                type="button"
                onClick={handleMissingGoogleConfig}
                className="w-full flex items-center justify-center gap-3 rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm font-bold text-slate-800 shadow-lg transition-all hover:bg-slate-100"
              >
                <GoogleMark />
                Continue with Google
              </button>
            )}

            {googleClientId && (
              <div className="relative min-h-11">
                <div ref={googleButtonRef} className={googleLoading ? "pointer-events-none opacity-60" : ""} />
                {!googleReady && (
                  <div className="flex h-11 items-center justify-center rounded-xl border border-slate-600 bg-slate-800/50 text-slate-300">
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Loading Google sign-in
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="mt-8 text-center">
            <p className="text-slate-400 text-sm">
              Don't have an account?{" "}
              <Link to="/register" className="font-bold text-white hover:text-blue-300 transition-colors underline decoration-blue-500/50 hover:decoration-blue-300">
                Create one now
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginSection;
