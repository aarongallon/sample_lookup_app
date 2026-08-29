import SwiftUI

struct MenuBarPanel: View {
    @ObservedObject var viewModel: SampleLookupViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            header

            GroupBox {
                VStack(alignment: .leading, spacing: 8) {
                    Text(viewModel.nowPlayingStatus)
                        .font(.caption)
                        .foregroundStyle(.secondary)

                    TextField("Artist", text: $viewModel.artist)
                        .textFieldStyle(.roundedBorder)
                    TextField("Title", text: $viewModel.title)
                        .textFieldStyle(.roundedBorder)

                    HStack {
                        Button("Use Now Playing") {
                            viewModel.refreshNowPlaying()
                        }
                        .disabled(viewModel.isLoading)

                        Spacer()

                        Button("Find samples") {
                            viewModel.findSamples()
                        }
                        .buttonStyle(.borderedProminent)
                        .disabled(viewModel.isLoading || viewModel.artist.isEmpty || viewModel.title.isEmpty)
                        .keyboardShortcut(.defaultAction)
                    }
                }
                .padding(4)
            }

            if !viewModel.history.isEmpty && viewModel.samples.isEmpty && viewModel.errorText == nil {
                historySection
            }

            results

            HStack {
                Text("⌥⌘S toggles this panel · lookups only when you ask")
                    .font(.caption2)
                    .foregroundStyle(.tertiary)
                Spacer()
                Button("Quit") {
                    NSApplication.shared.terminate(nil)
                }
                .font(.caption2)
                .buttonStyle(.plain)
                .foregroundStyle(.secondary)
            }
        }
        .padding(14)
        .frame(width: 340)
        .onAppear {
            viewModel.refreshNowPlaying()
        }
    }

    private var header: some View {
        HStack {
            Image(systemName: "waveform")
                .foregroundStyle(.tint)
            Text("Sample Lookup")
                .font(.headline)
            Spacer()
            if viewModel.isLoading {
                ProgressView()
                    .controlSize(.small)
            }
        }
    }

    @ViewBuilder
    private var historySection: some View {
        Divider()
        Text("Recent")
            .font(.caption.weight(.semibold))
            .foregroundStyle(.secondary)
        ForEach(viewModel.history, id: \.self) { entry in
            Button {
                let parts = entry.components(separatedBy: " — ")
                if parts.count == 2 {
                    viewModel.artist = parts[1]
                    viewModel.title = parts[0]
                    viewModel.findSamples()
                }
            } label: {
                Text(entry)
                    .font(.caption)
                    .lineLimit(1)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
            .buttonStyle(.plain)
            .foregroundStyle(.primary)
        }
    }

    @ViewBuilder
    private var results: some View {
        if let errorText = viewModel.errorText {
            Text(errorText)
                .font(.callout)
                .foregroundStyle(.red)
        }

        if let matched = viewModel.matchedLabel {
            Text(matched)
                .font(.subheadline.weight(.semibold))
            if let source = viewModel.source {
                Text(sourceLabel(source))
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }

        if let message = viewModel.message, viewModel.samples.isEmpty {
            Text(message)
                .font(.callout)
                .foregroundStyle(.secondary)
        }

        if !viewModel.samples.isEmpty {
            Divider()
            Text("Samples")
                .font(.subheadline.weight(.semibold))
            ForEach(viewModel.samples) { sample in
                SampleRowMac(sample: sample)
            }
        }
    }

    private func sourceLabel(_ raw: String) -> String {
        switch raw {
        case "genius": return "via Genius"
        case "local": return "via local database"
        case "cache": return "via cache"
        case "whosampled": return "via WhoSampled"
        default: return raw
        }
    }
}

struct SampleRowMac: View {
    let sample: SampleTrack

    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            if let urlString = sample.url, let url = URL(string: urlString) {
                Link(destination: url) {
                    HStack(spacing: 4) {
                        Text(sample.title)
                            .font(.body.weight(.medium))
                        Image(systemName: "arrow.up.right.square")
                            .font(.caption)
                    }
                }
            } else {
                Text(sample.title)
                    .font(.body.weight(.medium))
            }
            HStack(spacing: 6) {
                Text(sample.artist)
                if let year = sample.year {
                    Text("· \(year)")
                }
                if let type = sample.type {
                    Text("· \(type)")
                }
            }
            .font(.caption)
            .foregroundStyle(.secondary)
        }
        .padding(.vertical, 2)
    }
}
