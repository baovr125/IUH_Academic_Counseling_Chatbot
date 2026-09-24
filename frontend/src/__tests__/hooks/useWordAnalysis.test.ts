import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useWordAnalysis } from '../../hooks/useWordAnalysis';
import * as translationService from '../../services/translationService';

// Mock translationService
vi.mock('../../services/translationService', () => ({
  analyzeWord: vi.fn(),
}));

describe('useWordAnalysis hook', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should initialize with default state', () => {
    const { result } = renderHook(() => useWordAnalysis());
    expect(result.current.isLoading).toBe(false);
    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it('should call analyzeWord and update state successfully', async () => {
    const mockData = {
      lemma: 'test',
      pos: 'Noun',
      source_lang: 'en',
      context_match: { meaning: 'A trial', examples: [] },
      other_meanings: []
    };
    
    vi.mocked(translationService.analyzeWord).mockResolvedValueOnce({ ok: true, data: mockData } as any);

    const { result } = renderHook(() => useWordAnalysis());

    act(() => {
      result.current.analyze('This is a test', 'test', 'en', 'vi');
    });

    act(() => {
      vi.advanceTimersByTime(500);
    });

    expect(result.current.isLoading).toBe(true);
    expect(result.current.error).toBeNull();

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    expect(translationService.analyzeWord).toHaveBeenCalledTimes(1);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.data).toEqual(mockData);
  });

  it('should abort previous request when a new one is made (Race Condition)', async () => {
    // Simulate slow network for the first request
    const promise1 = new Promise((resolve) => setTimeout(() => resolve({ lemma: 'first' }), 1000));
    // Simulate fast network for the second request
    const promise2 = Promise.resolve({ lemma: 'second' });

    vi.mocked(translationService.analyzeWord)
      .mockImplementationOnce(() => promise1.then(data => ({ ok: true, data })) as any)
      .mockImplementationOnce(() => promise2.then(data => ({ ok: true, data })) as any);

    const { result } = renderHook(() => useWordAnalysis());

    act(() => {
      // First click
      result.current.analyze('First test', 'first', 'en', 'vi');
    });
    
    act(() => {
      // Advance timer for first click debounce
      vi.advanceTimersByTime(500); 
    });

    act(() => {
      // Second click immediately after
      result.current.analyze('Second test', 'second', 'en', 'vi');
    });

    act(() => {
      // Advance timer for second click debounce
      vi.advanceTimersByTime(500); 
    });

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    // Both should be called
    expect(translationService.analyzeWord).toHaveBeenCalledTimes(2);
    // But the final state should be the second request's result
    expect(result.current.data).toEqual({ lemma: 'second' });
    // And AbortController should have been passed to the first
    const firstCallArgs = vi.mocked(translationService.analyzeWord).mock.calls[0];
    const secondCallArgs = vi.mocked(translationService.analyzeWord).mock.calls[1];
    expect(firstCallArgs[1]).toBeInstanceOf(AbortSignal); // options.signal
    expect(secondCallArgs[1]).toBeInstanceOf(AbortSignal);
  });

  it('should handle errors gracefully', async () => {
    vi.mocked(translationService.analyzeWord).mockRejectedValueOnce(new Error('Network Error'));

    const { result } = renderHook(() => useWordAnalysis());

    act(() => {
      result.current.analyze('Test', 'test', 'en', 'vi');
    });

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBe('Network error');
    expect(result.current.data).toBeNull();
  });
});
