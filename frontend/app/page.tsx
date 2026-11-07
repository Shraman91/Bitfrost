'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { PlayCircle, Trophy, Activity, Zap, Cpu, ArrowUpRight } from 'lucide-react';
import { api } from '../lib/api';
import { LeaderboardItem } from '../types';
import LeaderboardTable from '../components/LeaderboardTable';
import EfficiencyFrontierChart from '../components/EfficiencyFrontierChart';

export default function HomePage() {
  const [leaderboard, setLeaderboard] = useState<LeaderboardItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getLeaderboard();
      setLeaderboard(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load leaderboard');
    } finally {
      setLoading(false);
    }
  };

  const totalRuns = leaderboard.reduce((acc, curr) => acc + curr.total_runs, 0);
  const totalPassed = leaderboard.reduce((acc, curr) => acc + curr.passed_runs, 0);
  const overallPassRate = totalRuns > 0 ? ((totalPassed / totalRuns) * 100).toFixed(1) : '0.0';

  return (
    <div className="space-y-10">
      {/* Hero Section */}
      <div className="relative rounded-3xl border border-arena-border bg-gradient-to-br from-arena-surface via-arena-card/80 to-slate-900/60 p-8 sm:p-10 shadow-2xl overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20" />
        <div className="absolute bottom-0 left-0 w-72 h-72 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none -ml-20 -mb-20" />
        
        <div className="relative z-10 max-w-3xl space-y-4">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 text-xs font-mono">
            <Zap className="w-3.5 h-3.5" />
            <span>Ungameable AI Coding Agent Benchmark</span>
          </div>
          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white">
            How Coding Agents <span className="bg-gradient-to-r from-indigo-400 via-cyan-300 to-emerald-400 bg-clip-text text-transparent">Really Perform</span>
          </h1>
          <p className="text-slate-400 text-base sm:text-lg leading-relaxed">
            Every LLM call flows strictly through our platform to <strong>Bifrost</strong>.
            We measure exact token usage, API costs, execution latency, and pass rates across identical tasks.
          </p>

          <div className="flex flex-wrap gap-4 pt-2">
            <Link
              href="/benchmarks/new"
              className="inline-flex items-center space-x-2 bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white font-medium px-5 py-2.5 rounded-xl shadow-lg shadow-indigo-600/30 transition-all text-sm"
            >
              <PlayCircle className="w-4 h-4" />
              <span>Launch Benchmark</span>
            </Link>
            <Link
              href="/agents"
              className="inline-flex items-center space-x-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-medium px-5 py-2.5 rounded-xl transition-all text-sm"
            >
              <Cpu className="w-4 h-4" />
              <span>Register Agent</span>
            </Link>
          </div>
        </div>

        {/* Aggregate Stats Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-8 pt-8 border-t border-arena-border/60">
          <div>
            <div className="text-xs text-slate-500 font-medium uppercase tracking-wider">Agents Benchmarked</div>
            <div className="text-2xl font-bold text-white font-mono mt-1">{leaderboard.length}</div>
          </div>
          <div>
            <div className="text-xs text-slate-500 font-medium uppercase tracking-wider">Total Runs Completed</div>
            <div className="text-2xl font-bold text-cyan-400 font-mono mt-1">{totalRuns}</div>
          </div>
          <div>
            <div className="text-xs text-slate-500 font-medium uppercase tracking-wider">Overall Pass Rate</div>
            <div className="text-2xl font-bold text-emerald-400 font-mono mt-1">{overallPassRate}%</div>
          </div>
          <div>
            <div className="text-xs text-slate-500 font-medium uppercase tracking-wider">Standardized Gateway</div>
            <div className="text-2xl font-bold text-indigo-400 font-mono mt-1">Bifrost :8080</div>
          </div>
        </div>
      </div>

      {/* Efficiency Frontier Section */}
      <div className="rounded-3xl border border-arena-border bg-arena-surface/80 p-6 sm:p-8 shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight flex items-center space-x-2">
              <span>The Efficiency Frontier</span>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-indigo-500/15 text-indigo-400 border border-indigo-500/30">
                Cost vs Pass-Rate
              </span>
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Top-left agents are Pareto-optimal: high correctness at minimal token expenditure.
            </p>
          </div>
        </div>
        <EfficiencyFrontierChart data={leaderboard} />
      </div>

      {/* Leaderboard Table Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <Trophy className="w-5 h-5 text-amber-400" />
            <h2 className="text-xl font-bold text-white tracking-tight">Agent Leaderboard</h2>
          </div>
          <button
            onClick={loadData}
            className="text-xs text-slate-400 hover:text-white transition-colors font-mono"
          >
            Refresh Data
          </button>
        </div>

        {loading ? (
          <div className="p-12 text-center text-slate-400 bg-arena-surface rounded-2xl border border-arena-border">
            Loading leaderboard metrics...
          </div>
        ) : error ? (
          <div className="p-6 text-center text-rose-400 bg-rose-500/10 rounded-2xl border border-rose-500/30">
            {error}
          </div>
        ) : (
          <LeaderboardTable data={leaderboard} />
        )}
      </div>
    </div>
  );
}

