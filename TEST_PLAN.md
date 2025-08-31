# Multi-Platform Chat Librarian - Test Plan

## Overview
This test plan covers verification of both existing ChatGPT functionality (backward compatibility) and new Gemini platform support. Follow these steps to ensure all features work correctly.

## Prerequisites

### 1. Environment Setup
```bash
# Clone and navigate to the repository
git clone https://github.com/Christian-Blank/ai-chat-web-librarian.git
cd ai-chat-web-librarian

# Switch to the gemini branch
git checkout gemini

# Set up Python environment (requires Python 3.11+)
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -e .
playwright install
```

### 2. Account Requirements
- **ChatGPT Account**: Active OpenAI account with chat history
- **Gemini Account**: Active Google account with Gemini chat history
- Both accounts should have at least 2-3 conversations for testing

### 3. Browser Requirements
- Chrome browser installed (Playwright will use this)
- No existing Chrome instances running during testing

## Test Cases

### A. Backward Compatibility Tests (ChatGPT)

#### A1. Default ChatGPT Interactive Mode
```bash
chat-librarian select --first-run
```
**Expected Results:**
- [ ] Browser opens to https://chat.openai.com
- [ ] Login process works (first time)
- [ ] Chat history loads and displays in a table
- [ ] Can select a chat by number
- [ ] Chat downloads successfully to `ChatGPT_Downloads/[chat-title].md`
- [ ] Generated markdown file contains properly formatted conversation

#### A2. ChatGPT Quick Download (Last Chat)
```bash
chat-librarian last --first-run
```
**Expected Results:**
- [ ] Downloads most recent ChatGPT conversation automatically
- [ ] No interactive selection required
- [ ] File saved to `ChatGPT_Downloads/`

#### A3. ChatGPT Download by Title
```bash
chat-librarian title "Your Exact Chat Title Here" --first-run
```
**Expected Results:**
- [ ] Finds and downloads the specified chat
- [ ] Case-insensitive matching works
- [ ] Error message if chat title not found

#### A4. Explicit ChatGPT Platform Selection
```bash
chat-librarian select --platform chatgpt --first-run
```
**Expected Results:**
- [ ] Behaves identically to A1 (no platform flag)
- [ ] Confirms backward compatibility maintained

### B. New Gemini Platform Tests

#### B1. Gemini Interactive Mode
```bash
chat-librarian select --platform gemini --first-run
```
**Expected Results:**
- [ ] Browser opens to https://gemini.google.com/app
- [ ] Google login process works (first time)
- [ ] Gemini chat history loads and displays in a table
- [ ] Can select a chat by number
- [ ] Chat downloads successfully to `Gemini_Downloads/[chat-title].md`
- [ ] Generated markdown file contains properly formatted conversation

#### B2. Gemini Quick Download (Last Chat)
```bash
chat-librarian last --platform gemini --first-run
```
**Expected Results:**
- [ ] Downloads most recent Gemini conversation automatically
- [ ] File saved to `Gemini_Downloads/`

#### B3. Gemini Download by Title
```bash
chat-librarian title "Your Gemini Chat Title" --platform gemini --first-run
```
**Expected Results:**
- [ ] Finds and downloads the specified Gemini chat
- [ ] Case-insensitive matching works
- [ ] Error message if chat title not found

### C. Session Persistence Tests

#### C1. ChatGPT Session Persistence
```bash
# First run (should require login)
chat-librarian select --first-run

# Second run (should use saved session)
chat-librarian select
```
**Expected Results:**
- [ ] First run opens visible browser for login
- [ ] Second run works without login (uses saved session)
- [ ] Separate user data stored in `~/.chat_scraper_data/chatgpt_data/`

#### C2. Gemini Session Persistence
```bash
# First run (should require login)
chat-librarian select --platform gemini --first-run

# Second run (should use saved session)
chat-librarian select --platform gemini
```
**Expected Results:**
- [ ] First run opens visible browser for login
- [ ] Second run works without login (uses saved session)
- [ ] Separate user data stored in `~/.chat_scraper_data/gemini_data/`

### D. Output Format Verification

#### D1. ChatGPT Markdown Quality
**Check downloaded ChatGPT file contains:**
- [ ] Proper heading with chat title
- [ ] User messages clearly marked with `### User`
- [ ] Assistant messages clearly marked with `### Assistant`
- [ ] Code blocks properly formatted with language detection
- [ ] Lists and formatting preserved
- [ ] Separators (`---`) between messages

#### D2. Gemini Markdown Quality
**Check downloaded Gemini file contains:**
- [ ] Proper heading with chat title
- [ ] User messages clearly marked with `### User`
- [ ] Assistant messages clearly marked with `### Assistant`
- [ ] Clean text without HTML artifacts
- [ ] Separators (`---`) between messages

### E. Error Handling Tests

#### E1. Invalid Platform
```bash
chat-librarian select --platform invalid
```
**Expected Results:**
- [ ] Clear error message: "Unsupported platform: invalid. Supported: chatgpt, gemini"
- [ ] Application exits gracefully

#### E2. Nonexistent Chat Title
```bash
chat-librarian title "This Chat Does Not Exist" --platform chatgpt --first-run
```
**Expected Results:**
- [ ] Clear error message about chat not found
- [ ] Application exits gracefully

#### E3. Network/Browser Issues
**Simulate by closing browser during operation:**
- [ ] Application handles browser closure gracefully
- [ ] Clear error messages displayed
- [ ] No crashes or hanging processes

### F. CLI Help and Documentation

#### F1. Main Help
```bash
chat-librarian --help
```
**Expected Results:**
- [ ] Shows all available commands
- [ ] Mentions both ChatGPT and Gemini support

#### F2. Command-Specific Help
```bash
chat-librarian select --help
chat-librarian last --help
chat-librarian title --help
```
**Expected Results:**
- [ ] Each shows `--platform` option
- [ ] Clear descriptions of chatgpt/gemini options
- [ ] Examples of usage

## Quick Smoke Test

For a rapid verification, run this minimal test sequence:

```bash
# Test backward compatibility
chat-librarian last --first-run
ls ChatGPT_Downloads/

# Test new Gemini support  
chat-librarian last --platform gemini --first-run
ls Gemini_Downloads/

# Verify both created markdown files
```

## Test Environment Cleanup

After testing, clean up test files:
```bash
rm -rf ChatGPT_Downloads/ Gemini_Downloads/
rm -rf ~/.chat_scraper_data/
```

## Success Criteria

✅ **All tests pass**: Every checkbox above should be checked  
✅ **No regressions**: All existing ChatGPT functionality works identically  
✅ **New functionality**: Gemini platform works as documented  
✅ **Clean separation**: Separate user data and download directories  
✅ **Error handling**: Graceful handling of invalid inputs and network issues  

## Troubleshooting

### Common Issues
1. **Browser hangs**: Close all Chrome instances and retry
2. **Permission errors**: Ensure write permissions in current directory
3. **Network timeouts**: Check internet connection and platform availability
4. **Login loops**: Clear browser data and retry with `--first-run`

### Debug Mode
For verbose output during testing:
```bash
# Run with Python for detailed error messages
python -m chat_librarian.main select --platform gemini --first-run
