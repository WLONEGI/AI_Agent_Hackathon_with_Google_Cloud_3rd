"""
Design Compliance Tests Package

設計書準拠性テストモジュール
バックエンド実装が設計書要件に準拠していることを自動検証
"""

from .test_design_requirements import DesignRequirementsTest
from .test_phase_pipeline_compliance import PhasePipelineComplianceTest
from .test_hitl_compliance import HITLComplianceTest
from .test_architecture_patterns import ArchitecturePatternsTest

__all__ = [
    "DesignRequirementsTest",
    "PhasePipelineComplianceTest", 
    "HITLComplianceTest",
    "ArchitecturePatternsTest"
]