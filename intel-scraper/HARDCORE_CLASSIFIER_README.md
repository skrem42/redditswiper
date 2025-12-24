# Hardcore/Softcore Content Classifier

Automatically classifies NSFW subreddits as "hardcore" or "softcore" using ChatGPT to determine their appropriateness for OnlyFans creator promotion.

## Classification Criteria

### Softcore (Appropriate for OF Promotion)
- Suggestive/sexy content without explicit sexual acts
- Bikini/lingerie photos, modeling poses
- Body appreciation subreddits (fit girls, petite, curves, etc.)
- Teasing/flirting content
- Amateur selfies that are sexy but not explicit
- **Examples:** legalteens, xsmallgirls, fitgirls, bikinis, gonewild, petite, curvy

### Hardcore (NOT Appropriate for OF Promotion)
- Explicit sexual acts clearly visible
- Pornographic content (penetration, oral sex, etc.)
- Graphic sexual content
- Content focused on explicit acts rather than just nudity/poses
- **Examples:** nsfwhardcore, porn, deepthroat, anal, blowjobs, cumsluts, latinchickswhitedicks

## Setup

### 1. Database Migration

First, add the required columns to your database. Run this in Supabase SQL editor:

```sql
-- Run the migration file
-- intel-scraper/migrations/add_content_rating.sql
```

Or manually execute:
```sql
ALTER TABLE nsfw_subreddit_intel
ADD COLUMN IF NOT EXISTS content_rating TEXT,
ADD COLUMN IF NOT EXISTS content_rating_confidence TEXT,
ADD COLUMN IF NOT EXISTS content_rating_reasoning TEXT;

-- Add constraints
ALTER TABLE nsfw_subreddit_intel
ADD CONSTRAINT content_rating_check 
CHECK (content_rating IS NULL OR content_rating IN ('hardcore', 'softcore', 'uncertain'));

ALTER TABLE nsfw_subreddit_intel
ADD CONSTRAINT content_rating_confidence_check 
CHECK (content_rating_confidence IS NULL OR content_rating_confidence IN ('high', 'medium', 'low'));

-- Add index
CREATE INDEX IF NOT EXISTS idx_nsfw_subreddit_intel_content_rating 
ON nsfw_subreddit_intel(content_rating);
```

### 2. Environment Variables

Ensure you have `OPENAI_API_KEY` set in your `/scraper/.env` file:

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

## Usage

### Continuous Mode (Production)

Process all unclassified subreddits continuously:

```bash
cd intel-scraper
python hardcore_classifier.py
```

With custom settings:
```bash
python hardcore_classifier.py --batch-size 100 --concurrency 10
```

### Test Mode

Test classification on specific subreddits:

```bash
# Test a few subreddits
python hardcore_classifier.py --test legalteens fitgirls nsfwhardcore porn deepthroat

# Output example:
# Classified r/legalteens as softcore (confidence: high)
# Classified r/fitgirls as softcore (confidence: high)
# Classified r/nsfwhardcore as hardcore (confidence: high)
# Classified r/porn as hardcore (confidence: high)
# Classified r/deepthroat as hardcore (confidence: high)
```

## Options

- `--batch-size N` - Number of subreddits to process per batch (default: 50)
- `--concurrency N` - Number of concurrent API calls (default: 5)
- `--test SUBREDDIT1 SUBREDDIT2 ...` - Test mode with specific subreddits

## How It Works

1. **Fetches Subreddit Data:** Gets subreddit info from Reddit's JSON API (`/r/{subreddit}/about.json`)
2. **Sends to ChatGPT:** Uses GPT-4o-mini to analyze:
   - Subreddit name
   - Description
   - Title
   - Subscriber count
3. **Classifies Content:** Returns one of three ratings:
   - `hardcore` - Explicit sexual content
   - `softcore` - Suggestive/sexy but not explicit
   - `uncertain` - Unable to determine
4. **Updates Database:** Saves classification with confidence level and reasoning

## Database Schema

New columns in `nsfw_subreddit_intel`:

| Column | Type | Description |
|--------|------|-------------|
| `content_rating` | TEXT | Classification: 'hardcore', 'softcore', or 'uncertain' |
| `content_rating_confidence` | TEXT | Confidence: 'high', 'medium', or 'low' |
| `content_rating_reasoning` | TEXT | Brief explanation of the classification |

## Cost

Uses OpenAI GPT-4o-mini:
- **Cost:** ~$0.0002 per subreddit
- **Rate:** ~50-100 subreddits per minute (depending on concurrency)
- **Total Cost for 2000 subreddits:** ~$0.40

## Filtering in Frontend

Once classified, you can filter subreddits in your app:

```typescript
// Only show softcore subs appropriate for OF promotion
const { data } = await supabase
  .from('nsfw_subreddit_intel')
  .select('*')
  .eq('content_rating', 'softcore')
  .order('subscribers', { ascending: false });
```

## Edge Cases

The classifier handles ambiguous cases by:
- Leaning toward "softcore" for nude modeling/posing subreddits
- Only marking "hardcore" if there's clear indication of explicit acts
- Using "uncertain" when the name/description is ambiguous

## Monitoring

The worker outputs real-time statistics:

```
📊 Total: 127 classified (45 hardcore, 78 softcore, 4 uncertain, 0 failed) - 254.0/hour
```

## Running Continuously

To run the classifier as a background service:

```bash
# Using nohup
nohup python hardcore_classifier.py > classifier.log 2>&1 &

# Using screen
screen -S classifier
python hardcore_classifier.py
# Press Ctrl+A, then D to detach
```

## Troubleshooting

### "All subreddits classified!"
This means all existing subreddits have been classified. The worker will wait 5 minutes and check again for new ones.

### Rate Limiting
If you hit OpenAI rate limits, reduce `--concurrency`:
```bash
python hardcore_classifier.py --concurrency 3
```

### Reddit API 429 Errors
The classifier includes retry logic with exponential backoff. If issues persist, reduce batch size:
```bash
python hardcore_classifier.py --batch-size 20
```

