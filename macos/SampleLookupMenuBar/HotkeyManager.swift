import AppKit
import Carbon

/// Optional ⌥⌘S hotkey to toggle the menu bar panel. Lookup stays user-initiated inside the panel.
final class HotkeyManager {
    static let shared = HotkeyManager()

    private var hotKeyRef: EventHotKeyRef?
    private var handlerRef: EventHandlerRef?
    var onToggle: (() -> Void)?

    private let hotKeyID = EventHotKeyID(signature: OSType(0x534D504C), id: 1) // 'SMPL'

    func register() {
        unregister()

        var eventType = EventTypeSpec(eventClass: OSType(kEventClassKeyboard), eventKind: UInt32(kEventHotKeyPressed))
        let userData = Unmanaged.passUnretained(self).toOpaque()
        InstallEventHandler(GetApplicationEventTarget(), { _, event, userData in
            guard let userData else { return noErr }
            let manager = Unmanaged<HotkeyManager>.fromOpaque(userData).takeUnretainedValue()
            var hkID = EventHotKeyID()
            GetEventParameter(event, EventParamName(kEventParamDirectObject), EventParamType(typeEventHotKeyID), nil, MemoryLayout<EventHotKeyID>.size, nil, &hkID)
            if hkID.id == manager.hotKeyID.id {
                DispatchQueue.main.async { manager.onToggle?() }
            }
            return noErr
        }, 1, &eventType, userData, &handlerRef)

        // Option + Command + S
        let keyCode = UInt32(kVK_ANSI_S)
        let modifiers = UInt32(cmdKey | optionKey)
        RegisterEventHotKey(keyCode, modifiers, hotKeyID, GetApplicationEventTarget(), 0, &hotKeyRef)
    }

    func unregister() {
        if let hotKeyRef {
            UnregisterEventHotKey(hotKeyRef)
            self.hotKeyRef = nil
        }
        if let handlerRef {
            RemoveEventHandler(handlerRef)
            self.handlerRef = nil
        }
    }

    deinit {
        unregister()
    }
}
