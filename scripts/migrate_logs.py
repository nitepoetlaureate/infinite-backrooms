#!/usr/bin/env python3
"""
Log File Migration Script

This script migrates old log files to the new standardized naming convention:
  Old formats: backroom_*.txt, ai_conversation_*.txt
  New format: streamlit_backroom_YYYY-MM-DD.txt

Usage:
    python scripts/migrate_logs.py [--log-dir DIR] [--dry-run] [--verbose]

Options:
    --log-dir DIR    Directory containing log files (default: conversations/)
    --dry-run        Show what would be migrated without making changes
    --verbose        Show detailed output
    --help           Show this help message
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

# Old log file patterns to match
OLD_PATTERNS = [
    r"backroom_(\d{4}-\d{2}-\d{2})\.txt",
    r"ai_conversation_(\d{4}-\d{2}-\d{2})\.txt",
    r"conversation_(\d{4}-\d{2}-\d{2})\.txt",
]

# New standardized format
NEW_PATTERN_TEMPLATE = "streamlit_backroom_{date}.txt"
CURRENT_PATTERN = r"streamlit_backroom_(\d{4}-\d{2}-\d{2})\.txt"


def find_old_log_files(log_dir: Path, verbose: bool = False) -> list[tuple[Path, str]]:
    """
    Find all log files that need migration.

    Args:
        log_dir: Directory to search for log files
        verbose: Whether to show detailed output

    Returns:
        List of tuples (file_path, extracted_date)
    """
    files_to_migrate = []

    if not log_dir.exists():
        print(f"❌ Error: Directory '{log_dir}' does not exist")
        return files_to_migrate

    for txt_file in log_dir.glob("*.txt"):
        for pattern in OLD_PATTERNS:
            match = re.match(pattern, txt_file.name)
            if match:
                date_str = match.group(1)
                files_to_migrate.append((txt_file, date_str))
                if verbose:
                    print(f"Found old format: {txt_file.name}")
                break

    return files_to_migrate


def validate_date(date_str: str) -> bool:
    """
    Validate that the date string is in YYYY-MM-DD format.

    Args:
        date_str: Date string to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def generate_new_filename(date_str: str) -> str:
    """
    Generate new standardized filename.

    Args:
        date_str: Date in YYYY-MM-DD format

    Returns:
        New filename string
    """
    return NEW_PATTERN_TEMPLATE.format(date=date_str)


def migrate_file(
    old_path: Path, date_str: str, dry_run: bool = False, verbose: bool = False
) -> bool:
    """
    Migrate a single log file to new naming convention.

    Args:
        old_path: Current file path
        date_str: Extracted date string
        dry_run: If True, don't actually rename
        verbose: Show detailed output

    Returns:
        True if migration successful (or would be successful in dry-run)
    """
    # Validate date
    if not validate_date(date_str):
        print(f"⚠️  Invalid date format in {old_path.name}: {date_str}")
        return False

    # Generate new filename
    new_filename = generate_new_filename(date_str)
    new_path = old_path.parent / new_filename

    # Check if target already exists
    if new_path.exists():
        if verbose:
            print(f"⏭️  Skipping {old_path.name} → {new_filename} (target exists)")
        return False

    # Perform migration
    if dry_run:
        print(f"📝 Would migrate: {old_path.name} → {new_filename}")
        return True
    else:
        try:
            old_path.rename(new_path)
            print(f"✅ Migrated: {old_path.name} → {new_filename}")
            return True
        except Exception as e:
            print(f"❌ Error migrating {old_path.name}: {e}")
            return False


def check_conflicts(log_dir: Path, files_to_migrate: list[tuple[Path, str]]) -> list[str]:
    """
    Check for potential filename conflicts.

    Args:
        log_dir: Log directory
        files_to_migrate: List of files to migrate

    Returns:
        List of conflict messages
    """
    conflicts = []

    for old_path, date_str in files_to_migrate:
        new_filename = generate_new_filename(date_str)
        new_path = log_dir / new_filename

        if new_path.exists():
            conflicts.append(
                f"Conflict: {old_path.name} → {new_filename} (target already exists)"
            )

    return conflicts


def show_summary(
    total_files: int,
    migrated: int,
    skipped: int,
    failed: int,
    dry_run: bool = False
):
    """
    Show migration summary.

    Args:
        total_files: Total files found
        migrated: Number of files migrated
        skipped: Number of files skipped
        failed: Number of files that failed
        dry_run: Whether this was a dry run
    """
    print("\n" + "=" * 60)
    print("Migration Summary")
    print("=" * 60)
    print(f"Total old log files found: {total_files}")
    print(f"{'Would be migrated' if dry_run else 'Successfully migrated'}: {migrated}")
    print(f"Skipped (target exists): {skipped}")
    print(f"Failed: {failed}")
    print("=" * 60)

    if dry_run and migrated > 0:
        print("\n💡 Run without --dry-run to perform actual migration")


def main():
    """Main entry point for log migration script."""
    parser = argparse.ArgumentParser(
        description="Migrate log files to standardized naming convention",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run to see what would be migrated
  python scripts/migrate_logs.py --dry-run

  # Migrate files in default directory
  python scripts/migrate_logs.py

  # Migrate files in custom directory
  python scripts/migrate_logs.py --log-dir /path/to/logs

  # Verbose output
  python scripts/migrate_logs.py --verbose
        """
    )

    parser.add_argument(
        "--log-dir",
        type=Path,
        default=Path("conversations"),
        help="Directory containing log files (default: conversations/)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without making changes"
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed output"
    )

    args = parser.parse_args()

    # Banner
    print("=" * 60)
    print("Log File Migration Tool")
    print("=" * 60)
    print(f"Log directory: {args.log_dir.absolute()}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE MIGRATION'}")
    print("=" * 60 + "\n")

    # Find files to migrate
    files_to_migrate = find_old_log_files(args.log_dir, args.verbose)

    if not files_to_migrate:
        print("✅ No old log files found. All files are already using the current naming convention.")
        return 0

    print(f"Found {len(files_to_migrate)} file(s) to migrate\n")

    # Check for conflicts
    conflicts = check_conflicts(args.log_dir, files_to_migrate)
    if conflicts:
        print("⚠️  Warning: Found potential conflicts:\n")
        for conflict in conflicts:
            print(f"  {conflict}")
        print()

    # Perform migration
    migrated = 0
    skipped = 0
    failed = 0

    for old_path, date_str in files_to_migrate:
        result = migrate_file(old_path, date_str, args.dry_run, args.verbose)

        if result:
            migrated += 1
        else:
            new_filename = generate_new_filename(date_str)
            new_path = old_path.parent / new_filename
            if new_path.exists():
                skipped += 1
            else:
                failed += 1

    # Show summary
    show_summary(len(files_to_migrate), migrated, skipped, failed, args.dry_run)

    # Return appropriate exit code
    if failed > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
