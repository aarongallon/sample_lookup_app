import WidgetKit
import SwiftUI

@main
struct SampleLookupWidgetBundle: WidgetBundle {
    var body: some Widget {
        SampleLookupWidget()
        if #available(iOSApplicationExtension 18.0, *) {
            SampleLookupControl()
        }
    }
}
