#!/usr/bin/env python3
"""Test script for mixed-language incident extraction and normalization."""

import json
import sys
from services.report_summarizer import extract_normalized_incident


def test_tamil_english_codeswitching():
    """Test Tamil + English code-switching normalization."""
    print("=" * 70)
    print("TEST 1: Tamil-English Code-Switching")
    print("=" * 70)
    
    transcript = "phone la battery drain aaguthu, mic work aagula, step up transformer short circuit aaduchi"
    
    print(f"\nInput Transcript:\n{transcript}\n")
    print("Processing with LLM normalization...")
    
    result = extract_normalized_incident(transcript)
    
    print(f"\n✓ Extraction completed ({result['provider']} - {result['latency_ms']}ms)\n")
    print("STRUCTURED OUTPUT:")
    print("-" * 70)
    print(f"Affected Device:      {result.get('affected_device', 'N/A')}")
    print(f"Primary Symptom:      {result.get('primary_symptom', 'N/A')}")
    print(f"Severity:             {result.get('severity', 'N/A')}")
    print(f"Recommended Action:   {result.get('recommended_action', 'N/A')}")
    print(f"Confidence:           {result['confidence']}")
    
    print("\nNORMALIZED STATEMENTS:")
    for i, stmt in enumerate(result.get('normalized_statements', []), 1):
        print(f"  {i}. {stmt}")
    
    print(f"\nCORE SUMMARY:\n{result['core_summary']}")
    print()


def test_complex_multilingual():
    """Test complex multi-issue scenario with mixed language."""
    print("=" * 70)
    print("TEST 2: Complex Multi-Issue Scenario")
    print("=" * 70)
    
    transcript = (
        "server la continuously CPU usage 95% ku mela poguthu, "
        "database connection pool exhaust aaiduchi, "
        "log files la out of memory error varuthu, "
        "service restart panna kooda same issue"
    )
    
    print(f"\nInput Transcript:\n{transcript}\n")
    print("Processing...")
    
    result = extract_normalized_incident(transcript)
    
    print(f"\n✓ Extraction completed ({result['provider']} - {result['latency_ms']}ms)\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print()


def test_english_only():
    """Test pure English input."""
    print("=" * 70)
    print("TEST 3: Pure English Input")
    print("=" * 70)
    
    transcript = (
        "The production server is experiencing intermittent connection timeouts, "
        "API response times have increased to 5+ seconds, "
        "clients are reporting HTTP 503 errors during peak hours"
    )
    
    print(f"\nInput Transcript:\n{transcript}\n")
    print("Processing...")
    
    result = extract_normalized_incident(transcript)
    
    print(f"\n✓ Extraction completed ({result['provider']} - {result['latency_ms']}ms)\n")
    print("Core Summary:")
    print(result['core_summary'])
    print(f"\nSeverity: {result.get('severity', 'N/A')} | Confidence: {result['confidence']}")
    print()


def test_single_statement():
    """Test single statement extraction."""
    print("=" * 70)
    print("TEST 4: Single Statement")
    print("=" * 70)
    
    transcript = "wifi router completely down, no connectivity"
    
    print(f"\nInput: {transcript}\n")
    
    result = extract_normalized_incident(transcript)
    
    print(f"✓ Provider: {result['provider']}")
    print(f"✓ Summary: {result['core_summary']}")
    print(f"✓ Confidence: {result['confidence']}\n")


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("INCIDENT EXTRACTION & NORMALIZATION TEST SUITE")
    print("=" * 70 + "\n")
    
    tests = [
        test_tamil_english_codeswitching,
        test_complex_multilingual,
        test_english_only,
        test_single_statement,
    ]
    
    for test_fn in tests:
        try:
            test_fn()
        except KeyboardInterrupt:
            print("\n\n⚠️  Tests interrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Test failed: {e}\n")
            continue
    
    print("=" * 70)
    print("ALL TESTS COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()
