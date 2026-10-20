import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { act, renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const svc = vi.hoisted(() => ({ fetchStudyQueue: vi.fn(), fetchStudyStats: vi.fn() }));
vi.mock("../src/services/flashcardService", async (orig) => ({ ...(await orig<object>()), ...svc }));
vi.mock("../src/hooks/useAuth", () => ({ useAuth: () => ({ user: { id: "u1" } }) }));

import { useStudyQueue } from "../src/hooks/flashcards/useStudyQueue";

const wrapper = ({ children }: { children: React.ReactNode }) => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
};

const card = (id: string) => ({ id, deck_id: "d", term: id, definition: id }) as any;
const stats = (total: number) => ({ total, new: total, due: 0, learning: 0, mastered: 0, weak: 0 });

beforeEach(() => {
  svc.fetchStudyQueue.mockReset();
  svc.fetchStudyStats.mockReset();
});

describe("useStudyQueue", () => {
  it("uses the server queue when the server knows the deck", async () => {
    svc.fetchStudyStats.mockResolvedValue({ ok: true, data: stats(3) });
    svc.fetchStudyQueue.mockResolvedValue({ ok: true, data: [card("s1"), card("s2")] });
    const { result } = renderHook(() => useStudyQueue("d", [card("local")], false), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.queue.map((c) => c.id)).toEqual(["s1", "s2"]);
    expect(result.current.isFallback).toBe(false);
    expect(result.current.stats?.total).toBe(3);
  });

  it("an empty server queue is NOT replaced by local cards when the deck has cards (nothing is due)", async () => {
    svc.fetchStudyStats.mockResolvedValue({ ok: true, data: stats(10) });
    svc.fetchStudyQueue.mockResolvedValue({ ok: true, data: [] });
    const { result } = renderHook(() => useStudyQueue("d", [card("local")], false), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.queue).toEqual([]);
    expect(result.current.isFallback).toBe(false);
  });

  it("falls back to local cards when the server has no such deck (LocalStorage-only decks)", async () => {
    svc.fetchStudyStats.mockResolvedValue({ ok: true, data: stats(0) });
    svc.fetchStudyQueue.mockResolvedValue({ ok: true, data: [] });
    const { result } = renderHook(() => useStudyQueue("d", [card("local")], false), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.queue.map((c) => c.id)).toEqual(["local"]);
    expect(result.current.isFallback).toBe(true);
  });

  it("falls back to local cards when the server errors", async () => {
    svc.fetchStudyStats.mockResolvedValue({ ok: false, error: { message: "down" } });
    svc.fetchStudyQueue.mockResolvedValue({ ok: false, error: { message: "down" } });
    const { result } = renderHook(() => useStudyQueue("d", [card("local")], false), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.isFallback).toBe(true);
    expect(result.current.queue).toHaveLength(1);
  });

  it("stays in the loading state while local cards are still loading in fallback mode", async () => {
    svc.fetchStudyStats.mockResolvedValue({ ok: true, data: stats(0) });
    svc.fetchStudyQueue.mockResolvedValue({ ok: true, data: [] });
    const { result } = renderHook(() => useStudyQueue("d", [], true), { wrapper });
    await waitFor(() => expect(svc.fetchStudyStats).toHaveBeenCalled());
    await act(async () => {});
    expect(result.current.isLoading).toBe(true);
  });

  it("does nothing without a deck id", () => {
    const { result } = renderHook(() => useStudyQueue(undefined, [], false), { wrapper });
    expect(svc.fetchStudyQueue).not.toHaveBeenCalled();
    expect(result.current.queue).toEqual([]);
  });

  it("loadWeak swaps the queue, refresh restores the server queue", async () => {
    svc.fetchStudyStats.mockResolvedValue({ ok: true, data: stats(5) });
    svc.fetchStudyQueue.mockImplementation(async (_id: string, opts?: { weakOnly?: boolean }) => ({
      ok: true, data: opts?.weakOnly ? [card("weak1")] : [card("due1"), card("due2")]
    }));
    const { result } = renderHook(() => useStudyQueue("d", [], false), { wrapper });
    await waitFor(() => expect(result.current.queue).toHaveLength(2));

    let found = 0;
    await act(async () => { found = await result.current.loadWeak(); });
    expect(found).toBe(1);
    expect(svc.fetchStudyQueue).toHaveBeenLastCalledWith("d", { weakOnly: true, newLimit: 0, limit: 100 });
    expect(result.current.queue.map((c) => c.id)).toEqual(["weak1"]);

    await act(async () => { await result.current.refresh(); });
    await waitFor(() => expect(result.current.queue.map((c) => c.id)).toEqual(["due1", "due2"]));
  });

  it("refreshStats refetches only the stats", async () => {
    svc.fetchStudyStats.mockResolvedValue({ ok: true, data: stats(5) });
    svc.fetchStudyQueue.mockResolvedValue({ ok: true, data: [card("a")] });
    const { result } = renderHook(() => useStudyQueue("d", [], false), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    const queueCalls = svc.fetchStudyQueue.mock.calls.length;
    await act(async () => { await result.current.refreshStats(); });
    expect(svc.fetchStudyStats).toHaveBeenCalledTimes(2);
    expect(svc.fetchStudyQueue.mock.calls.length).toBe(queueCalls);
  });
});
