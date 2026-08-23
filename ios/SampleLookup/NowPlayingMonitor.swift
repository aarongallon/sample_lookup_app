import MusicKit
import MediaPlayer

enum NowPlayingMonitor {
    static func currentTrack() async -> NowPlayingTrack? {
        // Try MusicKit first (requires authorization)
        let status = await MusicAuthorization.request()
        if status == .authorized {
            if let entry = ApplicationMusicPlayer.shared.queue.currentEntry {
                switch entry.item {
                case .song(let song):
                    return NowPlayingTrack(title: song.title, artist: song.artistName)
                default:
                    break
                }
            }
        }

        // Fallback: MPNowPlayingInfoCenter
        let info = MPNowPlayingInfoCenter.default().nowPlayingInfo
        if let title = info?[MPMediaItemPropertyTitle] as? String,
           let artist = info?[MPMediaItemPropertyArtist] as? String,
           !title.isEmpty, !artist.isEmpty {
            return NowPlayingTrack(title: title, artist: artist)
        }

        return nil
    }
}
