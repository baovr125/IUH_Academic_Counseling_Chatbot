import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { StudyMode } from "../src/components/flashcards/StudyMode";
import type { BackendDeck, BackendCardItem } from "../src/services/flashcardService";

describe("Flashcard StudyMode Component", () => {
  const mockDeck: BackendDeck = {
    id: "deck-123",
    title: "Từ vựng Kỹ thuật Phần mềm",
    description: "Bộ thẻ chuyên ngành",
    lang_code: "en",
    langCode: "en",
    cardCount: 1,
    dueCount: 1,
  };

  const mockCard: BackendCardItem = {
    id: "card-1",
    deck_id: "deck-123",
    term: "Microservices",
    definition: "Kiến trúc phần mềm phân tán thành các dịch vụ độc lập",
    phonetic: "/ˈmaɪ.kroʊˌsɝː.vɪsɪz/",
    example_sentence: "Microservices architecture improves scalability.",
    recommended_mode: "flip",
  };

  const defaultProps = {
    deck: mockDeck,
    studyQueue: [mockCard],
    isLoading: false,
    onRateFSRS: vi.fn(),
    onVerifySpelling: vi.fn(),
    onPlayAudio: vi.fn(),
    onPrefetchAudio: vi.fn(),
    isPlayingAudio: false,
    onOpenAddCard: vi.fn(),
    onBackToDecks: vi.fn(),
  };

  it("renders front text and phonetic", () => {
    render(
      <MemoryRouter>
        <StudyMode {...defaultProps} />
      </MemoryRouter>
    );

    expect(screen.getByText("Microservices")).toBeInTheDocument();
    expect(screen.getByText("/ˈmaɪ.kroʊˌsɝː.vɪsɪz/")).toBeInTheDocument();
  });

  it("reveals definition when card is flipped", () => {
    render(
      <MemoryRouter>
        <StudyMode {...defaultProps} />
      </MemoryRouter>
    );

    const cardHint = screen.getByText(/Bấm vào thẻ/i);
    fireEvent.click(cardHint);

    expect(
      screen.getByText("Kiến trúc phần mềm phân tán thành các dịch vụ độc lập")
    ).toBeInTheDocument();
  });

  it("triggers onRateFSRS when rating button is clicked after flipping", () => {
    const onRateMock = vi.fn();
    render(
      <MemoryRouter>
        <StudyMode {...defaultProps} onRateFSRS={onRateMock} />
      </MemoryRouter>
    );

    const cardHint = screen.getByText(/Bấm vào thẻ/i);
    fireEvent.click(cardHint);

    const goodButton = screen.getByText(/\[3\] Tốt/i);
    fireEvent.click(goodButton);

    expect(onRateMock).toHaveBeenCalledWith("card-1", 3);
  });
});
