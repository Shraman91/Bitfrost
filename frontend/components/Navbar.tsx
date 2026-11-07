'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Shield, Zap, Cpu, PlayCircle, BarChart3, Radio } from 'lucide-react';
import { api } from '../lib/api';

export default function Navbar() {
  const pathname = usePathname();
  const [bifrostStatus, setBifrostStatus] = useState<{ reachable: boolean } | null>(null);

  useEffect(() => {
    api.getHealth()
      .then((res) => setBifrostStatus(res.bifrost))
      .catch(() => setBifrostStatus({ reachable: false }));
  }, []);

  const navLinks = [
    { href: '/', label: 'Leaderboard', icon: BarChart3 },
    { href: '/agents', label: 'Agents', icon: Cpu },
    { href: '/benchmarks/new', label: 'Run Benchmark', icon: PlayCircle },
  ];

  return (
    <nav className="border-b border-arena-border bg-arena-surface/80 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-8">
            <Link href="/" className="flex items-center space-x-2.5 group">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/20 group-hover:shadow-indigo-500/40 transition-all">
                <Zap className="w-5 h-5 text-white" />
              </div>
              <div className="flex flex-col">
                <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
                  AgentArena
                </span>
                <span className="text-[10px] text-cyan-400 font-mono tracking-wider uppercase -mt-1">
                  Bifrost Gateway
                </span>
              </div>
            </Link>

            <div className="hidden md:flex items-center space-x-1">
              {navLinks.map((link) => {
                const Icon = link.icon;
                const isActive = pathname === link.href;
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
                      isActive
                        ? 'bg-arena-accent/15 text-indigo-400 border border-arena-accent/30 shadow-sm'
                        : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{link.label}</span>
                  </Link>
                );
              })}
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-slate-900/80 border border-arena-border text-xs font-mono">
              <span className="relative flex h-2 w-2">
                <span
                  className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                    bifrostStatus?.reachable ? 'bg-emerald-400' : 'bg-amber-400'
                  }`}
                />
                <span
                  className={`relative inline-flex rounded-full h-2 w-2 ${
                    bifrostStatus?.reachable ? 'bg-emerald-500' : 'bg-amber-500'
                  }`}
                />
              </span>
              <span className="text-slate-400">Bifrost:</span>
              <span className={bifrostStatus?.reachable ? 'text-emerald-400' : 'text-amber-400'}>
                {bifrostStatus === null ? 'Checking...' : bifrostStatus.reachable ? 'Online :8080' : 'Ready (Mock)'}
              </span>
            </div>

            <Link
              href="/benchmarks/new"
              className="hidden sm:inline-flex items-center space-x-2 bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white px-4 py-2 rounded-lg text-sm font-medium shadow-md shadow-indigo-600/20 transition-all"
            >
              <PlayCircle className="w-4 h-4" />
              <span>Start Run</span>
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}

