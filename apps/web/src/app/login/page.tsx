"use client";

import { useSearchParams } from "next/navigation";
import { createClient } from "@/utils/supabase/client";
import { motion } from "framer-motion";
import { useState, Suspense } from "react";

function LoginForm() {
  const searchParams = useSearchParams();
  const role = searchParams.get("role") || "learner";
  const [loading, setLoading] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const supabase = createClient();

  const handleGoogleLogin = async () => {
    setLoading(true);
    await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/auth/callback?role=${role}`,
      },
    });
  };

  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg("");
    
    const formData = new FormData();
    formData.append('email', email);
    formData.append('password', password);
    formData.append('role', role);

    const { login } = await import('./actions');
    const result = await login(formData);
    
    if (result.error) {
      setErrorMsg(result.error);
      setLoading(false);
    } else {
      window.location.href = role === 'learner' ? '/learn/chat' : `/${role}/chat`;
    }
  };

  const handleEmailSignup = async () => {
    setLoading(true);
    setErrorMsg("");
    
    const formData = new FormData();
    formData.append('email', email);
    formData.append('password', password);
    formData.append('role', role);

    const { signup } = await import('./actions');
    const result = await signup(formData);
    
    if (result.error) {
      setErrorMsg(result.error);
      setLoading(false);
    } else {
      window.location.href = role === 'learner' ? '/learn/chat' : `/${role}/chat`;
    }
  };

  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="liquid-glass liquid-glass-lg bg-slate-900/40 rounded-3xl p-8 max-w-md w-full border border-white/10 shadow-2xl text-center"
    >
      <h1 className="text-3xl font-bold text-white mb-2">Welcome Back</h1>
      <p className="text-slate-400 mb-6">Sign in to your {role === 'faculty' ? 'Faculty' : 'Learner'} account</p>
      
      {errorMsg && (
        <div className="mb-4 p-3 bg-red-500/20 border border-red-500/50 rounded-xl text-red-200 text-sm">
          {errorMsg}
        </div>
      )}

      <form onSubmit={handleEmailLogin} className="space-y-4 mb-6">
        <input 
          type="email" 
          placeholder="Email address" 
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
        />
        <input 
          type="password" 
          placeholder="Password" 
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
        />
        
        <div className="flex gap-3">
          <button 
            type="submit"
            disabled={loading}
            className="flex-1 py-3 px-4 bg-indigo-600 text-white rounded-xl font-medium hover:bg-indigo-700 transition-colors disabled:opacity-50"
          >
            {loading ? '...' : 'Log In'}
          </button>
          <button 
            type="button"
            onClick={handleEmailSignup}
            disabled={loading}
            className="flex-1 py-3 px-4 bg-slate-800 text-white border border-white/10 rounded-xl font-medium hover:bg-slate-700 transition-colors disabled:opacity-50"
          >
            Sign Up
          </button>
        </div>
      </form>

      <div className="relative mb-6">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-white/10"></div>
        </div>
        <div className="relative flex justify-center text-sm">
          <span className="px-2 bg-slate-900/40 text-slate-500">Or continue with</span>
        </div>
      </div>

      <button 
        onClick={handleGoogleLogin}
        type="button"
        disabled={loading}
        className="w-full py-3 px-4 bg-white text-slate-900 rounded-xl font-medium hover:bg-slate-100 transition-colors flex items-center justify-center gap-3 disabled:opacity-50"
      >
        <svg viewBox="0 0 24 24" className="w-5 h-5" fill="currentColor">
            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
        </svg>
        Google
      </button>
    </motion.div>
  );
}

export default function LoginPage() {
  return (
    <main className="min-h-screen flex items-center justify-center relative overflow-hidden bg-slate-950 text-slate-50">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-indigo-900 via-slate-950 to-slate-950 opacity-80" />
      <div className="relative z-10 w-full px-4 flex justify-center">
        <Suspense fallback={<div className="text-white">Loading...</div>}>
          <LoginForm />
        </Suspense>
      </div>
    </main>
  );
}
