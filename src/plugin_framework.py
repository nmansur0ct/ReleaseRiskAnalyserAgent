"""
Modular Plugin Framework for Release Risk Analyzer
Enables easy addition and configuration of new analysis agents
"""

import asyncio
import importlib.util
import inspect
import yaml
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Type, Set, Callable, TYPE_CHECKING
from pydantic import BaseModel, Field, validator
from enum import Enum
from datetime import datetime
import logging
from pathlib import Path

if TYPE_CHECKING:
    from .enhanced_models import RiskAnalysisState

logger = logging.getLogger(__name__)

class AgentCapability(Enum):
    """Defines what capabilities an agent provides"""
    ANALYSIS = "analysis"
    VALIDATION = "validation"
    DECISION = "decision"
    ENRICHMENT = "enrichment"
    NOTIFICATION = "notification"
    MONITORING = "monitoring"
    SECURITY = "security"
    PERFORMANCE = "performance"
    COMPLIANCE = "compliance"

class ExecutionMode(Enum):
    """Defines how an agent should be executed"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"

class AgentMetadata(BaseModel):
    """Metadata describing the agent plugin"""
    name: str
    version: str
    description: str
    author: str
    capabilities: List[AgentCapability]
    dependencies: List[str] = []
    execution_priority: int = Field(ge=1, le=100, default=50)
    execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    parallel_compatible: bool = True
    required_config: Dict[str, Any] = {}
    optional_config: Dict[str, Any] = {}
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None

class AgentInput(BaseModel):
    """Standardized input interface for all agents"""
    data: Dict[str, Any]
    context: Dict[str, Any] = {}
    config: Dict[str, Any] = {}
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.now)

class AgentOutput(BaseModel):
    """Standardized output interface for all agents"""
    result: Dict[str, Any]
    metadata: Dict[str, Any] = {}
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    analysis_method: str = "unknown"
    execution_time: Optional[float] = None
    errors: List[str] = []
    warnings: List[str] = []
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.now)

class AgentStatus(Enum):
    """Agent status enumeration"""
    DISCOVERED = "discovered"
    VALIDATING = "validating"
    VALIDATED = "validated"
    LOADING = "loading"
    LOADED = "loaded"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    ERROR = "error"
    UNLOADING = "unloading"
    UNLOADED = "unloaded"

class BaseAgentPlugin(ABC):
    """Base class for all agent plugins"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.metadata = self.get_metadata()
        self.status = AgentStatus.DISCOVERED
        self.last_error: Optional[str] = None
        self.validate_config()
    
    @abstractmethod
    def get_metadata(self) -> AgentMetadata:
        """Return agent metadata"""
        pass
    
    @abstractmethod
    async def process(self, input_data: AgentInput, state: 'RiskAnalysisState') -> AgentOutput:
        """Main processing method for the agent"""
        pass
    
    def validate_config(self) -> None:
        """Validate agent configuration"""
        required_config = self.metadata.required_config
        for key, expected_type in required_config.items():
            if key not in self.config:
                raise ValueError(f"Required config '{key}' missing for agent '{self.metadata.name}'")
            
            # Type validation
            if not isinstance(self.config[key], expected_type):
                raise TypeError(f"Config '{key}' must be of type {expected_type.__name__}")
    
    async def health_check(self) -> bool:
        """Health check for the agent"""
        try:
            # Basic health check - can be overridden by specific agents
            return self.status in [AgentStatus.READY, AgentStatus.RUNNING]
        except Exception as e:
            logger.error(f"Health check failed for agent {self.metadata.name}: {e}")
            return False
    
    async def initialize(self) -> None:
        """Initialize agent resources"""
        self.status = AgentStatus.INITIALIZING
        try:
            # Override in specific agents for custom initialization
            self.status = AgentStatus.READY
        except Exception as e:
            self.status = AgentStatus.ERROR
            self.last_error = str(e)
            raise
    
    async def cleanup(self) -> None:
        """Cleanup agent resources"""
        self.status = AgentStatus.UNLOADING
        try:
            # Override in specific agents for custom cleanup
            self.status = AgentStatus.UNLOADED
        except Exception as e:
            logger.error(f"Cleanup failed for agent {self.metadata.name}: {e}")

