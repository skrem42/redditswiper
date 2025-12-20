"use client";

import { ExternalLink, Calendar, TrendingUp, MessageSquare, Clock } from "lucide-react";
import type { RedditLead } from "@/lib/supabase";

interface UserProfileProps {
  lead: RedditLead;
}

export function UserProfile({ lead }: UserProfileProps) {
  const accountAge = lead.account_created_at
    ? Math.floor(
        (Date.now() - new Date(lead.account_created_at).getTime()) /
          (1000 * 60 * 60 * 24)
      )
    : null;

  const formatAccountAge = (days: number | null) => {
    if (days === null) return "Unknown";
    if (days < 30) return `${days} days`;
    if (days < 365) return `${Math.floor(days / 30)} months`;
    return `${(days / 365).toFixed(1)} years`;
  };

  const getLinkIcon = (url: string): string => {
    if (url.includes("onlyfans")) return "🔥";
    if (url.includes("linktree") || url.includes("linktr.ee")) return "🌳";
    if (url.includes("fansly")) return "💜";
    if (url.includes("patreon")) return "🎨";
    if (url.includes("cashapp")) return "💵";
    if (url.includes("venmo")) return "💸";
    return "🔗";
  };

  const getLinkName = (url: string): string => {
    try {
      const hostname = new URL(url).hostname.replace("www.", "");
      const path = new URL(url).pathname.replace("/", "");
      if (path && path.length < 20) {
        return `${hostname}/${path}`;
      }
      return hostname;
    } catch {
      return url.slice(0, 30);
    }
  };

  return (
    <div className="space-y-4">
      {/* Header with avatar and username */}
      <div className="flex items-center gap-4">
        {lead.avatar_url ? (
          <img
            src={lead.avatar_url}
            alt={lead.reddit_username}
            className="w-16 h-16 rounded-full object-cover border-2 border-primary/30"
          />
        ) : (
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center text-2xl font-bold text-white">
            {lead.reddit_username.charAt(0).toUpperCase()}
          </div>
        )}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-foreground truncate">
              u/{lead.reddit_username}
            </h2>
            <a
              href={lead.profile_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-muted-foreground hover:text-accent transition-colors"
            >
              <ExternalLink size={16} />
            </a>
          </div>
          {lead.bio && (
            <p className="text-sm text-muted-foreground line-clamp-2 mt-1">
              {lead.bio}
            </p>
          )}
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-secondary/50 rounded-lg p-3">
          <div className="flex items-center gap-2 text-muted-foreground text-xs mb-1">
            <TrendingUp size={12} />
            <span>Karma</span>
          </div>
          <div className="text-lg font-semibold text-foreground">
            {lead.karma.toLocaleString()}
          </div>
        </div>

        <div className="bg-secondary/50 rounded-lg p-3">
          <div className="flex items-center gap-2 text-muted-foreground text-xs mb-1">
            <MessageSquare size={12} />
            <span>Posts</span>
          </div>
          <div className="text-lg font-semibold text-foreground">
            {lead.total_posts}
          </div>
        </div>

        <div className="bg-secondary/50 rounded-lg p-3">
          <div className="flex items-center gap-2 text-muted-foreground text-xs mb-1">
            <Calendar size={12} />
            <span>Account Age</span>
          </div>
          <div className="text-lg font-semibold text-foreground">
            {formatAccountAge(accountAge)}
          </div>
        </div>

        <div className="bg-secondary/50 rounded-lg p-3">
          <div className="flex items-center gap-2 text-muted-foreground text-xs mb-1">
            <Clock size={12} />
            <span>Posts/Day</span>
          </div>
          <div className="text-lg font-semibold text-foreground">
            {lead.posting_frequency ? lead.posting_frequency.toFixed(2) : "—"}
          </div>
        </div>
      </div>

      {/* Extracted links */}
      {lead.extracted_links && lead.extracted_links.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-medium text-muted-foreground">
            Found Links ({lead.extracted_links.length})
          </h3>
          <div className="flex flex-wrap gap-2">
            {lead.extracted_links.map((link, idx) => (
              <a
                key={idx}
                href={link}
                target="_blank"
                rel="noopener noreferrer"
                className="link-badge inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium text-accent hover:bg-accent/20 transition-colors"
              >
                <span>{getLinkIcon(link)}</span>
                <span className="truncate max-w-[150px]">
                  {getLinkName(link)}
                </span>
                <ExternalLink size={10} className="flex-shrink-0" />
              </a>
            ))}
          </div>
        </div>
      )}

      {/* First/Last seen */}
      <div className="flex items-center justify-between text-xs text-muted-foreground pt-2 border-t border-border">
        <span>First seen: {new Date(lead.first_seen).toLocaleDateString()}</span>
        <span>Last seen: {new Date(lead.last_seen).toLocaleDateString()}</span>
      </div>
    </div>
  );
}


