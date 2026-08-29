import WidgetKit
import SwiftUI
import MusicKit

struct NowPlayingEntry: TimelineEntry {
    let date: Date
    let title: String
    let artist: String
}

struct NowPlayingProvider: TimelineProvider {
    func placeholder(in context: Context) -> NowPlayingEntry {
        NowPlayingEntry(date: .now, title: "Song Title", artist: "Artist")
    }

    func getSnapshot(in context: Context, completion: @escaping (NowPlayingEntry) -> Void) {
        completion(NowPlayingEntry(date: .now, title: "Song Title", artist: "Artist"))
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<NowPlayingEntry>) -> Void) {
        var title = "Not Playing"
        var artist = ""

        if let entry = ApplicationMusicPlayer.shared.queue.currentEntry {
            switch entry.item {
            case .song(let song):
                title = song.title
                artist = song.artistName
            default:
                break
            }
        }

        let entry = NowPlayingEntry(date: .now, title: title, artist: artist)
        let nextUpdate = Calendar.current.date(byAdding: .second, value: 30, to: .now)!
        completion(Timeline(entries: [entry], policy: .after(nextUpdate)))
    }
}

struct NowPlayingWidgetView: View {
    let entry: NowPlayingEntry

    private var deepLinkURL: URL? {
        guard entry.title != "Not Playing", !entry.title.isEmpty else { return nil }
        var components = URLComponents()
        components.scheme = "samplelookup"
        components.host = "lookup"
        components.queryItems = [
            URLQueryItem(name: "artist", value: entry.artist),
            URLQueryItem(name: "title", value: entry.title),
            URLQueryItem(name: "auto", value: "1"),
        ]
        return components.url
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Image(systemName: "waveform")
                    .foregroundStyle(.tint)
                Text("Sample Lookup")
                    .font(.caption2.weight(.semibold))
                    .foregroundStyle(.secondary)
            }
            Spacer()
            Text(entry.title)
                .font(.subheadline.weight(.semibold))
                .lineLimit(2)
            if !entry.artist.isEmpty {
                Text(entry.artist)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
            }
            Text("Tap to find samples")
                .font(.caption2)
                .foregroundStyle(.tertiary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(4)
        .widgetURL(deepLinkURL)
    }
}

struct SampleLookupWidget: Widget {
    let kind: String = "SampleLookupWidget"

    var body: some WidgetConfiguration {
        StaticConfiguration(kind: kind, provider: NowPlayingProvider()) { entry in
            NowPlayingWidgetView(entry: entry)
                .containerBackground(.fill.tertiary, for: .widget)
        }
        .configurationDisplayName("Sample Lookup")
        .description("Shows the current track. Tap to find samples.")
        .supportedFamilies([.systemSmall, .systemMedium])
    }
}
