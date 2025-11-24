# Chrome Profile Migration Script

An interactive Python script to selectively migrate data between Chrome profiles.

**Platform: macOS only** (uses macOS-specific paths and commands)

## Features

- **Profile discovery** - Automatically finds Chrome profiles on first run
- **Interactive setup** - Choose source and destination profiles easily
- **Config file** - Save your profile paths for reuse
- **Interactive menu** - Choose exactly what to migrate with checkboxes
- **Safe defaults** - Extensions, bookmarks, keyword searches, and profile picture enabled by default
- **Automatic backup** - Creates timestamped backup before any changes
- **Smart migration** - Won't duplicate existing data
- **Vanilla Python** - Uses only standard library (no external dependencies!)

## What it can migrate

1. **Extensions** ✓ (enabled by default)
   - All installed extensions and their data
   - Extension Rules, Scripts, State
   - Local Extension Settings
   - **Preferences** (tells Chrome which extensions are installed)
   - **Secure Preferences** (extension settings and permissions)

2. **Bookmarks** ✓ (enabled by default)
   - All bookmarks and folders
   - Bookmarks file + backup

3. **Keyword Searches** ✓ (enabled by default)
   - Custom search engines from the omnibox
   - Extracted from Web Data SQLite database
   - Only migrates custom searches (not pre-populated ones)

4. **Profile Picture** ✓ (enabled by default)
   - Your Google profile picture

5. **Tabs & Sessions** ✗ (disabled by default)
   - Restores your previously open tabs and windows
   - **Warning**: This will replace your current tabs!

## Requirements

- Python 3 (uses only standard library - no pip install needed!)
- macOS
- Chrome must be closed during migration

## Quick Start

### IMPORTANT: Create New Profile First

**To avoid account contamination, follow this workflow:**

1. **Create a fresh Chrome profile WITHOUT signing in:**
   - Open Chrome
   - Click your profile icon → "Add" → "Continue without an account"
   - Give it a name (e.g., "New Profile")
   - **DO NOT sign in to Google yet!**

2. **Note the profile name** (e.g., "Profile 17") by checking:
   - Chrome Settings → You and Google → (profile name shown at top)
   - Or check `~/Library/Application Support/Google/Chrome/` for the newest profile folder

3. **Close Chrome completely** (not just the window - quit Chrome)

4. **Run the migration to restore your settings into this new profile**

5. **After migration is complete, open Chrome and sign in** to your Google account to start sync

This ensures the new profile isn't contaminated with old account data from the backup.

### First Run - Profile Discovery

1. **Run the script:**
   ```bash
   chmod +x migrate_chrome_profile.py
   ./migrate_chrome_profile.py
   ```

2. **The script will automatically discover Chrome profiles** and show you a menu:
   ```
   ============================================================
   No config.ini found. Let's set up your profiles.
   ============================================================
   [12:34:56] Discovering Chrome profiles...
   [12:34:56] Found 3 Chrome profile(s)

   SELECT SOURCE PROFILE (to migrate FROM):
   ============================================================
   1. Default
      ~/Library/Application Support/Google/Chrome/Default
   2. Profile 1
      ~/Library/Application Support/Google/Chrome/Profile 1
   3. Profile 16
      ~/Library/Application Support/Google/Chrome/Profile 16

   Or enter a custom path (e.g., ~/Desktop/backup/Profile)
   ============================================================

   Your choice (number or path):
   ```

3. **Choose your source** (e.g., `1` for Default or enter a custom path like `~/Desktop/chrome_backup/Default`)

4. **Choose your destination:**
   - **Option 0 (recommended)**: Automatically creates `~/backups/Default_20250117/`
   - Or select an existing Chrome profile to migrate into
   - Or enter a custom path

5. **The script creates `config.ini`** and exits. Run it again to perform migration!

### Subsequent Runs - Migration

1. **Run the script again:**
   ```bash
   ./migrate_chrome_profile.py
   ```

2. **The script loads your saved profiles** from `config.ini` and shows the migration menu:
   ```
   ============================================================
   Select what to migrate (current defaults shown):
   ============================================================
   1. [X] Extensions and extension settings
   2. [X] Bookmarks and bookmark folders
   3. [X] Custom search engines (omnibox keywords)
   4. [X] Google profile picture
   5. [ ] Open tabs and windows (restores last session)

   Options:
     - Enter numbers to toggle (e.g., '1 3 5' or '1,3,5')
     - Press Enter to accept current selection
     - Type 'all' to select everything
     - Type 'none' to deselect everything
   ============================================================
   ```

3. **Make your selections and the script handles the rest:**
   - Checks if Chrome is running (must be closed)
   - Creates automatic backup
   - Migrates selected items
   - Shows completion summary

4. **Verify the migration** by opening Chrome and checking:
   - Extensions are installed and working
   - Bookmarks are in the bookmark bar
   - Custom search engines in Settings → Search engine
   - Profile picture appears in Chrome toolbar
   - Tabs restored (if enabled)

## Configuration

### Changing Profile Paths

Edit `config.ini` to change which profiles to use:

```ini
[profiles]
from_profile = ~/Desktop/chrome_backup/Default
to_profile = ~/backups/Default_20250117
```

**Other destination examples:**
```ini
# Migrate to existing Chrome profile
to_profile = ~/Library/Application Support/Google/Chrome/Profile 16

# Custom backup location
to_profile = ~/.backup/chrome_backup_20250117
```

### Changing Migration Defaults

Edit `MIGRATION_OPTIONS` in the script to change what's selected by default:

```python
MIGRATION_OPTIONS = {
    'extensions': {'enabled': True, ...},
    'bookmarks': {'enabled': True, ...},
    'keyword_searches': {'enabled': True, ...},
    'profile_picture': {'enabled': True, ...},
    'tabs': {'enabled': False, ...}  # Off by default
}
```

