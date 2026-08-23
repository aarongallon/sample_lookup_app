import Foundation

public struct SampleTrack: Codable, Identifiable, Hashable, Sendable {
    public var id: String { "\(artist)|\(title)|\(year.map(String.init) ?? "")" }
    public let title: String
    public let artist: String
    public let year: Int?
    public let type: String?
    public let url: String?
}

public struct SamplesResponse: Codable, Sendable {
    public let query: [String: String]
    public let matchedTrack: [String: String]?
    public let samples: [SampleTrack]
    public let source: String
    public let message: String?

    enum CodingKeys: String, CodingKey {
        case query, samples, source, message
        case matchedTrack = "matched_track"
    }
}

public enum SampleAPIError: LocalizedError, Sendable {
    case invalidURL
    case badStatus(Int)
    case emptyQuery

    public var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Could not build API URL."
        case .badStatus(let code):
            return "API returned status \(code)."
        case .emptyQuery:
            return "Artist and title are required."
        }
    }
}

public actor SampleAPIClient {
    public var baseURL: URL

    public init(baseURL: URL = URL(string: "http://127.0.0.1:8000")!) {
        self.baseURL = baseURL
    }

    public func fetchSamples(artist: String, title: String) async throws -> SamplesResponse {
        let artist = artist.trimmingCharacters(in: .whitespacesAndNewlines)
        let title = title.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !artist.isEmpty, !title.isEmpty else { throw SampleAPIError.emptyQuery }

        var components = URLComponents(url: baseURL.appendingPathComponent("samples"), resolvingAgainstBaseURL: false)
        components?.queryItems = [
            URLQueryItem(name: "artist", value: artist),
            URLQueryItem(name: "title", value: title),
        ]
        guard let url = components?.url else { throw SampleAPIError.invalidURL }

        var request = URLRequest(url: url)
        request.timeoutInterval = 30

        let (data, response) = try await URLSession.shared.data(for: request)
        if let http = response as? HTTPURLResponse, !(200...299).contains(http.statusCode) {
            throw SampleAPIError.badStatus(http.statusCode)
        }
        return try JSONDecoder().decode(SamplesResponse.self, from: data)
    }
}
