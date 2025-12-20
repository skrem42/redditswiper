"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, ExternalLink, ChevronLeft, ChevronRight } from "lucide-react";
import type { RedditPost } from "@/lib/supabase";

interface ContentGalleryProps {
  posts: RedditPost[];
  username: string;
}

export function ContentGallery({ posts, username }: ContentGalleryProps) {
  const [selectedPost, setSelectedPost] = useState<RedditPost | null>(null);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);

  // Get all posts with media
  const postsWithMedia = posts.filter(
    (post) => post.media_urls && post.media_urls.length > 0
  );

  // Get all media from all posts for the lightbox
  const allMedia = postsWithMedia.flatMap((post) =>
    post.media_urls.map((url) => ({ url, post }))
  );

  const openLightbox = (post: RedditPost, mediaIndex: number) => {
    setSelectedPost(post);
    // Find the global index for this media item
    let globalIndex = 0;
    for (const p of postsWithMedia) {
      if (p.id === post.id) {
        globalIndex += mediaIndex;
        break;
      }
      globalIndex += p.media_urls.length;
    }
    setCurrentImageIndex(globalIndex);
  };

  const closeLightbox = useCallback(() => {
    setSelectedPost(null);
    setCurrentImageIndex(0);
  }, []);

  const nextImage = useCallback(() => {
    setCurrentImageIndex((prev) => (prev + 1) % allMedia.length);
  }, [allMedia.length]);

  const prevImage = useCallback(() => {
    setCurrentImageIndex(
      (prev) => (prev - 1 + allMedia.length) % allMedia.length
    );
  }, [allMedia.length]);

  // Keyboard navigation for lightbox
  useEffect(() => {
    if (!selectedPost) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        closeLightbox();
      } else if (e.key === "ArrowLeft") {
        prevImage();
      } else if (e.key === "ArrowRight") {
        nextImage();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [selectedPost, closeLightbox, nextImage, prevImage]);

  if (posts.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No posts found for this user
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Stats bar */}
      <div className="flex items-center justify-between text-sm text-muted-foreground px-1">
        <span>{posts.length} posts</span>
        <span>{postsWithMedia.length} with media</span>
      </div>

      {/* Posts grid */}
      <div className="space-y-3 max-h-[300px] overflow-y-auto pr-2">
        {posts.slice(0, 10).map((post) => (
          <div
            key={post.id}
            className="bg-secondary/50 rounded-lg p-3 space-y-2"
          >
            {/* Post title */}
            <div className="flex items-start justify-between gap-2">
              <h4 className="text-sm font-medium text-foreground line-clamp-2">
                {post.title || "No title"}
              </h4>
              {post.permalink && (
                <a
                  href={post.permalink}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-muted-foreground hover:text-accent transition-colors flex-shrink-0"
                >
                  <ExternalLink size={14} />
                </a>
              )}
            </div>

            {/* Post meta */}
            <div className="flex items-center gap-3 text-xs text-muted-foreground">
              <span className="text-primary">r/{post.subreddit_name}</span>
              <span>↑ {post.upvotes}</span>
              <span>💬 {post.num_comments}</span>
              {post.post_created_at && (
                <span>
                  {new Date(post.post_created_at).toLocaleDateString()}
                </span>
              )}
            </div>

            {/* Media thumbnails */}
            {post.media_urls && post.media_urls.length > 0 && (
              <div className="flex gap-2 overflow-x-auto pb-1">
                {post.media_urls.slice(0, 4).map((url, idx) => (
                  <button
                    key={idx}
                    onClick={() => openLightbox(post, idx)}
                    className="relative flex-shrink-0 w-16 h-16 rounded-md overflow-hidden gallery-item bg-muted"
                  >
                    <img
                      src={url}
                      alt={`Media ${idx + 1}`}
                      className="w-full h-full object-cover"
                      loading="lazy"
                    />
                    {post.media_urls.length > 4 && idx === 3 && (
                      <div className="absolute inset-0 bg-black/60 flex items-center justify-center text-white text-sm font-medium">
                        +{post.media_urls.length - 4}
                      </div>
                    )}
                  </button>
                ))}
              </div>
            )}

            {/* Post content preview */}
            {post.content && (
              <p className="text-xs text-muted-foreground line-clamp-2">
                {post.content}
              </p>
            )}
          </div>
        ))}

        {posts.length > 10 && (
          <div className="text-center text-sm text-muted-foreground py-2">
            + {posts.length - 10} more posts
          </div>
        )}
      </div>

      {/* Lightbox */}
      <AnimatePresence>
        {selectedPost && allMedia.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center"
            onClick={closeLightbox}
          >
            {/* Close button */}
            <button
              onClick={(e) => {
                e.stopPropagation();
                closeLightbox();
              }}
              className="absolute top-4 right-4 z-10 p-3 rounded-full bg-white/20 hover:bg-white/30 transition-colors"
            >
              <X size={28} className="text-white" />
            </button>

            {/* Navigation */}
            {allMedia.length > 1 && (
              <>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    prevImage();
                  }}
                  className="absolute left-4 p-3 rounded-full bg-white/10 hover:bg-white/20 transition-colors"
                >
                  <ChevronLeft size={24} className="text-white" />
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    nextImage();
                  }}
                  className="absolute right-4 p-3 rounded-full bg-white/10 hover:bg-white/20 transition-colors"
                >
                  <ChevronRight size={24} className="text-white" />
                </button>
              </>
            )}

            {/* Image */}
            <motion.div
              key={currentImageIndex}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="max-w-[90vw] max-h-[90vh]"
              onClick={(e) => e.stopPropagation()}
            >
              <img
                src={allMedia[currentImageIndex]?.url}
                alt="Full size"
                className="max-w-full max-h-[85vh] object-contain rounded-lg"
              />
              <div className="text-center mt-2 text-white/70 text-sm">
                {currentImageIndex + 1} / {allMedia.length}
              </div>
            </motion.div>

            {/* Post info */}
            <div className="absolute bottom-4 left-4 right-4 text-white/80 text-sm text-center">
              <a
                href={allMedia[currentImageIndex]?.post.permalink || "#"}
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-white transition-colors"
              >
                {allMedia[currentImageIndex]?.post.title || "View on Reddit"} →
              </a>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}


