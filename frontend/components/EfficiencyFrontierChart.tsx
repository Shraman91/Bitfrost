'use client';

import React from 'react';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { LeaderboardItem } from '../types';

interface Props {
  data: LeaderboardItem[];
}

export default function EfficiencyFrontierChart({ data }: Props) {
  const chartData = data
    .filter((item) => item.total_runs > 0)
    .map((item) => ({
      name: item.agent_name,
      model: item.model,
      cost: item.avg_cost_usd,
      passRate: item.pass_rate,
      efficiency: item.efficiency_score,
      tokens: item.avg_tokens,
    }));

  if (chartData.length === 0) {
    return (
      <div className="h-72 flex flex-col items-center justify-center border border-dashed border-arena-border rounded-2xl bg-arena-card/30 p-6 text-center">
        <p className="text-slate-400 text-sm">No benchmark data available yet.</p>
        <p className="text-slate-600 text-xs mt-1">Run a benchmark to plot the efficiency frontier.</p>
      </div>
    );
  }

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const d = payload[0].payload;
      return (
        <div className="bg-slate-900 border border-arena-border p-3.5 rounded-xl shadow-xl text-xs space-y-1.5 min-w-[200px]">
          <p className="font-semibold text-white text-sm">{d.name}</p>
          <p className="text-slate-400 font-mono text-[11px]">{d.model}</p>
          <div className="border-t border-slate-800 my-1 pt-1.5 space-y-1">
            <div className="flex justify-between">
              <span className="text-slate-400">Pass Rate:</span>
              <span className="font-semibold text-emerald-400">{d.passRate}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Avg Cost / Run:</span>
              <span className="font-mono text-cyan-400">${d.cost.toFixed(5)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Avg Tokens:</span>
              <span className="font-mono text-slate-300">{Math.round(d.tokens)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Efficiency Score:</span>
              <span className="font-bold text-indigo-400">{d.efficiency}</span>
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ top: 20, right: 30, bottom: 20, left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f293d" />
          <XAxis
            type="number"
            dataKey="cost"
            name="Avg Cost"
            unit="$"
            stroke="#64748b"
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            tickFormatter={(val) => `$${val.toFixed(4)}`}
            label={{ value: 'Avg Cost per Task ($ USD)', position: 'insideBottom', offset: -10, fill: '#64748b', fontSize: 12 }}
          />
          <YAxis
            type="number"
            dataKey="passRate"
            name="Pass Rate"
            unit="%"
            domain={[0, 100]}
            stroke="#64748b"
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            label={{ value: 'Task Pass Rate (%)', angle: -90, position: 'insideLeft', offset: 0, fill: '#64748b', fontSize: 12 }}
          />
          <ZAxis range={[120, 240]} />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine y={80} stroke="#10b981" strokeDasharray="4 4" label={{ value: 'Target 80%', fill: '#10b981', fontSize: 10, position: 'insideTopRight' }} />
          <Scatter
            name="Agents"
            data={chartData}
            fill="#6366f1"
            stroke="#818cf8"
            strokeWidth={2}
          />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}

