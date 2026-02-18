# Variant Analysis Feature

## Overview

The **Variant Analysis** feature provides deep insights into how advertisers test and optimize their ad campaigns through creative variations. When an advertiser runs multiple versions of the same campaign (same message, different creatives), this feature automatically detects, groups, and analyzes these variants to reveal their testing strategy.

## What is a Variant?

A **variant** is a version of the same ad campaign that shares:
- ✅ Same **page/advertiser** (e.g., "Willliam Fitness")
- ✅ Same **headline/title** (e.g., "Strong After 40")
- ❌ Different **creative elements** (images, videos, body text variations)

**Example:**
```
Campaign: "Strong After 40" by Willliam Fitness
├── Variant 1: Image of person exercising + Text A
├── Variant 2: Image of person exercising + Text B
├── Variant 3: Video testimonial + Text A
└── Variant 4: Video testimonial + Text C
```

All 4 ads are **variants** of the same campaign because they promote the same core message but test different creative executions.

## Variants vs. Other Campaigns

### Variants (Same Campaign)
- **Same headline**: "Strong After 40"
- **Same core message**: Help people over 40 get fit
- **Different execution**: Testing images, videos, text variations
- **Purpose**: A/B testing to optimize performance

### Other Campaigns (Different Campaigns)
- **Different headline**: "Strong After 40" vs. "Fitness After 50"
- **Different core message**: Two separate product lines or value propositions
- **Purpose**: Separate marketing initiatives

### Visual Representation
```
Advertiser: Willliam Fitness
│
├── Campaign 1: "Strong After 40" [57 variants]
│   ├── Variant 1: Image A + Body Text A
│   ├── Variant 2: Image B + Body Text A
│   └── ... (55 more variants)
│
└── Campaign 2: "Fitness After 50" [12 variants]
    ├── Variant 1: Image C + Body Text D
    └── ... (11 more variants)
```

**In the UI:**
- **Variant Analysis** shows insights about the 57 variants of "Strong After 40"
- **View Other Campaigns** button shows other campaigns like "Fitness After 50"

## Special Case: Multi-Language Campaigns

**Important Note:** Sometimes what appears as "Other Campaigns" are actually the **same campaign in different languages**.

**Example:**
```
Advertiser: Global Fitness Brand
│
├── Campaign (English): "Get Fit Fast" [20 variants]
├── Campaign (Spanish): "Ponte en Forma Rápido" [15 variants]
└── Campaign (French): "Mettez-vous en Forme Rapidement" [12 variants]
```

These appear as separate campaigns because:
- ❌ Different headlines (different languages)
- ✅ Same core message and value proposition
- ✅ Same advertiser targeting different markets

**How to identify:**
1. Check if the advertiser targets multiple countries
2. Look for similar themes/messaging across campaigns
3. Check if creative media is similar across "campaigns"
4. Use Google Translate on headlines to verify if they're translations

## Types of Variant Analysis

The Variant Analysis feature performs **5 types of analysis** to reveal testing strategies:

### 1. Body Text Variations
**What it detects:** Different versions of the main ad copy

**Example Insight:**
```
Testing 3 different text versions - analyze which performs best
```

**What to look for:**
- **Problem-focused vs. Solution-focused** copy
- **Short vs. Long** descriptions
- **Emotional vs. Logical** appeals
- **Different value propositions** tested

**Real Example:**
```
Variant 1: "Struggling to lose weight after 40? Our program makes it easy..."
Variant 2: "Join 10,000+ people who transformed their body after 40..."
Variant 3: "Science-backed workout program designed for people over 40..."
```

### 2. Call-to-Action (CTA) Variations
**What it detects:** Different CTA buttons being tested

**Example Insight:**
```
Experimenting with 4 CTAs - track conversion rates
```

**Common CTA tests:**
- "Learn More" vs. "Get Started" vs. "Sign Up Free"
- "Shop Now" vs. "See Prices" vs. "Get Offer"
- Generic vs. Specific CTAs

