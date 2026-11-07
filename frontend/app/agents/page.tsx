'use client';

import React, { useEffect, useState } from 'react';
import { Cpu, Plus, Radio, Trash2, CheckCircle2, AlertCircle, ExternalLink, Zap } from 'lucide-react';
import { api } from '../../lib/api';
import { Agent } from '../../types';

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);

  // Form state
  const [name, setName] = useState('');
  const [endpoint, setEndpoint] = useState('http://localhost:8001/run');
  const [model, setModel] = useState('openai/gpt-4o-mini');
  const [description, setDescription] = useState('');
  
  // Connection testing state
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string; latency_ms: number } | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    try {
      setLoading(true);
      const data = await api.getAgents();
      setAgents(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleTestConnection = async () => {
    if (!endpoint) return;
    setTesting(true);
    setTestResult(null);
    try {
      const res = await api.testConnection(endpoint);
      setTestResult(res);
    } catch (err: any) {
      setTestResult({ success: false, message: err.message || 'Connection failed', latency_ms: 0 });
    } finally {
      setTesting(false);
    }
  };

  const handleCreateAgent = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError(null);
    try {
      await api.createAgent({
        name,
        type: 'external_http',
        endpoint,
        model,
        description,
      });
      setIsModalOpen(false);
      setName('');
      setDescription('');
      setTestResult(null);
      loadAgents();
    } catch (err: any) {
      setSubmitError(err.message || 'Failed to create agent');
    }
  };

  const handleDeleteAgent = async (id: string) => {
    if (!confirm('Are you sure you want to delete this agent?')) return;
    try {
      await api.deleteAgent(id);
      loadAgents();
    } catch (err) {
      console.error(err);
    }
  };

  const builtinAgents = agents.filter((a) => a.type === 'builtin');
  const externalAgents = agents.filter((a) => a.type === 'external_http');

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight flex items-center space-x-2.5">
            <Cpu className="w-7 h-7 text-indigo-400" />
            <span>Agent Registry</span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Built-in reference agents and external framework integrations adhering to the contract.
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="inline-flex items-center space-x-2 bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-xl text-sm font-medium shadow-md transition-all self-start"
        >
          <Plus className="w-4 h-4" />
          <span>Register External Agent</span>
        </button>
      </div>

      {/* Builtin Reference Agents */}
      <div className="space-y-4">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400 flex items-center space-x-2">
          <Zap className="w-4 h-4 text-amber-400" />
          <span>Built-in Reference Agents</span>
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {builtinAgents.map((agent) => (
            <div
              key={agent.id}
              className="rounded-2xl border border-arena-border bg-arena-surface p-5 shadow-lg flex flex-col justify-between hover:border-indigo-500/40 transition-all"
            >
              <div className="space-y-2.5">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white text-base">{agent.name}</span>
                  <span className="text-[10px] px-2 py-0.5 rounded-full font-mono bg-indigo-500/15 text-indigo-400 border border-indigo-500/30 uppercase">
                    builtin
                  </span>
                </div>
                <div className="text-xs text-slate-400 leading-relaxed">{agent.description}</div>
              </div>
              <div className="pt-4 mt-4 border-t border-arena-border/50 flex items-center justify-between text-xs font-mono text-slate-500">
                <span>Model: {agent.model}</span>
                <span className="text-emerald-400">Strict Metered</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* External Agents */}
      <div className="space-y-4 pt-4">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400 flex items-center space-x-2">
          <Radio className="w-4 h-4 text-emerald-400" />
          <span>External HTTP Agents ({externalAgents.length})</span>
        </h2>

        {externalAgents.length === 0 ? (
          <div className="p-8 text-center rounded-2xl border border-dashed border-arena-border bg-arena-surface/40 text-slate-500 text-sm">
            No external agents registered yet. Click &quot;Register External Agent&quot; to hook up an agent via the standard contract.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {externalAgents.map((agent) => (
              <div
                key={agent.id}
                className="rounded-2xl border border-arena-border bg-arena-surface p-5 shadow-lg flex flex-col justify-between hover:border-emerald-500/40 transition-all"
              >
                <div className="space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-white text-base">{agent.name}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full font-mono bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 uppercase">
                      external
                    </span>
                  </div>
                  <div className="text-xs text-slate-400">{agent.description || 'Custom external coding agent.'}</div>
                  <div className="text-xs font-mono text-cyan-400 bg-slate-900/60 p-2 rounded-lg break-all">
                    {agent.endpoint}
                  </div>
                </div>

                <div className="pt-4 mt-4 border-t border-arena-border/50 flex items-center justify-between">
                  <span className="text-xs font-mono text-slate-500">{agent.model}</span>
                  <button
                    onClick={() => handleDeleteAgent(agent.id)}
                    className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                    title="Delete Agent"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Registration Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="bg-arena-surface border border-arena-border rounded-2xl p-6 sm:p-8 max-w-lg w-full shadow-2xl space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-white">Register External Agent</h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateAgent} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Agent Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. MyLangChainAgent"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-slate-900 border border-arena-border rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Endpoint URL (POST)</label>
                <div className="flex space-x-2">
                  <input
                    type="url"
                    required
                    placeholder="http://localhost:8001/run"
                    value={endpoint}
                    onChange={(e) => setEndpoint(e.target.value)}
                    className="flex-1 bg-slate-900 border border-arena-border rounded-xl px-3.5 py-2 text-sm font-mono text-white focus:outline-none focus:border-indigo-500"
                  />
                  <button
                    type="button"
                    onClick={handleTestConnection}
                    disabled={testing}
                    className="bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 px-3 py-2 rounded-xl text-xs font-medium transition-colors"
                  >
                    {testing ? 'Pinging...' : 'Test'}
                  </button>
                </div>
                {testResult && (
                  <div className={`mt-2 p-2.5 rounded-lg text-xs flex items-center space-x-2 ${
                    testResult.success ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                  }`}>
                    {testResult.success ? <CheckCircle2 className="w-4 h-4 shrink-0" /> : <AlertCircle className="w-4 h-4 shrink-0" />}
                    <span>{testResult.message} ({testResult.latency_ms}ms)</span>
                  </div>
                )}
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Target LLM Model</label>
                <input
                  type="text"
                  required
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  placeholder="openai/gpt-4o-mini"
                  className="w-full bg-slate-900 border border-arena-border rounded-xl px-3.5 py-2 text-sm font-mono text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Description</label>
                <textarea
                  rows={2}
                  placeholder="Agent architecture, prompting strategy, or framework used."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full bg-slate-900 border border-arena-border rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              {submitError && (
                <div className="p-3 rounded-lg bg-rose-500/10 text-rose-400 text-xs border border-rose-500/20">
                  {submitError}
                </div>
              )}

              <div className="flex justify-end space-x-3 pt-3">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 text-sm text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="bg-indigo-600 hover:bg-indigo-500 text-white font-medium px-5 py-2 rounded-xl text-sm transition-all"
                >
                  Register Agent
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

