"use client";

import { useState } from "react";
import { ExternalLink, RotateCcw, ArrowLeft, Check, MessageCircle, ChevronDown, ChevronUp, Star } from "lucide-react";
import type { RedditLead } from "@/lib/supabase";
import { markLeadContacted, unmarkLeadContacted, updateLeadNotes } from "@/lib/supabase";

interface LeadsListProps {
  leads: RedditLead[];
  onRestore?: (leadId: string) => void;
  showRestore?: boolean;
  onBack?: () => void;
  title?: string;
  showContactCheckbox?: boolean;
  onLeadUpdate?: () => void;
}

export function LeadsList({ 
  leads, 
  onRestore, 
  showRestore = false, 
  onBack, 
  title,
  showContactCheckbox = false,
  onLeadUpdate,
}: LeadsListProps) {
  const [expandedLead, setExpandedLead] = useState<string | null>(null);
  const [localLeads, setLocalLeads] = useState<Record<string, { contacted: boolean; notes: string }>>({});
  const [savingNotes, setSavingNotes] = useState<string | null>(null);

  const handleContactToggle = async (lead: RedditLead) => {
    const isCurrentlyContacted = lead.contacted_at !== null || localLeads[lead.id]?.contacted;
    
    // Optimistic update
    setLocalLeads(prev => ({
      ...prev,
      [lead.id]: {
        ...prev[lead.id],
        contacted: !isCurrentlyContacted,
        notes: prev[lead.id]?.notes || lead.notes || "",
      }
    }));

    if (isCurrentlyContacted) {
      await unmarkLeadContacted(lead.id);
    } else {
      await markLeadContacted(lead.id);
    }
    
    onLeadUpdate?.();
  };

  const handleNotesChange = (leadId: string, notes: string) => {
    setLocalLeads(prev => ({
      ...prev,
      [leadId]: {
        ...prev[leadId],
        notes,
      }
    }));
  };

  const handleNotesSave = async (leadId: string) => {
    const notes = localLeads[leadId]?.notes || "";
    setSavingNotes(leadId);
    await updateLeadNotes(leadId, notes);
    setSavingNotes(null);
    onLeadUpdate?.();
  };

  const isContacted = (lead: RedditLead) => {
    if (localLeads[lead.id]?.contacted !== undefined) {
      return localLeads[lead.id].contacted;
    }
    return lead.contacted_at !== null;
  };

  const getNotes = (lead: RedditLead) => {
    return localLeads[lead.id]?.notes ?? lead.notes ?? "";
  };

  const formatContactedDate = (dateStr: string | null) => {
    if (!dateStr) return null;
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", { 
      month: "short", 
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  };

  return (
    <div className="space-y-4">
      {/* Header with back button */}
      {onBack && (
        <div className="flex items-center gap-3 pb-2 border-b border-border">
          <button
            onClick={onBack}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-secondary hover:bg-secondary/80 text-foreground transition-colors"
          >
            <ArrowLeft size={18} />
            <span>Back to Swiper</span>
          </button>
          {title && (
            <h2 className="text-lg font-semibold text-foreground">{title}</h2>
          )}
        </div>
      )}

      {leads.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          <p>No leads in this category</p>
        </div>
      ) : (
        <div className="space-y-3 max-h-[60vh] overflow-y-auto pr-2">
          {leads.map((lead) => {
            const contacted = isContacted(lead);
            const isExpanded = expandedLead === lead.id;
            
            return (
              <div
                key={lead.id}
                className={`bg-card rounded-xl transition-colors ${
                  contacted ? "border-l-4 border-l-blue-500" : ""
                }`}
              >
                {/* Main row */}
                <div className="p-4 flex items-center gap-4">
                  {/* Contact checkbox */}
                  {showContactCheckbox && (
                    <button
                      onClick={() => handleContactToggle(lead)}
                      className={`w-6 h-6 rounded-md border-2 flex items-center justify-center transition-all flex-shrink-0 ${
                        contacted
                          ? "bg-blue-500 border-blue-500 text-white"
                          : "border-muted-foreground/40 hover:border-blue-500"
                      }`}
                      title={contacted ? "Mark as not contacted" : "Mark as contacted"}
                    >
                      {contacted && <Check size={14} strokeWidth={3} />}
                    </button>
                  )}

                  {/* Avatar */}
                  {lead.avatar_url ? (
                    <img
                      src={lead.avatar_url}
                      alt={lead.reddit_username}
                      className="w-12 h-12 rounded-full object-cover border border-border flex-shrink-0"
                    />
                  ) : (
                    <div className="w-12 h-12 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center text-lg font-bold text-white flex-shrink-0">
                      {lead.reddit_username.charAt(0).toUpperCase()}
                    </div>
                  )}

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      {lead.status === "superliked" && (
                        <Star size={14} className="text-amber-500 fill-amber-500 flex-shrink-0" />
                      )}
                      <span className={`font-medium truncate ${contacted ? "text-muted-foreground" : "text-foreground"}`}>
                        u/{lead.reddit_username}
                      </span>
                      <a
                        href={lead.profile_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-muted-foreground hover:text-accent flex-shrink-0"
                      >
                        <ExternalLink size={14} />
                      </a>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-muted-foreground mt-1 flex-wrap">
                      <span>↑ {lead.karma.toLocaleString()}</span>
                      <span>{lead.total_posts} posts</span>
                      {lead.extracted_links.length > 0 && (
                        <span className="text-accent">
                          {lead.extracted_links.length} links
                        </span>
                      )}
                      {contacted && lead.contacted_at && (
                        <span className="flex items-center gap-1 text-blue-500">
                          <MessageCircle size={10} />
                          {formatContactedDate(lead.contacted_at)}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Links preview */}
                  {lead.extracted_links.length > 0 && (
                    <div className="hidden lg:flex gap-1 flex-shrink-0">
                      {lead.extracted_links.slice(0, 2).map((link, idx) => (
                        <a
                          key={idx}
                          href={link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="px-2 py-1 rounded-full bg-accent/10 text-accent text-xs hover:bg-accent/20 transition-colors"
                        >
                          {link.includes("onlyfans") ? "🔥 OF" : "🔗 Link"}
                        </a>
                      ))}
                    </div>
                  )}

                  {/* Expand/collapse for notes */}
                  {showContactCheckbox && (
                    <button
                      onClick={() => setExpandedLead(isExpanded ? null : lead.id)}
                      className="p-2 rounded-lg bg-secondary hover:bg-secondary/80 text-muted-foreground hover:text-foreground transition-colors flex-shrink-0"
                      title="Add notes"
                    >
                      {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </button>
                  )}

                  {/* Restore button */}
                  {showRestore && onRestore && (
                    <button
                      onClick={() => onRestore(lead.id)}
                      className="p-2 rounded-lg bg-secondary hover:bg-secondary/80 text-muted-foreground hover:text-foreground transition-colors flex-shrink-0"
                      title="Move back to pending"
                    >
                      <RotateCcw size={16} />
                    </button>
                  )}
                </div>

                {/* Expanded notes section */}
                {isExpanded && (
                  <div className="px-4 pb-4 pt-0 border-t border-border/50">
                    <div className="mt-3">
                      <label className="text-xs text-muted-foreground mb-1 block">Notes</label>
                      <div className="flex gap-2">
                        <textarea
                          value={getNotes(lead)}
                          onChange={(e) => handleNotesChange(lead.id, e.target.value)}
                          placeholder="Add notes about this lead..."
                          className="flex-1 bg-secondary/50 rounded-lg px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground resize-none focus:outline-none focus:ring-2 focus:ring-accent/50"
                          rows={2}
                        />
                        <button
                          onClick={() => handleNotesSave(lead.id)}
                          disabled={savingNotes === lead.id}
                          className="px-3 py-2 rounded-lg bg-accent text-white text-sm hover:bg-accent/90 transition-colors disabled:opacity-50 self-end"
                        >
                          {savingNotes === lead.id ? "..." : "Save"}
                        </button>
                      </div>
                    </div>

                    {/* Quick links in expanded view */}
                    {lead.extracted_links.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {lead.extracted_links.map((link, idx) => (
                          <a
                            key={idx}
                            href={link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="px-3 py-1 rounded-full bg-accent/10 text-accent text-xs hover:bg-accent/20 transition-colors"
                          >
                            {link.includes("onlyfans") ? "🔥 OnlyFans" : 
                             link.includes("linktree") ? "🌳 Linktree" :
                             link.includes("instagram") ? "📷 Instagram" :
                             link.includes("twitter") || link.includes("x.com") ? "𝕏 Twitter" :
                             "🔗 " + new URL(link).hostname}
                          </a>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}


