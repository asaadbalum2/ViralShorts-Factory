"""
Create a readable HTML viewer for your chat so you can access it even if Cursor won't open it
"""
import json
from pathlib import Path
from datetime import datetime

RECOVERED_CHAT_FILE = Path("./recovered_chat_complete.json")

def create_viewer():
    """Create an HTML viewer for the chat"""
    if not RECOVERED_CHAT_FILE.exists():
        print("[ERROR] recovered_chat_complete.json not found")
        return False
    
    print("=" * 60)
    print("Creating Readable Chat Viewer")
    print("=" * 60)
    
    # Load data
    with open(RECOVERED_CHAT_FILE, 'r', encoding='utf-8') as f:
        recovered_data = json.load(f)
    
    prompts = []
    generations = []
    
    for entry in recovered_data:
        key = entry.get('key')
        data = entry.get('data')
        
        if key == 'aiService.prompts' and isinstance(data, list):
            prompts = data
        elif key == 'aiService.generations' and isinstance(data, list):
            generations = data
    
    # Create HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Recurring stuck issue - Chat Viewer</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #1e1e1e;
            color: #d4d4d4;
        }}
        h1 {{
            color: #4ec9b0;
            border-bottom: 2px solid #4ec9b0;
            padding-bottom: 10px;
        }}
        .message {{
            margin: 20px 0;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid;
        }}
        .user {{
            background: #264f78;
            border-color: #4ec9b0;
        }}
        .assistant {{
            background: #37373d;
            border-color: #ce9178;
        }}
        .message-header {{
            font-weight: bold;
            margin-bottom: 10px;
            color: #4ec9b0;
        }}
        .message-content {{
            white-space: pre-wrap;
            line-height: 1.6;
        }}
        .timestamp {{
            font-size: 0.85em;
            color: #858585;
            margin-top: 10px;
        }}
        .stats {{
            background: #2d2d30;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
    </style>
</head>
<body>
    <h1>Recurring stuck issue - Complete Chat History</h1>
    
    <div class="stats">
        <strong>Total Messages:</strong> {len(prompts)} prompts + {len(generations)} AI responses = {len(prompts) + len(generations)} total messages
        <br><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </div>
"""
    
    # Add messages
    prompt_idx = 0
    gen_idx = 0
    
    # Try to match prompts with generations by timestamp or order
    for i in range(max(len(prompts), len(generations))):
        # Add user prompt
        if prompt_idx < len(prompts):
            prompt = prompts[prompt_idx]
            text = prompt.get('text', '') if isinstance(prompt, dict) else str(prompt)
            html += f"""
    <div class="message user">
        <div class="message-header">You (Prompt {prompt_idx + 1})</div>
        <div class="message-content">{text[:5000]}</div>
    </div>
"""
            prompt_idx += 1
        
        # Add AI response
        if gen_idx < len(generations):
            gen = generations[gen_idx]
            text = gen.get('textDescription', '') if isinstance(gen, dict) else str(gen)
            timestamp = gen.get('unixMs', 0) if isinstance(gen, dict) else None
            time_str = ""
            if timestamp:
                try:
                    dt = datetime.fromtimestamp(timestamp / 1000)
                    time_str = f'<div class="timestamp">{dt.strftime("%Y-%m-%d %H:%M:%S")}</div>'
                except:
                    pass
            
            html += f"""
    <div class="message assistant">
        <div class="message-header">AI Assistant (Response {gen_idx + 1})</div>
        <div class="message-content">{text[:10000]}</div>
        {time_str}
    </div>
"""
            gen_idx += 1
    
    html += """
</body>
</html>
"""
    
    # Save
    output_file = Path("./chat_viewer.html")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n[SUCCESS] Created: {output_file}")
    print(f"\nYou can now:")
    print(f"  1. Open {output_file} in any web browser")
    print(f"  2. View all {len(prompts)} prompts and {len(generations)} responses")
    print(f"  3. Search, scroll, and read your complete conversation")
    print(f"\nThis works even if Cursor won't open the chat!")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    create_viewer()















