"""
Enhanced Voice Call Evaluations Analysis Tool - MongoDB Version
Provides comprehensive analysis of voice call evaluations stored in MongoDB
"""

import argparse
import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
import os
from dataclasses import dataclass
from collections import defaultdict
import statistics

# MongoDB imports - Import OID patch first for Pydantic v2 compatibility
from super_services.libs.core.model import *  # This applies the OID patch
from super_services.db.services import *  # This initializes the connection
from super_services.db.services.models.voice_evaluation import (
    CallSessionModel,
    ConversationTurnModel,
    CallEvaluationResultModel,
    CallQualityMetricsModel
)

# For audio playback
try:
    from pydub import AudioSegment
    from pydub.playback import play
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False


@dataclass
class SessionMetrics:
    """Container for session-level metrics"""
    session_id: str
    agent_id: str
    start_time: datetime
    duration: float = 0.0
    total_turns: int = 0
    avg_similarity: float = 0.0
    avg_relevancy: float = 0.0
    avg_completeness: float = 0.0
    avg_accuracy: float = 0.0
    overall_quality: float = 0.0
    avg_response_time: float = 0.0
    error_count: int = 0


class VoiceEvaluationAnalyzer:
    """Enhanced analyzer for voice call evaluation data using MongoDB"""

    def __init__(self):
        print("✅ VoiceEvaluationAnalyzer initialized with MongoDB")

    def format_evaluation_report(self, session_id: str = None) -> str:
        """Format evaluation results in a clean, tabular report"""
        # Get session details
        if session_id:
            session = CallSessionModel.get(session_id=session_id)
        else:
            # Get the most recent session
            sessions = list(CallSessionModel.find())
            if not sessions:
                return "No evaluation data found."
            sessions.sort(key=lambda x: x.call_start_time, reverse=True)
            session = sessions[0]
            session_id = session.session_id

        if not session:
            return "No evaluation data found for the specified session."

        # Get evaluation results
        evals = list(CallEvaluationResultModel.find(session_id=session_id))
        evals.sort(key=lambda x: x.turn_number)

        total_turns = len(evals)
        avg_similarity = sum(e.similarity or 0 for e in evals) / len(evals) if evals else 0
        avg_relevancy = sum(e.relevancy or 0 for e in evals) / len(evals) if evals else 0
        avg_completeness = sum(e.completeness or 0 for e in evals) / len(evals) if evals else 0
        avg_accuracy = sum(e.accuracy or 0 for e in evals) / len(evals) if evals else 0
        overall_quality = (avg_similarity + avg_relevancy + avg_accuracy + avg_completeness) / 4

        # Format the report
        report = []
        report.append("\n" + "="*100)
        report.append("VOICE AGENT EVALUATION REPORT".center(100))
        report.append("="*100)

        # Session header
        report.append(f"\n{'Session ID:':<20} {session_id}")
        report.append(f"{'Agent ID:':<20} {session.agent_id or 'N/A'}")
        report.append(f"{'Start Time:':<20} {datetime.fromtimestamp(session.call_start_time).strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"{'Total Turns:':<20} {total_turns}")
        report.append(f"{'Avg Resp Time:':<20} 0.00s")
        report.append("-"*100)

        # Summary scores
        report.append("\nSUMMARY METRICS".center(100))
        report.append("-"*100)
        report.append(f"{'Overall Quality:':<20} {overall_quality*100:.1f}%")
        report.append(f"{'Avg Similarity:':<20} {avg_similarity*100:.1f}%")
        report.append(f"{'Avg Relevancy:':<20} {avg_relevancy*100:.1f}%")
        report.append(f"{'Avg Completeness:':<20} {avg_completeness*100:.1f}%")
        report.append(f"{'Avg Accuracy:':<20} {avg_accuracy*100:.1f}%")

        # Evaluation details in tabular format
        report.append("\nDETAILED EVALUATION".center(100))
        report.append("-"*100)

        # Table header
        report.append("\n" + " | ".join([
            "Turn #".ljust(5),
            "User Question".ljust(40),
            "Eval Question".ljust(40),
            "Agent Reply".ljust(40),
            "Expected Output".ljust(40),
            "Sim".ljust(5),
            "Rel".ljust(5),
            "Comp".ljust(5),
            "Acc".ljust(5),
            "Keywords"
        ]))
        report.append("-" * 200)

        # Table rows
        for e in evals:
            keywords = e.matched_keywords or ""
            if keywords and isinstance(keywords, str):
                try:
                    kw_list = json.loads(keywords)
                    if isinstance(kw_list, list):
                        keywords = ", ".join(kw_list)
                except:
                    pass

            def truncate(text, length=35):
                if not text:
                    return ""
                return (text[:length-3] + '...') if len(str(text)) > length else str(text)

            sim_score = e.similarity or 0.0
            rel_score = e.relevancy or 0.0
            comp_score = e.completeness or 0.0
            acc_score = e.accuracy or 0.0

            report.append(" | ".join([
                str(e.turn_number).ljust(5),
                truncate(e.user_question, 35).ljust(40),
                truncate(e.eval_question, 35).ljust(40),
                truncate(e.agent_reply, 35).ljust(40),
                truncate(e.expected_output, 35).ljust(40),
                f"{sim_score*100:.0f}%".ljust(5),
                f"{rel_score*100:.0f}%".ljust(5),
                f"{comp_score*100:.0f}%".ljust(5),
                f"{acc_score*100:.0f}%".ljust(5),
                truncate(keywords, 15)
            ]))
            report.append("-" * 200)

        report.append("\n" + "="*100)
        return "\n".join(report)

    def get_single_session_metrics(self, session_id: str) -> Optional[SessionMetrics]:
        """Get metrics for a specific session"""
        session = CallSessionModel.get(session_id=session_id)
        if not session:
            return None

        # Get evaluation results
        evals = list(CallEvaluationResultModel.find(session_id=session_id))
        total_turns = len(evals)

        if evals:
            avg_similarity = sum(e.similarity or 0 for e in evals) / len(evals)
            avg_relevancy = sum(e.relevancy or 0 for e in evals) / len(evals)
            avg_completeness = sum(e.completeness or 0 for e in evals) / len(evals)
            avg_accuracy = sum(e.accuracy or 0 for e in evals) / len(evals)
            overall_quality = (avg_similarity + avg_relevancy + avg_completeness + avg_accuracy) / 4
        else:
            avg_similarity = avg_relevancy = avg_completeness = avg_accuracy = overall_quality = 0.0

        # Count low quality turns as errors
        error_count = sum(1 for e in evals if (
            (e.similarity or 0) < 0.5 or
            (e.relevancy or 0) < 0.5 or
            (e.completeness or 0) < 0.5 or
            (e.accuracy or 0) < 0.5
        ))

        return SessionMetrics(
            session_id=session_id,
            agent_id=session.agent_id or 'N/A',
            start_time=datetime.fromtimestamp(session.call_start_time) if session.call_start_time else datetime.now(),
            duration=session.duration or 0.0,
            total_turns=total_turns,
            avg_similarity=avg_similarity,
            avg_relevancy=avg_relevancy,
            avg_completeness=avg_completeness,
            avg_accuracy=avg_accuracy,
            overall_quality=overall_quality,
            avg_response_time=0.0,
            error_count=error_count
        )

    def get_session_metrics(self, session_id: str = None, agent_id: str = None, time_range: tuple = None) -> List[SessionMetrics]:
        """Get metrics for sessions"""
        query = {}

        if session_id:
            query["session_id"] = session_id
        if agent_id:
            query["agent_id"] = agent_id
        if time_range and len(time_range) == 2:
            start_date, end_date = time_range
            query["call_start_time"] = {
                "$gte": start_date.timestamp(),
                "$lte": end_date.timestamp()
            }

        sessions = list(CallSessionModel.find(query))
        result = []

        for session in sessions:
            metrics = self.get_single_session_metrics(session.session_id)
            if metrics:
                result.append(metrics)

        return result

    def get_quality_trends(self, agent_id: str = None, days: int = 30) -> Dict[str, Any]:
        """Get quality trends over time"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        sessions = self.get_session_metrics(
            agent_id=agent_id,
            time_range=(start_date, end_date)
        )

        if not sessions:
            return {
                'dates': [],
                'scores': [],
                'avg_score': 0,
                'total_sessions': 0
            }

        # Group by date
        date_scores = defaultdict(list)
        for session in sessions:
            if not session or not hasattr(session, 'start_time') or not hasattr(session, 'overall_quality'):
                continue

            date_str = session.start_time.strftime('%Y-%m-%d') if session.start_time else 'unknown'
            if session.overall_quality is not None:
                date_scores[date_str].append(session.overall_quality)

        if not date_scores:
            return {
                'dates': [],
                'scores': [],
                'avg_score': 0,
                'total_sessions': 0
            }

        # Sort dates and calculate daily averages
        sorted_dates = sorted(date_scores.keys())
        avg_scores = []

        for date in sorted_dates:
            scores = date_scores[date]
            if scores:
                avg_scores.append(statistics.mean(scores))
            else:
                avg_scores.append(0.0)

        return {
            'dates': sorted_dates,
            'scores': avg_scores,
            'avg_score': statistics.mean(avg_scores) if avg_scores else 0,
            'total_sessions': len(sessions)
        }

    def plot_quality_trends(self, agent_id: str = None, days: int = 30):
        """Plot quality trends over time"""
        trends = self.get_quality_trends(agent_id, days)

        if not trends['dates']:
            print("No data available for the selected criteria")
            return

        plt.figure(figsize=(12, 6))
        plt.plot(trends['dates'], trends['scores'], marker='o')
        plt.title(f"Voice Call Quality Trends{f' - Agent: {agent_id}' if agent_id else ''}")
        plt.xlabel('Date')
        plt.ylabel('Average Quality Score')
        plt.xticks(rotation=45)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.show()

    def export_to_csv(self, output_dir: str = "exports"):
        """Export all data to CSV files"""
        os.makedirs(output_dir, exist_ok=True)

        # Export sessions
        sessions = self.get_session_metrics()
        sessions_df = pd.DataFrame([
            {
                'session_id': s.session_id,
                'agent_id': s.agent_id,
                'start_time': s.start_time.isoformat(),
                'duration': s.duration,
                'total_turns': s.total_turns,
                'avg_similarity': s.avg_similarity,
                'avg_relevancy': s.avg_relevancy,
                'avg_completeness': s.avg_completeness,
                'avg_accuracy': s.avg_accuracy,
                'overall_quality': s.overall_quality,
                'avg_response_time': s.avg_response_time,
                'error_count': s.error_count
            }
            for s in sessions
        ])

        sessions_df.to_csv(f"{output_dir}/sessions.csv", index=False)
        print(f"Exported {len(sessions_df)} sessions to {output_dir}/sessions.csv")

    def close(self):
        """Close any connections (no-op for MongoDB with mongomantic)"""
        pass


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Analyze Voice Call Evaluations (MongoDB)")

    parser.add_argument("--agent", type=str, help="Filter by agent ID")
    parser.add_argument("--session-id", "--session", type=str, help="Show details for specific session")
    parser.add_argument("--list-sessions", action="store_true",
                       help="List all available sessions")
    parser.add_argument("--days", type=int, default=30,
                       help="Number of days of data to analyze")
    parser.add_argument("--export", action="store_true",
                       help="Export data to CSV")
    parser.add_argument("--output-dir", type=str, default="exports",
                       help="Directory to save exported files")
    parser.add_argument("--no-plot", action="store_true",
                       help="Disable plotting")
    parser.add_argument("--play-audio", action="store_true",
                       help="Play audio recording for session")

    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_args()

    try:
        analyzer = VoiceEvaluationAnalyzer()

        if args.list_sessions:
            sessions = analyzer.get_session_metrics()
            if not sessions:
                print("No sessions found.")
                return

            print("\nAvailable Sessions:")
            print("-" * 80)
            for i, session in enumerate(sessions, 1):
                print(f"{i}. {session.session_id} - {session.agent_id} - {session.start_time}")

        elif args.session_id:
            # Show the formatted evaluation report
            print(analyzer.format_evaluation_report(args.session_id))

        else:
            # Show quality trends
            print("\n Generating quality trends...")
            if not args.no_plot:
                analyzer.plot_quality_trends(agent_id=args.agent, days=args.days)
            else:
                trends = analyzer.get_quality_trends(agent_id=args.agent, days=args.days)
                print(f"\nQuality Trends (Last {args.days} days):")
                print(f"  Average Score: {trends['avg_score']:.2%}")
                print(f"  Total Sessions: {trends['total_sessions']}")

            # Export data if requested
            if args.export:
                analyzer.export_to_csv(args.output_dir)

    except Exception as e:
        print(f"\n Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if 'analyzer' in locals():
            analyzer.close()


if __name__ == "__main__":
    main()
