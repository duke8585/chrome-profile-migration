#!/usr/bin/env python3
"""
Chrome Profile Migration Script
Migrates extensions, bookmarks, keyword searches, and more from a backup profile to Profile 16
"""

import os
import shutil
import sqlite3
import sys
from pathlib import Path
from datetime import datetime
import subprocess
import configparser
import tempfile

# ============================================================================
# CONFIGURATION - What to migrate (change defaults here)
# ============================================================================

# Configuration file
CONFIG_FILE = "config.ini"
CONFIG_EXAMPLE = "config.ini.example"

# Chrome profile directory (macOS only)
CHROME_DIR = os.path.expanduser("~/Library/Application Support/Google/Chrome")

# Migration options - Set to True/False to enable/disable by default
MIGRATION_OPTIONS = {
    'extensions': {
        'enabled': True,
        'description': 'Extensions and extension settings'
    },
    'bookmarks': {
        'enabled': True,
        'description': 'Bookmarks and bookmark folders'
    },
    'keyword_searches': {
        'enabled': True,
        'description': 'Custom search engines (omnibox keywords)'
    },
    'profile_picture': {
        'enabled': True,
        'description': 'Google profile picture'
    },
    'tabs': {
        'enabled': False,  # Off by default - can restore old tabs
        'description': 'Open tabs and windows (restores last session)'
    }
}

# Items to migrate based on options
EXTENSIONS_DIRS = [
    "Extensions",
    "Extension Rules",
    "DNR Extension Rules",
    "Extension Scripts",
    "Extension State",
    "Local Extension Settings"
]

EXTENSION_PREFERENCE_FILES = [
    "Preferences",
    "Secure Preferences"
]

BOOKMARK_FILES = [
    "Bookmarks",
    "Bookmarks.bak"
]

PROFILE_PICTURE_FILE = "Google Profile Picture.png"

TABS_ITEMS = [
    "Sessions",
    "Session Storage"
]

