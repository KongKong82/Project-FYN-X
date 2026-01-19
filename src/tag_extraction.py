"""
Tag extraction optimized for personal memory and conversation tracking.
Extracts: names, topics, activities, locations, temporal references.
UPDATED: Now extracts only important/memorable sentences and detects self-introductions.
"""

import re
from typing import List, Set, Dict, Tuple, Optional
from datetime import datetime

# Common words to filter out
STOP_WORDS = {
    "the", "this", "that", "these", "those", "what", "when", "where", 
    "which", "how", "with", "from", "about", "there", "their", "they",
    "have", "has", "had", "been", "were", "was", "are", "you", "your",
    "could", "would", "should", "will", "tell", "know", "think", "want",
    "like", "just", "also", "very", "much", "more", "most", "some", "any",
    "each", "every", "both", "such", "only", "than", "then", "them",
    "does", "did", "doing", "into", "through", "during", "before", "after",
    "above", "below", "between", "under", "again", "further", "once",
    "make", "made", "said", "says", "please", "thanks", "here", "there"
}

# Action/activity verbs that indicate events worth remembering
ACTIVITY_VERBS = {
    "visited", "went", "traveled", "saw", "met", "talked", "discussed",
    "played", "watched", "read", "wrote", "built", "created", "fixed",
    "learned", "studied", "taught", "helped", "worked", "started", "finished",
    "bought", "sold", "cooked", "ate", "drank", "celebrated", "moved",
    "called", "texted", "emailed", "messaged", "meeting", "project",
    "planning", "designing", "developing", "testing", "launched"
}

# Topics that often indicate important conversation subjects
TOPIC_INDICATORS = {
    "work", "job", "career", "family", "friend", "house", "apartment",
    "car", "trip", "vacation", "hobby", "project", "problem", "issue",
    "idea", "plan", "goal", "dream", "health", "doctor", "school",
    "university", "college", "course", "class", "exam", "grade",
    "movie", "show", "book", "game", "music", "concert", "restaurant",
    "birthday", "anniversary", "wedding", "party", "event", "deadline",
    "presentation", "interview", "promotion", "raise"
}

# Temporal markers
TEMPORAL_MARKERS = {
    "yesterday", "today", "tomorrow", "tonight", "morning", "afternoon",
    "evening", "night", "monday", "tuesday", "wednesday", "thursday",
    "friday", "saturday", "sunday", "week", "month", "year", "january",
    "february", "march", "april", "may", "june", "july", "august",
    "september", "october", "november", "december", "recently", "soon",
    "now", "later", "earlier"
}

# Importance indicators for sentence scoring
IMPORTANCE_INDICATORS = {
    "important", "remember", "remind", "never", "always", "must",
    "need", "want", "love", "hate", "favorite", "best", "worst",
    "excited", "worried", "nervous", "happy", "sad", "angry",
    "decided", "realized", "discovered", "learned", "found"
}


