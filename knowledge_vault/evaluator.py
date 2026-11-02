import re

def score_creative(campaign_data):
    """
    Evaluates marketing copy and poster data against the Autonomous 10-Point Viral Rubric:
    1. Hook Velocity (0-2 pts)
    2. Empirical Math Proof (0-2 pts)
    3. Contrast Ratio (0-2 pts)
    4. Cognitive Ease (0-2 pts)
    5. CTA Urgency & Risk Reversal (0-2 pts)
    
    Total score: 0 to 10.0
    """
    headline = campaign_data.get("headline", "").upper()
    subtext = campaign_data.get("subtext", "")
    script = campaign_data.get("script", "")
    caption = campaign_data.get("caption", "")
    full_text = f"{headline} {subtext} {script} {caption}".lower()

    scores = {}
    recommendations = []

    # 1. Hook Velocity (0-2 pts)
    hook_score = 0.0
    power_keywords = ["why pay", "stop paying", "swiggy", "zomato", "petpooja", "28%", "commission", "hike", "bill", "₹15,000", "0.8s", "dirty secret"]
    matched_power = [kw for kw in power_keywords if kw in full_text]
    
    if len(matched_power) >= 3:
        hook_score = 2.0
    elif len(matched_power) >= 1:
        hook_score = 1.5
    else:
        hook_score = 0.5
        recommendations.append("Strengthen headline with high-contrast power words (e.g., 'Stop Paying', '28% Commission').")
    scores["hook_velocity"] = hook_score

    # 2. Empirical Math Proof (0-2 pts)
    math_score = 0.0
    has_rupee = "₹" in full_text or "rupee" in full_text
    has_numbers = bool(re.search(r'\d+', headline + " " + subtext))
    has_comparison = ("28%" in full_text or "25%" in full_text) and ("0%" in full_text or "100%" in full_text or "99" in full_text)

    if has_rupee and has_numbers and has_comparison:
        math_score = 2.0
    elif has_rupee and has_numbers:
        math_score = 1.4
    else:
        math_score = 0.6
        recommendations.append("Add empirical rupee-for-rupee math (e.g., ₹500 bill vs ₹140 loss).")
    scores["empirical_proof"] = math_score

    # 3. Contrast Ratio (Villain vs Hero) (0-2 pts)
    contrast_score = 0.0
    has_villain = any(v in full_text for v in ["aggregator", "swiggy", "zomato", "petpooja", "monopoly", "trap", "lock-in", "paper kot"])
    has_hero = any(h in full_text for h in ["cafe qr", "direct", "0%", "sachet", "thermal", "keep 100%"])

    if has_villain and has_hero:
        contrast_score = 2.0
    elif has_hero:
        contrast_score = 1.2
        recommendations.append("Explicitly contrast against the incumbent villain (e.g., Petpooja ₹15,000 upfront).")
    else:
        contrast_score = 0.5
    scores["contrast_ratio"] = contrast_score

    # 4. Cognitive Ease (0-2 pts)
    ease_score = 2.0
    words = headline.split()
    if len(words) > 8:
        ease_score -= 0.5
        recommendations.append(f"Headline is {len(words)} words; trim to 7 words or fewer for instant comprehension.")

    banned_cliches = ["revolutionize", "elevate", "synergy", "paradigm", "cutting edge", "best food"]
    for cliche in banned_cliches:
        if cliche in full_text:
            ease_score -= 0.5
            recommendations.append(f"Remove generic buzzword '{cliche}' to preserve raw operator authenticity.")
    scores["cognitive_ease"] = max(0.5, ease_score)

    # 5. CTA Urgency & Risk Reversal (0-2 pts)
    cta_score = 0.0
    has_free = "free" in full_text
    has_action = any(a in full_text for a in ["demo", "reply", "comment", "trial", "kit"])

    if has_free and has_action:
        cta_score = 2.0
    elif has_action:
        cta_score = 1.3
    else:
        cta_score = 0.5
        recommendations.append("Strengthen CTA with a zero-risk reversal (e.g. 'Free 7-Day Trial + Standees').")
    scores["cta_urgency"] = cta_score

    total_score = round(sum(scores.values()), 1)
    grade = "VIRAL_READY" if total_score >= 8.5 else "SOLID_ENGAGING" if total_score >= 7.0 else "NEEDS_OPTIMIZATION"

    return {
        "score": min(10.0, total_score),
        "grade": grade,
        "breakdown": scores,
        "recommendations": recommendations if recommendations else ["Creative perfectly optimized against viral benchmark rules."]
    }

if __name__ == "__main__":
    sample = {
        "headline": "WHY PAY 28% COMMISSION ON EVERY ORDER?",
        "subtext": "Aggregators just raised platform fees again. Stop giving away your profit margin.",
        "script": "On a 500 rupee order, 140 rupees goes straight to aggregators. Switch to Cafe QR.",
        "caption": "Reply DEMO for Free 7-Day Trial"
    }
    result = score_creative(sample)
    print("Rubric Score Result:", result)
