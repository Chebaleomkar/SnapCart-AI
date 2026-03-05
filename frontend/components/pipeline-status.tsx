"use client";

interface PipelineStatusProps {
    timing: Record<string, number>;
    currentStep: string;
    error?: string | null;
}

const STEPS = [
    { key: "url_parsing", label: "URL Parsing", icon: "🔗" },
    { key: "audio_extraction", label: "Audio Download", icon: "🎵" },
    { key: "transcription", label: "Transcription", icon: "📝" },
    { key: "ingredient_extraction", label: "Ingredient Extraction", icon: "🥕" },
    { key: "cart", label: "Cart Integration", icon: "🛒" },
];

export function PipelineStatus({ timing, currentStep, error }: PipelineStatusProps) {
    return (
        <div className="w-full space-y-3">
            <div className="flex items-center gap-2 text-sm text-zinc-400">
                <svg className="animate-spin h-3.5 w-3.5 text-purple-400" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Pipeline running...
            </div>

            <div className="grid gap-2">
                {STEPS.map((step) => {
                    const isCompleted = timing[step.key] !== undefined;
                    const isCurrent = currentStep === step.key;
                    const isPending = !isCompleted && !isCurrent;
                    const hasError = error && isCurrent;

                    return (
                        <div
                            key={step.key}
                            className={`flex items-center gap-3 px-4 py-2.5 rounded-lg border transition-all duration-300 ${hasError
                                    ? "bg-red-500/10 border-red-500/30 text-red-400"
                                    : isCompleted
                                        ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
                                        : isCurrent
                                            ? "bg-purple-500/10 border-purple-500/30 text-purple-300 animate-pulse"
                                            : "bg-zinc-900/30 border-zinc-800/50 text-zinc-600"
                                }`}
                        >
                            <span className="text-base">{step.icon}</span>
                            <span className="flex-1 text-sm font-medium">{step.label}</span>
                            {isCompleted && (
                                <span className="text-xs text-emerald-500 font-mono">
                                    {timing[step.key]}s ✓
                                </span>
                            )}
                            {isCurrent && !hasError && (
                                <span className="text-xs text-purple-400">
                                    Processing...
                                </span>
                            )}
                            {hasError && (
                                <span className="text-xs text-red-400">Failed</span>
                            )}
                            {isPending && (
                                <span className="text-xs text-zinc-600">Pending</span>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
