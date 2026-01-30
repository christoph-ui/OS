// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "CRM",
    platforms: [
        .iOS(.v17)
    ],
    products: [
        .library(name: "CRM", targets: ["CRM"])
    ],
    targets: [
        .target(name: "CRM", path: "CRM")
    ]
)
