'use client';

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import {
  ArrowLeft,
  CheckCircle2,
  XCircle,
  Coins,
  Clock,
  Layers,
  Terminal,
  FileCode,
  FileText,
  Loader2,
} from 'lucide-react';
import { api } from '../../../lib/api';
import { Run, Task } from '../../../types';
import CodeViewer from '../../../components/CodeViewer';

export default function RunDetailPage() {
  const params = useParams();
  const id = params?.id as string;

  const [run, setRun] = useState<Run | null>(null);
  const [task, setTask] = useState<Task | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    loadRun();
  }, [id]);

  const loadRun = async () => {
    try {
      setLoading(true);
      const data = await api.getRun(id);
      setRun(data.run);
      setTask(data.task);
    } catch (err: any) {
      setError(err.message || 'Failed to load run details');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="py-20 text-center text-slate-400 flex flex-col items-center justify-center space-y-3">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
        <p className="text-sm">Loading run {id}...</p>
      </div>
    );
  }

  if (error || !run) {
    return (
      <div className="p-8 text-center bg-rose-500/10 border border-rose-500/30 rounded-2xl text-rose-400 space-y-3">
        <p>{error || 'Run not found'}</p>
        <Link href="/" className="inline-block text-xs text-white underline">
          Back to Home
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Top Header */}
      <div className="space-y-2">
        <Link
          href={`/benchmarks/${run.benchmark_id}`}
          className="inline-flex items-center space-x-1.5 text-xs text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Benchmark Matrix</span>
        </Link>

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center space-x-3">
              <h1 className="text-xl sm:text-2xl font-bold text-white font-mono tracking-tight">
                {run.id}
              </h1>
              <span
                className={`inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-mono font-semibold ${
                  run.passed
                    ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                    : 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                }`}
              >
                {run.passed ? (
                  <>
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Passed (Score: {Math.round(run.score * 100)}%)</span>
                  </>
                ) : (
                  <>
                    <XCircle className="w-3.5 h-3.5" />
                    <span>Failed (Score: {Math.round(run.score * 100)}%)</span>
                  </>
                )}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Agent: <span className="font-semibold text-slate-200">{run.agent_id}</span> &bull; Task:{' '}
              <span className="font-semibold text-slate-200">{run.task_id}</span> &bull; Model:{' '}
              <span className="font-mono text-cyan-400">{run.model}</span>
            </p>
          </div>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="rounded-2xl border border-arena-border bg-arena-surface p-4 shadow-lg">
          <div className="flex items-center space-x-2 text-xs text-slate-400 mb-1">
            <Coins className="w-4 h-4 text-cyan-400" />
            <span>Cost (USD)</span>
          </div>
          <div className="text-xl font-bold text-cyan-400 font-mono">
            ${run.cost_usd.toFixed(5)}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5 font-mono">Bifrost Metered</div>
        </div>

        <div className="rounded-2xl border border-arena-border bg-arena-surface p-4 shadow-lg">
          <div className="flex items-center space-x-2 text-xs text-slate-400 mb-1">
            <Layers className="w-4 h-4 text-indigo-400" />
            <span>Tokens (Total)</span>
          </div>
          <div className="text-xl font-bold text-white font-mono">
            {run.tokens_total.toLocaleString()}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5 font-mono">
            in: {run.tokens_in} &bull; out: {run.tokens_out}
          </div>
        </div>

        <div className="rounded-2xl border border-arena-border bg-arena-surface p-4 shadow-lg">
          <div className="flex items-center space-x-2 text-xs text-slate-400 mb-1">
            <Clock className="w-4 h-4 text-amber-400" />
            <span>Latency</span>
          </div>
          <div className="text-xl font-bold text-amber-400 font-mono">
            {Math.round(run.latency_ms)}ms
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5 font-mono">Gateway overhead incl.</div>
        </div>

        <div className="rounded-2xl border border-arena-border bg-arena-surface p-4 shadow-lg">
          <div className="flex items-center space-x-2 text-xs text-slate-400 mb-1">
            <Terminal className="w-4 h-4 text-emerald-400" />
            <span>LLM Calls</span>
          </div>
          <div className="text-xl font-bold text-white font-mono">
            {run.llm_calls}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5 font-mono">
            Tests passed: {run.passed_tests}/{run.total_tests}
          </div>
        </div>
      </div>

      {/* Task Prompt Display */}
      {task && (
        <div className="rounded-2xl border border-arena-border bg-arena-surface p-6 space-y-3 shadow-lg">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-white uppercase tracking-wider flex items-center space-x-2">
              <FileText className="w-4 h-4 text-indigo-400" />
              <span>Task Prompt: {task.title}</span>
            </h2>
            <span className={`text-[10px] font-mono px-2 py-0.5 rounded ${
              task.difficulty === 'easy' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'
            }`}>
              {task.difficulty}
            </span>
          </div>
          <div className="bg-slate-900/80 rounded-xl p-4 text-xs text-slate-300 font-mono whitespace-pre-wrap leading-relaxed border border-arena-border/50">
            {task.prompt}
          </div>
        </div>
      )}

      {/* Generated Code Viewer */}
      <div className="space-y-3">
        <h2 className="text-sm font-semibold text-white uppercase tracking-wider flex items-center space-x-2">
          <FileCode className="w-4 h-4 text-indigo-400" />
          <span>Generated Solution Files</span>
        </h2>
        <CodeViewer files={run.files || {}} />
      </div>

      {/* Sandbox Test Execution Logs */}
      <div className="space-y-3">
        <h2 className="text-sm font-semibold text-white uppercase tracking-wider flex items-center space-x-2">
          <Terminal className="w-4 h-4 text-emerald-400" />
          <span>Sandbox Test Output (unittest log)</span>
        </h2>
        <div className="rounded-xl border border-arena-border bg-slate-950 p-4 font-mono text-xs overflow-x-auto max-h-72">
          {run.test_output ? (
            <pre className="text-slate-300 whitespace-pre-wrap">{run.test_output}</pre>
          ) : run.error ? (
            <pre className="text-rose-400 whitespace-pre-wrap">Error: {run.error}</pre>
          ) : (
            <span className="text-slate-600">No test output recorded.</span>
          )}
        </div>
      </div>

      {/* Agent Notes */}
      {run.notes && (
        <div className="rounded-2xl border border-arena-border bg-arena-surface/60 p-4 text-xs text-slate-400">
          <strong className="text-slate-300">Agent Notes:</strong> {run.notes}
        </div>
      )}
    </div>
  );
}