**Why it matters:**
- CTAs have massive impact on conversion rates
- Small wording changes can double click-through rates
- Reveals what action the advertiser wants most

### 3. Text Length Variations
**What it detects:** Testing short vs. long copy

**Example Insight:**
```
Varying text length from 50 to 250 characters
```

**Testing hypothesis:**
- **Short copy**: Grabs attention, works for visual products
- **Long copy**: Builds trust, explains complex products
- **Medium copy**: Balanced approach

**What this reveals:**
- Whether the product needs explanation
- Target audience's reading preference
- Mobile vs. desktop optimization

### 4. Creative Media Variations
**What it detects:** Different images/videos being tested

**Example Insight:**
```
57 creative variations - likely testing different images/videos
```

**Common tests:**
- **Product shot** vs. **Lifestyle image** vs. **Before/After**
- **Video testimonial** vs. **Product demo** vs. **Founder story**
- **Professional photo** vs. **User-generated content**
- **Different models/demographics** (age, gender, ethnicity)

**Why it matters:**
- Creatives drive 75%+ of ad performance
- Visual testing is the most common A/B test
- Reveals target audience preferences

### 5. Headline Variations (within same campaign)
**What it detects:** Minor headline tweaks while maintaining core message

**Example Insight:**
```
Testing 2 headline variations with same theme
```

**Example:**
```
Headline A: "Get Fit After 40"
Headline B: "Stay Fit After 40"

("Get" = aspirational, "Stay" = maintenance)
```

**Note:** Major headline changes = different campaigns, not variants.

## How the Feature Works

### Automatic Detection
The system automatically:
1. **Groups ads** by `page_name + headline`
2. **Counts variants** for each group
3. **Triggers analysis** when 5+ variants detected
4. **Compares fields** across all variants to find differences

### Analysis Threshold
- **Minimum 5 variants** required for analysis
- Why? Less than 5 variants = not enough data for meaningful insights
- With 5+ variants, patterns become statistically significant

### Display Logic
The Variant Analysis section appears when:
```javascript
ad.variant_count >= 5
```

### Data Analyzed
For each variant, we compare:
- ✅ Body text content
- ✅ Headline (minor variations)
- ✅ Call-to-action button
- ✅ Text length (character count)
- ✅ Creative type (image, video, carousel)
- ✅ Platform targeting (Facebook, Instagram, etc.)

## User Interface

### 1. Table View (Recommended)
**Default view** showing grouped campaigns:

```
┌──────────────────────────────────────────────────────┐
│ [+] 57  | Willliam Fitness                           │
│         | Strong After 40                            │
│         | "Transform your body in just 21 days..."   │
│         | Days: 45  | Status: Active                 │
└──────────────────────────────────────────────────────┘
```

**Clicking the [+] button expands all 57 variants:**

```
┌──────────────────────────────────────────────────────┐
│ [-] 57  | Willliam Fitness - Strong After 40         │
├──────────────────────────────────────────────────────┤
│   └─ Variant 2 | "Transform your body..."            │
│   └─ Variant 3 | "Get stronger, faster..."           │
│   └─ Variant 4 | "Join thousands who..."             │
│   ... (53 more)                                      │
└──────────────────────────────────────────────────────┘
```

### 2. Ad Detail Panel
When viewing a single ad with 5+ variants:

```
┌─────────────────────────────────────────────┐
│ 🔍 Variant Analysis                         │
│ 57 variants                                 │
├─────────────────────────────────────────────┤
│ Differences Detected:                       │
│                                             │
│ • Body Text (3 variations)                  │
│   Testing different messaging approaches    │
│                                             │
│ • Call-to-Action (2 CTAs)                   │
│   "Learn More" vs "Get Started"             │
├─────────────────────────────────────────────┤
│ Key Insights:                               │
│                                             │
│ • Testing 3 different text versions -       │
│   analyze which performs best               │
│                                             │
│ • Experimenting with 2 CTAs -               │
│   track conversion rates                    │
│                                             │
│ • 57 creative variations -                  │
│   likely testing images/videos              │
├─────────────────────────────────────────────┤
│ 💡 Tip: Expand the row in table view       │
│    to see all 57 variants side-by-side     │
└─────────────────────────────────────────────┘
```

