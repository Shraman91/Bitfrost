'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { PlayCircle, CheckSquare, Square, Cpu, Check, Filter } from 'lucide-react';
import { api } from '../../../lib/api';
import { Agent, Task } from '../../../types';

export default function NewBenchmarkPage() {
  const router = useRouter();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Selections
  const [selectedAgentIds, setSelectedAgentIds] = useState<string[]>([]);
  const [selectedTaskIds, setSelectedTaskIds] = useState<string[]>([]);
  const [modelOverride, setModelOverride] = useState<string>('openai/gpt-4o-mini');
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [agentsData, tasksData] = await Promise.all([
        api.getAgents(),
        api.getTasks(),
      ]);
      setAgents(agentsData);
      setTasks(tasksData);
      // Select all by default
      setSelectedAgentIds(agentsData.map((a) => a.id));
      setSelectedTaskIds(tasksData.map((t) => t.id));
    } catch (err: any) {
      setError(err.message || 'Failed to load agents or tasks');
    } finally {
      setLoading(false);
    }
  };

  const toggleAgent = (id: string) => {
    setSelectedAgentIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const toggleTask = (id: string) => {
    setSelectedTaskIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const handleSelectAllAgents = () => {
    if (selectedAgentIds.length === agents.length) {
      setSelectedAgentIds([]);
    } else {
      setSelectedAgentIds(agents.map((a) => a.id));
    }
  };

  const handleSelectAllTasks = () => {
    if (selectedTaskIds.length === tasks.length) {
      setSelectedTaskIds([]);
    } else {
      setSelectedTaskIds(tasks.map((t) => t.id));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedAgentIds.length === 0 || selectedTaskIds.length === 0) {
      setError('Please select at least one agent and one task.');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      const bench = await api.createBenchmark({
        agent_ids: selectedAgentIds,
        task_ids: selectedTaskIds,
        model: modelOverride || undefined,
      });
      router.push(`/benchmarks/${bench.id}`);
    } catch (err: any) {
      setError(err.message || 'Failed to create benchmark');
      setSubmitting(false);
    }
  };

  const totalRuns = selectedAgentIds.length * selectedTaskIds.length;

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight flex items-center space-x-2.5">
          <PlayCircle className="w-7 h-7 text-indigo-400" />
          <span>Launch New Benchmark</span>
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Configure agents and task suite to benchmark identical code generation under Bifrost gateway metering.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Model Selection */}
        <div className="rounded-2xl border border-arena-border bg-arena-surface p-6 shadow-xl space-y-3">
          <label className="block text-sm font-semibold text-white">Target LLM Model</label>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {[
              { id: 'openai/gpt-4o-mini', name: 'GPT-4o-mini', desc: '$0.15 / 1M in' },
              { id: 'openai/gpt-4o', name: 'GPT-4o', desc: '$2.50 / 1M in' },
              { id: 'anthropic/claude-3-5-sonnet', name: 'Claude 3.5 Sonnet', desc: '$3.00 / 1M in' },
            ].map((m) => (
              <button
                type="button"
                key={m.id}
                onClick={() => setModelOverride(m.id)}
                className={`p-3.5 rounded-xl border text-left transition-all ${
                  modelOverride === m.id
                    ? 'border-indigo-500 bg-indigo-500/10 text-white'
                    : 'border-arena-border bg-slate-900/60 text-slate-400 hover:text-white'
                }`}
              >
                <div className="font-semibold text-sm">{m.name}</div>
                <div className="text-xs font-mono text-slate-500 mt-0.5">{m.id}</div>
                <div className="text-[11px] text-cyan-400 font-mono mt-1">{m.desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Agent Selection */}
        <div className="rounded-2xl border border-arena-border bg-arena-surface p-6 shadow-xl space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-semibold text-white">Select Agents ({selectedAgentIds.length}/{agents.length})</h2>
              <p className="text-xs text-slate-400">Choose agents to evaluate in this benchmark run.</p>
            </div>
            <button
              type="button"
              onClick={handleSelectAllAgents}
              className="text-xs text-indigo-400 hover:text-indigo-300 font-medium"
            >
              {selectedAgentIds.length === agents.length ? 'Deselect All' : 'Select All'}
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {agents.map((agent) => {
              const selected = selectedAgentIds.includes(agent.id);
              return (
                <div
                  key={agent.id}
                  onClick={() => toggleAgent(agent.id)}
                  className={`cursor-pointer p-4 rounded-xl border transition-all flex flex-col justify-between ${
                    selected
                      ? 'border-indigo-500 bg-indigo-500/10 text-white'
                      : 'border-arena-border bg-slate-900/50 text-slate-400 hover:bg-slate-800/40'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <span className="font-semibold text-sm">{agent.name}</span>
                    {selected ? (
                      <CheckSquare className="w-4 h-4 text-indigo-400 shrink-0" />
                    ) : (
                      <Square className="w-4 h-4 text-slate-600 shrink-0" />
                    )}
                  </div>
                  <div className="text-xs text-slate-500 mt-2 line-clamp-2">{agent.description}</div>
                  <div className="text-[10px] font-mono text-cyan-400 uppercase mt-3">
                    {agent.type}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Task Selection */}
        <div className="rounded-2xl border border-arena-border bg-arena-surface p-6 shadow-xl space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-semibold text-white">Select Tasks ({selectedTaskIds.length}/{tasks.length})</h2>
              <p className="text-xs text-slate-400">Coding tasks with hidden test suites executed in isolated sandboxes.</p>
            </div>
            <button
              type="button"
              onClick={handleSelectAllTasks}
              className="text-xs text-indigo-400 hover:text-indigo-300 font-medium"
            >
              {selectedTaskIds.length === tasks.length ? 'Deselect All' : 'Select All'}
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-96 overflow-y-auto pr-1">
            {tasks.map((task) => {
              const selected = selectedTaskIds.includes(task.id);
              return (
                <div
                  key={task.id}
                  onClick={() => toggleTask(task.id)}
                  className={`cursor-pointer p-3.5 rounded-xl border transition-all flex items-center justify-between ${
                    selected
                      ? 'border-indigo-500 bg-indigo-500/10 text-white'
                      : 'border-arena-border bg-slate-900/50 text-slate-400 hover:bg-slate-800/40'
                  }`}
                >
                  <div className="flex flex-col pr-2">
                    <span className="font-medium text-sm text-slate-200">{task.title}</span>
                    <div className="flex items-center space-x-2 mt-0.5">
                      <span className="text-[11px] text-slate-500 font-mono">{task.id}</span>
                      <span className={`text-[10px] px-1.5 py-0.2 rounded font-mono ${
                        task.difficulty === 'easy'
                          ? 'bg-emerald-500/10 text-emerald-400'
                          : task.difficulty === 'medium'
                          ? 'bg-amber-500/10 text-amber-400'
                          : 'bg-rose-500/10 text-rose-400'
                      }`}>
                        {task.difficulty}
                      </span>
                    </div>
                  </div>
                  {selected ? (
                    <CheckSquare className="w-4 h-4 text-indigo-400 shrink-0" />
                  ) : (
                    <Square className="w-4 h-4 text-slate-600 shrink-0" />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Submit Bar */}
        <div className="rounded-2xl border border-arena-border bg-arena-card/80 p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="text-sm">
            <span className="text-slate-400">Total Benchmark Runs: </span>
            <span className="font-bold text-white font-mono text-base">{totalRuns}</span>
            <span className="text-xs text-slate-500 ml-2">
              ({selectedAgentIds.length} agents &times; {selectedTaskIds.length} tasks)
            </span>
          </div>

          <button
            type="submit"
            disabled={submitting || totalRuns === 0}
            className="inline-flex items-center justify-center space-x-2 bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white font-medium px-6 py-2.5 rounded-xl shadow-lg shadow-indigo-600/30 transition-all text-sm disabled:opacity-50"
          >
            <PlayCircle className="w-4 h-4" />
            <span>{submitting ? 'Starting...' : 'Start Benchmark'}</span>
          </button>
        </div>
      </form>
    </div>
  );
}

