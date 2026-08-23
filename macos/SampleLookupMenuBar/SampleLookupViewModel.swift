import Foundation
import SwiftUI

@MainActor
final class SampleLookupViewModel: ObservableObject {
    @Published var artist: String = ""
    @Published var title: String = ""
    @Published var samples: [SampleTrack] = []
    @Published var source: String?
    @Published var message: String?
    @Published var matchedLabel: String?
    @Published var isLoading = false
    @Published var errorText: String?
    @Published var nowPlayingStatus: String = "Open this panel, then tap Find samples when you want a lookup."

    private let client = SampleAPIClient()

    func refreshNowPlaying() {
        if let track = NowPlayingMonitor.currentTrack() {
            artist = track.artist
            title = track.title
            nowPlayingStatus = "Now Playing from Music"
            errorText = nil
        } else {
            nowPlayingStatus = "No track from Music — enter artist & title manually."
        }
    }

    func findSamples() {
        Task { await performLookup() }
    }

    private func performLookup() async {
        isLoading = true
        errorText = nil
        message = nil
        samples = []
        source = nil
        matchedLabel = nil
        defer { isLoading = false }

        do {
            let response = try await client.fetchSamples(artist: artist, title: title)
            samples = response.samples
            source = response.source
            message = response.message
            if let matched = response.matchedTrack {
                let t = matched["title"] ?? title
                let a = matched["artist"] ?? artist
                matchedLabel = "\(t) — \(a)"
            }
            if response.samples.isEmpty, response.message == nil {
                message = "No samples listed for this track."
            }
        } catch {
            errorText = error.localizedDescription
        }
    }
}
