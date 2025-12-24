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
    // Count from nsfw_subreddit_intel (intel-analyzed subs) instead of subreddits table
    supabase.from("nsfw_subreddit_intel").select("*", { count: "exact", head: true }).eq("scrape_status", "completed"),
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
  // Fetch from nsfw_subreddit_intel (where intel worker puts analyzed subs)
  // Show all completed intel scrapes with pagination to bypass 1k limit
  const allData: any[] = [];
  const pageSize = 1000;
  let offset = 0;
  let hasMore = true;

  while (hasMore) {
    const { data, error } = await supabase
      .from("nsfw_subreddit_intel")
      .select("*")
      .eq("scrape_status", "completed")
      .order("subscribers", { ascending: false, nullsFirst: false })
      .range(offset, offset + pageSize - 1);

    if (error) {
      console.error("Error fetching subreddits:", error);
      break;
    }

    if (data && data.length > 0) {
      allData.push(...data);
      offset += pageSize;
      // If we got fewer results than pageSize, we've reached the end
      hasMore = data.length === pageSize;
    } else {
      hasMore = false;
    }
  }

  // Map nsfw_subreddit_intel fields to Subreddit interface
  return allData.map(sub => ({
    id: sub.id,
    name: sub.subreddit_name,
    display_name: sub.display_name || `r/${sub.subreddit_name}`,
    subscribers: sub.subscribers || 0,
    is_nsfw: true, // Intel table only has NSFW subs
  } as any));
}

