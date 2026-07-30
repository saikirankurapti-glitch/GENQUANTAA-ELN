import React from 'react';
import { 
  Dna, Sparkles, Shield, ArrowRight, FlaskConical, 
  TestTube2, FileText, CheckCircle2, Zap, Users, Lock, ChevronRight 
} from 'lucide-react';

interface LandingViewProps {
  onNavigateToLogin: (initialMode?: 'signin' | 'signup') => void;
  onNavigateToDashboard?: () => void;
}

export const LandingView: React.FC<LandingViewProps> = ({ 
  onNavigateToLogin
}) => {
  return (
    <div className="min-h-screen bg-slate-950 text-white font-sans selection:bg-blue-500 selection:text-white relative overflow-hidden">
      
      {/* Background Radial Glow Effects */}
      <div className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-blue-600/15 rounded-full blur-[140px] pointer-events-none"></div>
      <div className="absolute top-1/3 right-1/4 w-[500px] h-[500px] bg-teal-500/15 rounded-full blur-[140px] pointer-events-none"></div>

      {/* Top Navigation Navbar */}
      <header className="max-w-7xl mx-auto px-6 py-6 flex items-center justify-between relative z-10 border-b border-slate-800/80">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-blue-600 to-teal-400 flex items-center justify-center text-white shadow-lg shadow-blue-500/30">
            <Dna className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-xl text-white tracking-tight">AI-ELN</span>
            </div>
            <p className="text-xs text-slate-400">Electronic Lab Notebook & Discovery Engine</p>
          </div>
        </div>

        <nav className="hidden md:flex items-center gap-8 text-xs font-semibold text-slate-300">
          <a href="#features" className="hover:text-teal-400 transition-colors">Features</a>
          <a href="#ai-capabilities" className="hover:text-teal-400 transition-colors">AI Copilot & RAG</a>
          <a href="#compliance" className="hover:text-teal-400 transition-colors">21 CFR Part 11</a>
          <a href="#architecture" className="hover:text-teal-400 transition-colors">Architecture</a>
        </nav>

        <div className="flex items-center gap-3">
          <button
            onClick={() => onNavigateToLogin('signin')}
            className="text-xs font-bold px-4 py-2.5 rounded-xl text-slate-200 hover:text-white hover:bg-slate-800 transition-all cursor-pointer border border-slate-700"
          >
            Sign In
          </button>
          <button
            onClick={() => onNavigateToLogin('signup')}
            className="text-xs font-bold px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-teal-500 hover:from-blue-700 hover:to-teal-600 text-white shadow-lg shadow-blue-500/25 transition-all flex items-center gap-2 cursor-pointer"
          >
            <span>Create Free Account</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-6 pt-16 pb-20 text-center relative z-10 space-y-8">
        <div className="inline-flex items-center gap-2 bg-slate-900/90 border border-slate-800 rounded-full px-4 py-1.5 text-xs text-teal-300 font-semibold shadow-inner">
          <Sparkles className="w-4 h-4 text-teal-400" />
          <span>Next-Generation AI Electronic Lab Notebook for Modern Life Sciences</span>
        </div>

        <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight text-white max-w-4xl mx-auto leading-tight">
          Accelerate Scientific Discovery with <span className="bg-gradient-to-r from-blue-400 via-teal-300 to-emerald-400 bg-clip-text text-transparent">AI-Grounded R&D</span>
        </h1>

        <p className="text-slate-400 text-sm md:text-base max-w-2xl mx-auto leading-relaxed">
          Replace paper notebooks with structured, searchable, timestamped, and 21 CFR Part 11 auditable digital entries linked to samples, DNA sequences, and automated SOP generation.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
          <button
            onClick={() => onNavigateToLogin('signup')}
            className="w-full sm:w-auto px-8 py-4 bg-gradient-to-r from-blue-600 via-blue-500 to-teal-500 hover:from-blue-700 hover:to-teal-600 text-white font-bold text-sm rounded-2xl shadow-xl shadow-blue-500/30 transition-all flex items-center justify-center gap-3 cursor-pointer"
          >
            <span>Get Started — Sign Up</span>
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>

        {/* Feature Pill Stats */}
        <div className="pt-12 grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
          <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-2xl text-center">
            <h3 className="text-2xl font-bold text-blue-400 font-mono">10x</h3>
            <p className="text-xs text-slate-400 mt-1">Faster SOP Protocol Generation</p>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-2xl text-center">
            <h3 className="text-2xl font-bold text-teal-400 font-mono">100%</h3>
            <p className="text-xs text-slate-400 mt-1">21 CFR Part 11 Compliant</p>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-2xl text-center">
            <h3 className="text-2xl font-bold text-emerald-400 font-mono">&lt;2s</h3>
            <p className="text-xs text-slate-400 mt-1">Single-Pane Dashboard Load</p>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-2xl text-center">
            <h3 className="text-2xl font-bold text-indigo-400 font-mono">96%</h3>
            <p className="text-xs text-slate-400 mt-1">RAG Grounded Q&A Precision</p>
          </div>
        </div>
      </section>

      {/* Grid of Core Capabilities */}
      <section id="features" className="max-w-7xl mx-auto px-6 py-16 relative z-10 border-t border-slate-800">
        <div className="text-center space-y-2 mb-12">
          <h2 className="text-2xl md:text-3xl font-bold tracking-tight">Core R&D Modules Built for Scientists</h2>
          <p className="text-xs text-slate-400 max-w-xl mx-auto">End-to-end electronic notebook workflows designed for molecular biology, CRISPR editing, and team collaboration.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl space-y-4 hover:border-blue-500/50 transition-colors">
            <div className="w-12 h-12 rounded-2xl bg-blue-500/10 text-blue-400 flex items-center justify-center">
              <FlaskConical className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold">Structured ELN Notebook</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Capture hypothesis, materials, execution steps, gel photos, and results with append-only version history.
            </p>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl space-y-4 hover:border-teal-500/50 transition-colors">
            <div className="w-12 h-12 rounded-2xl bg-teal-500/10 text-teal-400 flex items-center justify-center">
              <TestTube2 className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold">Sample & Cryo Registry</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Track cell lines, plasmids, and reagents in 9x9 cryo freezer boxes with barcode scanning and custody tracking.
            </p>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl space-y-4 hover:border-indigo-500/50 transition-colors">
            <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center">
              <Dna className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold">DNA Sequence & BLAST</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Interactive FASTA viewer with color-coded nucleotides, GC content calculation, and NCBI BLAST alignment.
            </p>
          </div>
        </div>
      </section>

      {/* Footer CTA */}
      <footer className="max-w-7xl mx-auto px-6 py-12 border-t border-slate-800 flex flex-col md:flex-row items-center justify-between text-xs text-slate-500 relative z-10 gap-4">
        <div className="flex items-center gap-2">
          <Dna className="w-4 h-4 text-blue-500" />
          <span>© 2026 AI-Powered ELN Platform. All rights reserved.</span>
        </div>

        <div className="flex items-center gap-6">
          <button onClick={() => onNavigateToLogin('signin')} className="hover:text-white transition-colors cursor-pointer">Sign In / Register</button>
        </div>
      </footer>
    </div>
  );
};
