# leaf_classifier.py

def classify_size(w_cm, h_cm):
    max_dim = max(w_cm, h_cm)
    if max_dim <= 5:
        return "Small"
    elif 5 < max_dim <= 10:
        return "Medium"
    else:
        return "Large"

def summarize_growth_stage(small, medium, large):
    score = (small * 1) + (medium * 2) + (large * 3)
    if score <= 4:
        return "🌱 Sprout (LV.1)"
    elif 5 <= score <= 6:
        return "🌿 Bud (LV.2)"
    else:
        return "🌼 Bloom (LV.3)"
