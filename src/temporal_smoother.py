"""
Temporal Smoother
Smooth seat status over time to reduce flickering
Methods: Majority Voting, Hysteresis, Exponential Smoothing
"""

from collections import deque, Counter
from src.config import *


class TemporalSmoother:
    """
    Temporal smoothing untuk mengurangi flickering status seat
    
    Flickering terjadi karena:
    - Detection tidak stabil frame-to-frame
    - Objek partially occluded
    - Confidence threshold borderline
    
    Solution: Track status over multiple frames, smooth transitions
    """
    
    def __init__(self, window_size=5, method='majority_voting'):
        """
        Initialize temporal smoother
        
        Args:
            window_size: Number of frames to consider (3-10)
                        Larger = more stable, tapi slower response
            method: Smoothing method
                   - 'majority_voting': Most common status in window (RECOMMENDED)
                   - 'hysteresis': Require N consecutive frames to change
                   - 'exponential': Weighted average (recent = higher weight)
        """
        self.window_size = window_size
        self.method = method
        
        # Storage per seat: {seat_id: deque([status1, status2, ...])}
        self.history = {}
        
        # For hysteresis method: track consecutive frames
        self.transition_counters = {}
        self.last_output = {}
        
        # Status to numeric mapping (for exponential method)
        self.STATUS_TO_NUM = {
            STATUS_OCCUPIED: 1,
            STATUS_ON_HOLD: 2,
            STATUS_EMPTY: 3
        }
        self.NUM_TO_STATUS = {
            1: STATUS_OCCUPIED,
            2: STATUS_ON_HOLD,
            3: STATUS_EMPTY
        }
    
    def update(self, seat_id, current_status):
        """
        Update status history and return smoothed status
        
        Args:
            seat_id: Seat identifier (e.g., "T1", "t1")
            current_status: Current detected status (OCCUPIED/ON-HOLD/EMPTY)
        
        Returns:
            smoothed_status: Smoothed status after temporal filtering
        """
        # Normalize seat_id to lowercase
        seat_id = seat_id.lower()
        
        # Initialize history for new seat
        if seat_id not in self.history:
            self.history[seat_id] = deque(maxlen=self.window_size)
            self.transition_counters[seat_id] = 0
            self.last_output[seat_id] = current_status
        
        # Add current status to history
        self.history[seat_id].append(current_status)
        
        # Apply smoothing method
        if self.method == 'majority_voting':
            smoothed = self._majority_voting(seat_id)
        elif self.method == 'hysteresis':
            smoothed = self._hysteresis(seat_id, current_status)
        elif self.method == 'exponential':
            smoothed = self._exponential_smoothing(seat_id)
        else:
            smoothed = current_status  # No smoothing
        
        # Update last output
        self.last_output[seat_id] = smoothed
        
        return smoothed
    
    def _majority_voting(self, seat_id):
        """
        Return most frequent status in sliding window
        
        Example:
            Window: [Occupied, Empty, Empty, Empty, Occupied]
            Output: Empty (3/5 votes)
        
        Pros:
            - Simple and effective
            - Good balance between stability and responsiveness
            - Easy to understand
        
        Cons:
            - Fixed delay (window_size frames)
            - May miss very quick changes
        
        Best for: General use, recommended default
        """
        history = list(self.history[seat_id])
        
        # Need at least 2 frames
        if len(history) < 2:
            return history[-1]
        
        # Count occurrences
        counter = Counter(history)
        
        # Return most common status
        most_common_status, count = counter.most_common(1)[0]
        
        return most_common_status
    
    def _hysteresis(self, seat_id, current_status):
        """
        Require N consecutive frames before changing status
        
        Example (threshold=3):
            Current output: Occupied
            Frame 1: Empty detected → count=1, output=Occupied
            Frame 2: Empty detected → count=2, output=Occupied
            Frame 3: Empty detected → count=3, output=Empty ✅
        
        Pros:
            - Very stable
            - Excellent for preventing rapid oscillation
            - Good for noisy detections
        
        Cons:
            - Slower to respond to real changes
            - May miss quick transitions
        
        Best for: High noise environments, critical applications
        """
        history = list(self.history[seat_id])
        
        # Need at least 2 frames
        if len(history) < 2:
            return history[-1]
        
        last_output = self.last_output[seat_id]
        
        # Check if status is trying to change
        if current_status != last_output:
            # Increment counter
            self.transition_counters[seat_id] += 1
            
            # Check if we've reached threshold
            if self.transition_counters[seat_id] >= HYSTERESIS_THRESHOLD:
                # Change status
                self.transition_counters[seat_id] = 0
                return current_status
            else:
                # Keep old status
                return last_output
        else:
            # Status is stable, reset counter
            self.transition_counters[seat_id] = 0
            return current_status
    
    def _exponential_smoothing(self, seat_id):
        """
        Weighted average with exponential decay
        Recent frames have higher weight than older frames
        
        Example (alpha=0.3):
            Window: [Old ... Recent]
            Weights: [0.1, 0.15, 0.22, 0.33, 0.49]
            Recent frames contribute more to final decision
        
        Pros:
            - Smooth transitions
            - More responsive than majority voting
            - Good for visualization (smooth animations)
        
        Cons:
            - More complex
            - Requires numeric conversion
            - May not work well with 3 discrete states
        
        Best for: Smooth animations, visualization purposes
        """
        history = list(self.history[seat_id])
        
        # Need at least 2 frames
        if len(history) < 2:
            return history[-1]
        
        # Convert status to numeric
        numeric_history = [self.STATUS_TO_NUM.get(s, 3) for s in history]
        
        # Generate exponential weights
        # w_i = alpha * (1 - alpha)^i
        alpha = EXPONENTIAL_ALPHA
        n = len(numeric_history)
        weights = [alpha * ((1 - alpha) ** i) for i in range(n)]
        weights.reverse()  # Recent gets higher weight
        
        # Normalize weights
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]
        
        # Weighted average
        weighted_sum = sum(w * v for w, v in zip(weights, numeric_history))
        
        # Round to nearest status
        rounded = round(weighted_sum)
        rounded = max(1, min(3, rounded))  # Clamp to [1, 3]
        
        # Convert back to status string
        return self.NUM_TO_STATUS.get(rounded, STATUS_EMPTY)
    
    def update_batch(self, seat_statuses):
        """
        Update multiple seats at once
        
        Args:
            seat_statuses: Dict {seat_id: status_string}
        
        Returns:
            smoothed_statuses: Dict {seat_id: smoothed_status_string}
        """
        smoothed = {}
        for seat_id, status in seat_statuses.items():
            smoothed[seat_id] = self.update(seat_id, status)
        return smoothed
    
    def reset(self, seat_id=None):
        """
        Reset history for a seat or all seats
        
        Args:
            seat_id: Specific seat to reset, or None for all seats
        """
        if seat_id:
            seat_id = seat_id.lower()
            if seat_id in self.history:
                self.history[seat_id].clear()
                self.transition_counters[seat_id] = 0
        else:
            # Reset all
            self.history.clear()
            self.transition_counters.clear()
            self.last_output.clear()
    
    def get_history(self, seat_id):
        """
        Get status history for a seat (for debugging)
        
        Args:
            seat_id: Seat identifier
        
        Returns:
            list: History of statuses
        """
        seat_id = seat_id.lower()
        if seat_id in self.history:
            return list(self.history[seat_id])
        return []
    
    def get_stats(self):
        """
        Get statistics about smoothing (for debugging/monitoring)
        
        Returns:
            dict: Statistics
        """
        stats = {
            'method': self.method,
            'window_size': self.window_size,
            'tracked_seats': len(self.history),
            'seats': {}
        }
        
        for seat_id, history in self.history.items():
            stats['seats'][seat_id] = {
                'history_length': len(history),
                'current_status': self.last_output.get(seat_id, 'UNKNOWN'),
                'transition_counter': self.transition_counters.get(seat_id, 0)
            }
        
        return stats