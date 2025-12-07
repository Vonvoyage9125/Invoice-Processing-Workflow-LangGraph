"""
Enhanced logging for invoice workflow.
Tracks all stage transitions, tool selections, and checkpoints.
"""
import logging
import json
from datetime import datetime


def setup_logging(log_file: str = 'workflow.log', level=logging.DEBUG):
    """Configure logging for the workflow."""
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(level)
    fh.setFormatter(formatter)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(fh)
    root_logger.addHandler(ch)
    
    return root_logger


class WorkflowLogger:
    """Structured logging for workflow events."""
    
    def __init__(self, invoice_id: str):
        self.invoice_id = invoice_id
        self.logger = logging.getLogger(f'workflow.{invoice_id}')
        self.events = []
    
    def log_stage_start(self, stage_name: str, stage_id: str):
        """Log the start of a stage."""
        msg = f"[{stage_id}] Starting stage {stage_name}"
        self.logger.info(msg)
        self._record_event('stage_start', {'stage_id': stage_id, 'stage_name': stage_name})
    
    def log_stage_end(self, stage_id: str, status: str = 'OK'):
        """Log the completion of a stage."""
        msg = f"[{stage_id}] Stage completed with status: {status}"
        self.logger.info(msg)
        self._record_event('stage_end', {'stage_id': stage_id, 'status': status})
    
    def log_tool_selection(self, capability: str, tool_name: str, context: dict = None):
        """Log when Bigtool selects a tool."""
        msg = f"Bigtool selected {tool_name} for capability {capability}"
        self.logger.info(msg)
        self._record_event('tool_selection', {
            'capability': capability,
            'tool_name': tool_name,
            'context': context or {}
        })
    
    def log_ability_call(self, server: str, ability: str, params: dict = None):
        """Log when an ability is called on an MCP server."""
        msg = f"Calling ability {ability} on {server} server"
        self.logger.debug(msg)
        self._record_event('ability_call', {
            'server': server,
            'ability': ability,
            'params': params or {}
        })
    
    def log_checkpoint_created(self, checkpoint_id: str, reason: str):
        """Log checkpoint creation."""
        msg = f"Checkpoint created {checkpoint_id} - reason: {reason}"
        self.logger.warning(msg)
        self._record_event('checkpoint_created', {
            'checkpoint_id': checkpoint_id,
            'reason': reason
        })
    
    def log_hitl_decision(self, checkpoint_id: str, decision: str, reviewer_id: str):
        """Log HITL decision."""
        msg = f"HITL decision received: {decision} from {reviewer_id} for checkpoint {checkpoint_id}"
        self.logger.info(msg)
        self._record_event('hitl_decision', {
            'checkpoint_id': checkpoint_id,
            'decision': decision,
            'reviewer_id': reviewer_id
        })
    
    def log_error(self, stage: str, error: str, traceback_str: str = None):
        """Log an error."""
        msg = f"[{stage}] Error: {error}"
        self.logger.error(msg, exc_info=bool(traceback_str))
        self._record_event('error', {
            'stage': stage,
            'error': error,
            'traceback': traceback_str
        })
    
    def log_state_transition(self, from_stage: str, to_stage: str, state_keys: list = None):
        """Log state transition between stages."""
        msg = f"State transition: {from_stage} -> {to_stage}"
        self.logger.debug(msg)
        self._record_event('state_transition', {
            'from_stage': from_stage,
            'to_stage': to_stage,
            'state_keys': state_keys or []
        })
    
    def _record_event(self, event_type: str, details: dict):
        """Record an event in memory."""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'type': event_type,
            'invoice_id': self.invoice_id,
            'details': details
        }
        self.events.append(event)
    
    def export_events(self) -> str:
        """Export all logged events as JSON."""
        return json.dumps(self.events, indent=2, default=str)
    
    def export_events_to_file(self, file_path: str):
        """Export all logged events to a JSON file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self.export_events())


# Module-level logger setup
_root_logger = None

def get_root_logger():
    """Get or initialize the root logger."""
    global _root_logger
    if _root_logger is None:
        _root_logger = setup_logging()
    return _root_logger
