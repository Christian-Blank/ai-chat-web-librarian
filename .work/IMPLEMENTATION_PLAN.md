---
status: done
---
# Implementation Plan for Multi-Platform Chat Downloader

## Overview
Extend the current ChatGPT-only chat librarian to support both ChatGPT and Gemini downloads with a flexible, maintainable architecture.

## Phase 1: Create Base Architecture (Foundation)
**Goal**: Set up abstract base class without breaking existing functionality

### Step 1: Create `base_downloader.py`
- Abstract base class with common browser management
- Abstract methods for platform-specific operations
- Shared utilities (filename sanitization, output directory management)

**Verification Step**: Run existing CLI commands to ensure nothing breaks

## Phase 2: Refactor ChatGPT Implementation
**Goal**: Extract ChatGPT-specific code while maintaining current functionality

### Step 2: Create `chatgpt_downloader.py`
- Copy current `downloader.py` content
- Modify to inherit from `BaseChatDownloader`
- Remove common code (now in base class)

### Step 3: Update imports in `main.py`
- Import from new module location
- No functional changes yet

**Verification Step**: Test all three CLI commands (select, last, title) with ChatGPT

## Phase 3: Add Platform Selection Infrastructure
**Goal**: Support multiple platforms in CLI without breaking defaults

### Step 4: Update CLI in `main.py`
- Add `--platform` parameter (default: "chatgpt")
- Create factory function to instantiate correct downloader
- Update all command functions

**Verification Step**: Test that existing commands still work without --platform flag

## Phase 4: Implement Gemini Support
**Goal**: Add Gemini functionality incrementally

### Step 5: Create `gemini_downloader.py` skeleton
- Basic class structure inheriting from base
- Implement `__aenter__` with Gemini URL
- Stub out other methods

### Step 6: Implement Gemini authentication
- Handle Google login flow
- Test authentication persistence

### Step 7: Implement chat listing
- Map Gemini selectors for sidebar
- Parse chat titles from DOM

### Step 8: Implement chat downloading
- Navigate to specific chat
- Parse messages with Gemini-specific selectors
- Convert to Markdown format

**Verification Step**: Test each Gemini command incrementally

## Phase 5: Polish and Documentation
**Goal**: Ensure robustness and usability

### Step 9: Add error handling
- Platform-specific error messages
- Graceful fallbacks

### Step 10: Update documentation
- README.md with multi-platform usage
- Update help strings in CLI

### Step 11: Final testing
- Test all commands on both platforms
- Verify saved files are properly formatted

## Implementation Order with Verification Points

1. **Base architecture** → Verify: Existing commands work
2. **Refactor ChatGPT** → Verify: ChatGPT downloads work
3. **Add platform CLI** → Verify: Default behavior unchanged
4. **Gemini skeleton** → Verify: Can launch Gemini site
5. **Gemini auth** → Verify: Can log into Google
6. **Gemini list** → Verify: Can see chat titles
7. **Gemini download** → Verify: Can save one chat
8. **Full Gemini** → Verify: All commands work
9. **Polish** → Verify: Error cases handled

## Key Technical Details

### Gemini-Specific Selectors (from DOM analysis)
- **URL**: `https://gemini.google.com/app`
- **Chat sidebar**: `mat-sidenav`
- **Chat history container**: `div.chat-history-scroll-container`
- **Individual chat items**: Elements within the history container
- **Conversation container**: `div.conversation-container`
- **User messages**: `div.user-query`
- **Assistant responses**: `div.model-response`

### Architecture Changes
```
chat_librarian/
├── __init__.py
├── main.py (updated with platform selection)
├── base_downloader.py (new - abstract base class)
├── chatgpt_downloader.py (renamed from downloader.py)
├── gemini_downloader.py (new)
└── utils.py (new - shared utilities)
```

This incremental approach ensures we can catch issues early and maintain a working state throughout development.