def log(message):
    """Print timestamped log message"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def load_config():
    """Load configuration from config.ini file"""
    config = configparser.ConfigParser()

    if not os.path.exists(CONFIG_FILE):
        return None

    config.read(CONFIG_FILE)

    if 'profiles' not in config:
        return None

    from_profile = config['profiles'].get('from_profile', '').strip()
    to_profile = config['profiles'].get('to_profile', '').strip()

    if not from_profile or not to_profile:
        return None

    return {
        'from_profile': os.path.expanduser(from_profile),
        'to_profile': os.path.expanduser(to_profile)
    }

def discover_chrome_profiles():
    """Discover available Chrome profiles on the system"""
    profiles = []

    if not os.path.exists(CHROME_DIR):
        return profiles

    # Look for Default and Profile N directories
    for item in os.listdir(CHROME_DIR):
        item_path = os.path.join(CHROME_DIR, item)

        # Check if it's a directory and looks like a profile
        if os.path.isdir(item_path):
            # Check for Preferences file to confirm it's a profile
            prefs_file = os.path.join(item_path, "Preferences")
            if item == "Default" or item.startswith("Profile "):
                if os.path.exists(prefs_file):
                    profiles.append({
                        'name': item,
                        'path': item_path
                    })

    # Sort profiles (Default first, then Profile 1, Profile 2, etc.)
    def sort_key(p):
        if p['name'] == 'Default':
            return (0, 0)
        elif p['name'].startswith('Profile '):
            try:
                num = int(p['name'].split()[1])
                return (1, num)
            except:
                return (2, p['name'])
        return (2, p['name'])

    profiles.sort(key=sort_key)
    return profiles

def select_profile(profiles, prompt):
    """Let user select a profile from the list"""
    print(f"\n{prompt}")
    print("="*60)

    for i, profile in enumerate(profiles, 1):
        print(f"{i}. {profile['name']}")
        print(f"   {profile['path']}")

    print("\nOr enter a custom path (e.g., ~/Desktop/backup/Profile)")
    print("="*60)

    while True:
        choice = input("\nYour choice (number or path): ").strip()

        if not choice:
            print("Please enter a number or path")
            continue

        # Check if it's a number
        try:
            num = int(choice)
            if 1 <= num <= len(profiles):
                return profiles[num - 1]['path']
            else:
                print(f"Please enter a number between 1 and {len(profiles)}")
        except ValueError:
            # It's a path
            expanded_path = os.path.expanduser(choice)
            if os.path.exists(expanded_path):
                return expanded_path
            else:
                print(f"Path does not exist: {expanded_path}")
                retry = input("Try again? (y/n): ").strip().lower()
                if retry != 'y':
                    return None

def create_config(from_profile, to_profile):
    """Create config.ini file with selected profiles"""
    config = configparser.ConfigParser()

    config['profiles'] = {
        'from_profile': from_profile,
        'to_profile': to_profile
    }

    with open(CONFIG_FILE, 'w') as f:
        config.write(f)

    log(f"✓ Created {CONFIG_FILE}")

def run_profile_discovery():
    """Interactive profile discovery and config creation"""
    print("\n" + "="*60)
    print("No config.ini found. Let's set up your profiles.")
    print("="*60)

    # Discover profiles
    log("Discovering Chrome profiles...")
    profiles = discover_chrome_profiles()

    if not profiles:
        log("⚠️  No Chrome profiles found in standard location")
        log(f"Expected location: {CHROME_DIR}")
        print("\nPlease manually create config.ini with your profile paths.")
        print(f"See {CONFIG_EXAMPLE} for the format.")
        sys.exit(1)

    log(f"Found {len(profiles)} Chrome profile(s)")

    # Select source profile
    from_profile = select_profile(profiles, "SELECT SOURCE PROFILE (to migrate FROM):")
    if not from_profile:
        log("Source profile selection cancelled")
        sys.exit(1)

    print(f"\n✓ Source: {from_profile}")

    # Select destination
    print("\n" + "="*60)
    print("SELECT DESTINATION (to migrate TO):")
    print("="*60)
    print("Choose where to migrate your profile data:")
    print()
    print("0. Create backup in ~/backups/ (recommended)")

    source_name = os.path.basename(from_profile)
    timestamp = datetime.now().strftime('%Y%m%d')
    backup_path = os.path.expanduser(f"~/backups/{source_name}_{timestamp}")
    print(f"   → {backup_path}")
    print()

    for i, profile in enumerate(profiles, 1):
        print(f"{i}. {profile['name']}")
        print(f"   {profile['path']}")

    print("\nOr enter a custom path")
    print("="*60)

    while True:
        choice = input("\nYour choice (0 for backup, number, or path): ").strip()

        if not choice:
            print("Please enter a choice")
            continue

        # Option 0: Create backup
        if choice == '0':
            to_profile = backup_path
            break

        # Check if it's a number
        try:
            num = int(choice)
            if 1 <= num <= len(profiles):
                to_profile = profiles[num - 1]['path']
                break
            else:
                print(f"Please enter 0 or a number between 1 and {len(profiles)}")
        except ValueError:
            # It's a custom path
            expanded_path = os.path.expanduser(choice)
            if os.path.exists(expanded_path):
                to_profile = expanded_path
                break
            else:
                print(f"Path does not exist: {expanded_path}")
                create = input("Create it? (y/n): ").strip().lower()
                if create == 'y':
                    to_profile = expanded_path
                    break

    print(f"\n✓ Destination: {to_profile}")

    # Create config file
    print("\n" + "="*60)
    log("Creating config.ini with your selections...")
    create_config(from_profile, to_profile)

    print("\n" + "="*60)
    print("✓ Configuration saved!")
    print("="*60)
    print(f"\nYour config.ini has been created with:")
    print(f"  FROM: {from_profile}")
    print(f"  TO:   {to_profile}")
    print(f"\nYou can edit {CONFIG_FILE} anytime to change these paths.")
    print("\nNow run the script again to perform the migration:")
    print("  ./migrate_chrome_profile.py")
    print("="*60)
    sys.exit(0)

def check_chrome_running():
    """Check if Chrome is running and warn user"""
    try:
        result = subprocess.run(
            ["pgrep", "-x", "Google Chrome"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            log("⚠️  WARNING: Chrome is currently running!")
            response = input("Chrome must be closed for migration. Close it now? (y/n): ")
            if response.lower() == 'y':
                log("Please close Chrome manually, then press Enter to continue...")
                input()
            else:
                log("Migration cancelled.")
                sys.exit(0)
    except Exception as e:
        log(f"Could not check if Chrome is running: {e}")

def validate_paths(from_profile, to_profile):
    """Validate source and destination paths"""
    if not os.path.exists(from_profile):
        log(f"❌ ERROR: Source profile not found: {from_profile}")
        log(f"Please check your {CONFIG_FILE} settings")
        sys.exit(1)

    if not os.path.exists(to_profile):
        log(f"⚠️  WARNING: Destination profile not found: {to_profile}")
        response = input("Destination doesn't exist. Create it? (y/n): ").strip().lower()
        if response == 'y':
            try:
                os.makedirs(to_profile, exist_ok=True)
                log(f"✓ Created destination directory: {to_profile}")
            except Exception as e:
                log(f"❌ ERROR: Could not create destination: {e}")
                sys.exit(1)
        else:
            log("Migration cancelled")
            sys.exit(1)

    log(f"✓ Source profile found: {from_profile}")
    log(f"✓ Destination profile found: {to_profile}")

def show_migration_menu(options):
    """Show interactive menu to select what to migrate"""
    print("\n" + "="*60)
    print("Select what to migrate (current defaults shown):")
    print("="*60)

    for i, (key, config) in enumerate(options.items(), 1):
        status = "[X]" if config['enabled'] else "[ ]"
        print(f"{i}. {status} {config['description']}")

    print("\nOptions:")
    print("  - Enter numbers to toggle (e.g., '1 3 5' or '1,3,5')")
    print("  - Press Enter to accept current selection")
    print("  - Type 'all' to select everything")
    print("  - Type 'none' to deselect everything")
    print("="*60)

    while True:
        choice = input("\nYour choice: ").strip().lower()

        if choice == '':
            break
        elif choice == 'all':
            for key in options:
                options[key]['enabled'] = True
            show_migration_menu(options)
            return options
        elif choice == 'none':
            for key in options:
                options[key]['enabled'] = False
            show_migration_menu(options)
            return options
        else:
            # Parse numbers
            try:
                # Handle both space and comma separated
                numbers = choice.replace(',', ' ').split()
                keys = list(options.keys())

                for num_str in numbers:
                    num = int(num_str)
                    if 1 <= num <= len(keys):
                        key = keys[num - 1]
                        options[key]['enabled'] = not options[key]['enabled']
                    else:
                        print(f"Invalid number: {num}")

                show_migration_menu(options)
                return options
            except ValueError:
                print("Invalid input. Please enter numbers, 'all', 'none', or press Enter.")

    return options

def create_backup(to_profile):
    """Create backup of destination profile before migration"""
    backup_dir = to_profile + f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    log(f"Creating backup at: {backup_dir}")

    try:
        shutil.copytree(to_profile, backup_dir)
        log(f"✓ Backup created successfully")
        return backup_dir
    except Exception as e:
        log(f"❌ ERROR creating backup: {e}")
        sys.exit(1)

def copy_extensions(from_profile, to_profile):
    """Copy extension directories from source to destination"""
    log("\n=== Copying Extensions ===")

    for dir_name in EXTENSIONS_DIRS:
        source = os.path.join(from_profile, dir_name)
        dest = os.path.join(to_profile, dir_name)

        if not os.path.exists(source):
            log(f"⚠️  Skipping {dir_name} (not found in backup)")
            continue

        try:
            # Remove existing directory if it exists
            if os.path.exists(dest):
                log(f"Removing existing {dir_name}...")
                shutil.rmtree(dest)

            # Copy the directory
            log(f"Copying {dir_name}...")
            shutil.copytree(source, dest)

            # Count extensions if it's the main Extensions directory
            if dir_name == "Extensions":
                ext_count = len([d for d in os.listdir(dest) if os.path.isdir(os.path.join(dest, d))])
                log(f"✓ Copied {ext_count} extensions")
            else:
                log(f"✓ Copied {dir_name}")

        except Exception as e:
            log(f"❌ ERROR copying {dir_name}: {e}")

def copy_bookmarks(from_profile, to_profile):
    """Copy bookmark files from source to destination"""
    log("\n=== Copying Bookmarks ===")

    for filename in BOOKMARK_FILES:
        source = os.path.join(from_profile, filename)
        dest = os.path.join(to_profile, filename)

        if not os.path.exists(source):
            log(f"⚠️  Skipping {filename} (not found in backup)")
            continue

        try:
            log(f"Copying {filename}...")
            shutil.copy2(source, dest)

            file_size = os.path.getsize(source)
            log(f"✓ Copied {filename} ({file_size} bytes)")

        except Exception as e:
            log(f"❌ ERROR copying {filename}: {e}")

def copy_profile_picture(from_profile, to_profile):
    """Copy Google profile picture"""
    log("\n=== Copying Profile Picture ===")

    source = os.path.join(from_profile, PROFILE_PICTURE_FILE)
    dest = os.path.join(to_profile, PROFILE_PICTURE_FILE)

    if not os.path.exists(source):
        log(f"⚠️  Profile picture not found in backup")
        return

    try:
        log(f"Copying profile picture...")
        shutil.copy2(source, dest)
        log(f"✓ Copied profile picture")
    except Exception as e:
        log(f"❌ ERROR copying profile picture: {e}")

def copy_tabs(from_profile, to_profile):
    """Copy tabs and sessions to restore open tabs"""
    log("\n=== Copying Tabs & Sessions ===")
    log("⚠️  This will restore your old open tabs and windows")

    for item_name in TABS_ITEMS:
        source = os.path.join(from_profile, item_name)
        dest = os.path.join(to_profile, item_name)

        if not os.path.exists(source):
            log(f"⚠️  Skipping {item_name} (not found in backup)")
            continue

        try:
            if os.path.isdir(source):
                # Remove existing directory if it exists
                if os.path.exists(dest):
                    log(f"Removing existing {item_name}...")
                    shutil.rmtree(dest)

                log(f"Copying {item_name}...")
                shutil.copytree(source, dest)

                if item_name == "Sessions":
                    session_files = len([f for f in os.listdir(dest) if os.path.isfile(os.path.join(dest, f))])
                    log(f"✓ Copied {item_name} ({session_files} session files)")
                else:
                    log(f"✓ Copied {item_name}")
            else:
                log(f"Copying {item_name}...")
                shutil.copy2(source, dest)
                log(f"✓ Copied {item_name}")

        except Exception as e:
            log(f"❌ ERROR copying {item_name}: {e}")

def copy_extension_preferences(from_profile, to_profile):
    """Copy Preferences files needed for extensions to be recognized"""
    log("\n=== Copying Extension Preferences ===")

    for filename in EXTENSION_PREFERENCE_FILES:
        source = os.path.join(from_profile, filename)
        dest = os.path.join(to_profile, filename)

        if not os.path.exists(source):
            log(f"⚠️  Skipping {filename} (not found in backup)")
            continue

        try:
            log(f"Copying {filename}...")
            shutil.copy2(source, dest)

            file_size = os.path.getsize(source)
            log(f"✓ Copied {filename} ({file_size / 1024:.1f} KB)")

        except Exception as e:
            log(f"❌ ERROR copying {filename}: {e}")

def migrate_keyword_searches(from_profile, to_profile):
    """Migrate custom keyword searches from Web Data SQLite database"""
    log("\n=== Migrating Keyword Searches ===")

    source_db = os.path.join(from_profile, "Web Data")
    dest_db = os.path.join(to_profile, "Web Data")

    if not os.path.exists(source_db):
        log("⚠️  Web Data database not found in source, skipping keyword searches")
        return

    # If destination doesn't have Web Data, just copy the entire file
    if not os.path.exists(dest_db):
        log("No existing Web Data in destination, copying entire database...")
        try:
            shutil.copy2(source_db, dest_db)
            log("✓ Copied Web Data database (includes all keyword searches)")
            return
        except Exception as e:
            log(f"❌ ERROR copying Web Data database: {e}")
            return

    try:
        # Create temporary copies to work with
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_source:
            temp_source = tmp_source.name
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_dest:
            temp_dest = tmp_dest.name

        shutil.copy2(source_db, temp_source)
        shutil.copy2(dest_db, temp_dest)

        # Connect to both databases
        source_conn = sqlite3.connect(temp_source)
        dest_conn = sqlite3.connect(temp_dest)

        source_cursor = source_conn.cursor()
        dest_cursor = dest_conn.cursor()

        # Get all custom keyword searches from source
        # The keywords table stores custom search engines
        source_cursor.execute("""
            SELECT keyword, short_name, favicon_url, url, safe_for_autoreplace,
                   usage_count, date_created, last_modified
            FROM keywords
            WHERE id NOT IN (
                SELECT id FROM keywords WHERE prepopulate_id > 0
            )
        """)

        keywords = source_cursor.fetchall()

        if not keywords:
            log("No custom keyword searches found in backup")
        else:
            log(f"Found {len(keywords)} custom keyword search(es)")

            # Insert keywords into destination (skip if already exists)
            migrated_count = 0
            for kw in keywords:
                keyword, short_name = kw[0], kw[1]
                try:
                    # Check if keyword already exists
                    dest_cursor.execute("SELECT id FROM keywords WHERE keyword = ?", (keyword,))
                    if dest_cursor.fetchone():
                        log(f"  ⚠️  Skipping '{keyword}' (already exists)")
                        continue

                    # Insert the keyword
                    dest_cursor.execute("""
                        INSERT INTO keywords
                        (keyword, short_name, favicon_url, url, safe_for_autoreplace,
                         usage_count, date_created, last_modified)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, kw)

                    migrated_count += 1
                    log(f"  ✓ Migrated '{keyword}' ({short_name})")

                except sqlite3.Error as e:
                    log(f"  ❌ ERROR migrating '{keyword}': {e}")

            if migrated_count > 0:
                dest_conn.commit()
                log(f"✓ Migrated {migrated_count} keyword search(es)")

                # Copy the modified database back
                shutil.copy2(temp_dest, dest_db)
                log("✓ Updated Web Data database")

        source_conn.close()
        dest_conn.close()

        # Clean up temp files
        os.remove(temp_source)
        os.remove(temp_dest)

    except sqlite3.Error as e:
        log(f"❌ ERROR migrating keyword searches: {e}")
    except Exception as e:
        log(f"❌ ERROR: {e}")

