"use client";

import { useState, useEffect, useCallback } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { RefreshCw, Zap, Undo2 } from "lucide-react";
import {
  getPendingLeads,
  getLeadsByStatus,
  getLeadsBySubreddit,
  getContactedLeads,
  updateLeadStatus,
  getStats,
  getSubreddits,
  type RedditLead,
  type Stats,
  type Subreddit,
} from "@/lib/supabase";
import { SwipeCard } from "@/components/SwipeCard";
import { StatsBar } from "@/components/StatsBar";
import { LeadsList } from "@/components/LeadsList";
import { SubredditSelector } from "@/components/SubredditSelector";
import { KeywordManager } from "@/components/KeywordManager";

// History entry for undo
interface SwipeHistoryEntry {
  lead: RedditLead;
  action: "approved" | "rejected" | "superliked";
}

export default function Home() {
  const [leads, setLeads] = useState<RedditLead[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [swipeHistory, setSwipeHistory] = useState<SwipeHistoryEntry[]>([]);
  const [stats, setStats] = useState<Stats>({
    total_leads: 0,
    total_posts: 0,
    total_subreddits: 0,
    pending_leads: 0,
    approved_leads: 0,
    rejected_leads: 0,
    superliked_leads: 0,
    contacted_leads: 0,
  });
  const [currentFilter, setCurrentFilter] = useState("pending");
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  // Subreddit filtering - multi-select exclusion
  const [subreddits, setSubreddits] = useState<Subreddit[]>([]);
  const [excludedSubreddits, setExcludedSubreddits] = useState<Set<string>>(new Set());
  const [subredditPendingCounts, setSubredditPendingCounts] = useState<Record<string, number>>({});

  // Fetch subreddits
  const fetchSubreddits = useCallback(async () => {
    try {
      const data = await getSubreddits();
      setSubreddits(data);
      
      // Calculate pending counts per subreddit (using subreddit_name now)
      const { supabase } = await import("@/lib/supabase");
      const counts: Record<string, number> = {};
      
      for (const sub of data) {
        const { data: posts } = await supabase
          .from("reddit_posts")
          .select("lead_id")
          .eq("subreddit_name", sub.name); // Use name instead of id
        
        if (posts) {
          const leadIds = [...new Set(posts.map((p) => p.lead_id))];
          if (leadIds.length > 0) {
            const { data: leads } = await supabase
              .from("reddit_leads")
              .select("id")
              .in("id", leadIds)
              .eq("status", "pending");
            counts[sub.id] = leads?.length || 0;
          }
        }
      }
      setSubredditPendingCounts(counts);
    } catch (error) {
      console.error("Error fetching subreddits:", error);
    }
  }, []);

  // Fetch leads based on current filter and excluded subreddits
  const fetchLeads = useCallback(async () => {
    setIsLoading(true);
    try {
      let data: RedditLead[];
      
      if (currentFilter === "pending") {
        data = await getPendingLeads(100); // Fetch more to filter
      } else if (currentFilter === "contacted") {
        data = await getContactedLeads(100);
      } else {
        data = await getLeadsByStatus(currentFilter, 100);
      }
      
      // Filter out leads from excluded subreddits
      if (excludedSubreddits.size > 0 && data.length > 0) {
        // Get subreddit IDs for each lead's posts
        const { supabase } = await import("@/lib/supabase");
        
        // For each lead, check if ALL their posts are from excluded subreddits
        const filteredData: RedditLead[] = [];
        
        for (const lead of data) {
          // Get subreddit IDs from this lead's posts
          const leadSubredditIds = new Set(
            (lead.reddit_posts || [])
              .map(p => p.subreddit_id)
              .filter(Boolean) as string[]
          );
          
          // If lead has no posts with subreddit info, include them
          if (leadSubredditIds.size === 0) {
            filteredData.push(lead);
            continue;
          }
          
          // Check if at least one post is from a non-excluded subreddit
          const hasNonExcludedPost = Array.from(leadSubredditIds).some(
            subId => !excludedSubreddits.has(subId)
          );
          
          if (hasNonExcludedPost) {
            filteredData.push(lead);
          }
        }
        
        data = filteredData;
      }
      
      setLeads(data.slice(0, 50)); // Limit final results
      setCurrentIndex(0);
    } catch (error) {
      console.error("Error fetching leads:", error);
    } finally {
      setIsLoading(false);
    }
  }, [currentFilter, excludedSubreddits]);

  // Fetch stats
  const fetchStats = useCallback(async () => {
    try {
      const data = await getStats();
      setStats(data);
    } catch (error) {
      console.error("Error fetching stats:", error);
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchSubreddits();
    fetchLeads();
    fetchStats();
  }, [fetchSubreddits, fetchLeads, fetchStats]);

  // Keyboard shortcut for undo
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "z" || e.key === "Z") {
        if (currentFilter === "pending" && swipeHistory.length > 0) {
          handleUndo();
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [currentFilter, swipeHistory.length]);

  // Refetch when filter or exclusions change
  useEffect(() => {
    fetchLeads();
  }, [currentFilter, excludedSubreddits, fetchLeads]);

  // Handle swipe
  const handleSwipe = async (direction: "left" | "right") => {
    const currentLead = leads[currentIndex];
    if (!currentLead) return;

    const status = direction === "right" ? "approved" : "rejected";

    // Add to history for undo
    setSwipeHistory((prev) => [...prev, { lead: currentLead, action: status }]);

    // Optimistic update
    setLeads((prev) => prev.filter((_, i) => i !== currentIndex));
    setStats((prev) => ({
      ...prev,
      pending_leads: Math.max(0, prev.pending_leads - 1),
      approved_leads:
        status === "approved" ? prev.approved_leads + 1 : prev.approved_leads,
      rejected_leads:
        status === "rejected" ? prev.rejected_leads + 1 : prev.rejected_leads,
    }));

    // Update in database
    await updateLeadStatus(currentLead.id, status);
  };

  // Handle super like
  const handleSuperLike = async () => {
    const currentLead = leads[currentIndex];
    if (!currentLead) return;

    // Add to history for undo
    setSwipeHistory((prev) => [...prev, { lead: currentLead, action: "superliked" }]);

    // Optimistic update
    setLeads((prev) => prev.filter((_, i) => i !== currentIndex));
    setStats((prev) => ({
      ...prev,
      pending_leads: Math.max(0, prev.pending_leads - 1),
      superliked_leads: prev.superliked_leads + 1,
    }));

    // Update in database
    await updateLeadStatus(currentLead.id, "superliked");
  };

  // Handle undo - go back to previous lead
  const handleUndo = async () => {
    if (swipeHistory.length === 0) return;

    const lastEntry = swipeHistory[swipeHistory.length - 1];
    
    // Remove from history
    setSwipeHistory((prev) => prev.slice(0, -1));

    // Add lead back to the front of the list
    setLeads((prev) => [lastEntry.lead, ...prev]);
    
    // Update stats
    setStats((prev) => ({
      ...prev,
      pending_leads: prev.pending_leads + 1,
      approved_leads:
        lastEntry.action === "approved"
          ? Math.max(0, prev.approved_leads - 1)
          : prev.approved_leads,
      rejected_leads:
        lastEntry.action === "rejected"
          ? Math.max(0, prev.rejected_leads - 1)
          : prev.rejected_leads,
      superliked_leads:
        lastEntry.action === "superliked"
          ? Math.max(0, prev.superliked_leads - 1)
          : prev.superliked_leads,
    }));

    // Update in database - set back to pending
    const { supabase } = await import("@/lib/supabase");
    await supabase
      .from("reddit_leads")
      .update({ status: "pending", updated_at: new Date().toISOString() })
      .eq("id", lastEntry.lead.id);
  };

  // Handle restore (move back to pending)
  const handleRestore = async (leadId: string) => {
    // Find the lead
    const lead = leads.find((l) => l.id === leadId);
    if (!lead) return;

    // Optimistic update
    setLeads((prev) => prev.filter((l) => l.id !== leadId));
    setStats((prev) => ({
      ...prev,
      pending_leads: prev.pending_leads + 1,
      approved_leads:
        lead.status === "approved"
          ? Math.max(0, prev.approved_leads - 1)
          : prev.approved_leads,
      rejected_leads:
        lead.status === "rejected"
          ? Math.max(0, prev.rejected_leads - 1)
          : prev.rejected_leads,
    }));

    // Update in database - we need to update to pending status
    // Note: This requires a slight modification to updateLeadStatus to handle "pending"
    // For now, we'll just update the status directly
    const { supabase } = await import("@/lib/supabase");
    await supabase
      .from("reddit_leads")
      .update({ status: "pending", updated_at: new Date().toISOString() })
      .eq("id", leadId);
  };

  // Refresh data
  const handleRefresh = async () => {
    setIsRefreshing(true);
    await Promise.all([fetchLeads(), fetchStats(), fetchSubreddits()]);
    setIsRefreshing(false);
  };

  const currentLead = leads[currentIndex];
  const showSwiper = currentFilter === "pending";

  return (
    <main className="min-h-screen p-6 md:p-8 max-w-4xl mx-auto">
      {/* Header */}
      <header className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold gradient-text flex items-center gap-2">
            <Zap className="text-primary" />
            Lead Swiper
          </h1>
          <p className="text-muted-foreground mt-1">
            Swipe through Reddit leads for your OF agency
          </p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={isRefreshing}
          className="p-3 rounded-xl bg-secondary hover:bg-secondary/80 text-foreground transition-all disabled:opacity-50"
          title="Refresh data"
        >
          <RefreshCw
            size={20}
            className={isRefreshing ? "animate-spin" : ""}
          />
        </button>
      </header>

      {/* Filters row */}
      <div className="flex items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-4">
          <SubredditSelector
            subreddits={subreddits}
            excludedSubreddits={excludedSubreddits}
            onExclusionChange={(excluded) => {
              setExcludedSubreddits(excluded);
              setSwipeHistory([]); // Clear undo history when filter changes
            }}
            pendingCounts={subredditPendingCounts}
          />
          {excludedSubreddits.size > 0 && (
            <span className="text-sm text-muted-foreground">
              Hiding {excludedSubreddits.size} subreddit{excludedSubreddits.size > 1 ? "s" : ""}
            </span>
          )}
        </div>
        
        {/* Keyword Manager */}
        <KeywordManager onJobQueued={() => fetchSubreddits()} />
      </div>

      {/* Stats bar with filters */}
      <StatsBar
        stats={stats}
        currentFilter={currentFilter}
        onFilterChange={setCurrentFilter}
      />

      {/* Main content area */}
      <div className="relative min-h-[600px]">
        {isLoading ? (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center space-y-4">
              <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto" />
              <p className="text-muted-foreground">Loading leads...</p>
            </div>
          </div>
        ) : showSwiper ? (
          // Swipe mode for pending leads
          <>
            {leads.length > 0 ? (
              <>
                {/* Card stack indicator */}
                <div className="text-center mb-4 text-sm text-muted-foreground">
                  {currentIndex + 1} of {leads.length} pending leads
                </div>

                {/* Swipe cards */}
                <div className="relative h-[75vh] min-h-[600px]">
                  <AnimatePresence mode="popLayout">
                    {currentLead && (
                      <SwipeCard
                        key={currentLead.id}
                        lead={currentLead}
                        onSwipe={handleSwipe}
                        onSuperLike={handleSuperLike}
                        isActive={true}
                      />
                    )}
                  </AnimatePresence>
                </div>

                {/* Keyboard hints and undo button */}
                <div className="flex items-center justify-center gap-4 mt-4">
                  {/* Undo button */}
                  <button
                    onClick={handleUndo}
                    disabled={swipeHistory.length === 0}
                    className="flex items-center gap-2 px-4 py-2 rounded-xl bg-secondary hover:bg-secondary/80 text-foreground transition-all disabled:opacity-30 disabled:cursor-not-allowed"
                    title="Undo last swipe (Z)"
                  >
                    <Undo2 size={16} />
                    <span className="text-sm">Undo</span>
                    {swipeHistory.length > 0 && (
                      <span className="text-xs text-muted-foreground">
                        ({swipeHistory.length})
                      </span>
                    )}
                  </button>
                  
                  {/* Keyboard hints */}
                  <div className="flex items-center gap-3 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <kbd className="px-2 py-1 bg-secondary rounded">←</kbd>
                      Reject
                    </span>
                    <span className="flex items-center gap-1">
                      <kbd className="px-2 py-1 bg-amber-500/20 text-amber-400 rounded">↑</kbd>
                      <span className="text-amber-400">Super</span>
                    </span>
                    <span className="flex items-center gap-1">
                      <kbd className="px-2 py-1 bg-secondary rounded">→</kbd>
                      Approve
                    </span>
                    <span className="flex items-center gap-1">
                      <kbd className="px-2 py-1 bg-secondary rounded">Z</kbd>
                      Undo
                    </span>
                  </div>
                </div>
              </>
            ) : (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center py-20"
              >
                <div className="w-20 h-20 bg-success/10 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-4xl">🎉</span>
                </div>
                <h2 className="text-2xl font-bold text-foreground mb-2">
                  All caught up!
                </h2>
                <p className="text-muted-foreground mb-6">
                  No more pending leads to review. Run the scraper to find more!
                </p>
                <button
                  onClick={handleRefresh}
                  className="px-6 py-3 bg-primary text-primary-foreground rounded-xl font-medium hover:bg-primary/90 transition-colors"
                >
                  Check for new leads
                </button>
              </motion.div>
            )}
          </>
        ) : (
          // List mode for approved/rejected/superliked/contacted leads
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="bg-card rounded-2xl p-6"
          >
            <LeadsList
              leads={leads}
              onRestore={handleRestore}
              showRestore={currentFilter !== "contacted"}
              onBack={() => setCurrentFilter("pending")}
              title={`${currentFilter.charAt(0).toUpperCase() + currentFilter.slice(1)} Leads`}
              showContactCheckbox={currentFilter === "approved" || currentFilter === "superliked" || currentFilter === "contacted"}
              onLeadUpdate={() => {
                fetchStats();
                if (currentFilter === "contacted") {
                  fetchLeads();
                }
              }}
            />
          </motion.div>
        )}
      </div>
    </main>
  );
}


