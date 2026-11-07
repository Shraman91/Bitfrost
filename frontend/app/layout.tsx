import './globals.css';
import Navbar from '../components/Navbar';

export const metadata = {
  title: 'AgentArena - Benchmarking AI Coding Agents',
  description: 'Evaluate AI coding agents on identical tasks under identical constraints with standardized Bifrost metering.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-arena-bg text-slate-100 min-h-screen flex flex-col antialiased selection:bg-indigo-500/30 selection:text-indigo-200">
        <Navbar />
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
        <footer className="border-t border-arena-border py-6 text-center text-xs text-slate-500">
          AgentArena &bull; Powered by Maxim AI Bifrost LLM Gateway &bull; Standardized Token, Latency &amp; Cost Metering
        </footer>
      </body>
    </html>
  );
}

