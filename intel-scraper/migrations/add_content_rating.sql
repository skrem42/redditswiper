-- Add content rating columns to nsfw_subreddit_intel table
-- Run this in Supabase SQL editor

ALTER TABLE nsfw_subreddit_intel
ADD COLUMN IF NOT EXISTS content_rating TEXT,
ADD COLUMN IF NOT EXISTS content_rating_confidence TEXT,
ADD COLUMN IF NOT EXISTS content_rating_reasoning TEXT;

-- Add check constraint for valid content ratings
ALTER TABLE nsfw_subreddit_intel
ADD CONSTRAINT content_rating_check 
CHECK (content_rating IS NULL OR content_rating IN ('hardcore', 'softcore', 'uncertain'));

-- Add check constraint for valid confidence levels
ALTER TABLE nsfw_subreddit_intel
ADD CONSTRAINT content_rating_confidence_check 
CHECK (content_rating_confidence IS NULL OR content_rating_confidence IN ('high', 'medium', 'low'));

-- Create index for filtering by content rating
CREATE INDEX IF NOT EXISTS idx_nsfw_subreddit_intel_content_rating 
ON nsfw_subreddit_intel(content_rating);

-- Comments
COMMENT ON COLUMN nsfw_subreddit_intel.content_rating IS 'Content classification: hardcore (explicit acts), softcore (suggestive/sexy), or uncertain';
COMMENT ON COLUMN nsfw_subreddit_intel.content_rating_confidence IS 'Confidence level of the classification: high, medium, or low';
COMMENT ON COLUMN nsfw_subreddit_intel.content_rating_reasoning IS 'Brief explanation of why the subreddit was classified this way';

