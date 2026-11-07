'use client';

import React, { useState } from 'react';
import { Copy, Check, FileCode } from 'lucide-react';

interface Props {
  files: Record<string, string>;
}

export default function CodeViewer({ files }: Props) {
  const fileKeys = Object.keys(files);
  const [selectedFile, setSelectedFile] = useState<string>(fileKeys[0] || '');
  const [copied, setCopied] = useState<boolean>(false);

  if (fileKeys.length === 0) {
    return (
      <div className="p-8 text-center border border-dashed border-arena-border rounded-xl text-slate-500 text-sm">
        No code files were generated for this run.
      </div>
    );
  }

  const activeContent = files[selectedFile] || '';

  const handleCopy = () => {
    navigator.clipboard.writeText(activeContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rounded-xl border border-arena-border bg-slate-950/90 overflow-hidden shadow-2xl">
      {/* File Tabs Header */}
      <div className="flex items-center justify-between border-b border-arena-border bg-slate-900/80 px-4 py-2">
        <div className="flex items-center space-x-1.5 overflow-x-auto">
          {fileKeys.map((filename) => (
            <button
              key={filename}
              onClick={() => setSelectedFile(filename)}
              className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-mono transition-all ${
                selectedFile === filename
                  ? 'bg-slate-800 text-indigo-400 font-semibold border border-slate-700'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/40'
              }`}
            >
              <FileCode className="w-3.5 h-3.5" />
              <span>{filename}</span>
            </button>
          ))}
        </div>
        <button
          onClick={handleCopy}
          className="flex items-center space-x-1.5 px-2.5 py-1 text-xs text-slate-400 hover:text-white bg-slate-800/50 hover:bg-slate-800 rounded-md transition-colors"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-emerald-400">Copied!</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>

      {/* Code body */}
      <div className="p-4 overflow-x-auto max-h-[480px]">
        <pre className="text-xs font-mono text-slate-200 leading-relaxed">
          <code>
            {activeContent.split('\n').map((line, idx) => (
              <div key={idx} className="flex">
                <span className="inline-block w-8 text-slate-600 select-none text-right pr-3 font-mono text-[11px]">
                  {idx + 1}
                </span>
                <span className="flex-1 whitespace-pre">{line}</span>
              </div>
            ))}
          </code>
        </pre>
      </div>
    </div>
  );
}

