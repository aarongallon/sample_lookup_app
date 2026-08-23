import SwiftUI

@main
struct SampleLookupMenuBarApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) private var appDelegate

    var body: some Scene {
        // Settings is unused in MVP but required so SwiftUI App has a Scene.
        Settings {
            Form {
                Text("Sample Lookup talks to http://127.0.0.1:8000")
                Text("Menu bar icon · ⌥⌘S toggles panel · Find samples is on demand")
                    .foregroundStyle(.secondary)
            }
            .padding()
            .frame(width: 360)
        }
    }
}
