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

// API functions
export async function getPendingLeads(limit = 50, offset = 0): Promise<RedditLead[]> {
  const { data, error } = await supabase
    .from("reddit_leads")
    .select("*, reddit_posts(*)")
    .eq("status", "pending")
    .order("karma", { ascending: false })
    .range(offset, offset + limit - 1);

  if (error) {
    console.error("Error fetching leads:", error);
    return [];
  }

  return data || [];
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
  const { error: updateError } = await supabase
    .from("reddit_leads")
    .update({ status, updated_at: new Date().toISOString() })
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
  const { data: leads } = await supabase
    .from("reddit_leads")
    .select("id, status, contacted_at");

  const { count: postsCount } = await supabase
    .from("reddit_posts")
    .select("*", { count: "exact", head: true });

  const { count: subredditsCount } = await supabase
    .from("subreddits")
    .select("*", { count: "exact", head: true });

  const leadsData = leads || [];

  return {
    total_leads: leadsData.length,
    total_posts: postsCount || 0,
    total_subreddits: subredditsCount || 0,
    pending_leads: leadsData.filter((l) => l.status === "pending").length,
    approved_leads: leadsData.filter((l) => l.status === "approved").length,
    rejected_leads: leadsData.filter((l) => l.status === "rejected").length,
    superliked_leads: leadsData.filter((l) => l.status === "superliked").length,
    contacted_leads: leadsData.filter((l) => l.contacted_at !== null).length,
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
  const { data, error } = await supabase
    .from("subreddits")
    .select("*")
    .order("name", { ascending: true });

  if (error) {
    console.error("Error fetching subreddits:", error);
    return [];
  }

  return data || [];
}

export async function getLeadsBySubreddit(
  subredditId: string,
  status: string = "pending",
  limit = 50,
  offset = 0
): Promise<RedditLead[]> {
  // Get lead IDs that have posts in this subreddit
  const { data: postData, error: postError } = await supabase
    .from("reddit_posts")
    .select("lead_id")
    .eq("subreddit_id", subredditId);

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
  // Get lead IDs that have posts in this subreddit
  const { data: postData } = await supabase
    .from("reddit_posts")
    .select("lead_id")
    .eq("subreddit_id", subredditId);

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

