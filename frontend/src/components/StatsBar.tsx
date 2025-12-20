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
      count: stats.pending_leads,
      icon: Clock,
      color: "text-yellow-500",
      bgColor: "bg-yellow-500/10",
      borderColor: "border-yellow-500/30",
    },
    {
      id: "superliked",
      label: "Super",
      count: stats.superliked_leads,
      icon: Star,
      color: "text-amber-500",
      bgColor: "bg-amber-500/10",
      borderColor: "border-amber-500/30",
    },
    {
      id: "approved",
      label: "Approved",
      count: stats.approved_leads,
      icon: CheckCircle,
      color: "text-success",
      bgColor: "bg-success/10",
      borderColor: "border-success/30",
    },
    {
      id: "contacted",
      label: "Contacted",
      count: stats.contacted_leads,
      icon: MessageCircle,
      color: "text-blue-500",
      bgColor: "bg-blue-500/10",
      borderColor: "border-blue-500/30",
    },
    {
      id: "rejected",
      label: "Rejected",
      count: stats.rejected_leads,
      icon: XCircle,
      color: "text-destructive",
      bgColor: "bg-destructive/10",
      borderColor: "border-destructive/30",
    },
  ];

  return (
    <div className="glass rounded-2xl p-4 mb-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Users className="text-primary" size={20} />
          <span className="text-lg font-semibold">
            {stats.total_leads.toLocaleString()} Total Leads
          </span>
        </div>
        <div className="text-sm text-muted-foreground">
          {stats.total_posts.toLocaleString()} posts from{" "}
          {stats.total_subreddits} subreddits
        </div>
      </div>

      <div className="flex gap-3">
        {filters.map((filter) => (
          <button
            key={filter.id}
            onClick={() => onFilterChange(filter.id)}
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl border transition-all ${
              currentFilter === filter.id
                ? `${filter.bgColor} ${filter.borderColor} ${filter.color}`
                : "bg-secondary/50 border-border text-muted-foreground hover:bg-secondary"
            }`}
          >
            <filter.icon size={18} />
            <span className="font-medium">{filter.label}</span>
            <span
              className={`px-2 py-0.5 rounded-full text-xs font-bold ${
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


