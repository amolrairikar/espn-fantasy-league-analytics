import React, { useEffect, useState } from "react";
import { fetchHealthCheck } from "@/api/health/api_calls";

type Props = {
  children?: React.ReactNode;
};

export default function ApiErrorBanner({ children }: Props) {
  const [hasServerError, setHasServerError] = useState(false);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    let mounted = true;

    async function check() {
      try {
        await fetchHealthCheck();
      } catch (err) {
        if (mounted) setHasServerError(true);
      } finally {
        if (mounted) setChecking(false);
      }
    }

    check();
    return () => {
      mounted = false;
    };
  }, []);

  if (checking) return null;

  if (hasServerError) {
    return (
      <div className="min-h-screen flex flex-col">
        <div className="w-full text-center bg-destructive/10 dark:bg-destructive/20 text-destructive py-3 font-bold shadow-sm">
          500 Server Error
        </div>

        <div className="flex-1 flex items-center justify-center px-4">
          <div className="max-w-lg text-center">
            <h2 className="text-xl font-semibold mb-2 text-foreground">Server is currently unavailable.</h2>
            <p className="text-sm text-muted-foreground">Please try again later.</p>
          </div>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