class AgentPluginRegistry:
    """Registry for managing agent plugins"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgentPlugin] = {}
        self.metadata: Dict[str, AgentMetadata] = {}
        self.execution_order: List[str] = []
        self.parallel_groups: Dict[int, List[str]] = {}
        self.dependency_graph: Dict[str, List[str]] = {}
        
    async def register_agent(self, agent: BaseAgentPlugin) -> None:
        """Register a new agent plugin"""
        metadata = agent.get_metadata()
        
        # Validate dependencies
        await self._validate_dependencies(metadata)
        
        # Initialize agent
        await agent.initialize()
        
        # Register agent
        self.agents[metadata.name] = agent
        self.metadata[metadata.name] = metadata
        
        # Update execution planning
        self._update_execution_plan()
        
        logger.info(f"Registered agent: {metadata.name} v{metadata.version}")
        
    async def unregister_agent(self, agent_name: str) -> None:
        """Unregister an agent plugin"""
        if agent_name in self.agents:
            agent = self.agents[agent_name]
            await agent.cleanup()
            
            del self.agents[agent_name]
            del self.metadata[agent_name]
            self._update_execution_plan()
            
            logger.info(f"Unregistered agent: {agent_name}")
    
    def get_agent(self, agent_name: str) -> Optional[BaseAgentPlugin]:
        """Get agent by name"""
        return self.agents.get(agent_name)
    
    def get_execution_plan(self) -> Dict[str, Any]:
        """Get complete execution plan"""
        return {
            "sequential_order": self.execution_order,
            "parallel_groups": self.parallel_groups,
            "dependency_graph": self.dependency_graph
        }
    
    def get_agents_by_capability(self, capability: AgentCapability) -> List[str]:
        """Get agents that provide a specific capability"""
        return [
            name for name, metadata in self.metadata.items()
            if capability in metadata.capabilities
        ]
    
    async def health_check_all(self) -> Dict[str, bool]:
        """Run health check on all agents"""
        health_status = {}
        for name, agent in self.agents.items():
            health_status[name] = await agent.health_check()
        return health_status
    
    async def _validate_dependencies(self, metadata: AgentMetadata) -> None:
        """Validate agent dependencies are satisfied"""
        for dep in metadata.dependencies:
            if dep not in self.agents:
                raise ValueError(f"Dependency '{dep}' not found for agent '{metadata.name}'")
    
    def _update_execution_plan(self) -> None:
        """Update execution plan based on dependencies, priorities, and execution modes"""
        # Build dependency graph
        self._build_dependency_graph()
        
        # Determine execution order with parallel groups
        self._determine_execution_order()
        
    def _build_dependency_graph(self) -> None:
        """Build dependency graph for all agents"""
        self.dependency_graph = {}
        for name, metadata in self.metadata.items():
            self.dependency_graph[name] = metadata.dependencies.copy()
    
    def _determine_execution_order(self) -> None:
        """Determine execution order considering dependencies and parallel execution"""
        # Topological sort with parallel group detection
        in_degree = {name: len(deps) for name, deps in self.dependency_graph.items()}
        
        self.execution_order = []
        self.parallel_groups = {}
        group_id = 0
        
        while in_degree:
            # Find all nodes with no dependencies
            ready_nodes = [name for name, degree in in_degree.items() if degree == 0]
            
            if not ready_nodes:
                # Circular dependency detected
                raise ValueError("Circular dependency detected in agent configuration")
            
            # Separate sequential and parallel nodes
            sequential_nodes = []
            parallel_nodes = []
            
            for node in ready_nodes:
                metadata = self.metadata[node]
                if metadata.execution_mode == ExecutionMode.PARALLEL and metadata.parallel_compatible:
                    parallel_nodes.append(node)
                else:
                    sequential_nodes.append(node)
            
            # Sort by priority
            sequential_nodes.sort(key=lambda x: self.metadata[x].execution_priority)
            parallel_nodes.sort(key=lambda x: self.metadata[x].execution_priority)
            
            # Add to execution plan
            if parallel_nodes:
                self.parallel_groups[group_id] = parallel_nodes
                self.execution_order.extend(parallel_nodes)
                group_id += 1
            
            self.execution_order.extend(sequential_nodes)
            
            # Update in_degree for next iteration
            for node in ready_nodes:
                del in_degree[node]
                for other_node, deps in self.dependency_graph.items():
                    if node in deps and other_node in in_degree:
                        in_degree[other_node] -= 1

class ConfigurationManager:
    """Manages plugin configuration with hot-reload capability"""
    
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.callbacks: List[Callable] = []
        self.last_modified: Optional[float] = None
        
    async def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            
            self.last_modified = self.config_path.stat().st_mtime
            logger.info(f"Configuration loaded from {self.config_path}")
            return self.config
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    async def watch_config(self) -> None:
        """Watch configuration file for changes"""
        while True:
            try:
                current_mtime = self.config_path.stat().st_mtime
                if self.last_modified and current_mtime > self.last_modified:
                    logger.info("Configuration file changed, reloading...")
                    old_config = self.config.copy()
                    await self.load_config()
                    
                    # Notify callbacks of config change
                    for callback in self.callbacks:
                        await callback(old_config, self.config)
                
                await asyncio.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error(f"Error watching config file: {e}")
                await asyncio.sleep(5)  # Wait longer on error
    
    def add_change_callback(self, callback: Callable) -> None:
        """Add callback for configuration changes"""
        self.callbacks.append(callback)
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Get configuration for specific agent"""
        agents_config = self.config.get('agents', [])
        for agent_config in agents_config:
            if agent_config.get('name') == agent_name:
                return agent_config.get('config', {})
        return {}

