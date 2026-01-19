"""
Memory management system for FYN-X.
Handles storage, retrieval, and management of conversation memories.
UPDATED: Added name field, automatic name detection, only saves known speakers.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from src.tag_extraction import extract_memory_from_conversation, detect_self_introduction


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
    
    def search_by_tags(self, tags: List[str], limit: int = 5, speaker_name: Optional[str] = None) -> List[Dict]:
        """
        Search memories by tags, optionally filtered by speaker name.
        
        Args:
            tags: List of search tags
            limit: Maximum number of results
            speaker_name: If provided, only return memories for this person
            
        Returns:
            List of matching memories, sorted by relevance
        """
        if not tags:
            return []
        
        # Score each memory by tag overlap
        scored_memories = []
        tags_lower = [t.lower() for t in tags]
        
        for memory in self.memories:
            # Filter by speaker name if provided
            if speaker_name:
                mem_name = memory.get('speaker_name', '').lower()
                if mem_name != speaker_name.lower() and mem_name != 'unknown':
                    continue
            
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
        """Search for memories involving a specific person (mentioned in conversation)."""
        person_lower = person_name.lower()
        
        results = []
        for memory in self.memories:
            people = [p.lower() for p in memory.get('people_mentioned', [])]
            if person_lower in people:
                results.append(memory)
        
        # Return most recent first
        results.sort(key=lambda x: x['timestamp'], reverse=True)
        return results[:limit]
    
    def search_by_speaker_name(self, speaker_name: str, limit: int = 5) -> List[Dict]:
        """Search for memories by the person who was speaking (speaker_name field)."""
        speaker_lower = speaker_name.lower()
        
        results = []
        for memory in self.memories:
            mem_speaker = memory.get('speaker_name', '').lower()
            if mem_speaker == speaker_lower:
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
    
    def get_recent_memories(self, limit: int = 5, speaker_name: Optional[str] = None) -> List[Dict]:
        """
        Get the most recent memories.
        
        Args:
            limit: Maximum number of memories
            speaker_name: If provided, only return memories for this person
        """
        memories_to_search = self.memories
        
        # Filter by speaker if provided
        if speaker_name:
            speaker_lower = speaker_name.lower()
            memories_to_search = [
                m for m in self.memories 
                if m.get('speaker_name', '').lower() == speaker_lower or 
                   m.get('speaker_name', '').lower() == 'unknown'
            ]
        
        sorted_memories = sorted(
            memories_to_search, 
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
                'unique_topics': 0,
                'unique_speakers': 0
            }
        
        all_people = set()
        all_topics = set()
        all_speakers = set()
        total_conversations = 0
        
        for memory in self.memories:
            all_people.update(memory.get('people_mentioned', []))
            all_topics.update(memory.get('topics_discussed', []))
            speaker_name = memory.get('speaker_name', 'unknown')
            if speaker_name and speaker_name != 'unknown':
                all_speakers.add(speaker_name)
            total_conversations += memory.get('conversation_length', 0)
        
        return {
            'total_memories': len(self.memories),
            'total_conversations': total_conversations,
            'unique_people': len(all_people),
            'unique_topics': len(all_topics),
            'unique_speakers': len(all_speakers),
            'people': sorted(list(all_people)),
            'topics': sorted(list(all_topics)),
            'speakers': sorted(list(all_speakers))
        }


class ConversationSession:
    """Manages an active conversation session with automatic name detection."""
    
    def __init__(self, speaker_name: str = None):
        """
        Initialize conversation session.
        
        Args:
            speaker_name: Name of the person speaking (None = unknown)
        """
        self.history = []
        self.speaker_name = speaker_name  # Can be None or a name
        self.start_time = datetime.now()
        self.name_just_learned = False  # Track if we just learned the name
        
    def set_speaker_name(self, name: str):
        """Update the speaker name if learned during conversation."""
        if not self.speaker_name and name:
            self.name_just_learned = True
        self.speaker_name = name
    
    def detect_name_from_turn(self, user_text: str) -> Optional[str]:
        """
        Automatically detect if user is introducing themselves.
        
        Args:
            user_text: The user's message
            
        Returns:
            Detected name or None
        """
        detected_name = detect_self_introduction(user_text)
        
        if detected_name and not self.speaker_name:
            self.set_speaker_name(detected_name)
            return detected_name
        
        return None
        
    def add_turn(self, speaker: str, text: str):
        """Add a conversational turn and check for name introduction."""
        self.history.append({
            'speaker': speaker,
            'text': text,
            'timestamp': datetime.now().isoformat()
        })
    
    def should_save(self, min_turns: int = 4) -> bool:
        """
        Determine if conversation is worth saving.
        Only saves if speaker name is known.
        """
        # Don't save if we don't know who we're talking to
        if not self.speaker_name:
            return False
        
        # Save if there's meaningful interaction
        user_turns = [t for t in self.history if t['speaker'] == 'user']
        return len(user_turns) >= min_turns
    
    def can_save_memory(self) -> bool:
        """Check if we can save memories (speaker must be known)."""
        return self.speaker_name is not None
    
    def to_memory(self) -> Dict:
        """Convert conversation to memory format."""
        memory = extract_memory_from_conversation(self.history)
        
        # Add speaker name field (can be None, but should not save if None)
        memory['speaker_name'] = self.speaker_name
        memory['session_start'] = self.start_time.isoformat()
        
        return memory
    
    def get_context_summary(self, last_n_turns: int = 4) -> str:
        """Get recent conversation context for the prompt."""
        recent = self.history[-last_n_turns:] if len(self.history) > last_n_turns else self.history
        
        return "\n".join([
            f"{turn['speaker'].upper()}: {turn['text']}"
            for turn in recent
        ])
    
    def get_speaker_identity_context(self) -> str:
        """Get context about speaker identity for the prompt."""
        if self.speaker_name:
            return f"Speaking with: {self.speaker_name}"
        else:
            return "Speaking with: Unknown person"
