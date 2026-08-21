import { useEffect, useState, useCallback } from "react";
import { useAuth } from "./useAuth";
import * as dashboardService from "../services/dashboardService";
import { getDecks } from "../services/deckStorage";
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

    let statsData = { ...result.data };

    // Dynamic enrichment from local decks if available
    try {
      const localDecks = getDecks(user?.id);
      if (localDecks && localDecks.length > 0) {
        let totalCards = 0;
        let dueCount = 0;
        localDecks.forEach((deck) => {
          if (deck.cards) {
            totalCards += deck.cards.length;
            // Estimate due count (e.g. cards needing review or not rated)
            dueCount += Math.min(deck.cards.length, Math.ceil(deck.cards.length * 0.4));
          }
        });

        if (totalCards > 0) {
          statsData.flashcardSummary = {
            ...statsData.flashcardSummary,
            totalCards: totalCards,
            dueTodayCount: Math.max(dueCount, 4),
            topDeckTitle: localDecks[0].title,
            topDeckId: localDecks[0].id,
          };
        }
      }
    } catch (e) {
      console.warn("Error enriching dashboard with local decks:", e);
    }

    setStats(statsData);
    setIsLoading(false);
  }, [user]);

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  return { stats, isLoading, error, refresh: loadStats };
}

