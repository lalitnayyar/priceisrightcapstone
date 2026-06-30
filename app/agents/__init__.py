"""
Price Is Right — Agents package.

Contains all 7 agents in the multi-agent deal-hunting framework:
  1. ScannerAgent       — RSS feed monitor using GPT-5
  2. FrontierAgent      — RAG + GPT-5.1 price estimator
  3. SpecialistAgent    — Fine-tuned LLM price estimator (Modal)
  4. NeuralNetworkAgent — Deep residual DNN price estimator
  5. EnsembleAgent      — Weighted combination of agents 2-4
  6. MessagingAgent     — Push notification via Pushover + Claude
  7. PlanningAgent      — Orchestrator coordinating all agents
"""
from app.agents.agent import Agent
from app.agents.scanner_agent import ScannerAgent
from app.agents.frontier_agent import FrontierAgent
from app.agents.specialist_agent import SpecialistAgent
from app.agents.neural_network_agent import NeuralNetworkAgent
from app.agents.ensemble_agent import EnsembleAgent
from app.agents.messaging_agent import MessagingAgent
from app.agents.planning_agent import PlanningAgent
from app.agents.autonomous_planning_agent import AutonomousPlanningAgent

__all__ = [
    "Agent",
    "ScannerAgent",
    "FrontierAgent",
    "SpecialistAgent",
    "NeuralNetworkAgent",
    "EnsembleAgent",
    "MessagingAgent",
    "PlanningAgent",
    "AutonomousPlanningAgent",
]