export async function getLeadsBySubreddit(
  subredditId: string,
  status: string = "pending",
  limit = 50,
  offset = 0
): Promise<RedditLead[]> {
  // subredditId is now from nsfw_subreddit_intel, need to get subreddit_name
  const { data: intelSub } = await supabase
    .from("nsfw_subreddit_intel")
    .select("subreddit_name")
    .eq("id", subredditId)
    .single();

  if (!intelSub) {
    return [];
  }

  const subredditName = intelSub.subreddit_name;

  // Get lead IDs that have posts with this subreddit_name (with pagination)
  const allLeadIds = new Set<string>();
  let postOffset = 0;
  const pageSize = 1000;

  while (true) {
    const { data: postData, error: postError } = await supabase
      .from("reddit_posts")
      .select("lead_id")
      .eq("subreddit_name", subredditName)
      .range(postOffset, postOffset + pageSize - 1);

    if (postError) {
      console.error("Error fetching posts:", postError);
      break;
    }

    if (!postData || postData.length === 0) {
      break;
    }

    postData.forEach(p => allLeadIds.add(p.lead_id));

    if (postData.length < pageSize) {
      break;
    }

    postOffset += pageSize;
  }

  if (allLeadIds.size === 0) {
    return [];
  }

  const leadIds = Array.from(allLeadIds);

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
  // subredditId is from nsfw_subreddit_intel, get subreddit_name
  const { data: intelSub } = await supabase
    .from("nsfw_subreddit_intel")
    .select("subreddit_name")
    .eq("id", subredditId)
    .single();

  if (!intelSub) {
    return { pending: 0, approved: 0, rejected: 0, superliked: 0 };
  }

  // Get lead IDs that have posts with this subreddit_name (with pagination)
  const allLeadIds = new Set<string>();
  let offset = 0;
  const pageSize = 1000;

  while (true) {
    const { data: postData } = await supabase
      .from("reddit_posts")
      .select("lead_id")
      .eq("subreddit_name", intelSub.subreddit_name)
      .range(offset, offset + pageSize - 1);

    if (!postData || postData.length === 0) {
      break;
    }

    postData.forEach(p => allLeadIds.add(p.lead_id));

    if (postData.length < pageSize) {
      break;
    }

    offset += pageSize;
  }

  if (allLeadIds.size === 0) {
    return { pending: 0, approved: 0, rejected: 0, superliked: 0 };
  }

  const leadIds = Array.from(allLeadIds);

  // Use count queries instead of fetching all data
  const pending = await supabase
    .from("reddit_leads")
    .select("*", { count: "exact", head: true })
    .in("id", leadIds)
    .eq("status", "pending");

  const approved = await supabase
    .from("reddit_leads")
    .select("*", { count: "exact", head: true })
    .in("id", leadIds)
    .eq("status", "approved");

  const rejected = await supabase
    .from("reddit_leads")
    .select("*", { count: "exact", head: true })
    .in("id", leadIds)
    .eq("status", "rejected");

  const superliked = await supabase
    .from("reddit_leads")
    .select("*", { count: "exact", head: true })
    .in("id", leadIds)
    .eq("status", "superliked");

  return {
    pending: pending.count || 0,
    approved: approved.count || 0,
    rejected: rejected.count || 0,
    superliked: superliked.count || 0,
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

// =============================================================================
// SUBREDDIT INTEL - Detailed subreddit metrics with weekly engagement data
// =============================================================================

export interface SubredditIntel {
  id: string;
  subreddit_name: string;
  display_name: string | null;
  subscribers: number | null;
  weekly_visitors: number | null;
  weekly_contributions: number | null;
  competition_score: number | null;
  description: string | null;
  rules_count: number;
  created_utc: string | null;
  is_verified: boolean;
  allows_images: boolean;
  allows_videos: boolean;
  allows_polls: boolean;
  post_requirements: Record<string, unknown>;
  moderator_count: number;
  community_icon_url: string | null;
  banner_url: string | null;
  last_scraped_at: string | null;
  scrape_status: "pending" | "processing" | "completed" | "failed";
  error_message: string | null;
  created_at: string;
  updated_at: string;
  // LLM-analyzed fields
  verification_required: boolean | null;
  sellers_allowed: "allowed" | "not_allowed" | "unknown" | null;
  niche_categories: string[] | null;
  llm_analysis_confidence: "high" | "medium" | "low" | null;
  llm_analysis_reasoning: string | null;
  // Content rating (hardcore/softcore classifier)
  content_rating: "hardcore" | "softcore" | "uncertain" | null;
  content_rating_confidence: "high" | "medium" | "low" | null;
  content_rating_reasoning: string | null;
}

export interface SubredditIntelFilters {
  minSubscribers?: number;
  maxSubscribers?: number;
  minWeeklyVisitors?: number;
  maxCompetitionScore?: number;
  search?: string;
  verificationRequired?: boolean;
  sellersAllowed?: "allowed" | "not_allowed";
  contentRating?: "hardcore" | "softcore";
  sortBy?: "subscribers" | "weekly_visitors" | "weekly_contributions" | "competition_score";
  sortDesc?: boolean;
}

export async function updateSubredditIntelField(
  subredditId: string,
  field: "verification_required" | "sellers_allowed" | "content_rating",
  value: boolean | string | null
): Promise<boolean> {
  try {
    const { error } = await supabase
      .from("nsfw_subreddit_intel")
      .update({ [field]: value })
      .eq("id", subredditId);

    if (error) {
      console.error(`Error updating ${field}:`, error);
      return false;
    }
    return true;
  } catch (error) {
    console.error(`Error updating ${field}:`, error);
    return false;
  }
}

export async function getSubredditIntel(
  limit = 100,
  offset = 0,
  filters: SubredditIntelFilters = {}
): Promise<SubredditIntel[]> {
  let query = supabase
    .from("nsfw_subreddit_intel")
    .select("*")
    .eq("scrape_status", "completed");

  // Apply filters
  if (filters.minSubscribers) {
    query = query.gte("subscribers", filters.minSubscribers);
  }
  if (filters.maxSubscribers) {
    query = query.lte("subscribers", filters.maxSubscribers);
  }
  if (filters.minWeeklyVisitors) {
    query = query.gte("weekly_visitors", filters.minWeeklyVisitors);
  }
  if (filters.maxCompetitionScore) {
    query = query.lte("competition_score", filters.maxCompetitionScore);
  }
  if (filters.search) {
    query = query.ilike("subreddit_name", `%${filters.search}%`);
  }
  if (filters.verificationRequired !== undefined) {
    query = query.eq("verification_required", filters.verificationRequired);
  }
  if (filters.sellersAllowed) {
    query = query.eq("sellers_allowed", filters.sellersAllowed);
  }
  if (filters.contentRating) {
    query = query.eq("content_rating", filters.contentRating);
  }

  // Apply sorting
  const sortBy = filters.sortBy || "weekly_visitors";
  const sortDesc = filters.sortDesc !== false;
  query = query.order(sortBy, { ascending: !sortDesc, nullsFirst: false });

  // Pagination
  query = query.range(offset, offset + limit - 1);

  const { data, error } = await query;

  if (error) {
    console.error("Error fetching subreddit intel:", error);
    return [];
  }

  return data || [];
}

export async function getSubredditIntelStats(): Promise<{
  total: number;
  completed: number;
  pending: number;
  failed: number;
  avgCompetitionScore: number | null;
}> {
  const { data, error } = await supabase
    .from("nsfw_subreddit_intel")
    .select("scrape_status, competition_score");

  if (error) {
    console.error("Error fetching intel stats:", error);
    return { total: 0, completed: 0, pending: 0, failed: 0, avgCompetitionScore: null };
  }

  const items = data || [];
  const completed = items.filter(d => d.scrape_status === "completed");
  const competitionScores = completed
    .map(d => d.competition_score)
    .filter((s): s is number => s !== null);

  const avgCompetition = competitionScores.length > 0
    ? competitionScores.reduce((a, b) => a + b, 0) / competitionScores.length
    : null;

  return {
    total: items.length,
    completed: completed.length,
    pending: items.filter(d => d.scrape_status === "pending").length,
    failed: items.filter(d => d.scrape_status === "failed").length,
    avgCompetitionScore: avgCompetition,
  };
}

