"""
Workflow Execution Engine using LangGraph
Orchestrates multi-step workflows across MCPs
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage

from orchestrator.mcp.mcp_router import mcp_router

logger = logging.getLogger(__name__)


class WorkflowState(dict):
    """
    Workflow state that gets passed between nodes

    Contains:
    - customer_id: Customer ID for MCP isolation
    - workflow_id: Workflow being executed
    - execution_id: Execution instance ID
    - input: Original workflow input
    - current_data: Data flowing through workflow
    - results: Results from each step
    - errors: List of errors encountered
    - metadata: Additional context
    """
    pass


class WorkflowEngine:
    """
    LangGraph-based workflow execution engine

    Executes multi-step workflows by orchestrating MCP calls.
    Handles state management, error recovery, and logging.
    """

    def __init__(self, db_session=None):
        """
        Initialize workflow engine

        Args:
            db_session: SQLAlchemy session for logging (optional)
        """
        self.db = db_session
        self.logger = logger

    async def execute_workflow(
        self,
        workflow_definition: Dict[str, Any],
        customer_id: str,
        workflow_id: str,
        execution_id: str,
        input_data: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a workflow using LangGraph

        Args:
            workflow_definition: Workflow definition (nodes, edges, entry_point)
            customer_id: Customer ID for isolation
            workflow_id: Workflow template ID
            execution_id: Execution instance ID
            input_data: Input data for workflow
            config: Optional execution configuration

        Returns:
            Workflow execution results
        """
        self.logger.info(f"Starting workflow execution {execution_id} for customer {customer_id}")

        # Initialize state
        initial_state = WorkflowState({
            "customer_id": customer_id,
            "workflow_id": workflow_id,
            "execution_id": execution_id,
            "input": input_data,
            "current_data": input_data,
            "results": {},
            "errors": [],
            "metadata": config or {},
            "step_count": 0
        })

        try:
            # Build LangGraph workflow
            graph = self._build_graph(workflow_definition)

            # Execute workflow
            final_state = await graph.ainvoke(initial_state)

            return {
                "status": "completed" if not final_state.get("errors") else "failed",
                "output": final_state.get("current_data"),
                "results": final_state.get("results"),
                "errors": final_state.get("errors"),
                "step_count": final_state.get("step_count", 0)
            }

        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}", exc_info=True)
            return {
                "status": "failed",
                "output": None,
                "results": {},
                "errors": [str(e)],
                "step_count": 0
            }

    def _build_graph(self, definition: Dict[str, Any]) -> StateGraph:
        """
        Build LangGraph state machine from workflow definition

        Args:
            definition: Workflow definition with nodes and edges

        Returns:
            Compiled StateGraph
        """
        # Create graph
        workflow = StateGraph(WorkflowState)

        # Add nodes (each node is an MCP call)
        nodes = definition.get("nodes", [])
        for node in nodes:
            node_id = node["id"]
            workflow.add_node(node_id, self._create_node_function(node))

        # Add edges (workflow transitions)
        edges = definition.get("edges", [])
        for edge in edges:
            from_node = edge["from"]
            to_node = edge["to"]

            # Conditional edge or direct edge
            if "condition" in edge:
                # Conditional transition (e.g., only if previous step succeeded)
                workflow.add_conditional_edges(
                    from_node,
                    self._create_condition_function(edge["condition"]),
                    {True: to_node, False: END}
                )
            else:
                # Direct transition
                workflow.add_edge(from_node, to_node)

        # Set entry point
        entry_point = definition.get("entry_point", nodes[0]["id"] if nodes else None)
        if entry_point:
            workflow.set_entry_point(entry_point)

        # Add final node to END
        last_nodes = self._find_terminal_nodes(definition)
        for node_id in last_nodes:
            workflow.add_edge(node_id, END)

        # Compile graph
        return workflow.compile()

    def _create_node_function(self, node: Dict[str, Any]):
        """
        Create async function for a workflow node

        Args:
            node: Node configuration from workflow definition

        Returns:
            Async function that executes the node
        """
        mcp_name = node["mcp"]
        action = node["action"]
        node_config = node.get("config", {})

        async def node_executor(state: WorkflowState) -> WorkflowState:
            """Execute this workflow step"""
            step_start = datetime.utcnow()
            node_id = node["id"]

            self.logger.info(f"Executing step '{node_id}': {mcp_name}.{action}")

            try:
                # Prepare input for MCP
                input_for_mcp = self._prepare_mcp_input(
                    state["current_data"],
                    action,
                    node_config
                )

                # Call MCP via router
                result = await mcp_router.query_mcp(
                    mcp_name=mcp_name,
                    customer_id=state["customer_id"],
                    query=input_for_mcp.get("query", action),
                    context=input_for_mcp.get("context", {})
                )

                # Store result
                state["results"][node_id] = result
                state["current_data"] = self._extract_output(result, action)
                state["step_count"] += 1

                # Log step execution (if DB session available)
                if self.db:
                    await self._log_step(
                        execution_id=state["execution_id"],
                        step_index=state["step_count"],
                        step_id=node_id,
                        mcp_name=mcp_name,
                        action=action,
                        input_data=input_for_mcp,
                        output_data=result,
                        status="success",
                        duration_ms=int((datetime.utcnow() - step_start).total_seconds() * 1000)
                    )

                self.logger.info(f"Step '{node_id}' completed successfully")

            except Exception as e:
                self.logger.error(f"Step '{node_id}' failed: {e}")
                state["errors"].append({
                    "step": node_id,
                    "mcp": mcp_name,
                    "error": str(e)
                })

                # Log failed step
                if self.db:
                    await self._log_step(
                        execution_id=state["execution_id"],
                        step_index=state["step_count"],
                        step_id=node_id,
                        mcp_name=mcp_name,
                        action=action,
                        input_data={},
                        output_data={},
                        status="failed",
                        error_message=str(e),
                        duration_ms=int((datetime.utcnow() - step_start).total_seconds() * 1000)
                    )

                # Optionally retry based on config
                max_retries = node_config.get("max_retries", 0)
                if max_retries > 0:
                    # TODO: Implement retry logic
                    pass

            return state

        return node_executor

    def _prepare_mcp_input(
        self,
        current_data: Any,
        action: str,
        node_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepare input for MCP call from workflow data

        Args:
            current_data: Current data flowing through workflow
            action: Action to perform
            node_config: Node-specific configuration

        Returns:
            Formatted input for MCP
        """
        return {
            "query": f"{action}: {current_data}" if isinstance(current_data, str) else action,
            "context": {
                "data": current_data,
                "config": node_config
            }
        }

    def _extract_output(self, mcp_result: Dict[str, Any], action: str) -> Any:
        """
        Extract output from MCP result for next step

        Args:
            mcp_result: MCP response
            action: Action that was performed

        Returns:
            Extracted data for next step
        """
        # Try to extract meaningful data from MCP response
        if "results" in mcp_result:
            return mcp_result["results"]
        elif "data" in mcp_result:
            return mcp_result["data"]
        elif "output" in mcp_result:
            return mcp_result["output"]
        else:
            return mcp_result

    def _create_condition_function(self, condition: str):
        """
        Create condition function for conditional edges

        Args:
            condition: Condition type (e.g., "success", "has_data")

        Returns:
            Condition function
        """
        def condition_checker(state: WorkflowState) -> bool:
            """Check if condition is met"""
            if condition == "success":
                return len(state.get("errors", [])) == 0
            elif condition == "has_data":
                return state.get("current_data") is not None
            elif condition == "error":
                return len(state.get("errors", [])) > 0
            else:
                return True  # Default: always proceed

        return condition_checker

    def _find_terminal_nodes(self, definition: Dict[str, Any]) -> List[str]:
        """
        Find nodes that have no outgoing edges (terminal nodes)

        Args:
            definition: Workflow definition

        Returns:
            List of terminal node IDs
        """
        nodes = definition.get("nodes", [])
        edges = definition.get("edges", [])

        all_node_ids = {node["id"] for node in nodes}
        nodes_with_outgoing = {edge["from"] for edge in edges}

        terminal_nodes = all_node_ids - nodes_with_outgoing

        return list(terminal_nodes) if terminal_nodes else [nodes[-1]["id"]] if nodes else []

    async def _log_step(
        self,
        execution_id: str,
        step_index: int,
        step_id: str,
        mcp_name: str,
        action: str,
        input_data: Dict,
        output_data: Dict,
        status: str,
        duration_ms: int,
        error_message: str = None
    ):
        """
        Log step execution to database

        Args:
            execution_id: Workflow execution ID
            step_index: Step number
            step_id: Node ID
            mcp_name: MCP name
            action: Action performed
            input_data: Step input
            output_data: Step output
            status: Step status
            duration_ms: Execution duration
            error_message: Error message (if failed)
        """
        from api.models.workflow_step_log import WorkflowStepLog

        if not self.db:
            return

        try:
            log = WorkflowStepLog(
                execution_id=execution_id,
                step_index=step_index,
                step_id=step_id,
                step_name=f"{mcp_name}.{action}",
                mcp_name=mcp_name,
                mcp_action=action,
                input_data=input_data,
                output_data=output_data,
                status=status,
                error_message=error_message,
                duration_ms=duration_ms,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )

            self.db.add(log)
            self.db.commit()

        except Exception as e:
            self.logger.error(f"Failed to log step: {e}")
            # Don't fail workflow if logging fails
            pass
