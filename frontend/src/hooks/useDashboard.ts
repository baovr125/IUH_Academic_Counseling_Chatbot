import { useEffect, useState, useCallback } from "react";
import { useAuth } from "./useAuth";
import * as dashboardService from "../services/dashboardService";
import type { DashboardStats } from "../types";

export function useDashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadStats = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    const result = await dashboardService.fetchDashboardStats(user);
    if (!result.ok) {
      setError(result.error.message);
      setIsLoading(false);
      return;
    }

    setStats(result.data);
    setIsLoading(false);
  }, [user]);

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  return { stats, isLoading, error, refresh: loadStats };
}

