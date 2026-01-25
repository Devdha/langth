"use client";

import { MatchedWord } from "@/types/v2";

interface HighlightedTextProps {
  text: string;
  matchedWords: MatchedWord[];
  highlightClass?: string;
}

export default function HighlightedText({
  text,
  matchedWords,
  highlightClass = "bg-yellow-200 text-yellow-900 px-0.5 rounded font-bold"
}: HighlightedTextProps) {
  // If no matches, render plain text
  if (matchedWords.length === 0) {
    return <>{text}</>;
  }

  // Sort matched words by startIndex to process them in order
  const sortedMatches = [...matchedWords].sort((a, b) => a.startIndex - b.startIndex);

  // Build segments: [plain, highlighted, plain, highlighted, ...]
  const segments: Array<{ text: string; isHighlight: boolean }> = [];
  let lastIndex = 0;

  sortedMatches.forEach((match) => {
    // Handle potential overlap - if current match starts before lastIndex,
    // skip it (defensive programming)
    if (match.startIndex < lastIndex) {
      return;
    }

    // Add plain text before this match (if any)
    if (match.startIndex > lastIndex) {
      segments.push({
        text: text.slice(lastIndex, match.startIndex),
        isHighlight: false,
      });
    }

    // Add highlighted match
    segments.push({
      text: text.slice(match.startIndex, match.endIndex),
      isHighlight: true,
    });

    lastIndex = match.endIndex;
  });

  // Add remaining plain text after last match (if any)
  if (lastIndex < text.length) {
    segments.push({
      text: text.slice(lastIndex),
      isHighlight: false,
    });
  }

  return (
    <>
      {segments.map((segment, index) =>
        segment.isHighlight ? (
          <span key={index} className={highlightClass}>
            {segment.text}
          </span>
        ) : (
          <span key={index}>{segment.text}</span>
        )
      )}
    </>
  );
}
