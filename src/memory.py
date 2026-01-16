"""
Memory management system for FYN-X.
Handles storage, retrieval, and management of conversation memories.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from src.tag_extraction import extract_memory_from_conversation


class MemoryManager:
    """Manages the persistent memory storage for FYN-X."""
    
    def __init__(self, memory_file: str = "data/memories.json"):
        self.memory_file = Path(memory_file)
        self.memories = self._load_memories()
        
    def _load_memories(self) -> List[Dict]:
        """Load memories from JSON file."""
        if not self.memory_file.exists():
            return []
        
        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('memories', [])
        except json.JSONDecodeError:
            print(f"Warning: Could not parse {self.memory_file}, starting fresh")
            return []
    
    def _save_memories(self):
        """Save memories to JSON file."""
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'last_updated': datetime.now().isoformat(),
            'total_memories': len(self.memories),
            'memories': self.memories
        }
        
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def add_memory(self, memory: Dict) -> int:
        """
        Add a new memory to the database.
        
        Args:
            memory: Memory dict (from extract_memory_from_conversation)
            
        Returns:
            Memory ID (index in list)
        """
        memory['id'] = len(self.memories)
        self.memories.append(memory)
        self._save_memories()
        return memory['id']
    
    def search_by_tags(self, tags: List[str], limit: int = 5) -> List[Dict]:
        """
        Search memories by tags, ranked by relevance.
        
        Args:
            tags: List of search tags
            limit: Maximum number of results
            
        Returns:
            List of matching memories, sorted by relevance
        """
        if not tags:
            return []
        
        # Score each memory by tag overlap
        scored_memories = []
        tags_lower = [t.lower() for t in tags]
        
        for memory in self.memories:
            memory_tags = [t.lower() for t in memory.get('tags', [])]
            
            # Count matching tags
            matches = len(set(tags_lower) & set(memory_tags))
            
            if matches > 0:
                scored_memories.append({
                    'memory': memory,
                    'score': matches
                })
        
        # Sort by score (descending) and return top results
        scored_memories.sort(key=lambda x: x['score'], reverse=True)
        return [item['memory'] for item in scored_memories[:limit]]
    
    def search_by_person(self, person_name: str, limit: int = 5) -> List[Dict]:
        """Search for memories involving a specific person."""
        person_lower = person_name.lower()
        
        results = []
        for memory in self.memories:
            people = [p.lower() for p in memory.get('people_mentioned', [])]
            if person_lower in people:
                results.append(memory)
        
        # Return most recent first
        results.sort(key=lambda x: x['timestamp'], reverse=True)
        return results[:limit]
    
    def search_by_topic(self, topic: str, limit: int = 5) -> List[Dict]:
        """Search for memories discussing a specific topic."""
        topic_lower = topic.lower()
        
        results = []
        for memory in self.memories:
            topics = [t.lower() for t in memory.get('topics_discussed', [])]
            if topic_lower in topics:
                results.append(memory)
        
        results.sort(key=lambda x: x['timestamp'], reverse=True)
        return results[:limit]
    
    def get_recent_memories(self, limit: int = 5) -> List[Dict]:
        """Get the most recent memories."""
        sorted_memories = sorted(
            self.memories, 
            key=lambda x: x['timestamp'], 
            reverse=True
        )
        return sorted_memories[:limit]
    
    def get_memory_by_id(self, memory_id: int) -> Optional[Dict]:
        """Retrieve a specific memory by ID."""
        for memory in self.memories:
            if memory.get('id') == memory_id:
                return memory
        return None
    
    def get_stats(self) -> Dict:
        """Get statistics about the memory database."""
        if not self.memories:
            return {
                'total_memories': 0,
                'total_conversations': 0,
                'unique_people': 0,
                'unique_topics': 0
            }
        
        all_people = set()
        all_topics = set()
        total_conversations = 0
        
        for memory in self.memories:
            all_people.update(memory.get('people_mentioned', []))
            all_topics.update(memory.get('topics_discussed', []))
            total_conversations += memory.get('conversation_length', 0)
        
        return {
            'total_memories': len(self.memories),
            'total_conversations': total_conversations,
            'unique_people': len(all_people),
            'unique_topics': len(all_topics),
            'people': sorted(list(all_people)),
            'topics': sorted(list(all_topics))
        }


class ConversationSession:
    """Manages an active conversation session."""
    
    def __init__(self, speaker_identity: str = "unknown"):
        self.history = []
        self.speaker_identity = speaker_identity
        self.start_time = datetime.now()
        
    def add_turn(self, speaker: str, text: str):
        """Add a conversational turn."""
        self.history.append({
            'speaker': speaker,
            'text': text,
            'timestamp': datetime.now().isoformat()
        })
    
    def should_save(self, min_turns: int = 4) -> bool:
        """Determine if conversation is worth saving."""
        # Save if there's meaningful interaction
        user_turns = [t for t in self.history if t['speaker'] == 'user']
        return len(user_turns) >= min_turns
    
    def to_memory(self) -> Dict:
        """Convert conversation to memory format."""
        memory = extract_memory_from_conversation(self.history)
        memory['speaker_identity'] = self.speaker_identity
        memory['session_start'] = self.start_time.isoformat()
        return memory
    
    def get_context_summary(self, last_n_turns: int = 4) -> str:
        """Get recent conversation context for the prompt."""
        recent = self.history[-last_n_turns:] if len(self.history) > last_n_turns else self.history
        
        return "\n".join([
            f"{turn['speaker'].upper()}: {turn['text']}"
            for turn in recent
        ])
