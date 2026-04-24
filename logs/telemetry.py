import json
import os
import time
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(__file__).parent
ACTIONS_LOG = LOG_DIR / 'actions.jsonl'
METRICS_FILE = LOG_DIR / 'metrics.json'
ERRORS_DIR = LOG_DIR / 'errors'

class Telemetry:
    def __init__(self):
        LOG_DIR.mkdir(exist_ok=True)
        ERRORS_DIR.mkdir(exist_ok=True)
        self._load_metrics()
    
    def _load_metrics(self):
        if METRICS_FILE.exists():
            with open(METRICS_FILE) as f:
                self.metrics = json.load(f)
        else:
            self.metrics = {
                'total_actions': 0,
                'errors_by_type': {},
                'avg_response_ms': 0,
                'campaigns_created': 0,
                'active_campaigns': set()
            }
    
    def _save_metrics(self):
        data = self.metrics.copy()
        data['active_campaigns'] = list(data['active_campaigns'])
        with open(METRICS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    
    def log_action(self, action_type: str, user: str, campaign_id: str = None, 
                   success: bool = True, error_type: str = None, duration_ms: float = 0,
                   extra: dict = None):
        entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'action_type': action_type,
            'user': user,
            'campaign_id': campaign_id,
            'success': success,
            'duration_ms': duration_ms
        }
        if error_type:
            entry['error_type'] = error_type
        if extra:
            entry['extra'] = extra
        
        with open(ACTIONS_LOG, 'a') as f:
            f.write(json.dumps(entry) + '\n')
        
        self.metrics['total_actions'] += 1
        if error_type:
            self.metrics['errors_by_type'][error_type] =                 self.metrics['errors_by_type'].get(error_type, 0) + 1
        if campaign_id:
            self.metrics['active_campaigns'].add(campaign_id)
        self._save_metrics()
    
    def log_error(self, action_type: str, user: str, campaign_id: str,
                   error: Exception, state_snapshot: dict = None):
        filename = f"error-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{action_type}.json"
        snapshot = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'action_type': action_type,
            'user': user,
            'campaign_id': campaign_id,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'stack_trace': str(error.__traceback__),
            'state_snapshot': state_snapshot or {}
        }
        with open(ERRORS_DIR / filename, 'w') as f:
            json.dump(snapshot, f, indent=2)
        
        self.log_action(action_type, user, campaign_id, 
                       success=False, error_type=type(error).__name__)
    
    def get_metrics(self):
        return self.metrics.copy()

telemetry = Telemetry()
