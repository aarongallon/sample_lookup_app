# Sample Lookup Menu Bar (macOS)

Companion for the Sample Lookup API. Lives in the menu bar — lookups only when you ask.

## Requirements

- macOS 13+
- Music app (for Now Playing)
- API running at `http://127.0.0.1:8000`

## Run the API

```bash
cd ~/projects/sample-lookup-api
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

## Build & run the menu bar app

```bash
cd ~/projects/sample-lookup-api/macos
open SampleLookupMenuBar.xcodeproj
```

In Xcode: select **SampleLookupMenuBar** → Run (⌘R).

Or from the terminal:

```bash
xcodebuild -project SampleLookupMenuBar.xcodeproj -scheme SampleLookupMenuBar -configuration Debug build
open ~/Library/Developer/Xcode/DerivedData/SampleLookupMenuBar-*/Build/Products/Debug/SampleLookupMenuBar.app
```

## How to use

1. Play a song in Music
2. Click the **waveform** icon in the menu bar (or press **⌥⌘S**)
3. Confirm artist/title (or tap **Use Now Playing**)
4. Tap **Find samples**

Nothing is looked up until you tap that button.

## Permissions

macOS may ask for Automation access so the app can read the current track from Music. Allow it when prompted (System Settings → Privacy & Security → Automation).

Global hotkey **⌥⌘S** may require Accessibility permission the first time you use it from a non-focused context; for the status-item click path, no Accessibility grant is needed.
