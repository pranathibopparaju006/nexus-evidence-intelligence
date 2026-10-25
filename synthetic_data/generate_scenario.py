import json
import random
from datetime import datetime, timedelta
import uuid
import os


def generate_product_misinfo_scenario():
    """
    Generate synthetic scenario: Product safety misinformation campaign.
    Non-political, suitable for academic demonstration.
    """
    scenario = {
        "name": "Product Safety Narrative Evolution",
        "description": "Synthetic dataset showing coordinated misinformation about a fictional product",
        "ground_truth": {
            "coordinated_accounts": ["bot_001", "bot_002", "bot_003"],
            "organic_accounts": ["user_001", "user_002", "user_003"],
            "narrative_sequence": [
                "initial_concern",
                "safety_claim",
                "amplification",
                "counter_narrative"
            ]
        },
        "content": []
    }
    
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    
    # Phase 1: Initial concern (organic)
    scenario["content"].append({
        "id": str(uuid.uuid4()),
        "text": "Has anyone else noticed the new XYZ phone getting warm during charging? Just wondering if this is normal.",
        "author": "user_001",
        "timestamp": base_time.isoformat(),
        "platform": "forum",
        "type": "organic"
    })
    
    # Phase 2: Safety claim (coordinated - mutation 1)
    scenario["content"].append({
        "id": str(uuid.uuid4()),
        "text": "BREAKING: XYZ phones are FIRE HAZARDS. Multiple reports of overheating leading to potential battery explosions. This is a serious safety issue that the company is hiding.",
        "author": "bot_001",
        "timestamp": (base_time + timedelta(hours=2)).isoformat(),
        "platform": "social_media",
        "type": "coordinated",
        "mutation": "emotional_escalation"
    })
    
    # Phase 3: Amplification (coordinated - similar message)
    scenario["content"].append({
        "id": str(uuid.uuid4()),
        "text": "URGENT: XYZ phone overheating is NOT normal. Battery explosion risk confirmed by multiple users. Share this to warn others! #XYZDanger",
        "author": "bot_002",
        "timestamp": (base_time + timedelta(hours=2, minutes=15)).isoformat(),
        "platform": "social_media",
        "type": "coordinated",
        "mutation": "linguistic_reformulation"
    })
    
    # Phase 4: Screenshot/meme (coordinated - cross-modal)
    scenario["content"].append({
        "id": str(uuid.uuid4()),
        "text": "[IMAGE: Fake news screenshot claiming XYZ recall]",
        "author": "bot_003",
        "timestamp": (base_time + timedelta(hours=3)).isoformat(),
        "platform": "social_media",
        "type": "coordinated",
        "mutation": "cross_modal",
        "image_ocr": "EXCLUSIVE: XYZ phones recalled due to fire hazard. Company stock plummets."
    })
    
    # Phase 5: Counter-narrative (organic)
    scenario["content"].append({
        "id": str(uuid.uuid4()),
        "text": "I've been using the XYZ phone for months with no issues. The heating is within normal parameters for fast charging. Some people are spreading misinformation.",
        "author": "user_002",
        "timestamp": (base_time + timedelta(hours=5)).isoformat(),
        "platform": "forum",
        "type": "organic"
    })
    
    return scenario


def generate_security_rumor_scenario():
    """
    Generate synthetic scenario: Security breach rumor evolution.
    """
    scenario = {
        "name": "Security Breach Rumor Evolution",
        "description": "Synthetic dataset showing evolution of a security incident rumor",
        "content": []
    }
    
    base_time = datetime(2024, 2, 15, 9, 0, 0)
    
    # Initial rumor
    scenario["content"].append({
        "id": str(uuid.uuid4()),
        "text": "Heard that ABC Corp had a data breach last night. Can anyone confirm?",
        "author": "employee_001",
        "timestamp": base_time.isoformat(),
        "platform": "internal_chat",
        "type": "organic"
    })
    
    # Mutation: Escalation
    scenario["content"].append({
        "id": str(uuid.uuid4()),
        "text": "CONFIRMED: ABC Corp suffered MASSIVE data breach. Millions of customer records exposed. Company is trying to cover it up.",
        "author": "unknown_001",
        "timestamp": (base_time + timedelta(minutes=30)).isoformat(),
        "platform": "social_media",
        "type": "coordinated",
        "mutation": "escalation"
    })
    
    # Mutation: Entity shift
    scenario["content"].append({
        "id": str(uuid.uuid4()),
        "text": "Sources say ABC Corp's subsidiary XYZ Services was the actual target. Customer payment data compromised.",
        "author": "unknown_002",
        "timestamp": (base_time + timedelta(hours=1)).isoformat(),
        "platform": "blog",
        "type": "coordinated",
        "mutation": "entity_shift"
    })
    
    # Official response
    scenario["content"].append({
        "id": str(uuid.uuid4()),
        "text": "ABC Corp Statement: We experienced a minor systems outage, not a data breach. No customer data was compromised. We are investigating the cause.",
        "author": "abc_corp_official",
        "timestamp": (base_time + timedelta(hours=3)).isoformat(),
        "platform": "press_release",
        "type": "official"
    })
    
    return scenario


