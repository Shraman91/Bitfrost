'use client';

import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { Run, Agent } from '../types';

interface Props {
  runs: Run[];
  agents: Agent[];
}

export default function ComparisonCharts({ runs, agents }: Props) {
  // Aggregate metrics per agent for this benchmark
  const chartData = agents.map((agent) => {
    const agentRuns = runs.filter((r) => r.agent_id === agent.id);
    const total = agentRuns.length;
    const passed = agentRuns.filter((r) => r.passed).length;
    const passRate = total > 0 ? (passed / total) * 100 : 0;
    const avgCost = total > 0 ? agentRuns.reduce((acc, r) => acc + r.cost_usd, 0) / total : 0;
    const avgLatency = total > 0 ? agentRuns.reduce((acc, r) => acc + r.latency_ms, 0) / total : 0;
    const avgTokens = total > 0 ? agentRuns.reduce((acc, r) => acc + r.tokens_total, 0) / total : 0;

    return {
      name: agent.name,
      passRate: Math.round(passRate),
      avgCost: Number(avgCost.toFixed(5)),
      avgLatency: Math.round(avgLatency),
      avgTokens: Math.round(avgTokens),
    };
  });

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {/* Chart 1: Pass Rate */}
      <div className="bg-arena-surface border border-arena-border rounded-2xl p-5 shadow-lg">
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">
          Pass Rate (%)
        </h3>
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 10, bottom: 20, left: -10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f293d" />
              <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <YAxis domain={[0, 100]} tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: 8, fontSize: 12 }}
                formatter={(val) => [`${val}%`, 'Pass Rate']}
              />
              <Bar dataKey="passRate" fill="#10b981" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Chart 2: Avg Cost */}
      <div className="bg-arena-surface border border-arena-border rounded-2xl p-5 shadow-lg">
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">
          Avg Cost per Task ($)
        </h3>
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 10, bottom: 20, left: -10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f293d" />
              <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} tickFormatter={(v) => `$${v}`} />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: 8, fontSize: 12 }}
                formatter={(val: number) => [`$${val.toFixed(5)}`, 'Avg Cost']}
              />
              <Bar dataKey="avgCost" fill="#06b6d4" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Chart 3: Avg Latency */}
      <div className="bg-arena-surface border border-arena-border rounded-2xl p-5 shadow-lg">
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">
          Avg Latency (ms)
        </h3>
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 10, bottom: 20, left: -10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f293d" />
              <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: 8, fontSize: 12 }}
                formatter={(val) => [`${val}ms`, 'Avg Latency']}
              />
              <Bar dataKey="avgLatency" fill="#6366f1" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

