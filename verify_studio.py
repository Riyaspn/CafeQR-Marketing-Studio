import os
import json
from pathlib import Path

from config import DRAFTS_DIR
import creative_brain
import poster_engine
from knowledge_vault.evaluator import score_creative

def test_full_pipeline():
    print("=" * 60)
    print("🧪 Running End-to-End Verification of CafeQR Marketing Studio")
    print("=" * 60)

    # 1. Test Creative Brain & Evaluator
    topic = {
        "title": "Zomato & Swiggy Hike Platform Fees as Restaurants Protest 28% Commission",
        "source": "F&B National Digest",
        "category": "AGGREGATOR_EXPLOITATION"
    }
    
    print("\n1. Generating creative campaign from trend...")
    campaign = creative_brain.generate_creative_campaign(topic)
    print(f"   Headline: {campaign['headline']}")
    print(f"   Subtext:  {campaign['subtext']}")
    
    assert "evaluation" in campaign, "Evaluation missing from campaign!"
    ev = campaign["evaluation"]
    print(f"   Viral Score: {ev['score']}/10.0 ({ev['grade']})")
    print(f"   Breakdown: {ev['breakdown']}")
    print(f"   Recommendations: {ev['recommendations']}")

    # 2. Test Poster Rendering
    print("\n2. Rendering high-res agency editorial poster (1080x1350)...")
    poster_path = poster_engine.render_poster(campaign, filename="e2e_verified_agency_editorial.png")
    print(f"   Poster saved to: {poster_path}")
    assert Path(poster_path).exists(), "Poster file was not created!"
    assert Path(poster_path).stat().st_size > 50000, "Poster file size is suspiciously small!"
    print(f"   Poster verified! Size: {Path(poster_path).stat().st_size:,} bytes")

    # 3. Test Live Scorecard on Dynamic Copy
    print("\n3. Testing dynamic copy scoring with custom input...")
    custom_copy = {
        "headline": "STOP PAYING ₹15,000 UPFRONT FOR POS",
        "subtext": "Why lock your cash into bloated 1990s legacy software when Cafe QR is ₹99/month?",
        "script": "On a 500 rupee order, 140 rupees goes straight to aggregators. Switch to Cafe QR.",
        "caption": "Reply DEMO for Free 7-Day Trial"
    }
    custom_score = score_creative(custom_copy)
    print(f"   Custom Copy Score: {custom_score['score']}/10.0 ({custom_score['grade']})")
    assert custom_score['score'] >= 8.5, f"Expected viral score >= 8.5, got {custom_score['score']}"

    print("\n" + "=" * 60)
    print("🎉 ALL SYSTEMS FULLY OPERATIONAL AND VERIFIED!")
    print("=" * 60)

if __name__ == "__main__":
    test_full_pipeline()
