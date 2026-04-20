"""Combines per-sensor cues to compute a composite student focus score."""

import time

# Track consecutive states for stability
class FocusStateTracker:
    def __init__(self):
        self.eye_closed_frames = 0
        self.yawning_frames = 0
        self.laughing_frames = 0
        self.distracted_frames = 0
        self.last_update = time.time()

    def update(self, gaze, head_direction, yawn, laugh):
        """Update state tracking and return stability factors."""
        current_time = time.time()

        # Reset counters if too much time has passed (new session)
        if current_time - self.last_update > 30:  # 30 second reset
            self.eye_closed_frames = 0
            self.yawning_frames = 0
            self.laughing_frames = 0
            self.distracted_frames = 0

        self.last_update = current_time

        # Update counters
        if gaze == "Eyes Closed":
            self.eye_closed_frames += 1
        else:
            self.eye_closed_frames = max(0, self.eye_closed_frames - 1)

        if yawn:
            self.yawning_frames += 1
        else:
            self.yawning_frames = max(0, self.yawning_frames - 1)

        if laugh:
            self.laughing_frames += 1
        else:
            self.laughing_frames = max(0, self.laughing_frames - 1)

        # Check if looking away from screen
        distracted = (gaze in ["Looking Left", "Looking Right", "Looking Down", "Looking Up"] or
                     head_direction in ["Looking Left", "Looking Right", "Looking Down", "Looking Up",
                                      "Head Tilted Left", "Head Tilted Right"])

        if distracted:
            self.distracted_frames += 1
        else:
            self.distracted_frames = max(0, self.distracted_frames - 1)

        # Return stability factors (higher = more consistent behavior)
        return {
            'eye_closed_stability': min(1.0, self.eye_closed_frames / 10),  # Max at 10 frames
            'yawning_stability': min(1.0, self.yawning_frames / 5),       # Max at 5 frames
            'laughing_stability': min(1.0, self.laughing_frames / 3),     # Max at 3 frames
            'distraction_stability': min(1.0, self.distracted_frames / 8) # Max at 8 frames
        }

# Global state tracker
state_tracker = FocusStateTracker()

def normalize(value, min_value, max_value):
    if max_value <= min_value:
        return 0.0
    return max(0.0, min(1.0, (value - min_value) / (max_value - min_value)))


def compute_focus_score(gaze, head_direction, yawn, laugh, mouth_distance=0.0, mouth_width=0.0, mouth_height=0.0):
    """
    Compute comprehensive focus score based on multiple behavioral cues.

    Parameters:
    - gaze: string indicating eye direction ("Looking Forward", "Eyes Closed", etc.)
    - head_direction: string indicating head orientation
    - yawn: boolean indicating yawning detection
    - laugh: boolean indicating laughing detection
    - mouth_distance: float for yawn intensity
    - mouth_width, mouth_height: floats for laugh intensity

    Returns: float focus score (0-10 scale)
    """
    # Get stability factors
    stability = state_tracker.update(gaze, head_direction, yawn, laugh)

    # Base attention scores (0.0 to 1.0 scale)
    eye_contact_score = 0.0
    if gaze == "Looking Forward":
        eye_contact_score = 1.0
    elif gaze in ("Looking Left", "Looking Right"):
        eye_contact_score = 0.6  # Partial attention
    elif gaze in ("Looking Up", "Looking Down"):
        eye_contact_score = 0.3  # Minimal attention
    elif gaze == "Eyes Closed":
        eye_contact_score = 0.0  # No attention (sleeping)

    head_attention_score = 0.0
    if head_direction == "Looking Forward":
        head_attention_score = 1.0
    elif head_direction in ("Looking Left", "Looking Right"):
        head_attention_score = 0.7
    elif head_direction in ("Looking Up", "Looking Down"):
        head_attention_score = 0.4
    elif head_direction in ("Head Tilted Left", "Head Tilted Right"):
        head_attention_score = 0.2

    # Behavioral penalties
    behavioral_penalty = 0.0

    # Yawning penalty (increases with stability and intensity)
    if yawn:
        yawn_penalty = 0.3 + (stability['yawning_stability'] * 0.4)  # 0.3 to 0.7
        # Increase penalty for wide yawns
        if mouth_distance > 50:  # Threshold for intense yawns
            yawn_penalty += 0.2
        behavioral_penalty += yawn_penalty

    # Laughing penalty (less severe than yawning)
    if laugh:
        laugh_penalty = 0.2 + (stability['laughing_stability'] * 0.2)  # 0.2 to 0.4
        behavioral_penalty += laugh_penalty

    # Eyes closed penalty (severe - indicates sleeping)
    if gaze == "Eyes Closed":
        sleep_penalty = 0.8 + (stability['eye_closed_stability'] * 0.2)  # 0.8 to 1.0
        behavioral_penalty += sleep_penalty

    # Distraction penalty for prolonged looking away
    if stability['distraction_stability'] > 0.5:
        distraction_penalty = stability['distraction_stability'] * 0.4  # Up to 0.4
        behavioral_penalty += distraction_penalty

    # Ensure penalty doesn't exceed 1.0
    behavioral_penalty = min(1.0, behavioral_penalty)

    # Expression score (1.0 = neutral, lower = distracted behaviors)
    expression_score = 1.0 - behavioral_penalty

    # Weighted combination
    # Weights: Eye contact (35%), Head direction (30%), Expression (35%)
    weights = [0.35, 0.30, 0.35]
    scores = [eye_contact_score, head_attention_score, expression_score]

    # Compute weighted average
    focus_score = sum(w * s for w, s in zip(weights, scores))

    # Add small baseline score to prevent zero scores
    focus_score = max(0.1, focus_score)

    # Convert to 0-10 scale and round to 1 decimal place
    final_score = round(focus_score * 10, 1)

    return final_score
