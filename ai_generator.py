#!/usr/bin/env python3
"""
AI-Powered Question Generator using Groq (FREE LLM API)
Generates viral "Would You Rather" questions using AI
"""

import os
import json
import random
from typing import List, Dict, Optional

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False


def get_groq_client():
    """Get Groq client if available."""
    api_key = os.environ.get('GROQ_API_KEY')
    if not api_key or not GROQ_AVAILABLE:
        return None
    return Groq(api_key=api_key)


def generate_viral_questions(count: int = 10, category: str = "general") -> List[Dict]:
    """
    Use Groq AI to generate viral Would You Rather questions.
    
    Categories: general, money, superpowers, social, tech, life
    """
    client = get_groq_client()
    
    if not client:
        print("⚠️ Groq not available. Using fallback questions.")
        return []
    
    category_prompts = {
        "general": "diverse and thought-provoking",
        "money": "about wealth, success, and financial decisions",
        "superpowers": "about supernatural abilities and powers",
        "social": "about relationships, fame, and social situations",
        "tech": "about technology, AI, and the future",
        "life": "about life choices, career, and personal growth"
    }
    
    category_desc = category_prompts.get(category, category_prompts["general"])
    
    prompt = f"""You are an expert at creating viral "Would You Rather" questions for YouTube Shorts.

Generate {count} "Would You Rather" questions that are {category_desc}.

Requirements for VIRAL questions (based on data analysis):
1. Both options must be genuinely difficult to choose between (50/50 split)
2. Options should trigger emotional response or deep thinking
3. Questions should be relatable to a wide audience
4. Include some with surprising/counterintuitive elements
5. Make them conversation starters that people want to share
6. Avoid controversial political/religious topics
7. Each option should be 5-15 words for readability

For each question, also estimate what percentage would choose option A (be realistic, 30-70 range).

Return ONLY valid JSON array (no markdown):
[
  {{"option_a": "...", "option_b": "...", "percentage_a": 45}},
  {{"option_a": "...", "option_b": "...", "percentage_a": 52}}
]"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a viral content expert. Return ONLY valid JSON, no markdown."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.9,
            max_tokens=2000
        )
        
        content = response.choices[0].message.content.strip()
        
        # Clean up response
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        
        questions = json.loads(content)
        
        print(f"✅ Generated {len(questions)} AI questions!")
        return questions
        
    except Exception as e:
        print(f"❌ AI generation failed: {e}")
        return []


def generate_trending_questions() -> List[Dict]:
    """Generate questions based on current trends."""
    client = get_groq_client()
    
    if not client:
        return []
    
    prompt = """Generate 5 "Would You Rather" questions based on CURRENT 2024-2025 trends:
- AI and technology
- Work from home vs office
- Social media and influencers
- Climate and environment
- Gaming and entertainment

Make them relevant to what young people (18-35) are talking about NOW.

Return ONLY valid JSON array:
[{"option_a": "...", "option_b": "...", "percentage_a": 50}]"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Return ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=1500
        )
        
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        
        return json.loads(content)
        
    except Exception as e:
        print(f"❌ Trending generation failed: {e}")
        return []


def refresh_questions_file(output_path: str = "questions.json", count: int = 50):
    """
    Refresh the questions.json file with AI-generated questions.
    Mixes categories for variety.
    """
    print("🤖 Generating fresh AI questions...")
    
    all_questions = []
    
    # Generate from different categories
    categories = ["general", "money", "superpowers", "social", "tech", "life"]
    per_category = max(5, count // len(categories))
    
    for category in categories:
        questions = generate_viral_questions(per_category, category)
        all_questions.extend(questions)
        
    # Add trending questions
    trending = generate_trending_questions()
    all_questions.extend(trending)
    
    # Shuffle for variety
    random.shuffle(all_questions)
    
    # Take requested count
    all_questions = all_questions[:count]
    
    if all_questions:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_questions, f, indent=2)
        print(f"✅ Saved {len(all_questions)} questions to {output_path}")
    else:
        print("⚠️ No AI questions generated. Keeping existing file.")
    
    return all_questions


if __name__ == "__main__":
    import sys
    
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    questions = refresh_questions_file(count=count)
    
    print(f"\n📊 Sample questions generated:")
    for q in questions[:3]:
        print(f"  • {q['option_a']} OR {q['option_b']}?")



