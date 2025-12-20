"use client";

import { useState, useEffect, useRef } from "react";
import { ChevronDown, X, Layers } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import type { Subreddit } from "@/lib/supabase";

interface SubredditSelectorProps {
  subreddits: Subreddit[];
  selectedSubreddit: Subreddit | null;
  onSelect: (subreddit: Subreddit | null) => void;
  pendingCounts?: Record<string, number>;
}

export function SubredditSelector({
  subreddits,
  selectedSubreddit,
  onSelect,
  pendingCounts = {},
}: SubredditSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState("");
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Filter subreddits by search
  const filteredSubreddits = subreddits.filter((sub) =>
    sub.name.toLowerCase().includes(search.toLowerCase())
  );

  // Sort by pending count (highest first)
  const sortedSubreddits = [...filteredSubreddits].sort((a, b) => {
    const countA = pendingCounts[a.id] || 0;
    const countB = pendingCounts[b.id] || 0;
    return countB - countA;
  });

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Trigger button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center gap-2 px-4 py-2.5 rounded-xl border transition-all ${
          selectedSubreddit
            ? "bg-primary/10 border-primary/30 text-primary"
            : "bg-secondary border-border hover:border-primary/30"
        }`}
      >
        <Layers size={16} />
        <span className="font-medium">
          {selectedSubreddit ? `r/${selectedSubreddit.name}` : "All Subreddits"}
        </span>
        <ChevronDown
          size={16}
          className={`transition-transform ${isOpen ? "rotate-180" : ""}`}
        />
      </button>

      {/* Clear selection button */}
      {selectedSubreddit && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onSelect(null);
          }}
          className="absolute -right-2 -top-2 p-1 rounded-full bg-destructive text-white hover:bg-destructive/80 transition-colors"
        >
          <X size={12} />
        </button>
      )}

      {/* Dropdown */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="absolute top-full left-0 mt-2 w-72 bg-card border border-border rounded-xl shadow-xl z-50 overflow-hidden"
          >
            {/* Search input */}
            <div className="p-3 border-b border-border">
              <input
                type="text"
                placeholder="Search subreddits..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full px-3 py-2 bg-secondary rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                autoFocus
              />
            </div>

            {/* Options list */}
            <div className="max-h-64 overflow-y-auto">
              {/* All subreddits option */}
              <button
                onClick={() => {
                  onSelect(null);
                  setIsOpen(false);
                  setSearch("");
                }}
                className={`w-full px-4 py-3 text-left hover:bg-secondary/50 transition-colors flex items-center justify-between ${
                  !selectedSubreddit ? "bg-primary/10" : ""
                }`}
              >
                <span className="font-medium">All Subreddits</span>
                <span className="text-xs text-muted-foreground">
                  {Object.values(pendingCounts).reduce((a, b) => a + b, 0)} pending
                </span>
              </button>

              {/* Divider */}
              <div className="border-t border-border" />

              {/* Subreddit options */}
              {sortedSubreddits.map((sub) => {
                const count = pendingCounts[sub.id] || 0;
                return (
                  <button
                    key={sub.id}
                    onClick={() => {
                      onSelect(sub);
                      setIsOpen(false);
                      setSearch("");
                    }}
                    className={`w-full px-4 py-3 text-left hover:bg-secondary/50 transition-colors flex items-center justify-between ${
                      selectedSubreddit?.id === sub.id ? "bg-primary/10" : ""
                    }`}
                  >
                    <div>
                      <span className="font-medium">r/{sub.name}</span>
                      {sub.subscribers > 0 && (
                        <span className="text-xs text-muted-foreground ml-2">
                          {sub.subscribers.toLocaleString()} members
                        </span>
                      )}
                    </div>
                    {count > 0 && (
                      <span className="px-2 py-0.5 bg-amber-500/20 text-amber-400 rounded-full text-xs font-medium">
                        {count}
                      </span>
                    )}
                  </button>
                );
              })}

              {sortedSubreddits.length === 0 && (
                <div className="px-4 py-6 text-center text-muted-foreground text-sm">
                  No subreddits found
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

