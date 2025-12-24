"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { RefreshCw, Zap, Undo2, BarChart3, Users } from "lucide-react";
import {
  getPendingLeads,
  getLeadsByStatus,
  getLeadsBySubreddit,
  getContactedLeads,
  updateLeadStatus,
  getStats,
  getSubreddits,
  releaseLeadClaims,
  refreshLeadClaims,
  type RedditLead,
  type Stats,
  type Subreddit,
} from "@/lib/supabase";
import { getDeviceId } from "@/lib/deviceId";
import { SwipeCard } from "@/components/SwipeCard";
import { StatsBar } from "@/components/StatsBar";
import { LeadsList } from "@/components/LeadsList";
import { SubredditSelector } from "@/components/SubredditSelector";
import { KeywordManager } from "@/components/KeywordManager";
import { SortSelector, type SortOption } from "@/components/SortSelector";
import { SubredditExplorer } from "@/components/SubredditExplorer";

// History entry for undo
interface SwipeHistoryEntry {
  lead: RedditLead;
  action: "approved" | "rejected" | "superliked";
}

// Main navigation views
type MainView = "leads" | "subreddits";

export default function Home() {
  const [mainView, setMainView] = useState<MainView>("leads");
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
  const [sortBy, setSortBy] = useState<SortOption>("avg_upvotes");
  
  // Device ID for claim system
  const [deviceId, setDeviceId] = useState<string>("");
  
  // Subreddit filtering - multi-select exclusion
  const [subreddits, setSubreddits] = useState<Subreddit[]>([]);
  const [excludedSubreddits, setExcludedSubreddits] = useState<Set<string>>(new Set());
  const [subredditPendingCounts, setSubredditPendingCounts] = useState<Record<string, number>>({});
  
  // Initialize device ID on mount
  useEffect(() => {
    setDeviceId(getDeviceId());
  }, []);

  // Fetch subreddits
  const fetchSubreddits = useCallback(async () => {
    try {
      const data = await getSubreddits();
      setSubreddits(data);
      
      // Calculate pending counts per subreddit (using subreddit_name now)
      const { supabase } = await import("@/lib/supabase");
      const counts: Record<string, number> = {};
      
      for (const sub of data) {
        // Fetch all posts for this subreddit with pagination (to bypass 1k limit)
        const allPostLeadIds = new Set<string>();
        let offset = 0;
        const pageSize = 1000;
        
        while (true) {
          const { data: posts } = await supabase
            .from("reddit_posts")
            .select("lead_id")
            .eq("subreddit_name", sub.name)
            .range(offset, offset + pageSize - 1);
          
          if (!posts || posts.length === 0) break;
          
          posts.forEach(p => allPostLeadIds.add(p.lead_id));
          
          if (posts.length < pageSize) break;
          offset += pageSize;
        }
        
        if (allPostLeadIds.size > 0) {
          // Count pending leads for these lead IDs
          const leadIdsArray = Array.from(allPostLeadIds);
          
          // Use count query instead of fetching all leads
          const { count } = await supabase
            .from("reddit_leads")
            .select("*", { count: "exact", head: true })
            .in("id", leadIdsArray)
            .eq("status", "pending");
          
          counts[sub.id] = count || 0;
        }
      }
      setSubredditPendingCounts(counts);
    } catch (error) {
      console.error("Error fetching subreddits:", error);
    }
  }, []);

  // Fetch leads based on current filter and excluded subreddits
  const fetchLeads = useCallback(async () => {
    if (!deviceId) return; // Wait for device ID to be set
    
    setIsLoading(true);
    try {
      let data: RedditLead[];
      
      if (currentFilter === "pending") {
        // Pass deviceId for claim-based filtering
        data = await getPendingLeads(100, 0, deviceId);
      } else if (currentFilter === "contacted") {
        data = await getContactedLeads(100);
      } else {
        data = await getLeadsByStatus(currentFilter, 100);
      }
      
      // Filter out leads from excluded subreddits
      if (excludedSubreddits.size > 0 && data.length > 0) {
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
  }, [currentFilter, excludedSubreddits, deviceId]);

  // Fetch stats
  const fetchStats = useCallback(async () => {
    try {
      const data = await getStats();
      setStats(data);
    } catch (error) {
      console.error("Error fetching stats:", error);
    }
  }, []);

  // Initial load - wait for device ID
  useEffect(() => {
    if (!deviceId) return;
    fetchSubreddits();
    fetchLeads();
    fetchStats();
  }, [fetchSubreddits, fetchLeads, fetchStats, deviceId]);

  // Refresh claims periodically to prevent expiry (every 2 minutes)
  useEffect(() => {
    if (!deviceId || currentFilter !== "pending" || leads.length === 0) return;
    
    const interval = setInterval(async () => {
      const leadIds = leads.map(l => l.id);
      await refreshLeadClaims(leadIds, deviceId);
    }, 2 * 60 * 1000); // 2 minutes
    
    return () => clearInterval(interval);
  }, [deviceId, currentFilter, leads]);

  // Release claims when leaving the page
  useEffect(() => {
    if (!deviceId) return;
    
    const handleBeforeUnload = () => {
      // Use sendBeacon for reliable cleanup on page close
      const url = `${process.env.NEXT_PUBLIC_SUPABASE_URL}/rest/v1/reddit_leads?claimed_by=eq.${deviceId}&status=eq.pending`;
      const body = JSON.stringify({ claimed_by: null, claimed_at: null });
      navigator.sendBeacon(url, body);
    };
    
    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
      // Also release claims when component unmounts (navigation)
      releaseLeadClaims(deviceId);
    };
  }, [deviceId]);

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
    const leadToSwipe = sortedLeads[currentIndex];
    if (!leadToSwipe) return;

    const status = direction === "right" ? "approved" : "rejected";

    // Add to history for undo
    setSwipeHistory((prev) => [...prev, { lead: leadToSwipe, action: status }]);

    // Optimistic update - filter by lead ID, not by index
    setLeads((prev) => prev.filter((lead) => lead.id !== leadToSwipe.id));
    setStats((prev) => ({
      ...prev,
      pending_leads: Math.max(0, prev.pending_leads - 1),
      approved_leads:
        status === "approved" ? prev.approved_leads + 1 : prev.approved_leads,
      rejected_leads:
        status === "rejected" ? prev.rejected_leads + 1 : prev.rejected_leads,
    }));

    // Update in database
    await updateLeadStatus(leadToSwipe.id, status);
  };

  // Handle super like
  const handleSuperLike = async () => {
    const leadToSwipe = sortedLeads[currentIndex];
    if (!leadToSwipe) return;

    // Add to history for undo
    setSwipeHistory((prev) => [...prev, { lead: leadToSwipe, action: "superliked" }]);

    // Optimistic update - filter by lead ID, not by index
    setLeads((prev) => prev.filter((lead) => lead.id !== leadToSwipe.id));
    setStats((prev) => ({
      ...prev,
      pending_leads: Math.max(0, prev.pending_leads - 1),
      superliked_leads: prev.superliked_leads + 1,
    }));

    // Update in database
    await updateLeadStatus(leadToSwipe.id, "superliked");
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

  // Sort leads based on selected option
  const sortedLeads = useMemo(() => {
    if (currentFilter !== "pending") return leads; // Only sort pending leads
    
    const leadsWithMetrics = leads.map(lead => {
      // Calculate average upvotes
      let avgUpvotes = 0;
      if (lead.reddit_posts && lead.reddit_posts.length > 0) {
        const totalUpvotes = lead.reddit_posts.reduce((sum, post) => sum + (post.upvotes || 0), 0);
        avgUpvotes = totalUpvotes / lead.reddit_posts.length;
      }
      
      // Get posting frequency
      const postsPerDay = lead.posting_frequency || 0;
      
      return { lead, avgUpvotes, postsPerDay };
    });
    
    // Sort based on selected option
    const sorted = [...leadsWithMetrics].sort((a, b) => {
      switch (sortBy) {
        case "avg_upvotes":
          return b.avgUpvotes - a.avgUpvotes; // Descending
        case "total_karma":
          return b.lead.karma - a.lead.karma; // Descending
        case "posts_per_day":
          return b.postsPerDay - a.postsPerDay; // Descending
        default:
          return 0;
      }
    });
    
    return sorted.map(item => item.lead);
  }, [leads, sortBy, currentFilter]);

  const currentLead = sortedLeads[currentIndex];
  const showSwiper = currentFilter === "pending";

  return (
    <main className="min-h-screen p-3 md:p-6 lg:p-8 max-w-4xl mx-auto">
      {/* Header - Compact on mobile */}
      <header className="flex items-center justify-between mb-3 md:mb-6 gap-2 flex-wrap">
        <div className="flex-shrink-0">
          <h1 className="text-xl md:text-3xl font-bold gradient-text flex items-center gap-2">
            <Zap className="text-primary w-5 h-5 md:w-6 md:h-6" />
            <span className="hidden sm:inline">Reddit Scraper</span>
            <span className="sm:hidden">Leads</span>
          </h1>
          <p className="text-muted-foreground text-xs md:text-base mt-0.5 md:mt-1 hidden md:block">
            Discover leads and analyze subreddits
          </p>
        </div>
        
        {/* Main Navigation Tabs - Smaller on mobile */}
        <div className="flex items-center gap-1 md:gap-2 bg-secondary rounded-lg md:rounded-xl p-0.5 md:p-1">
          <button
            onClick={() => setMainView("leads")}
            className={`flex items-center gap-1 md:gap-2 px-2 md:px-4 py-1.5 md:py-2 rounded-md md:rounded-lg font-medium transition-all text-sm md:text-base ${
              mainView === "leads"
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <Users size={16} className="md:w-[18px] md:h-[18px]" />
            <span className="hidden xs:inline">Leads</span>
          </button>
          <button
            onClick={() => setMainView("subreddits")}
            className={`flex items-center gap-1 md:gap-2 px-2 md:px-4 py-1.5 md:py-2 rounded-md md:rounded-lg font-medium transition-all text-sm md:text-base ${
              mainView === "subreddits"
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <BarChart3 size={16} className="md:w-[18px] md:h-[18px]" />
            <span className="hidden xs:inline">Subs</span>
          </button>
        </div>
        
        {mainView === "leads" && (
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="p-2 md:p-3 rounded-lg md:rounded-xl bg-secondary hover:bg-secondary/80 text-foreground transition-all disabled:opacity-50"
            title="Refresh data"
          >
            <RefreshCw
              size={18}
              className={isRefreshing ? "animate-spin" : ""}
            />
          </button>
        )}
      </header>

      {/* Subreddit Explorer View */}
      {mainView === "subreddits" && (
        <SubredditExplorer />
      )}
      
      {/* Leads View */}
      {mainView === "leads" && (
        <>
          {/* Filters row - Hidden when swiping on mobile for more space */}
          <div className="relative z-30 flex items-center justify-between gap-2 md:gap-4 mb-3 md:mb-6 flex-wrap">
            <div className="flex items-center gap-2 md:gap-4">
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
                <span className="hidden md:inline text-sm text-muted-foreground">
                  Hiding {excludedSubreddits.size} subreddit{excludedSubreddits.size > 1 ? "s" : ""}
                </span>
              )}
            </div>
            
            <div className="flex items-center gap-2 md:gap-3">
              {/* Sort Selector - only show for pending leads */}
              {currentFilter === "pending" && (
                <SortSelector currentSort={sortBy} onSortChange={setSortBy} />
              )}
              
              {/* Keyword Manager */}
              <KeywordManager onJobQueued={() => fetchSubreddits()} />
            </div>
          </div>

          {/* Stats bar with filters */}
          <StatsBar
            stats={stats}
            currentFilter={currentFilter}
            onFilterChange={setCurrentFilter}
          />

          {/* Main content area */}
          <div className="relative min-h-[400px] md:min-h-[600px]">
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
            {sortedLeads.length > 0 ? (
              <>
                {/* Card stack indicator - smaller on mobile */}
                <div className="text-center mb-2 md:mb-4 text-xs md:text-sm text-muted-foreground">
                  {currentIndex + 1} of {sortedLeads.length} pending
                </div>

                {/* Swipe cards - full height on mobile, constrained on desktop */}
                <div className="relative h-[calc(100vh-200px)] md:h-[70vh] md:min-h-[550px]">
                  <AnimatePresence mode="popLayout">
                    {currentLead && (
                      <SwipeCard
                        key={currentLead.id}
                        lead={currentLead}
                        nextLeads={sortedLeads.slice(currentIndex + 1, currentIndex + 4)}
                        onSwipe={handleSwipe}
                        onSuperLike={handleSuperLike}
                        isActive={true}
                      />
                    )}
                  </AnimatePresence>
                </div>

                {/* Keyboard hints and undo button - hidden on mobile (buttons are in card) */}
                <div className="hidden md:flex items-center justify-center gap-4 mt-4">
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

                {/* Mobile undo button - fixed at bottom */}
                <div className="md:hidden fixed bottom-4 left-1/2 -translate-x-1/2 z-30">
                  <button
                    onClick={handleUndo}
                    disabled={swipeHistory.length === 0}
                    className="flex items-center gap-2 px-4 py-2 rounded-full bg-secondary/90 backdrop-blur text-foreground transition-all disabled:opacity-30 disabled:cursor-not-allowed shadow-lg"
                    title="Undo last swipe"
                  >
                    <Undo2 size={16} />
                    <span className="text-sm">Undo</span>
                    {swipeHistory.length > 0 && (
                      <span className="text-xs text-muted-foreground">
                        ({swipeHistory.length})
                      </span>
                    )}
                  </button>
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
        </>
      )}
    </main>
  );
}


