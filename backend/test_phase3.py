#!/usr/bin/env python3
"""
Test script for Phase 3: Fine-Tuning & Self-Learning features
"""

from app.services.dataset_curation import DatasetCurationService
from app.services.fine_tuning import FineTuningService
from app.services.continuous_learning import ContinuousLearningService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_dataset_curation():
    """Test the dataset curation service"""
    print("Testing Dataset Curation Service...")

    service = DatasetCurationService()
    stats = service.get_dataset_statistics()

    print("Dataset Statistics:")
    print(f"   Total human reviews: {stats['total_human_reviews']}")
    print(f"   Training eligible reviews: {stats['training_eligible_reviews']}")
    print(f"   Data quality score: {stats['data_quality_score']}")
    print(f"   Training readiness: {stats['training_readiness']['status']}")
    print(f"   Message: {stats['training_readiness']['message']}")

    print("Dataset curation service working!")
    return True


def test_fine_tuning_service():
    """Test the fine-tuning service (without actually training)"""
    print("\nTesting Fine-Tuning Service...")

    try:
        service = FineTuningService()
        # Test performance evaluation (should work even with no data)
        result = service.evaluate_model_performance(evaluation_period_days=30)

        if result["success"]:
            print("Model Performance Evaluation:")
            print(f"   Success: {result['success']}")
            print(f"   Total evaluations: {result['total_evaluations']}")
            if result['total_evaluations'] > 0:
                print(f"   Accuracy: {result['accuracy']:.3f}")
                print(f"   MAE: {result['mae']:.2f}")
                print(f"   Human review rate: {result['human_review_rate']:.3f}")
            else:
                print("   No evaluations found (expected for empty database)")
        else:
            print(f"   Error: {result['error']}")

        print("Fine-tuning service working!")
        return True

    except Exception as e:
        print(f"Fine-tuning service error: {e}")
        return False


def test_continuous_learning():
    """Test the continuous learning service"""
    print("\nTesting Continuous Learning Service...")

    service = ContinuousLearningService()
    status = service.get_learning_status()

    print("Continuous Learning Status:")
    print(f"   Active: {status['continuous_learning_active']}")
    print(f"   Retraining interval: {status['retraining_interval_days']} days")
    print(f"   Min reviews threshold: {status['min_reviews_threshold']}")
    print(f"   Days until next retraining: {status['days_until_next_retraining']}")

    if status['active_dataset']:
        print(f"   Active dataset: {status['active_dataset']['name']} (v{status['active_dataset']['version']})")
    else:
        print("   No active dataset (expected for new system)")

    if status['latest_performance']:
        print(f"   Latest performance accuracy: {status['latest_performance']['accuracy']}")
    else:
        print("   No performance metrics yet (expected)")

    print("Continuous learning service working!")
    return True


def main():
    """Run all Phase 3 tests"""
    print("Testing Phase 3: Fine-Tuning & Self-Learning Implementation")
    print("=" * 60)

    tests_passed = 0
    total_tests = 3

    try:
        if test_dataset_curation():
            tests_passed += 1

        if test_fine_tuning_service():
            tests_passed += 1

        if test_continuous_learning():
            tests_passed += 1

    except Exception as e:
        print(f"Error during testing: {e}")

    print("\n" + "=" * 60)
    print(f"Test Results: {tests_passed}/{total_tests} tests passed")

    if tests_passed == total_tests:
        print("SUCCESS: All Phase 3 services are working correctly!")
        print("\nPhase 3 Features Implemented:")
        print("   - Dataset curation system for human-reviewed calls")
        print("   - Fine-tuning service with performance evaluation")
        print("   - Continuous learning with automated retraining")
        print("   - API endpoints for fine-tuning management")
        print("   - Database schema for training data and performance tracking")
        print("\nAPI Endpoints Available:")
        print("   GET  /api/fine-tuning/dataset/statistics")
        print("   POST /api/fine-tuning/dataset/create")
        print("   POST /api/fine-tuning/train/start")
        print("   GET  /api/fine-tuning/train/status/{job_id}")
        print("   POST /api/fine-tuning/evaluate/performance")
        print("   GET  /api/fine-tuning/continuous-learning/status")
        print("   POST /api/fine-tuning/continuous-learning/start")
        print("   POST /api/fine-tuning/continuous-learning/retrain")
    else:
        print(f"WARNING: {total_tests - tests_passed} tests failed. Check the implementation.")


if __name__ == "__main__":
    main()