## Safety Features

- **Automatic backup**: Creates a timestamped backup of destination profile before migration
- **Non-destructive**: If something goes wrong, restore from the backup directory
- **Chrome check**: Warns if Chrome is running (must be closed for safe migration)
- **Duplicate prevention**: Won't overwrite existing keyword searches with the same name
- **Path validation**: Creates destination directory if it doesn't exist
- **Account sanitization**: Automatically removes old account information from Preferences files to prevent account contamination

## Backup Location

The script creates a backup at:
```
<destination_profile>.backup_YYYYMMDD_HHMMSS/
```

Example:
```
~/Library/Application Support/Google/Chrome/Profile 16.backup_20250117_123456/
```

## Troubleshooting

**No config.ini found on subsequent runs:**
- The script will run profile discovery again
- Or manually create `config.ini` following `config.ini.example` format

**Source or destination path doesn't exist:**
- Check your `config.ini` paths
- Make sure source profile exists
- Destination can be created automatically if it doesn't exist

**Extensions not showing up:**
- Make sure Chrome is completely closed during migration
- The script copies both extension files AND Preferences
- After migration, restart Chrome completely (not just close the window)

**Bookmarks not showing:**
- Check if the bookmark bar is enabled (⌘⇧B)
- Verify the source profile had bookmark files

**Keyword searches missing:**
- Check Chrome Settings > Search Engine > Manage search engines
- The source's Web Data database may not have had custom searches

**Old account email still showing up:**
- This can happen if you signed in to the profile BEFORE running migration
- **Solution**: Create a NEW profile without signing in first, then migrate into it
- The script sanitizes Preferences files, but Chrome may cache account info if already signed in
- After migration completes, THEN sign in to your new account

## Example Output

### First Run (Profile Discovery)
```
╔════════════════════════════════════════════╗
║  Chrome Profile Migration Script          ║
║  macOS only                                ║
╚════════════════════════════════════════════╝

============================================================
No config.ini found. Let's set up your profiles.
============================================================
[12:34:56] Discovering Chrome profiles...
[12:34:56] Found 2 Chrome profile(s)

SELECT SOURCE PROFILE (to migrate FROM):
============================================================
1. Default
   ~/Library/Application Support/Google/Chrome/Default
2. Profile 16
   ~/Library/Application Support/Google/Chrome/Profile 16

Or enter a custom path (e.g., ~/Desktop/backup/Profile)
============================================================

Your choice (number or path): 1

✓ Source: ~/Library/Application Support/Google/Chrome/Default

============================================================
SELECT DESTINATION (to migrate TO):
============================================================
Choose where to migrate your profile data:

0. Create backup in ~/backups/ (recommended)
   → ~/backups/Default_20250117

1. Default
   ~/Library/Application Support/Google/Chrome/Default
2. Profile 16
   ~/Library/Application Support/Google/Chrome/Profile 16

Or enter a custom path
============================================================

Your choice (0 for backup, number, or path): 0

✓ Destination: ~/backups/Default_20250117

============================================================
✓ Configuration saved!
============================================================

Your config.ini has been created with:
  FROM: ~/Library/Application Support/Google/Chrome/Default
  TO:   ~/backups/Default_20250117

You can edit config.ini anytime to change these paths.

Now run the script again to perform the migration:
  ./migrate_chrome_profile.py
============================================================
```

### Migration Run
```
╔════════════════════════════════════════════╗
║  Chrome Profile Migration Script          ║
║  macOS only                                ║
╚════════════════════════════════════════════╝

Using profiles from config.ini:
  FROM: /Users/you/Desktop/chrome_backup/Default
  TO:   /Users/you/Library/Application Support/Google/Chrome/Profile 16

[12:34:56] ✓ Source profile found: /Users/you/Desktop/chrome_backup/Default
[12:34:56] ✓ Destination profile found: .../Profile 16

============================================================
Select what to migrate (current defaults shown):
============================================================
1. [X] Extensions and extension settings
2. [X] Bookmarks and bookmark folders
3. [X] Custom search engines (omnibox keywords)
4. [X] Google profile picture
5. [ ] Open tabs and windows (restores last session)

Your choice: [Enter to accept]

============================================================
Will migrate:
  ✓ Extensions and extension settings
  ✓ Bookmarks and bookmark folders
  ✓ Custom search engines (omnibox keywords)
  ✓ Google profile picture
============================================================

[12:34:57] Creating backup of Profile 16...
[12:34:58] ✓ Backup created successfully

=== Copying Extensions ===
[12:34:58] Copying Extensions...
[12:35:02] ✓ Copied 9 extensions

=== Copying Extension Preferences ===
[12:35:02] Copying Preferences...
[12:35:02] ✓ Copied Preferences (258.4 KB)

=== Copying Bookmarks ===
[12:35:02] Copying Bookmarks...
[12:35:02] ✓ Copied Bookmarks (42156 bytes)

=== Copying Profile Picture ===
[12:35:02] ✓ Copied profile picture

=== Migrating Keyword Searches ===
[12:35:03] Found 3 custom keyword search(es)
[12:35:03]   ✓ Migrated 'gh' (GitHub)
[12:35:03] ✓ Migrated 2 keyword search(es)

============================================================
✓ Migration complete!
✓ Backup saved at: ...Profile 16.backup_20250117_123458
============================================================
```

## What's NOT migrated

- Passwords (for security reasons)
- History
- Cookies and sessions
- Cache
- Autofill data
- Site settings
- Extension-specific local data (may vary)

To migrate these, you'll need to either:
1. Sign in to Chrome sync
2. Manually export/import them
3. Copy additional files (not recommended without Chrome closed)
