"use client";

import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

interface URLInputProps {
    onSubmit: (url: string) => void;
    loading: boolean;
}

export function URLInput({ onSubmit, loading }: URLInputProps) {
    const [url, setUrl] = useState("");

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (url.trim() && !loading) {
            onSubmit(url.trim());
        }
    };

    return (
        <form onSubmit={handleSubmit} className="w-full">
            <div className="flex gap-3 items-center">
                <div className="relative flex-1 group">
                    <Input
                        type="url"
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                        placeholder="Paste a YouTube recipe video URL..."
                        disabled={loading}
                        className="h-14 text-base bg-zinc-900/50 border-zinc-700/50 placeholder:text-zinc-500 focus-visible:ring-purple-500/50 focus-visible:border-purple-500/50 rounded-xl pr-4 pl-5 transition-all duration-200 group-hover:border-zinc-600"
                    />
                    <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-purple-500/5 to-pink-500/5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
                </div>
                <Button
                    type="submit"
                    disabled={!url.trim() || loading}
                    className="h-14 px-8 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white font-semibold shadow-lg shadow-purple-500/25 hover:shadow-purple-500/40 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {loading ? (
                        <div className="flex items-center gap-2">
                            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                            </svg>
                            Processing...
                        </div>
                    ) : (
                        <div className="flex items-center gap-2">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                                <path d="M12 5v14M5 12h14" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
                            </svg>
                            Extract & Cart
                        </div>
                    )}
                </Button>
            </div>
            <p className="text-xs text-zinc-500 mt-2 pl-2">
                Supports YouTube videos and Shorts • Ingredients auto-added to Swiggy Instamart
            </p>
        </form>
    );
}
