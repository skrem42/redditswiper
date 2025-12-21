"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search,
  ExternalLink,
  TrendingUp,
  TrendingDown,
  Users,
  MessageSquare,
  ChevronUp,
  ChevronDown,
  Filter,
  X,
  BarChart3,
  Eye,
  RefreshCw,
} from "lucide-react";
import {
  getSubredditIntel,
  getSubredditIntelStats,
  type SubredditIntel,
  type SubredditIntelFilters,
} from "@/lib/supabase";

type SortField = "subscribers" | "weekly_visitors" | "weekly_contributions" | "competition_score";

function formatNumber(num: number | null | undefined): string {
  if (num === null || num === undefined) return "—";
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
  return num.toLocaleString();
}

function getCompetitionColor(score: number | null): string {
  if (score === null) return "text-muted-foreground";
  if (score < 0.005) return "text-emerald-400"; // Very low competition
  if (score < 0.01) return "text-green-400"; // Low competition
  if (score < 0.03) return "text-yellow-400"; // Moderate
  if (score < 0.05) return "text-orange-400"; // High
  return "text-red-400"; // Very high
}

function getCompetitionLabel(score: number | null): string {
  if (score === null) return "Unknown";
  if (score < 0.005) return "Very Low";
  if (score < 0.01) return "Low";
  if (score < 0.03) return "Moderate";
  if (score < 0.05) return "High";
  return "Very High";
}

interface SubredditRowProps {
  subreddit: SubredditIntel;
  index: number;
}

