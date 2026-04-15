"""Combines per-sensor cues to compute a composite student focus score."""

def normalize(value, min_value, max_value):
    if max_value <= min_value:
        return 0.0
    return max(0.0, min(1.0, (value - min_value) / (max_value - min_value)))


def compute_focus_score(gaze, head_direction, yawn, laugh):
    eye_contact = 1.0 if gaze == "Looking Forward" else 0.4 if gaze in ("Looking Left", "Looking Right") else 0.0
    head_attention = 1.0 if head_direction == "Looking Forward" else 0.4 if head_direction in ("Looking Left", "Looking Right") else 0.0

    exp = 0.0
    if yawn:
        exp -= 0.5
    if laugh:
        exp -= 0.3
    exp = max(-1.0, min(1.0, exp))
    expression_score = 1.0 + exp

    # Balance weights - sum 1
    score = (0.4 * eye_contact) + (0.3 * head_attention) + (0.2 * expression_score) + 0.1
    score = max(0, min(1, score))

    return round(score * 10, 1)
