import { useEffect, useState } from 'react';

import type { SessionResponse } from '../types/load';

const SESSION_STORAGE_KEY = 'eit-dash-web-session-id';

export function useSession() {
  const [session, setSession] = useState<SessionResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const bootstrapSession = async () => {
      setIsLoading(true);
      setError(null);

      const storedId = window.localStorage.getItem(SESSION_STORAGE_KEY);
      if (storedId) {
        const response = await fetch(`/api/sessions/${storedId}`);
        if (response.ok) {
          const existingSession = (await response.json()) as SessionResponse;
          setSession(existingSession);
          setIsLoading(false);
          return;
        }
      }

      const response = await fetch('/api/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ label: 'Web load flow' }),
      });

      if (!response.ok) {
        throw new Error(`Session bootstrap failed with ${response.status}`);
      }

      const createdSession = (await response.json()) as SessionResponse;
      window.localStorage.setItem(SESSION_STORAGE_KEY, createdSession.session_id);
      setSession(createdSession);
      setIsLoading(false);
    };

    bootstrapSession().catch((caughtError: unknown) => {
      const message = caughtError instanceof Error ? caughtError.message : 'Unknown session bootstrap error.';
      setError(message);
      setIsLoading(false);
    });
  }, []);

  return { session, isLoading, error };
}
