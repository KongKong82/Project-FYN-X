"""
Benchmarking utilities for FYN-X performance monitoring.
Tracks execution time of different modules to identify optimization opportunities.
"""

import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Callable
from datetime import datetime
from functools import wraps
from contextlib import contextmanager


class PerformanceTracker:
    """Tracks and logs performance metrics for FYN-X modules."""
    
    def __init__(self, log_file: str = "data/performance_log.json"):
        self.log_file = Path(log_file)
        self.current_session = []
        self.session_start = None
        
    def start_session(self):
        """Begin a new performance tracking session."""
        self.session_start = time.time()
        self.current_session = []
    
    def log_timing(self, module: str, duration: float, metadata: Optional[Dict] = None):
        """
        Log timing for a specific module.
        
        Args:
            module: Name of the module/function
            duration: Execution time in seconds
            metadata: Additional context (e.g., input size, memory count)
        """
        entry = {
            'module': module,
            'duration_ms': round(duration * 1000, 2),
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        self.current_session.append(entry)
    
    def end_session(self, save: bool = True) -> Dict:
        """
        End session and optionally save to file.
        
        Returns:
            Session summary with total time and module breakdown
        """
        if not self.session_start:
            return {}
        
        total_time = time.time() - self.session_start
        
        summary = {
            'session_timestamp': datetime.now().isoformat(),
            'total_duration_ms': round(total_time * 1000, 2),
            'module_count': len(self.current_session),
            'modules': self.current_session
        }
        
        if save:
            self._save_session(summary)
        
        return summary
    
    def _save_session(self, summary: Dict):
        """Append session summary to log file."""
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing logs
        if self.log_file.exists():
            with open(self.log_file, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = {'sessions': []}
        else:
            data = {'sessions': []}
        
        # Append new session
        data['sessions'].append(summary)
        
        # Keep only last 100 sessions to prevent file bloat
        data['sessions'] = data['sessions'][-100:]
        
        # Save
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def get_module_stats(self, module_name: str, last_n_sessions: int = 10) -> Dict:
        """
        Get statistics for a specific module across recent sessions.
        
        Returns:
            Dict with avg, min, max execution times
        """
        if not self.log_file.exists():
            return {}
        
        with open(self.log_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        sessions = data.get('sessions', [])[-last_n_sessions:]
        
        # Extract timings for this module
        timings = []
        for session in sessions:
            for module_entry in session.get('modules', []):
                if module_entry['module'] == module_name:
                    timings.append(module_entry['duration_ms'])
        
        if not timings:
            return {}
        
        return {
            'module': module_name,
            'count': len(timings),
            'avg_ms': round(sum(timings) / len(timings), 2),
            'min_ms': round(min(timings), 2),
            'max_ms': round(max(timings), 2),
            'total_ms': round(sum(timings), 2)
        }
    
    def print_session_summary(self, summary: Optional[Dict] = None):
        """Print a formatted summary of the current session."""
        if not summary:
            summary = self.end_session(save=False)
        
        if not summary:
            print("No session data available")
            return
        
        print("\n" + "=" * 60)
        print("PERFORMANCE SUMMARY")
        print("=" * 60)
        print(f"Total Time: {summary['total_duration_ms']:.2f}ms")
        print(f"Modules Called: {summary['module_count']}")
        print()
        
        # Group by module and sum durations
        module_totals = {}
        for entry in summary['modules']:
            module = entry['module']
            duration = entry['duration_ms']
            
            if module not in module_totals:
                module_totals[module] = {'total': 0, 'count': 0, 'calls': []}
            
            module_totals[module]['total'] += duration
            module_totals[module]['count'] += 1
            module_totals[module]['calls'].append(duration)
        
        # Sort by total time
        sorted_modules = sorted(
            module_totals.items(), 
            key=lambda x: x[1]['total'], 
            reverse=True
        )
        
        print("Module Breakdown:")
        print("-" * 60)
        for module, stats in sorted_modules:
            avg = stats['total'] / stats['count']
            pct = (stats['total'] / summary['total_duration_ms']) * 100
            print(f"{module:30} {stats['total']:8.2f}ms ({pct:5.1f}%) "
                  f"[{stats['count']} calls, avg: {avg:.2f}ms]")
        
        print("=" * 60 + "\n")


# Singleton instance
_tracker = PerformanceTracker()


@contextmanager
def track_time(module_name: str, metadata: Optional[Dict] = None):
    """
    Context manager for timing a code block.
    
    Usage:
        with track_time("memory_search", {"query_length": len(query)}):
            results = search_memories(query)
    """
    start = time.time()
    try:
        yield
    finally:
        duration = time.time() - start
        _tracker.log_timing(module_name, duration, metadata)


def timed(module_name: Optional[str] = None):
    """
    Decorator for timing function execution.
    
    Usage:
        @timed("ollama_inference")
        def run_model(prompt):
            return model.generate(prompt)
    """
    def decorator(func: Callable) -> Callable:
        name = module_name or func.__name__
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                _tracker.log_timing(name, duration)
        
        return wrapper
    return decorator


# Public API
def start_session():
    """Start a new performance tracking session."""
    _tracker.start_session()


def end_session(print_summary: bool = True) -> Dict:
    """End session and optionally print summary."""
    summary = _tracker.end_session(save=True)
    
    if print_summary and summary:
        _tracker.print_session_summary(summary)
    
    return summary


def get_module_stats(module_name: str, last_n: int = 10) -> Dict:
    """Get statistics for a specific module."""
    return _tracker.get_module_stats(module_name, last_n)


def print_all_module_stats(last_n: int = 10):
    """Print stats for all tracked modules."""
    if not _tracker.log_file.exists():
        print("No performance data available")
        return
    
    with open(_tracker.log_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    sessions = data.get('sessions', [])[-last_n:]
    
    # Collect all unique modules
    all_modules = set()
    for session in sessions:
        for entry in session.get('modules', []):
            all_modules.add(entry['module'])
    
    print("\n" + "=" * 80)
    print(f"MODULE STATISTICS (last {last_n} sessions)")
    print("=" * 80)
    
    for module in sorted(all_modules):
        stats = get_module_stats(module, last_n)
        if stats:
            print(f"{module:30} Avg: {stats['avg_ms']:7.2f}ms  "
                  f"Min: {stats['min_ms']:7.2f}ms  "
                  f"Max: {stats['max_ms']:7.2f}ms  "
                  f"({stats['count']} calls)")
    
    print("=" * 80 + "\n")


# Example usage
if __name__ == "__main__":
    # Example 1: Using context manager
    start_session()
    
    with track_time("test_module_1", {"size": 100}):
        time.sleep(0.1)
    
    with track_time("test_module_2"):
        time.sleep(0.05)
    
    with track_time("test_module_1"):  # Same module, different call
        time.sleep(0.12)
    
    summary = end_session(print_summary=True)
    
    # Example 2: Using decorator
    @timed("decorated_function")
    def slow_function():
        time.sleep(0.2)
        return "done"
    
    start_session()
    result = slow_function()
    end_session(print_summary=True)
