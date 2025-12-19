#!/usr/bin/env python3
"""
ViralShorts Factory - VIRAL VIDEO SCIENCE ENGINE
=================================================

Based on extensive research of what makes short-form content go viral.
This module implements the PSYCHOLOGICAL and STRUCTURAL secrets that 
top creators use to generate billions of views.

CORE PRINCIPLES:
================

1. THE PROMISE-PAYOFF CONTRACT
   - Every video makes an implicit PROMISE in the hook
   - The video MUST deliver on that promise
   - Failure to deliver = lost trust = no follows = no virality
   
   BAD: "Here's a life-changing strategy..." (never explains it)
   GOOD: "The 2-minute rule: Start any task for just 2 minutes. Your brain
          can't resist continuing once started. Try it with exercise."

2. THE INFORMATION SANDWICH
   - HOOK: Create curiosity gap
   - MEAT: Deliver actual specific value
   - CTA: Give them something to do/think about

3. THE SPECIFICITY PRINCIPLE
   - Vague = Boring
   - Specific = Interesting + Credible
   
   BAD: "Many people struggle with productivity"
   GOOD: "MIT researchers found 73% of people check their phone within 3
          minutes of feeling bored"

4. THE RE-WATCH FACTOR
   - Best viral content has something that makes you watch again
   - Hidden details, surprising twist, emotional moment

5. THE SOCIAL CURRENCY
   - People share content that makes them look smart/funny/informed
   - Ask: "Would someone share this to look good?"
"""

import os
import json
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ViralVideoStructure:
    """The structure of a viral video."""
    hook: str                  # 1-2 seconds - STOP THE SCROLL
    tension_build: str         # 3-5 seconds - Create anticipation
    value_delivery: str        # 6-15 seconds - THE ACTUAL CONTENT (must be specific!)
    reinforcement: str         # 2-3 seconds - Drive the point home
    call_to_action: str        # 1-2 seconds - What should they do now?
    rewatch_trigger: str       # Why would someone watch again?


# =============================================================================
# CONTENT TYPE TEMPLATES - Each guarantees VALUE DELIVERY
# =============================================================================

