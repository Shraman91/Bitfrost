'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { ArrowUpDown, Trophy, Zap, Clock, DollarSign, CheckCircle2 } from 'lucide-react';
import { LeaderboardItem } from '../types';

interface Props {
  data: LeaderboardItem[];
}

type SortField = 'efficiency_score' | 'pass_rate' | 'avg_cost_usd' | 'avg_tokens' | 'avg_latency_ms';

export default function LeaderboardTable({ data }: Props) {
  const [sortField, setSortField] = useState<SortField>('efficiency_score');
  const [sortAsc, setSortAsc] = useState<boolean>(false);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  const sortedData = [...data].sort((a, b) => {
    const valA = a[sortField];
    const valB = b[sortField];
    return sortAsc ? (valA > valB ? 1 : -1) : (valA < valB ? 1 : -1);
  });

  return (
    <div className="overflow-x-auto rounded-2xl border border-arena-border bg-arena-surface/90 shadow-xl">
      <table className="w-full text-left border-collapse text-sm">
        <thead>
          <tr className="border-b border-arena-border bg-arena-card/60 text-xs font-semibold text-slate-400 uppercase tracking-wider">
            <th className="py-4 px-5">Rank</th>
            <th className="py-4 px-5">Agent & Strategy</th>
            <th className="py-4 px-5 cursor-pointer hover:text-white" onClick={() => handleSort('efficiency_score')}>
              <div className="flex items-center space-x-1">
                <span>Efficiency Score</span>
                <ArrowUpDown className="w-3.5 h-3.5" />
              </div>
            </th>
            <th className="py-4 px-5 cursor-pointer hover:text-white" onClick={() => handleSort('pass_rate')}>
              <div className="flex items-center space-x-1">
                <span>Pass Rate</span>
                <ArrowUpDown className="w-3.5 h-3.5" />
              </div>
            </th>
            <th className="py-4 px-5 cursor-pointer hover:text-white" onClick={() => handleSort('avg_cost_usd')}>
              <div className="flex items-center space-x-1">
                <span>Avg Cost</span>
                <ArrowUpDown className="w-3.5 h-3.5" />
              </div>
            </th>
            <th className="py-4 px-5 cursor-pointer hover:text-white" onClick={() => handleSort('avg_tokens')}>
              <div className="flex items-center space-x-1">
                <span>Avg Tokens</span>
                <ArrowUpDown className="w-3.5 h-3.5" />
              </div>
            </th>
            <th className="py-4 px-5 cursor-pointer hover:text-white" onClick={() => handleSort('avg_latency_ms')}>
              <div className="flex items-center space-x-1">
                <span>Avg Latency</span>
                <ArrowUpDown className="w-3.5 h-3.5" />
              </div>
            </th>
            <th className="py-4 px-5">Runs</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-arena-border/50 text-slate-300">
          {sortedData.map((item, index) => {
            const isTop = index === 0 && item.total_runs > 0;
            return (
              <tr key={item.agent_id} className="hover:bg-slate-800/40 transition-colors">
                <td className="py-4 px-5 font-mono">
                  {isTop ? (
                    <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-amber-500/20 text-amber-400 font-bold border border-amber-500/40 text-xs">
                      1
                    </span>
                  ) : (
                    <span className="text-slate-500 font-medium">#{index + 1}</span>
                  )}
                </td>
                <td className="py-4 px-5">
                  <div className="flex flex-col">
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold text-white">{item.agent_name}</span>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-mono uppercase border ${
                        item.agent_type === 'builtin'
                          ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30'
                          : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                      }`}>
                        {item.agent_type}
                      </span>
                    </div>
                    <span className="text-xs text-slate-500 font-mono mt-0.5">{item.model}</span>
                  </div>
                </td>
                <td className="py-4 px-5">
                  <span className="text-base font-bold text-indigo-400 font-mono">
                    {item.efficiency_score.toFixed(1)}
                  </span>
                </td>
                <td className="py-4 px-5">
                  <div className="flex items-center space-x-2">
                    <span className={`font-semibold font-mono ${
                      item.pass_rate >= 80 ? 'text-emerald-400' : item.pass_rate >= 50 ? 'text-amber-400' : 'text-slate-400'
                    }`}>
                      {item.pass_rate.toFixed(1)}%
                    </span>
                    <span className="text-xs text-slate-500">
                      ({item.passed_runs}/{item.total_runs})
                    </span>
                  </div>
                </td>
                <td className="py-4 px-5 font-mono text-cyan-400">
                  ${item.avg_cost_usd.toFixed(5)}
                </td>
                <td className="py-4 px-5 font-mono text-slate-300">
                  {Math.round(item.avg_tokens).toLocaleString()}
                </td>
                <td className="py-4 px-5 font-mono text-slate-400">
                  {Math.round(item.avg_latency_ms)}ms
                </td>
                <td className="py-4 px-5 font-mono text-xs text-slate-400">
                  {item.total_runs}
                </td>
              </tr>
            );
          })}
          {sortedData.length === 0 && (
            <tr>
              <td colSpan={8} className="py-10 text-center text-slate-500">
                No agents registered yet. Seed builtin agents to get started.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

