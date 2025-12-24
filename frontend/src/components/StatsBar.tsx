"use client";

import { Users, CheckCircle, XCircle, Clock, Star, MessageCircle } from "lucide-react";
import type { Stats } from "@/lib/supabase";

interface StatsBarProps {
  stats: Stats;
  currentFilter: string;
  onFilterChange: (filter: string) => void;
}

export function StatsBar({ stats, currentFilter, onFilterChange }: StatsBarProps) {
  const filters = [
    {
      id: "pending",
      label: "Pending",
      shortLabel: "Pend",
      count: stats.pending_leads,
      icon: Clock,
      color: "text-yellow-500",
      bgColor: "bg-yellow-500/10",
      borderColor: "border-yellow-500/30",
    },
    {
      id: "superliked",
      label: "Super",
      shortLabel: "⭐",
      count: stats.superliked_leads,
      icon: Star,
      color: "text-amber-500",
      bgColor: "bg-amber-500/10",
      borderColor: "border-amber-500/30",
    },
    {
      id: "approved",
      label: "Approved",
      shortLabel: "Yes",
      count: stats.approved_leads,
      icon: CheckCircle,
      color: "text-success",
      bgColor: "bg-success/10",
      borderColor: "border-success/30",
    },
    {
      id: "contacted",
      label: "Contacted",
      shortLabel: "DM'd",
      count: stats.contacted_leads,
      icon: MessageCircle,
      color: "text-blue-500",
      bgColor: "bg-blue-500/10",
      borderColor: "border-blue-500/30",
    },
    {
      id: "rejected",
      label: "Rejected",
      shortLabel: "No",
      count: stats.rejected_leads,
      icon: XCircle,
      color: "text-destructive",
      bgColor: "bg-destructive/10",
      borderColor: "border-destructive/30",
    },
  ];

  return (
    <div className="glass rounded-xl md:rounded-2xl p-2 md:p-4 mb-3 md:mb-6">
      {/* Header - condensed on mobile */}
      <div className="flex items-center justify-between mb-2 md:mb-4">
        <div className="flex items-center gap-1.5 md:gap-2">
          <Users className="text-primary w-4 h-4 md:w-5 md:h-5" />
          <span className="text-sm md:text-lg font-semibold">
            {stats.total_leads.toLocaleString()} <span className="hidden sm:inline">Total </span>Leads
          </span>
        </div>
        <div className="hidden md:block text-sm text-muted-foreground">
          {stats.total_posts.toLocaleString()} posts from{" "}
          {stats.total_subreddits} subreddits
        </div>
      </div>

      {/* Filter buttons - horizontal scroll on mobile */}
      <div className="flex gap-1.5 md:gap-2 overflow-x-auto pb-1 -mx-2 px-2 md:mx-0 md:px-0 md:flex-wrap">
        {filters.map((filter) => (
          <button
            key={filter.id}
            onClick={() => onFilterChange(filter.id)}
            className={`flex-shrink-0 flex items-center justify-center gap-1 md:gap-1.5 px-2 md:px-3 py-1.5 md:py-2 rounded-lg md:rounded-xl border transition-all whitespace-nowrap ${
              currentFilter === filter.id
                ? `${filter.bgColor} ${filter.borderColor} ${filter.color}`
                : "bg-secondary/50 border-border text-muted-foreground hover:bg-secondary"
            }`}
          >
            <filter.icon size={14} className="md:w-4 md:h-4" />
            <span className="font-medium text-xs md:text-sm hidden sm:inline">{filter.label}</span>
            <span className="font-medium text-xs sm:hidden">{filter.shortLabel}</span>
            <span
              className={`px-1 md:px-1.5 py-0.5 rounded-full text-[10px] md:text-xs font-bold ${
                currentFilter === filter.id
                  ? `${filter.bgColor} ${filter.color}`
                  : "bg-muted text-muted-foreground"
              }`}
            >
              {filter.count}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