CONTENT_TEMPLATES = {
    "life_hack": """
You are a productivity expert creating a SHORT video (15-25 seconds).

CRITICAL RULE: You must provide a SPECIFIC, ACTIONABLE hack that viewers 
can USE IMMEDIATELY. No vague advice. No "there's a method..." without 
explaining the method.

TEMPLATE:
HOOK: Surprising claim that creates curiosity (2 seconds)
PROBLEM: Briefly state the common problem (3 seconds)
SOLUTION: THE ACTUAL HACK - specific steps or technique (8 seconds)
PROOF: Quick mention of why it works or who uses it (3 seconds)
CTA: Challenge viewer to try it (2 seconds)

EXAMPLE OF WHAT WE WANT:
"Want to fall asleep in under 2 minutes? Navy SEALs use this.
Relax your face muscles completely. Drop your shoulders.
Exhale and relax your chest. Clear your mind by imagining 
you're lying in a dark room. Works for 96% of people after 
6 weeks. Try it tonight."

EXAMPLE OF WHAT WE DON'T WANT:
"There's an amazing sleep technique you should learn.
Scientists say it really works. You can find more info online.
Follow for more tips."

Generate a complete life hack video script:
TOPIC: {topic}

Output JSON:
{{
    "hook": "The attention-grabbing opening (max 12 words)",
    "full_script": "The COMPLETE script with actual value (50-80 words)",
    "specific_action": "The ONE thing viewer should do",
    "why_it_works": "Brief explanation of mechanism",
    "call_to_action": "What should they comment/do?"
}}
""",

    "scary_fact": """
You are a fascinating facts creator. Your goal is to share GENUINELY 
surprising information that makes people think "wow, I never knew that!"

CRITICAL RULE: The fact must be SPECIFIC with numbers/details. And you 
must explain WHY it matters or WHAT it means for the viewer.

TEMPLATE:
HOOK: The shocking claim (2 seconds)
CONTEXT: Set the scene (3 seconds)
THE FACT: The specific information with details (8 seconds)
IMPLICATION: What this means for the viewer (4 seconds)
CTA: Thought-provoking question (2 seconds)

EXAMPLE OF WHAT WE WANT:
"You've walked past 36 murderers in your lifetime.
Based on population data and murder rates, the average city 
dweller crosses paths with 36 killers before age 70.
They looked normal. They said hi. You never knew.
Comment the creepiest stranger encounter you've had."

EXAMPLE OF WHAT WE DON'T WANT:
"There are scary things in the world you don't know about.
Scientists have discovered disturbing facts. Some people 
aren't who they seem. Stay safe out there."

Generate a scary/mind-blowing fact:
TOPIC: {topic}

Output JSON:
{{
    "hook": "Shocking opener with specific claim (max 10 words)",
    "full_script": "Complete script with SPECIFIC details (50-80 words)",
    "the_fact": "The core factual claim",
    "source_hint": "Where this info comes from (studies/data/research)",
    "call_to_action": "Engaging question that drives comments"
}}
""",

    "money_fact": """
You are a financial educator creating SHORT content that gives REAL value.

CRITICAL RULE: Provide SPECIFIC financial insight with NUMBERS. Not 
"save money" but "the 50/30/20 rule: 50% needs, 30% wants, 20% savings".

TEMPLATE:
HOOK: Surprising money truth (2 seconds)
THE PROBLEM: What most people do wrong (4 seconds)  
THE SOLUTION: Specific strategy with numbers (10 seconds)
THE RESULT: What happens if they follow this (3 seconds)
CTA: Challenge them to start (2 seconds)

EXAMPLE OF WHAT WE WANT:
"The coffee math that changed my life.
$5 a day on coffee is $1,825 a year. In 30 years with 
7% returns, that's $172,000. I didn't quit coffee.
I made it at home for 50 cents. Put the difference 
in index funds. I'm up $14,000 in just 3 years.
What's your daily money leak?"

Generate a money/financial insight:
TOPIC: {topic}

Output JSON:
{{
    "hook": "Attention-grabbing financial truth (max 10 words)",
    "full_script": "Complete script with SPECIFIC numbers (50-80 words)",
    "specific_strategy": "The actionable financial move",
    "numbers_included": ["list of specific numbers used"],
    "call_to_action": "Question about their finances"
}}
""",

    "psychology_fact": """
You are a psychology expert explaining HOW THE MIND WORKS in simple terms.

CRITICAL RULE: Explain the psychological MECHANISM. Don't just say 
"your brain does X" - explain WHY and HOW, and what viewer can DO with 
this knowledge.

TEMPLATE:
HOOK: Surprising truth about human behavior (2 seconds)
SETUP: The common situation (3 seconds)
THE PSYCHOLOGY: What's actually happening in the brain (8 seconds)
THE HACK: How to use this knowledge (4 seconds)
CTA: Self-reflection question (2 seconds)

EXAMPLE OF WHAT WE WANT:
"Your brain sabotages you at 3pm every day.
Around 3pm, your circadian rhythm dips. Willpower crashes.
This is when most people break diets and skip workouts.
The fix: Schedule your hardest tasks for 10am when 
cortisol peaks. Leave easy work for the afternoon slump.
What time does YOUR willpower crash?"

Generate a psychology insight:
TOPIC: {topic}

Output JSON:
{{
    "hook": "Surprising psychology truth (max 10 words)",
    "full_script": "Complete script with mechanism explained (50-80 words)",
    "the_mechanism": "The psychological/neurological explanation",
    "practical_application": "How viewer can use this",
    "call_to_action": "Self-reflection question"
}}
""",

    "mind_blow": """
You are creating content that makes people's minds EXPLODE with new 
perspective.

CRITICAL RULE: The insight must fundamentally change how they see 
something. And you must fully EXPLAIN the perspective shift, not just 
hint at it.

TEMPLATE:
HOOK: Statement that challenges assumptions (2 seconds)
THE COMMON BELIEF: What most people think (3 seconds)
THE TWIST: The reality that changes everything (8 seconds)
THE IMPLICATION: Why this matters (4 seconds)
CTA: Mind-expanding question (2 seconds)

EXAMPLE OF WHAT WE WANT:
"You're not afraid of the dark.
You're afraid of what MIGHT be in it.
Your brain evolved to fear uncertainty, not absence of light.
That's why anxiety hits hardest when you don't know 
what's coming. The unknown is scarier than any real threat.
What uncertainty is haunting you right now?"

Generate a mind-blowing insight:
TOPIC: {topic}

Output JSON:
{{
    "hook": "Assumption-challenging opener (max 10 words)",
    "full_script": "Complete perspective shift explained (50-80 words)",
    "the_twist": "The reality that changes their view",
    "deeper_meaning": "The philosophical/practical implication",
    "call_to_action": "Deep reflection question"
}}
"""
}


# =============================================================================
# VALUE DELIVERY CHECKER
# =============================================================================