def main():
    """Main migration function"""
    log("╔════════════════════════════════════════════╗")
    log("║  Chrome Profile Migration Script          ║")
    log("║  macOS only                                ║")
    log("╚════════════════════════════════════════════╝")

    # Step 1: Load configuration or run discovery
    config = load_config()
    if not config:
        run_profile_discovery()
        # run_profile_discovery exits after creating config
        return

    from_profile = config['from_profile']
    to_profile = config['to_profile']

    log(f"\nUsing profiles from {CONFIG_FILE}:")
    log(f"  FROM: {from_profile}")
    log(f"  TO:   {to_profile}")

    # Step 2: Check if Chrome is running
    check_chrome_running()

    # Step 3: Validate paths
    validate_paths(from_profile, to_profile)

    # Step 3: Show migration options and let user customize
    import copy
    options = copy.deepcopy(MIGRATION_OPTIONS)
    options = show_migration_menu(options)

    # Check if anything is selected
    if not any(opt['enabled'] for opt in options.values()):
        log("\n⚠️  No items selected for migration. Exiting.")
        sys.exit(0)

    # Show summary of what will be migrated
    log("\n" + "="*60)
    log("Will migrate:")
    for key, config in options.items():
        if config['enabled']:
            log(f"  ✓ {config['description']}")
    log("="*60)

    # Step 4: Create backup
    backup_path = create_backup(to_profile)
    log(f"\nBackup created at: {backup_path}")

    # Step 5: Migrate data based on selections
    if options['extensions']['enabled']:
        copy_extensions(from_profile, to_profile)
        copy_extension_preferences(from_profile, to_profile)  # Critical: must be done after copying extensions

    if options['bookmarks']['enabled']:
        copy_bookmarks(from_profile, to_profile)

    if options['profile_picture']['enabled']:
        copy_profile_picture(from_profile, to_profile)

    if options['tabs']['enabled']:
        copy_tabs(from_profile, to_profile)

    if options['keyword_searches']['enabled']:
        migrate_keyword_searches(from_profile, to_profile)

    # Step 6: Summary
    log("\n" + "="*60)
    log("✓ Migration complete!")
    log(f"✓ Backup saved at: {backup_path}")
    log("="*60)
    log("\nYou can now start Chrome and verify the migration.")
    log("If anything went wrong, restore from the backup directory.")

if __name__ == "__main__":
    main()
