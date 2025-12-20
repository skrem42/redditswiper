"use client";

import { ExternalLink, RotateCcw, ArrowLeft } from "lucide-react";
import type { RedditLead } from "@/lib/supabase";

interface LeadsListProps {
  leads: RedditLead[];
  onRestore?: (leadId: string) => void;
  showRestore?: boolean;
  onBack?: () => void;
  title?: string;
}

export function LeadsList({ leads, onRestore, showRestore = false, onBack, title }: LeadsListProps) {
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
      {leads.map((lead) => (
        <div
          key={lead.id}
          className="bg-card rounded-xl p-4 flex items-center gap-4 hover:bg-card/80 transition-colors"
        >
          {/* Avatar */}
          {lead.avatar_url ? (
            <img
              src={lead.avatar_url}
              alt={lead.reddit_username}
              className="w-12 h-12 rounded-full object-cover border border-border"
            />
          ) : (
            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center text-lg font-bold text-white">
              {lead.reddit_username.charAt(0).toUpperCase()}
            </div>
          )}

          {/* Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="font-medium text-foreground truncate">
                u/{lead.reddit_username}
              </span>
              <a
                href={lead.profile_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-muted-foreground hover:text-accent"
              >
                <ExternalLink size={14} />
              </a>
            </div>
            <div className="flex items-center gap-3 text-xs text-muted-foreground mt-1">
              <span>↑ {lead.karma.toLocaleString()}</span>
              <span>{lead.total_posts} posts</span>
              {lead.extracted_links.length > 0 && (
                <span className="text-accent">
                  {lead.extracted_links.length} links
                </span>
              )}
            </div>
          </div>

          {/* Links preview */}
          {lead.extracted_links.length > 0 && (
            <div className="hidden md:flex gap-1">
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

          {/* Restore button */}
          {showRestore && onRestore && (
            <button
              onClick={() => onRestore(lead.id)}
              className="p-2 rounded-lg bg-secondary hover:bg-secondary/80 text-muted-foreground hover:text-foreground transition-colors"
              title="Move back to pending"
            >
              <RotateCcw size={16} />
            </button>
          )}
        </div>
      ))}
        </div>
      )}
    </div>
  );
}


