# MetAds - Phase 5 Testing Checklist

**Project:** MetAds - Competitive Intelligence Tool
**Phase:** 5 (Integration & Polish)
**Date:** February 1, 2026

---

## Quick Start Testing

### Prerequisites

```bash
# 1. Start backend
cd backend
source venv/bin/activate
python run.py
# Backend running on http://localhost:5001

# 2. Start frontend (new terminal)
cd frontend
npm run dev
# Frontend running on http://localhost:5173

# 3. Open browser
open http://localhost:5173
```

### Test Account
- **Email:** test@example.com
- **Password:** Test123!
- **OR** Use Google OAuth

---

## Test Suite 1: Authentication Flow ✅ (VERIFIED)

### 1.1 Sign Up
- [ ] Navigate to http://localhost:5173
- [ ] Should redirect to `/sign-in`
- [ ] Click "Sign Up" link
- [ ] Enter email + password
- [ ] Successfully creates account
- [ ] Redirects to niche selector `/`

### 1.2 Sign In
- [ ] Sign out if signed in
- [ ] Click "Sign in with Google" (if configured)
- [ ] Successfully authenticates
- [ ] Redirects to niche selector `/`

### 1.3 Sign Out
- [ ] Click user avatar (top right)
- [ ] Click "Sign out"
- [ ] Redirects to `/sign-in`
- [ ] Cannot access `/` without auth

### 1.4 Protected Routes
- [ ] Sign out
- [ ] Try to access `/n/test-niche` directly
- [ ] Should redirect to `/sign-in`
- [ ] After sign in, redirects back to intended page

**Status:** ✅ PASSED (Auth fixed in previous session)

---

## Test Suite 2: Niche Management Flow

