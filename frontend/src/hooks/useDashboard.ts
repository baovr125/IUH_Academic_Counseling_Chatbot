import { useEffect, useState } from "react";
import * as dashboardService from "../services/dashboardService";
import type { DashboardStats } from "../types";

export function useDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      setIsLoading(true);
      const result = await dashboardService.fetchDashboardStats();
      setIsLoading(false);
      if (!result.ok) {
        setError(result.error.message);
        return;
      }
      setStats(result.data);
    })();
  }, []);

  return { stats, isLoading, error };
}