def generate_corporate_crisis_scenario():
    """
    Generate synthetic scenario: Corporate crisis with coordinated attack.
    """
    scenario = {
        "name": "Corporate Crisis Narrative Attack",
        "description": "Coordinated narrative attack on fictional company",
        "content": []
    }
    
    base_time = datetime(2024, 3, 10, 8, 0, 0)
    
    # Initial negative news
    scenario["content"].append({
        "id": str(uuid.uuid4()),
        "text": "TechCorp announces 10% workforce reduction amid market challenges.",
        "author": "news_wire",
        "timestamp": base_time.isoformat(),
        "platform": "news",
        "type": "organic"
    })
    
    # Coordinated negative spin
    scenario["content"].append({
        "id": str(uuid.uuid4()),
        "text": "TechCorp is FAILING. Mass layoffs prove the company is collapsing. Sell your stock now before it's too late!",
        "author": "short_seller_001",
        "timestamp": (base_time + timedelta(minutes=45)).isoformat(),
        "platform": "social_media",
        "type": "coordinated",
        "mutation": "emotional_escalation"
    })
    
    # Coordinated meme/image
    scenario["content"].append({
        "id": str(uuid.uuid4()),
        "text": "[IMAGE: TechCorp logo with 'BANKRUPT' text]",
        "author": "meme_account_001",
        "timestamp": (base_time + timedelta(hours=1)).isoformat(),
        "platform": "social_media",
        "type": "coordinated",
        "mutation": "visual_amplification"
    })
    
    # Forum discussion
    scenario["content"].append({
        "id": str(uuid.uuid4()),
        "text": "Is TechCorp really in trouble? The layoffs seem concerning but might be strategic restructuring.",
        "author": "analyst_001",
        "timestamp": (base_time + timedelta(hours=2)).isoformat(),
        "platform": "forum",
        "type": "organic"
    })
    
    # Company response
    scenario["content"].append({
        "id": str(uuid.uuid4()),
        "text": "TechCorp: Our restructuring positions us for long-term growth. We remain financially strong with $2B in cash reserves.",
        "author": "techcorp_pr",
        "timestamp": (base_time + timedelta(hours=4)).isoformat(),
        "platform": "press_release",
        "type": "official"
    })
    
    return scenario


def save_scenario(scenario, filename):
    """Save scenario to JSON file."""
    os.makedirs("synthetic_data/output", exist_ok=True)
    filepath = f"synthetic_data/output/{filename}"
    with open(filepath, 'w') as f:
        json.dump(scenario, f, indent=2)
    print(f"Saved: {filepath}")


if __name__ == "__main__":
    # Generate all scenarios
    product_scenario = generate_product_misinfo_scenario()
    save_scenario(product_scenario, "product_misinfo.json")
    
    security_scenario = generate_security_rumor_scenario()
    save_scenario(security_scenario, "security_rumor.json")
    
    corporate_scenario = generate_corporate_crisis_scenario()
    save_scenario(corporate_scenario, "corporate_crisis.json")
    
    print("\nAll synthetic scenarios generated successfully!")
    print("\nScenarios include:")
    print("1. Product Misinformation - Safety rumors about fictional product")
    print("2. Security Rumor - Data breach rumor evolution")
    print("3. Corporate Crisis - Coordinated narrative attack on company")
    print("\nEach scenario includes ground truth labels for evaluation.")
