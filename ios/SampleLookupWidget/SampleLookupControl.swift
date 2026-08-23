import AppIntents
import WidgetKit
import SwiftUI

@available(iOSApplicationExtension 18.0, *)
struct SampleLookupControl: ControlWidget {
    var body: some ControlWidgetConfiguration {
        StaticControlConfiguration(kind: "SampleLookupControl") {
            ControlWidgetButton(action: OpenSampleLookupIntent()) {
                Label("Find Samples", systemImage: "waveform")
            }
        }
        .displayName("Sample Lookup")
        .description("Open Sample Lookup to find what songs were sampled.")
    }
}

@available(iOS 18.0, *)
struct OpenSampleLookupIntent: AppIntent {
    static var title: LocalizedStringResource = "Open Sample Lookup"
    static var openAppWhenRun: Bool = true

    func perform() async throws -> some IntentResult {
        return .result()
    }
}
