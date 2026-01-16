"""
Test script for FYN-X memory and tag extraction systems.
Run this to verify components are working correctly.
"""

from src.tag_extraction import extract_tags, explain_extraction, extract_conversation_metadata
from src.memory import MemoryManager, ConversationSession
from src.search import format_memories_for_prompt


def test_tag_extraction():
    """Test the tag extraction system."""
    print("=" * 60)
    print("TAG EXTRACTION TESTS")
    print("=" * 60)
    
    test_inputs = [
        "Hey, I just got back from visiting Sarah in Portland",
        "Yesterday I met with my friend Tom to discuss the new project at work",
        "Can you remind me what we talked about last Tuesday?",
        "I need to plan a birthday party for my daughter next month",
        "My car broke down yesterday and I had to call a mechanic"
    ]
    
    for i, text in enumerate(test_inputs, 1):
        print(f"\nTest {i}:")
        print(explain_extraction(text))
        print("-" * 60)


def test_memory_system():
    """Test the memory management system."""
    print("\n" + "=" * 60)
    print("MEMORY SYSTEM TESTS")
    print("=" * 60)
    
    # Create a test conversation
    session = ConversationSession(speaker_identity="test_user")
    
    session.add_turn("user", "Hey FYN-X, I just met with Sarah to discuss the marketing project")
    session.add_turn("fynx", "Ah, how productive! Marketing projects can be quite involved.")
    session.add_turn("user", "Yeah, we decided to launch next month")
    session.add_turn("fynx", "Next month—excellent timing. I shall note that.")
    session.add_turn("user", "We also talked about hiring a new designer")
    session.add_turn("fynx", "A wise decision. Creative talent is invaluable.")
    
    print("\n1. Session created with 6 turns")
    print(f"   Should save: {session.should_save()}")
    
    # Convert to memory
    memory = session.to_memory()
    print("\n2. Memory extracted from conversation:")
    print(f"   Topics: {memory['topics_discussed']}")
    print(f"   People: {memory['people_mentioned']}")
    print(f"   Tags: {memory['tags'][:10]}")  # Show first 10
    
    # Test memory manager
    print("\n3. Testing MemoryManager:")
    manager = MemoryManager("data/test_memories.json")
    
    # Add memory
    memory_id = manager.add_memory(memory)
    print(f"   Memory saved with ID: {memory_id}")
    
    # Search by tags
    results = manager.search_by_tags(["sarah", "project"])
    print(f"   Search for 'sarah' and 'project': {len(results)} results")
    
    # Search by person
    results = manager.search_by_person("sarah")
    print(f"   Search for person 'sarah': {len(results)} results")
    
    # Get stats
    stats = manager.get_stats()
    print(f"   Database stats: {stats['total_memories']} memories, {stats['unique_people']} people")
    
    print("\n4. Formatted memory for prompt:")
    formatted = format_memories_for_prompt(results, max_memories=1)
    print(formatted[:300] + "...")  # Show first 300 chars


def test_retrieval_scenario():
    """Test a realistic memory retrieval scenario."""
    print("\n" + "=" * 60)
    print("RETRIEVAL SCENARIO TEST")
    print("=" * 60)
    
    # Create memory manager with test data
    manager = MemoryManager("data/test_memories.json")
    
    # Simulate several past conversations
    conversations = [
        {
            "speaker": "riley",
            "turns": [
                ("user", "I went to that new Italian restaurant downtown with Maria"),
                ("fynx", "Oh wonderful! Italian cuisine is quite delightful."),
                ("user", "Yeah, the pasta was amazing"),
                ("fynx", "I shall note this recommendation for future reference.")
            ]
        },
        {
            "speaker": "riley",
            "turns": [
                ("user", "I need to finish that Python project for work"),
                ("fynx", "Ah yes, programming tasks. How is it progressing?"),
                ("user", "Almost done, just need to add testing"),
                ("fynx", "Testing is most crucial. Well done for prioritizing it.")
            ]
        },
        {
            "speaker": "guest",
            "turns": [
                ("user", "Tell me about the Clone Wars"),
                ("fynx", "Ah, the Clone Wars—a most turbulent period..."),
                ("user", "Who was involved?"),
                ("fynx", "The Republic and Separatists, primarily...")
            ]
        }
    ]
    
    # Add conversations to memory
    print("\nAdding test conversations to memory...")
    for conv in conversations:
        session = ConversationSession(conv["speaker"])
        for speaker, text in conv["turns"]:
            session.add_turn(speaker, text)
        
        if session.should_save(min_turns=2):
            memory = session.to_memory()
            manager.add_memory(memory)
    
    print(f"Added {len(conversations)} conversations")
    
    # Test queries
    print("\n" + "-" * 60)
    print("Testing memory retrieval:")
    print("-" * 60)
    
    test_queries = [
        "Where did I go with Maria?",
        "What projects am I working on?",
        "Tell me about restaurants"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        tags = extract_tags(query)
        print(f"Tags: {tags}")
        
        results = manager.search_by_tags(tags, limit=2)
        print(f"Results: {len(results)} memories found")
        
        if results:
            print(f"Top result topics: {results[0].get('topics_discussed', [])}")
            print(f"Top result people: {results[0].get('people_mentioned', [])}")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("FYN-X COMPONENT TEST SUITE")
    print("=" * 60)
    
    try:
        test_tag_extraction()
        test_memory_system()
        test_retrieval_scenario()
        
        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED")
        print("=" * 60)
        print("\nNote: Test memories saved to data/test_memories.json")
        print("You can safely delete this file if needed.")
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
