export type AgentType = 'builtin' | 'external_http';

export interface Agent {
  id: string;
  name: string;
  type: AgentType;
  endpoint?: string;
  model: string;
  description?: string;
  created_at: number;
}

export interface Task {
  id: string;
  title: string;
  difficulty: 'easy' | 'medium' | 'hard';
  timeout: number;
  prompt: string;
  starter_files: Record<string, string>;
  hidden_tests?: string;
}

export type BenchmarkStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface Benchmark {
  id: string;
  agent_ids: string[];
  task_ids: string[];
  model?: string;
  status: BenchmarkStatus;
  total_runs: number;
  completed_runs: number;
  created_at: number;
  finished_at?: number;
}

export type RunStatus = 'pending' | 'running' | 'completed' | 'failed' | 'timed_out';

export interface Run {
  id: string;
  benchmark_id: string;
  agent_id: string;
  task_id: string;
  model: string;
  status: RunStatus;
  passed: boolean;
  score: number;
  passed_tests: number;
  total_tests: number;
  tokens_in: number;
  tokens_out: number;
  tokens_total: number;
  cost_usd: number;
  latency_ms: number;
  llm_calls: number;
  error?: string | null;
  files: Record<string, string>;
  notes?: string | null;
  test_output?: string | null;
  created_at: number;
  finished_at?: number | null;
}

export interface LeaderboardItem {
  agent_id: string;
  agent_name: string;
  agent_type: string;
  model: string;
  total_runs: number;
  passed_runs: number;
  pass_rate: number;
  avg_score: number;
  avg_tokens: number;
  avg_tokens_in: number;
  avg_tokens_out: number;
  avg_cost_usd: number;
  avg_latency_ms: number;
  avg_llm_calls: number;
  efficiency_score: number;
}