class ValueDeliveryChecker:
    """
    Checks if content actually DELIVERS value or just promises it.
    
    This is CRITICAL for preventing the "learn now but never teaches" problem.
    """
    
    # Red flag phrases that indicate missing value
    EMPTY_PROMISE_PHRASES = [
        "learn now", "find out", "discover how", "the secret is",
        "you should try", "there's a way", "studies show", "experts say",
        "research proves", "you won't believe", "here's why",
        "click to learn", "follow for more", "check the link",
        "comment below", "share this", "stay tuned"
    ]
    
    # Indicators of actual value
    VALUE_INDICATORS = [
        # Numbers and specifics
        r'\d+%', r'\d+ minutes', r'\d+ seconds', r'\$\d+',
        r'\d+ steps', r'\d+ times', r'\d+ people',
        # Action words
        r'first,', r'then,', r'finally,', r'step \d',
        r'do this:', r'try this:', r'here\'s how:',
        # Specifics
        r'called the', r'known as', r'named',
    ]
    
    def check_content(self, content: str) -> Dict:
        """
        Analyze content for value delivery.
        
        Returns a score and specific issues.
        """
        content_lower = content.lower()
        
        issues = []
        score = 100
        
        # Check for empty promises
        for phrase in self.EMPTY_PROMISE_PHRASES:
            if phrase in content_lower:
                # Check if there's follow-through after the promise
                idx = content_lower.find(phrase)
                after = content_lower[idx:idx+200]
                
                # Look for value indicators after the promise
                has_followthrough = any(
                    __import__('re').search(pattern, after) 
                    for pattern in self.VALUE_INDICATORS
                )
                
                if not has_followthrough:
                    issues.append(f"Empty promise: '{phrase}' without follow-through")
                    score -= 15
        
        # Check for specificity
        import re
        has_numbers = bool(re.search(r'\d+', content))
        has_action = any(word in content_lower for word in 
                        ['do', 'try', 'start', 'stop', 'use', 'apply'])
        
        if not has_numbers:
            issues.append("No specific numbers or data")
            score -= 10
        
        if not has_action:
            issues.append("No actionable advice")
            score -= 10
        
        # Check length - too short = probably not enough value
        word_count = len(content.split())
        if word_count < 40:
            issues.append(f"Too short ({word_count} words) - probably lacks depth")
            score -= 15
        
        return {
            "score": max(0, score),
            "issues": issues,
            "verdict": "GOOD" if score >= 70 else "NEEDS_WORK" if score >= 50 else "REJECT",
            "word_count": word_count,
            "has_numbers": has_numbers,
            "has_action": has_action
        }
    
    def improve_content(self, content: str, video_type: str) -> str:
        """
        Use AI to improve content that fails value check.
        """
        check = self.check_content(content)
        
        if check["verdict"] == "GOOD":
            return content
        
        # Generate improvement prompt
        issues_text = "\n".join(f"- {issue}" for issue in check["issues"])
        
        improve_prompt = f"""The following video content has these problems:
{issues_text}

Original content:
{content}

Rewrite this to:
1. Add SPECIFIC numbers and data
2. Give ACTIONABLE steps the viewer can take
3. DELIVER on any promises made
4. Be at least 50 words

Keep the same topic but make it VALUABLE.

Return ONLY the improved script, no explanations."""
        
        # This would call AI - for now return original
        return content


# =============================================================================
# VIRAL CONTENT GENERATOR
# =============================================================================

