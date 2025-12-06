'use client';

import { useState } from 'react';

export default function Home() {
  const [idea, setIdea] = useState('');
  const [workflowId, setWorkflowId] = useState<string | null>(null);
  const [status, setStatus] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const startGeneration = async () => {
    setLoading(true);
    setError(null);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(`${apiUrl}/api/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ idea }),
      });

      if (!res.ok) throw new Error('Failed to start generation');

      const data = await res.json();
      setWorkflowId(data.workflow_id);
      pollStatus(data.workflow_id);
    } catch (err: any) {
      setError(err.message);
      setLoading(false);
    }
  };

  const pollStatus = async (id: string) => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${apiUrl}/api/status/${id}`);
        const data = await res.json();
        setStatus(data);

        if (data.status === 'completed' && data.current_phase === 7) {
          clearInterval(interval);
          setLoading(false);
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 2000);
  };

  return (
    <main className="flex min-h-screen flex-col items-center p-24 bg-gray-50">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm lg:flex">
        <h1 className="text-4xl font-bold mb-8 text-blue-600">AI Manga Generator</h1>
      </div>

      <div className="w-full max-w-md space-y-4">
        <textarea
          className="w-full p-4 border rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500"
          rows={4}
          placeholder="Enter your manga idea here..."
          value={idea}
          onChange={(e) => setIdea(e.target.value)}
          disabled={loading}
        />

        <button
          className={`w-full py-3 px-6 rounded-lg text-white font-bold transition-colors ${loading ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'
            }`}
          onClick={startGeneration}
          disabled={loading || !idea}
        >
          {loading ? 'Generating...' : 'Start Generation'}
        </button>

        {error && (
          <div className="p-4 bg-red-100 text-red-700 rounded-lg">
            Error: {error}
          </div>
        )}

        {status && (
          <div className="mt-8 p-6 bg-white rounded-xl shadow-md w-full">
            <h2 className="text-xl font-bold mb-4">Status: {status.status}</h2>
            <div className="space-y-2">
              <p>Phase: {status.current_phase} / 7</p>
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div
                  className="bg-blue-600 h-2.5 rounded-full transition-all duration-500"
                  style={{ width: `${(status.current_phase / 7) * 100}%` }}
                ></div>
              </div>

              {status.history && (
                <div className="mt-4 text-xs text-gray-500 max-h-40 overflow-y-auto">
                  {status.history.map((h: any, i: number) => (
                    <div key={i} className="border-l-2 border-blue-300 pl-2 mb-1">
                      Phase {h.phase}: {h.status}
                    </div>
                  ))}
                </div>
              )}

              {status.current_phase === 7 && status.data?.pdf_url && (
                <div className="mt-6 text-center">
                  <a
                    href={`http://localhost:8000${status.data.pdf_url}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-block bg-green-600 text-white py-2 px-6 rounded-lg hover:bg-green-700 transition-colors"
                  >
                    Download Manga PDF
                  </a>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
