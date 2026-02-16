#!/usr/bin/env python3
"""
Example script to run task analysis on call data.

This script demonstrates how to use the analyze_and_export_calls function
to process call tasks from multiple run IDs and export the results to CSV.

Usage:
    python run_task_analysis.py
"""

from super_services.voice.analysis.task_analyser import (
    analyze_and_export_calls,
    analyze_and_export_calls_advanced
)


def main():
    """
    Main function to run the analysis.
    Update the run_ids list with your actual run IDs.
    """

    # Example 1: Basic usage
    print("=" * 80)
    print("EXAMPLE 1: Basic Analysis")
    print("=" * 80)

    # Replace these with your actual run IDs
    run_ids = [
        "Rb07b6d1Tb07b6d1",  # Replace with actual run ID
        # Add more run IDs here
    ]

    output_file = "call_analysis_report.csv"

    # Run the analysis
    stats = analyze_and_export_calls(
        run_ids=run_ids,
        output_csv_path=output_file
    )

    print(f"\nAnalysis complete! Results saved to: {output_file}")
    print(f"Statistics: {stats}")

    # Example 2: Advanced usage with filtering
    print("\n\n" + "=" * 80)
    print("EXAMPLE 2: Advanced Analysis with Filtering")
    print("=" * 80)

    # Only export calls with "Interested" or "Call Back" status
    stats_advanced = analyze_and_export_calls_advanced(
        run_ids=run_ids,
        output_csv_path="filtered_calls.csv",
        include_transcript=False,  # Set to True if you want full transcripts
        filter_by_status=["Interested", "Call Back"]  # Only these statuses
    )

    print(f"\nAdvanced analysis complete! Results saved to: filtered_calls.csv")
    print(f"Statistics: {stats_advanced}")

    # Example 3: With space_id filter
    print("\n\n" + "=" * 80)
    print("EXAMPLE 3: Analysis with Space ID Filter")
    print("=" * 80)

    stats_filtered = analyze_and_export_calls(
        run_ids=run_ids,
        output_csv_path="space_filtered_calls.csv",
        space_id="your_space_id_here"  # Replace with actual space ID if needed
    )

    print(f"\nFiltered analysis complete! Results saved to: space_filtered_calls.csv")
    print(f"Statistics: {stats_filtered}")


if __name__ == "__main__":
    main()