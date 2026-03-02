#!/usr/bin/env python3
"""
Feature Module Generator for iOS projects following the claude-ios-skill patterns.

Usage:
    python generate_feature.py <feature-name> --path <project-path>

Example:
    python generate_feature.py user-profile --path /path/to/AppModules
    python generate_feature.py settings --path /path/to/AppModules
"""

import os
import sys
import argparse
from pathlib import Path


def to_pascal_case(name: str) -> str:
    """Convert kebab-case or snake_case to PascalCase."""
    return ''.join(word.capitalize() for word in name.replace('-', '_').split('_'))


def to_camel_case(name: str) -> str:
    """Convert kebab-case or snake_case to camelCase."""
    pascal = to_pascal_case(name)
    return pascal[0].lower() + pascal[1:] if pascal else ''


def create_directory(path: Path):
    """Create directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)
    print(f"  Created: {path}")


def write_file(path: Path, content: str):
    """Write content to file."""
    path.write_text(content)
    print(f"  Created: {path}")


def generate_viewmodel(feature_name: str) -> str:
    """Generate @MainActor @Observable ViewModel with individual properties."""
    pascal = to_pascal_case(feature_name)

    return f'''import Foundation

@MainActor
@Observable
final class {pascal}ViewModel {{
    // State — individual properties for granular SwiftUI observation
    private(set) var items: [String] = []
    private(set) var isLoading = false
    var errorMessage: String?

    // TODO: Replace with actual repository protocol
    // private let repository: {pascal}Repository

    init(/* repository: {pascal}Repository */) {{
        // self.repository = repository
    }}

    func onAppear() async {{
        isLoading = true
        defer {{ isLoading = false }}
        do {{
            // TODO: Replace with actual data loading
            // items = try await repository.getItems()
            items = ["Item 1", "Item 2", "Item 3"]
        }} catch {{
            errorMessage = error.localizedDescription
        }}
    }}

    func refresh() async {{
        await onAppear()
    }}

    func deleteItem(id: String) async {{
        // TODO: Implement delete
        items.removeAll {{ $0 == id }}
    }}
}}
'''


def generate_screen(feature_name: str) -> str:
    """Generate SwiftUI Screen that receives ViewModel as let."""
    pascal = to_pascal_case(feature_name)

    return f'''import SwiftUI

struct {pascal}Screen: View {{
    let viewModel: {pascal}ViewModel

    var body: some View {{
        List(viewModel.items, id: \\.self) {{ item in
            Text(item)
        }}
        .overlay {{
            if viewModel.isLoading && viewModel.items.isEmpty {{
                ProgressView()
            }}
        }}
        .overlay {{
            if let error = viewModel.errorMessage, viewModel.items.isEmpty {{
                ContentUnavailableView(
                    "Error",
                    systemImage: "exclamationmark.triangle",
                    description: Text(error)
                )
            }}
        }}
    }}
}}

// MARK: - Previews

#Preview("With Data") {{
    let viewModel = {pascal}ViewModel()
    viewModel.items = ["Item 1", "Item 2", "Item 3"]
    return {pascal}Screen(viewModel: viewModel)
}}

#Preview("Loading") {{
    let viewModel = {pascal}ViewModel()
    viewModel.isLoading = true
    return {pascal}Screen(viewModel: viewModel)
}}

#Preview("Error") {{
    let viewModel = {pascal}ViewModel()
    viewModel.errorMessage = "Something went wrong"
    return {pascal}Screen(viewModel: viewModel)
}}
'''


def generate_route(feature_name: str) -> str:
    """Generate Route (owns ViewModel via @State, handles navigation)."""
    pascal = to_pascal_case(feature_name)

    return f'''import SwiftUI

// TODO: Inject repository dependency via init
public struct {pascal}Route: View {{
    @State private var viewModel = {pascal}ViewModel()

    public var body: some View {{
        {pascal}Screen(viewModel: viewModel)
            .task {{ await viewModel.onAppear() }}
            .refreshable {{ await viewModel.refresh() }}
            .navigationTitle("{pascal}")
    }}
}}
'''


def generate_viewmodel_tests(feature_name: str) -> str:
    """Generate ViewModel test file."""
    pascal = to_pascal_case(feature_name)

    return f'''import Testing
@testable import Feature{pascal}

@Suite("{pascal}ViewModel")
struct {pascal}ViewModelTests {{

    @Test("starts with empty state")
    func startsEmpty() async {{
        let viewModel = await {pascal}ViewModel()
        await #expect(viewModel.items.isEmpty)
        await #expect(viewModel.isLoading == false)
        await #expect(viewModel.errorMessage == nil)
    }}

    @Test("loads items on appear")
    func loadsItemsOnAppear() async {{
        let viewModel = await {pascal}ViewModel()
        await viewModel.onAppear()

        await #expect(!viewModel.items.isEmpty)
        await #expect(viewModel.isLoading == false)
    }}
}}
'''


def generate_feature_module(feature_name: str, project_path: Path):
    """Generate complete iOS feature module structure."""
    pascal = to_pascal_case(feature_name)

    sources_dir = project_path / "Sources" / f"Feature{pascal}"
    tests_dir = project_path / "Tests" / f"Feature{pascal}Tests"

    # Create directories
    create_directory(sources_dir)
    create_directory(tests_dir)

    # Generate source files
    write_file(sources_dir / f"{pascal}ViewModel.swift", generate_viewmodel(feature_name))
    write_file(sources_dir / f"{pascal}Screen.swift", generate_screen(feature_name))
    write_file(sources_dir / f"{pascal}Route.swift", generate_route(feature_name))

    # Generate test files
    write_file(tests_dir / f"{pascal}ViewModelTests.swift", generate_viewmodel_tests(feature_name))

    print(f"\nFeature module 'Feature{pascal}' generated successfully!")
    print(f"\nNext steps:")
    print(f"1. Add to Package.swift products:")
    print(f'   .library(name: "Feature{pascal}", targets: ["Feature{pascal}"]),')
    print(f"\n2. Add to Package.swift targets:")
    print(f'   .target(')
    print(f'       name: "Feature{pascal}",')
    print(f'       dependencies: ["CoreData", "CoreUI"]')
    print(f'   ),')
    print(f'   .testTarget(')
    print(f'       name: "Feature{pascal}Tests",')
    print(f'       dependencies: ["Feature{pascal}", "CoreTesting"]')
    print(f'   ),')
    print(f"\n3. Import Feature{pascal} in your App target")
    print(f"4. Add {pascal}Route to your navigation")


def main():
    parser = argparse.ArgumentParser(
        description="Generate iOS feature module following claude-ios-skill patterns"
    )
    parser.add_argument(
        "name",
        help="Feature name (kebab-case, e.g., 'user-profile')"
    )
    parser.add_argument(
        "--path",
        required=True,
        help="Path to AppModules package (contains Package.swift)"
    )

    args = parser.parse_args()

    project_path = Path(args.path).resolve()

    if not project_path.exists():
        print(f"Error: Path does not exist: {project_path}")
        sys.exit(1)

    print(f"Generating feature module: {args.name}")
    print(f"Path: {project_path}")
    print()

    generate_feature_module(args.name, project_path)


if __name__ == "__main__":
    main()
