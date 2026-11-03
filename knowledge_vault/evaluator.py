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
    has_comparison = (
        ("28%" in full_text or "25%" in full_text or "15,000" in full_text or "15000" in full_text) and 
        ("0%" in full_text or "100%" in full_text or "999" in full_text or "2,498" in full_text or "2498" in full_text or "1,000" in full_text)
    )

    if has_rupee and has_numbers and has_comparison:
        math_score = 2.0
    elif has_rupee and has_numbers:
        math_score = 1.4
    else:
        math_score = 0.6
        recommendations.append("Add empirical rupee-for-rupee math (e.g., Year 1 ₹2,498, Year 2+ ₹999/yr vs ₹15,000 legacy trap).")
    scores["empirical_proof"] = math_score

    # 3. Contrast Ratio (Villain vs Hero) (0-2 pts)
    contrast_score = 0.0
    has_villain = any(v in full_text for v in ["aggregator", "swiggy", "zomato", "petpooja", "monopoly", "trap", "lock-in", "paper kot"])
    has_hero = any(h in full_text for h in ["cafe qr", "direct", "0%", "sachet", "thermal", "keep 100%", "999", "2,498", "base plan", "pay-only"])

    if has_villain and has_hero:
        contrast_score = 2.0
    elif has_hero:
        contrast_score = 1.2
        recommendations.append("Explicitly contrast against the incumbent villain (e.g., Petpooja ₹15,000 upfront).")
    else:
        contrast_score = 0.5
    scores["contrast_ratio"] = contrast_score

    # 4. Cognitive Ease & Anti-AI Gauntlet (Profound & Wisprflow Rules) (0-2 pts)
    ease_score = 2.0
    words = headline.split()
    if len(words) > 8:
        ease_score -= 0.4
        recommendations.append(f"Headline is {len(words)} words; trim to 7 words or fewer for instant comprehension.")

    # Em Dash Rule
    if "—" in caption or "—" in headline or "—" in script:
        ease_score -= 0.3
        recommendations.append("Profound Anti-AI Rule: Zero em dashes (—). Replace with plain commas, periods, or colons.")

    # Negative Parallelism / Contrast Framing Rule
    if any(nf in full_text for nf in ["it's not about", "this isn't about", "it's not just", "not only"]):
        ease_score -= 0.3
        recommendations.append("Wisprflow Rule: Eliminate contrast framing ('it's not X, it's Y'). State what Cafe QR is directly.")

    # Profound & Wisprflow Banned Vocabulary
    banned_ai_words = [
        "revolutionize", "elevate", "synergy", "paradigm", "cutting edge", "cutting-edge",
        "game-changer", "game-changing", "robust", "seamless", "seamlessly", "innovative",
        "leverage", "utilize", "empower", "foster", "garner", "delve", "vibrant",
        "pivotal", "crucial", "vital", "testament", "tapestry", "ecosystem", "unlock"
    ]
    matched_banned = [w for w in banned_ai_words if w in full_text]
    if matched_banned:
        ease_score -= 0.3 * len(matched_banned)
        recommendations.append(f"Anti-AI Gauntlet: Remove banned corporate jargon: {', '.join(matched_banned)}. Use plain operator language.")

    scores["cognitive_ease"] = round(max(0.4, ease_score), 2)

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

    # Legendary Ad Masters Audit (Hormozi, Ogilvy, Schwartz, Williams)
    has_sensory = any(s in full_text for s in ["printer", "thermal", "chime", "rush", "table", "counter", "smoke", "tap", "spit", "ring", "glowing", "neon"])
    has_ogilvy_headline = bool(re.search(r'\d+', headline)) or any(w in headline.lower() for w in ["how", "why", "what", "new", "stop", "alert"])
    has_ogilvy_caption = len(caption) >= 80
    has_schwartz_mechanism = any(m in full_text for m in ["0.8", "thermal", "dynamic upi", "sachet", "pay-only", "base plan", "qr"])
    has_hormozi_magnet = any(m in full_text for m in ["demo", "audit", "calculator", "trial", "standee", "kit", "pilot"])

    masters_audit = {
        "alex_hormozi_lead_magnet": "PASS" if has_hormozi_magnet else "NEEDS_IMPROVEMENT",
        "david_ogilvy_80_20_headline": "PASS" if has_ogilvy_headline else "NEEDS_IMPROVEMENT",
        "david_ogilvy_caption_law": "PASS" if has_ogilvy_caption else "NEEDS_IMPROVEMENT",
        "eugene_schwartz_mechanism": "PASS" if has_schwartz_mechanism else "NEEDS_IMPROVEMENT",
        "roy_williams_sensory_resonance": "PASS" if has_sensory else "NEEDS_IMPROVEMENT"
    }

    if not has_sensory:
        recommendations.append("Wizard of Ads (Roy Williams): Add sensory details (sight of neon QR, sound of thermal printer zipp-zipp, relief of peak rush).")
    if not has_ogilvy_headline:
        recommendations.append("Ogilvy on Advertising: Headline must carry news or specific numbers (never cute puns).")
    if not has_schwartz_mechanism:
        recommendations.append("Breakthrough Advertising (Eugene Schwartz): Highlight Cafe QR's Unique Mechanism (0.8s direct thermal print or ₹999/yr renewal).")
    if not has_hormozi_magnet:
        recommendations.append("100M Leads (Alex Hormozi): Offer a frictionless Grand Slam lead magnet (e.g. Reply DEMO for 2-min unedited video audit).")

    total_score = round(sum(scores.values()), 1)
    grade = "VIRAL_READY" if total_score >= 8.5 else "SOLID_ENGAGING" if total_score >= 7.0 else "NEEDS_OPTIMIZATION"

    return {
        "score": min(10.0, total_score),
        "grade": grade,
        "breakdown": scores,
        "legendary_masters_audit": masters_audit,
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