def detect_self_introduction(text: str) -> Optional[str]:
    """
    Detect if the user is introducing themselves and extract their name.
    
    Patterns detected:
    - "I'm [Name]" / "I am [Name]"
    - "My name is [Name]"
    - "Call me [Name]"
    - "This is [Name]"
    - "Name's [Name]" / "Name is [Name]"
    - "Hi, I'm [Name]"
    
    Args:
        text: User input text
        
    Returns:
        Detected name or None
    """
    # Patterns to match self-introduction
    patterns = [
        r"(?:^|[.!?]\s+)(?:hi|hello|hey)?,?\s*i'?m\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        r"(?:^|[.!?]\s+)i\s+am\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        r"my name(?:'s| is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        r"call me\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        r"(?:^|[.!?]\s+)this is\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        r"(?:name's|name is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            # Validate it's a proper name (capitalized, not a common word)
            if name and name[0].isupper() and name.lower() not in STOP_WORDS:
                # Return with proper capitalization
                return name.title()
    
    return None


def extract_names(text: str) -> Set[str]:
    """
    Extract potential names (capitalized words that aren't sentence starters).
    Simple heuristic - can be improved with NER later.
    """
    names = set()
    
    # Look for capitalized words not at sentence start
    sentences = re.split(r'[.!?]+\s+', text)
    for sentence in sentences:
        words = sentence.split()
        for i, word in enumerate(words):
            # Skip first word of sentence, skip all-caps
            if i == 0 or word.isupper():
                continue
            
            # Check if capitalized and alphabetic
            if word and word[0].isupper() and word.isalpha():
                names.add(word.lower())
    
    return names


def extract_entities(text: str) -> Dict[str, Set[str]]:
    """
    Extract different types of entities from text.
    Returns dict with categories: names, activities, topics, temporal
    """
    text_lower = text.lower()
    words = set(re.findall(r'\b\w+\b', text_lower))
    
    entities = {
        'names': extract_names(text),
        'activities': words & ACTIVITY_VERBS,
        'topics': words & TOPIC_INDICATORS,
        'temporal': words & TEMPORAL_MARKERS,
        'importance': words & IMPORTANCE_INDICATORS,
        'general': set()
    }
    
    # General keywords (not stop words, length > 3)
    for word in words:
        if word not in STOP_WORDS and len(word) > 3:
            if (word not in entities['activities'] and 
                word not in entities['topics'] and
                word not in entities['temporal'] and
                word not in entities['importance']):
                entities['general'].add(word)
    
    return entities


def score_sentence_importance(sentence: str) -> Tuple[float, Dict]:
    """
    Score a sentence based on how memorable/important it is.
    
    Returns:
        (score, details) where score is 0-100 and details explains the score
    """
    entities = extract_entities(sentence)
    
    score = 0.0
    details = {}
    
    # Names mentioned: +15 per name (capped at 30)
    name_count = len(entities['names'])
    name_score = min(name_count * 15, 30)
    score += name_score
    details['names'] = name_count
    
    # Activities: +10 per activity verb (capped at 30)
    activity_count = len(entities['activities'])
    activity_score = min(activity_count * 10, 30)
    score += activity_score
    details['activities'] = activity_count
    
    # Topics: +8 per topic (capped at 24)
    topic_count = len(entities['topics'])
    topic_score = min(topic_count * 8, 24)
    score += topic_score
    details['topics'] = topic_count
    
    # Temporal markers: +5 per temporal word (capped at 15)
    temporal_count = len(entities['temporal'])
    temporal_score = min(temporal_count * 5, 15)
    score += temporal_score
    details['temporal'] = temporal_count
    
    # Importance indicators: +12 per indicator (capped at 36)
    importance_count = len(entities['importance'])
    importance_score = min(importance_count * 12, 36)
    score += importance_score
    details['importance'] = importance_count
    
    # Length bonus: longer sentences often contain more info
    word_count = len(sentence.split())
    if word_count > 5:
        length_score = min((word_count - 5) * 0.5, 10)
        score += length_score
        details['length'] = word_count
    
    # Normalize to 0-100
    score = min(score, 100)
    
    return score, details


def extract_important_sentences(text: str, min_score: float = 30.0, max_sentences: int = 5) -> List[Dict]:
    """
    Extract the most important/memorable sentences from text.
    
    Args:
        text: Input text (could be single turn or conversation)
        min_score: Minimum importance score to include (0-100)
        max_sentences: Maximum number of sentences to return
        
    Returns:
        List of dicts with 'text', 'score', and 'details'
    """
    # Split into sentences
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # Score each sentence
    scored_sentences = []
    for sentence in sentences:
        score, details = score_sentence_importance(sentence)
        if score >= min_score:
            scored_sentences.append({
                'text': sentence,
                'score': score,
                'details': details
            })
    
    # Sort by score and return top N
    scored_sentences.sort(key=lambda x: x['score'], reverse=True)
    return scored_sentences[:max_sentences]


def extract_tags(text: str, prioritize_categories: bool = True) -> List[str]:
    """
    Extract tags optimized for memory retrieval.
    
    Args:
        text: Input text from user
        prioritize_categories: If True, categorize and prioritize certain tag types
        
    Returns:
        Sorted list of tags for memory search
    """
    entities = extract_entities(text)
    
    all_tags = set()
    
    # Add all entity types
    for category, tags in entities.items():
        all_tags.update(tags)
    
    return sorted(list(all_tags))


def extract_conversation_metadata(text: str, speaker: str = "user") -> Dict:
    """
    Extract metadata from conversation for memory storage.
    
    Returns:
        Dict with tags, entities, timestamp, speaker info
    """
    entities = extract_entities(text)
    
    return {
        'timestamp': datetime.now().isoformat(),
        'speaker': speaker,
        'text': text,
        'tags': sorted(list(set().union(*entities.values()))),
        'entities': {k: sorted(list(v)) for k, v in entities.items()},
        'word_count': len(text.split())
    }


def extract_memory_from_conversation(conversation_history: List[Dict]) -> Dict:
    """
    Analyze full conversation and extract memorable information.
    UPDATED: Now extracts only the most important sentences instead of full conversation.
    
    Args:
        conversation_history: List of turn dicts with 'speaker' and 'text'
        
    Returns:
        Memory entry dict ready for storage
    """
    # Collect all tags across conversation
    all_tags = set()
    all_entities = {'names': set(), 'activities': set(), 
                   'topics': set(), 'temporal': set(), 'importance': set(), 'general': set()}
    
    user_turns = []
    important_sentences = []
    
    # Process each user turn
    for turn in conversation_history:
        if turn['speaker'] == 'user':
            user_text = turn['text']
            user_turns.append(user_text)
            
            # Extract entities
            entities = extract_entities(user_text)
            for category, tags in entities.items():
                all_entities[category].update(tags)
                all_tags.update(tags)
            
            # Extract important sentences from this turn
            important = extract_important_sentences(user_text, min_score=25.0, max_sentences=2)
            important_sentences.extend(important)
    
    # Sort all important sentences by score and keep top 5
    important_sentences.sort(key=lambda x: x['score'], reverse=True)
    top_sentences = important_sentences[:5]
    
    # Create compact summary from important sentences
    summary_text = " | ".join([s['text'] for s in top_sentences])
    
    return {
        'timestamp': datetime.now().isoformat(),
        'conversation_length': len(conversation_history),
        'user_turns': len(user_turns),
        'tags': sorted(list(all_tags)),
        'entities': {k: sorted(list(v)) for k, v in all_entities.items()},
        'important_sentences': [
            {'text': s['text'], 'score': s['score']} 
            for s in top_sentences
        ],
        'summary': summary_text,
        'topics_discussed': sorted(list(all_entities['topics'])),
        'people_mentioned': sorted(list(all_entities['names'])),
        # Only store full conversation if it's very short (< 4 turns)
        'full_conversation': None
    }


# Debugging helper
def explain_extraction(text: str) -> str:
    """Show what was extracted and why."""
    entities = extract_entities(text)
    tags = extract_tags(text)
    important = extract_important_sentences(text)
    name_detected = detect_self_introduction(text)
    
    lines = [
        f"Input: '{text}'",
    ]
    
    if name_detected:
        lines.append(f"\n🎯 SELF-INTRODUCTION DETECTED: {name_detected}")
    
    lines.extend([
        f"\nExtracted entities by category:",
        f"  Names: {sorted(entities['names'])}",
        f"  Activities: {sorted(entities['activities'])}",
        f"  Topics: {sorted(entities['topics'])}",
        f"  Temporal: {sorted(entities['temporal'])}",
        f"  Importance: {sorted(entities['importance'])}",
        f"  General: {sorted(list(entities['general'])[:10])}",
        f"\nAll tags for search: {tags[:20]}",
        f"\nImportant sentences:"
    ])
    
    for sent in important:
        lines.append(f"  [{sent['score']:.1f}] {sent['text']}")
    
    return "\n".join(lines)
