"use client";

import { useState, useEffect, useMemo } from "react";
import { motion, useMotionValue, useTransform, PanInfo, AnimatePresence } from "framer-motion";
import { X, Heart, ExternalLink, ChevronLeft, ChevronRight, TrendingUp, Clock, FileText, Star, ThumbsUp } from "lucide-react";
import type { RedditLead } from "@/lib/supabase";

interface SwipeCardProps {
  lead: RedditLead;
  onSwipe: (direction: "left" | "right") => void;
  onSuperLike?: () => void;
  isActive: boolean;
}

export function SwipeCard({ lead, onSwipe, onSuperLike, isActive }: SwipeCardProps) {
  const [exitDirection, setExitDirection] = useState<"left" | "right" | "up" | null>(null);
  const [carouselIndex, setCarouselIndex] = useState(0);
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const x = useMotionValue(0);
  const rotate = useTransform(x, [-300, 0, 300], [-15, 0, 15]);
  const opacity = useTransform(x, [-300, -100, 0, 100, 300], [0.5, 1, 1, 1, 0.5]);

  // Overlay indicators
  const rejectOpacity = useTransform(x, [-150, 0], [1, 0]);
  const approveOpacity = useTransform(x, [0, 150], [0, 1]);

  // Extract and analyze links - check bio, extracted_links, and post content
  const linkAnalysis = useMemo(() => {
    const links = [...(lead.extracted_links || [])];
    const urlRegex = /https?:\/\/[^\s<>"{}|\\^`\[\]]+/gi;
    const ofUsernameRegex = /onlyfans\.com\/[\w\-.]+/gi;
    
    const extractUrls = (text: string) => {
      if (!text) return;
      const urlMatches = text.match(urlRegex) || [];
      urlMatches.forEach(l => {
        if (!links.includes(l)) links.push(l);
      });
      const ofMatches = text.match(ofUsernameRegex) || [];
      ofMatches.forEach(m => {
        const fullUrl = m.startsWith('http') ? m : `https://${m}`;
        if (!links.includes(fullUrl)) links.push(fullUrl);
      });
    };
    
    extractUrls(lead.bio || '');
    
    if (lead.reddit_posts) {
      lead.reddit_posts.forEach(post => {
        extractUrls(post.title || '');
        extractUrls(post.content || '');
      });
    }
    
    let ofLinks = links.filter(l => l.toLowerCase().includes("onlyfans.com"));
    const bioMentionsOF = lead.bio && /\b(onlyfans|only\s*fans|\bof\b)/i.test(lead.bio);
    const likelyOFLink = `https://onlyfans.com/${lead.reddit_username.toLowerCase()}`;
    
    if (ofLinks.length === 0 && bioMentionsOF) {
      ofLinks = [likelyOFLink];
    }
    
    const hasOF = ofLinks.length > 0;
    const hasTracking = ofLinks.some(l => /\/c\d+/i.test(l));
    const bioIndicatesOF = bioMentionsOF && ofLinks[0] === likelyOFLink;
    const linktreeLinks = links.filter(l => 
      /linktr\.ee|beacons\.ai|allmylinks|solo\.to|linkr\.bio/i.test(l)
    );
    const hasLinktree = linktreeLinks.length > 0;
    const socialLinks = links.filter(l =>
      /instagram|twitter|x\.com|tiktok|snapchat|telegram/i.test(l)
    );
    const hasSocials = socialLinks.length > 0;
    
    return { ofLinks, hasOF, hasTracking, linktreeLinks, hasLinktree, socialLinks, hasSocials, allLinks: links, bioIndicatesOF };
  }, [lead.extracted_links, lead.bio, lead.reddit_posts, lead.reddit_username]);

  // Get unique media - show up to 12 images
  const mediaUrls = useMemo(() => {
    if (!lead.reddit_posts) return [];
    const allUrls = lead.reddit_posts.flatMap(p => p.media_urls || []);
    const unique = [...new Set(allUrls)];
    // Shuffle for variety
    for (let i = unique.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [unique[i], unique[j]] = [unique[j], unique[i]];
    }
    return unique.slice(0, 12);
  }, [lead.reddit_posts]);

  // Preload images for faster viewing
  useEffect(() => {
    mediaUrls.forEach((url) => {
      const img = new Image();
      img.src = url;
    });
  }, [mediaUrls]);

  // Calculate carousel pages (3 images per page)
  const IMAGES_PER_PAGE = 3;
  const totalPages = Math.ceil(mediaUrls.length / IMAGES_PER_PAGE);
  const currentPageImages = mediaUrls.slice(
    carouselIndex * IMAGES_PER_PAGE, 
    (carouselIndex + 1) * IMAGES_PER_PAGE
  );

  // Get unique subreddits where this lead was found
  const foundInSubreddits = useMemo(() => {
    if (!lead.reddit_posts) return [];
    const subs = new Set<string>();
    lead.reddit_posts.forEach(post => {
      if (post.subreddit_name) {
        subs.add(post.subreddit_name);
      }
    });
    return Array.from(subs).sort();
  }, [lead.reddit_posts]);

  // Stats calculations
  const stats = useMemo(() => {
    const accountDays = lead.account_created_at 
      ? Math.floor((Date.now() - new Date(lead.account_created_at).getTime()) / (1000 * 60 * 60 * 24))
      : 0;
    
    let accountAge = "Unknown";
    if (accountDays > 0) {
      if (accountDays < 30) accountAge = `${accountDays}d`;
      else if (accountDays < 365) accountAge = `${Math.floor(accountDays / 30)}mo`;
      else accountAge = `${(accountDays / 365).toFixed(1)}yr`;
    }
    
    // Use posting_frequency from scraper if available, otherwise calculate
    let postsPerDay: string;
    if (lead.posting_frequency !== null && lead.posting_frequency !== undefined) {
      postsPerDay = Number(lead.posting_frequency).toFixed(2);
    } else if (accountDays > 0 && lead.total_posts > 0) {
      postsPerDay = (lead.total_posts / accountDays).toFixed(2);
    } else {
      postsPerDay = "—";
    }
    
    // Calculate average upvotes from scraped posts
    let avgUpvotes: string;
    if (lead.reddit_posts && lead.reddit_posts.length > 0) {
      const totalUpvotes = lead.reddit_posts.reduce((sum, post) => sum + (post.upvotes || 0), 0);
      const avg = totalUpvotes / lead.reddit_posts.length;
      if (avg >= 1000) {
        avgUpvotes = `${(avg / 1000).toFixed(1)}k`;
      } else {
        avgUpvotes = Math.round(avg).toString();
      }
    } else {
      avgUpvotes = "—";
    }
    
    return { accountAge, accountDays, postsPerDay, avgUpvotes };
  }, [lead.account_created_at, lead.total_posts, lead.posting_frequency, lead.reddit_posts]);

  const handleDragEnd = (_: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => {
    const threshold = 150;
    if (info.offset.x > threshold) {
      setExitDirection("right");
      onSwipe("right");
    } else if (info.offset.x < -threshold) {
      setExitDirection("left");
      onSwipe("left");
    }
  };

  const handleButtonSwipe = (direction: "left" | "right") => {
    setExitDirection(direction);
    onSwipe(direction);
  };

  const handleSuperLike = () => {
    if (onSuperLike) {
      setExitDirection("up");
      onSuperLike();
    }
  };

  // Track which image in lightbox
  const [lightboxImageIndex, setLightboxImageIndex] = useState(0);

  // Keyboard controls
  useEffect(() => {
    if (!isActive) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      // Lightbox mode - arrow keys navigate images, escape closes
      if (lightboxOpen) {
        if (e.key === "Escape") {
          setLightboxOpen(false);
        } else if (e.key === "ArrowLeft" && lightboxImageIndex > 0) {
          setLightboxImageIndex(lightboxImageIndex - 1);
        } else if (e.key === "ArrowRight" && lightboxImageIndex < mediaUrls.length - 1) {
          setLightboxImageIndex(lightboxImageIndex + 1);
        }
        return;
      }
      
      // Card swipe controls - A/D for swipe, arrows for page navigation
      if (e.key === "a") {
        handleButtonSwipe("left");
      } else if (e.key === "d") {
        handleButtonSwipe("right");
      } else if (e.key === "ArrowUp" || e.key === "w" || e.key === "s") {
        handleSuperLike();
      } else if (e.key === "ArrowLeft" && totalPages > 1) {
        setCarouselIndex(prev => Math.max(0, prev - 1));
      } else if (e.key === "ArrowRight" && totalPages > 1) {
        setCarouselIndex(prev => Math.min(totalPages - 1, prev + 1));
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isActive, lightboxOpen, lightboxImageIndex, carouselIndex, mediaUrls.length, totalPages, onSuperLike]);

  const exitVariants = {
    left: { x: -500, rotate: -30, opacity: 0, transition: { duration: 0.4, ease: "easeOut" } },
    right: { x: 500, rotate: 30, opacity: 0, transition: { duration: 0.4, ease: "easeOut" } },
    up: { y: -500, scale: 1.1, opacity: 0, transition: { duration: 0.4, ease: "easeOut" } },
  };

  return (
    <>
      <motion.div
        className="absolute inset-0 flex items-center justify-center"
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={exitDirection ? exitVariants[exitDirection] : { opacity: 0, scale: 0.8 }}
        transition={{ duration: 0.3 }}
      >
        <motion.div
          className="relative w-full max-w-xl bg-card rounded-2xl card-shadow overflow-hidden cursor-grab active:cursor-grabbing"
          style={{ x, rotate, opacity }}
          drag={isActive ? "x" : false}
          dragConstraints={{ left: 0, right: 0 }}
          dragElastic={0.7}
          onDragEnd={handleDragEnd}
          whileTap={{ scale: 0.98 }}
        >
          {/* Swipe indicators */}
          <motion.div
            className="absolute top-4 left-4 z-20 px-4 py-2 bg-destructive/90 rounded-lg text-white font-bold text-lg rotate-[-15deg] border-2 border-white"
            style={{ opacity: rejectOpacity }}
          >
            NOPE
          </motion.div>
          <motion.div
            className="absolute top-4 right-4 z-20 px-4 py-2 bg-success/90 rounded-lg text-white font-bold text-lg rotate-[15deg] border-2 border-white"
            style={{ opacity: approveOpacity }}
          >
            YES!
          </motion.div>

          {/* Content area - no scrolling needed now */}
          <div onPointerDownCapture={(e) => e.stopPropagation()}>
            {/* 3-Image Carousel */}
            {mediaUrls.length > 0 ? (
              <div className="relative bg-black/30 p-2">
                {/* 3-image grid */}
                <div className="grid grid-cols-3 gap-1.5">
                  {currentPageImages.map((url, i) => {
                    const globalIndex = carouselIndex * IMAGES_PER_PAGE + i;
                    return (
                      <button
                        key={globalIndex}
                        onClick={() => {
                          setLightboxImageIndex(globalIndex);
                          setLightboxOpen(true);
                        }}
                        className="relative aspect-[3/4] overflow-hidden rounded-lg cursor-pointer group bg-muted"
                      >
                        <img
                          src={url}
                          alt={`Preview ${globalIndex + 1}`}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
                          loading="eager"
                        />
                        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors" />
                      </button>
                    );
                  })}
                  {/* Fill empty slots if less than 3 images on last page */}
                  {currentPageImages.length < IMAGES_PER_PAGE && 
                    Array(IMAGES_PER_PAGE - currentPageImages.length).fill(0).map((_, i) => (
                      <div key={`empty-${i}`} className="aspect-[3/4] rounded-lg bg-muted/20" />
                    ))
                  }
                </div>

                {/* Page navigation - only show if multiple pages */}
                {totalPages > 1 && (
                  <>
                    {carouselIndex > 0 && (
                      <button
                        onClick={() => setCarouselIndex(carouselIndex - 1)}
                        className="absolute left-0 top-1/2 -translate-y-1/2 p-1.5 rounded-r-lg bg-black/60 hover:bg-black/80 transition-colors"
                      >
                        <ChevronLeft size={18} className="text-white" />
                      </button>
                    )}
                    {carouselIndex < totalPages - 1 && (
                      <button
                        onClick={() => setCarouselIndex(carouselIndex + 1)}
                        className="absolute right-0 top-1/2 -translate-y-1/2 p-1.5 rounded-l-lg bg-black/60 hover:bg-black/80 transition-colors"
                      >
                        <ChevronRight size={18} className="text-white" />
                      </button>
                    )}
                  </>
                )}

                {/* Page indicator & count */}
                <div className="flex items-center justify-center gap-2 mt-2">
                  {totalPages > 1 && (
                    <div className="flex items-center gap-1">
                      {Array(totalPages).fill(0).map((_, i) => (
                        <button
                          key={i}
                          onClick={() => setCarouselIndex(i)}
                          className={`w-1.5 h-1.5 rounded-full transition-all ${
                            i === carouselIndex 
                              ? 'bg-white w-3' 
                              : 'bg-white/40 hover:bg-white/60'
                          }`}
                        />
                      ))}
                    </div>
                  )}
                  <span className="text-[10px] text-white/60">
                    {mediaUrls.length} photos
                  </span>
                </div>
              </div>
            ) : (
              <div className="h-20 bg-gradient-to-br from-primary/20 via-accent/20 to-purple-500/20 flex items-center justify-center">
                <span className="text-muted-foreground text-sm">No media available</span>
              </div>
            )}

            {/* Stats Bar - Prominent */}
            <div className="grid grid-cols-4 gap-1 p-3 bg-gradient-to-r from-primary/10 via-accent/10 to-purple-500/10 border-y border-border/50">
              <div className="flex flex-col items-center justify-center text-center">
                <TrendingUp size={14} className="text-emerald-400 mb-1" />
                <div className="text-sm font-bold text-foreground">{lead.karma.toLocaleString()}</div>
                <div className="text-[9px] text-muted-foreground uppercase tracking-wide">Karma</div>
              </div>
              <div className="flex flex-col items-center justify-center text-center border-l border-border/30">
                <FileText size={14} className="text-sky-400 mb-1" />
                <div className="text-sm font-bold text-foreground">{stats.postsPerDay}</div>
                <div className="text-[9px] text-muted-foreground uppercase tracking-wide">Posts/Day</div>
              </div>
              <div className="flex flex-col items-center justify-center text-center border-l border-border/30">
                <ThumbsUp size={14} className="text-rose-400 mb-1" />
                <div className="text-sm font-bold text-foreground">{stats.avgUpvotes}</div>
                <div className="text-[9px] text-muted-foreground uppercase tracking-wide">Avg Upvotes</div>
              </div>
              <div className="flex flex-col items-center justify-center text-center border-l border-border/30">
                <Clock size={14} className="text-amber-400 mb-1" />
                <div className="text-sm font-bold text-foreground">{stats.accountAge}</div>
                <div className="text-[9px] text-muted-foreground uppercase tracking-wide">Age</div>
              </div>
            </div>

            {/* Indicator Badges Row */}
            <div className="grid grid-cols-4 gap-2 p-3 bg-secondary/20">
              <div className={`rounded-lg p-2 text-center ${
                linkAnalysis.hasOF 
                  ? linkAnalysis.bioIndicatesOF 
                    ? 'bg-amber-500/20 border border-amber-500/40' 
                    : 'bg-sky-500/20 border border-sky-500/40' 
                  : 'bg-muted/30'
              }`}>
                <div className="text-lg">🔥</div>
                <div className={`text-[10px] font-medium ${
                  linkAnalysis.hasOF 
                    ? linkAnalysis.bioIndicatesOF ? 'text-amber-400' : 'text-sky-400' 
                    : 'text-muted-foreground'
                }`}>
                  {linkAnalysis.hasOF ? linkAnalysis.bioIndicatesOF ? 'OF Likely' : 'OF Found' : 'No OF'}
                </div>
              </div>
              
              <div className={`rounded-lg p-2 text-center ${
                linkAnalysis.hasTracking 
                  ? 'bg-amber-500/20 border border-amber-500/40' 
                  : linkAnalysis.hasOF ? 'bg-emerald-500/20 border border-emerald-500/40' : 'bg-muted/30'
              }`}>
                <div className="text-lg">{linkAnalysis.hasTracking ? '🏷️' : linkAnalysis.hasOF ? '✓' : '—'}</div>
                <div className={`text-[10px] font-medium ${
                  linkAnalysis.hasTracking ? 'text-amber-400' : linkAnalysis.hasOF ? 'text-emerald-400' : 'text-muted-foreground'
                }`}>
                  {linkAnalysis.hasTracking ? 'Agency?' : linkAnalysis.hasOF ? 'No Track' : '—'}
                </div>
              </div>
              
              <div className={`rounded-lg p-2 text-center ${linkAnalysis.hasLinktree ? 'bg-emerald-500/20 border border-emerald-500/40' : 'bg-muted/30'}`}>
                <div className="text-lg">🌳</div>
                <div className={`text-[10px] font-medium ${linkAnalysis.hasLinktree ? 'text-emerald-400' : 'text-muted-foreground'}`}>
                  {linkAnalysis.hasLinktree ? 'Linktree' : 'No Link'}
                </div>
              </div>
              
              <div className={`rounded-lg p-2 text-center ${linkAnalysis.hasSocials ? 'bg-purple-500/20 border border-purple-500/40' : 'bg-muted/30'}`}>
                <div className="text-lg">📱</div>
                <div className={`text-[10px] font-medium ${linkAnalysis.hasSocials ? 'text-purple-400' : 'text-muted-foreground'}`}>
                  {linkAnalysis.hasSocials ? `${linkAnalysis.socialLinks.length} Social` : 'None'}
                </div>
              </div>
            </div>

            {/* User Info Section */}
            <div className="p-4 space-y-3">
              {/* Header with avatar and username */}
              <div className="flex items-center gap-3">
                {lead.avatar_url ? (
                  <img
                    src={lead.avatar_url}
                    alt={lead.reddit_username}
                    className="w-12 h-12 rounded-full object-cover border-2 border-primary/30"
                  />
                ) : (
                  <div className="w-12 h-12 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center text-xl font-bold text-white">
                    {lead.reddit_username.charAt(0).toUpperCase()}
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h2 className="text-lg font-bold text-foreground truncate">
                      u/{lead.reddit_username}
                    </h2>
                    <a
                      href={lead.profile_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-muted-foreground hover:text-accent transition-colors"
                    >
                      <ExternalLink size={14} />
                    </a>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {lead.total_posts} total posts
                  </div>
                </div>
              </div>

              {/* Found in subreddits */}
              {foundInSubreddits.length > 0 && (
                <div className="flex flex-col gap-1.5">
                  <div className="text-[10px] text-muted-foreground uppercase tracking-wide font-medium">
                    Found in {foundInSubreddits.length} sub{foundInSubreddits.length > 1 ? 's' : ''}
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {foundInSubreddits.map((subName) => (
                      <a
                        key={subName}
                        href={`https://reddit.com/r/${subName}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-2 py-1 rounded-md bg-primary/10 text-primary text-xs font-medium hover:bg-primary/20 transition-colors border border-primary/20"
                      >
                        r/{subName}
                      </a>
                    ))}
                  </div>
                </div>
              )}

              {/* Bio */}
              {lead.bio && (
                <p className="text-sm text-muted-foreground bg-secondary/30 rounded-lg p-3">
                  {lead.bio}
                </p>
              )}

              {/* Quick Action Links */}
              <div className="flex flex-wrap gap-2">
                {/* OnlyFans Button - or Check Bio for Links if no OF found */}
                {linkAnalysis.ofLinks.length > 0 ? (
                  <a
                    href={linkAnalysis.ofLinks[0]}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={`flex items-center gap-2 px-4 py-2.5 rounded-lg font-medium transition-colors shadow-lg text-sm ${
                      linkAnalysis.bioIndicatesOF 
                        ? 'bg-amber-500 text-white hover:bg-amber-600 shadow-amber-500/20' 
                        : 'bg-sky-500 text-white hover:bg-sky-600 shadow-sky-500/20'
                    }`}
                  >
                    🔥 {linkAnalysis.bioIndicatesOF ? 'Check OnlyFans' : 'View OnlyFans'}
                    <ExternalLink size={14} />
                  </a>
                ) : (
                  // No OF link found - show button to check their bio/profile for links
                  <a
                    href={lead.profile_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-pink-500 to-rose-500 text-white rounded-lg font-medium hover:from-pink-600 hover:to-rose-600 transition-colors shadow-lg shadow-pink-500/20 text-sm"
                  >
                    🔍 Check Bio for Links
                    <ExternalLink size={14} />
                  </a>
                )}

                {/* Linktree Button */}
                {linkAnalysis.linktreeLinks.length > 0 && (
                  <a
                    href={linkAnalysis.linktreeLinks[0]}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 px-4 py-2 bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 rounded-lg font-medium hover:bg-emerald-500/30 transition-colors text-sm"
                  >
                    🌳 Linktree
                    <ExternalLink size={12} />
                  </a>
                )}

                {/* Reddit Profile - only show if we have an OF link (otherwise the "Check Bio" button covers this) */}
                {linkAnalysis.ofLinks.length > 0 && (
                  <a
                    href={lead.profile_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 px-4 py-2 bg-orange-500/20 text-orange-400 border border-orange-500/40 rounded-lg font-medium hover:bg-orange-500/30 transition-colors text-sm"
                  >
                    Reddit Profile
                    <ExternalLink size={12} />
                  </a>
                )}
              </div>
            </div>
          </div>

          {/* Action buttons */}
          <div 
            className="flex items-center justify-center gap-4 p-4 bg-card border-t border-border"
            onPointerDownCapture={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => handleButtonSwipe("left")}
              className="w-14 h-14 rounded-full bg-destructive/10 border-2 border-destructive text-destructive flex items-center justify-center hover:bg-destructive hover:text-white transition-all btn-glow-red"
              title="Reject (← or A)"
            >
              <X size={24} strokeWidth={3} />
            </button>
            
            {/* Super Like button */}
            {onSuperLike && (
              <button
                onClick={handleSuperLike}
                className="w-12 h-12 rounded-full bg-amber-500/10 border-2 border-amber-500 text-amber-500 flex items-center justify-center hover:bg-amber-500 hover:text-white transition-all shadow-lg shadow-amber-500/20"
                title="Super Like (↑ or S)"
              >
                <Star size={20} strokeWidth={2.5} fill="currentColor" />
              </button>
            )}
            
            <button
              onClick={() => handleButtonSwipe("right")}
              className="w-14 h-14 rounded-full bg-success/10 border-2 border-success text-success flex items-center justify-center hover:bg-success hover:text-white transition-all btn-glow-green"
              title="Approve (→ or D)"
            >
              <Heart size={24} strokeWidth={2.5} fill="currentColor" />
            </button>
          </div>
        </motion.div>
      </motion.div>

      {/* Lightbox for full-size image preview */}
      <AnimatePresence>
        {lightboxOpen && mediaUrls.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/95 flex items-center justify-center"
            onClick={() => setLightboxOpen(false)}
          >
            {/* Close button */}
            <button
              onClick={(e) => {
                e.stopPropagation();
                setLightboxOpen(false);
              }}
              className="absolute top-4 right-4 z-10 p-3 rounded-full bg-white/20 hover:bg-white/30 transition-colors"
            >
              <X size={28} className="text-white" />
            </button>

            {/* Image counter */}
            <div className="absolute top-4 left-4 text-white/80 text-sm font-medium bg-black/40 px-3 py-1 rounded-full">
              {lightboxImageIndex + 1} / {mediaUrls.length}
            </div>

            {/* Navigation arrows */}
            {lightboxImageIndex > 0 && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setLightboxImageIndex(lightboxImageIndex - 1);
                }}
                className="absolute left-4 top-1/2 -translate-y-1/2 p-3 rounded-full bg-white/20 hover:bg-white/30 transition-colors"
              >
                <ChevronLeft size={32} className="text-white" />
              </button>
            )}
            {lightboxImageIndex < mediaUrls.length - 1 && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setLightboxImageIndex(lightboxImageIndex + 1);
                }}
                className="absolute right-4 top-1/2 -translate-y-1/2 p-3 rounded-full bg-white/20 hover:bg-white/30 transition-colors"
              >
                <ChevronRight size={32} className="text-white" />
              </button>
            )}

            {/* Main image */}
            <motion.img
              key={lightboxImageIndex}
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              src={mediaUrls[lightboxImageIndex]}
              alt={`Full preview ${lightboxImageIndex + 1}`}
              className="max-h-[90vh] max-w-[90vw] object-contain rounded-lg"
              onClick={(e) => e.stopPropagation()}
            />

            {/* Keyboard hint */}
            <div className="absolute bottom-4 left-1/2 -translate-x-1/2 text-white/60 text-xs flex items-center gap-4">
              <span>← → Navigate</span>
              <span>ESC Close</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
