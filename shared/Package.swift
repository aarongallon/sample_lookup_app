// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "SampleLookupShared",
    platforms: [.macOS(.v13), .iOS(.v17)],
    products: [
        .library(name: "SampleLookupShared", targets: ["SampleLookupShared"]),
    ],
    targets: [
        .target(name: "SampleLookupShared"),
    ]
)
