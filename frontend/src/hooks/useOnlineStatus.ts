import { useState, useEffect } from "react";
import { drainQueue } from "../offline/queue";

export function useOnlineStatus(): boolean {
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    // Drain on mount in case items were queued during a previous offline session
    if (navigator.onLine) {
      void drainQueue();
    }

    const handleOnline = () => {
      setIsOnline(true);
      void drainQueue();
    };
    const handleOffline = () => setIsOnline(false);

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  return isOnline;
}
