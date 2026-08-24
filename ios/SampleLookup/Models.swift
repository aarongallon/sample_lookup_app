import Foundation

struct SampleTrack: Codable, Identifiable, Hashable {
    var id: String { "\(artist)|\(title)|\(year.map(String.init) ?? "")" }
    let title: String
    let artist: String
    let year: Int?
    let type: String?
    let url: String?
}

struct SamplesResponse: Codable {
    let query: [String: String]
    let matchedTrack: [String: String]?
    let samples: [SampleTrack]
    let source: String
    let message: String?

    enum CodingKeys: String, CodingKey {
        case query, samples, source, message
        case matchedTrack = "matched_track"
    }
}

struct NowPlayingTrack: Equatable {
    var title: String
    var artist: String

    var isEmpty: Bool {
        title.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
            || artist.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }
}

enum APIConfig {
    /// Change this to your Railway URL after deploying
    static let defaultBaseURL = "https://samplelookupapp-production.up.railway.app"
}
