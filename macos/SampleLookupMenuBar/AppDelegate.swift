import AppKit
import SwiftUI

@MainActor
final class StatusItemController: NSObject {
    private var statusItem: NSStatusItem?
    private var popover: NSPopover?
    private let viewModel = SampleLookupViewModel()

    func install() {
        let item = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        if let button = item.button {
            button.image = NSImage(systemSymbolName: "waveform", accessibilityDescription: "Sample Lookup")
            button.image?.isTemplate = true
            button.action = #selector(togglePopover(_:))
            button.target = self
        }
        statusItem = item

        let popover = NSPopover()
        popover.behavior = .transient
        popover.animates = true
        popover.contentSize = NSSize(width: 340, height: 420)
        popover.contentViewController = NSHostingController(rootView: MenuBarPanel(viewModel: viewModel))
        self.popover = popover

        HotkeyManager.shared.onToggle = { [weak self] in
            self?.togglePopover(nil)
        }
        HotkeyManager.shared.register()
    }

    @objc func togglePopover(_ sender: Any?) {
        guard let button = statusItem?.button, let popover else { return }
        if popover.isShown {
            popover.performClose(sender)
        } else {
            viewModel.refreshNowPlaying()
            popover.show(relativeTo: button.bounds, of: button, preferredEdge: .minY)
            popover.contentViewController?.view.window?.makeKey()
            NSApp.activate(ignoringOtherApps: true)
        }
    }
}

final class AppDelegate: NSObject, NSApplicationDelegate {
    private var statusController: StatusItemController?

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.accessory)
        let controller = StatusItemController()
        controller.install()
        statusController = controller
    }

    func applicationWillTerminate(_ notification: Notification) {
        HotkeyManager.shared.unregister()
    }
}