### 2.1 Create Niche
- [ ] Sign in
- [ ] On niche selector page `/`
- [ ] Click "+ Create Niche" button
- [ ] Fill form:
  - Name: `Test Niche E2E`
  - Description: `End-to-end testing niche`
  - Keywords: `test, e2e, automation`
  - Color: Select blue (#3B82F6)
  - Icon: Select 🧪
  - Countries: US, BR
  - Platforms: Instagram, Facebook
- [ ] Click "Create"
- [ ] Redirects to `/n/test-niche-e2e`
- [ ] Niche appears in niche selector

### 2.2 Edit Niche
- [ ] Navigate to niche workspace
- [ ] Click settings button (⚙️)
- [ ] Navigate to `/n/test-niche-e2e/settings`
- [ ] Edit name to: `Updated Test Niche`
- [ ] Add keyword: `updated`
- [ ] Change color to green
- [ ] Click "Save Changes"
- [ ] Verify success message
- [ ] Navigate back to niche selector
- [ ] Verify niche name updated

### 2.3 Delete Niche
- [ ] Navigate to niche settings
- [ ] Scroll to "Danger Zone"
- [ ] Click "Delete Niche"
- [ ] Confirm deletion in modal
- [ ] Redirects to `/`
- [ ] Verify niche removed from list

**Expected:** All operations complete without errors

---

## Test Suite 3: Ad Collection Flow ⭐ (NEW)

### 3.1 Trigger Collection
- [ ] Create or navigate to a niche
- [ ] Click "📥 Collect Ads" button (top right)
- [ ] Modal opens with title "Collect Ads"
- [ ] Select keyword from dropdown (or enter custom)
- [ ] Select limit: 50 ads
- [ ] Click "Start Collection"

### 3.2 Collection Progress
- [ ] Button changes to "Collecting..."
- [ ] Progress spinner appears (large, centered)
- [ ] Progress message shows:
  - "Collecting ads from Meta Ad Library..."
  - "Fetching up to 50 ads for `<keyword>`"
  - "This may take 10-30 seconds"
- [ ] Cancel button is disabled during collection

### 3.3 Collection Success
- [ ] Wait for collection to complete (10-30s)
- [ ] Success message appears:
  - "✅ Collection Complete!"
  - "Collected **X** ads (**Y** new, **Z** updated)"
  - Message from backend
- [ ] Success message has green background
- [ ] "Start Collection" button hidden
- [ ] "Close" button enabled

### 3.4 Collection Results
- [ ] Click "Close"
- [ ] Modal closes
- [ ] Search view automatically refreshes
- [ ] New ads appear in results list
- [ ] Ad count updated

### 3.5 Collection Error Handling
- [ ] Open collect modal
- [ ] Select custom keyword
- [ ] Leave keyword field empty
- [ ] Click "Start Collection"
- [ ] Error message: "Please enter a keyword"
- [ ] Enter invalid keyword (e.g., random gibberish)
- [ ] Click "Start Collection"
- [ ] If Meta API returns error, shows error message
- [ ] Error message has red background
- [ ] Can retry with different keyword

**Expected:** Collection completes successfully with proper feedback

---

## Test Suite 4: Search & Filter Flow

### 4.1 Basic Search
- [ ] Navigate to niche workspace `/n/<slug>`
- [ ] Search panel visible on left (desktop)
- [ ] Enter search term: `video`
- [ ] Click "Apply Filters"
- [ ] Results load in center panel
- [ ] Results contain "video" in text
- [ ] Result count displayed

### 4.2 Platform Filter
- [ ] Select platform: Instagram
- [ ] Click "Apply Filters"
- [ ] Results show only Instagram ads
- [ ] Platform badge visible on ad cards

### 4.3 Status Filter
- [ ] Select status: Active
- [ ] Click "Apply Filters"
- [ ] Results show only active ads
- [ ] Status badge shows "Active"

### 4.4 Sort Options
- [ ] Select sort: "Days Active"
- [ ] Select order: Descending
- [ ] Click "Apply Filters"
- [ ] Results sorted by days active (highest first)
- [ ] Change order to Ascending
- [ ] Results re-sorted (lowest first)

### 4.5 Clear Filters
- [ ] With filters applied
- [ ] Click "Clear All"
- [ ] All filters reset to default
- [ ] Results refresh with all ads

### 4.6 Pagination
- [ ] Scroll to bottom of results
- [ ] Click "Load More" (if visible)
- [ ] More results appended
- [ ] No duplicate ads
- [ ] Loading indicator during fetch

**Expected:** All filters work correctly and independently

---

## Test Suite 5: Ad Detail Flow

### 5.1 View Ad Details
- [ ] Click on an ad card in results
- [ ] Detail panel opens on right (desktop)
- [ ] Ad card highlighted in results
- [ ] Detail panel shows:
  - [ ] Page name
  - [ ] Verified badge (if applicable)
  - [ ] Creative preview (image/video)
  - [ ] Ad headline
  - [ ] Ad body text
  - [ ] CTA button text
  - [ ] Landing page link
  - [ ] Days active metric
  - [ ] Status badge
  - [ ] Start date
  - [ ] End date (if inactive)
  - [ ] Platform badges

### 5.2 Creative Carousel
- [ ] View ad with multiple creatives
- [ ] Carousel shows navigation dots/arrows
- [ ] Click next arrow
- [ ] Next creative displays
- [ ] Click previous arrow
- [ ] Previous creative displays
- [ ] Swipe works on mobile

### 5.3 Related Ads
- [ ] View ad details
- [ ] Related ads count displayed (e.g., "3 variants")
- [ ] Click "View Related" button
- [ ] Related ads section expands or navigates
- [ ] Shows ads from same page_id
- [ ] Insights displayed:
  - [ ] Total variants count
  - [ ] Longest running badge
  - [ ] Newest badge

### 5.4 Landing Page Link
- [ ] Click "🔗 View Landing Page" link
- [ ] Opens in new tab
- [ ] Navigates to ad's landing URL

**Expected:** All ad information displays correctly

---

## Test Suite 6: Saved Ads Flow

### 6.1 Save an Ad
- [ ] View ad details
- [ ] Click "☆ Save" button
- [ ] Button changes to "★ Saved"
- [ ] Button color changes (filled star)
- [ ] Ad card shows saved indicator

### 6.2 Add Notes
- [ ] With saved ad open
- [ ] Click "Edit Notes" (or notes section)
- [ ] Enter notes: `Great example of problem-solution copywriting`
- [ ] Click "Save"
- [ ] Notes appear in detail panel

### 6.3 Add Tags
- [ ] With saved ad open
- [ ] Click "Edit Tags" (or tags input)
- [ ] Enter tags: `copywriting, problem-solution, video-editing`
- [ ] Tags saved and displayed
- [ ] Tags appear as chips/badges

### 6.4 View Saved Ads
- [ ] Navigate to "⭐ Saved" tab
- [ ] List of saved ads displays
- [ ] Shows ads with notes/tags
- [ ] Tags shown on cards

### 6.5 Filter by Tag
- [ ] On Saved view
- [ ] Click tag filter: `copywriting`
- [ ] Only ads with that tag display
- [ ] Click "All" to clear filter

### 6.6 Update Notes/Tags
- [ ] View saved ad details
- [ ] Edit notes, change text
- [ ] Add/remove tags
- [ ] Save changes
- [ ] Changes persisted

### 6.7 Unsave an Ad
- [ ] View saved ad
- [ ] Click "★ Saved" button
- [ ] Button changes to "☆ Save"
- [ ] Ad removed from Saved view
- [ ] Notes/tags cleared

**Expected:** Saved ads persist and can be managed with notes/tags

---

## Test Suite 7: Mobile Responsive Flow

### 7.1 Setup Mobile View
- [ ] Open Chrome DevTools (F12)
- [ ] Toggle device toolbar (Ctrl+Shift+M)
- [ ] Select "iPhone 12 Pro" or similar
- [ ] Reload page

### 7.2 Mobile Navigation
- [ ] Niche selector displays as vertical stack
- [ ] Niche cards full width
- [ ] Tap on niche
- [ ] Workspace loads

### 7.3 Mobile Search
- [ ] Search panel hidden on mobile
- [ ] "🔍 Filters" button visible
- [ ] Tap "Filters" button
- [ ] Filter overlay opens (full screen)
- [ ] Apply filters
- [ ] Overlay closes

### 7.4 Mobile Results
- [ ] Results display as carousel (not grid)
- [ ] Swipe left/right to navigate
- [ ] Smooth swipe animation
- [ ] Ad cards full width

### 7.5 Mobile Ad Detail
- [ ] Tap on ad card
- [ ] Detail overlay opens (full screen)
- [ ] "← Back" button visible
- [ ] All content scrollable
- [ ] Tap "Back"
- [ ] Overlay closes, back to carousel

### 7.6 Mobile Collect
- [ ] Tap "Collect Ads" button
- [ ] Modal opens (full screen on mobile)
- [ ] Form inputs touch-friendly
- [ ] Collection works same as desktop

**Expected:** All features work smoothly on mobile

---

## Test Suite 8: Multi-User Data Isolation

### 8.1 User A
- [ ] Sign in as `user_a@test.com`
- [ ] Create niche: "User A Niche"
- [ ] Collect some ads
- [ ] Save an ad with notes
- [ ] Sign out

### 8.2 User B
- [ ] Sign in as `user_b@test.com`
- [ ] Niche selector shows NO niches
- [ ] "User A Niche" NOT visible
- [ ] Create niche: "User B Niche"
- [ ] Verify only own niche visible
- [ ] Sign out

### 8.3 User A Again
- [ ] Sign in as `user_a@test.com`
- [ ] "User A Niche" still exists
- [ ] Saved ads still there
- [ ] Notes preserved
- [ ] "User B Niche" NOT visible

**Expected:** Complete data isolation between users

---

## Test Suite 9: Error Handling & Edge Cases

### 9.1 Network Errors
- [ ] Open DevTools Network tab
- [ ] Set throttling to "Offline"
- [ ] Try to search ads
- [ ] Error message displays
- [ ] Restore "Online"
- [ ] Retry works

### 9.2 Empty States
- [ ] Create new niche (no ads yet)
- [ ] Search view shows "No ads found" message
- [ ] Shows suggestion to collect ads
- [ ] Saved view shows "No saved ads yet"

### 9.3 Search No Results
- [ ] Search for gibberish keyword: `xyzabc123`
- [ ] Results show "No ads found"
- [ ] "Clear filters" link visible
- [ ] Click to clear

### 9.4 Ad with No Creatives
- [ ] View ad with missing media
- [ ] Placeholder image shown
- [ ] No JavaScript errors

### 9.5 Long Text Handling
- [ ] View ad with very long body text
- [ ] Text displays without breaking layout
- [ ] Scrollable if needed

### 9.6 Special Characters
- [ ] Create niche with special chars: `Test & "Quotes" <HTML>`
- [ ] Name displays correctly
- [ ] No XSS vulnerability

---

## Test Suite 10: Performance Testing

### 10.1 Load Time
- [ ] Clear browser cache
- [ ] Navigate to `/`
- [ ] Page loads in < 2 seconds
- [ ] No console errors

### 10.2 Search Performance
- [ ] Search with no filters
- [ ] Results load in < 300ms
- [ ] Pagination smooth

### 10.3 Large Dataset
- [ ] Niche with 500+ ads
- [ ] Search still performant
- [ ] Scrolling smooth
- [ ] No memory leaks

### 10.4 Slow Connection
- [ ] Throttle to "Slow 3G"
- [ ] Loading indicators show
- [ ] Page remains usable
- [ ] No timeouts

---

## Browser Compatibility

### Desktop
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

### Mobile
- [ ] iOS Safari (iPhone)
- [ ] Chrome (Android)

---

## Test Results Summary

### Completed Test Suites

| Suite | Status | Notes |
|-------|--------|-------|
| 1. Authentication | ✅ PASSED | OAuth fixed |
| 2. Niche Management | ⏳ PENDING | |
| 3. Ad Collection | ⏳ PENDING | **NEW - Test this!** |
| 4. Search & Filter | ⏳ PENDING | |
| 5. Ad Detail | ⏳ PENDING | |
| 6. Saved Ads | ⏳ PENDING | |
| 7. Mobile Responsive | ⏳ PENDING | |
| 8. Multi-User Isolation | ⏳ PENDING | |
| 9. Error Handling | ⏳ PENDING | |
| 10. Performance | ⏳ PENDING | |

### Critical Bugs Found
(Document any bugs here)

- None yet

### Non-Critical Issues
(Document minor issues here)

- None yet

---

## Next Steps After Testing

1. **Fix Critical Bugs** - Block release
2. **Fix Non-Critical Issues** - Nice to have
3. **Performance Optimization** - If needed
4. **Documentation** - Update README with findings
5. **Tag v0.1.0** - Create release

---

## Testing Commands

### Backend Tests
```bash
cd backend
pytest
# Should show: 22 tests passed
```

### Frontend Dev Server
```bash
cd frontend
npm run dev
```

### Build Production
```bash
cd frontend
npm run build
npm run preview
```

---

## Support

If you encounter issues:
1. Check browser console for errors
2. Check backend terminal for errors
3. Review [OAUTH_FIX_PROGRESS.md](OAUTH_FIX_PROGRESS.md:1-405) for auth issues
4. Review [PHASE_5_PLAN.md](PHASE_5_PLAN.md:1-1) for detailed test scenarios

**Ready to test! Start with Test Suite 2 (Niche Management) and work through each suite systematically.** 🧪