### 3. Buttons Available

**View X Other Campaigns** (when available)
- Shows when advertiser has multiple distinct campaigns
- Opens modal with campaigns that have different headlines
- Helps discover advertiser's full marketing strategy
- May include same campaign in different languages

**View Full Ad on Meta**
- Links to Meta Ad Library for full creative preview
- Required to see actual images/videos
- Shows complete ad as it appears to users

## Practical Use Cases

### 1. Competitive Research
**Scenario:** You're launching a fitness app for people over 40

**How Variant Analysis Helps:**
```
1. Find Willliam Fitness "Strong After 40" campaign
2. See they're testing 57 variants (serious optimization)
3. Analyze insights:
   - Testing "transformation" vs. "maintenance" messaging
   - CTAs: "Learn More" performs better than "Sign Up"
   - Long-form copy (200+ chars) used consistently
   - Video testimonials + before/after images dominate
4. Apply learnings:
   - Use "transformation" angle in your copy
   - Start with "Learn More" CTA, not "Sign Up"
   - Invest in video testimonials early
   - Don't test short copy - go straight to long-form
```

**Result:** Skip months of testing, launch with proven strategy

### 2. Identify Winning Patterns
**Scenario:** Analyzing successful campaigns

**Pattern Detection:**
```
High Variant Count (50+) + Long Days Active (60+) = Winner

This advertiser:
- Found a winning campaign
- Heavily optimizing creatives
- Not changing core message (it works!)
- Focus on scaling via better creatives
```

**Insight:** When you find your winner, double down on creative testing, not message testing.

### 3. Market Entry Strategy
**Scenario:** Entering a new market/niche

**Research Process:**
```
1. Search for top advertisers in niche
2. Find campaigns with 10+ variants
3. Analyze what they're testing:
   - Which aspects varied most? (That's what matters)
   - Which stayed consistent? (That's proven)
4. Identify gaps:
   - What angles are they NOT testing?
   - Opportunity for differentiation
```

### 4. Budget Planning
**Scenario:** Determining test budget

**High Variant Counts Indicate:**
- Market is competitive (more testing needed)
- Creative optimization is critical
- Budget 3-5x normal for creative production
- Plan for longer testing period

**Low Variant Counts Indicate:**
- Simple product/message works
- Less creative testing needed
- Can launch faster with less budget

## Technical Implementation

### Backend Analysis
Location: `backend/app/routes/ads.py`

**Endpoint:**
```
GET /api/niches/{slug}/ads/{ad_id}/variants/analysis
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total_variants": 57,
    "differences": [
      {
        "field": "body_text",
        "label": "Body Text",
        "variations_count": 3,
        "description": "Testing different text variations",
        "values": ["Text A", "Text B", "Text C"]
      },
      {
        "field": "cta",
        "label": "Call-to-Action",
        "variations_count": 2,
        "description": "Experimenting with different CTAs",
        "values": ["Learn More", "Get Started"]
      }
    ]
  }
}
```

### Frontend Components

**Main Component:**
```
frontend/src/components/VariantAnalysis.vue
```

**Used in:**
```
frontend/src/components/AdDetailPanel.vue
```

**Conditional Rendering:**
```vue
<VariantAnalysis
  v-if="ad.variant_count >= 5"
  :niche-slug="nicheSlug"
  :ad-id="ad.id"
/>
```

## Data Model

### Variant Grouping
**Primary Key:**
```
page_name + headline
```