function SubredditRow({ subreddit, index }: SubredditRowProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.02 }}
      className="group"
    >
      <div
        onClick={() => setIsExpanded(!isExpanded)}
        className="grid grid-cols-12 gap-4 items-center px-4 py-3 hover:bg-white/5 cursor-pointer transition-colors rounded-lg"
      >
        {/* Subreddit Name */}
        <div className="col-span-4 flex items-center gap-3">
          {subreddit.community_icon_url ? (
            <img
              src={subreddit.community_icon_url}
              alt=""
              className="w-8 h-8 rounded-full object-cover"
            />
          ) : (
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-orange-500 to-red-600 flex items-center justify-center text-white text-xs font-bold">
              {subreddit.subreddit_name.charAt(0).toUpperCase()}
            </div>
          )}
          <div className="min-w-0">
            <a
              href={`https://reddit.com/r/${subreddit.subreddit_name}`}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="font-medium text-foreground hover:text-primary transition-colors flex items-center gap-1 group/link"
            >
              r/{subreddit.subreddit_name}
              <ExternalLink
                size={12}
                className="opacity-0 group-hover/link:opacity-100 transition-opacity"
              />
            </a>
            <p className="text-xs text-muted-foreground truncate max-w-[200px]">
              {subreddit.description || "No description"}
            </p>
          </div>
        </div>

        {/* Subscribers */}
        <div className="col-span-2 text-center">
          <div className="flex items-center justify-center gap-1.5">
            <Users size={14} className="text-muted-foreground" />
            <span className="font-medium">{formatNumber(subreddit.subscribers)}</span>
          </div>
        </div>

        {/* Weekly Visitors */}
        <div className="col-span-2 text-center">
          <div className="flex items-center justify-center gap-1.5">
            <Eye size={14} className="text-blue-400" />
            <span className="font-medium text-blue-400">
              {formatNumber(subreddit.weekly_visitors)}
            </span>
          </div>
        </div>

        {/* Weekly Contributions */}
        <div className="col-span-2 text-center">
          <div className="flex items-center justify-center gap-1.5">
            <MessageSquare size={14} className="text-purple-400" />
            <span className="font-medium text-purple-400">
              {formatNumber(subreddit.weekly_contributions)}
            </span>
          </div>
        </div>

        {/* Competition Score */}
        <div className="col-span-2 text-center">
          <div className="flex flex-col items-center">
            <span className={`font-bold ${getCompetitionColor(subreddit.competition_score)}`}>
              {subreddit.competition_score !== null
                ? (subreddit.competition_score * 100).toFixed(2) + "%"
                : "—"}
            </span>
            <span className={`text-xs ${getCompetitionColor(subreddit.competition_score)}`}>
              {getCompetitionLabel(subreddit.competition_score)}
            </span>
          </div>
        </div>
      </div>

      {/* Expanded details */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-4 py-4 bg-white/5 rounded-lg mx-2 mb-2 grid grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Rules:</span>
                <span className="ml-2 font-medium">{subreddit.rules_count}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Moderators:</span>
                <span className="ml-2 font-medium">{subreddit.moderator_count}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Last Scraped:</span>
                <span className="ml-2 font-medium">
                  {subreddit.last_scraped_at
                    ? new Date(subreddit.last_scraped_at).toLocaleDateString()
                    : "Never"}
                </span>
              </div>
              <div className="col-span-3">
                <span className="text-muted-foreground">Media Allowed:</span>
                <span className="ml-2 space-x-2">
                  {subreddit.allows_images && (
                    <span className="inline-block px-2 py-0.5 bg-green-500/20 text-green-400 rounded text-xs">
                      Images
                    </span>
                  )}
                  {subreddit.allows_videos && (
                    <span className="inline-block px-2 py-0.5 bg-blue-500/20 text-blue-400 rounded text-xs">
                      Videos
                    </span>
                  )}
                  {subreddit.allows_polls && (
                    <span className="inline-block px-2 py-0.5 bg-purple-500/20 text-purple-400 rounded text-xs">
                      Polls
                    </span>
                  )}
                </span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export function SubredditExplorer() {
  const [subreddits, setSubreddits] = useState<SubredditIntel[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showFilters, setShowFilters] = useState(false);
  const [stats, setStats] = useState({
    total: 0,
    completed: 0,
    pending: 0,
    failed: 0,
    avgCompetitionScore: null as number | null,
  });

  // Filters
  const [search, setSearch] = useState("");
  const [minSubscribers, setMinSubscribers] = useState<string>("");
  const [maxCompetition, setMaxCompetition] = useState<string>("");
  const [sortBy, setSortBy] = useState<SortField>("weekly_visitors");
  const [sortDesc, setSortDesc] = useState(true);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    try {
      const filters: SubredditIntelFilters = {
        sortBy,
        sortDesc,
      };

      if (search) filters.search = search;
      if (minSubscribers) filters.minSubscribers = parseInt(minSubscribers);
      if (maxCompetition) filters.maxCompetitionScore = parseFloat(maxCompetition) / 100;

      const [data, statsData] = await Promise.all([
        getSubredditIntel(200, 0, filters),
        getSubredditIntelStats(),
      ]);

      setSubreddits(data);
      setStats(statsData);
    } catch (error) {
      console.error("Error fetching subreddit intel:", error);
    } finally {
      setIsLoading(false);
    }
  }, [search, minSubscribers, maxCompetition, sortBy, sortDesc]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Debounced search
  const [debouncedSearch, setDebouncedSearch] = useState(search);
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search), 300);
    return () => clearTimeout(timer);
  }, [search]);

  useEffect(() => {
    if (debouncedSearch !== search) return;
    fetchData();
  }, [debouncedSearch]);

  const handleSort = (field: SortField) => {
    if (sortBy === field) {
      setSortDesc(!sortDesc);
    } else {
      setSortBy(field);
      setSortDesc(true);
    }
  };

  const SortHeader = ({ field, label }: { field: SortField; label: string }) => (
    <button
      onClick={() => handleSort(field)}
      className="flex items-center justify-center gap-1 hover:text-primary transition-colors w-full"
    >
      <span>{label}</span>
      {sortBy === field && (
        sortDesc ? <ChevronDown size={14} /> : <ChevronUp size={14} />
      )}
    </button>
  );

  const clearFilters = () => {
    setSearch("");
    setMinSubscribers("");
    setMaxCompetition("");
  };

  const hasActiveFilters = search || minSubscribers || maxCompetition;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <BarChart3 className="text-primary" />
            Subreddit Intelligence
          </h2>
          <p className="text-muted-foreground mt-1">
            Analyze NSFW subreddits by engagement and competition
          </p>
        </div>
        <button
          onClick={fetchData}
          disabled={isLoading}
          className="p-3 rounded-xl bg-secondary hover:bg-secondary/80 transition-all disabled:opacity-50"
        >
          <RefreshCw size={20} className={isLoading ? "animate-spin" : ""} />
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-card rounded-xl p-4 border border-border">
          <div className="text-2xl font-bold text-primary">{stats.completed}</div>
          <div className="text-sm text-muted-foreground">Analyzed Subreddits</div>
        </div>
        <div className="bg-card rounded-xl p-4 border border-border">
          <div className="text-2xl font-bold text-yellow-400">{stats.pending}</div>
          <div className="text-sm text-muted-foreground">Pending Analysis</div>
        </div>
        <div className="bg-card rounded-xl p-4 border border-border">
          <div className="text-2xl font-bold text-red-400">{stats.failed}</div>
          <div className="text-sm text-muted-foreground">Failed</div>
        </div>
        <div className="bg-card rounded-xl p-4 border border-border">
          <div className={`text-2xl font-bold ${getCompetitionColor(stats.avgCompetitionScore)}`}>
            {stats.avgCompetitionScore !== null
              ? (stats.avgCompetitionScore * 100).toFixed(2) + "%"
              : "—"}
          </div>
          <div className="text-sm text-muted-foreground">Avg Competition</div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="flex items-center gap-4">
        {/* Search */}
        <div className="relative flex-1">
          <Search
            size={18}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"
          />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search subreddits..."
            className="w-full pl-10 pr-4 py-2.5 bg-secondary rounded-xl border border-border focus:border-primary focus:outline-none transition-colors"
          />
        </div>

        {/* Filter Toggle */}
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl border transition-colors ${
            showFilters || hasActiveFilters
              ? "bg-primary/20 border-primary text-primary"
              : "bg-secondary border-border hover:border-primary/50"
          }`}
        >
          <Filter size={18} />
          <span>Filters</span>
          {hasActiveFilters && (
            <span className="w-2 h-2 rounded-full bg-primary" />
          )}
        </button>

        {hasActiveFilters && (
          <button
            onClick={clearFilters}
            className="flex items-center gap-1 px-3 py-2.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <X size={14} />
            Clear
          </button>
        )}
      </div>

      {/* Filter Panel */}
      <AnimatePresence>
        {showFilters && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="bg-card rounded-xl p-4 border border-border grid grid-cols-3 gap-4">
              <div>
                <label className="text-sm text-muted-foreground mb-1 block">
                  Min Subscribers
                </label>
                <input
                  type="number"
                  value={minSubscribers}
                  onChange={(e) => setMinSubscribers(e.target.value)}
                  placeholder="e.g. 10000"
                  className="w-full px-3 py-2 bg-secondary rounded-lg border border-border focus:border-primary focus:outline-none"
                />
              </div>
              <div>
                <label className="text-sm text-muted-foreground mb-1 block">
                  Max Competition (%)
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={maxCompetition}
                  onChange={(e) => setMaxCompetition(e.target.value)}
                  placeholder="e.g. 1.0"
                  className="w-full px-3 py-2 bg-secondary rounded-lg border border-border focus:border-primary focus:outline-none"
                />
              </div>
              <div className="flex items-end">
                <button
                  onClick={fetchData}
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
                >
                  Apply Filters
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Results Table */}
      <div className="bg-card rounded-2xl border border-border overflow-hidden">
        {/* Table Header */}
        <div className="grid grid-cols-12 gap-4 items-center px-4 py-3 bg-secondary/50 border-b border-border text-sm font-medium text-muted-foreground">
          <div className="col-span-4">Subreddit</div>
          <div className="col-span-2 text-center">
            <SortHeader field="subscribers" label="Subscribers" />
          </div>
          <div className="col-span-2 text-center">
            <SortHeader field="weekly_visitors" label="Weekly Visitors" />
          </div>
          <div className="col-span-2 text-center">
            <SortHeader field="weekly_contributions" label="Weekly Posts" />
          </div>
          <div className="col-span-2 text-center">
            <SortHeader field="competition_score" label="Competition" />
          </div>
        </div>

        {/* Table Body */}
        <div className="divide-y divide-border/50 max-h-[600px] overflow-y-auto">
          {isLoading ? (
            <div className="flex items-center justify-center py-20">
              <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
            </div>
          ) : subreddits.length === 0 ? (
            <div className="text-center py-20 text-muted-foreground">
              <BarChart3 size={48} className="mx-auto mb-4 opacity-50" />
              <p>No subreddits found matching your criteria.</p>
              <p className="text-sm mt-1">Try adjusting your filters or run the intel scraper.</p>
            </div>
          ) : (
            subreddits.map((subreddit, index) => (
              <SubredditRow key={subreddit.id} subreddit={subreddit} index={index} />
            ))
          )}
        </div>

        {/* Table Footer */}
        {subreddits.length > 0 && (
          <div className="px-4 py-3 bg-secondary/30 border-t border-border text-sm text-muted-foreground">
            Showing {subreddits.length} subreddits
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-6 text-sm text-muted-foreground">
        <span className="font-medium">Competition Score:</span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-emerald-400" />
          Very Low (&lt;0.5%)
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-green-400" />
          Low (&lt;1%)
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-yellow-400" />
          Moderate (&lt;3%)
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-orange-400" />
          High (&lt;5%)
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-red-400" />
          Very High (&gt;5%)
        </span>
      </div>
    </div>
  );
}

