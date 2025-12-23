set dotenv-load

# Default recipe to run when just is called without arguments
default:
    @just --list

test test_file_or_dir="--durations=5 tests":
   uv run pytest --cov=src --cov-report term-missing:skip-covered {{test_file_or_dir}}

typecheck:
    uv run ty check src tests

format:
    uv run ruff check --fix .
    uv run ruff format .

check: format typecheck test

seed *tables:
 cd src && python -m tools.seed {{tables}}

run:
 cd src && exec python -m backend.main

# Bump git tag version (major, minor, or patch)
tag-bump type="patch":
    #!/usr/bin/env python3
    import subprocess
    import sys
    
    try:
        import semver
    except ImportError:
        print("Error: semver package not installed. Run: uv sync")
        sys.exit(1)
    
    bump_type = "{{type}}"
    
    # Get the latest tag
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True,
            text=True,
            check=True
        )
        latest_tag = result.stdout.strip()
    except subprocess.CalledProcessError:
        latest_tag = "0.0.0"
    
    # Strip 'v' prefix if present
    version_str = latest_tag.lstrip('v')
    
    # Parse current version
    try:
        current_version = semver.Version.parse(version_str)
    except ValueError:
        print(f"Error: Invalid semantic version tag '{latest_tag}'")
        sys.exit(1)
    
    # Bump version based on type
    if bump_type == "major":
        new_version = current_version.bump_major()
    elif bump_type == "minor":
        new_version = current_version.bump_minor()
    elif bump_type == "patch":
        new_version = current_version.bump_patch()
    else:
        print(f"Error: Invalid bump type '{bump_type}'. Use: major, minor, or patch")
        sys.exit(1)
    
    new_tag = str(new_version)
    
    # Check for uncommitted changes
    result = subprocess.run(
        ["git", "diff", "--quiet"],
        capture_output=True
    )
    has_uncommitted = result.returncode != 0
    
    result = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        capture_output=True
    )
    has_staged = result.returncode != 0
    
    if has_uncommitted or has_staged:
        print("Warning: You have uncommitted changes in your working directory")
        if sys.stdin.isatty():
            response = input("Continue creating tag anyway? [y/N]: ")
            if response.lower() != 'y':
                print("Tag creation cancelled")
                sys.exit(0)
        else:
            print("Running in non-interactive mode, proceeding with tag creation...")
    
    # Create the new tag
    try:
        subprocess.run(
            ["git", "tag", new_tag],
            check=True
        )
        print(f"✓ Bumped version from {current_version} to {new_version}")
        print(f"✓ Created tag: {new_tag}")
    except subprocess.CalledProcessError as e:
        print(f"Error creating tag: {e}")
        sys.exit(1)