'use client';

import React from 'react';
import Link from 'next/link';
import { CheckCircle2, XCircle, Clock, Loader2, ExternalLink } from 'lucide-react';
import { Run, Agent, Task } from '../types';

interface Props {
  runs: Run[];
  agents: Agent[];
  tasks: Task[];
}

export default function BenchmarkGrid({ runs, agents, tasks }: Props) {
  // Map (agent_id + task_id) -> run
  const runMap: Record<string, Run> = {};
  for (const r of runs) {
    runMap[`${r.agent_id}_${r.task_id}`] = r;
  }

  return (
    <div className="overflow-x-auto rounded-2xl border border-arena-border bg-arena-surface shadow-xl">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="border-b border-arena-border bg-arena-card/80 text-xs font-semibold text-slate-400 uppercase tracking-wider">
            <th className="py-4 px-5 min-w-[200px]">Task</th>
            {agents.map((agent) => (
              <th key={agent.id} className="py-4 px-5 min-w-[170px] text-center border-l border-arena-border/50">
                <div className="flex flex-col items-center">
                  <span className="text-white font-semibold">{agent.name}</span>
                  <span className="text-[10px] text-slate-500 font-mono lowercase">{agent.model}</span>
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-arena-border/50 text-sm">
          {tasks.map((task) => (
            <tr key={task.id} className="hover:bg-slate-800/30 transition-colors">
              <td className="py-4 px-5">
                <div className="flex flex-col">
                  <span className="font-medium text-white">{task.title}</span>
                  <div className="flex items-center space-x-2 mt-0.5">
                    <span className="text-xs text-slate-500 font-mono">{task.id}</span>
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
              </td>
              {agents.map((agent) => {
                const run = runMap[`${agent.id}_${task.id}`];

                if (!run) {
                  return (
                    <td key={agent.id} className="py-4 px-5 text-center border-l border-arena-border/50 text-slate-600 text-xs">
                      Pending
                    </td>
                  );
                }

                return (
                  <td key={agent.id} className="py-3 px-4 border-l border-arena-border/50">
                    <Link
                      href={`/runs/${run.id}`}
                      className="group flex flex-col p-2.5 rounded-xl border border-transparent hover:border-indigo-500/40 hover:bg-slate-800/60 transition-all text-xs"
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="flex items-center space-x-1.5">
                          {run.status === 'running' ? (
                            <span className="flex items-center space-x-1 text-amber-400 font-medium">
                              <Loader2 className="w-3.5 h-3.5 animate-spin" />
                              <span>Running</span>
                            </span>
                          ) : run.passed ? (
                            <span className="flex items-center space-x-1 text-emerald-400 font-medium">
                              <CheckCircle2 className="w-3.5 h-3.5" />
                              <span>Passed</span>
                            </span>
                          ) : (
                            <span className="flex items-center space-x-1 text-rose-400 font-medium">
                              <XCircle className="w-3.5 h-3.5" />
                              <span>Failed</span>
                            </span>
                          )}
                        </span>
                        <ExternalLink className="w-3 h-3 text-slate-600 group-hover:text-indigo-400 transition-colors" />
                      </div>

                      <div className="grid grid-cols-2 gap-1 text-[11px] font-mono text-slate-400">
                        <div>Score: <span className="text-white font-semibold">{Math.round(run.score * 100)}%</span></div>
                        <div>Cost: <span className="text-cyan-400">${run.cost_usd.toFixed(4)}</span></div>
                        <div>Tokens: <span className="text-slate-300">{run.tokens_total}</span></div>
                        <div>Time: <span className="text-slate-400">{Math.round(run.latency_ms)}ms</span></div>
                      </div>
                    </Link>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

