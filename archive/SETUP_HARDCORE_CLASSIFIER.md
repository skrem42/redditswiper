# Setup Instructions: Hardcore/Softcore Classifier

I've created a new worker that classifies subreddits as "hardcore" or "softcore" to help identify which are appropriate for OF creator promotion.

## ✅ What's Been Created

1. **`hardcore_classifier.py`** - Main worker script
2. **`migrations/add_content_rating.sql`** - Database migration
3. **`HARDCORE_CLASSIFIER_README.md`** - Full documentation
4. Updated frontend TypeScript types to include new fields
5. Updated `requirements.txt` to include `openai`

## 🚀 Setup Steps

### 1. Run Database Migration

**Option A: Using Supabase Dashboard (Recommended)**

1. Go to https://supabase.com/dashboard/project/YOUR_PROJECT_ID/sql
2. Copy and paste the contents of `intel-scraper/migrations/add_content_rating.sql`
3. Click "Run"

**Option B: Using psql**

```bash
psql $DATABASE_URL < intel-scraper/migrations/add_content_rating.sql
```

This will add three new columns to `nsfw_subreddit_intel`:
- `content_rating` - 'hardcore', 'softcore', or 'uncertain'
- `content_rating_confidence` - 'high', 'medium', or 'low'
- `content_rating_reasoning` - Brief explanation

### 2. Set OpenAI API Key

The classifier uses GPT-4o-mini which costs ~$0.0002 per subreddit.

Add your OpenAI API key to `/scraper/.env`:

```bash
OPENAI_API_KEY=sk-proj-YOUR_REAL_API_KEY_HERE
```

You can get an API key from: https://platform.openai.com/api-keys

### 3. Install Dependencies

```bash
cd /Users/calummelling/Desktop/redditscraper
source venv/bin/activate
pip install openai
```

## 🧪 Test the Classifier

Test with a few example subreddits:

```bash
cd intel-scraper
source ../venv/bin/activate
python hardcore_classifier.py --test legalteens fitgirls nsfwhardcore porn deepthroat
```

**Expected output:**
```
Classified r/legalteens as softcore (confidence: high)
Classified r/fitgirls as softcore (confidence: high)
Classified r/nsfwhardcore as hardcore (confidence: high)
Classified r/porn as hardcore (confidence: high)
Classified r/deepthroat as hardcore (confidence: high)
```

## 🏃 Run the Classifier

### Continuous Mode (Recommended)

Process all unclassified subreddits automatically:

```bash
cd intel-scraper
source ../venv/bin/activate
python hardcore_classifier.py --batch-size 50 --concurrency 5
```

The worker will:
1. Find all subreddits in `nsfw_subreddit_intel` that don't have a `content_rating`
2. Fetch their data from Reddit's JSON API
3. Send to ChatGPT for classification
4. Update the database with the result
5. Repeat until all are classified

### Run as Background Service

```bash
# Using nohup
cd intel-scraper
source ../venv/bin/activate
nohup python hardcore_classifier.py > ../logs/classifier.log 2>&1 &

# Using screen (recommended)
screen -S classifier
cd intel-scraper
source ../venv/bin/activate
python hardcore_classifier.py
# Press Ctrl+A then D to detach
```

## 📊 Classification Logic

### Softcore (Appropriate for OF Promotion)
- Suggestive/sexy content without explicit acts
- Examples: legalteens, xsmallgirls, fitgirls, bikinis, gonewild, petite, curvy

### Hardcore (NOT Appropriate for OF Promotion)  
- Explicit sexual acts clearly visible
- Examples: nsfwhardcore, porn, deepthroat, anal, blowjobs, cumsluts

### Key Distinction
- **Softcore** = Sexy/nude poses and teasing (showing body)
- **Hardcore** = Explicit sexual acts in progress (doing sexual acts)

## 🔍 Use in Frontend

Once subreddits are classified, filter them in your app:

```typescript
// Only show softcore subs appropriate for OF promotion
const { data } = await supabase
  .from('nsfw_subreddit_intel')
  .select('*')
  .eq('content_rating', 'softcore')
  .order('subscribers', { ascending: false });

// Exclude hardcore subs
const { data } = await supabase
  .from('nsfw_subreddit_intel')
  .select('*')
  .neq('content_rating', 'hardcore')
  .order('subscribers', { ascending: false });
```

## 💰 Cost Estimate

Using GPT-4o-mini:
- **Per subreddit:** ~$0.0002
- **For 2000 subreddits:** ~$0.40
- **Speed:** 50-100 subreddits/minute (with concurrency=5)

## 📈 Monitoring

The classifier logs real-time stats:

```
📊 Total: 127 classified (45 hardcore, 78 softcore, 4 uncertain, 0 failed) - 254.0/hour
```

## ⚠️ Troubleshooting

### "Could not find the 'content_rating' column"
→ Run the database migration first (Step 1)

### "Invalid API key"
→ Set a valid OpenAI API key in `/scraper/.env` (Step 2)

### Rate limiting from Reddit
→ Reduce concurrency: `--concurrency 3`

### Rate limiting from OpenAI
→ Reduce concurrency or upgrade your OpenAI plan

## 📝 Files Created

```
intel-scraper/
├── hardcore_classifier.py               # Main worker script
├── migrations/
│   └── add_content_rating.sql          # Database migration
├── HARDCORE_CLASSIFIER_README.md       # Full documentation
└── SETUP_HARDCORE_CLASSIFIER.md        # This file

frontend/src/lib/
└── supabase.ts                         # Updated TypeScript types
```

## 🎯 Next Steps

1. ✅ Run the database migration
2. ✅ Add OpenAI API key to .env
3. ✅ Test with `--test` mode
4. ✅ Run in continuous mode
5. ✅ Add filters to your frontend as needed

For more details, see `HARDCORE_CLASSIFIER_README.md`.

