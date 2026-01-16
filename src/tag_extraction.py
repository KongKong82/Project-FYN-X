"""
Tag extraction optimized for personal memory and conversation tracking.
Extracts: names, topics, activities, locations, temporal references.
"""

import re
from typing import List, Set, Dict
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
    "called", "texted", "emailed", "messaged", "meeting", "project"
}

# Topics that often indicate important conversation subjects
TOPIC_INDICATORS = {
    "work", "job", "career", "family", "friend", "house", "apartment",
    "car", "trip", "vacation", "hobby", "project", "problem", "issue",
    "idea", "plan", "goal", "dream", "health", "doctor", "school",
    "university", "college", "course", "class", "exam", "grade",
    "movie", "show", "book", "game", "music", "concert", "restaurant",
    "birthday", "anniversary", "wedding", "party", "event"
}

# Temporal markers
TEMPORAL_MARKERS = {
    "yesterday", "today", "tomorrow", "tonight", "morning", "afternoon",
    "evening", "night", "monday", "tuesday", "wednesday", "thursday",
    "friday", "saturday", "sunday", "week", "month", "year", "january",
    "february", "march", "april", "may", "june", "july", "august",
    "september", "october", "november", "december", "recently", "soon"
}


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
        'general': set()
    }
    
    # General keywords (not stop words, length > 3)
    for word in words:
        if word not in STOP_WORDS and len(word) > 3:
            if (word not in entities['activities'] and 
                word not in entities['topics'] and
                word not in entities['temporal']):
                entities['general'].add(word)
    
    return entities


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
    This runs after conversation ends to create a memory entry.
    
    Args:
        conversation_history: List of turn dicts with 'speaker' and 'text'
        
    Returns:
        Memory entry dict ready for storage
    """
    # Collect all tags across conversation
    all_tags = set()
    all_entities = {'names': set(), 'activities': set(), 
                   'topics': set(), 'temporal': set(), 'general': set()}
    
    user_turns = []
    full_text = []
    
    for turn in conversation_history:
        if turn['speaker'] == 'user':
            user_turns.append(turn['text'])
            full_text.append(f"User: {turn['text']}")
            
            entities = extract_entities(turn['text'])
            for category, tags in entities.items():
                all_entities[category].update(tags)
                all_tags.update(tags)
        else:
            full_text.append(f"FYN-X: {turn['text']}")
    
    # Create summary (first few and last few exchanges)
    summary_turns = []
    if len(conversation_history) > 6:
        summary_turns = conversation_history[:3] + conversation_history[-3:]
    else:
        summary_turns = conversation_history
    
    summary = "\n".join([f"{t['speaker']}: {t['text']}" for t in summary_turns])
    
    return {
        'timestamp': datetime.now().isoformat(),
        'conversation_length': len(conversation_history),
        'user_turns': len(user_turns),
        'tags': sorted(list(all_tags)),
        'entities': {k: sorted(list(v)) for k, v in all_entities.items()},
        'summary': summary,
        'full_conversation': "\n".join(full_text) if len(conversation_history) <= 10 else None,
        'topics_discussed': sorted(list(all_entities['topics'])),
        'people_mentioned': sorted(list(all_entities['names']))
    }


# Debugging helper
def explain_extraction(text: str) -> str:
    """Show what was extracted and why."""
    entities = extract_entities(text)
    tags = extract_tags(text)
    
    lines = [
        f"Input: '{text}'",
        f"\nExtracted entities by category:",
        f"  Names: {sorted(entities['names'])}",
        f"  Activities: {sorted(entities['activities'])}",
        f"  Topics: {sorted(entities['topics'])}",
        f"  Temporal: {sorted(entities['temporal'])}",
        f"  General: {sorted(list(entities['general'])[:10])}",  # Limit output
        f"\nAll tags for search: {tags[:20]}"  # Limit output
    ]
    
    return "\n".join(lines)
