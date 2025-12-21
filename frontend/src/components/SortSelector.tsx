"use client";

import { useState, useEffect, useRef } from "react";
import { ChevronDown, ArrowUpDown } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export type SortOption = "avg_upvotes" | "total_karma" | "posts_per_day";

interface SortSelectorProps {
  currentSort: SortOption;
  onSortChange: (sort: SortOption) => void;
}

const SORT_OPTIONS: { value: SortOption; label: string; description: string }[] = [
  { 
    value: "avg_upvotes", 
    label: "Avg Upvotes", 
    description: "Sort by average upvotes per post" 
  },
  { 
    value: "total_karma", 
    label: "Total Karma", 
    description: "Sort by total account karma" 
  },
  { 
    value: "posts_per_day", 
    label: "Posts/Day", 
    description: "Sort by posting frequency" 
  },
];

export function SortSelector({ currentSort, onSortChange }: SortSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
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

  const currentOption = SORT_OPTIONS.find(opt => opt.value === currentSort) || SORT_OPTIONS[0];

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Trigger button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-4 py-2.5 rounded-xl border bg-secondary border-border hover:border-primary/30 transition-all"
      >
        <ArrowUpDown size={16} />
        <span className="font-medium">{currentOption.label}</span>
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
            className="absolute top-full right-0 mt-2 w-56 bg-card border border-border rounded-xl shadow-xl z-50 overflow-hidden"
          >
            {/* Header */}
            <div className="p-3 border-b border-border bg-secondary/30">
              <span className="text-sm font-medium">Sort Leads By</span>
            </div>

            {/* Options list */}
            <div>
              {SORT_OPTIONS.map((option) => {
                const isSelected = currentSort === option.value;
                
                return (
                  <button
                    key={option.value}
                    onClick={() => {
                      onSortChange(option.value);
                      setIsOpen(false);
                    }}
                    className={`w-full px-4 py-3 text-left hover:bg-secondary/50 transition-colors ${
                      isSelected ? "bg-primary/10" : ""
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className={`font-medium ${isSelected ? "text-primary" : ""}`}>
                          {option.label}
                        </div>
                        <div className="text-xs text-muted-foreground mt-0.5">
                          {option.description}
                        </div>
                      </div>
                      {isSelected && (
                        <div className="w-2 h-2 rounded-full bg-primary ml-2" />
                      )}
                    </div>
                  </button>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

