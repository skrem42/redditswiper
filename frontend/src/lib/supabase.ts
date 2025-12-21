import { createClient, SupabaseClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "https://placeholder.supabase.co";
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "placeholder_key";

// Lazy initialization to avoid build-time errors
let _supabase: SupabaseClient | null = null;

export function getSupabase(): SupabaseClient {
  if (!_supabase) {
    _supabase = createClient(supabaseUrl, supabaseAnonKey);
  }
  return _supabase;
}

// For convenience, export a getter that creates the client on first access
export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// Types based on our database schema
export interface RedditLead {
  id: string;
  reddit_username: string;
  reddit_id: string | null;
  karma: number;
  comment_karma: number;
  account_created_at: string | null;
  avatar_url: string | null;
  banner_url: string | null;
  profile_url: string;
  total_posts: number;
  posting_frequency: number | null;
  first_seen: string;
  last_seen: string;
  extracted_links: string[];
  bio: string | null;
  status: "pending" | "approved" | "rejected" | "superliked" | "contacted";
  contacted_at: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  reddit_posts?: RedditPost[];
  // Claim fields for multi-user support
  claimed_by?: string | null;
  claimed_at?: string | null;
}

export interface RedditPost {
  id: string;
  reddit_post_id: string;
  lead_id: string;
  subreddit_id: string | null;
  subreddit_name: string | null;
  title: string | null;
  content: string | null;
  url: string | null;
  permalink: string | null;
  media_urls: string[];
  upvotes: number;
  upvote_ratio: number | null;
  num_comments: number;
  is_nsfw: boolean;
  post_created_at: string | null;
  created_at: string;
}

export interface Stats {
  total_leads: number;
  total_posts: number;
  total_subreddits: number;
  pending_leads: number;
  approved_leads: number;
  rejected_leads: number;
  superliked_leads: number;
  contacted_leads: number;
}

// Claim expiry time in minutes
const CLAIM_EXPIRY_MINUTES = 5;

// API functions

/**
 * Get pending leads with claim-based filtering for multi-user support
 * Only returns leads that are:
 * - Not claimed by anyone
 * - Claimed by the current device
 * - Have expired claims (older than 5 minutes)
 * 
 * After fetching, claims the leads for this device
 */
export async function getPendingLeads(
  limit = 50, 
  offset = 0,
  deviceId?: string
): Promise<RedditLead[]> {
  // Calculate claim expiry threshold
  const expiryThreshold = new Date(
    Date.now() - CLAIM_EXPIRY_MINUTES * 60 * 1000
  ).toISOString();

  // Build the query - get leads that are claimable
  let query = supabase
    .from("reddit_leads")
    .select("*, reddit_posts(*)")
    .eq("status", "pending")
    .order("karma", { ascending: false });

  if (deviceId) {
    // Filter for unclaimed, owned, or expired claims
    // Using OR filter: claimed_by is null OR claimed_by = deviceId OR claimed_at < expiryThreshold
    query = query.or(
      `claimed_by.is.null,claimed_by.eq.${deviceId},claimed_at.lt.${expiryThreshold}`
    );
  }

  const { data, error } = await query.range(offset, offset + limit - 1);

  if (error) {
    console.error("Error fetching leads:", error);
    return [];
  }

  const leads = data || [];

  // Claim the fetched leads for this device
  if (deviceId && leads.length > 0) {
    const leadIds = leads.map((l) => l.id);
    const now = new Date().toISOString();

    await supabase
      .from("reddit_leads")
      .update({ claimed_by: deviceId, claimed_at: now })
      .in("id", leadIds)
      // Only claim if unclaimed or claim expired (avoid stealing active claims)
      .or(`claimed_by.is.null,claimed_at.lt.${expiryThreshold}`);
  }

  return leads;
}

/**
 * Release claims on leads (e.g., when leaving the page)
 */
export async function releaseLeadClaims(deviceId: string): Promise<void> {
  await supabase
    .from("reddit_leads")
    .update({ claimed_by: null, claimed_at: null })
    .eq("claimed_by", deviceId)
    .eq("status", "pending");
}

/**
 * Refresh claims to prevent expiry while actively swiping
 */
export async function refreshLeadClaims(
  leadIds: string[], 
  deviceId: string
): Promise<void> {
  if (leadIds.length === 0) return;
  
  await supabase
    .from("reddit_leads")
    .update({ claimed_at: new Date().toISOString() })
    .in("id", leadIds)
    .eq("claimed_by", deviceId);
}

export async function getLeadsByStatus(
  status: string,
  limit = 50,
  offset = 0
): Promise<RedditLead[]> {
  const { data, error } = await supabase
    .from("reddit_leads")
    .select("*, reddit_posts(*)")
    .eq("status", status)
    .order("updated_at", { ascending: false })
    .range(offset, offset + limit - 1);

  if (error) {
    console.error("Error fetching leads:", error);
    return [];
  }

  return data || [];
}

export async function updateLeadStatus(
  leadId: string,
  status: "approved" | "rejected" | "superliked",
  notes?: string
): Promise<boolean> {
  // Clear claim when status changes (no longer pending)
  const { error: updateError } = await supabase
    .from("reddit_leads")
    .update({ 
      status, 
      updated_at: new Date().toISOString(),
      claimed_by: null,
      claimed_at: null,
    })
    .eq("id", leadId);

  if (updateError) {
    console.error("Error updating lead status:", updateError);
    return false;
  }

  // Create decision record
  const { error: decisionError } = await supabase.from("lead_decisions").insert({
    lead_id: leadId,
    decision: status,
    notes,
  });

  if (decisionError) {
    console.error("Error creating decision record:", decisionError);
  }

  return true;
}

export async function getStats(): Promise<Stats> {
  // Use count queries to avoid Supabase's default 1000 row limit
  const [
    totalLeadsResult,
    postsResult,
    subredditsResult,
    pendingResult,
    approvedResult,
    rejectedResult,
    superlikedResult,
    contactedResult,
  ] = await Promise.all([
    supabase.from("reddit_leads").select("*", { count: "exact", head: true }),
    supabase.from("reddit_posts").select("*", { count: "exact", head: true }),
    supabase.from("subreddits").select("*", { count: "exact", head: true }),
    supabase.from("reddit_leads").select("*", { count: "exact", head: true }).eq("status", "pending"),
    supabase.from("reddit_leads").select("*", { count: "exact", head: true }).eq("status", "approved"),
    supabase.from("reddit_leads").select("*", { count: "exact", head: true }).eq("status", "rejected"),
    supabase.from("reddit_leads").select("*", { count: "exact", head: true }).eq("status", "superliked"),
    supabase.from("reddit_leads").select("*", { count: "exact", head: true }).not("contacted_at", "is", null),
  ]);

  return {
    total_leads: totalLeadsResult.count || 0,
    total_posts: postsResult.count || 0,
    total_subreddits: subredditsResult.count || 0,
    pending_leads: pendingResult.count || 0,
    approved_leads: approvedResult.count || 0,
    rejected_leads: rejectedResult.count || 0,
    superliked_leads: superlikedResult.count || 0,
    contacted_leads: contactedResult.count || 0,
  };
}

// Subreddit types and functions
export interface Subreddit {
  id: string;
  name: string;
  display_name: string;
  subscribers: number;
  is_nsfw: boolean;
}

export async function getSubreddits(): Promise<Subreddit[]> {
  // Fetch from subreddit_queue (where crawler puts discovered subs)
  // Only show completed or processing subs (actively being crawled)
  const { data, error } = await supabase
    .from("subreddit_queue")
    .select("*")
    .in("status", ["completed", "processing"])
    .order("subscribers", { ascending: false }); // Biggest subs first

  if (error) {
    console.error("Error fetching subreddits:", error);
    return [];
  }

  // Map subreddit_queue fields to Subreddit interface
  // Include status as an extra property for active indicator
  return (data || []).map(sub => ({
    id: sub.id,
    name: sub.subreddit_name,
    display_name: `r/${sub.subreddit_name}`,
    subscribers: sub.subscribers || 0,
    is_nsfw: sub.is_nsfw ?? true,
    status: sub.status, // Add status for active indicator
  } as any)); // Cast to any to avoid TS error with extra property
}

export async function getLeadsBySubreddit(
  subredditId: string,
  status: string = "pending",
  limit = 50,
  offset = 0
): Promise<RedditLead[]> {
  // subredditId is now from subreddit_queue, need to get subreddit_name
  const { data: queueSub } = await supabase
    .from("subreddit_queue")
    .select("subreddit_name")
    .eq("id", subredditId)
    .single();

  if (!queueSub) {
    return [];
  }

  const subredditName = queueSub.subreddit_name;

  // Get lead IDs that have posts with this subreddit_name
  const { data: postData, error: postError } = await supabase
    .from("reddit_posts")
    .select("lead_id")
    .eq("subreddit_name", subredditName);

  if (postError || !postData) {
    console.error("Error fetching posts:", postError);
    return [];
  }

  const leadIds = [...new Set(postData.map((p) => p.lead_id))];

  if (leadIds.length === 0) {
    return [];
  }

  const { data, error } = await supabase
    .from("reddit_leads")
    .select("*, reddit_posts(*)")
    .in("id", leadIds)
    .eq("status", status)
    .order("karma", { ascending: false })
    .range(offset, offset + limit - 1);

  if (error) {
    console.error("Error fetching leads:", error);
    return [];
  }

  return data || [];
}

export async function getSubredditStats(subredditId: string): Promise<{
  pending: number;
  approved: number;
  rejected: number;
  superliked: number;
}> {
  // subredditId is from subreddit_queue, get subreddit_name
  const { data: queueSub } = await supabase
    .from("subreddit_queue")
    .select("subreddit_name")
    .eq("id", subredditId)
    .single();

  if (!queueSub) {
    return { pending: 0, approved: 0, rejected: 0, superliked: 0 };
  }

  // Get lead IDs that have posts with this subreddit_name
  const { data: postData } = await supabase
    .from("reddit_posts")
    .select("lead_id")
    .eq("subreddit_name", queueSub.subreddit_name);

  const leadIds = [...new Set((postData || []).map((p) => p.lead_id))];

  if (leadIds.length === 0) {
    return { pending: 0, approved: 0, rejected: 0, superliked: 0 };
  }

  const { data: leads } = await supabase
    .from("reddit_leads")
    .select("status")
    .in("id", leadIds);

  const leadsData = leads || [];

  return {
    pending: leadsData.filter((l) => l.status === "pending").length,
    approved: leadsData.filter((l) => l.status === "approved").length,
    rejected: leadsData.filter((l) => l.status === "rejected").length,
    superliked: leadsData.filter((l) => l.status === "superliked").length,
  };
}

// =============================================================================
// SEARCH KEYWORDS & SCRAPE JOBS
// =============================================================================

export interface SearchKeyword {
  id: string;
  keyword: string;
  is_active: boolean;
  priority: number;
  times_scraped: number;
  last_scraped_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ScrapeJob {
  id: string;
  keyword_id: string | null;
  keyword: string;
  status: "pending" | "processing" | "completed" | "failed";
  priority: number;
  subreddits_found: number;
  leads_found: number;
  posts_found: number;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export async function getSearchKeywords(): Promise<SearchKeyword[]> {
  const { data, error } = await supabase
    .from("search_keywords")
    .select("*")
    .order("priority", { ascending: false });

  if (error) {
    console.error("Error fetching keywords:", error);
    return [];
  }

  return data || [];
}

export async function addSearchKeyword(keyword: string, priority: number = 1000): Promise<SearchKeyword | null> {
  // Check if keyword already exists
  const { data: existing } = await supabase
    .from("search_keywords")
    .select("*")
    .eq("keyword", keyword.toLowerCase().trim())
    .single();

  if (existing) {
    // Update priority if it exists
    const { data, error } = await supabase
      .from("search_keywords")
      .update({ priority, is_active: true, updated_at: new Date().toISOString() })
      .eq("id", existing.id)
      .select()
      .single();

    if (error) {
      console.error("Error updating keyword:", error);
      return null;
    }
    return data;
  }

  // Insert new keyword
  const { data, error } = await supabase
    .from("search_keywords")
    .insert({
      keyword: keyword.toLowerCase().trim(),
      priority,
      is_active: true,
    })
    .select()
    .single();

  if (error) {
    console.error("Error adding keyword:", error);
    return null;
  }

  return data;
}

export async function updateKeywordPriority(keywordId: string, priority: number): Promise<boolean> {
  const { error } = await supabase
    .from("search_keywords")
    .update({ priority, updated_at: new Date().toISOString() })
    .eq("id", keywordId);

  if (error) {
    console.error("Error updating priority:", error);
    return false;
  }
  return true;
}

export async function toggleKeywordActive(keywordId: string, isActive: boolean): Promise<boolean> {
  const { error } = await supabase
    .from("search_keywords")
    .update({ is_active: isActive, updated_at: new Date().toISOString() })
    .eq("id", keywordId);

  if (error) {
    console.error("Error toggling keyword:", error);
    return false;
  }
  return true;
}

export async function deleteKeyword(keywordId: string): Promise<boolean> {
  const { error } = await supabase
    .from("search_keywords")
    .delete()
    .eq("id", keywordId);

  if (error) {
    console.error("Error deleting keyword:", error);
    return false;
  }
  return true;
}

export async function getScrapeJobs(limit: number = 20): Promise<ScrapeJob[]> {
  const { data, error } = await supabase
    .from("scrape_jobs")
    .select("*")
    .order("created_at", { ascending: false })
    .limit(limit);

  if (error) {
    console.error("Error fetching scrape jobs:", error);
    return [];
  }

  return data || [];
}

export async function queueScrapeJob(keyword: string, keywordId?: string, priority: number = 1000): Promise<ScrapeJob | null> {
  const { data, error } = await supabase
    .from("scrape_jobs")
    .insert({
      keyword: keyword.toLowerCase().trim(),
      keyword_id: keywordId || null,
      priority,
      status: "pending",
    })
    .select()
    .single();

  if (error) {
    console.error("Error queuing scrape job:", error);
    return null;
  }

  return data;
}

export async function addKeywordAndScrape(keyword: string): Promise<{
  keyword: SearchKeyword | null;
  job: ScrapeJob | null;
}> {
  // Add keyword with high priority
  const savedKeyword = await addSearchKeyword(keyword, 1000);
  
  if (!savedKeyword) {
    return { keyword: null, job: null };
  }

  // Queue a scrape job for this keyword
  const job = await queueScrapeJob(keyword, savedKeyword.id, 1000);

  return { keyword: savedKeyword, job };
}

// =============================================================================
// CRM FUNCTIONS - CONTACT TRACKING
// =============================================================================

export async function markLeadContacted(
  leadId: string,
  notes?: string
): Promise<boolean> {
  const updateData: Record<string, unknown> = {
    contacted_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };
  
  if (notes !== undefined) {
    updateData.notes = notes;
  }

  const { error } = await supabase
    .from("reddit_leads")
    .update(updateData)
    .eq("id", leadId);

  if (error) {
    console.error("Error marking lead as contacted:", error);
    return false;
  }

  return true;
}

export async function unmarkLeadContacted(leadId: string): Promise<boolean> {
  const { error } = await supabase
    .from("reddit_leads")
    .update({
      contacted_at: null,
      updated_at: new Date().toISOString(),
    })
    .eq("id", leadId);

  if (error) {
    console.error("Error unmarking lead as contacted:", error);
    return false;
  }

  return true;
}

export async function updateLeadNotes(
  leadId: string,
  notes: string
): Promise<boolean> {
  const { error } = await supabase
    .from("reddit_leads")
    .update({
      notes,
      updated_at: new Date().toISOString(),
    })
    .eq("id", leadId);

  if (error) {
    console.error("Error updating lead notes:", error);
    return false;
  }

  return true;
}

export async function getContactedLeads(
  limit = 50,
  offset = 0
): Promise<RedditLead[]> {
  const { data, error } = await supabase
    .from("reddit_leads")
    .select("*, reddit_posts(*)")
    .not("contacted_at", "is", null)
    .order("contacted_at", { ascending: false })
    .range(offset, offset + limit - 1);

  if (error) {
    console.error("Error fetching contacted leads:", error);
    return [];
  }

  return data || [];
}

