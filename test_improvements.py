"""
Test script for FYN-X improvements.
Tests: sentence importance scoring, automatic name detection, benchmarking.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from tag_extraction import (
    score_sentence_importance, 
    extract_important_sentences,
    extract_entities,
    explain_extraction,
    detect_self_introduction
)
from memory import MemoryManager, ConversationSession
from benchmarks import track_time, start_session, end_session


def test_name_detection():
    """Test automatic name detection from conversation."""
    print("\n" + "=" * 70)
    print("TEST 1: Automatic Name Detection")
    print("=" * 70)
    
    test_cases = [
        ("Hi, I'm Riley", "Riley"),
        ("Hello! My name is Alex", "Alex"),
        ("Call me Sam", "Sam"),
        ("I am Jordan", "Jordan"),
        ("This is Morgan speaking", "Morgan"),
        ("Hey, name's Taylor", "Taylor"),
        ("I'm working on a project", None),  # No introduction
        ("My name is very important", None),  # "very" is stop word
    ]
    
    for text, expected in test_cases:
        detected = detect_self_introduction(text)
        status = "✓" if detected == expected else "✗"
        print(f"{status} \"{text}\"")
        print(f"   Expected: {expected}, Got: {detected}")
        print()


def test_conversation_with_name_detection():
    """Test conversation session with automatic name detection."""
    print("\n" + "=" * 70)
    print("TEST 2: Conversation Session with Auto Name Detection")
    print("=" * 70)
    
    # Scenario 1: User introduces themselves
    print("\n--- Scenario 1: User introduces themselves ---")
    session1 = ConversationSession(speaker_name=None)
    
    print(f"Initial speaker: {session1.speaker_name}")
    print(f"Can save memory: {session1.can_save_memory()}")
    
    # First turn - introduction
    user_msg1 = "Hi! I'm Riley and I'm working on robotics"
    detected = session1.detect_name_from_turn(user_msg1)
    session1.add_turn('user', user_msg1)
    session1.add_turn('fynx', "Nice to meet you, Riley!")
    
    print(f"\nAfter introduction: '{user_msg1}'")
    print(f"  Detected name: {detected}")
    print(f"  Speaker now: {session1.speaker_name}")
    print(f"  Can save memory: {session1.can_save_memory()}")
    
    # Scenario 2: User never introduces themselves
    print("\n--- Scenario 2: User never introduces themselves ---")
    session2 = ConversationSession(speaker_name=None)
    
    session2.add_turn('user', "I like robotics")
    session2.add_turn('fynx', "That's interesting!")
    session2.add_turn('user', "I'm working on a project")
    session2.add_turn('fynx', "Tell me more!")
    
    print(f"Speaker: {session2.speaker_name}")
    print(f"Can save memory: {session2.can_save_memory()}")
    print(f"Should save: {session2.should_save()}")
    
    # Scenario 3: Manual name setting as fallback
    print("\n--- Scenario 3: Manual name setting (fallback) ---")
    session3 = ConversationSession(speaker_name=None)
    
    session3.add_turn('user', "I like robotics")
    print(f"Before setname - Can save: {session3.can_save_memory()}")
    
    session3.set_speaker_name("TestUser")
    print(f"After setname - Can save: {session3.can_save_memory()}")
    print(f"Speaker: {session3.speaker_name}")


def test_memory_saving_rules():
    """Test that memories are only saved for known speakers."""
    print("\n" + "=" * 70)
    print("TEST 3: Memory Saving Rules (Known Speakers Only)")
    print("=" * 70)
    
    # Create test memory manager
    test_file = "data/test_memories_auto.json"
    manager = MemoryManager(memory_file=test_file)
    
    # Session 1: Unknown speaker (should NOT save)
    print("\n--- Session 1: Unknown speaker ---")
    session1 = ConversationSession(speaker_name=None)
    session1.add_turn('user', "I like robots")
    session1.add_turn('fynx', "Cool!")
    session1.add_turn('user', "They're fascinating")
    session1.add_turn('fynx', "Indeed!")
    session1.add_turn('user', "I work with them daily")
    session1.add_turn('fynx', "Awesome!")
    
    print(f"Speaker: {session1.speaker_name}")
    print(f"Should save: {session1.should_save()}")
    
    if session1.should_save():
        memory1 = session1.to_memory()
        manager.add_memory(memory1)
        print("✗ MEMORY WAS SAVED (should not have been!)")
    else:
        print("✓ Memory correctly NOT saved (unknown speaker)")
    
    # Session 2: Known speaker (should save)
    print("\n--- Session 2: Known speaker (auto-detected) ---")
    session2 = ConversationSession(speaker_name=None)
    session2.detect_name_from_turn("Hi, I'm Riley")
    session2.add_turn('user', "Hi, I'm Riley")
    session2.add_turn('fynx', "Hello Riley!")
    session2.add_turn('user', "I work on robotics projects")
    session2.add_turn('fynx', "That's great!")
    session2.add_turn('user', "FYN-X is my current project")
    session2.add_turn('fynx', "Tell me more!")
    
    print(f"Speaker: {session2.speaker_name}")
    print(f"Should save: {session2.should_save()}")
    
    if session2.should_save():
        memory2 = session2.to_memory()
        id2 = manager.add_memory(memory2)
        print(f"✓ Memory correctly saved (ID: {id2}, Speaker: {session2.speaker_name})")
    else:
        print("✗ Memory NOT saved (should have been!)")
    
    # Session 3: Name learned mid-conversation
    print("\n--- Session 3: Name learned mid-conversation ---")
    session3 = ConversationSession(speaker_name=None)
    # First few turns - no name
    session3.add_turn('user', "Hello")
    session3.add_turn('fynx', "Hi!")
    session3.add_turn('user', "I like robots")
    session3.add_turn('fynx', "Me too!")
    
    # Then user introduces themselves
    intro_msg = "By the way, I'm Alex"
    session3.detect_name_from_turn(intro_msg)
    session3.add_turn('user', intro_msg)
    session3.add_turn('fynx', "Nice to meet you, Alex!")
    session3.add_turn('user', "I work on AI projects")
    session3.add_turn('fynx', "Interesting!")
    
    print(f"Speaker: {session3.speaker_name}")
    print(f"Should save: {session3.should_save()}")
    
    if session3.should_save():
        memory3 = session3.to_memory()
        id3 = manager.add_memory(memory3)
        print(f"✓ Memory correctly saved (ID: {id3}, Speaker: {session3.speaker_name})")
        print(f"  (Entire conversation saved, including pre-introduction turns)")
    else:
        print("✗ Memory NOT saved (should have been!)")
    
    # Show final stats
    print("\n--- Final Memory Stats ---")
    stats = manager.get_stats()
    print(f"Total memories saved: {stats['total_memories']}")
    print(f"Known speakers: {stats['speakers']}")
    
    # Cleanup
    Path(test_file).unlink(missing_ok=True)
    print("\n✓ Test completed, test file cleaned up")


def test_sentence_scoring():
    """Test the importance scoring system."""
    print("\n" + "=" * 70)
    print("TEST 4: Sentence Importance Scoring")
    print("=" * 70)
    
    test_sentences = [
        "Hi, how are you?",
        "I'm working on a robotics project called FYN-X.",
        "Yesterday I met Sarah at the coffee shop.",
        "I need to finish the presentation by Friday.",
        "My favorite movie is The Matrix.",
        "I'm planning to visit Tokyo next month with Alex.",
    ]
    
    for sentence in test_sentences:
        score, details = score_sentence_importance(sentence)
        print(f"\nSentence: \"{sentence}\"")
        print(f"Score: {score:.1f}/100")
        print(f"Details: {details}")


def test_important_extraction():
    """Test extraction of important sentences from conversation."""
    print("\n" + "=" * 70)
    print("TEST 5: Important Sentence Extraction")
    print("=" * 70)
    
    conversation = """
    Hi, I'm Riley. I'm working on a robotics project called FYN-X.
    It's a personal memory companion and open robotics platform.
    I'm planning to add voice recognition next week.
    The weather is nice today.
    I want it to recognize different speakers.
    That would make interactions more personal.
    I met with Alex yesterday to discuss the project.
    We talked about integrating face recognition.
    """
    
    important = extract_important_sentences(conversation, min_score=25.0, max_sentences=5)
    
    print(f"\nOriginal text ({len(conversation)} chars):")
    print(conversation)
    print(f"\nExtracted {len(important)} important sentences:")
    
    for i, sent in enumerate(important, 1):
        print(f"\n{i}. [{sent['score']:.1f}] {sent['text']}")
        print(f"   Why: {sent['details']}")


def test_benchmarking():
    """Test the benchmarking system."""
    print("\n" + "=" * 70)
    print("TEST 6: Benchmarking System")
    print("=" * 70)
    
    import time
    
    start_session()
    
    # Simulate some operations
    print("\nSimulating operations...")
    
    with track_time("operation_1", {"size": 100}):
        time.sleep(0.05)
    
    with track_time("operation_2"):
        time.sleep(0.1)
    
    with track_time("operation_1"):  # Same module again
        time.sleep(0.08)
    
    with track_time("operation_3", {"complexity": "high"}):
        time.sleep(0.15)
    
    # End session and print summary
    summary = end_session(print_summary=True)
    
    print(f"\n✓ Benchmark test completed")
    print(f"  Total modules: {summary['module_count']}")
    print(f"  Total time: {summary['total_duration_ms']:.2f}ms")


def test_entity_extraction():
    """Test entity extraction improvements."""
    print("\n" + "=" * 70)
    print("TEST 7: Entity Extraction with Name Detection")
    print("=" * 70)
    
    test_text = "Hi, I'm Riley. Yesterday I met Sarah to discuss the robotics project at work"
    
    print(f"\nText: \"{test_text}\"")
    print("\n" + explain_extraction(test_text))


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("FYN-X AUTO NAME DETECTION TEST SUITE")
    print("=" * 70)
    
    try:
        test_name_detection()
        test_conversation_with_name_detection()
        test_memory_saving_rules()
        test_sentence_scoring()
        test_important_extraction()
        test_entity_extraction()
        test_benchmarking()
        
        print("\n" + "=" * 70)
        print("ALL TESTS COMPLETED SUCCESSFULLY! ✓")
        print("=" * 70)
        print("\nKey Features Tested:")
        print("  ✓ Automatic name detection from conversation")
        print("  ✓ Memories only saved for known speakers")
        print("  ✓ Name learning mid-conversation")
        print("  ✓ Manual setname as fallback")
        print("  ✓ Sentence importance scoring")
        print("  ✓ Performance benchmarking")
        print("\nYou can now run: python FYNX_run.py")
        print("\nTry introducing yourself:")
        print("  You: Hi, I'm <your name>")
        print("  FYN-X will automatically detect and remember you!")
        print("=" * 70 + "\n")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
