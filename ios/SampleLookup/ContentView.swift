import SwiftUI

struct ContentView: View {
    @StateObject private var viewModel = SampleLookupViewModel()

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    nowPlayingSection
                    inputSection
                    resultsSection
                }
                .padding()
            }
            .navigationTitle("Sample Lookup")
            .onAppear {
                viewModel.refreshNowPlaying()
            }
        }
    }

    private var nowPlayingSection: some View {
        GroupBox {
            HStack {
                Image(systemName: "waveform")
                    .foregroundStyle(.tint)
                Text(viewModel.nowPlayingStatus)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                Spacer()
            }
        }
    }

    private var inputSection: some View {
        VStack(spacing: 12) {
            TextField("Artist", text: $viewModel.artist)
                .textFieldStyle(.roundedBorder)
                .autocorrectionDisabled()
            TextField("Title", text: $viewModel.title)
                .textFieldStyle(.roundedBorder)
                .autocorrectionDisabled()

            HStack {
                Button {
                    viewModel.refreshNowPlaying()
                } label: {
                    Label("Use Now Playing", systemImage: "music.note")
                }
                .disabled(viewModel.isLoading)

                Spacer()

                Button {
                    viewModel.findSamples()
                } label: {
                    if viewModel.isLoading {
                        ProgressView()
                    } else {
                        Label("Find samples", systemImage: "magnifyingglass")
                    }
                }
                .buttonStyle(.borderedProminent)
                .disabled(viewModel.isLoading || viewModel.artist.isEmpty || viewModel.title.isEmpty)
            }
        }
    }

    @ViewBuilder
    private var resultsSection: some View {
        if let errorText = viewModel.errorText {
            Text(errorText)
                .font(.callout)
                .foregroundStyle(.red)
        }

        if let matched = viewModel.matchedLabel {
            Divider()
            Text(matched)
                .font(.headline)
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
                .padding(.top, 4)
        }

        if !viewModel.samples.isEmpty {
            Text("Samples")
                .font(.title3.weight(.semibold))
                .padding(.top, 4)

            ForEach(viewModel.samples) { sample in
                SampleRow(sample: sample)
            }
        }
    }
}

struct SampleRow: View {
    let sample: SampleTrack

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
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
        .padding(.vertical, 4)
    }
}
