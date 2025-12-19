# TikTok Setup Guide for ViralShorts Factory

## Why TikTok?
- **UNLIMITED uploads** (no daily limit like YouTube's 6-10/day)
- **Algorithm favors new creators** (easier to go viral)
- **Fastest growing platform** for short-form content
- **Direct monetization** via Creator Fund (1000+ followers)

## Option 1: Manual Upload (Recommended for Now)
1. Download TikTok app on phone
2. Create account with same branding (ViralShorts-Factory or similar)
3. Videos are saved to `output/tiktok_queue/` folder
4. Transfer to phone via:
   - USB cable
   - Cloud (Google Drive, OneDrive)
   - Email to yourself
5. Upload via TikTok app

## Option 2: Automated Upload (Advanced)

### Using Browser Automation (Selenium/Playwright)
```bash
pip install playwright
playwright install chromium
```

The `tiktok_uploader.py` would:
1. Open TikTok web in browser
2. Login with saved cookies
3. Upload video programmatically
4. Add caption and hashtags

### Getting TikTok Session Cookie
1. Login to TikTok in Chrome
2. Open Developer Tools (F12)
3. Go to Application > Cookies
4. Copy `sessionid` value
5. Set as `TIKTOK_SESSION_ID` env variable

⚠️ **Warning**: TikTok actively blocks automation. Manual upload is more reliable.

## Option 3: Third-Party Services (Easiest)

### ShortSync (FREE tier)
- Upload once → posts to TikTok, YouTube, Instagram
- URL: https://shortsync.app
- Free: 10 videos/month
- Paid: Unlimited

### Taisly (FREE tier)
- Automated reposting
- URL: https://taisly.com
- Schedules posts across platforms

### Vubli (FREE tier)
- AI-generated titles, descriptions, tags
- URL: https://vubli.ai
- Auto-scheduling

## Best TikTok Practices

### Optimal Posting Times
- Mon-Fri: 6-9 AM, 12-3 PM, 7-11 PM
- Weekends: 9 AM - 12 PM, 7-11 PM
- (Your audience's timezone!)

### Hashtags That Work
```
#fyp #foryou #foryoupage #viral #trending
#scary #facts #money #psychology #motivation
```

### Caption Formula
```
[Hook question or statement] 👀

[Main content teaser]

Follow for more! ✨

#fyp #viral #trending
```

## TikTok Creator Fund Requirements
- 10,000 followers
- 100,000 video views (last 30 days)
- 18+ years old
- Account in good standing

## Earnings Potential
- $0.02 - $0.04 per 1,000 views
- 1M views ≈ $20-40
- Top creators: $1,000-10,000/month from Fund alone
- Brand deals: Much higher

## Recommended Strategy
1. **Start manual**: Upload 3-5 videos/day
2. **Track performance**: See what works
3. **Scale**: Once profitable, consider paid automation
4. **Cross-promote**: Link to YouTube in bio