**Example:**
```
"Willliam Fitness|Strong After 40" → Group of 57 ads
"Willliam Fitness|Fitness After 50" → Group of 12 ads (different campaign)
```

### Variant Count Field
**Added to Ad Detail Response:**
```python
# backend/app/routes/ads.py (Line 216-228)
variant_count = Ad.query.filter(
    Ad.niche_id == niche.niche_id,
    Ad.page_id == ad.page_id,
    Ad.headline == ad.headline
).count()

ad_data = ad.to_dict()
ad_data['variant_count'] = variant_count
```

## Best Practices

### For Researchers
1. **Start with high variant counts** (20+) - these are proven campaigns
2. **Check days active** - 30+ days = working well
3. **Look for consistency** - what doesn't change is what works
4. **Analyze differences** - what varies is what's being optimized
5. **Cross-reference languages** - same campaign, different markets

### For Advertisers
1. **Don't over-test early** - find message-market fit first
2. **Once you have a winner** - test 20+ creative variations
3. **Keep core message stable** - only vary execution
4. **Track variant performance** - kill losers, scale winners
5. **Test one variable at a time** - isolate what works

### For Developers
1. **Variant threshold**: 5+ (not 3) for statistical significance
2. **Group carefully**: Small headline differences = same campaign
3. **Language detection**: Future enhancement for multi-language grouping
4. **Performance**: Cache variant counts in ad detail response
5. **UI clarity**: Always distinguish variants from other campaigns

## Future Enhancements

### Planned Features
1. **Language Detection**
   - Auto-detect multi-language variants
   - Group by translated headlines
   - Show "Same campaign (5 languages)" insight

2. **Performance Scoring**
   - Estimate variant performance based on longevity
   - Highlight "likely winner" variants
   - Show performance trends over time

3. **Visual Similarity Analysis**
   - Compare creative images/videos
   - Detect image variations (color, crop, overlays)
   - Group by visual theme

4. **A/B Test Suggestions**
   - AI-suggested variations based on successful patterns
   - "Top advertisers are testing X, you should too"
   - Predicted performance impact

5. **Variant Export**
   - Download all variants for external analysis
   - Export to spreadsheet with metadata
   - Integration with design tools

## Troubleshooting

### "No variant analysis shown"
**Possible causes:**
- Less than 5 variants exist (threshold not met)
- Variants have different headlines (separate campaigns)
- Data not yet loaded (check network tab)

**Solution:**
- Verify `ad.variant_count >= 5`
- Check API response includes `variant_count` field
- Ensure backend endpoint returns analysis data

### "Variants grouped incorrectly"
**Possible causes:**
- Headline has typos/variations
- Different languages treated as same campaign
- Page name changed over time

**Solution:**
- Manual review of headline field
- Consider fuzzy matching for similar headlines
- Implement language detection

### "Other Campaigns showing same ads"
**Explanation:**
This is correct behavior when:
- Advertiser runs same campaign in different languages
- Headlines are translations, not different campaigns
- Should be shown as "Other Campaigns" until language detection implemented

**Workaround:**
- Manually review headlines for similarity
- Use Google Translate to verify
- Check targeting countries for language clues

## Related Documentation

- **CLAUDE.md** - Full system architecture and implementation guide
- **backend/app/routes/ads.py** - Variant analysis endpoint implementation
- **frontend/src/components/VariantAnalysis.vue** - UI component
- **frontend/src/components/AdTable.vue** - Variant grouping and display

## Summary

The Variant Analysis feature provides deep competitive intelligence by automatically detecting and analyzing how advertisers optimize their campaigns through creative testing. By understanding variant patterns, you can:

- ✅ Skip months of A/B testing
- ✅ Launch with proven strategies
- ✅ Identify winning creative patterns
- ✅ Understand market competitiveness
- ✅ Optimize budget allocation

**Key Takeaway:** High variant counts + long active periods = proven winners worth studying and learning from.
