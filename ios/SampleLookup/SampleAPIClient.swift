import Foundation

enum SampleAPIError: LocalizedError {
    case invalidURL
    case badStatus(Int)
    case emptyQuery

    var errorDescription: String? {
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

actor SampleAPIClient {
    var baseURL: URL

    init(baseURL: URL = URL(string: APIConfig.defaultBaseURL)!) {
        self.baseURL = baseURL
    }

    func fetchSamples(artist: String, title: String) async throws -> SamplesResponse {
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
