# ViralShortsFactory Project - Full Context

**Note**: Folder name is `YShortsGen`, but project name is **ViralShortsFactory**

This document contains the complete project context from our previous conversation.

## Project Overview

**ViralShortsFactory** (folder: YShortsGen) is an AI-powered YouTube Shorts generator that:
- Discovers viral topics from Reddit, Google Trends, YouTube Trending
- Generates engaging scripts (45-60 seconds)
- Creates videos with text overlays, TTS narration, and dynamic visuals
- Automatically uploads to YouTube with optimized metadata
- Runs autonomously with scheduled daily generation (3 videos/day)
- Uses 100% free tools (Groq, Gemini, Reddit API, Google TTS, etc.)

## Conversation Summary

- **Total Messages**: 279
- **Total AI Responses**: 50
- **Full conversation history**: See `recovered_chat_complete.json`

## Last Major Work Done

### 1. Video Quality Enhancements
- **Flaw Detection System**: Implemented detection for awkward phrases in generated videos
  - Example issue: "you are losing 3333 dollars every year" (awkward specific numbers)
  - Created generic master prompts for AI agents to detect and prevent such issues
  - Focus on making videos feel less AI-generated

### 2. Comprehensive Project Improvements
The last major request was to "do ALL" improvements with these requirements:
- ✅ All changes via generic master prompts (no hardcoding)
- ✅ Quota management (Groq, Gemini tokens, QLog)
- ✅ Only fully free tools (no trials, no credit cards)
- ✅ Integration with production workflows
- ✅ Analytics feedback updates (weekly and monthly)
- ✅ Proper local testing
- ✅ Self-review and bug fixes
- ✅ Research other Gemini models if helpful
- ✅ Ensure project prompts are "god-like level" and generic
- ✅ No quota waste
- ✅ Dashboard reflects everything
- ✅ Workflow validation and persistence

### 3. Key Principles
- **Quality over speed**: "development time is the least of my concerns, quality isn't!"
- **Generic prompts only**: Everything should use AI agents with master prompts
- **No hardcoding**: Hybrid solutions only if better than generic prompts
- **Full integration**: All changes must integrate with production workflows

## Project Structure

```
YShortsGen/
├── core/                    # Core application logic
│   ├── config.py
│   ├── database.py
│   ├── topic_discovery.py
│   ├── content_generator.py
│   ├── video_creator.py
│   ├── youtube_uploader.py
│   ├── scheduler.py
│   └── ...
├── web/                     # Web UI
│   ├── web_ui.py
│   └── templates/
├── main.py                  # Main entry point
└── ...
```

## How to Continue

When you open the new chat "Project Continuation - YShortsGen", you can:

1. **Ask**: "What was the last thing you did?" 
   - I'll reference the flaw detection and comprehensive improvements work

2. **Ask**: "What's the current state of the project?"
   - I'll check the codebase and tell you what's implemented

3. **Ask**: "Continue from where we left off"
   - I'll review recent changes and continue development

4. **Ask**: "What needs to be done next?"
   - I'll check what was requested but not yet completed

## Important Notes

- Full conversation history (279 messages) is preserved in `recovered_chat_complete.json`
- Last 50 messages are loaded in the chat for immediate context
- All project files are in the codebase and can be analyzed
- The project uses only free tools and generic AI prompts

## Next Steps

1. Open the chat "Project Continuation - YShortsGen" in Cursor
2. Ask me what was last done
3. We'll continue developing from there!
