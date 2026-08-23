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

            results

            Text("⌥⌘S toggles this panel · lookups only when you ask")
                .font(.caption2)
                .foregroundStyle(.tertiary)
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
                Text("Source: \(source)")
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
                VStack(alignment: .leading, spacing: 2) {
                    Text(sample.title)
                        .font(.body.weight(.medium))
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
    }
}
