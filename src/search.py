"""
Search and retrieval functions for FYN-X memory system.
UPDATED: Support for speaker_name and important_sentences fields.
"""

from typing import List, Dict


def search_by_tag(memories: List[Dict], tag: str) -> List[Dict]:
    """
    Search memories by a single tag.
    
    Args:
        memories: List of memory entries
        tag: Tag to search for
        
    Returns:
        List of matching memories
    """
    tag = tag.lower()
    return [
        memory for memory in memories
        if tag in (t.lower() for t in memory.get('tags', []))
    ]


def search_by_multiple_tags(memories: List[Dict], tags: List[str], threshold: int = 1) -> List[Dict]:
    """
    Search memories by multiple tags with a match threshold.
    
    Args:
        memories: List of memory entries
        tags: List of tags to search for
        threshold: Minimum number of matching tags required
        
    Returns:
        List of matching memories sorted by relevance
    """
    tags_lower = [t.lower() for t in tags]
    scored_results = []
    
    for memory in memories:
        memory_tags = [t.lower() for t in memory.get('tags', [])]
        matches = len(set(tags_lower) & set(memory_tags))
        
        if matches >= threshold:
            scored_results.append({
                'memory': memory,
                'score': matches
            })
    
    # Sort by score descending
    scored_results.sort(key=lambda x: x['score'], reverse=True)
    return [item['memory'] for item in scored_results]


def format_memory_for_prompt(memory: Dict, include_full: bool = False) -> str:
    """
    Format a memory entry for inclusion in the LLM prompt.
    UPDATED: Prioritizes important_sentences over full conversation.
    
    Args:
        memory: Memory dict
        include_full: Whether to include full conversation (deprecated)
        
    Returns:
        Formatted string for prompt injection
    """
    lines = []
    
    # Header with speaker name if available
    timestamp = memory.get('timestamp', 'unknown')
    speaker = memory.get('speaker_name')
    if speaker:
        lines.append(f"[MEMORY | {timestamp} | Speaker: {speaker}]")
    else:
        lines.append(f"[MEMORY | {timestamp} | Speaker: Unknown]")
    
    # People mentioned in conversation
    if memory.get('people_mentioned'):
        people = ", ".join(memory['people_mentioned'])
        lines.append(f"People mentioned: {people}")
    
    # Topics discussed
    if memory.get('topics_discussed'):
        topics = ", ".join(memory['topics_discussed'])
        lines.append(f"Topics: {topics}")
    
    # Important sentences (NEW - prioritized)
    important = memory.get('important_sentences', [])
    if important:
        lines.append("\nKey points remembered:")
        for sent_info in important[:3]:  # Top 3 most important
            text = sent_info.get('text', sent_info) if isinstance(sent_info, dict) else sent_info
            lines.append(f"  • {text}")
    # Fallback to summary if no important sentences
    elif memory.get('summary'):
        lines.append("\nSummary:")
        lines.append(memory['summary'])
    # Fallback to full conversation (legacy support)
    elif include_full and memory.get('full_conversation'):
        lines.append("\nConversation:")
        lines.append(memory['full_conversation'])
    
    return "\n".join(lines)


def format_memories_for_prompt(memories: List[Dict], max_memories: int = 5) -> str:
    """
    Format multiple memories for prompt injection.
    
    Args:
        memories: List of memory dicts
        max_memories: Maximum number to include
        
    Returns:
        Formatted block of memories
    """
    if not memories:
        return "No relevant memories found."
    
    formatted = []
    for i, memory in enumerate(memories[:max_memories], 1):
        formatted.append(f"--- Memory {i} ---")
        formatted.append(format_memory_for_prompt(memory))
        formatted.append("")
    
    return "\n".join(formatted)


def get_memory_context_stats(memories: List[Dict]) -> Dict:
    """
    Get statistics about a set of memories (useful for debugging).
    
    Args:
        memories: List of memory dicts
        
    Returns:
        Dict with statistics
    """
    if not memories:
        return {
            'count': 0,
            'speakers': [],
            'topics': [],
            'people': []
        }
    
    all_speakers = set()
    all_topics = set()
    all_people = set()
    
    for memory in memories:
        speaker = memory.get('speaker_name')
        if speaker:
            all_speakers.add(speaker)
        
        all_topics.update(memory.get('topics_discussed', []))
        all_people.update(memory.get('people_mentioned', []))
    
    return {
        'count': len(memories),
        'speakers': sorted(list(all_speakers)),
        'topics': sorted(list(all_topics)),
        'people': sorted(list(all_people))
    }
