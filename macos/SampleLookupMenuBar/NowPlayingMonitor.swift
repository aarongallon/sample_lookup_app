import AppKit
import Foundation

/// Reads the current track from the Music app via AppleScript (on demand only).
enum NowPlayingMonitor {
    static func currentTrack() -> NowPlayingTrack? {
        let script = """
        tell application "System Events"
          if not (exists process "Music") then return ""
        end tell
        tell application "Music"
          if player state is stopped then return ""
          try
            set t to name of current track
            set a to artist of current track
            return t & linefeed & a
          on error
            return ""
          end try
        end tell
        """

        var error: NSDictionary?
        guard let appleScript = NSAppleScript(source: script) else { return nil }
        let output = appleScript.executeAndReturnError(&error)
        guard error == nil else { return nil }

        let text = output.stringValue?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
        guard !text.isEmpty else { return nil }

        let parts = text.split(separator: "\n", maxSplits: 1, omittingEmptySubsequences: false)
        guard parts.count == 2 else { return nil }
        let title = String(parts[0]).trimmingCharacters(in: .whitespacesAndNewlines)
        let artist = String(parts[1]).trimmingCharacters(in: .whitespacesAndNewlines)
        guard !title.isEmpty, !artist.isEmpty else { return nil }
        return NowPlayingTrack(title: title, artist: artist)
    }
}