class PluginLoader:
    """Dynamically loads agent plugins from various sources"""
    
    def __init__(self):
        self.loaded_plugins: Dict[str, Type[BaseAgentPlugin]] = {}
    
    async def load_plugins_from_directory(self, plugin_dir: str) -> List[Type[BaseAgentPlugin]]:
        """Load plugins from a directory"""
        plugin_path = Path(plugin_dir)
        plugins = []
        
        for plugin_file in plugin_path.glob("*.py"):
            if plugin_file.name.startswith("__"):
                continue
                
            try:
                plugin_class = await self._load_plugin_from_file(plugin_file)
                if plugin_class:
                    plugins.append(plugin_class)
            except Exception as e:
                logger.error(f"Failed to load plugin from {plugin_file}: {e}")
        
        return plugins
    
    async def _load_plugin_from_file(self, plugin_file: Path) -> Optional[Type[BaseAgentPlugin]]:
        """Load a single plugin from file"""
        module_name = plugin_file.stem
        spec = importlib.util.spec_from_file_location(module_name, plugin_file)
        
        if not spec or not spec.loader:
            return None
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find BaseAgentPlugin subclasses in the module
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and 
                issubclass(obj, BaseAgentPlugin) and 
                obj is not BaseAgentPlugin):
                
                self.loaded_plugins[obj.__name__] = obj
                return obj
        
        return None
    
    def get_plugin_class(self, class_name: str) -> Optional[Type[BaseAgentPlugin]]:
        """Get loaded plugin class by name"""
        return self.loaded_plugins.get(class_name)

