#!/usr/bin/env python3
"""
Trending Content Generator
Generates viral "Would You Rather" questions based on:
1. Google Trends
2. Reddit trending topics
3. Current events
4. Seasonal/timely content
"""

import os
import json
import random
from datetime import datetime
from typing import List, Dict, Optional

# Try to import trending sources
try:
    from pytrends.request import TrendReq
    PYTRENDS_AVAILABLE = True
except ImportError:
    PYTRENDS_AVAILABLE = False
    print("⚠️ pytrends not installed. Google Trends disabled.")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class TrendingContentGenerator:
    """
    Generates viral, engaging "Would You Rather" questions
    based on current trends and proven viral formats.
    """
    
    # VIRAL question categories - designed to maximize engagement/comments
    VIRAL_CATEGORIES = {
        "money_vs_everything": {
            "weight": 25,  # Money topics always go viral
            "templates": [
                ("Get $10 million but you can never see your family again", "Stay with your family but struggle financially forever"),
                ("Win $1 million today", "Get $100 guaranteed every day for the rest of your life"),
                ("Be a billionaire but die at 50", "Live to 100 but always be middle class"),
                ("Have $50 million but everyone you know hates you", "Be broke but loved by everyone"),
                ("Never work again but live on $40k/year", "Work 60 hours/week but make $500k/year"),
                ("Inherit $5 million from a stranger", "Have your parents live 20 extra years"),
                ("Double your salary but lose your best friend", "Keep your friend but never get a raise"),
                ("Win the lottery but can never travel", "Stay average income but go anywhere free"),
            ],
            "variables": {}
        },
        "impossible_powers": {
            "weight": 20,
            "templates": [
                ("Read minds but everyone can read yours too", "Be invisible but only when alone"),
                ("Fly at walking speed", "Run at 200mph but can't stop for 10 minutes"),
                ("Pause time but you age while frozen", "Rewind time but lose all memories of that time"),
                ("Teleport anywhere but arrive naked", "Fly but only 3 feet off the ground"),
                ("See the future but can't change it", "Change the past but forget you did"),
                ("Be immune to all diseases but feel double the pain", "Never feel pain but get sick constantly"),
                ("Control fire but be freezing cold forever", "Control ice but be burning hot forever"),
            ],
            "variables": {}
        },
        "social_nightmare": {
            "weight": 20,
            "templates": [
                ("Everyone can see your screen at all times", "Everyone can hear your thoughts"),
                ("Your crush sees all your old posts about them", "Your boss sees everything you've said about work"),
                ("Your parents read all your DMs", "Your DMs get posted publicly every month"),
                ("Everyone knows your exact bank balance", "Everyone knows your search history"),
                ("Your Spotify gets broadcast wherever you go", "Your location is always visible to everyone"),
                ("Accidentally like your ex's old photo every week", "Auto-send your last screenshot to your boss"),
                ("Your Amazon purchases are public", "Your Netflix history is public"),
            ],
            "variables": {}
        },
        "relationship_chaos": {
            "weight": 18,
            "templates": [
                ("Know your partner is 'the one' but they don't feel the same", "Never know for sure but they're obsessed with you"),
                ("Date your celebrity crush but they're super boring", "Date someone average but they're your perfect match"),
                ("Have a perfect relationship that ends in 5 years", "Have a difficult relationship that lasts forever"),
                ("Know exactly when you'll meet your soulmate", "Meet them tomorrow but not know it's them"),
                ("Your ex becomes your boss", "Your boss becomes your ex"),
                ("Marry for money and eventually fall in love", "Marry for love and eventually go broke"),
                ("Have a partner who's brutally honest", "Have a partner who's always supportive but lies"),
            ],
            "variables": {}
        },
        "life_gamble": {
            "weight": 15,
            "templates": [
                ("Know exactly when you'll die", "Die randomly at any moment"),
                ("Live your dream life for 10 years then forget everything", "Live an average life but remember it all"),
                ("Be the smartest person alive but everyone finds you annoying", "Be average intelligence but everyone loves you"),
                ("Experience your happiest day every week", "Never feel sad again but also never feel extreme joy"),
                ("Everyone remembers you after you die", "No one remembers you but you live 50 extra years"),
                ("Redo your life from age 10 with current knowledge", "Skip to age 60 with guaranteed success"),
                ("Live in a perfect simulation forever", "Live in the real world for 10 more years"),
            ],
            "variables": {}
        },
        "gen_z_specific": {
            "weight": 15,
            "templates": [
                ("Go viral for something embarrassing", "Never have any social media presence"),
                ("Have 10 million followers but no real friends", "Have 5 close friends but no online presence"),
                ("Be permanently banned from TikTok", "Be permanently banned from YouTube"),
                ("Have unlimited Uber Eats but can't cook", "Be an amazing chef but no delivery apps exist"),
                ("Always have the latest tech but no one to share it with", "Outdated tech but always with friends"),
                ("Free Spotify Premium forever but only one playlist", "Free Netflix but only random shows"),
                ("Go back to flip phones forever", "Go back to dial-up internet forever"),
            ],
            "variables": {}
        },
        "dark_humor": {
            "weight": 7,
            "templates": [
                ("Know how your friends really feel about you", "Live happily in ignorance"),
                ("Have everyone you meet tell you one honest thing", "Never hear anything negative about yourself"),
                ("See exactly how you look to others", "See exactly how others see your personality"),
                ("Know every lie anyone tells you", "Be an undetectable liar yourself"),
                ("Know if someone is thinking about you right now", "Never know who's talking about you"),
            ],
            "variables": {}
        },
    }
    
    # Seasonal/timely content boosters
    SEASONAL_TOPICS = {
        1: ["New Year's resolutions", "winter", "gym", "fresh start"],
        2: ["Valentine's Day", "love", "relationships", "dating"],
        3: ["Spring", "March Madness", "St Patrick's"],
        4: ["Easter", "spring break", "taxes"],
        5: ["Mother's Day", "summer planning", "graduation"],
        6: ["Father's Day", "summer", "vacation"],
        7: ["Summer vacation", "beach", "4th of July"],
        8: ["Back to school", "summer ending"],
        9: ["Fall", "football season", "Labor Day"],
        10: ["Halloween", "fall vibes", "pumpkin spice"],
        11: ["Thanksgiving", "Black Friday", "gratitude"],
        12: ["Christmas", "holidays", "New Year's", "gifts", "family"],
    }
    
    def __init__(self):
        self.current_month = datetime.now().month
        self.pytrends = None
        if PYTRENDS_AVAILABLE:
            try:
                self.pytrends = TrendReq(hl='en-US', tz=360)
            except Exception as e:
                print(f"⚠️ PyTrends init failed: {e}")
    
    def get_google_trends(self) -> List[str]:
        """Fetch current Google Trends with retry logic."""
        if not self.pytrends:
            return self._get_fallback_trends()
        
        for attempt in range(3):
            try:
                trending = self.pytrends.trending_searches(pn='united_states')
                topics = trending[0].tolist()[:10]
                if topics:
                    print(f"✅ Got {len(topics)} Google Trends topics")
                    return topics
            except Exception as e:
                if attempt < 2:
                    import time
                    time.sleep(2)
                    continue
                print(f"⚠️ Google Trends failed after 3 attempts: {e}")
        
        return self._get_fallback_trends()
    
    def _get_fallback_trends(self) -> List[str]:
        """Get AI-generated 'trending' topics when real trends unavailable."""
        # Current events and evergreen viral topics
        return [
            "2024 trends", "viral challenges", "celebrity drama",
            "tech news", "money tips", "relationship advice",
            "social media", "gaming", "fitness goals", "AI technology"
        ]
    
    def get_reddit_trends(self) -> List[str]:
        """Fetch trending topics from Reddit with better handling."""
        if not REQUESTS_AVAILABLE:
            return []
        
        # Try multiple subreddits for viral content
        subreddits = [
            'r/WouldYouRather',  # Perfect for our format!
            'r/polls',
            'r/AskReddit', 
            'r/unpopularopinion'
        ]
        
        topics = []
        
        for subreddit in subreddits:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) QuizBot/2.0'
                }
                response = requests.get(
                    f'https://www.reddit.com/{subreddit}/hot.json?limit=10',
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    for post in data.get('data', {}).get('children', []):
                        title = post.get('data', {}).get('title', '')
                        if len(title) > 10 and len(title) < 200:
                            topics.append(title[:80])
                    
                    if topics:
                        print(f"✅ Got {len(topics)} topics from Reddit")
                        break  # Got enough
                        
            except Exception as e:
                continue  # Try next subreddit
        
        if not topics:
            print("⚠️ Reddit fetch failed, using fallback")
        
        return topics[:10]
    
    def generate_from_template(self, category: str) -> Dict:
        """Generate a question from a template."""
        cat_data = self.VIRAL_CATEGORIES.get(category, {})
        templates = cat_data.get("templates", [])
        variables = cat_data.get("variables", {})
        
        if not templates:
            return None
        
        template = random.choice(templates)
        option_a = template[0]
        option_b = template[1]
        
        # Replace variables
        for var_name, var_options in variables.items():
            placeholder = "{" + var_name + "}"
            if placeholder in option_a:
                option_a = option_a.replace(placeholder, random.choice(var_options))
            if placeholder in option_b:
                option_b = option_b.replace(placeholder, random.choice(var_options))
        
        # Generate realistic percentage (usually controversial splits)
        # Avoid 50/50 - more interesting to have slight leans
        percentage_a = random.choice([
            random.randint(35, 45),  # Lean B
            random.randint(55, 65),  # Lean A
            random.randint(25, 35),  # Strong B
            random.randint(65, 75),  # Strong A
        ])
        
        return {
            "option_a": option_a,
            "option_b": option_b,
            "percentage_a": percentage_a,
            "category": category,
            "generated_at": datetime.now().isoformat()
        }
    
    def generate_batch(self, count: int = 50) -> List[Dict]:
        """Generate a batch of viral questions."""
        print(f"🎯 Generating {count} viral questions...")
        
        questions = []
        
        # Calculate weighted selection
        categories = list(self.VIRAL_CATEGORIES.keys())
        weights = [self.VIRAL_CATEGORIES[c]["weight"] for c in categories]
        
        for i in range(count):
            # Select category based on weight
            category = random.choices(categories, weights=weights, k=1)[0]
            
            question = self.generate_from_template(category)
            if question:
                questions.append(question)
        
        # Shuffle to mix categories
        random.shuffle(questions)
        
        print(f"✅ Generated {len(questions)} questions")
        
        # Log category distribution
        cat_counts = {}
        for q in questions:
            cat = q.get("category", "unknown")
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
        print(f"📊 Distribution: {cat_counts}")
        
        return questions
    
    def generate_ai_enhanced_batch(self, count: int = 50) -> List[Dict]:
        """Generate questions using AI for extra creativity."""
        try:
            from multi_ai import MultiAIGenerator
            ai = MultiAIGenerator()
            
            print(f"🤖 Generating {count} AI-enhanced questions...")
            
            questions = []
            
            # Get trending context
            trends = self.get_google_trends()
            seasonal = self.SEASONAL_TOPICS.get(self.current_month, [])
            context = trends + seasonal
            
            system = """You are an expert at creating VIRAL "Would You Rather" questions for YouTube Shorts.

CRITICAL RULES:
1. Each option MUST be 5-12 words MAX (for voiceover)
2. Be controversial but appropriate
3. No obviously "correct" answer
4. Relatable to most people
5. Funny, shocking, or thought-provoking

EXAMPLES OF GOOD SHORT OPTIONS:
- "Have $10 million but no friends"
- "Be invisible but only when alone"
- "Know when you die but not how"

Return ONLY valid JSON: {"option_a": "SHORT 5-12 WORDS", "option_b": "SHORT 5-12 WORDS", "percentage_a": X}
Where X is 1-99 (avoid 50)"""

            prompts = [
                "Create a SHORT viral money dilemma. Options must be under 12 words each.",
                "Create a SHORT superpower question. Options must be under 12 words each.",
                "Create a SHORT embarrassing situation question. Under 12 words each option.",
                "Create a SHORT life tradeoff question. Under 12 words each option.",
                "Create a SHORT social media dilemma. Under 12 words each option.",
            ]
            
            for i in range(count):
                try:
                    prompt = random.choice(prompts)
                    result = ai.generate(prompt, system)
                    
                    if result:
                        # Clean and parse
                        clean = result.strip()
                        if clean.startswith("```"):
                            clean = clean.split("```")[1]
                            if clean.startswith("json"):
                                clean = clean[4:]
                        
                        question = json.loads(clean)
                        
                        # VALIDATE LENGTH - reject if too long
                        opt_a = question.get("option_a", "")
                        opt_b = question.get("option_b", "")
                        if len(opt_a) > 80 or len(opt_b) > 80:
                            print(f"   ⚠️ Question too long ({len(opt_a)}/{len(opt_b)} chars), using template")
                            fallback = self.generate_from_template(random.choice(list(self.VIRAL_CATEGORIES.keys())))
                            if fallback:
                                questions.append(fallback)
                            continue
                        
                        question["source"] = "ai"
                        question["generated_at"] = datetime.now().isoformat()
                        questions.append(question)
                        print(f"   ✅ Question {len(questions)}/{count}")
                except Exception as e:
                    print(f"   ⚠️ AI question failed: {e}")
                    # Fallback to template
                    fallback = self.generate_from_template(random.choice(list(self.VIRAL_CATEGORIES.keys())))
                    if fallback:
                        questions.append(fallback)
            
            print(f"✅ Generated {len(questions)} AI-enhanced questions")
            return questions
            
        except ImportError:
            print("⚠️ AI not available, using templates only")
            return self.generate_batch(count)
    
    def refresh_questions_file(self, count: int = 100, use_ai: bool = True):
        """Refresh the questions.json file with fresh content."""
        print(f"\n🔄 Refreshing questions file with {count} new questions...")
        
        questions = []
        
        if use_ai:
            # Try AI first (70% AI if available)
            ai_count = int(count * 0.7)
            ai_questions = self.generate_ai_enhanced_batch(ai_count)
            questions.extend(ai_questions)
            print(f"✅ Generated {len(ai_questions)} AI-enhanced questions")
        
        # ALWAYS add template questions as fallback/supplement
        needed = count - len(questions)
        if needed > 0:
            template_questions = self.generate_batch(needed)
            questions.extend(template_questions)
            print(f"✅ Added {len(template_questions)} template questions")
        
        # SAFETY CHECK: If still no questions, use hardcoded emergency fallbacks
        if len(questions) < 5:
            print("⚠️ Using emergency fallback questions...")
            questions.extend(self._emergency_fallback())
        
        # Shuffle final mix
        random.shuffle(questions)
        
        # Save to file
        output_path = "questions.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(questions, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved {len(questions)} questions to {output_path}")
        return questions
    
    def _emergency_fallback(self) -> List[Dict]:
        """Emergency fallback questions - NEVER fails."""
        return [
            {"option_a": "Have $1 million right now", "option_b": "Have $10 million in 10 years", "percentage_a": 62},
            {"option_a": "Be able to fly", "option_b": "Be able to teleport anywhere instantly", "percentage_a": 38},
            {"option_a": "Read everyone's mind", "option_b": "Be invisible whenever you want", "percentage_a": 45},
            {"option_a": "Live to 200 but alone", "option_b": "Live to 80 with the love of your life", "percentage_a": 23},
            {"option_a": "Have your browser history made public", "option_b": "Have all your texts made public", "percentage_a": 41},
            {"option_a": "Know how you die", "option_b": "Know when you die", "percentage_a": 55},
            {"option_a": "Have unlimited WiFi everywhere forever", "option_b": "Have unlimited phone battery forever", "percentage_a": 48},
            {"option_a": "Never need to sleep again", "option_b": "Never need to eat again", "percentage_a": 67},
            {"option_a": "Be famous but everyone hates you", "option_b": "Be unknown but loved by everyone you meet", "percentage_a": 28},
            {"option_a": "Only eat pizza for every meal", "option_b": "Never eat pizza again", "percentage_a": 35},
            {"option_a": "Have summer all year round", "option_b": "Have winter all year round", "percentage_a": 72},
            {"option_a": "Speak every language fluently", "option_b": "Talk to any animal", "percentage_a": 58},
            {"option_a": "Relive the same perfect day forever", "option_b": "Fast forward 10 years into the future", "percentage_a": 44},
            {"option_a": "Win $50,000 but lose all your friends", "option_b": "Keep friends but never win more than $100", "percentage_a": 31},
            {"option_a": "Be a millionaire but work 80 hours/week", "option_b": "Make $60k but work only 20 hours/week", "percentage_a": 39},
        ]


def main():
    """Generate fresh trending content."""
    import argparse
    parser = argparse.ArgumentParser(description="Generate trending WYR questions")
    parser.add_argument("count", type=int, nargs="?", default=100, help="Number of questions")
    parser.add_argument("--no-ai", action="store_true", help="Skip AI generation")
    
    args = parser.parse_args()
    
    generator = TrendingContentGenerator()
    generator.refresh_questions_file(count=args.count, use_ai=not args.no_ai)


if __name__ == "__main__":
    main()



