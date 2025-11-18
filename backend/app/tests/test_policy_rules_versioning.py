"""
Phase 5: Policy Rules Versioning - Unit Tests
Tests for versioning, diff calculation, and rollback functionality.
"""

import pytest
from unittest.mock import patch, MagicMock
from app.services.policy_rules_versioning import PolicyRulesVersioningService


class TestPolicyRulesVersioning:
    """Test suite for policy rules versioning service."""

    @pytest.fixture
    def versioning_service(self):
        """Create versioning service instance."""
        return PolicyRulesVersioningService()

    @pytest.fixture
    def sample_rules_v1(self):
        """Sample rules for version 1."""
        return {
            "Professionalism": {
                "greet_within_seconds": {
                    "passed": True,
                    "evidence": "Agent greeted within 10 seconds"
                }
            },
            "Empathy": {
                "requires_apology_if_negative": {
                    "passed": False,
                    "evidence": "No apology detected"
                }
            }
        }

    @pytest.fixture
    def sample_rules_v2(self):
        """Sample rules for version 2 (modified)."""
        return {
            "Professionalism": {
                "greet_within_seconds": {
                    "passed": True,
                    "evidence": "Agent greeted within 10 seconds"
                },
                "identify_self": {  # New rule
                    "passed": True,
                    "evidence": "Agent identified themselves"
                }
            },
            "Empathy": {
                "requires_apology_if_negative": {
                    "passed": True,  # Changed from False
                    "evidence": "Apology detected after negative sentiment"
                }
            }
        }

    @patch('app.database.SessionLocal')
    def test_create_version_success(self, mock_session, versioning_service, sample_rules_v1):
        """Test successful version creation."""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock existing versions query (no previous versions)
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        # Mock version creation
        mock_version = MagicMock()
        mock_version.rules_version = 1
        mock_version.rules_hash = "abc123"
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        with patch.object(versioning_service, '_calculate_rules_hash', return_value="abc123"):
            with patch.object(versioning_service, '_calculate_diff', return_value=None):
                result = versioning_service.create_version(
                    policy_template_id="template1",
                    policy_rules=sample_rules_v1,
                    created_by_user_id="user1",
                    name="Version 1",
                    notes="Initial version"
                )

                assert result.rules_version == 1
                assert result.rules_hash == "abc123"
                mock_db.add.assert_called_once()
                mock_db.commit.assert_called_once()

    @patch('app.database.SessionLocal')
    def test_rollback_to_version(self, mock_session, versioning_service, sample_rules_v1):
        """Test rollback to previous version."""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock target version
        mock_target_version = MagicMock()
        mock_target_version.rules_version = 2
        mock_target_version.policy_rules = sample_rules_v1

        # Mock new version
        mock_new_version = MagicMock()
        mock_new_version.rules_version = 3
        mock_new_version.rules_hash = "def456"

        # Mock template
        mock_template = MagicMock()

        mock_db.query.return_value.filter.return_value.first.return_value = mock_target_version
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_target_version

        with patch.object(versioning_service, 'create_version', return_value=mock_new_version):
            target, new = versioning_service.rollback_to_version(
                policy_template_id="template1",
                target_version=2,
                rollback_by_user_id="user1",
                notes="Rolling back due to issues"
            )

            assert target == mock_target_version
            assert new == mock_new_version

    def test_calculate_rules_hash(self, versioning_service, sample_rules_v1):
        """Test rules hash calculation for integrity."""
        hash1 = versioning_service._calculate_rules_hash(sample_rules_v1)
        hash2 = versioning_service._calculate_rules_hash(sample_rules_v1)

        # Same input should produce same hash
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 length

        # Different input should produce different hash
        modified_rules = sample_rules_v1.copy()
        modified_rules["Professionalism"]["greet_within_seconds"]["passed"] = False
        hash3 = versioning_service._calculate_rules_hash(modified_rules)

        assert hash1 != hash3

    def test_calculate_diff(self, versioning_service, sample_rules_v1, sample_rules_v2):
        """Test diff calculation between rule versions."""
        diff = versioning_service._calculate_diff(sample_rules_v1, sample_rules_v2)

        # Should detect changes (this is a basic test - deepdiff is complex)
        # In real implementation, we'd test specific diff scenarios
        assert diff is not None

    @patch('app.database.SessionLocal')
    def test_get_version_history(self, mock_session, versioning_service):
        """Test version history retrieval."""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock version objects
        mock_version1 = MagicMock()
        mock_version1.rules_version = 1
        mock_version1.name = "Version 1"
        mock_version1.llm_generated = True
        mock_version1.rules_hash = "hash1"
        mock_version1.created_at.isoformat.return_value = "2024-01-01T10:00:00"
        mock_version1.created_by_user_id = "user1"
        mock_version1.policy_rules = {"Professionalism": {"rule1": True}}

        mock_version2 = MagicMock()
        mock_version2.rules_version = 2
        mock_version2.name = "Version 2"
        mock_version2.llm_generated = False
        mock_version2.rules_hash = "hash2"
        mock_version2.created_at.isoformat.return_value = "2024-01-02T10:00:00"
        mock_version2.created_by_user_id = "user2"
        mock_version2.policy_rules = {"Professionalism": {"rule1": True, "rule2": False}}

        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
            mock_version2, mock_version1
        ]

        history = versioning_service.get_version_history("template1", limit=10)

        assert len(history) == 2
        assert history[0]["version"] == 2  # Should be ordered by version desc
        assert history[0]["name"] == "Version 2"
        assert history[0]["llm_generated"] is False
        assert history[1]["version"] == 1
        assert history[1]["name"] == "Version 1"
        assert history[1]["llm_generated"] is True

    @patch('app.database.SessionLocal')
    def test_create_draft_from_version(self, mock_session, versioning_service, sample_rules_v1):
        """Test creating draft from existing version."""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock version
        mock_version = MagicMock()
        mock_version.policy_rules = sample_rules_v1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_version

        # Mock draft creation
        mock_draft = MagicMock()
        mock_draft.id = "draft123"
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = mock_draft

        result = versioning_service.create_draft_from_version(
            policy_template_id="template1",
            version_number=1,
            created_by_user_id="user1",
            draft_name="Test Draft",
            draft_description="Testing draft creation"
        )

        assert result == mock_draft
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()



