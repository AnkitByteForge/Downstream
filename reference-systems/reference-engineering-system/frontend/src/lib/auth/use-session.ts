"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { ApiError, authApi, type SessionOut } from "@/lib/api-client";

interface SessionState {
  session: SessionOut | null;
  loading: boolean;
}

/**
 * Resolves the current human session against the backend's own
 * /auth/session endpoint — the frontend never trusts a locally-cached
 * belief about being logged in, it asks the backend on every mount.
 * Redirects to /login on a 401, so every protected page can rely on this
 * hook alone for its auth gate.
 */
export function useRequireSession(): SessionState {
  const router = useRouter();
  const [state, setState] = useState<SessionState>({ session: null, loading: true });

  useEffect(() => {
    let cancelled = false;

    authApi
      .session()
      .then((session) => {
        if (!cancelled) setState({ session, loading: false });
      })
      .catch((err) => {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 401) {
          router.replace("/login");
          return;
        }
        setState({ session: null, loading: false });
      });

    return () => {
      cancelled = true;
    };
  }, [router]);

  return state;
}
