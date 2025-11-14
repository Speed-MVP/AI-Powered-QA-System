#!/usr/bin/env python3
"""
Benchmarking Tool for AI Evaluation System
MVP Evaluation Improvements - Phase 3

Compares AI evaluations against human-reviewed gold labels to measure:
- Overall score alignment (correlation)
- Category-level accuracy
- Violation precision & recall
- Human review rate
- Confidence score calibration

Usage:
    python tools/benchmark.py --input gold_labels.csv --output benchmark_results.json --html benchmark_report.html
"""

import json
import csv
import argparse
import statistics
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import sys
import os

# Add backend directory to path for imports
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from app.database import SessionLocal
from app.models.evaluation import Evaluation
from app.models.human_review import HumanReview
from app.models.category_score import CategoryScore
from app.models.recording import Recording
from app.models.rule_engine_results import RuleEngineResults


class BenchmarkTool:
    """
    Comprehensive benchmarking tool for AI evaluation system.
    Measures accuracy, precision, recall, and other metrics against human reviews.
    """

    def __init__(self):
        self.db = SessionLocal()
        self.results = {
            "metadata": {
                "run_timestamp": datetime.utcnow().isoformat(),
                "tool_version": "1.0",
                "total_evaluations": 0,
                "total_human_reviews": 0
            },
            "metrics": {},
            "category_analysis": {},
            "violation_analysis": {},
            "confidence_analysis": {},
            "recommendations": []
        }

    def load_gold_labels(self, csv_path: str) -> List[Dict[str, Any]]:
        """
        Load gold labels from CSV file.

        Expected CSV format:
        recording_id,human_overall_score,human_category_scores_json,human_violations_json,notes
        """
        gold_labels = []

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                gold_label = {
                    "recording_id": row["recording_id"],
                    "human_overall_score": float(row["human_overall_score"]) if row.get("human_overall_score") else None,
                    "human_category_scores": json.loads(row.get("human_category_scores_json", "{}")),
                    "human_violations": json.loads(row.get("human_violations_json", "[]")),
                    "notes": row.get("notes", "")
                }
                gold_labels.append(gold_label)

        print(f"Loaded {len(gold_labels)} gold label entries from {csv_path}")
        return gold_labels

    def run_benchmark(self, gold_labels: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run complete benchmark analysis comparing AI vs human evaluations.
        """
        print(f"Starting benchmark analysis for {len(gold_labels)} evaluations...")

        # Analyze each evaluation
        benchmark_data = []
        for gold_label in gold_labels:
            evaluation_data = self._analyze_single_evaluation(gold_label)
            if evaluation_data:
                benchmark_data.append(evaluation_data)

        self.results["metadata"]["total_evaluations"] = len(benchmark_data)

        # Compute aggregate metrics
        self._compute_overall_metrics(benchmark_data)
        self._compute_category_metrics(benchmark_data)
        self._compute_violation_metrics(benchmark_data)
        self._compute_confidence_metrics(benchmark_data)
        self._generate_recommendations(benchmark_data)

        print("Benchmark analysis complete!")
        return self.results

    def _analyze_single_evaluation(self, gold_label: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Analyze a single evaluation against its gold label.
        """
        recording_id = gold_label["recording_id"]

        # Get AI evaluation
        evaluation = self.db.query(Evaluation).filter(
            Evaluation.recording_id == recording_id
        ).first()

        if not evaluation:
            print(f"Warning: No AI evaluation found for recording {recording_id}")
            return None

        # Get human review if it exists (optional for gold labels)
        human_review = self.db.query(HumanReview).filter(
            HumanReview.evaluation_id == evaluation.id
        ).first()

        # Get category scores
        ai_category_scores = {cs.category_name: cs.score for cs in evaluation.category_scores}

        # Get rule engine results
        rule_results = self.db.query(RuleEngineResults).filter(
            RuleEngineResults.evaluation_id == evaluation.id
        ).first()

        # Build analysis data
        analysis = {
            "recording_id": recording_id,
            "evaluation_id": evaluation.id,
            "ai_overall_score": evaluation.overall_score,
            "human_overall_score_gold": gold_label["human_overall_score"],
            "ai_category_scores": ai_category_scores,
            "human_category_scores_gold": gold_label["human_category_scores"],
            "ai_violations": evaluation.llm_analysis.get("violations", []) if evaluation.llm_analysis else [],
            "human_violations_gold": gold_label["human_violations"],
            "confidence_score": evaluation.confidence_score,
            "requires_human_review": evaluation.requires_human_review,
            "rule_engine_results": rule_results.rules if rule_results else {},
            "has_human_review": human_review is not None,
            "evaluation_status": evaluation.status.value if hasattr(evaluation.status, 'value') else str(evaluation.status)
        }

        # Add human review data if available
        if human_review:
            analysis.update({
                "human_overall_score_actual": human_review.human_overall_score,
                "human_category_scores_actual": human_review.human_category_scores,
                "human_violations_actual": human_review.human_violations,
                "ai_human_delta": human_review.delta
            })

        return analysis

    def _compute_overall_metrics(self, benchmark_data: List[Dict[str, Any]]) -> None:
        """
        Compute overall performance metrics.
        """
        if not benchmark_data:
            return

        # Overall score correlation and accuracy
        ai_scores = []
        human_scores_gold = []
        human_scores_actual = []

        for data in benchmark_data:
            if data["ai_overall_score"] is not None:
                ai_scores.append(data["ai_overall_score"])

                if data["human_overall_score_gold"] is not None:
                    human_scores_gold.append(data["human_overall_score_gold"])

                if data.get("human_overall_score_actual") is not None:
                    human_scores_actual.append(data["human_overall_score_actual"])

        # Calculate correlation if we have enough data
        overall_correlation = None
        if len(ai_scores) >= 10 and len(human_scores_gold) >= 10:
            try:
                overall_correlation = statistics.correlation(ai_scores[:len(human_scores_gold)], human_scores_gold)
            except statistics.StatisticsError:
                overall_correlation = None

        # Mean absolute error
        mae_gold = None
        mae_actual = None

        if len(ai_scores) == len(human_scores_gold):
            errors = [abs(ai - human) for ai, human in zip(ai_scores, human_scores_gold)]
            mae_gold = statistics.mean(errors)

        if len(ai_scores) == len(human_scores_actual):
            errors = [abs(ai - human) for ai, human in zip(ai_scores, human_scores_actual)]
            mae_actual = statistics.mean(errors)

        # Human review rate
        human_review_rate = sum(1 for data in benchmark_data if data["requires_human_review"]) / len(benchmark_data)

        self.results["metrics"]["overall"] = {
            "total_evaluations": len(benchmark_data),
            "correlation_coefficient": overall_correlation,
            "mean_absolute_error_vs_gold": mae_gold,
            "mean_absolute_error_vs_actual": mae_actual,
            "human_review_rate": human_review_rate,
            "correlation_interpretation": self._interpret_correlation(overall_correlation)
        }

    def _compute_category_metrics(self, benchmark_data: List[Dict[str, Any]]) -> None:
        """
        Compute per-category performance metrics.
        """
        category_metrics = {}

        # Collect all categories
        all_categories = set()
        for data in benchmark_data:
            all_categories.update(data["ai_category_scores"].keys())
            all_categories.update(data["human_category_scores_gold"].keys())

        for category in sorted(all_categories):
            ai_scores = []
            human_scores_gold = []

            for data in benchmark_data:
                ai_score = data["ai_category_scores"].get(category)
                human_score = data["human_category_scores_gold"].get(category)

                if ai_score is not None and human_score is not None:
                    ai_scores.append(ai_score)
                    human_scores_gold.append(human_score)

            if len(ai_scores) >= 5:  # Need minimum data for meaningful analysis
                try:
                    correlation = statistics.correlation(ai_scores, human_scores_gold)
                    mae = statistics.mean([abs(ai - human) for ai, human in zip(ai_scores, human_scores_gold)])

                    category_metrics[category] = {
                        "correlation": correlation,
                        "mean_absolute_error": mae,
                        "sample_size": len(ai_scores),
                        "correlation_interpretation": self._interpret_correlation(correlation)
                    }
                except statistics.StatisticsError:
                    category_metrics[category] = {
                        "correlation": None,
                        "mean_absolute_error": None,
                        "sample_size": len(ai_scores),
                        "error": "insufficient_data"
                    }

        self.results["category_analysis"] = category_metrics

    def _compute_violation_metrics(self, benchmark_data: List[Dict[str, Any]]) -> None:
        """
        Compute violation detection precision and recall.
        """
        total_ai_violations = 0
        total_human_violations = 0
        true_positives = 0
        false_positives = 0
        false_negatives = 0

        for data in benchmark_data:
            ai_violations = data["ai_violations"]
            human_violations = data["human_violations_gold"]

            total_ai_violations += len(ai_violations)
            total_human_violations += len(human_violations)

            # Simple overlap-based matching (can be improved with fuzzy matching)
            ai_violation_types = {v.get("rule_id", str(v)) for v in ai_violations}
            human_violation_types = {v.get("rule_id", str(v)) for v in human_violations}

            # Calculate matches
            matches = ai_violation_types & human_violation_types
            true_positives += len(matches)
            false_positives += len(ai_violation_types - matches)
            false_negatives += len(human_violation_types - matches)

        # Calculate precision and recall
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        self.results["violation_analysis"] = {
            "total_ai_violations": total_ai_violations,
            "total_human_violations": total_human_violations,
            "true_positives": true_positives,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "precision_interpretation": self._interpret_precision(precision),
            "recall_interpretation": self._interpret_recall(recall)
        }

    def _compute_confidence_metrics(self, benchmark_data: List[Dict[str, Any]]) -> None:
        """
        Analyze confidence score calibration and human review routing.
        """
        confidence_levels = []
        actually_needed_review = []
        was_flagged_for_review = []

        for data in benchmark_data:
            confidence = data["confidence_score"]
            if confidence is not None:
                confidence_levels.append(confidence)
                was_flagged_for_review.append(data["requires_human_review"])

                # Determine if review was actually needed (significant discrepancy)
                ai_score = data["ai_overall_score"]
                human_score = data["human_overall_score_gold"]
                if ai_score is not None and human_score is not None:
                    discrepancy = abs(ai_score - human_score)
                    actually_needed_review.append(discrepancy > 10)  # >10 point difference
                else:
                    actually_needed_review.append(False)

        if confidence_levels:
            # Confidence distribution
            confidence_distribution = {
                "high_confidence": sum(1 for c in confidence_levels if c >= 0.8),
                "medium_confidence": sum(1 for c in confidence_levels if 0.5 <= c < 0.8),
                "low_confidence": sum(1 for c in confidence_levels if c < 0.5)
            }

            # Review routing accuracy
            correctly_flagged = 0
            incorrectly_flagged = 0
            missed_reviews = 0

            for flagged, needed in zip(was_flagged_for_review, actually_needed_review):
                if flagged and needed:
                    correctly_flagged += 1
                elif flagged and not needed:
                    incorrectly_flagged += 1
                elif not flagged and needed:
                    missed_reviews += 1

            total_reviews = len([x for x in actually_needed_review if x])
            review_precision = correctly_flagged / (correctly_flagged + incorrectly_flagged) if (correctly_flagged + incorrectly_flagged) > 0 else 0
            review_recall = correctly_flagged / total_reviews if total_reviews > 0 else 0

            self.results["confidence_analysis"] = {
                "confidence_distribution": confidence_distribution,
                "review_routing": {
                    "correctly_flagged": correctly_flagged,
                    "incorrectly_flagged": incorrectly_flagged,
                    "missed_reviews": missed_reviews,
                    "review_precision": review_precision,
                    "review_recall": review_recall
                },
                "average_confidence": statistics.mean(confidence_levels) if confidence_levels else None,
                "confidence_std_dev": statistics.stdev(confidence_levels) if len(confidence_levels) >= 2 else None
            }

    def _generate_recommendations(self, benchmark_data: List[Dict[str, Any]]) -> None:
        """
        Generate actionable recommendations based on benchmark results.
        """
        recommendations = []

        # Overall correlation recommendations
        overall_metrics = self.results["metrics"].get("overall", {})
        correlation = overall_metrics.get("correlation_coefficient")

        if correlation is None or correlation < 0.5:
            recommendations.append({
                "priority": "high",
                "category": "correlation",
                "issue": "Low correlation between AI and human scores",
                "recommendation": "Review prompt engineering and few-shot examples. Consider collecting more human reviews for better training data.",
                "metric": f"Correlation: {correlation:.3f}" if correlation else "Correlation: N/A"
            })

        # Human review rate recommendations
        review_rate = overall_metrics.get("human_review_rate", 0)
        if review_rate > 0.4:
            recommendations.append({
                "priority": "high",
                "category": "review_rate",
                "issue": "High human review rate indicates poor AI confidence",
                "recommendation": "Tune confidence engine thresholds or improve AI accuracy to reduce manual review burden.",
                "metric": f"Review rate: {review_rate:.1%}"
            })

        # Violation detection recommendations
        violation_metrics = self.results["violation_analysis"]
        precision = violation_metrics.get("precision", 0)
        recall = violation_metrics.get("recall", 0)

        if precision < 0.7:
            recommendations.append({
                "priority": "medium",
                "category": "violation_precision",
                "issue": "Low precision in violation detection (too many false positives)",
                "recommendation": "Adjust rule engine thresholds or improve violation detection logic.",
                "metric": f"Precision: {precision:.3f}"
            })

        if recall < 0.7:
            recommendations.append({
                "priority": "medium",
                "category": "violation_recall",
                "issue": "Low recall in violation detection (missing violations)",
                "recommendation": "Review rule engine patterns and consider adding more violation detection rules.",
                "metric": f"Recall: {recall:.3f}"
            })

        # Category-specific recommendations
        category_metrics = self.results["category_analysis"]
        poor_categories = [
            cat for cat, metrics in category_metrics.items()
            if metrics.get("correlation", 1.0) < 0.5
        ]

        if poor_categories:
            recommendations.append({
                "priority": "medium",
                "category": "category_performance",
                "issue": f"Poor performance in categories: {', '.join(poor_categories)}",
                "recommendation": "Review rubric definitions and scoring logic for these categories. Consider category-specific prompt adjustments.",
                "metric": f"Categories with correlation < 0.5: {len(poor_categories)}"
            })

        self.results["recommendations"] = recommendations

    def _interpret_correlation(self, correlation: Optional[float]) -> str:
        """Interpret correlation coefficient."""
        if correlation is None:
            return "insufficient_data"
        elif correlation >= 0.8:
            return "excellent"
        elif correlation >= 0.6:
            return "good"
        elif correlation >= 0.4:
            return "fair"
        elif correlation >= 0.2:
            return "poor"
        else:
            return "very_poor"

    def _interpret_precision(self, precision: float) -> str:
        """Interpret precision score."""
        if precision >= 0.8:
            return "excellent"
        elif precision >= 0.7:
            return "good"
        elif precision >= 0.6:
            return "fair"
        elif precision >= 0.5:
            return "poor"
        else:
            return "very_poor"

    def _interpret_recall(self, recall: float) -> str:
        """Interpret recall score."""
        return self._interpret_precision(recall)  # Same scale

    def save_results(self, json_path: str, html_path: Optional[str] = None) -> None:
        """
        Save benchmark results to JSON file and optionally generate HTML report.
        """
        # Save JSON
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, default=str)

        print(f"Benchmark results saved to {json_path}")

        # Generate HTML report if requested
        if html_path:
            self._generate_html_report(html_path)
            print(f"HTML report generated at {html_path}")

    def _generate_html_report(self, html_path: str) -> None:
        """
        Generate a comprehensive HTML report with charts and visualizations.
        """
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>AI Evaluation Benchmark Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .metric {{ background: #f0f0f0; padding: 20px; margin: 10px 0; border-radius: 5px; }}
        .excellent {{ color: #28a745; }}
        .good {{ color: #17a2b8; }}
        .fair {{ color: #ffc107; }}
        .poor {{ color: #fd7e14; }}
        .very-poor {{ color: #dc3545; }}
        .recommendation {{ border-left: 4px solid #007bff; padding-left: 15px; margin: 10px 0; }}
        .high {{ border-color: #dc3545; }}
        .medium {{ border-color: #ffc107; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>AI Evaluation Benchmark Report</h1>
    <p><strong>Generated:</strong> {self.results['metadata']['run_timestamp']}</p>
    <p><strong>Total Evaluations:</strong> {self.results['metadata']['total_evaluations']}</p>

    <h2>Overall Performance</h2>
    <div class="metric">
        <h3>Correlation Analysis</h3>
        <p>Correlation Coefficient: <span class="{self._interpret_correlation(self.results['metrics'].get('overall', {}).get('correlation_coefficient'))}">{self.results['metrics'].get('overall', {}).get('correlation_coefficient', 'N/A')}</span></p>
        <p>Mean Absolute Error vs Gold Labels: {self.results['metrics'].get('overall', {}).get('mean_absolute_error_vs_gold', 'N/A'):.2f if self.results['metrics'].get('overall', {}).get('mean_absolute_error_vs_gold') else 'N/A'}</p>
        <p>Human Review Rate: {self.results['metrics'].get('overall', {}).get('human_review_rate', 0):.1%}</p>
    </div>

    <h2>Category Performance</h2>
    <table>
        <tr><th>Category</th><th>Correlation</th><th>MAE</th><th>Sample Size</th></tr>
        {"".join(f"<tr><td>{cat}</td><td>{metrics.get('correlation', 'N/A'):.3f if metrics.get('correlation') else 'N/A'}</td><td>{metrics.get('mean_absolute_error', 'N/A'):.2f if metrics.get('mean_absolute_error') else 'N/A'}</td><td>{metrics.get('sample_size', 0)}</td></tr>" for cat, metrics in self.results['category_analysis'].items())}
    </table>

    <h2>Violation Detection</h2>
    <div class="metric">
        <p>Precision: <span class="{self._interpret_precision(self.results['violation_analysis'].get('precision', 0))}">{self.results['violation_analysis'].get('precision', 0):.3f}</span></p>
        <p>Recall: <span class="{self._interpret_precision(self.results['violation_analysis'].get('recall', 0))}">{self.results['violation_analysis'].get('recall', 0):.3f}</span></p>
        <p>F1 Score: {self.results['violation_analysis'].get('f1_score', 0):.3f}</p>
    </div>

    <h2>Recommendations</h2>
    {"".join(f'<div class="recommendation {rec["priority"]}"><h4>{rec["issue"]}</h4><p>{rec["recommendation"]}</p><p><em>{rec["metric"]}</em></p></div>' for rec in self.results['recommendations'])}
</body>
</html>
        """

        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)


def main():
    parser = argparse.ArgumentParser(description="Benchmark AI evaluation system against human reviews")
    parser.add_argument("--input", required=True, help="Path to CSV file with gold labels")
    parser.add_argument("--output", default="benchmark_results.json", help="Output JSON file path")
    parser.add_argument("--html", help="Generate HTML report at specified path")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    # Validate input file exists
    if not Path(args.input).exists():
        print(f"Error: Input file {args.input} does not exist")
        return 1

    try:
        # Run benchmark
        tool = BenchmarkTool()
        gold_labels = tool.load_gold_labels(args.input)
        results = tool.run_benchmark(gold_labels)
        tool.save_results(args.output, args.html)

        print("\nBenchmark completed successfully!")
        print(f"Results saved to: {args.output}")
        if args.html:
            print(f"HTML report saved to: {args.html}")

        return 0

    except Exception as e:
        print(f"Error running benchmark: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
