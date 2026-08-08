import React, { useState } from 'react';
import { Dna, ArrowRight, UserPlus, LogIn, AlertCircle, CheckCircle2, Phone, Mail, Lock, User as UserIcon, Eye, EyeOff } from 'lucide-react';
import { useAuth } from '../../providers/AuthProvider';

interface LoginViewProps {
  initialMode?: 'signin' | 'signup';
  onNavigateToLanding: () => void;
  // onLoginSuccess is no longer needed directly since auth state is global
}

export const LoginView: React.FC<LoginViewProps> = ({ 
  initialMode = 'signin',
  onNavigateToLanding 
}) => {
  const { login, register, isLoading } = useAuth();
  const [authMode, setAuthMode] = useState<'signin' | 'signup'>(initialMode);

  // Sign In Form Inputs & Visibility Toggle
  const [signInEmail, setSignInEmail] = useState('');
  const [signInPassword, setSignInPassword] = useState('');
  const [showSignInPassword, setShowSignInPassword] = useState(false);

  // Sign Up Form Inputs & Visibility Toggle
  const [signUpFirstName, setSignUpFirstName] = useState('');
  const [signUpLastName, setSignUpLastName] = useState('');
  const [signUpEmail, setSignUpEmail] = useState('');
  const [signUpPassword, setSignUpPassword] = useState('');
  const [showSignUpPassword, setShowSignUpPassword] = useState(false);

  // Status Alerts
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Handle Sign In Authentication
  const handleSignInSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      await login({
        username_or_email: signInEmail,
        password: signInPassword,
      });
      // The AuthProvider will handle the redirect or state update internally,
      // which will naturally unmount this LoginView in App.tsx
    } catch (err: any) {
      let msg = 'Invalid email or password.';
      if (err.response?.data?.detail) {
        if (typeof err.response.data.detail === 'string') {
          msg = err.response.data.detail;
        } else if (Array.isArray(err.response.data.detail)) {
          msg = err.response.data.detail.map((d: any) => d.msg || d.detail).join(' ');
        }
      } else if (err.message) {
        msg = err.message;
      }
      setErrorMessage(msg);
    }
  };

  const handleSignUpSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      await register({
        first_name: signUpFirstName,
        last_name: signUpLastName,
        email: signUpEmail,
        password: signUpPassword,
      });
      setSuccessMessage('Registration successful! You can now sign in.');
      setAuthMode('signin');
      setSignInEmail(signUpEmail);
      setSignInPassword(signUpPassword);
    } catch (err: any) {
      let msg = 'Failed to register. Please contact administrator.';
      if (err.response?.data?.detail) {
        if (typeof err.response.data.detail === 'string') {
          msg = err.response.data.detail;
        } else if (Array.isArray(err.response.data.detail)) {
          msg = err.response.data.detail.map((d: any) => d.msg || d.detail).join(' ');
        }
      } else if (err.message) {
        msg = err.message;
      }
      setErrorMessage(msg);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-6 text-white relative overflow-hidden font-sans">
      {/* Glow Effects */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-600/20 rounded-full blur-3xl pointer-events-none"></div>
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-teal-500/20 rounded-full blur-3xl pointer-events-none"></div>

      {/* Top Header Back to Landing */}
      <div className="absolute top-6 left-6 z-20">
        <button
          onClick={onNavigateToLanding}
          className="text-xs font-semibold text-slate-400 hover:text-white flex items-center gap-2 bg-slate-900/80 px-3.5 py-2 rounded-xl border border-slate-800 transition-colors cursor-pointer"
        >
          <span>← Back to Landing Page</span>
        </button>
      </div>

      <div className="w-full max-w-md bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-3xl p-8 shadow-2xl space-y-6 relative z-10">
        
        {/* Logo & Header */}
        <div className="text-center space-y-2">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-blue-600 to-teal-400 flex items-center justify-center text-white mx-auto shadow-lg shadow-blue-500/30">
            <Dna className="w-8 h-8 animate-pulse" />
          </div>
          <h1 className="text-2xl font-extrabold tracking-tight">AI-Powered ELN</h1>
          <p className="text-xs text-slate-400">Electronic Lab Notebook Authentication</p>
        </div>

        {/* Auth Mode Toggle Tabs (Sign In vs Sign Up) */}
        <div className="flex bg-slate-950 p-1.5 rounded-2xl border border-slate-800">
          <button
            type="button"
            onClick={() => { setAuthMode('signin'); setErrorMessage(null); setSuccessMessage(null); }}
            className={`flex-1 py-2.5 text-xs font-bold rounded-xl transition-all flex items-center justify-center gap-2 cursor-pointer ${
              authMode === 'signin'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <LogIn className="w-3.5 h-3.5" />
            <span>Sign In</span>
          </button>

          <button
            type="button"
            onClick={() => { setAuthMode('signup'); setErrorMessage(null); setSuccessMessage(null); }}
            className={`flex-1 py-2.5 text-xs font-bold rounded-xl transition-all flex items-center justify-center gap-2 cursor-pointer ${
              authMode === 'signup'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <UserPlus className="w-3.5 h-3.5" />
            <span>Sign Up</span>
          </button>
        </div>

        {/* Error Alert */}
        {errorMessage && (
          <div className="p-3.5 bg-rose-950/80 border border-rose-800/80 rounded-xl text-rose-200 text-xs flex items-start gap-2.5 animate-fadeIn">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
            <p className="leading-relaxed">{errorMessage}</p>
          </div>
        )}

        {/* Success Alert */}
        {successMessage && (
          <div className="p-3.5 bg-emerald-950/80 border border-emerald-800/80 rounded-xl text-emerald-200 text-xs flex items-start gap-2.5 animate-fadeIn">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            <p className="leading-relaxed">{successMessage}</p>
          </div>
        )}

        {/* MODE 1: SIGN IN FORM */}
        {authMode === 'signin' ? (
          <form onSubmit={handleSignInSubmit} className="space-y-4 text-xs" autoComplete="off">
            <div>
              <label className="block text-slate-300 font-semibold mb-1 flex items-center gap-1.5">
                <Mail className="w-3.5 h-3.5 text-blue-400" />
                <span>Registered Gmail / Email</span>
              </label>
              <input
                type="email"
                required
                autoComplete="off"
                value={signInEmail}
                onChange={(e) => setSignInEmail(e.target.value)}
                placeholder="e.g. user@organization.com"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-xs"
              />
            </div>

            <div>
              <label className="block text-slate-300 font-semibold mb-1 flex items-center gap-1.5">
                <Lock className="w-3.5 h-3.5 text-blue-400" />
                <span>Password</span>
              </label>
              <div className="relative">
                <input
                  type={showSignInPassword ? 'text' : 'password'}
                  required
                  autoComplete="current-password"
                  value={signInPassword}
                  onChange={(e) => setSignInPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 pr-10 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-xs"
                />
                <button
                  type="button"
                  onClick={() => setShowSignInPassword(!showSignInPassword)}
                  className="absolute right-3 top-3 text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
                  title={showSignInPassword ? 'Hide Password' : 'Show Password'}
                >
                  {showSignInPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 bg-gradient-to-r from-blue-600 to-teal-500 hover:from-blue-700 hover:to-teal-600 disabled:opacity-50 text-white font-bold text-xs rounded-xl shadow-lg shadow-blue-500/25 transition-all flex items-center justify-center gap-2 cursor-pointer mt-2"
            >
              <span>{isLoading ? 'Authenticating...' : 'Sign In & Open Dashboard'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>



            <p className="text-[11px] text-center text-slate-400 pt-2">
              Don't have an account yet?{' '}
              <button
                type="button"
                onClick={() => setAuthMode('signup')}
                className="text-blue-400 font-bold hover:underline cursor-pointer"
              >
                Sign Up Here
              </button>
            </p>
          </form>
        ) : (
          <form onSubmit={handleSignUpSubmit} className="space-y-3.5 text-xs" autoComplete="off">
            <div className="flex gap-3">
              <div className="flex-1">
                <label className="block text-slate-300 font-semibold mb-1 flex items-center gap-1.5">
                  <UserIcon className="w-3.5 h-3.5 text-teal-400" />
                  <span>First Name</span>
                </label>
                <input
                  type="text"
                  required
                  value={signUpFirstName}
                  onChange={(e) => setSignUpFirstName(e.target.value)}
                  placeholder="Jane"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-white focus:outline-none focus:ring-2 focus:ring-teal-500 font-mono text-xs"
                />
              </div>
              <div className="flex-1">
                <label className="block text-slate-300 font-semibold mb-1">
                  <span>Last Name</span>
                </label>
                <input
                  type="text"
                  required
                  value={signUpLastName}
                  onChange={(e) => setSignUpLastName(e.target.value)}
                  placeholder="Doe"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-white focus:outline-none focus:ring-2 focus:ring-teal-500 font-mono text-xs"
                />
              </div>
            </div>

            <div>
              <label className="block text-slate-300 font-semibold mb-1 flex items-center gap-1.5">
                <Mail className="w-3.5 h-3.5 text-teal-400" />
                <span>Email Address</span>
              </label>
              <input
                type="email"
                required
                value={signUpEmail}
                onChange={(e) => setSignUpEmail(e.target.value)}
                placeholder="user@organization.com"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-white focus:outline-none focus:ring-2 focus:ring-teal-500 font-mono text-xs"
              />
            </div>

            <div>
              <label className="block text-slate-300 font-semibold mb-1 flex items-center gap-1.5">
                <Lock className="w-3.5 h-3.5 text-teal-400" />
                <span>Password</span>
              </label>
              <div className="relative">
                <input
                  type={showSignUpPassword ? 'text' : 'password'}
                  required
                  value={signUpPassword}
                  onChange={(e) => setSignUpPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 pr-10 text-white focus:outline-none focus:ring-2 focus:ring-teal-500 font-mono text-xs"
                />
                <button
                  type="button"
                  onClick={() => setShowSignUpPassword(!showSignUpPassword)}
                  className="absolute right-3 top-3 text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
                >
                  {showSignUpPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 bg-gradient-to-r from-teal-500 to-blue-600 hover:from-teal-600 hover:to-blue-700 disabled:opacity-50 text-white font-bold text-xs rounded-xl shadow-lg shadow-teal-500/25 transition-all flex items-center justify-center gap-2 cursor-pointer mt-4"
            >
              <span>{isLoading ? 'Registering...' : 'Register Account'}</span>
              <UserPlus className="w-4 h-4" />
            </button>
            
            <p className="text-[11px] text-center text-slate-400 pt-2">
              Already have an account?{' '}
              <button
                type="button"
                onClick={() => setAuthMode('signin')}
                className="text-teal-400 font-bold hover:underline cursor-pointer"
              >
                Sign In Here
              </button>
            </p>
          </form>
        )}
      </div>
    </div>
  );
};