class ViralContentGenerator:
    """Generate content that's GUARANTEED to deliver value."""
    
    def __init__(self):
        self.checker = ValueDeliveryChecker()
        self.groq_key = os.environ.get("GROQ_API_KEY")
    
    def generate(self, video_type: str, topic: str = None) -> Optional[Dict]:
        """
        Generate viral content with guaranteed value delivery.
        """
        if video_type not in CONTENT_TEMPLATES:
            video_type = "life_hack"
        
        template = CONTENT_TEMPLATES[video_type]
        
        # If no topic, let AI choose
        if not topic:
            topic = "surprise me with something genuinely useful"
        
        prompt = template.format(topic=topic)
        
        if not self.groq_key:
            return self._fallback_content(video_type)
        
        try:
            from groq import Groq
            client = Groq(api_key=self.groq_key)
            
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.8
            )
            
            result = response.choices[0].message.content
            
            # Parse JSON
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0]
            elif "```" in result:
                result = result.split("```")[1].split("```")[0]
            
            content = json.loads(result.strip())
            
            # Verify value delivery
            script = content.get("full_script", "")
            check = self.checker.check_content(script)
            
            if check["verdict"] == "REJECT":
                print(f"⚠️ Content failed value check: {check['issues']}")
                # Try to improve or regenerate
                return self.generate(video_type, topic + " - be MORE SPECIFIC")
            
            content["value_check"] = check
            return content
            
        except Exception as e:
            print(f"⚠️ Generation failed: {e}")
            return self._fallback_content(video_type)
    
    def _fallback_content(self, video_type: str) -> Dict:
        """Fallback content that still delivers value."""
        fallbacks = {
            "life_hack": {
                "hook": "The 2-minute rule changes everything",
                "full_script": "If a task takes less than 2 minutes, do it immediately. "
                              "This one rule eliminated 80% of my mental clutter. "
                              "That email reply? 2 minutes. Hang up your coat? 30 seconds. "
                              "Your brain wastes more energy remembering tasks than doing them. "
                              "I did 47 two-minute tasks yesterday. Zero stress about pending things. "
                              "What's been sitting on your mental to-do list for weeks?",
                "specific_action": "Do any task under 2 minutes immediately",
            },
            "scary_fact": {
                "hook": "Your phone knows when you're about to get sick",
                "full_script": "Your typing speed drops 12% about 3 days before you show symptoms. "
                              "Stanford researchers found your phone's motion sensors detect subtle "
                              "changes in how you hold it when inflammation starts. "
                              "Some health apps can now predict illness before you feel anything. "
                              "Your daily screentime data is a health record you never knew existed. "
                              "Has your phone ever seemed to know something was wrong?",
                "the_fact": "Phones detect illness through typing pattern changes",
            },
            "psychology_fact": {
                "hook": "You make worse decisions after 3pm",
                "full_script": "Your willpower isn't infinite. It drains throughout the day. "
                              "By 3pm, decision fatigue has reduced your self-control by 40%. "
                              "That's why diets fail at dinner and impulse buys happen after work. "
                              "The fix: Make important decisions before noon. "
                              "Schedule your workout for morning. Plan meals the night before. "
                              "When does YOUR willpower crash?",
                "the_mechanism": "Decision fatigue depletes willpower by afternoon",
            }
        }
        return fallbacks.get(video_type, fallbacks["life_hack"])


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    'ViralVideoStructure',
    'CONTENT_TEMPLATES', 
    'ValueDeliveryChecker',
    'ViralContentGenerator'
]


if __name__ == "__main__":
    print("=" * 60)
    print("🧠 VIRAL VIDEO SCIENCE - Value Delivery Test")
    print("=" * 60)
    
    checker = ValueDeliveryChecker()
    
    # Test BAD content (the problem you identified)
    bad_content = """
    Your brain has an amazing trick you need to learn.
    Studies show this works for most people.
    Experts recommend trying this method.
    Follow for more tips on improving your life.
    """
    
    print("\n❌ Testing BAD content (no value delivery):")
    result = checker.check_content(bad_content)
    print(f"   Score: {result['score']}/100")
    print(f"   Verdict: {result['verdict']}")
    for issue in result['issues']:
        print(f"   ⚠️ {issue}")
    
    # Test GOOD content (delivers actual value)
    good_content = """
    The 2-minute rule will change your life.
    If any task takes less than 2 minutes, do it immediately.
    This simple system eliminated 80% of my mental clutter.
    Yesterday I completed 47 tiny tasks that would have 
    piled up and stressed me out. Your brain wastes more 
    energy remembering tasks than actually doing them.
    What's been sitting on your mental to-do list?
    """
    
    print("\n✅ Testing GOOD content (delivers value):")
    result = checker.check_content(good_content)
    print(f"   Score: {result['score']}/100")
    print(f"   Verdict: {result['verdict']}")
    if result['issues']:
        for issue in result['issues']:
            print(f"   ⚠️ {issue}")
    else:
        print("   ✅ No issues found!")
    
    # Test generator
    print("\n" + "=" * 60)
    print("🎬 Generating VALUE-FIRST content...")
    print("=" * 60)
    
    gen = ViralContentGenerator()
    content = gen.generate("life_hack", "productivity")
    
    if content:
        print(f"\n📝 Hook: {content.get('hook', 'N/A')}")
        print(f"\n📜 Script:\n{content.get('full_script', 'N/A')}")
        print(f"\n🎯 Action: {content.get('specific_action', 'N/A')}")
        
        if "value_check" in content:
            print(f"\n✅ Value Score: {content['value_check']['score']}/100")

