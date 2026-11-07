'use client';

import React, { useEffect, useState, useRef } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { PlayCircle, CheckCircle2, Clock, Loader2, BarChart2, ArrowLeft, RefreshCw } from 'lucide-react';
import { api } from '../../../lib/api';
import { Benchmark, Run, Agent, Task } from '../../../types';
import BenchmarkGrid from '../../../components/BenchmarkGrid';
import ComparisonCharts from '../../../components/ComparisonCharts';

export default function BenchmarkDetailPage() {
  const params = useParams();
  const id = params?.id as string;

  const [benchmark, setBenchmark] = useState<Benchmark | null>(null);
  const [runs, setRuns] = useState<Run[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);

  // Load benchmark details, agents, and tasks
  const loadBenchmark = async () => {
    if (!id) return;
    try {
      const [benchData, allAgents, allTasks] = await Promise.all([
        api.getBenchmark(id),
        api.getAgents(),
        api.getTasks(),
      ]);

      setBenchmark(benchData.benchmark);
      setRuns(benchData.runs);

      // Filter agents and tasks that belong to this benchmark
      const activeAgents = allAgents.filter((a) => benchData.benchmark.agent_ids.includes(a.id));
      const activeTasks = allTasks.filter((t) => benchData.benchmark.task_ids.includes(t.id));

      setAgents(activeAgents.length > 0 ? activeAgents : allAgents);
      setTasks(activeTasks.length > 0 ? activeTasks : allTasks);
    } catch (err: any) {
      setError(err.message || 'Failed to load benchmark');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBenchmark();

    // Setup SSE live stream
    const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const sseUrl = `${API_BASE.replace(/\/$/, '')}/benchmarks/${id}/live`;
    const es = new EventSource(sseUrl);
    eventSourceRef.current = es;

    es.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.type === 'run_completed' || payload.type === 'run_started') {
          const updatedRun: Run = payload.run;
          setRuns((prev) => {
            const index = prev.findIndex((r) => r.id === updatedRun.id);
            if (index >= 0) {
              const copy = [...prev];
              copy[index] = updatedRun;
              return copy;
            }
            return [...prev, updatedRun];
          });
        } else if (payload.type === 'benchmark_progress') {
          setBenchmark((prev) =>
            prev ? { ...prev, completed_runs: payload.completed_runs, status: payload.status } : null
          );
        }
      } catch (e) {
        console.error('SSE parse error:', e);
      }
    };

    es.onerror = () => {
      // Fallback polling if SSE disconnects
      console.log('SSE connection degraded, falling back to polling.');
    };

    // Polling fallback interval while running
    const pollInterval = setInterval(() => {
      if (benchmark?.status === 'running') {
        loadBenchmark();
      }
    }, 4000);

    return () => {
      es.close();
      clearInterval(pollInterval);
    };
  }, [id]);

  if (loading) {
    return (
      <div className="py-20 text-center text-slate-400 flex flex-col items-center justify-center space-y-3">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
        <p className="text-sm">Loading benchmark {id}...</p>
      </div>
    );
  }

  if (error || !benchmark) {
    return (
      <div className="p-8 text-center bg-rose-500/10 border border-rose-500/30 rounded-2xl text-rose-400 space-y-3">
        <p>{error || 'Benchmark not found'}</p>
        <Link href="/" className="inline-block text-xs text-white underline">
          Back to Leaderboard
        </Link>
      </div>
    );
  }

  const progressPercent =
    benchmark.total_runs > 0
      ? Math.round((benchmark.completed_runs / benchmark.total_runs) * 100)
      : 0;

  return (
    <div className="space-y-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <Link
            href="/"
            className="inline-flex items-center space-x-1.5 text-xs text-slate-400 hover:text-white transition-colors mb-1"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Leaderboard</span>
          </Link>
          <div className="flex items-center space-x-3">
            <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight font-mono">
              {benchmark.id}
            </h1>
            <span
              className={`text-xs px-2.5 py-1 rounded-full font-mono font-semibold uppercase ${
                benchmark.status === 'completed'
                  ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                  : 'bg-amber-500/15 text-amber-400 border border-amber-500/30 flex items-center space-x-1'
              }`}
            >
              {benchmark.status === 'running' && <Loader2 className="w-3 h-3 animate-spin mr-1" />}
              {benchmark.status}
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Model: <span className="font-mono text-cyan-400">{benchmark.model || 'openai/gpt-4o-mini'}</span>
          </p>
        </div>

        <button
          onClick={loadBenchmark}
          className="self-start sm:self-auto flex items-center space-x-2 bg-slate-800 hover:bg-slate-700 text-slate-300 px-3.5 py-2 rounded-xl text-xs font-medium border border-slate-700 transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Progress Bar */}
      <div className="rounded-2xl border border-arena-border bg-arena-surface p-5 space-y-2.5 shadow-lg">
        <div className="flex justify-between text-xs text-slate-400">
          <span>
            Progress: <strong className="text-white">{benchmark.completed_runs}</strong> of{' '}
            <strong className="text-white">{benchmark.total_runs}</strong> runs completed
          </span>
          <span className="font-mono text-indigo-400 font-bold">{progressPercent}%</span>
        </div>
        <div className="w-full bg-slate-900 rounded-full h-2.5 overflow-hidden border border-slate-800">
          <div
            className="bg-gradient-to-r from-indigo-500 to-cyan-400 h-2.5 rounded-full transition-all duration-500"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      {/* Live Agent x Task Matrix Grid */}
      <div className="space-y-3">
        <h2 className="text-base font-semibold text-white tracking-tight flex items-center space-x-2">
          <span>Execution Matrix (Agents &times; Tasks)</span>
          <span className="text-[10px] text-cyan-400 font-mono bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">
            Live Updates
          </span>
        </h2>
        <BenchmarkGrid runs={runs} agents={agents} tasks={tasks} />
      </div>

      {/* Agent Comparison Bar Charts */}
      {runs.length > 0 && (
        <div className="space-y-4 pt-4">
          <h2 className="text-base font-semibold text-white tracking-tight">Agent Performance Comparison</h2>
          <ComparisonCharts runs={runs} agents={agents} />
        </div>
      )}
    </div>
  );
}

