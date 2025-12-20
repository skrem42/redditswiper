# Reddit OnlyFans Lead Scraper

A complete system for discovering and qualifying OnlyFans creator leads from Reddit. Includes a Python scraper that finds NSFW subreddits, aggregates posts by user, and stores comprehensive profile data in Supabase. The React/Next.js frontend provides a Tinder-style swipe interface for reviewing leads.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Python Scraper                            │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────┐ │
│  │  Discover    │ → │ Fetch Posts  │ → │ Group by User &      │ │
│  │  Subreddits  │   │ via .json    │   │ Fetch Profile Data   │ │
│  └──────────────┘   └──────────────┘   └──────────────────────┘ │
└─────────────────────────────┬───────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                         Supabase                                 │
│  ┌──────────────┐ ┌──────────────┐ ┌─────────┐ ┌─────────────┐  │
│  │ reddit_leads │ │ reddit_posts │ │subreddit│ │lead_decision│  │
│  └──────────────┘ └──────────────┘ └─────────┘ └─────────────┘  │
└─────────────────────────────┬───────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     Next.js Frontend                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Tinder-Style Swipe Interface                 │   │
│  │  ← Reject                                        Approve →│   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Features

### Scraper
- 🔍 Discovers NSFW subreddits containing "onlyfans" in the name
- 📊 Fetches posts using Reddit's public `.json` API
- 👤 Groups posts by user and fetches comprehensive profile data
- 🔗 Extracts OnlyFans, Linktree, and other platform links
- 💾 Stores all data in Supabase with proper deduplication

### Frontend
- 💫 Tinder-style swipe interface with gesture support
- ⌨️ Keyboard shortcuts (Arrow keys or A/D for swiping)
- 📸 Content gallery with lightbox for media preview
- 📈 Stats dashboard showing lead pipeline
- 🔄 Filter between pending/approved/rejected leads

## Setup

### 1. Environment Variables

**For the Python scraper**, create `scraper/.env`:

```bash
# Supabase Configuration
SUPABASE_URL=https://jmchmbwhnmlednaycxqh.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImptY2htYndobm1sZWRuYXljeHFoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjMzODI4MzYsImV4cCI6MjA3ODk1ODgzNn0.Ux8SqBEj1isHUGIiGh4I-MM54dUb3sd0D7VsRjRKDuU

# Scraper Configuration (optional)
SCRAPE_DELAY_SECONDS=2
MAX_POSTS_PER_SUBREDDIT=100
MAX_SUBREDDITS=50
```

**For the frontend**, create `frontend/.env.local`:

```bash
NEXT_PUBLIC_SUPABASE_URL=https://jmchmbwhnmlednaycxqh.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImptY2htYndobm1sZWRuYXljeHFoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjMzODI4MzYsImV4cCI6MjA3ODk1ODgzNn0.Ux8SqBEj1isHUGIiGh4I-MM54dUb3sd0D7VsRjRKDuU
```

Or run with environment variables inline:

```bash
# Frontend
cd frontend
NEXT_PUBLIC_SUPABASE_URL=https://jmchmbwhnmlednaycxqh.supabase.co \
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key \
npm run dev
```

### 2. Python Scraper Setup

```bash
cd scraper

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the scraper
python main.py              # Full scrape: discover subs + scrape posts
python main.py --discover   # Only discover new subreddits
python main.py --scrape     # Only scrape posts from known subreddits
python main.py --stats      # Show scraping statistics
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to access the lead swiper.

## Database Schema

### reddit_leads
Core lead table with aggregated user data:
- `reddit_username` - Reddit username
- `karma` - Total karma (link + comment)
- `account_created_at` - Account creation date
- `avatar_url`, `banner_url` - Profile images
- `total_posts` - Number of posts scraped
- `posting_frequency` - Posts per day
- `extracted_links` - Array of OnlyFans/Linktree URLs
- `bio` - User bio/description
- `status` - pending/approved/rejected/contacted

### reddit_posts
All scraped content:
- `reddit_post_id` - Reddit's post ID
- `lead_id` - Foreign key to reddit_leads
- `title`, `content` - Post text
- `media_urls` - Array of image/video URLs
- `upvotes`, `num_comments` - Engagement metrics
- `subreddit_name` - Source subreddit

### subreddits
Discovered NSFW subreddits:
- `name` - Subreddit name
- `subscribers` - Subscriber count
- `last_scraped` - Last scrape timestamp

### lead_decisions
Qualification history:
- `lead_id` - Foreign key to reddit_leads
- `decision` - approved/rejected
- `notes` - Optional notes
- `decided_at` - Decision timestamp

## Rate Limiting

Reddit's public JSON API has rate limits. The scraper implements:
- 2-second delays between requests (configurable)
- Exponential backoff on 429 (rate limit) errors
- Caching of subreddit lists to avoid redundant discovery

## License

MIT

