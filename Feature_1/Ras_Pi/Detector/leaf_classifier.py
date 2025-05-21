# leaf_classifier.py

def classify_size(w_cm, h_cm):
    max_dim = max(w_cm, h_cm)
    if max_dim <= 5:
        return "Small"
    elif 5 < max_dim <= 10:
        return "Medium"
    else:
        return "Large"

def summarize_tower_growth(small, medium, large):
    total = small + medium + large
    score = (small * 1) + (medium * 2) + (large * 3)
    avg = score / total if total else 0

    if avg <= 1.5:
        return "🌱 Tower Stage: Sprout (LV.1)"
    elif avg <= 2.2:
        return "🌿 Tower Stage: Bud (LV.2)"
    else:
        return "🌼 Tower Stage: Bloom (LV.3)"
