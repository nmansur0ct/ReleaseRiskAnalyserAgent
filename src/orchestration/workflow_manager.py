"""
Workflow Manager for Risk Agent Analyzer

Manages analysis workflow and execution coordination.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

class WorkflowManager:
    """Manages analysis workflow execution"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize workflow manager"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.start_time = None
        self.end_time = None
    
    def start_workflow(self, repo_count: int) -> None:
        """Start the analysis workflow"""
        self.start_time = datetime.now()
        self.logger.info(f"Starting analysis workflow for {repo_count} repositories")
    
    def end_workflow(self, success_count: int, total_count: int) -> None:
        """End the analysis workflow"""
        self.end_time = datetime.now()
        duration = self.end_time - self.start_time if self.start_time else None
        
        self.logger.info(f"Workflow completed: {success_count}/{total_count} repositories analyzed")
        if duration:
            self.logger.info(f"Total execution time: {duration.total_seconds():.1f} seconds")
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get workflow execution summary"""
        duration = None
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
        
        return {
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration_seconds': duration,
            'config': self.config
        }