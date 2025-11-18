"""
Risk Assessor for Risk Agent Analyzer

Evaluates risk levels and makes assessment decisions.
"""

import logging
from typing import Dict, Any, List
from ..utilities.data_structures import RiskLevel, QualityClassification

class RiskAssessor:
    """Assesses risk levels for PRs and repositories"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the risk assessor"""
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def determine_pr_risk_level(self, pr_data: Dict[str, Any]) -> str:

        """Determine risk level for a single PR"""
        risk_score = 0
        
        # File change risk - handle both list and int types
        files_changed_raw = pr_data.get('changed_files', 0)
        if isinstance(files_changed_raw, list):
            files_changed = len(files_changed_raw)
        elif isinstance(files_changed_raw, (int, float)):
            files_changed = int(files_changed_raw)
        else:
            files_changed = 0
            
        if files_changed > 20:
            risk_score += 3
        elif files_changed > 10:
            risk_score += 2
        elif files_changed > 5:
            risk_score += 1
        
        # Line change risk - ensure numeric types
        additions = pr_data.get('additions', 0)
        deletions = pr_data.get('deletions', 0)
        
        # Handle potential non-numeric values
        if isinstance(additions, (list, str)):
            additions = 0
        if isinstance(deletions, (list, str)):
            deletions = 0
            
        total_changes = int(additions) + int(deletions)
        if total_changes > 1000:
            risk_score += 3
        elif total_changes > 500:
            risk_score += 2
        elif total_changes > 100:
            risk_score += 1
        
        # Author experience (heuristic)
        author = pr_data.get('user', {}).get('login', '')
        if author.startswith(('new', 'temp', 'contractor')):
            risk_score += 2
        
        # PR description quality
        description = pr_data.get('body', '')
        if not description or len(description.strip()) < 50:
            risk_score += 1
        
        # Determine risk level
        if risk_score >= 7:
            return RiskLevel.HIGH.value
        elif risk_score >= 4:
            return RiskLevel.MEDIUM.value
        else:
            return RiskLevel.LOW.value
    
    def assess_repository_quality(self, total_issues: int, critical_issues: int, 
                                 major_issues: int, minor_issues: int) -> QualityClassification:
        """Assess overall repository quality based on issue counts"""
        # Calculate issue ratios
        if total_issues == 0:
            return QualityClassification.GOOD
        
        critical_ratio = (critical_issues / total_issues) * 100
        major_ratio = (major_issues / total_issues) * 100
        
        # Classification logic
        if critical_issues > 5 or critical_ratio > 30:
            return QualityClassification.BAD
        elif critical_issues > 0 or major_issues > 10 or critical_ratio > 10:
            return QualityClassification.OK
        else:
            return QualityClassification.GOOD
    
    def determine_repository_risk_level(self, critical_issues: int, major_issues: int, 
                                      total_issues: int) -> RiskLevel:
        """Determine overall risk level for repository"""
        if critical_issues > 5 or (total_issues > 0 and (critical_issues / total_issues) > 0.3):
            return RiskLevel.HIGH
        elif critical_issues > 0 or major_issues > 10:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def get_risk_recommendation(self, risk_level: RiskLevel, 
                              quality_classification: QualityClassification) -> str:
        """Get recommendation based on risk and quality assessment"""
        if quality_classification == QualityClassification.BAD:
            return "IMMEDIATE ACTION REQUIRED - Critical security and quality issues detected"
        elif quality_classification == QualityClassification.OK:
            return "Review and remediation recommended - Multiple issues need attention"
        else:
            return "Code quality acceptable - Minor improvements suggested"
    
    def calculate_quality_scores(self, total_issues: int, critical_issues: int, 
                               major_issues: int, minor_issues: int) -> Dict[str, float]:
        """Calculate quality score percentages"""
        if total_issues == 0:
            return {
                'critical_score': 0.0,
                'major_score': 0.0,
                'minor_score': 0.0
            }
        
        return {
            'critical_score': (critical_issues / total_issues) * 100,
            'major_score': (major_issues / total_issues) * 100,
            'minor_score': (minor_issues / total_issues) * 100
        }
    
    def aggregate_pr_assessments(self, pr_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate assessments from multiple PRs"""
        if not pr_results:
            return {
                'approved': 0,
                'conditional': 0,
                'rejected': 0,
                'low_risk': 0,
                'medium_risk': 0,
                'high_risk': 0,
                'avg_confidence': 0.0,
                'avg_score': 0.0
            }
        
        approved = 0
        conditional = 0
        rejected = 0
        low_risk = 0
        medium_risk = 0
        high_risk = 0
        total_confidence = 0.0
        total_score = 0.0
        
        for result in pr_results:
            verdict = result.get('verdict', {})
            
            # Count recommendations
            recommendation = verdict.get('recommendation', '').upper()
            if 'APPROVE' in recommendation:
                approved += 1
            elif 'CONDITIONAL' in recommendation:
                conditional += 1
            elif 'REJECT' in recommendation:
                rejected += 1
            
            # Count risk levels
            risk_level = verdict.get('risk_level', '').upper()
            if risk_level == 'LOW':
                low_risk += 1
            elif risk_level == 'MEDIUM':
                medium_risk += 1
            elif risk_level == 'HIGH':
                high_risk += 1
            
            # Aggregate scores
            confidence = verdict.get('confidence', 0)
            score = verdict.get('score', 0)
            if confidence:
                total_confidence += confidence
            if score:
                total_score += score
        
        count = len(pr_results)
        
        return {
            'approved': approved,
            'conditional': conditional,
            'rejected': rejected,
            'low_risk': low_risk,
            'medium_risk': medium_risk,
            'high_risk': high_risk,
            'avg_confidence': total_confidence / count if count > 0 else 0.0,
            'avg_score': total_score / count if count > 0 else 0.0
        }