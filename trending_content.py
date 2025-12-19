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
    
    # Proven viral question categories
    VIRAL_CATEGORIES = {
        "money_dilemma": {
            "weight": 20,  # Higher weight = more likely to be selected
            "templates": [
                ("Have ${low_amount} right now", "Have ${high_amount} in {years} years"),
                ("Win ${amount} but lose all your friends", "Keep your friends but never win more than $100"),
                ("Be a millionaire but work 80 hours a week", "Make ${medium} but work 20 hours a week"),
                ("Get ${amount} every month for life", "Get ${lump_sum} one time only"),
                ("Have unlimited money but no one can know", "Have ${modest} but everyone thinks you're rich"),
            ],
            "variables": {
                "low_amount": ["1 million", "500,000", "100,000"],
                "high_amount": ["10 million", "50 million", "100 million"],
                "medium": ["75,000/year", "50,000/year", "60,000/year"],
                "amount": ["10,000", "5,000", "25,000"],
                "lump_sum": ["1 million", "2 million", "500,000"],
                "modest": ["100,000/year", "80,000/year"],
                "years": ["10", "5", "20"],
            }
        },
        "superpower": {
            "weight": 15,
            "templates": [
                ("Be able to fly", "Be able to teleport anywhere instantly"),
                ("Read everyone's mind", "Be invisible whenever you want"),
                ("Have super strength", "Have super speed"),
                ("Control time", "Control weather"),
                ("Never need to sleep", "Never need to eat"),
                ("Speak every language fluently", "Talk to any animal"),
                ("Have perfect memory", "Be able to forget anything instantly"),
            ],
            "variables": {}
        },
        "life_tradeoff": {
            "weight": 18,
            "templates": [
                ("Live to 200 but alone", "Live to 80 with the love of your life"),
                ("Know how you die", "Know when you die"),
                ("Relive the same day forever", "Fast forward 10 years"),
                ("Never feel physical pain", "Never feel emotional pain"),
                ("Be famous but everyone hates you", "Be unknown but everyone who meets you loves you"),
                ("Live in the past with modern knowledge", "Live in the future knowing nothing"),
            ],
            "variables": {}
        },
        "embarrassing": {
            "weight": 15,
            "templates": [
                ("Have your browser history made public", "Have all your texts made public"),
                ("Accidentally send a mean text to that person", "Trip in front of your crush every day"),
                ("Always have food in your teeth", "Always have your fly down"),
                ("Burp loudly during every silence", "Fart silently in every elevator"),
                ("Have everyone see your camera roll", "Have everyone hear your Spotify history"),
            ],
            "variables": {}
        },
        "tech_modern": {
            "weight": 12,
            "templates": [
                ("Have unlimited WiFi everywhere forever", "Have unlimited phone battery forever"),
                ("Only use TikTok for the rest of your life", "Only use Instagram for the rest of your life"),
                ("Have the latest iPhone forever", "Have $5000 cash"),
                ("Delete all your social media", "Delete all your photos"),
                ("Have AI do all your work", "Have AI plan all your meals and exercise"),
            ],
            "variables": {}
        },
        "relationship": {
            "weight": 15,
            "templates": [
                ("Find your soulmate but they live across the world", "Marry someone okay who lives next door"),
                ("Have 100 friends but no best friend", "Have 1 best friend but no other friends"),
                ("Date someone 10 years older", "Date someone 10 years younger"),
                ("Know if your partner is 'the one' on day one", "Never know until you break up"),
            ],
            "variables": {}
        },
        "extreme_choice": {
            "weight": 5,
            "templates": [
                ("Only eat pizza for every meal", "Never eat pizza again"),
                ("Only watch one movie for the rest of your life", "Never watch movies again"),
                ("Give up music forever", "Give up TV/movies forever"),
                ("Have summer all year", "Have winter all year"),
                ("Only wear one color forever", "Wear a different random outfit every day"),
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
        """Fetch current Google Trends."""
        if not self.pytrends:
            return []
        
        try:
            trending = self.pytrends.trending_searches(pn='united_states')
            return trending[0].tolist()[:10]
        except Exception as e:
            print(f"⚠️ Google Trends fetch failed: {e}")
            return []
    
    def get_reddit_trends(self) -> List[str]:
        """Fetch trending topics from Reddit."""
        if not REQUESTS_AVAILABLE:
            return []
        
        try:
            headers = {'User-Agent': 'QuizBot/1.0'}
            # Get hot posts from r/all
            response = requests.get(
                'https://www.reddit.com/r/all/hot.json?limit=20',
                headers=headers,
                timeout=10
            )
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            topics = []
            
            for post in data.get('data', {}).get('children', []):
                title = post.get('data', {}).get('title', '')
                # Extract key words
                if len(title) > 10:
                    topics.append(title[:50])
            
            return topics[:10]
        except Exception as e:
            print(f"⚠️ Reddit fetch failed: {e}")
            return []
    
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
Your questions MUST:
1. Be controversial but appropriate
2. Make people THINK and DEBATE
3. Have no obviously "correct" answer
4. Be relatable to most people
5. Create emotional response (funny, shocking, or thought-provoking)

Return ONLY valid JSON: {"option_a": "...", "option_b": "...", "percentage_a": X}
Where X is 1-99 (avoid 50 - make it interesting like 35 or 67)"""

            prompts = [
                f"Create a viral money/wealth dilemma question. Current trending: {random.choice(context) if context else 'money'}",
                f"Create a viral superpower question that makes people debate.",
                f"Create a viral embarrassing situation question that's relatable.",
                f"Create a viral life tradeoff question about relationships or time.",
                f"Create a viral question about modern technology or social media.",
                f"Create a controversial but appropriate question about daily life choices.",
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



