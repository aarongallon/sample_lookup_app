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
    @Published var nowPlayingStatus: String = "Tap Use Now Playing, then Find samples."
    @Published var history: [String] = []

    private static let historyKey = "lookup_history"
    private static let maxHistory = 10
    private let client = SampleAPIClient()

    init() {
        history = UserDefaults.standard.stringArray(forKey: Self.historyKey) ?? []
    }

    func refreshNowPlaying() {
        Task {
            if let track = await NowPlayingMonitor.currentTrack() {
                artist = track.artist
                title = track.title
                nowPlayingStatus = "Now Playing from Music"
                errorText = nil
            } else {
                nowPlayingStatus = "No track from Music — enter manually."
            }
        }
    }

    func findSamples() {
        Task { await performLookup() }
    }

    func handleDeepLink(_ url: URL) {
        guard let components = URLComponents(url: url, resolvingAgainstBaseURL: false),
              components.scheme == "samplelookup" else { return }

        let params = Dictionary(
            uniqueKeysWithValues: (components.queryItems ?? []).compactMap { item in
                item.value.map { (item.name, $0) }
            }
        )

        if let a = params["artist"], !a.isEmpty { artist = a }
        if let t = params["title"], !t.isEmpty { title = t }

        if params["auto"] == "1" && !artist.isEmpty && !title.isEmpty {
            findSamples()
        }
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
            addToHistory(title: title, artist: artist)
        } catch {
            errorText = error.localizedDescription
        }
    }

    private func addToHistory(title: String, artist: String) {
        let entry = "\(title) — \(artist)"
        history.removeAll { $0 == entry }
        history.insert(entry, at: 0)
        if history.count > Self.maxHistory {
            history = Array(history.prefix(Self.maxHistory))
        }
        UserDefaults.standard.set(history, forKey: Self.historyKey)
    }
}
