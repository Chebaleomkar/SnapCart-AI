"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { getAuthStatus, getAuthLoginUrl, logout } from "@/lib/api";

export function SwiggyAuth() {
    const [authenticated, setAuthenticated] = useState(false);
    const [loading, setLoading] = useState(true);

    const checkStatus = async () => {
        try {
            const status = await getAuthStatus();
            setAuthenticated(status.authenticated);
        } catch {
            setAuthenticated(false);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        checkStatus();

        // Listen for OAuth popup callback
        const handleMessage = (event: MessageEvent) => {
            if (event.data?.type === "SWIGGY_AUTH_SUCCESS") {
                setAuthenticated(true);
            }
        };
        window.addEventListener("message", handleMessage);
        return () => window.removeEventListener("message", handleMessage);
    }, []);

    const handleConnect = async () => {
        try {
            const { authorize_url } = await getAuthLoginUrl();
            // Open OAuth in popup
            window.open(authorize_url, "SwiggyAuth", "width=600,height=700,popup=true");
        } catch (err) {
            console.error("Auth failed:", err);
        }
    };

    const handleDisconnect = async () => {
        await logout();
        setAuthenticated(false);
    };

    if (loading) {
        return (
            <Badge variant="outline" className="animate-pulse">
                Checking...
            </Badge>
        );
    }

    if (authenticated) {
        return (
            <div className="flex items-center gap-2">
                <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30">
                    <span className="mr-1.5 inline-block h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                    Swiggy Connected
                </Badge>
                <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleDisconnect}
                    className="text-xs text-zinc-500 hover:text-zinc-300"
                >
                    Disconnect
                </Button>
            </div>
        );
    }

    return (
        <Button
            onClick={handleConnect}
            size="sm"
            className="bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white font-medium shadow-lg shadow-orange-500/20 transition-all duration-200"
        >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" className="mr-1.5">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            Connect Swiggy
        </Button>
    );
}
