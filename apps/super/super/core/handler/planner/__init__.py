"""The Handler is the execution engine for the Orchestrator."""

from super.core.handler.planner.simple import SimplePlanHandler

DefaultPlanner = SimplePlanHandler  # Alias SimplePlanHandler as DefaultPlanner
