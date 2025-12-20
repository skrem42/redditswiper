"use client";

import { useState, useEffect, useRef } from "react";
import { ChevronDown, Check, Filter, RotateCcw } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import type { Subreddit } from "@/lib/supabase";

interface SubredditSelectorProps {
  subreddits: Subreddit[];
  excludedSubreddits: Set<string>;
  onExclusionChange: (excluded: Set<string>) => void;
  pendingCounts?: Record<string, number>;
}

export function SubredditSelector({
  subreddits,
  excludedSubreddits,
  onExclusionChange,
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

  const toggleSubreddit = (subId: string) => {
    const newExcluded = new Set(excludedSubreddits);
    if (newExcluded.has(subId)) {
      newExcluded.delete(subId);
    } else {
      newExcluded.add(subId);
    }
    onExclusionChange(newExcluded);
  };

  const selectAll = () => {
    onExclusionChange(new Set());
  };

  const deselectAll = () => {
    onExclusionChange(new Set(subreddits.map(s => s.id)));
  };

  const activeCount = subreddits.length - excludedSubreddits.size;
  const totalPending = Object.entries(pendingCounts)
    .filter(([id]) => !excludedSubreddits.has(id))
    .reduce((sum, [, count]) => sum + count, 0);

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Trigger button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center gap-2 px-4 py-2.5 rounded-xl border transition-all ${
          excludedSubreddits.size > 0
            ? "bg-amber-500/10 border-amber-500/30 text-amber-400"
            : "bg-secondary border-border hover:border-primary/30"
        }`}
      >
        <Filter size={16} />
        <span className="font-medium">
          {excludedSubreddits.size > 0 
            ? `${activeCount}/${subreddits.length} subs` 
            : "All Subreddits"}
        </span>
        <ChevronDown
          size={16}
          className={`transition-transform ${isOpen ? "rotate-180" : ""}`}
        />
      </button>

      {/* Dropdown */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="absolute top-full left-0 mt-2 w-80 bg-card border border-border rounded-xl shadow-xl z-50 overflow-hidden"
          >
            {/* Header */}
            <div className="p-3 border-b border-border bg-secondary/30">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Filter Subreddits</span>
                <span className="text-xs text-muted-foreground">
                  {totalPending} pending in {activeCount} subs
                </span>
              </div>
              {/* Search input */}
              <input
                type="text"
                placeholder="Search subreddits..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full px-3 py-2 bg-secondary rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                autoFocus
              />
            </div>

            {/* Quick actions */}
            <div className="flex items-center gap-2 p-2 border-b border-border">
              <button
                onClick={selectAll}
                className="flex-1 px-3 py-1.5 text-xs font-medium rounded-lg bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 transition-colors"
              >
                Select All
              </button>
              <button
                onClick={deselectAll}
                className="flex-1 px-3 py-1.5 text-xs font-medium rounded-lg bg-destructive/20 text-destructive hover:bg-destructive/30 transition-colors"
              >
                Deselect All
              </button>
              {excludedSubreddits.size > 0 && (
                <button
                  onClick={selectAll}
                  className="p-1.5 rounded-lg bg-secondary hover:bg-secondary/80 transition-colors"
                  title="Reset filters"
                >
                  <RotateCcw size={14} />
                </button>
              )}
            </div>

            {/* Options list */}
            <div className="max-h-72 overflow-y-auto">
              {sortedSubreddits.map((sub) => {
                const count = pendingCounts[sub.id] || 0;
                const isExcluded = excludedSubreddits.has(sub.id);
                // Check if sub is being actively crawled (from getSubreddits query that includes processing subs)
                const isActive = (sub as any).status === "processing";
                
                return (
                  <button
                    key={sub.id}
                    onClick={() => toggleSubreddit(sub.id)}
                    className={`w-full px-3 py-2.5 text-left hover:bg-secondary/50 transition-colors flex items-center gap-3 ${
                      isExcluded ? "opacity-50" : ""
                    } ${isActive ? "bg-blue-500/10" : ""}`}
                  >
                    {/* Checkbox */}
                    <div className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-all flex-shrink-0 ${
                      isExcluded 
                        ? "border-muted-foreground/40 bg-transparent" 
                        : "border-emerald-500 bg-emerald-500"
                    }`}>
                      {!isExcluded && <Check size={12} className="text-white" strokeWidth={3} />}
                    </div>

                    {/* Subreddit info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className={`font-medium truncate ${isExcluded ? "line-through" : ""}`}>
                          r/{sub.name}
                        </span>
                        {isActive && (
                          <span className="flex items-center gap-1 px-1.5 py-0.5 bg-blue-500/20 text-blue-400 rounded text-[9px] font-medium">
                            <span className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-pulse" />
                            ACTIVE
                          </span>
                        )}
                      </div>
                      {sub.subscribers > 0 && (
                        <span className="text-[10px] text-muted-foreground">
                          {sub.subscribers.toLocaleString()} members
                        </span>
                      )}
                    </div>

                    {/* Pending count */}
                    {count > 0 && (
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium flex-shrink-0 ${
                        isExcluded 
                          ? "bg-muted/30 text-muted-foreground" 
                          : "bg-amber-500/20 text-amber-400"
                      }`}>
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

            {/* Footer hint */}
            <div className="p-2 border-t border-border bg-secondary/20 text-center">
              <span className="text-[10px] text-muted-foreground">
                Uncheck subs to hide their leads
              </span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

