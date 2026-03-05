"use client";

import { useState } from "react";
import { URLInput } from "@/components/url-input";
import { SwiggyAuth } from "@/components/swiggy-auth";
import { PipelineStatus } from "@/components/pipeline-status";
import { ResultsDisplay } from "@/components/results-display";
import { processUrl, type PipelineResult } from "@/lib/api";

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PipelineResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState("");
  const [timing, setTiming] = useState<Record<string, number>>({});

  const handleSubmit = async (url: string) => {
    setLoading(true);
    setError(null);
    setResult(null);
    setTiming({});

    // Simulate step progress
    const steps = ["url_parsing", "audio_extraction", "transcription", "ingredient_extraction", "cart"];
    let stepIdx = 0;

    const interval = setInterval(() => {
      if (stepIdx < steps.length) {
        setCurrentStep(steps[stepIdx]);
        stepIdx++;
      }
    }, 2000);

    try {
      const data = await processUrl(url);
      clearInterval(interval);
      setTiming(data.timing);
      setCurrentStep("");

      if (data.error && !data.final_result) {
        setError(data.error);
      } else {
        setResult(data);
      }
    } catch (err) {
      clearInterval(interval);
      setCurrentStep("");
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      {/* Background gradient */}
      <div className="fixed inset-0 -z-10">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-gradient-to-b from-purple-500/8 via-transparent to-transparent rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-0 w-[400px] h-[400px] bg-gradient-to-t from-pink-500/5 to-transparent rounded-full blur-3xl" />
      </div>

      {/* Navbar */}
      <header className="sticky top-0 z-50 backdrop-blur-xl bg-zinc-950/80 border-b border-zinc-800/50">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-sm font-bold shadow-lg shadow-purple-500/20">
              S
            </div>
            <h1 className="text-lg font-bold tracking-tight">
              Snap<span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400">Cart</span>AI
            </h1>
          </div>
          <SwiggyAuth />
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-6 py-12">
        {/* Hero */}
        <div className="text-center mb-10 space-y-3">
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight">
            Recipe to Cart in{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-pink-400 to-orange-400">
              Seconds
            </span>
          </h2>
          <p className="text-zinc-400 text-base max-w-lg mx-auto">
            Paste a recipe video URL — we extract every ingredient and add them straight to your Swiggy Instamart cart.
          </p>
        </div>

        {/* URL Input */}
        <div className="mb-8">
          <URLInput onSubmit={handleSubmit} loading={loading} />
        </div>

        {/* Pipeline Progress */}
        {loading && (
          <div className="mb-8 animate-in fade-in slide-in-from-top-2 duration-300">
            <PipelineStatus timing={timing} currentStep={currentStep} error={error} />
          </div>
        )}

        {/* Error */}
        {error && !loading && (
          <div className="mb-8 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm animate-in fade-in duration-300">
            ⚠️ {error}
          </div>
        )}

        {/* Results */}
        {result && <ResultsDisplay result={result} />}

        {/* Empty State */}
        {!loading && !result && !error && (
          <div className="text-center py-16 space-y-6">
            <p className="text-sm text-zinc-600">
              Paste a recipe video URL — we extract every ingredient and add them straight to your Swiggy Instamart cart.
            </p>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-zinc-800/50 mt-16">
        <div className="max-w-4xl mx-auto px-6 py-6 text-center text-xs text-zinc-600">
          Built with Groq Whisper + LLM • Swiggy Instamart MCP • Next.js
        </div>
      </footer>
    </div>
  );
}
