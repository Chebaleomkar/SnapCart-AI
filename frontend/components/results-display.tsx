"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import type { PipelineResult } from "@/lib/api";

interface ResultsDisplayProps {
    result: PipelineResult;
}

export function ResultsDisplay({ result }: ResultsDisplayProps) {
    const final = result.final_result;
    if (!final) return null;

    const cartSummary = final.cart_summary;

    return (
        <div className="w-full space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Dish Info */}
            <Card className="bg-zinc-900/60 border-zinc-800/50 backdrop-blur-sm">
                <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                        <div>
                            <CardTitle className="text-xl text-white">
                                {final.dish_name || "Recipe"}
                            </CardTitle>
                            <div className="flex items-center gap-2 mt-2">
                                {final.cuisine && (
                                    <Badge variant="secondary" className="bg-purple-500/15 text-purple-300 border-purple-500/30">
                                        {final.cuisine}
                                    </Badge>
                                )}
                                {final.servings && (
                                    <Badge variant="secondary" className="bg-zinc-700/50 text-zinc-300">
                                        🍽️ {final.servings}
                                    </Badge>
                                )}
                            </div>
                        </div>
                        <div className="text-right text-xs text-zinc-500 font-mono">
                            {result.timing.total}s total
                        </div>
                    </div>
                </CardHeader>
                {final.notes && (
                    <CardContent className="pt-0">
                        <p className="text-sm text-zinc-400 italic">💡 {final.notes}</p>
                    </CardContent>
                )}
            </Card>

            {/* Cart Summary */}
            {cartSummary && (
                <Card className="bg-zinc-900/60 border-zinc-800/50 backdrop-blur-sm">
                    <CardHeader className="pb-3">
                        <CardTitle className="text-lg text-white flex items-center gap-2">
                            🛒 Cart Summary
                            {cartSummary.mcp_connected ? (
                                <Badge className="bg-emerald-500/15 text-emerald-400 border-emerald-500/30 text-xs">
                                    MCP Connected
                                </Badge>
                            ) : (
                                <Badge className="bg-orange-500/15 text-orange-400 border-orange-500/30 text-xs">
                                    Fallback Mode
                                </Badge>
                            )}
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-1 pt-0">
                        <div className="grid grid-cols-3 gap-4 text-center">
                            <div className="p-3 rounded-lg bg-zinc-800/50">
                                <div className="text-2xl font-bold text-white">{cartSummary.total}</div>
                                <div className="text-xs text-zinc-500">Total Items</div>
                            </div>
                            <div className="p-3 rounded-lg bg-emerald-500/10">
                                <div className="text-2xl font-bold text-emerald-400">{cartSummary.added_to_cart}</div>
                                <div className="text-xs text-zinc-500">Added to Cart</div>
                            </div>
                            <div className="p-3 rounded-lg bg-orange-500/10">
                                <div className="text-2xl font-bold text-orange-400">{cartSummary.fallback_urls}</div>
                                <div className="text-xs text-zinc-500">Search Links</div>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Ingredients List */}
            <Card className="bg-zinc-900/60 border-zinc-800/50 backdrop-blur-sm">
                <CardHeader className="pb-3">
                    <CardTitle className="text-lg text-white">
                        🥕 Ingredients ({final.ingredients.length})
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 pt-0">
                    {final.ingredients.map((ing, idx) => {
                        const cartItem = final.cart_items?.[idx];
                        return (
                            <div
                                key={idx}
                                className="flex items-center justify-between p-3 rounded-lg bg-zinc-800/30 hover:bg-zinc-800/50 transition-colors group"
                            >
                                <div className="flex items-center gap-3">
                                    <span className="text-sm font-medium text-white">{ing.name}</span>
                                    {ing.quantity && ing.quantity !== "Not specified" && (
                                        <span className="text-xs text-zinc-500">{ing.quantity}</span>
                                    )}
                                    <Badge variant="outline" className="text-[10px] px-1.5 py-0 border-zinc-700 text-zinc-500">
                                        {ing.category}
                                    </Badge>
                                </div>
                                <div className="flex items-center gap-2">
                                    {cartItem?.cart_status === "added" ? (
                                        <Badge className="bg-emerald-500/20 text-emerald-400 text-xs">✓ In Cart</Badge>
                                    ) : cartItem?.search_url ? (
                                        <a
                                            href={cartItem.search_url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="opacity-0 group-hover:opacity-100 transition-opacity"
                                        >
                                            <Button variant="ghost" size="sm" className="text-xs text-orange-400 hover:text-orange-300 h-7">
                                                Search on Swiggy →
                                            </Button>
                                        </a>
                                    ) : null}
                                </div>
                            </div>
                        );
                    })}

                    <Separator className="bg-zinc-800 my-3" />

                    {cartSummary && (
                        <a
                            href={cartSummary.combined_search_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="block"
                        >
                            <Button
                                variant="outline"
                                className="w-full border-orange-500/30 text-orange-400 hover:bg-orange-500/10 hover:text-orange-300"
                            >
                                🛍️ Search All on Swiggy Instamart
                            </Button>
                        </a>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
