# Sample Lookup iOS App

iPhone companion for the Sample Lookup API. Find what songs are sampled in whatever you're listening to.

## Features

- **Main app**: See Now Playing from Music, tap Find samples
- **Home Screen widget**: Shows current track, tap opens app
- **Control Center button** (iOS 18+): One-tap launch from Control Center

## Requirements

- iOS 17+ (Control Center button needs iOS 18+)
- Apple Developer account (free tier works for personal device testing)
- Sample Lookup API running and reachable from your phone

## Setup

### 1. Deploy the API (so your phone can reach it)

The API must be accessible over the network — `127.0.0.1` only works on your Mac.

**Option A — Railway (recommended):**
See the root README for Railway deployment instructions.

**Option B — Same Wi-Fi (for testing):**
```bash
cd ~/projects/sample-lookup-api
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Then find your Mac's local IP (`ifconfig | grep "inet "`) and update `APIConfig.defaultBaseURL` in `Models.swift` to `http://YOUR_MAC_IP:8000`.

### 2. Open in Xcode

```bash
open ~/projects/sample-lookup-api/ios/SampleLookup.xcodeproj
```

### 3. Run on device

1. Connect your iPhone
2. Select your device as the run destination
3. Press Run (Cmd+R)
4. Allow Music access when prompted

### 4. Add the widget

1. Long-press your Home Screen → tap +
2. Search "Sample Lookup"
3. Add the small or medium widget

### 5. Add Control Center button (iOS 18+)

1. Swipe down to open Control Center
2. Tap + to customize
3. Search "Sample Lookup" → add the Find Samples button