class WorkflowOrchestrator:
    """Orchestrates the execution of agent plugins"""
    
    def __init__(self, registry: AgentPluginRegistry, config_manager: ConfigurationManager):
        self.registry = registry
        self.config_manager = config_manager
        self.execution_stats: Dict[str, Any] = {}
    
    async def execute_workflow(self, input_data: AgentInput, state: 'RiskAnalysisState') -> Dict[str, AgentOutput]:
        """Execute the complete workflow"""
        execution_plan = self.registry.get_execution_plan()
        results = {}
        
        # Execute sequential agents
        for agent_name in execution_plan["sequential_order"]:
            if agent_name not in self.registry.parallel_groups.get(0, []):
                agent = self.registry.get_agent(agent_name)
                if agent and await self._should_execute_agent(agent_name):
                    try:
                        start_time = asyncio.get_event_loop().time()
                        result = await agent.process(input_data, state)
                        execution_time = asyncio.get_event_loop().time() - start_time
                        
                        result.execution_time = execution_time
                        results[agent_name] = result
                        
                        # Update state with results
                        await self._update_state(state, agent_name, result)
                        
                    except Exception as e:
                        logger.error(f"Error executing agent {agent_name}: {e}")
                        results[agent_name] = AgentOutput(
                            result={},
                            errors=[str(e)],
                            session_id=input_data.session_id
                        )
        
        # Execute parallel groups
        for group_id, agent_names in execution_plan["parallel_groups"].items():
            if len(agent_names) > 1:
                parallel_results = await self._execute_parallel_group(agent_names, input_data, state)
                results.update(parallel_results)
        
        return results
    
    async def _execute_parallel_group(self, agent_names: List[str], 
                                    input_data: AgentInput, 
                                    state: 'RiskAnalysisState') -> Dict[str, AgentOutput]:
        """Execute a group of agents in parallel"""
        tasks = []
        
        for agent_name in agent_names:
            agent = self.registry.get_agent(agent_name)
            if agent and await self._should_execute_agent(agent_name):
                task = asyncio.create_task(
                    self._execute_single_agent(agent, input_data, state),
                    name=f"agent_{agent_name}"
                )
                tasks.append((agent_name, task))
        
        results = {}
        completed_tasks = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
        
        for (agent_name, _), result in zip(tasks, completed_tasks):
            if isinstance(result, Exception):
                logger.error(f"Parallel execution error for {agent_name}: {result}")
                results[agent_name] = AgentOutput(
                    result={},
                    errors=[str(result)],
                    session_id=input_data.session_id
                )
            else:
                results[agent_name] = result
                await self._update_state(state, agent_name, result)
        
        return results
    
    async def _execute_single_agent(self, agent: BaseAgentPlugin, 
                                   input_data: AgentInput, 
                                   state: 'RiskAnalysisState') -> AgentOutput:
        """Execute a single agent with error handling"""
        try:
            start_time = asyncio.get_event_loop().time()
            result = await agent.process(input_data, state)
            execution_time = asyncio.get_event_loop().time() - start_time
            result.execution_time = execution_time
            return result
        except Exception as e:
            logger.error(f"Error executing agent {agent.metadata.name}: {e}")
            return AgentOutput(
                result={},
                errors=[str(e)],
                session_id=input_data.session_id
            )
    
    async def _should_execute_agent(self, agent_name: str) -> bool:
        """Determine if an agent should be executed based on configuration"""
        agent_config = self.config_manager.get_agent_config(agent_name)
        return agent_config.get('enabled', True)
    
    async def _update_state(self, state: 'RiskAnalysisState', 
                          agent_name: str, result: AgentOutput) -> None:
        """Update shared state with agent results"""
        # Update state based on agent capability
        agent = self.registry.get_agent(agent_name)
        if not agent:
            return
        
        capabilities = agent.metadata.capabilities
        
        if AgentCapability.ANALYSIS in capabilities:
            # Update analysis results
            if not hasattr(state, 'analysis_results'):
                state.analysis_results = {}
            state.analysis_results[agent_name] = result.result
        
        if AgentCapability.VALIDATION in capabilities:
            # Update validation results
            if not hasattr(state, 'validation_results'):
                state.validation_results = {}
            state.validation_results[agent_name] = result.result
        
        if AgentCapability.DECISION in capabilities:
            # Update decision results
            if not hasattr(state, 'decision_results'):
                state.decision_results = {}
            state.decision_results[agent_name] = result.result
        
        # Update confidence and metadata
        if not hasattr(state, 'confidence_levels'):
            state.confidence_levels = {}
        state.confidence_levels[agent_name] = result.confidence
        
        if not hasattr(state, 'analysis_methods'):
            state.analysis_methods = {}
        state.analysis_methods[agent_name] = result.analysis_method