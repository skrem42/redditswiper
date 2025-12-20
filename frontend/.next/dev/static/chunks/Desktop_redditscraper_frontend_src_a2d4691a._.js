(globalThis.TURBOPACK || (globalThis.TURBOPACK = [])).push([typeof document === "object" ? document.currentScript : undefined,
"[project]/Desktop/redditscraper/frontend/src/lib/supabase.ts [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "addKeywordAndScrape",
    ()=>addKeywordAndScrape,
    "addSearchKeyword",
    ()=>addSearchKeyword,
    "deleteKeyword",
    ()=>deleteKeyword,
    "getLeadsByStatus",
    ()=>getLeadsByStatus,
    "getLeadsBySubreddit",
    ()=>getLeadsBySubreddit,
    "getPendingLeads",
    ()=>getPendingLeads,
    "getScrapeJobs",
    ()=>getScrapeJobs,
    "getSearchKeywords",
    ()=>getSearchKeywords,
    "getStats",
    ()=>getStats,
    "getSubredditStats",
    ()=>getSubredditStats,
    "getSubreddits",
    ()=>getSubreddits,
    "getSupabase",
    ()=>getSupabase,
    "queueScrapeJob",
    ()=>queueScrapeJob,
    "supabase",
    ()=>supabase,
    "toggleKeywordActive",
    ()=>toggleKeywordActive,
    "updateKeywordPriority",
    ()=>updateKeywordPriority,
    "updateLeadStatus",
    ()=>updateLeadStatus
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$build$2f$polyfills$2f$process$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = /*#__PURE__*/ __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/node_modules/next/dist/build/polyfills/process.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f40$supabase$2f$supabase$2d$js$2f$dist$2f$index$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$locals$3e$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/node_modules/@supabase/supabase-js/dist/index.mjs [app-client] (ecmascript) <locals>");
;
const supabaseUrl = ("TURBOPACK compile-time value", "https://jmchmbwhnmlednaycxqh.supabase.co") || "https://placeholder.supabase.co";
const supabaseAnonKey = ("TURBOPACK compile-time value", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImptY2htYndobm1sZWRuYXljeHFoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjMzODI4MzYsImV4cCI6MjA3ODk1ODgzNn0.Ux8SqBEj1isHUGIiGh4I-MM54dUb3sd0D7VsRjRKDuU") || "placeholder_key";
// Lazy initialization to avoid build-time errors
let _supabase = null;
function getSupabase() {
    if (!_supabase) {
        _supabase = (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f40$supabase$2f$supabase$2d$js$2f$dist$2f$index$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$locals$3e$__["createClient"])(supabaseUrl, supabaseAnonKey);
    }
    return _supabase;
}
const supabase = (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f40$supabase$2f$supabase$2d$js$2f$dist$2f$index$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$locals$3e$__["createClient"])(supabaseUrl, supabaseAnonKey);
async function getPendingLeads(limit = 50, offset = 0) {
    const { data, error } = await supabase.from("reddit_leads").select("*, reddit_posts(*)").eq("status", "pending").order("karma", {
        ascending: false
    }).range(offset, offset + limit - 1);
    if (error) {
        console.error("Error fetching leads:", error);
        return [];
    }
    return data || [];
}
async function getLeadsByStatus(status, limit = 50, offset = 0) {
    const { data, error } = await supabase.from("reddit_leads").select("*, reddit_posts(*)").eq("status", status).order("updated_at", {
        ascending: false
    }).range(offset, offset + limit - 1);
    if (error) {
        console.error("Error fetching leads:", error);
        return [];
    }
    return data || [];
}
async function updateLeadStatus(leadId, status, notes) {
    const { error: updateError } = await supabase.from("reddit_leads").update({
        status,
        updated_at: new Date().toISOString()
    }).eq("id", leadId);
    if (updateError) {
        console.error("Error updating lead status:", updateError);
        return false;
    }
    // Create decision record
    const { error: decisionError } = await supabase.from("lead_decisions").insert({
        lead_id: leadId,
        decision: status,
        notes
    });
    if (decisionError) {
        console.error("Error creating decision record:", decisionError);
    }
    return true;
}
async function getStats() {
    const { data: leads } = await supabase.from("reddit_leads").select("id, status");
    const { count: postsCount } = await supabase.from("reddit_posts").select("*", {
        count: "exact",
        head: true
    });
    const { count: subredditsCount } = await supabase.from("subreddits").select("*", {
        count: "exact",
        head: true
    });
    const leadsData = leads || [];
    return {
        total_leads: leadsData.length,
        total_posts: postsCount || 0,
        total_subreddits: subredditsCount || 0,
        pending_leads: leadsData.filter((l)=>l.status === "pending").length,
        approved_leads: leadsData.filter((l)=>l.status === "approved").length,
        rejected_leads: leadsData.filter((l)=>l.status === "rejected").length,
        superliked_leads: leadsData.filter((l)=>l.status === "superliked").length
    };
}
async function getSubreddits() {
    const { data, error } = await supabase.from("subreddits").select("*").order("name", {
        ascending: true
    });
    if (error) {
        console.error("Error fetching subreddits:", error);
        return [];
    }
    return data || [];
}
async function getLeadsBySubreddit(subredditId, status = "pending", limit = 50, offset = 0) {
    // Get lead IDs that have posts in this subreddit
    const { data: postData, error: postError } = await supabase.from("reddit_posts").select("lead_id").eq("subreddit_id", subredditId);
    if (postError || !postData) {
        console.error("Error fetching posts:", postError);
        return [];
    }
    const leadIds = [
        ...new Set(postData.map((p)=>p.lead_id))
    ];
    if (leadIds.length === 0) {
        return [];
    }
    const { data, error } = await supabase.from("reddit_leads").select("*, reddit_posts(*)").in("id", leadIds).eq("status", status).order("karma", {
        ascending: false
    }).range(offset, offset + limit - 1);
    if (error) {
        console.error("Error fetching leads:", error);
        return [];
    }
    return data || [];
}
async function getSubredditStats(subredditId) {
    // Get lead IDs that have posts in this subreddit
    const { data: postData } = await supabase.from("reddit_posts").select("lead_id").eq("subreddit_id", subredditId);
    const leadIds = [
        ...new Set((postData || []).map((p)=>p.lead_id))
    ];
    if (leadIds.length === 0) {
        return {
            pending: 0,
            approved: 0,
            rejected: 0,
            superliked: 0
        };
    }
    const { data: leads } = await supabase.from("reddit_leads").select("status").in("id", leadIds);
    const leadsData = leads || [];
    return {
        pending: leadsData.filter((l)=>l.status === "pending").length,
        approved: leadsData.filter((l)=>l.status === "approved").length,
        rejected: leadsData.filter((l)=>l.status === "rejected").length,
        superliked: leadsData.filter((l)=>l.status === "superliked").length
    };
}
async function getSearchKeywords() {
    const { data, error } = await supabase.from("search_keywords").select("*").order("priority", {
        ascending: false
    });
    if (error) {
        console.error("Error fetching keywords:", error);
        return [];
    }
    return data || [];
}
async function addSearchKeyword(keyword, priority = 1000) {
    // Check if keyword already exists
    const { data: existing } = await supabase.from("search_keywords").select("*").eq("keyword", keyword.toLowerCase().trim()).single();
    if (existing) {
        // Update priority if it exists
        const { data, error } = await supabase.from("search_keywords").update({
            priority,
            is_active: true,
            updated_at: new Date().toISOString()
        }).eq("id", existing.id).select().single();
        if (error) {
            console.error("Error updating keyword:", error);
            return null;
        }
        return data;
    }
    // Insert new keyword
    const { data, error } = await supabase.from("search_keywords").insert({
        keyword: keyword.toLowerCase().trim(),
        priority,
        is_active: true
    }).select().single();
    if (error) {
        console.error("Error adding keyword:", error);
        return null;
    }
    return data;
}
async function updateKeywordPriority(keywordId, priority) {
    const { error } = await supabase.from("search_keywords").update({
        priority,
        updated_at: new Date().toISOString()
    }).eq("id", keywordId);
    if (error) {
        console.error("Error updating priority:", error);
        return false;
    }
    return true;
}
async function toggleKeywordActive(keywordId, isActive) {
    const { error } = await supabase.from("search_keywords").update({
        is_active: isActive,
        updated_at: new Date().toISOString()
    }).eq("id", keywordId);
    if (error) {
        console.error("Error toggling keyword:", error);
        return false;
    }
    return true;
}
async function deleteKeyword(keywordId) {
    const { error } = await supabase.from("search_keywords").delete().eq("id", keywordId);
    if (error) {
        console.error("Error deleting keyword:", error);
        return false;
    }
    return true;
}
async function getScrapeJobs(limit = 20) {
    const { data, error } = await supabase.from("scrape_jobs").select("*").order("created_at", {
        ascending: false
    }).limit(limit);
    if (error) {
        console.error("Error fetching scrape jobs:", error);
        return [];
    }
    return data || [];
}
async function queueScrapeJob(keyword, keywordId, priority = 1000) {
    const { data, error } = await supabase.from("scrape_jobs").insert({
        keyword: keyword.toLowerCase().trim(),
        keyword_id: keywordId || null,
        priority,
        status: "pending"
    }).select().single();
    if (error) {
        console.error("Error queuing scrape job:", error);
        return null;
    }
    return data;
}
async function addKeywordAndScrape(keyword) {
    // Add keyword with high priority
    const savedKeyword = await addSearchKeyword(keyword, 1000);
    if (!savedKeyword) {
        return {
            keyword: null,
            job: null
        };
    }
    // Queue a scrape job for this keyword
    const job = await queueScrapeJob(keyword, savedKeyword.id, 1000);
    return {
        keyword: savedKeyword,
        job
    };
}
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "SwipeCard",
    ()=>SwipeCard
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$render$2f$components$2f$motion$2f$proxy$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/node_modules/framer-motion/dist/es/render/components/motion/proxy.mjs [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$value$2f$use$2d$motion$2d$value$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/node_modules/framer-motion/dist/es/value/use-motion-value.mjs [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$value$2f$use$2d$transform$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/node_modules/framer-motion/dist/es/value/use-transform.mjs [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$components$2f$AnimatePresence$2f$index$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/node_modules/framer-motion/dist/es/components/AnimatePresence/index.mjs [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$x$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__X$3e$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/node_modules/lucide-react/dist/esm/icons/x.js [app-client] (ecmascript) <export default as X>");
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$heart$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Heart$3e$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/node_modules/lucide-react/dist/esm/icons/heart.js [app-client] (ecmascript) <export default as Heart>");
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$external$2d$link$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__ExternalLink$3e$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/node_modules/lucide-react/dist/esm/icons/external-link.js [app-client] (ecmascript) <export default as ExternalLink>");
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$chevron$2d$left$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__ChevronLeft$3e$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/node_modules/lucide-react/dist/esm/icons/chevron-left.js [app-client] (ecmascript) <export default as ChevronLeft>");
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$chevron$2d$right$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__ChevronRight$3e$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/node_modules/lucide-react/dist/esm/icons/chevron-right.js [app-client] (ecmascript) <export default as ChevronRight>");
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$trending$2d$up$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__TrendingUp$3e$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/node_modules/lucide-react/dist/esm/icons/trending-up.js [app-client] (ecmascript) <export default as TrendingUp>");
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$clock$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Clock$3e$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/node_modules/lucide-react/dist/esm/icons/clock.js [app-client] (ecmascript) <export default as Clock>");
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$file$2d$text$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__FileText$3e$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/node_modules/lucide-react/dist/esm/icons/file-text.js [app-client] (ecmascript) <export default as FileText>");
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$star$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Star$3e$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/node_modules/lucide-react/dist/esm/icons/star.js [app-client] (ecmascript) <export default as Star>");
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$thumbs$2d$up$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__ThumbsUp$3e$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/node_modules/lucide-react/dist/esm/icons/thumbs-up.js [app-client] (ecmascript) <export default as ThumbsUp>");
;
var _s = __turbopack_context__.k.signature();
"use client";
;
;
;
function SwipeCard({ lead, onSwipe, onSuperLike, isActive }) {
    _s();
    const [exitDirection, setExitDirection] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(null);
    const [lightboxIndex, setLightboxIndex] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(null);
    const x = (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$value$2f$use$2d$motion$2d$value$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useMotionValue"])(0);
    const rotate = (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$value$2f$use$2d$transform$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useTransform"])(x, [
        -300,
        0,
        300
    ], [
        -15,
        0,
        15
    ]);
    const opacity = (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$value$2f$use$2d$transform$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useTransform"])(x, [
        -300,
        -100,
        0,
        100,
        300
    ], [
        0.5,
        1,
        1,
        1,
        0.5
    ]);
    // Overlay indicators
    const rejectOpacity = (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$value$2f$use$2d$transform$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useTransform"])(x, [
        -150,
        0
    ], [
        1,
        0
    ]);
    const approveOpacity = (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$value$2f$use$2d$transform$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useTransform"])(x, [
        0,
        150
    ], [
        0,
        1
    ]);
    // Extract and analyze links - check bio, extracted_links, and post content
    const linkAnalysis = (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useMemo"])({
        "SwipeCard.useMemo[linkAnalysis]": ()=>{
            const links = [
                ...lead.extracted_links || []
            ];
            const urlRegex = /https?:\/\/[^\s<>"{}|\\^`\[\]]+/gi;
            const ofUsernameRegex = /onlyfans\.com\/[\w\-.]+/gi;
            const extractUrls = {
                "SwipeCard.useMemo[linkAnalysis].extractUrls": (text)=>{
                    if (!text) return;
                    const urlMatches = text.match(urlRegex) || [];
                    urlMatches.forEach({
                        "SwipeCard.useMemo[linkAnalysis].extractUrls": (l)=>{
                            if (!links.includes(l)) links.push(l);
                        }
                    }["SwipeCard.useMemo[linkAnalysis].extractUrls"]);
                    const ofMatches = text.match(ofUsernameRegex) || [];
                    ofMatches.forEach({
                        "SwipeCard.useMemo[linkAnalysis].extractUrls": (m)=>{
                            const fullUrl = m.startsWith('http') ? m : `https://${m}`;
                            if (!links.includes(fullUrl)) links.push(fullUrl);
                        }
                    }["SwipeCard.useMemo[linkAnalysis].extractUrls"]);
                }
            }["SwipeCard.useMemo[linkAnalysis].extractUrls"];
            extractUrls(lead.bio || '');
            if (lead.reddit_posts) {
                lead.reddit_posts.forEach({
                    "SwipeCard.useMemo[linkAnalysis]": (post)=>{
                        extractUrls(post.title || '');
                        extractUrls(post.content || '');
                    }
                }["SwipeCard.useMemo[linkAnalysis]"]);
            }
            let ofLinks = links.filter({
                "SwipeCard.useMemo[linkAnalysis].ofLinks": (l)=>l.toLowerCase().includes("onlyfans.com")
            }["SwipeCard.useMemo[linkAnalysis].ofLinks"]);
            const bioMentionsOF = lead.bio && /\b(onlyfans|only\s*fans|\bof\b)/i.test(lead.bio);
            const likelyOFLink = `https://onlyfans.com/${lead.reddit_username.toLowerCase()}`;
            if (ofLinks.length === 0 && bioMentionsOF) {
                ofLinks = [
                    likelyOFLink
                ];
            }
            const hasOF = ofLinks.length > 0;
            const hasTracking = ofLinks.some({
                "SwipeCard.useMemo[linkAnalysis].hasTracking": (l)=>/\/c\d+/i.test(l)
            }["SwipeCard.useMemo[linkAnalysis].hasTracking"]);
            const bioIndicatesOF = bioMentionsOF && ofLinks[0] === likelyOFLink;
            const linktreeLinks = links.filter({
                "SwipeCard.useMemo[linkAnalysis].linktreeLinks": (l)=>/linktr\.ee|beacons\.ai|allmylinks|solo\.to|linkr\.bio/i.test(l)
            }["SwipeCard.useMemo[linkAnalysis].linktreeLinks"]);
            const hasLinktree = linktreeLinks.length > 0;
            const socialLinks = links.filter({
                "SwipeCard.useMemo[linkAnalysis].socialLinks": (l)=>/instagram|twitter|x\.com|tiktok|snapchat|telegram/i.test(l)
            }["SwipeCard.useMemo[linkAnalysis].socialLinks"]);
            const hasSocials = socialLinks.length > 0;
            return {
                ofLinks,
                hasOF,
                hasTracking,
                linktreeLinks,
                hasLinktree,
                socialLinks,
                hasSocials,
                allLinks: links,
                bioIndicatesOF
            };
        }
    }["SwipeCard.useMemo[linkAnalysis]"], [
        lead.extracted_links,
        lead.bio,
        lead.reddit_posts,
        lead.reddit_username
    ]);
    // Get unique media for the grid
    const mediaUrls = (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useMemo"])({
        "SwipeCard.useMemo[mediaUrls]": ()=>{
            if (!lead.reddit_posts) return [];
            const allUrls = lead.reddit_posts.flatMap({
                "SwipeCard.useMemo[mediaUrls].allUrls": (p)=>p.media_urls || []
            }["SwipeCard.useMemo[mediaUrls].allUrls"]);
            const unique = [
                ...new Set(allUrls)
            ];
            for(let i = unique.length - 1; i > 0; i--){
                const j = Math.floor(Math.random() * (i + 1));
                [unique[i], unique[j]] = [
                    unique[j],
                    unique[i]
                ];
            }
            return unique.slice(0, 6);
        }
    }["SwipeCard.useMemo[mediaUrls]"], [
        lead.reddit_posts
    ]);
    // Stats calculations
    const stats = (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useMemo"])({
        "SwipeCard.useMemo[stats]": ()=>{
            const accountDays = lead.account_created_at ? Math.floor((Date.now() - new Date(lead.account_created_at).getTime()) / (1000 * 60 * 60 * 24)) : 0;
            let accountAge = "Unknown";
            if (accountDays > 0) {
                if (accountDays < 30) accountAge = `${accountDays}d`;
                else if (accountDays < 365) accountAge = `${Math.floor(accountDays / 30)}mo`;
                else accountAge = `${(accountDays / 365).toFixed(1)}yr`;
            }
            // Use posting_frequency from scraper if available, otherwise calculate
            let postsPerDay;
            if (lead.posting_frequency !== null && lead.posting_frequency !== undefined) {
                postsPerDay = Number(lead.posting_frequency).toFixed(2);
            } else if (accountDays > 0 && lead.total_posts > 0) {
                postsPerDay = (lead.total_posts / accountDays).toFixed(2);
            } else {
                postsPerDay = "—";
            }
            // Calculate average upvotes from scraped posts
            let avgUpvotes;
            if (lead.reddit_posts && lead.reddit_posts.length > 0) {
                const totalUpvotes = lead.reddit_posts.reduce({
                    "SwipeCard.useMemo[stats].totalUpvotes": (sum, post)=>sum + (post.upvotes || 0)
                }["SwipeCard.useMemo[stats].totalUpvotes"], 0);
                const avg = totalUpvotes / lead.reddit_posts.length;
                if (avg >= 1000) {
                    avgUpvotes = `${(avg / 1000).toFixed(1)}k`;
                } else {
                    avgUpvotes = Math.round(avg).toString();
                }
            } else {
                avgUpvotes = "—";
            }
            return {
                accountAge,
                accountDays,
                postsPerDay,
                avgUpvotes
            };
        }
    }["SwipeCard.useMemo[stats]"], [
        lead.account_created_at,
        lead.total_posts,
        lead.posting_frequency,
        lead.reddit_posts
    ]);
    const handleDragEnd = (_, info)=>{
        const threshold = 150;
        if (info.offset.x > threshold) {
            setExitDirection("right");
            onSwipe("right");
        } else if (info.offset.x < -threshold) {
            setExitDirection("left");
            onSwipe("left");
        }
    };
    const handleButtonSwipe = (direction)=>{
        setExitDirection(direction);
        onSwipe(direction);
    };
    const handleSuperLike = ()=>{
        if (onSuperLike) {
            setExitDirection("up");
            onSuperLike();
        }
    };
    // Keyboard controls
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "SwipeCard.useEffect": ()=>{
            if (!isActive) return;
            const handleKeyDown = {
                "SwipeCard.useEffect.handleKeyDown": (e)=>{
                    // Lightbox navigation
                    if (lightboxIndex !== null) {
                        if (e.key === "Escape") {
                            setLightboxIndex(null);
                        } else if (e.key === "ArrowLeft" && lightboxIndex > 0) {
                            setLightboxIndex(lightboxIndex - 1);
                        } else if (e.key === "ArrowRight" && lightboxIndex < mediaUrls.length - 1) {
                            setLightboxIndex(lightboxIndex + 1);
                        }
                        return;
                    }
                    // Card swipe controls
                    if (e.key === "ArrowLeft" || e.key === "a") {
                        handleButtonSwipe("left");
                    } else if (e.key === "ArrowRight" || e.key === "d") {
                        handleButtonSwipe("right");
                    } else if (e.key === "ArrowUp" || e.key === "w" || e.key === "s") {
                        handleSuperLike();
                    }
                }
            }["SwipeCard.useEffect.handleKeyDown"];
            window.addEventListener("keydown", handleKeyDown);
            return ({
                "SwipeCard.useEffect": ()=>window.removeEventListener("keydown", handleKeyDown)
            })["SwipeCard.useEffect"];
        }
    }["SwipeCard.useEffect"], [
        isActive,
        lightboxIndex,
        mediaUrls.length,
        onSuperLike
    ]);
    const exitVariants = {
        left: {
            x: -500,
            rotate: -30,
            opacity: 0,
            transition: {
                duration: 0.4,
                ease: "easeOut"
            }
        },
        right: {
            x: 500,
            rotate: 30,
            opacity: 0,
            transition: {
                duration: 0.4,
                ease: "easeOut"
            }
        },
        up: {
            y: -500,
            scale: 1.1,
            opacity: 0,
            transition: {
                duration: 0.4,
                ease: "easeOut"
            }
        }
    };
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["Fragment"], {
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$render$2f$components$2f$motion$2f$proxy$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["motion"].div, {
                className: "absolute inset-0 flex items-center justify-center",
                initial: {
                    scale: 0.95,
                    opacity: 0
                },
                animate: {
                    scale: 1,
                    opacity: 1
                },
                exit: exitDirection ? exitVariants[exitDirection] : {
                    opacity: 0,
                    scale: 0.8
                },
                transition: {
                    duration: 0.3
                },
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$render$2f$components$2f$motion$2f$proxy$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["motion"].div, {
                    className: "relative w-full max-w-xl bg-card rounded-2xl card-shadow overflow-hidden cursor-grab active:cursor-grabbing",
                    style: {
                        x,
                        rotate,
                        opacity
                    },
                    drag: isActive ? "x" : false,
                    dragConstraints: {
                        left: 0,
                        right: 0
                    },
                    dragElastic: 0.7,
                    onDragEnd: handleDragEnd,
                    whileTap: {
                        scale: 0.98
                    },
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$render$2f$components$2f$motion$2f$proxy$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["motion"].div, {
                            className: "absolute top-4 left-4 z-20 px-4 py-2 bg-destructive/90 rounded-lg text-white font-bold text-lg rotate-[-15deg] border-2 border-white",
                            style: {
                                opacity: rejectOpacity
                            },
                            children: "NOPE"
                        }, void 0, false, {
                            fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                            lineNumber: 208,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$render$2f$components$2f$motion$2f$proxy$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["motion"].div, {
                            className: "absolute top-4 right-4 z-20 px-4 py-2 bg-success/90 rounded-lg text-white font-bold text-lg rotate-[15deg] border-2 border-white",
                            style: {
                                opacity: approveOpacity
                            },
                            children: "YES!"
                        }, void 0, false, {
                            fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                            lineNumber: 214,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "max-h-[80vh] overflow-y-auto",
                            onPointerDownCapture: (e)=>e.stopPropagation(),
                            children: [
                                mediaUrls.length > 0 && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    className: "p-2 bg-black/40",
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                            className: "grid grid-cols-2 gap-2",
                                            children: mediaUrls.slice(0, 4).map((url, i)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                                    onClick: ()=>setLightboxIndex(i),
                                                    className: "relative aspect-[4/5] rounded-xl overflow-hidden bg-muted group cursor-pointer",
                                                    children: [
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("img", {
                                                            src: url,
                                                            alt: `Preview ${i + 1}`,
                                                            className: "w-full h-full object-cover group-hover:scale-105 transition-transform duration-300",
                                                            loading: "lazy"
                                                        }, void 0, false, {
                                                            fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                                            lineNumber: 236,
                                                            columnNumber: 23
                                                        }, this),
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                            className: "absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center",
                                                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                                className: "text-white/0 group-hover:text-white/90 text-sm font-medium transition-colors",
                                                                children: "Click to preview"
                                                            }, void 0, false, {
                                                                fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                                                lineNumber: 243,
                                                                columnNumber: 25
                                                            }, this)
                                                        }, void 0, false, {
                                                            fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                                            lineNumber: 242,
                                                            columnNumber: 23
                                                        }, this)
                                                    ]
                                                }, i, true, {
                                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                                    lineNumber: 231,
                                                    columnNumber: 21
                                                }, this))
                                        }, void 0, false, {
                                            fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                            lineNumber: 229,
                                            columnNumber: 17
                                        }, this),
                                        mediaUrls.length > 4 && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                            className: "text-center text-xs text-muted-foreground mt-2",
                                            children: [
                                                "+",
                                                mediaUrls.length - 4,
                                                " more images"
                                            ]
                                        }, void 0, true, {
                                            fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                            lineNumber: 251,
                                            columnNumber: 19
                                        }, this)
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                    lineNumber: 228,
                                    columnNumber: 15
                                }, this),
                                mediaUrls.length === 0 && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    className: "h-32 bg-gradient-to-br from-primary/20 via-accent/20 to-purple-500/20 flex items-center justify-center",
                                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        className: "text-muted-foreground text-sm",
                                        children: "No media available"
                                    }, void 0, false, {
                                        fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                        lineNumber: 261,
                                        columnNumber: 17
                                    }, this)
                                }, void 0, false, {
                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                    lineNumber: 260,
                                    columnNumber: 15
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    className: "grid grid-cols-4 gap-1 p-3 bg-gradient-to-r from-primary/10 via-accent/10 to-purple-500/10 border-y border-border/50",
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                            className: "flex flex-col items-center justify-center text-center",
                                            children: [
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$trending$2d$up$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__TrendingUp$3e$__["TrendingUp"], {
                                                    size: 14,
                                                    className: "text-emerald-400 mb-1"
                                                }, void 0, false, {
                                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                                    lineNumber: 268,
                                                    columnNumber: 17
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                    className: "text-sm font-bold text-foreground",
                                                    children: lead.karma.toLocaleString()
                                                }, void 0, false, {
                                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                                    lineNumber: 269,
                                                    columnNumber: 17
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                    className: "text-[9px] text-muted-foreground uppercase tracking-wide",
                                                    children: "Karma"
                                                }, void 0, false, {
                                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                                    lineNumber: 270,
                                                    columnNumber: 17
                                                }, this)
                                            ]
                                        }, void 0, true, {
                                            fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                            lineNumber: 267,
                                            columnNumber: 15
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                            className: "flex flex-col items-center justify-center text-center border-l border-border/30",
                                            children: [
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$file$2d$text$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__FileText$3e$__["FileText"], {
                                                    size: 14,
                                                    className: "text-sky-400 mb-1"
                                                }, void 0, false, {
                                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                                    lineNumber: 273,
                                                    columnNumber: 17
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                    className: "text-sm font-bold text-foreground",
                                                    children: stats.postsPerDay
                                                }, void 0, false, {
                                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                                    lineNumber: 274,
                                                    columnNumber: 17
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                    className: "text-[9px] text-muted-foreground uppercase tracking-wide",
                                                    children: "Posts/Day"
                                                }, void 0, false, {
                                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                                    lineNumber: 275,
                                                    columnNumber: 17
                                                }, this)
                                            ]
                                        }, void 0, true, {
                                            fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                            lineNumber: 272,
                                            columnNumber: 15
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                            className: "flex flex-col items-center justify-center text-center border-l border-border/30",
                                            children: [
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$thumbs$2d$up$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__ThumbsUp$3e$__["ThumbsUp"], {
                                                    size: 14,
                                                    className: "text-rose-400 mb-1"
                                                }, void 0, false, {
                                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                                    lineNumber: 278,
                                                    columnNumber: 17
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                    className: "text-sm font-bold text-foreground",
                                                    children: stats.avgUpvotes
                                                }, void 0, false, {
                                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                                    lineNumber: 279,
                                                    columnNumber: 17
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                    className: "text-[9px] text-muted-foreground uppercase tracking-wide",
                                                    children: "Avg Upvotes"
                                                }, void 0, false, {
                                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                                    lineNumber: 280,
                                                    columnNumber: 17
                                                }, this)
                                            ]
                                        }, void 0, true, {
                                            fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                            lineNumber: 277,
                                            columnNumber: 15
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                            className: "flex flex-col items-center justify-center text-center border-l border-border/30",
                                            children: [
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$clock$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Clock$3e$__["Clock"], {
                                                    size: 14,
                                                    className: "text-amber-400 mb-1"
                                                }, void 0, false, {
                                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                                    lineNumber: 283,
                                                    columnNumber: 17
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                    className: "text-sm font-bold text-foreground",
                                                    children: stats.accountAge
                                                }, void 0, false, {
                                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                                    lineNumber: 284,
                                                    columnNumber: 17
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                    className: "text-[9px] text-muted-foreground uppercase tracking-wide",
                                                    children: "Age"
                                                }, void 0, false, {
                                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                                    lineNumber: 285,
                                                    columnNumber: 17
                                                }, this)
                                            ]
                                        }, void 0, true, {
                                            fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                            lineNumber: 282,
                                            columnNumber: 15
                                        }, this)
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                    lineNumber: 266,
                                    columnNumber: 13
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    className: "grid grid-cols-4 gap-2 p-3 bg-secondary/20",
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                            className: `rounded-lg p-2 text-center ${linkAnalysis.hasOF ? linkAnalysis.bioIndicatesOF ? 'bg-amber-500/20 border border-amber-500/40' : 'bg-sky-500/20 border border-sky-500/40' : 'bg-muted/30'}`,
                                            children: [
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                    className: "text-lg",
                                                    children: "🔥"
                                                }, void 0, false, {
                                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                                    lineNumber: 298,
                                                    columnNumber: 17
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                    className: `text-[10px] font-medium ${linkAnalysis.hasOF ? linkAnalysis.bioIndicatesOF ? 'text-amber-400' : 'text-sky-400' : 'text-muted-foreground'}`,
                                                    children: linkAnalysis.hasOF ? linkAnalysis.bioIndicatesOF ? 'OF Likely' : 'OF Found' : 'No OF'
                                                }, void 0, false, {
                                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                                    lineNumber: 299,
                                                    columnNumber: 17
                                                }, this)
                                            ]
                                        }, void 0, true, {
                                            fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                            lineNumber: 291,
                                            columnNumber: 15
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                            className: `rounded-lg p-2 text-center ${linkAnalysis.hasTracking ? 'bg-amber-500/20 border border-amber-500/40' : linkAnalysis.hasOF ? 'bg-emerald-500/20 border border-emerald-500/40' : 'bg-muted/30'}`,
                                            children: [
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                    className: "text-lg",
                                                    children: linkAnalysis.hasTracking ? '🏷️' : linkAnalysis.hasOF ? '✓' : '—'
                                                }, void 0, false, {
                                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                                    lineNumber: 313,
                                                    columnNumber: 17
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                    className: `text-[10px] font-medium ${linkAnalysis.hasTracking ? 'text-amber-400' : linkAnalysis.hasOF ? 'text-emerald-400' : 'text-muted-foreground'}`,
                                                    children: linkAnalysis.hasTracking ? 'Agency?' : linkAnalysis.hasOF ? 'No Track' : '—'
                                                }, void 0, false, {
                                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                                    lineNumber: 314,
                                                    columnNumber: 17
                                                }, this)
                                            ]
                                        }, void 0, true, {
                                            fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                            lineNumber: 308,
                                            columnNumber: 15
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                            className: `rounded-lg p-2 text-center ${linkAnalysis.hasLinktree ? 'bg-emerald-500/20 border border-emerald-500/40' : 'bg-muted/30'}`,
                                            children: [
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                    className: "text-lg",
                                                    children: "🌳"
                                                }, void 0, false, {
                                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                                    lineNumber: 322,
                                                    columnNumber: 17
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                    className: `text-[10px] font-medium ${linkAnalysis.hasLinktree ? 'text-emerald-400' : 'text-muted-foreground'}`,
                                                    children: linkAnalysis.hasLinktree ? 'Linktree' : 'No Link'
                                                }, void 0, false, {
                                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                                    lineNumber: 323,
                                                    columnNumber: 17
                                                }, this)
                                            ]
                                        }, void 0, true, {
                                            fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                            lineNumber: 321,
                                            columnNumber: 15
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                            className: `rounded-lg p-2 text-center ${linkAnalysis.hasSocials ? 'bg-purple-500/20 border border-purple-500/40' : 'bg-muted/30'}`,
                                            children: [
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                    className: "text-lg",
                                                    children: "📱"
                                                }, void 0, false, {
                                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                                    lineNumber: 329,
                                                    columnNumber: 17
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                    className: `text-[10px] font-medium ${linkAnalysis.hasSocials ? 'text-purple-400' : 'text-muted-foreground'}`,
                                                    children: linkAnalysis.hasSocials ? `${linkAnalysis.socialLinks.length} Social` : 'None'
                                                }, void 0, false, {
                                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                                    lineNumber: 330,
                                                    columnNumber: 17
                                                }, this)
                                            ]
                                        }, void 0, true, {
                                            fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                            lineNumber: 328,
                                            columnNumber: 15
                                        }, this)
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                    lineNumber: 290,
                                    columnNumber: 13
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    className: "p-4 space-y-3",
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                            className: "flex items-center gap-3",
                                            children: [
                                                lead.avatar_url ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("img", {
                                                    src: lead.avatar_url,
                                                    alt: lead.reddit_username,
                                                    className: "w-12 h-12 rounded-full object-cover border-2 border-primary/30"
                                                }, void 0, false, {
                                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                                    lineNumber: 341,
                                                    columnNumber: 19
                                                }, this) : /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                    className: "w-12 h-12 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center text-xl font-bold text-white",
                                                    children: lead.reddit_username.charAt(0).toUpperCase()
                                                }, void 0, false, {
                                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                                    lineNumber: 347,
                                                    columnNumber: 19
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                    className: "flex-1 min-w-0",
                                                    children: [
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                            className: "flex items-center gap-2",
                                                            children: [
                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h2", {
                                                                    className: "text-lg font-bold text-foreground truncate",
                                                                    children: [
                                                                        "u/",
                                                                        lead.reddit_username
                                                                    ]
                                                                }, void 0, true, {
                                                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                                                    lineNumber: 353,
                                                                    columnNumber: 21
                                                                }, this),
                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("a", {
                                                                    href: lead.profile_url,
                                                                    target: "_blank",
                                                                    rel: "noopener noreferrer",
                                                                    className: "text-muted-foreground hover:text-accent transition-colors",
                                                                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$external$2d$link$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__ExternalLink$3e$__["ExternalLink"], {
                                                                        size: 14
                                                                    }, void 0, false, {
                                                                        fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                                                        lineNumber: 362,
                                                                        columnNumber: 23
                                                                    }, this)
                                                                }, void 0, false, {
                                                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                                                    lineNumber: 356,
                                                                    columnNumber: 21
                                                                }, this)
                                                            ]
                                                        }, void 0, true, {
                                                            fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                                            lineNumber: 352,
                                                            columnNumber: 19
                                                        }, this),
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                            className: "text-xs text-muted-foreground",
                                                            children: [
                                                                lead.total_posts,
                                                                " total posts"
                                                            ]
                                                        }, void 0, true, {
                                                            fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                                            lineNumber: 365,
                                                            columnNumber: 19
                                                        }, this)
                                                    ]
                                                }, void 0, true, {
                                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                                    lineNumber: 351,
                                                    columnNumber: 17
                                                }, this)
                                            ]
                                        }, void 0, true, {
                                            fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                            lineNumber: 339,
                                            columnNumber: 15
                                        }, this),
                                        lead.bio && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                            className: "text-sm text-muted-foreground bg-secondary/30 rounded-lg p-3",
                                            children: lead.bio
                                        }, void 0, false, {
                                            fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                            lineNumber: 373,
                                            columnNumber: 17
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                            className: "flex flex-wrap gap-2",
                                            children: [
                                                linkAnalysis.ofLinks.length > 0 ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("a", {
                                                    href: linkAnalysis.ofLinks[0],
                                                    target: "_blank",
                                                    rel: "noopener noreferrer",
                                                    className: `flex items-center gap-2 px-4 py-2.5 rounded-lg font-medium transition-colors shadow-lg text-sm ${linkAnalysis.bioIndicatesOF ? 'bg-amber-500 text-white hover:bg-amber-600 shadow-amber-500/20' : 'bg-sky-500 text-white hover:bg-sky-600 shadow-sky-500/20'}`,
                                                    children: [
                                                        "🔥 ",
                                                        linkAnalysis.bioIndicatesOF ? 'Check OnlyFans' : 'View OnlyFans',
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$external$2d$link$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__ExternalLink$3e$__["ExternalLink"], {
                                                            size: 14
                                                        }, void 0, false, {
                                                            fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                                            lineNumber: 393,
                                                            columnNumber: 21
                                                        }, this)
                                                    ]
                                                }, void 0, true, {
                                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                                    lineNumber: 382,
                                                    columnNumber: 19
                                                }, this) : // No OF link found - show button to check their bio/profile for links
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("a", {
                                                    href: lead.profile_url,
                                                    target: "_blank",
                                                    rel: "noopener noreferrer",
                                                    className: "flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-pink-500 to-rose-500 text-white rounded-lg font-medium hover:from-pink-600 hover:to-rose-600 transition-colors shadow-lg shadow-pink-500/20 text-sm",
                                                    children: [
                                                        "🔍 Check Bio for Links",
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$external$2d$link$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__ExternalLink$3e$__["ExternalLink"], {
                                                            size: 14
                                                        }, void 0, false, {
                                                            fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                                            lineNumber: 404,
                                                            columnNumber: 21
                                                        }, this)
                                                    ]
                                                }, void 0, true, {
                                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                                    lineNumber: 397,
                                                    columnNumber: 19
                                                }, this),
                                                linkAnalysis.linktreeLinks.length > 0 && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("a", {
                                                    href: linkAnalysis.linktreeLinks[0],
                                                    target: "_blank",
                                                    rel: "noopener noreferrer",
                                                    className: "flex items-center gap-2 px-4 py-2 bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 rounded-lg font-medium hover:bg-emerald-500/30 transition-colors text-sm",
                                                    children: [
                                                        "🌳 Linktree",
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$external$2d$link$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__ExternalLink$3e$__["ExternalLink"], {
                                                            size: 12
                                                        }, void 0, false, {
                                                            fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                                            lineNumber: 417,
                                                            columnNumber: 21
                                                        }, this)
                                                    ]
                                                }, void 0, true, {
                                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                                    lineNumber: 410,
                                                    columnNumber: 19
                                                }, this),
                                                linkAnalysis.ofLinks.length > 0 && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("a", {
                                                    href: lead.profile_url,
                                                    target: "_blank",
                                                    rel: "noopener noreferrer",
                                                    className: "flex items-center gap-2 px-4 py-2 bg-orange-500/20 text-orange-400 border border-orange-500/40 rounded-lg font-medium hover:bg-orange-500/30 transition-colors text-sm",
                                                    children: [
                                                        "Reddit Profile",
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$external$2d$link$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__ExternalLink$3e$__["ExternalLink"], {
                                                            size: 12
                                                        }, void 0, false, {
                                                            fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                                            lineNumber: 430,
                                                            columnNumber: 21
                                                        }, this)
                                                    ]
                                                }, void 0, true, {
                                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                                    lineNumber: 423,
                                                    columnNumber: 19
                                                }, this)
                                            ]
                                        }, void 0, true, {
                                            fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                            lineNumber: 379,
                                            columnNumber: 15
                                        }, this)
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                    lineNumber: 337,
                                    columnNumber: 13
                                }, this)
                            ]
                        }, void 0, true, {
                            fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                            lineNumber: 222,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "flex items-center justify-center gap-4 p-4 bg-card border-t border-border",
                            onPointerDownCapture: (e)=>e.stopPropagation(),
                            children: [
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                    onClick: ()=>handleButtonSwipe("left"),
                                    className: "w-14 h-14 rounded-full bg-destructive/10 border-2 border-destructive text-destructive flex items-center justify-center hover:bg-destructive hover:text-white transition-all btn-glow-red",
                                    title: "Reject (← or A)",
                                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$x$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__X$3e$__["X"], {
                                        size: 24,
                                        strokeWidth: 3
                                    }, void 0, false, {
                                        fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                        lineNumber: 447,
                                        columnNumber: 15
                                    }, this)
                                }, void 0, false, {
                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                    lineNumber: 442,
                                    columnNumber: 13
                                }, this),
                                onSuperLike && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                    onClick: handleSuperLike,
                                    className: "w-12 h-12 rounded-full bg-amber-500/10 border-2 border-amber-500 text-amber-500 flex items-center justify-center hover:bg-amber-500 hover:text-white transition-all shadow-lg shadow-amber-500/20",
                                    title: "Super Like (↑ or S)",
                                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$star$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Star$3e$__["Star"], {
                                        size: 20,
                                        strokeWidth: 2.5,
                                        fill: "currentColor"
                                    }, void 0, false, {
                                        fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                        lineNumber: 457,
                                        columnNumber: 17
                                    }, this)
                                }, void 0, false, {
                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                    lineNumber: 452,
                                    columnNumber: 15
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                    onClick: ()=>handleButtonSwipe("right"),
                                    className: "w-14 h-14 rounded-full bg-success/10 border-2 border-success text-success flex items-center justify-center hover:bg-success hover:text-white transition-all btn-glow-green",
                                    title: "Approve (→ or D)",
                                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$heart$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Heart$3e$__["Heart"], {
                                        size: 24,
                                        strokeWidth: 2.5,
                                        fill: "currentColor"
                                    }, void 0, false, {
                                        fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                        lineNumber: 466,
                                        columnNumber: 15
                                    }, this)
                                }, void 0, false, {
                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                    lineNumber: 461,
                                    columnNumber: 13
                                }, this)
                            ]
                        }, void 0, true, {
                            fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                            lineNumber: 438,
                            columnNumber: 11
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                    lineNumber: 198,
                    columnNumber: 9
                }, this)
            }, void 0, false, {
                fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                lineNumber: 191,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$components$2f$AnimatePresence$2f$index$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["AnimatePresence"], {
                children: lightboxIndex !== null && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$render$2f$components$2f$motion$2f$proxy$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["motion"].div, {
                    initial: {
                        opacity: 0
                    },
                    animate: {
                        opacity: 1
                    },
                    exit: {
                        opacity: 0
                    },
                    className: "fixed inset-0 z-50 bg-black/95 flex items-center justify-center",
                    onClick: ()=>setLightboxIndex(null),
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                            onClick: (e)=>{
                                e.stopPropagation();
                                setLightboxIndex(null);
                            },
                            className: "absolute top-4 right-4 z-10 p-3 rounded-full bg-white/20 hover:bg-white/30 transition-colors",
                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$x$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__X$3e$__["X"], {
                                size: 28,
                                className: "text-white"
                            }, void 0, false, {
                                fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                lineNumber: 490,
                                columnNumber: 15
                            }, this)
                        }, void 0, false, {
                            fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                            lineNumber: 483,
                            columnNumber: 13
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "absolute top-4 left-4 text-white/80 text-sm font-medium bg-black/40 px-3 py-1 rounded-full",
                            children: [
                                lightboxIndex + 1,
                                " / ",
                                mediaUrls.length
                            ]
                        }, void 0, true, {
                            fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                            lineNumber: 494,
                            columnNumber: 13
                        }, this),
                        lightboxIndex > 0 && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                            onClick: (e)=>{
                                e.stopPropagation();
                                setLightboxIndex(lightboxIndex - 1);
                            },
                            className: "absolute left-4 top-1/2 -translate-y-1/2 p-3 rounded-full bg-white/20 hover:bg-white/30 transition-colors",
                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$chevron$2d$left$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__ChevronLeft$3e$__["ChevronLeft"], {
                                size: 32,
                                className: "text-white"
                            }, void 0, false, {
                                fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                lineNumber: 507,
                                columnNumber: 17
                            }, this)
                        }, void 0, false, {
                            fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                            lineNumber: 500,
                            columnNumber: 15
                        }, this),
                        lightboxIndex < mediaUrls.length - 1 && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                            onClick: (e)=>{
                                e.stopPropagation();
                                setLightboxIndex(lightboxIndex + 1);
                            },
                            className: "absolute right-4 top-1/2 -translate-y-1/2 p-3 rounded-full bg-white/20 hover:bg-white/30 transition-colors",
                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$chevron$2d$right$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__ChevronRight$3e$__["ChevronRight"], {
                                size: 32,
                                className: "text-white"
                            }, void 0, false, {
                                fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                lineNumber: 518,
                                columnNumber: 17
                            }, this)
                        }, void 0, false, {
                            fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                            lineNumber: 511,
                            columnNumber: 15
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$render$2f$components$2f$motion$2f$proxy$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["motion"].img, {
                            initial: {
                                scale: 0.9,
                                opacity: 0
                            },
                            animate: {
                                scale: 1,
                                opacity: 1
                            },
                            exit: {
                                scale: 0.9,
                                opacity: 0
                            },
                            src: mediaUrls[lightboxIndex],
                            alt: `Full preview ${lightboxIndex + 1}`,
                            className: "max-h-[90vh] max-w-[90vw] object-contain rounded-lg",
                            onClick: (e)=>e.stopPropagation()
                        }, lightboxIndex, false, {
                            fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                            lineNumber: 523,
                            columnNumber: 13
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "absolute bottom-4 left-1/2 -translate-x-1/2 text-white/60 text-xs flex items-center gap-4",
                            children: [
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                    children: "← → Navigate"
                                }, void 0, false, {
                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                    lineNumber: 536,
                                    columnNumber: 15
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                    children: "ESC Close"
                                }, void 0, false, {
                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                                    lineNumber: 537,
                                    columnNumber: 15
                                }, this)
                            ]
                        }, void 0, true, {
                            fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                            lineNumber: 535,
                            columnNumber: 13
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                    lineNumber: 475,
                    columnNumber: 11
                }, this)
            }, void 0, false, {
                fileName: "[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx",
                lineNumber: 473,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true);
}
_s(SwipeCard, "XeI4PqcnNlH7a8iPRPP0AYCTWg8=", false, function() {
    return [
        __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$value$2f$use$2d$motion$2d$value$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useMotionValue"],
        __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$value$2f$use$2d$transform$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useTransform"],
        __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$value$2f$use$2d$transform$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useTransform"],
        __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$value$2f$use$2d$transform$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useTransform"],
        __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$value$2f$use$2d$transform$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useTransform"]
    ];
});
_c = SwipeCard;
var _c;
__turbopack_context__.k.register(_c, "SwipeCard");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/Desktop/redditscraper/frontend/src/components/StatsBar.tsx [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "StatsBar",
    ()=>StatsBar
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$users$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Users$3e$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/node_modules/lucide-react/dist/esm/icons/users.js [app-client] (ecmascript) <export default as Users>");
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$circle$2d$check$2d$big$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__CheckCircle$3e$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/node_modules/lucide-react/dist/esm/icons/circle-check-big.js [app-client] (ecmascript) <export default as CheckCircle>");
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$circle$2d$x$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__XCircle$3e$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/node_modules/lucide-react/dist/esm/icons/circle-x.js [app-client] (ecmascript) <export default as XCircle>");
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$clock$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Clock$3e$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/node_modules/lucide-react/dist/esm/icons/clock.js [app-client] (ecmascript) <export default as Clock>");
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$star$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Star$3e$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/node_modules/lucide-react/dist/esm/icons/star.js [app-client] (ecmascript) <export default as Star>");
"use client";
;
;
function StatsBar({ stats, currentFilter, onFilterChange }) {
    const filters = [
        {
            id: "pending",
            label: "Pending",
            count: stats.pending_leads,
            icon: __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$clock$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Clock$3e$__["Clock"],
            color: "text-yellow-500",
            bgColor: "bg-yellow-500/10",
            borderColor: "border-yellow-500/30"
        },
        {
            id: "superliked",
            label: "Super",
            count: stats.superliked_leads,
            icon: __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$star$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Star$3e$__["Star"],
            color: "text-amber-500",
            bgColor: "bg-amber-500/10",
            borderColor: "border-amber-500/30"
        },
        {
            id: "approved",
            label: "Approved",
            count: stats.approved_leads,
            icon: __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$circle$2d$check$2d$big$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__CheckCircle$3e$__["CheckCircle"],
            color: "text-success",
            bgColor: "bg-success/10",
            borderColor: "border-success/30"
        },
        {
            id: "rejected",
            label: "Rejected",
            count: stats.rejected_leads,
            icon: __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$circle$2d$x$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__XCircle$3e$__["XCircle"],
            color: "text-destructive",
            bgColor: "bg-destructive/10",
            borderColor: "border-destructive/30"
        }
    ];
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "glass rounded-2xl p-4 mb-6",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "flex items-center justify-between mb-4",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "flex items-center gap-2",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$users$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Users$3e$__["Users"], {
                                className: "text-primary",
                                size: 20
                            }, void 0, false, {
                                fileName: "[project]/Desktop/redditscraper/frontend/src/components/StatsBar.tsx",
                                lineNumber: 56,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                className: "text-lg font-semibold",
                                children: [
                                    stats.total_leads.toLocaleString(),
                                    " Total Leads"
                                ]
                            }, void 0, true, {
                                fileName: "[project]/Desktop/redditscraper/frontend/src/components/StatsBar.tsx",
                                lineNumber: 57,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/Desktop/redditscraper/frontend/src/components/StatsBar.tsx",
                        lineNumber: 55,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "text-sm text-muted-foreground",
                        children: [
                            stats.total_posts.toLocaleString(),
                            " posts from",
                            " ",
                            stats.total_subreddits,
                            " subreddits"
                        ]
                    }, void 0, true, {
                        fileName: "[project]/Desktop/redditscraper/frontend/src/components/StatsBar.tsx",
                        lineNumber: 61,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/Desktop/redditscraper/frontend/src/components/StatsBar.tsx",
                lineNumber: 54,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "flex gap-3",
                children: filters.map((filter)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                        onClick: ()=>onFilterChange(filter.id),
                        className: `flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl border transition-all ${currentFilter === filter.id ? `${filter.bgColor} ${filter.borderColor} ${filter.color}` : "bg-secondary/50 border-border text-muted-foreground hover:bg-secondary"}`,
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(filter.icon, {
                                size: 18
                            }, void 0, false, {
                                fileName: "[project]/Desktop/redditscraper/frontend/src/components/StatsBar.tsx",
                                lineNumber: 78,
                                columnNumber: 13
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                className: "font-medium",
                                children: filter.label
                            }, void 0, false, {
                                fileName: "[project]/Desktop/redditscraper/frontend/src/components/StatsBar.tsx",
                                lineNumber: 79,
                                columnNumber: 13
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                className: `px-2 py-0.5 rounded-full text-xs font-bold ${currentFilter === filter.id ? `${filter.bgColor} ${filter.color}` : "bg-muted text-muted-foreground"}`,
                                children: filter.count
                            }, void 0, false, {
                                fileName: "[project]/Desktop/redditscraper/frontend/src/components/StatsBar.tsx",
                                lineNumber: 80,
                                columnNumber: 13
                            }, this)
                        ]
                    }, filter.id, true, {
                        fileName: "[project]/Desktop/redditscraper/frontend/src/components/StatsBar.tsx",
                        lineNumber: 69,
                        columnNumber: 11
                    }, this))
            }, void 0, false, {
                fileName: "[project]/Desktop/redditscraper/frontend/src/components/StatsBar.tsx",
                lineNumber: 67,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/Desktop/redditscraper/frontend/src/components/StatsBar.tsx",
        lineNumber: 53,
        columnNumber: 5
    }, this);
}
_c = StatsBar;
var _c;
__turbopack_context__.k.register(_c, "StatsBar");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/Desktop/redditscraper/frontend/src/components/LeadsList.tsx [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "LeadsList",
    ()=>LeadsList
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$external$2d$link$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__ExternalLink$3e$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/node_modules/lucide-react/dist/esm/icons/external-link.js [app-client] (ecmascript) <export default as ExternalLink>");
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$rotate$2d$ccw$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__RotateCcw$3e$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/node_modules/lucide-react/dist/esm/icons/rotate-ccw.js [app-client] (ecmascript) <export default as RotateCcw>");
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$arrow$2d$left$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__ArrowLeft$3e$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/node_modules/lucide-react/dist/esm/icons/arrow-left.js [app-client] (ecmascript) <export default as ArrowLeft>");
"use client";
;
;
function LeadsList({ leads, onRestore, showRestore = false, onBack, title }) {
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "space-y-4",
        children: [
            onBack && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "flex items-center gap-3 pb-2 border-b border-border",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                        onClick: onBack,
                        className: "flex items-center gap-2 px-4 py-2 rounded-lg bg-secondary hover:bg-secondary/80 text-foreground transition-colors",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$arrow$2d$left$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__ArrowLeft$3e$__["ArrowLeft"], {
                                size: 18
                            }, void 0, false, {
                                fileName: "[project]/Desktop/redditscraper/frontend/src/components/LeadsList.tsx",
                                lineNumber: 24,
                                columnNumber: 13
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                children: "Back to Swiper"
                            }, void 0, false, {
                                fileName: "[project]/Desktop/redditscraper/frontend/src/components/LeadsList.tsx",
                                lineNumber: 25,
                                columnNumber: 13
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/Desktop/redditscraper/frontend/src/components/LeadsList.tsx",
                        lineNumber: 20,
                        columnNumber: 11
                    }, this),
                    title && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h2", {
                        className: "text-lg font-semibold text-foreground",
                        children: title
                    }, void 0, false, {
                        fileName: "[project]/Desktop/redditscraper/frontend/src/components/LeadsList.tsx",
                        lineNumber: 28,
                        columnNumber: 13
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/Desktop/redditscraper/frontend/src/components/LeadsList.tsx",
                lineNumber: 19,
                columnNumber: 9
            }, this),
            leads.length === 0 ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "text-center py-12 text-muted-foreground",
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                    children: "No leads in this category"
                }, void 0, false, {
                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/LeadsList.tsx",
                    lineNumber: 35,
                    columnNumber: 11
                }, this)
            }, void 0, false, {
                fileName: "[project]/Desktop/redditscraper/frontend/src/components/LeadsList.tsx",
                lineNumber: 34,
                columnNumber: 9
            }, this) : /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "space-y-3 max-h-[60vh] overflow-y-auto pr-2",
                children: leads.map((lead)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "bg-card rounded-xl p-4 flex items-center gap-4 hover:bg-card/80 transition-colors",
                        children: [
                            lead.avatar_url ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("img", {
                                src: lead.avatar_url,
                                alt: lead.reddit_username,
                                className: "w-12 h-12 rounded-full object-cover border border-border"
                            }, void 0, false, {
                                fileName: "[project]/Desktop/redditscraper/frontend/src/components/LeadsList.tsx",
                                lineNumber: 46,
                                columnNumber: 13
                            }, this) : /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "w-12 h-12 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center text-lg font-bold text-white",
                                children: lead.reddit_username.charAt(0).toUpperCase()
                            }, void 0, false, {
                                fileName: "[project]/Desktop/redditscraper/frontend/src/components/LeadsList.tsx",
                                lineNumber: 52,
                                columnNumber: 13
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "flex-1 min-w-0",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "flex items-center gap-2",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                className: "font-medium text-foreground truncate",
                                                children: [
                                                    "u/",
                                                    lead.reddit_username
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/Desktop/redditscraper/frontend/src/components/LeadsList.tsx",
                                                lineNumber: 60,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("a", {
                                                href: lead.profile_url,
                                                target: "_blank",
                                                rel: "noopener noreferrer",
                                                className: "text-muted-foreground hover:text-accent",
                                                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$external$2d$link$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__ExternalLink$3e$__["ExternalLink"], {
                                                    size: 14
                                                }, void 0, false, {
                                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/LeadsList.tsx",
                                                    lineNumber: 69,
                                                    columnNumber: 17
                                                }, this)
                                            }, void 0, false, {
                                                fileName: "[project]/Desktop/redditscraper/frontend/src/components/LeadsList.tsx",
                                                lineNumber: 63,
                                                columnNumber: 15
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/Desktop/redditscraper/frontend/src/components/LeadsList.tsx",
                                        lineNumber: 59,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "flex items-center gap-3 text-xs text-muted-foreground mt-1",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                children: [
                                                    "↑ ",
                                                    lead.karma.toLocaleString()
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/Desktop/redditscraper/frontend/src/components/LeadsList.tsx",
                                                lineNumber: 73,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                children: [
                                                    lead.total_posts,
                                                    " posts"
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/Desktop/redditscraper/frontend/src/components/LeadsList.tsx",
                                                lineNumber: 74,
                                                columnNumber: 15
                                            }, this),
                                            lead.extracted_links.length > 0 && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                className: "text-accent",
                                                children: [
                                                    lead.extracted_links.length,
                                                    " links"
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/Desktop/redditscraper/frontend/src/components/LeadsList.tsx",
                                                lineNumber: 76,
                                                columnNumber: 17
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/Desktop/redditscraper/frontend/src/components/LeadsList.tsx",
                                        lineNumber: 72,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/Desktop/redditscraper/frontend/src/components/LeadsList.tsx",
                                lineNumber: 58,
                                columnNumber: 11
                            }, this),
                            lead.extracted_links.length > 0 && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "hidden md:flex gap-1",
                                children: lead.extracted_links.slice(0, 2).map((link, idx)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("a", {
                                        href: link,
                                        target: "_blank",
                                        rel: "noopener noreferrer",
                                        className: "px-2 py-1 rounded-full bg-accent/10 text-accent text-xs hover:bg-accent/20 transition-colors",
                                        children: link.includes("onlyfans") ? "🔥 OF" : "🔗 Link"
                                    }, idx, false, {
                                        fileName: "[project]/Desktop/redditscraper/frontend/src/components/LeadsList.tsx",
                                        lineNumber: 87,
                                        columnNumber: 17
                                    }, this))
                            }, void 0, false, {
                                fileName: "[project]/Desktop/redditscraper/frontend/src/components/LeadsList.tsx",
                                lineNumber: 85,
                                columnNumber: 13
                            }, this),
                            showRestore && onRestore && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                onClick: ()=>onRestore(lead.id),
                                className: "p-2 rounded-lg bg-secondary hover:bg-secondary/80 text-muted-foreground hover:text-foreground transition-colors",
                                title: "Move back to pending",
                                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$rotate$2d$ccw$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__RotateCcw$3e$__["RotateCcw"], {
                                    size: 16
                                }, void 0, false, {
                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/LeadsList.tsx",
                                    lineNumber: 107,
                                    columnNumber: 15
                                }, this)
                            }, void 0, false, {
                                fileName: "[project]/Desktop/redditscraper/frontend/src/components/LeadsList.tsx",
                                lineNumber: 102,
                                columnNumber: 13
                            }, this)
                        ]
                    }, lead.id, true, {
                        fileName: "[project]/Desktop/redditscraper/frontend/src/components/LeadsList.tsx",
                        lineNumber: 40,
                        columnNumber: 9
                    }, this))
            }, void 0, false, {
                fileName: "[project]/Desktop/redditscraper/frontend/src/components/LeadsList.tsx",
                lineNumber: 38,
                columnNumber: 9
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/Desktop/redditscraper/frontend/src/components/LeadsList.tsx",
        lineNumber: 16,
        columnNumber: 5
    }, this);
}
_c = LeadsList;
var _c;
__turbopack_context__.k.register(_c, "LeadsList");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/Desktop/redditscraper/frontend/src/components/SubredditSelector.tsx [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "SubredditSelector",
    ()=>SubredditSelector
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$chevron$2d$down$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__ChevronDown$3e$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/node_modules/lucide-react/dist/esm/icons/chevron-down.js [app-client] (ecmascript) <export default as ChevronDown>");
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$x$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__X$3e$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/node_modules/lucide-react/dist/esm/icons/x.js [app-client] (ecmascript) <export default as X>");
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$layers$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Layers$3e$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/node_modules/lucide-react/dist/esm/icons/layers.js [app-client] (ecmascript) <export default as Layers>");
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$render$2f$components$2f$motion$2f$proxy$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/node_modules/framer-motion/dist/es/render/components/motion/proxy.mjs [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$components$2f$AnimatePresence$2f$index$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/node_modules/framer-motion/dist/es/components/AnimatePresence/index.mjs [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature();
"use client";
;
;
;
function SubredditSelector({ subreddits, selectedSubreddit, onSelect, pendingCounts = {} }) {
    _s();
    const [isOpen, setIsOpen] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    const [search, setSearch] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])("");
    const dropdownRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])(null);
    // Close dropdown when clicking outside
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "SubredditSelector.useEffect": ()=>{
            function handleClickOutside(event) {
                if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                    setIsOpen(false);
                }
            }
            document.addEventListener("mousedown", handleClickOutside);
            return ({
                "SubredditSelector.useEffect": ()=>document.removeEventListener("mousedown", handleClickOutside)
            })["SubredditSelector.useEffect"];
        }
    }["SubredditSelector.useEffect"], []);
    // Filter subreddits by search
    const filteredSubreddits = subreddits.filter((sub)=>sub.name.toLowerCase().includes(search.toLowerCase()));
    // Sort by pending count (highest first)
    const sortedSubreddits = [
        ...filteredSubreddits
    ].sort((a, b)=>{
        const countA = pendingCounts[a.id] || 0;
        const countB = pendingCounts[b.id] || 0;
        return countB - countA;
    });
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "relative",
        ref: dropdownRef,
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                onClick: ()=>setIsOpen(!isOpen),
                className: `flex items-center gap-2 px-4 py-2.5 rounded-xl border transition-all ${selectedSubreddit ? "bg-primary/10 border-primary/30 text-primary" : "bg-secondary border-border hover:border-primary/30"}`,
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$layers$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Layers$3e$__["Layers"], {
                        size: 16
                    }, void 0, false, {
                        fileName: "[project]/Desktop/redditscraper/frontend/src/components/SubredditSelector.tsx",
                        lineNumber: 59,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                        className: "font-medium",
                        children: selectedSubreddit ? `r/${selectedSubreddit.name}` : "All Subreddits"
                    }, void 0, false, {
                        fileName: "[project]/Desktop/redditscraper/frontend/src/components/SubredditSelector.tsx",
                        lineNumber: 60,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$chevron$2d$down$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__ChevronDown$3e$__["ChevronDown"], {
                        size: 16,
                        className: `transition-transform ${isOpen ? "rotate-180" : ""}`
                    }, void 0, false, {
                        fileName: "[project]/Desktop/redditscraper/frontend/src/components/SubredditSelector.tsx",
                        lineNumber: 63,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/Desktop/redditscraper/frontend/src/components/SubredditSelector.tsx",
                lineNumber: 51,
                columnNumber: 7
            }, this),
            selectedSubreddit && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                onClick: (e)=>{
                    e.stopPropagation();
                    onSelect(null);
                },
                className: "absolute -right-2 -top-2 p-1 rounded-full bg-destructive text-white hover:bg-destructive/80 transition-colors",
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$x$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__X$3e$__["X"], {
                    size: 12
                }, void 0, false, {
                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SubredditSelector.tsx",
                    lineNumber: 78,
                    columnNumber: 11
                }, this)
            }, void 0, false, {
                fileName: "[project]/Desktop/redditscraper/frontend/src/components/SubredditSelector.tsx",
                lineNumber: 71,
                columnNumber: 9
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$components$2f$AnimatePresence$2f$index$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["AnimatePresence"], {
                children: isOpen && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$render$2f$components$2f$motion$2f$proxy$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["motion"].div, {
                    initial: {
                        opacity: 0,
                        y: -10
                    },
                    animate: {
                        opacity: 1,
                        y: 0
                    },
                    exit: {
                        opacity: 0,
                        y: -10
                    },
                    className: "absolute top-full left-0 mt-2 w-72 bg-card border border-border rounded-xl shadow-xl z-50 overflow-hidden",
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "p-3 border-b border-border",
                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("input", {
                                type: "text",
                                placeholder: "Search subreddits...",
                                value: search,
                                onChange: (e)=>setSearch(e.target.value),
                                className: "w-full px-3 py-2 bg-secondary rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50",
                                autoFocus: true
                            }, void 0, false, {
                                fileName: "[project]/Desktop/redditscraper/frontend/src/components/SubredditSelector.tsx",
                                lineNumber: 93,
                                columnNumber: 15
                            }, this)
                        }, void 0, false, {
                            fileName: "[project]/Desktop/redditscraper/frontend/src/components/SubredditSelector.tsx",
                            lineNumber: 92,
                            columnNumber: 13
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "max-h-64 overflow-y-auto",
                            children: [
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                    onClick: ()=>{
                                        onSelect(null);
                                        setIsOpen(false);
                                        setSearch("");
                                    },
                                    className: `w-full px-4 py-3 text-left hover:bg-secondary/50 transition-colors flex items-center justify-between ${!selectedSubreddit ? "bg-primary/10" : ""}`,
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                            className: "font-medium",
                                            children: "All Subreddits"
                                        }, void 0, false, {
                                            fileName: "[project]/Desktop/redditscraper/frontend/src/components/SubredditSelector.tsx",
                                            lineNumber: 116,
                                            columnNumber: 17
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                            className: "text-xs text-muted-foreground",
                                            children: [
                                                Object.values(pendingCounts).reduce((a, b)=>a + b, 0),
                                                " pending"
                                            ]
                                        }, void 0, true, {
                                            fileName: "[project]/Desktop/redditscraper/frontend/src/components/SubredditSelector.tsx",
                                            lineNumber: 117,
                                            columnNumber: 17
                                        }, this)
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SubredditSelector.tsx",
                                    lineNumber: 106,
                                    columnNumber: 15
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    className: "border-t border-border"
                                }, void 0, false, {
                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SubredditSelector.tsx",
                                    lineNumber: 123,
                                    columnNumber: 15
                                }, this),
                                sortedSubreddits.map((sub)=>{
                                    const count = pendingCounts[sub.id] || 0;
                                    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                        onClick: ()=>{
                                            onSelect(sub);
                                            setIsOpen(false);
                                            setSearch("");
                                        },
                                        className: `w-full px-4 py-3 text-left hover:bg-secondary/50 transition-colors flex items-center justify-between ${selectedSubreddit?.id === sub.id ? "bg-primary/10" : ""}`,
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                children: [
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                        className: "font-medium",
                                                        children: [
                                                            "r/",
                                                            sub.name
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/Desktop/redditscraper/frontend/src/components/SubredditSelector.tsx",
                                                        lineNumber: 141,
                                                        columnNumber: 23
                                                    }, this),
                                                    sub.subscribers > 0 && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                        className: "text-xs text-muted-foreground ml-2",
                                                        children: [
                                                            sub.subscribers.toLocaleString(),
                                                            " members"
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/Desktop/redditscraper/frontend/src/components/SubredditSelector.tsx",
                                                        lineNumber: 143,
                                                        columnNumber: 25
                                                    }, this)
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/Desktop/redditscraper/frontend/src/components/SubredditSelector.tsx",
                                                lineNumber: 140,
                                                columnNumber: 21
                                            }, this),
                                            count > 0 && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                className: "px-2 py-0.5 bg-amber-500/20 text-amber-400 rounded-full text-xs font-medium",
                                                children: count
                                            }, void 0, false, {
                                                fileName: "[project]/Desktop/redditscraper/frontend/src/components/SubredditSelector.tsx",
                                                lineNumber: 149,
                                                columnNumber: 23
                                            }, this)
                                        ]
                                    }, sub.id, true, {
                                        fileName: "[project]/Desktop/redditscraper/frontend/src/components/SubredditSelector.tsx",
                                        lineNumber: 129,
                                        columnNumber: 19
                                    }, this);
                                }),
                                sortedSubreddits.length === 0 && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    className: "px-4 py-6 text-center text-muted-foreground text-sm",
                                    children: "No subreddits found"
                                }, void 0, false, {
                                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SubredditSelector.tsx",
                                    lineNumber: 158,
                                    columnNumber: 17
                                }, this)
                            ]
                        }, void 0, true, {
                            fileName: "[project]/Desktop/redditscraper/frontend/src/components/SubredditSelector.tsx",
                            lineNumber: 104,
                            columnNumber: 13
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/Desktop/redditscraper/frontend/src/components/SubredditSelector.tsx",
                    lineNumber: 85,
                    columnNumber: 11
                }, this)
            }, void 0, false, {
                fileName: "[project]/Desktop/redditscraper/frontend/src/components/SubredditSelector.tsx",
                lineNumber: 83,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/Desktop/redditscraper/frontend/src/components/SubredditSelector.tsx",
        lineNumber: 49,
        columnNumber: 5
    }, this);
}
_s(SubredditSelector, "AA+21ayMzCHDlqUCeNzNSHEj5io=");
_c = SubredditSelector;
var _c;
__turbopack_context__.k.register(_c, "SubredditSelector");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/Desktop/redditscraper/frontend/src/app/page.tsx [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>Home
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$components$2f$AnimatePresence$2f$index$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/node_modules/framer-motion/dist/es/components/AnimatePresence/index.mjs [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$render$2f$components$2f$motion$2f$proxy$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/node_modules/framer-motion/dist/es/render/components/motion/proxy.mjs [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$refresh$2d$cw$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__RefreshCw$3e$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/node_modules/lucide-react/dist/esm/icons/refresh-cw.js [app-client] (ecmascript) <export default as RefreshCw>");
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$zap$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Zap$3e$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/node_modules/lucide-react/dist/esm/icons/zap.js [app-client] (ecmascript) <export default as Zap>");
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$undo$2d$2$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Undo2$3e$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/node_modules/lucide-react/dist/esm/icons/undo-2.js [app-client] (ecmascript) <export default as Undo2>");
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$src$2f$lib$2f$supabase$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/src/lib/supabase.ts [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$src$2f$components$2f$SwipeCard$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/src/components/SwipeCard.tsx [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$src$2f$components$2f$StatsBar$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/src/components/StatsBar.tsx [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$src$2f$components$2f$LeadsList$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/src/components/LeadsList.tsx [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$src$2f$components$2f$SubredditSelector$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/Desktop/redditscraper/frontend/src/components/SubredditSelector.tsx [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature();
"use client";
;
;
;
;
;
;
;
;
function Home() {
    _s();
    const [leads, setLeads] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])([]);
    const [currentIndex, setCurrentIndex] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(0);
    const [swipeHistory, setSwipeHistory] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])([]);
    const [stats, setStats] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])({
        total_leads: 0,
        total_posts: 0,
        total_subreddits: 0,
        pending_leads: 0,
        approved_leads: 0,
        rejected_leads: 0,
        superliked_leads: 0
    });
    const [currentFilter, setCurrentFilter] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])("pending");
    const [isLoading, setIsLoading] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(true);
    const [isRefreshing, setIsRefreshing] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    // Subreddit filtering
    const [subreddits, setSubreddits] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])([]);
    const [selectedSubreddit, setSelectedSubreddit] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(null);
    const [subredditPendingCounts, setSubredditPendingCounts] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])({});
    // Fetch subreddits
    const fetchSubreddits = (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useCallback"])({
        "Home.useCallback[fetchSubreddits]": async ()=>{
            try {
                const data = await (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$src$2f$lib$2f$supabase$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["getSubreddits"])();
                setSubreddits(data);
                // Calculate pending counts per subreddit
                const { supabase } = await __turbopack_context__.A("[project]/Desktop/redditscraper/frontend/src/lib/supabase.ts [app-client] (ecmascript, async loader)");
                const counts = {};
                for (const sub of data){
                    const { data: posts } = await supabase.from("reddit_posts").select("lead_id").eq("subreddit_id", sub.id);
                    if (posts) {
                        const leadIds = [
                            ...new Set(posts.map({
                                "Home.useCallback[fetchSubreddits]": (p)=>p.lead_id
                            }["Home.useCallback[fetchSubreddits]"]))
                        ];
                        if (leadIds.length > 0) {
                            const { data: leads } = await supabase.from("reddit_leads").select("id").in("id", leadIds).eq("status", "pending");
                            counts[sub.id] = leads?.length || 0;
                        }
                    }
                }
                setSubredditPendingCounts(counts);
            } catch (error) {
                console.error("Error fetching subreddits:", error);
            }
        }
    }["Home.useCallback[fetchSubreddits]"], []);
    // Fetch leads based on current filter and selected subreddit
    const fetchLeads = (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useCallback"])({
        "Home.useCallback[fetchLeads]": async ()=>{
            setIsLoading(true);
            try {
                let data;
                if (selectedSubreddit) {
                    // Filter by subreddit
                    data = await (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$src$2f$lib$2f$supabase$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["getLeadsBySubreddit"])(selectedSubreddit.id, currentFilter, 50);
                } else if (currentFilter === "pending") {
                    data = await (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$src$2f$lib$2f$supabase$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["getPendingLeads"])(50);
                } else {
                    data = await (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$src$2f$lib$2f$supabase$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["getLeadsByStatus"])(currentFilter, 50);
                }
                setLeads(data);
                setCurrentIndex(0);
            } catch (error) {
                console.error("Error fetching leads:", error);
            } finally{
                setIsLoading(false);
            }
        }
    }["Home.useCallback[fetchLeads]"], [
        currentFilter,
        selectedSubreddit
    ]);
    // Fetch stats
    const fetchStats = (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useCallback"])({
        "Home.useCallback[fetchStats]": async ()=>{
            try {
                const data = await (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$src$2f$lib$2f$supabase$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["getStats"])();
                setStats(data);
            } catch (error) {
                console.error("Error fetching stats:", error);
            }
        }
    }["Home.useCallback[fetchStats]"], []);
    // Initial load
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "Home.useEffect": ()=>{
            fetchSubreddits();
            fetchLeads();
            fetchStats();
        }
    }["Home.useEffect"], [
        fetchSubreddits,
        fetchLeads,
        fetchStats
    ]);
    // Keyboard shortcut for undo
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "Home.useEffect": ()=>{
            const handleKeyDown = {
                "Home.useEffect.handleKeyDown": (e)=>{
                    if (e.key === "z" || e.key === "Z") {
                        if (currentFilter === "pending" && swipeHistory.length > 0) {
                            handleUndo();
                        }
                    }
                }
            }["Home.useEffect.handleKeyDown"];
            window.addEventListener("keydown", handleKeyDown);
            return ({
                "Home.useEffect": ()=>window.removeEventListener("keydown", handleKeyDown)
            })["Home.useEffect"];
        }
    }["Home.useEffect"], [
        currentFilter,
        swipeHistory.length
    ]);
    // Refetch when filter or subreddit changes
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "Home.useEffect": ()=>{
            fetchLeads();
        }
    }["Home.useEffect"], [
        currentFilter,
        selectedSubreddit,
        fetchLeads
    ]);
    // Handle swipe
    const handleSwipe = async (direction)=>{
        const currentLead = leads[currentIndex];
        if (!currentLead) return;
        const status = direction === "right" ? "approved" : "rejected";
        // Add to history for undo
        setSwipeHistory((prev)=>[
                ...prev,
                {
                    lead: currentLead,
                    action: status
                }
            ]);
        // Optimistic update
        setLeads((prev)=>prev.filter((_, i)=>i !== currentIndex));
        setStats((prev)=>({
                ...prev,
                pending_leads: Math.max(0, prev.pending_leads - 1),
                approved_leads: status === "approved" ? prev.approved_leads + 1 : prev.approved_leads,
                rejected_leads: status === "rejected" ? prev.rejected_leads + 1 : prev.rejected_leads
            }));
        // Update in database
        await (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$src$2f$lib$2f$supabase$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["updateLeadStatus"])(currentLead.id, status);
    };
    // Handle super like
    const handleSuperLike = async ()=>{
        const currentLead = leads[currentIndex];
        if (!currentLead) return;
        // Add to history for undo
        setSwipeHistory((prev)=>[
                ...prev,
                {
                    lead: currentLead,
                    action: "superliked"
                }
            ]);
        // Optimistic update
        setLeads((prev)=>prev.filter((_, i)=>i !== currentIndex));
        setStats((prev)=>({
                ...prev,
                pending_leads: Math.max(0, prev.pending_leads - 1),
                superliked_leads: prev.superliked_leads + 1
            }));
        // Update in database
        await (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$src$2f$lib$2f$supabase$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["updateLeadStatus"])(currentLead.id, "superliked");
    };
    // Handle undo - go back to previous lead
    const handleUndo = async ()=>{
        if (swipeHistory.length === 0) return;
        const lastEntry = swipeHistory[swipeHistory.length - 1];
        // Remove from history
        setSwipeHistory((prev)=>prev.slice(0, -1));
        // Add lead back to the front of the list
        setLeads((prev)=>[
                lastEntry.lead,
                ...prev
            ]);
        // Update stats
        setStats((prev)=>({
                ...prev,
                pending_leads: prev.pending_leads + 1,
                approved_leads: lastEntry.action === "approved" ? Math.max(0, prev.approved_leads - 1) : prev.approved_leads,
                rejected_leads: lastEntry.action === "rejected" ? Math.max(0, prev.rejected_leads - 1) : prev.rejected_leads,
                superliked_leads: lastEntry.action === "superliked" ? Math.max(0, prev.superliked_leads - 1) : prev.superliked_leads
            }));
        // Update in database - set back to pending
        const { supabase } = await __turbopack_context__.A("[project]/Desktop/redditscraper/frontend/src/lib/supabase.ts [app-client] (ecmascript, async loader)");
        await supabase.from("reddit_leads").update({
            status: "pending",
            updated_at: new Date().toISOString()
        }).eq("id", lastEntry.lead.id);
    };
    // Handle restore (move back to pending)
    const handleRestore = async (leadId)=>{
        // Find the lead
        const lead = leads.find((l)=>l.id === leadId);
        if (!lead) return;
        // Optimistic update
        setLeads((prev)=>prev.filter((l)=>l.id !== leadId));
        setStats((prev)=>({
                ...prev,
                pending_leads: prev.pending_leads + 1,
                approved_leads: lead.status === "approved" ? Math.max(0, prev.approved_leads - 1) : prev.approved_leads,
                rejected_leads: lead.status === "rejected" ? Math.max(0, prev.rejected_leads - 1) : prev.rejected_leads
            }));
        // Update in database - we need to update to pending status
        // Note: This requires a slight modification to updateLeadStatus to handle "pending"
        // For now, we'll just update the status directly
        const { supabase } = await __turbopack_context__.A("[project]/Desktop/redditscraper/frontend/src/lib/supabase.ts [app-client] (ecmascript, async loader)");
        await supabase.from("reddit_leads").update({
            status: "pending",
            updated_at: new Date().toISOString()
        }).eq("id", leadId);
    };
    // Refresh data
    const handleRefresh = async ()=>{
        setIsRefreshing(true);
        await Promise.all([
            fetchLeads(),
            fetchStats(),
            fetchSubreddits()
        ]);
        setIsRefreshing(false);
    };
    const currentLead = leads[currentIndex];
    const showSwiper = currentFilter === "pending";
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("main", {
        className: "min-h-screen p-6 md:p-8 max-w-4xl mx-auto",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("header", {
                className: "flex items-center justify-between mb-6",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h1", {
                                className: "text-3xl font-bold gradient-text flex items-center gap-2",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$zap$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Zap$3e$__["Zap"], {
                                        className: "text-primary"
                                    }, void 0, false, {
                                        fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
                                        lineNumber: 275,
                                        columnNumber: 13
                                    }, this),
                                    "Lead Swiper"
                                ]
                            }, void 0, true, {
                                fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
                                lineNumber: 274,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                className: "text-muted-foreground mt-1",
                                children: "Swipe through Reddit leads for your OF agency"
                            }, void 0, false, {
                                fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
                                lineNumber: 278,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
                        lineNumber: 273,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                        onClick: handleRefresh,
                        disabled: isRefreshing,
                        className: "p-3 rounded-xl bg-secondary hover:bg-secondary/80 text-foreground transition-all disabled:opacity-50",
                        title: "Refresh data",
                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$refresh$2d$cw$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__RefreshCw$3e$__["RefreshCw"], {
                            size: 20,
                            className: isRefreshing ? "animate-spin" : ""
                        }, void 0, false, {
                            fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
                            lineNumber: 288,
                            columnNumber: 11
                        }, this)
                    }, void 0, false, {
                        fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
                        lineNumber: 282,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
                lineNumber: 272,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "flex items-center gap-4 mb-6",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$src$2f$components$2f$SubredditSelector$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["SubredditSelector"], {
                        subreddits: subreddits,
                        selectedSubreddit: selectedSubreddit,
                        onSelect: (sub)=>{
                            setSelectedSubreddit(sub);
                            setSwipeHistory([]); // Clear undo history when switching
                        },
                        pendingCounts: subredditPendingCounts
                    }, void 0, false, {
                        fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
                        lineNumber: 297,
                        columnNumber: 9
                    }, this),
                    selectedSubreddit && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                        className: "text-sm text-muted-foreground",
                        children: [
                            "Filtering leads from r/",
                            selectedSubreddit.name
                        ]
                    }, void 0, true, {
                        fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
                        lineNumber: 307,
                        columnNumber: 11
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
                lineNumber: 296,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$src$2f$components$2f$StatsBar$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["StatsBar"], {
                stats: stats,
                currentFilter: currentFilter,
                onFilterChange: setCurrentFilter
            }, void 0, false, {
                fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
                lineNumber: 314,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "relative min-h-[600px]",
                children: isLoading ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "absolute inset-0 flex items-center justify-center",
                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "text-center space-y-4",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto"
                            }, void 0, false, {
                                fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
                                lineNumber: 325,
                                columnNumber: 15
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                className: "text-muted-foreground",
                                children: "Loading leads..."
                            }, void 0, false, {
                                fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
                                lineNumber: 326,
                                columnNumber: 15
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
                        lineNumber: 324,
                        columnNumber: 13
                    }, this)
                }, void 0, false, {
                    fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
                    lineNumber: 323,
                    columnNumber: 11
                }, this) : showSwiper ? // Swipe mode for pending leads
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["Fragment"], {
                    children: leads.length > 0 ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["Fragment"], {
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "text-center mb-4 text-sm text-muted-foreground",
                                children: [
                                    currentIndex + 1,
                                    " of ",
                                    leads.length,
                                    " pending leads"
                                ]
                            }, void 0, true, {
                                fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
                                lineNumber: 335,
                                columnNumber: 17
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "relative h-[75vh] min-h-[600px]",
                                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$components$2f$AnimatePresence$2f$index$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["AnimatePresence"], {
                                    mode: "popLayout",
                                    children: currentLead && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$src$2f$components$2f$SwipeCard$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["SwipeCard"], {
                                        lead: currentLead,
                                        onSwipe: handleSwipe,
                                        onSuperLike: handleSuperLike,
                                        isActive: true
                                    }, currentLead.id, false, {
                                        fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
                                        lineNumber: 343,
                                        columnNumber: 23
                                    }, this)
                                }, void 0, false, {
                                    fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
                                    lineNumber: 341,
                                    columnNumber: 19
                                }, this)
                            }, void 0, false, {
                                fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
                                lineNumber: 340,
                                columnNumber: 17
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "flex items-center justify-center gap-4 mt-4",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                        onClick: handleUndo,
                                        disabled: swipeHistory.length === 0,
                                        className: "flex items-center gap-2 px-4 py-2 rounded-xl bg-secondary hover:bg-secondary/80 text-foreground transition-all disabled:opacity-30 disabled:cursor-not-allowed",
                                        title: "Undo last swipe (Z)",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$undo$2d$2$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Undo2$3e$__["Undo2"], {
                                                size: 16
                                            }, void 0, false, {
                                                fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
                                                lineNumber: 363,
                                                columnNumber: 21
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                className: "text-sm",
                                                children: "Undo"
                                            }, void 0, false, {
                                                fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
                                                lineNumber: 364,
                                                columnNumber: 21
                                            }, this),
                                            swipeHistory.length > 0 && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                className: "text-xs text-muted-foreground",
                                                children: [
                                                    "(",
                                                    swipeHistory.length,
                                                    ")"
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
                                                lineNumber: 366,
                                                columnNumber: 23
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
                                        lineNumber: 357,
                                        columnNumber: 19
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "flex items-center gap-3 text-xs text-muted-foreground",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                className: "flex items-center gap-1",
                                                children: [
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("kbd", {
                                                        className: "px-2 py-1 bg-secondary rounded",
                                                        children: "←"
                                                    }, void 0, false, {
                                                        fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
                                                        lineNumber: 375,
                                                        columnNumber: 23
                                                    }, this),
                                                    "Reject"
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
                                                lineNumber: 374,
                                                columnNumber: 21
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                className: "flex items-center gap-1",
                                                children: [
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("kbd", {
                                                        className: "px-2 py-1 bg-amber-500/20 text-amber-400 rounded",
                                                        children: "↑"
                                                    }, void 0, false, {
                                                        fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
                                                        lineNumber: 379,
                                                        columnNumber: 23
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                        className: "text-amber-400",
                                                        children: "Super"
                                                    }, void 0, false, {
                                                        fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
                                                        lineNumber: 380,
                                                        columnNumber: 23
                                                    }, this)
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
                                                lineNumber: 378,
                                                columnNumber: 21
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                className: "flex items-center gap-1",
                                                children: [
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("kbd", {
                                                        className: "px-2 py-1 bg-secondary rounded",
                                                        children: "→"
                                                    }, void 0, false, {
                                                        fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
                                                        lineNumber: 383,
                                                        columnNumber: 23
                                                    }, this),
                                                    "Approve"
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
                                                lineNumber: 382,
                                                columnNumber: 21
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                className: "flex items-center gap-1",
                                                children: [
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("kbd", {
                                                        className: "px-2 py-1 bg-secondary rounded",
                                                        children: "Z"
                                                    }, void 0, false, {
                                                        fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
                                                        lineNumber: 387,
                                                        columnNumber: 23
                                                    }, this),
                                                    "Undo"
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
                                                lineNumber: 386,
                                                columnNumber: 21
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
                                        lineNumber: 373,
                                        columnNumber: 19
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
                                lineNumber: 355,
                                columnNumber: 17
                            }, this)
                        ]
                    }, void 0, true) : /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$render$2f$components$2f$motion$2f$proxy$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["motion"].div, {
                        initial: {
                            opacity: 0,
                            y: 20
                        },
                        animate: {
                            opacity: 1,
                            y: 0
                        },
                        className: "text-center py-20",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "w-20 h-20 bg-success/10 rounded-full flex items-center justify-center mx-auto mb-4",
                                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                    className: "text-4xl",
                                    children: "🎉"
                                }, void 0, false, {
                                    fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
                                    lineNumber: 400,
                                    columnNumber: 19
                                }, this)
                            }, void 0, false, {
                                fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
                                lineNumber: 399,
                                columnNumber: 17
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h2", {
                                className: "text-2xl font-bold text-foreground mb-2",
                                children: "All caught up!"
                            }, void 0, false, {
                                fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
                                lineNumber: 402,
                                columnNumber: 17
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                className: "text-muted-foreground mb-6",
                                children: "No more pending leads to review. Run the scraper to find more!"
                            }, void 0, false, {
                                fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
                                lineNumber: 405,
                                columnNumber: 17
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                onClick: handleRefresh,
                                className: "px-6 py-3 bg-primary text-primary-foreground rounded-xl font-medium hover:bg-primary/90 transition-colors",
                                children: "Check for new leads"
                            }, void 0, false, {
                                fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
                                lineNumber: 408,
                                columnNumber: 17
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
                        lineNumber: 394,
                        columnNumber: 15
                    }, this)
                }, void 0, false) : // List mode for approved/rejected leads
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$framer$2d$motion$2f$dist$2f$es$2f$render$2f$components$2f$motion$2f$proxy$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["motion"].div, {
                    initial: {
                        opacity: 0
                    },
                    animate: {
                        opacity: 1
                    },
                    className: "bg-card rounded-2xl p-6",
                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$Desktop$2f$redditscraper$2f$frontend$2f$src$2f$components$2f$LeadsList$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["LeadsList"], {
                        leads: leads,
                        onRestore: handleRestore,
                        showRestore: true,
                        onBack: ()=>setCurrentFilter("pending"),
                        title: `${currentFilter.charAt(0).toUpperCase() + currentFilter.slice(1)} Leads`
                    }, void 0, false, {
                        fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
                        lineNumber: 424,
                        columnNumber: 13
                    }, this)
                }, void 0, false, {
                    fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
                    lineNumber: 419,
                    columnNumber: 11
                }, this)
            }, void 0, false, {
                fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
                lineNumber: 321,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/Desktop/redditscraper/frontend/src/app/page.tsx",
        lineNumber: 270,
        columnNumber: 5
    }, this);
}
_s(Home, "Va8vSPuEYL1I/w4+oVcSDC7nHVQ=");
_c = Home;
var _c;
__turbopack_context__.k.register(_c, "Home");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
]);

//# sourceMappingURL=Desktop_redditscraper_frontend_src_a2d4691a._.js.map