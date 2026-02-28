#!/usr/bin/env python3
"""Test script for executive-grade report analysis.

Usage:
    python test_executive_analysis.py [report_file.md]
    
If no report file is specified, uses the latest report from backend/reports/
"""

import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from services.report_summarizer import analyse_executive_report


def main():
    # Determine which report to analyze
    if len(sys.argv) > 1:
        report_path = Path(sys.argv[1])
    else:
        # Find latest report
        reports_dir = Path(__file__).parent / "reports"
        md_files = sorted(reports_dir.glob("CLARA-*.md"), reverse=True)
        if not md_files:
            print("No report files found in backend/reports/")
            return 1
        report_path = md_files[0]
    
    if not report_path.exists():
        print(f"Report file not found: {report_path}")
        return 1
    
    print(f"Analyzing report: {report_path.name}")
    print("=" * 70)
    
    # Read report
    report_text = report_path.read_text(encoding="utf-8")
    
    # Perform executive analysis
    print("\nPerforming executive-grade analysis...\n")
    result = analyse_executive_report(report_text)
    
    # Display results
    print("ANALYSIS RESULT:")
    print("=" * 70)
    print(json.dumps({
        "core_summary": result["core_summary"],
        "confidence": result["confidence"]
    }, indent=2))
    print("=" * 70)
    
    print(f"\nProvider: {result['provider']}")
    print(f"Model: {result['model']}")
    print(f"Latency: {result['latency_ms']}ms")
    print(f"Fallback used: {result['fallback_used']}")
    
    # Also save JSON to file
    output_file = report_path.with_suffix('.executive_analysis.json')
    output_file.write_text(
        json.dumps(result, indent=2),
        encoding="utf-8"
    )
    print(f"\nFull analysis saved to: {output_file.name}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
