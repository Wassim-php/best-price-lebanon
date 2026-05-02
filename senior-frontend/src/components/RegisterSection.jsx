import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { User, Mail, Lock, Eye, EyeOff, UserPlus, AlertCircle, CheckCircle, MapPin, Building2, Home } from "lucide-react";
import authService from "../services/authService";

const InputField = ({
  label,
  name,
  type = "text",
  icon: Icon,
  placeholder,
  error,
  value,
  onChange,
  showToggle,
  onToggle,
}) => (
  <div>
    <label className="block text-xs font-bold text-blue-200 uppercase tracking-wider mb-1.5 ml-1">
      {label}
    </label>
    <div className="relative group">
      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
        <Icon className={`h-4 w-4 ${error ? "text-red-400" : "text-blue-300"} group-focus-within:text-white transition-colors`} />
      </div>
      <input
        type={type}
        name={name}
        value={value}
        onChange={onChange}
        className={`block w-full pl-10 pr-4 py-3 bg-slate-800/50 border rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-1 transition-all text-sm font-medium
          ${error
            ? "border-red-500/50 focus:border-red-500 focus:ring-red-500"
            : "border-slate-600 focus:border-blue-500 focus:ring-blue-500"
          }`}
        placeholder={placeholder}
      />
      {showToggle && (
        <button type="button" onClick={onToggle} className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-white cursor-pointer">
          {type === "password" ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
        </button>
      )}
    </div>
    {error && <p className="text-red-300 text-[10px] mt-1 ml-1 font-medium">{error}</p>}
  </div>
);

const RegisterSection = () => {
  const navigate = useNavigate();
  
  // --- STATE ---
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
    passwordConfirmation: "",
    locationType: "Inside Beirut", // Default value
    address: "",
    accept: false,
  });

  const [formErrors, setFormErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [generalError, setGeneralError] = useState("");

  // --- VALIDATION ---
  const validateForm = () => {
    const errors = {};
    if (!formData.username.trim()) errors.username = "Required";

    if (!formData.email) {
      errors.email = "Required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      errors.email = "Invalid email";
    }

    const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;
    if (!formData.password) {
      errors.password = "Required";
    } else if (!passwordRegex.test(formData.password)) {
      errors.password = "Weak password (8+ chars, upper, lower, #, symbol)";
    }

    if (formData.password !== formData.passwordConfirmation) {
      errors.passwordConfirmation = "Passwords do not match";
    }

    if (!formData.accept) errors.accept = "Required";

    return errors;
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({ ...prev, [name]: type === "checkbox" ? checked : value }));
    if (formErrors[name]) setFormErrors((prev) => ({ ...prev, [name]: "" }));
    setGeneralError("");
  };

  const handleLocationChange = (type) => {
    setFormData(prev => ({ ...prev, locationType: type }));
    if (formErrors.address) setFormErrors(prev => ({ ...prev, address: "" }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (isSubmitting) return;

    const errors = validateForm();
    if (Object.keys(errors).length > 0) {
      setFormErrors(errors);
      return;
    }

    setIsSubmitting(true);
    try {
      await authService.register(formData);
      navigate("/login");
    } catch (error) {
      const msg = error.message || "Registration failed";
      setGeneralError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 relative overflow-hidden font-sans py-10">
      
      {/* Background Glows */}
      <div className="absolute top-[-10%] left-[-10%] w-[600px] h-[600px] bg-blue-600/20 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[600px] h-[600px] bg-indigo-600/20 rounded-full blur-[120px] pointer-events-none" />

      {/* Main Card */}
      <div className="w-full max-w-lg bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl shadow-2xl overflow-hidden z-10 mx-4">
        
        {/* Top Bar */}
        <div className="h-1.5 w-full bg-gradient-to-r from-blue-500 via-indigo-500 to-violet-500" />

        <div className="p-8">
          
          {/* Header */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 mb-4 shadow-lg shadow-blue-500/30">
              <UserPlus className="w-7 h-7 text-white" />
            </div>
            <h2 className="text-2xl font-bold text-white tracking-tight">Create Account</h2>
            <p className="text-blue-200 mt-2 text-sm">Join the platform to compare & save.</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            
            {generalError && (
              <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-3 flex items-center gap-3 backdrop-blur-sm">
                <AlertCircle className="w-5 h-5 text-red-500" />
                <p className="text-red-200 text-sm font-medium">{generalError}</p>
              </div>
            )}

            {/* Username & Email */}
            <InputField label="Username" name="username" icon={User} placeholder="johndoe" error={formErrors.username} value={formData.username} onChange={handleChange} />
            <InputField label="Email Address" name="email" type="email" icon={Mail} placeholder="john@example.com" error={formErrors.email} value={formData.email} onChange={handleChange} />

            {/* Passwords */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <InputField 
                label="Password" name="password" 
                type={showPassword ? "text" : "password"} 
                icon={Lock} placeholder="••••••••" 
                error={formErrors.password}
                value={formData.password}
                onChange={handleChange}
                showToggle={true} onToggle={() => setShowPassword(!showPassword)}
              />
              <InputField 
                label="Confirm" name="passwordConfirmation" 
                type={showConfirm ? "text" : "password"} 
                icon={Lock} placeholder="••••••••" 
                error={formErrors.passwordConfirmation}
                value={formData.passwordConfirmation}
                onChange={handleChange}
                showToggle={true} onToggle={() => setShowConfirm(!showConfirm)}
              />
            </div>

            {/* --- LOCATION SELECTOR --- */}
            <div>
              <label className="block text-xs font-bold text-blue-200 uppercase tracking-wider mb-2.5 ml-1">
                Location
              </label>
              <div className="grid grid-cols-2 gap-3">
                {/* Option 1: Inside Beirut */}
                <div 
                  onClick={() => handleLocationChange("Inside Beirut")}
                  className={`cursor-pointer rounded-xl border p-3 flex flex-col items-center justify-center transition-all duration-200 ${
                    formData.locationType === "Inside Beirut"
                      ? "bg-blue-600 border-blue-500 shadow-lg shadow-blue-900/50"
                      : "bg-slate-800/50 border-slate-600 hover:bg-slate-700/50"
                  }`}
                >
                  <Building2 className={`w-5 h-5 mb-1 ${formData.locationType === "Inside Beirut" ? "text-white" : "text-slate-400"}`} />
                  <span className={`text-xs font-bold ${formData.locationType === "Inside Beirut" ? "text-white" : "text-slate-400"}`}>Inside Beirut</span>
                </div>

                {/* Option 2: Outside Beirut */}
                <div 
                  onClick={() => handleLocationChange("Outside Beirut")}
                  className={`cursor-pointer rounded-xl border p-3 flex flex-col items-center justify-center transition-all duration-200 ${
                    formData.locationType === "Outside Beirut"
                      ? "bg-indigo-600 border-indigo-500 shadow-lg shadow-indigo-900/50"
                      : "bg-slate-800/50 border-slate-600 hover:bg-slate-700/50"
                  }`}
                >
                  <MapPin className={`w-5 h-5 mb-1 ${formData.locationType === "Outside Beirut" ? "text-white" : "text-slate-400"}`} />
                  <span className={`text-xs font-bold ${formData.locationType === "Outside Beirut" ? "text-white" : "text-slate-400"}`}>Outside Beirut</span>
                </div>
              </div>
            </div>

            {/* --- CONDITIONAL ADDRESS INPUT --- */}
            <div className={`transition-all duration-300 ease-in-out overflow-hidden ${
              formData.locationType === "Outside Beirut" ? "max-h-24 opacity-100" : "max-h-0 opacity-0"
            }`}>
              <InputField 
                label="Full Address" 
                name="address" 
                icon={Home} 
                placeholder="City, Street, Building, Floor..." 
                error={formErrors.address}
                value={formData.address}
                onChange={handleChange}
              />
            </div>

            {/* Terms Checkbox */}
            <div className="pt-2">
              <label className="flex items-center cursor-pointer group">
                <div className="relative">
                  <input
                    type="checkbox"
                    name="accept"
                    checked={formData.accept}
                    onChange={handleChange}
                    className="sr-only"
                  />
                  <div className={`w-5 h-5 border-2 rounded transition-all flex items-center justify-center
                    ${formData.accept ? "bg-blue-500 border-blue-500" : "border-slate-500 bg-slate-800/50 group-hover:border-blue-400"}`}>
                    {formData.accept && <CheckCircle className="w-3.5 h-3.5 text-white" />}
                  </div>
                </div>
                <span className="ml-3 text-sm text-slate-300">
                  I agree to the <a href="#" className="text-blue-400 hover:text-blue-300 font-bold underline decoration-blue-500/30">Terms</a> & <a href="#" className="text-blue-400 hover:text-blue-300 font-bold underline decoration-blue-500/30">Policies</a>
                </span>
              </label>
              {formErrors.accept && <p className="text-red-400 text-xs mt-1 ml-8">{formErrors.accept}</p>}
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isSubmitting}
              className={`w-full relative flex justify-center items-center py-4 px-4 border border-transparent rounded-xl text-white font-bold text-md uppercase tracking-wide bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-slate-900 focus:ring-blue-500 transition-all shadow-lg shadow-blue-600/20 mt-4 ${
                isSubmitting ? "opacity-70 cursor-not-allowed" : "hover:-translate-y-0.5"
              }`}
            >
              {isSubmitting ? "Creating..." : "Create Account"}
            </button>
          </form>

          {/* Footer */}
          <div className="mt-8 text-center">
            <p className="text-slate-400 text-sm">
              Already have an account?{" "}
              <Link to="/login" className="font-bold text-white hover:text-blue-300 transition-colors underline decoration-blue-500/50 hover:decoration-blue-300">
                Log in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RegisterSection;