"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search,
  Plus,
  X,
  Loader2,
  CheckCircle,
  Clock,
  AlertCircle,
  Trash2,
  Play,
  Settings,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import {
  getSearchKeywords,
  getScrapeJobs,
  addKeywordAndScrape,
  toggleKeywordActive,
  deleteKeyword,
  queueScrapeJob,
  type SearchKeyword,
  type ScrapeJob,
} from "@/lib/supabase";

interface KeywordManagerProps {
  onJobQueued?: () => void;
}

export function KeywordManager({ onJobQueued }: KeywordManagerProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [keywords, setKeywords] = useState<SearchKeyword[]>([]);
  const [jobs, setJobs] = useState<ScrapeJob[]>([]);
  const [newKeyword, setNewKeyword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isAdding, setIsAdding] = useState(false);
  const [showJobs, setShowJobs] = useState(false);

  // Fetch data
  const fetchData = async () => {
    setIsLoading(true);
    const [keywordsData, jobsData] = await Promise.all([
      getSearchKeywords(),
      getScrapeJobs(10),
    ]);
    setKeywords(keywordsData);
    setJobs(jobsData);
    setIsLoading(false);
  };

  useEffect(() => {
    if (isOpen) {
      fetchData();
    }
  }, [isOpen]);

  // Poll for job updates when panel is open
  useEffect(() => {
    if (!isOpen) return;

    const interval = setInterval(() => {
      getScrapeJobs(10).then(setJobs);
    }, 5000);

    return () => clearInterval(interval);
  }, [isOpen]);

  // Add new keyword and queue scrape
  const handleAddKeyword = async () => {
    if (!newKeyword.trim()) return;

    setIsAdding(true);
    const result = await addKeywordAndScrape(newKeyword.trim());
    
    if (result.keyword) {
      setKeywords((prev) => [result.keyword!, ...prev]);
    }
    if (result.job) {
      setJobs((prev) => [result.job!, ...prev]);
      onJobQueued?.();
    }
    
    setNewKeyword("");
    setIsAdding(false);
  };

  // Queue a scrape for existing keyword
  const handleScrapeKeyword = async (kw: SearchKeyword) => {
    const job = await queueScrapeJob(kw.keyword, kw.id, 500);
    if (job) {
      setJobs((prev) => [job, ...prev]);
      onJobQueued?.();
    }
  };

  // Toggle keyword active status
  const handleToggleActive = async (kw: SearchKeyword) => {
    const success = await toggleKeywordActive(kw.id, !kw.is_active);
    if (success) {
      setKeywords((prev) =>
        prev.map((k) => (k.id === kw.id ? { ...k, is_active: !k.is_active } : k))
      );
    }
  };

  // Delete keyword
  const handleDelete = async (kw: SearchKeyword) => {
    if (!confirm(`Delete keyword "${kw.keyword}"?`)) return;
    
    const success = await deleteKeyword(kw.id);
    if (success) {
      setKeywords((prev) => prev.filter((k) => k.id !== kw.id));
    }
  };

  // Count pending jobs
  const pendingJobs = jobs.filter((j) => j.status === "pending" || j.status === "processing").length;

  const getJobStatusIcon = (status: ScrapeJob["status"]) => {
    switch (status) {
      case "pending":
        return <Clock size={14} className="text-amber-400" />;
      case "processing":
        return <Loader2 size={14} className="text-blue-400 animate-spin" />;
      case "completed":
        return <CheckCircle size={14} className="text-emerald-400" />;
      case "failed":
        return <AlertCircle size={14} className="text-red-400" />;
    }
  };

  return (
    <div className="relative">
      {/* Trigger button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center gap-2 px-4 py-2.5 rounded-xl border transition-all ${
          isOpen
            ? "bg-primary text-primary-foreground border-primary"
            : "bg-secondary border-border hover:border-primary/30"
        }`}
      >
        <Settings size={16} />
        <span className="font-medium">Keywords</span>
        {pendingJobs > 0 && (
          <span className="px-2 py-0.5 bg-amber-500 text-white rounded-full text-xs font-bold animate-pulse">
            {pendingJobs}
          </span>
        )}
      </button>

      {/* Panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            className="absolute top-full right-0 mt-2 w-96 bg-card border border-border rounded-xl shadow-2xl z-50 overflow-hidden"
          >
            {/* Header */}
            <div className="p-4 border-b border-border bg-secondary/30">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-bold text-foreground">Search Keywords</h3>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-1 rounded-lg hover:bg-secondary transition-colors"
                >
                  <X size={18} />
                </button>
              </div>

              {/* Add new keyword */}
              <div className="flex gap-2">
                <div className="flex-1 relative">
                  <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                  <input
                    type="text"
                    value={newKeyword}
                    onChange={(e) => setNewKeyword(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleAddKeyword()}
                    placeholder="Add new keyword..."
                    className="w-full pl-9 pr-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                  />
                </div>
                <button
                  onClick={handleAddKeyword}
                  disabled={isAdding || !newKeyword.trim()}
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {isAdding ? (
                    <Loader2 size={16} className="animate-spin" />
                  ) : (
                    <Plus size={16} />
                  )}
                  Add & Scrape
                </button>
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                New keywords are immediately queued for scraping
              </p>
            </div>

            {/* Keywords list */}
            <div className="max-h-64 overflow-y-auto">
              {isLoading ? (
                <div className="p-8 text-center">
                  <Loader2 size={24} className="animate-spin mx-auto text-muted-foreground" />
                </div>
              ) : keywords.length === 0 ? (
                <div className="p-8 text-center text-muted-foreground text-sm">
                  No keywords yet. Add one above!
                </div>
              ) : (
                <div className="divide-y divide-border">
                  {keywords.map((kw) => (
                    <div
                      key={kw.id}
                      className={`p-3 flex items-center gap-3 hover:bg-secondary/30 transition-colors ${
                        !kw.is_active ? "opacity-50" : ""
                      }`}
                    >
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-sm truncate">{kw.keyword}</div>
                        <div className="text-xs text-muted-foreground">
                          Scraped {kw.times_scraped}x
                          {kw.last_scraped_at && (
                            <> · Last: {new Date(kw.last_scraped_at).toLocaleDateString()}</>
                          )}
                        </div>
                      </div>
                      
                      {/* Priority badge */}
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                        kw.priority >= 100 ? "bg-primary/20 text-primary" : "bg-secondary text-muted-foreground"
                      }`}>
                        P{kw.priority}
                      </span>

                      {/* Actions */}
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => handleScrapeKeyword(kw)}
                          className="p-1.5 rounded-lg hover:bg-primary/20 text-primary transition-colors"
                          title="Queue scrape"
                        >
                          <Play size={14} />
                        </button>
                        <button
                          onClick={() => handleToggleActive(kw)}
                          className={`p-1.5 rounded-lg transition-colors ${
                            kw.is_active
                              ? "hover:bg-amber-500/20 text-amber-400"
                              : "hover:bg-emerald-500/20 text-emerald-400"
                          }`}
                          title={kw.is_active ? "Disable" : "Enable"}
                        >
                          {kw.is_active ? <ChevronDown size={14} /> : <ChevronUp size={14} />}
                        </button>
                        <button
                          onClick={() => handleDelete(kw)}
                          className="p-1.5 rounded-lg hover:bg-destructive/20 text-destructive transition-colors"
                          title="Delete"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Jobs section */}
            <div className="border-t border-border">
              <button
                onClick={() => setShowJobs(!showJobs)}
                className="w-full p-3 flex items-center justify-between hover:bg-secondary/30 transition-colors"
              >
                <span className="text-sm font-medium">
                  Recent Jobs {pendingJobs > 0 && `(${pendingJobs} active)`}
                </span>
                {showJobs ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
              </button>

              <AnimatePresence>
                {showJobs && (
                  <motion.div
                    initial={{ height: 0 }}
                    animate={{ height: "auto" }}
                    exit={{ height: 0 }}
                    className="overflow-hidden"
                  >
                    <div className="max-h-48 overflow-y-auto divide-y divide-border/50 bg-secondary/20">
                      {jobs.length === 0 ? (
                        <div className="p-4 text-center text-muted-foreground text-sm">
                          No scrape jobs yet
                        </div>
                      ) : (
                        jobs.map((job) => (
                          <div key={job.id} className="p-3 flex items-center gap-3">
                            {getJobStatusIcon(job.status)}
                            <div className="flex-1 min-w-0">
                              <div className="text-sm font-medium truncate">{job.keyword}</div>
                              <div className="text-xs text-muted-foreground">
                                {job.status === "completed" ? (
                                  <>
                                    {job.subreddits_found} subs · {job.leads_found} leads · {job.posts_found} posts
                                  </>
                                ) : job.status === "failed" ? (
                                  <span className="text-red-400">{job.error_message || "Failed"}</span>
                                ) : (
                                  new Date(job.created_at).toLocaleTimeString()
                                )}
                              </div>
                            </div>
                            <span className={`text-xs px-2 py-0.5 rounded-full ${
                              job.status === "pending" ? "bg-amber-500/20 text-amber-400" :
                              job.status === "processing" ? "bg-blue-500/20 text-blue-400" :
                              job.status === "completed" ? "bg-emerald-500/20 text-emerald-400" :
                              "bg-red-500/20 text-red-400"
                            }`}>
                              {job.status}
                            </span>
                          </div>
                        ))
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Footer */}
            <div className="p-3 border-t border-border bg-secondary/30 text-center">
              <p className="text-xs text-muted-foreground">
                Run <code className="bg-background px-1 rounded">python main.py --jobs</code> to process queue
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

