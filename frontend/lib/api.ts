import { Agent, Task, Benchmark, Run, LeaderboardItem } from '../types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE.replace(/\/$/, '')}${endpoint}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    cache: 'no-store',
  });

  if (!res.ok) {
    let errorDetail = `HTTP ${res.status}`;
    try {
      const errJson = await res.json();
      errorDetail = errJson.detail || errJson.message || errorDetail;
    } catch {
      errorDetail = await res.text();
    }
    throw new Error(errorDetail);
  }

  return res.json();
}

export const api = {
  // Health
  getHealth: () => fetchJson<{ status: string; bifrost: { reachable: boolean; url: string; error?: string }; database: { connected: boolean } }>('/health'),

  // Leaderboard
  getLeaderboard: () => fetchJson<LeaderboardItem[]>('/leaderboard'),

  // Agents
  getAgents: () => fetchJson<Agent[]>('/agents'),
  getAgent: (id: string) => fetchJson<Agent>(`/agents/${id}`),
  createAgent: (data: Partial<Agent>) =>
    fetchJson<Agent>('/agents', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  deleteAgent: (id: string) =>
    fetchJson<{ status: string }>(`/agents/${id}`, {
      method: 'DELETE',
    }),
  testConnection: (endpoint: string) =>
    fetchJson<{ success: boolean; status_code?: number; latency_ms: number; message: string }>('/agents/test-connection', {
      method: 'POST',
      body: JSON.stringify({ endpoint }),
    }),

  // Tasks
  getTasks: () => fetchJson<Task[]>('/tasks'),
  getTask: (id: string) => fetchJson<Task>(`/tasks/${id}`),

  // Benchmarks
  createBenchmark: (data: { agent_ids: string[]; task_ids: string[]; model?: string }) =>
    fetchJson<Benchmark>('/benchmarks', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  getBenchmark: (id: string) => fetchJson<{ benchmark: Benchmark; runs: Run[] }>(`/benchmarks/${id}`),

  // Runs
  getRun: (id: string) => fetchJson<{ run: Run; task: Task | null }>(`/runs/${id}`),
};

