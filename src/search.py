"""
Search and retrieval functions for FYN-X memory system.
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
    
    Args:
        memory: Memory dict
        include_full: Whether to include full conversation or just summary
        
    Returns:
        Formatted string for prompt injection
    """
    lines = []
    
    # Header
    timestamp = memory.get('timestamp', 'unknown')
    lines.append(f"[MEMORY | {timestamp}]")
    
    # People involved
    if memory.get('people_mentioned'):
        people = ", ".join(memory['people_mentioned'])
        lines.append(f"People: {people}")
    
    # Topics discussed
    if memory.get('topics_discussed'):
        topics = ", ".join(memory['topics_discussed'])
        lines.append(f"Topics: {topics}")
    
    # Content
    if include_full and memory.get('full_conversation'):
        lines.append("\nConversation:")
        lines.append(memory['full_conversation'])
    elif memory.get('summary'):
        lines.append("\nSummary:")
        lines.append(memory['summary'])
    
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
