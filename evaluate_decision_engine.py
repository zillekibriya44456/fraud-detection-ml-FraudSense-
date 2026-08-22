import pandas as pd
import time
from src.decision_engine import decision_engine

def evaluate():
    print("Evaluating Context-Aware Decision Engine vs Model-Only...")
    
    # Simulate a small validation set
    test_cases = [
        {"desc": "Low Risk Nominal", "prob": 0.10, "amount": 100.0, "behavior": 0.0, "history": "SUFFICIENT", "expected_model": "APPROVE", "expected_context": "APPROVE"},
        {"desc": "Borderline Medium", "prob": 0.45, "amount": 100.0, "behavior": 0.0, "history": "NONE", "expected_model": "VERIFY", "expected_context": "VERIFY"},
        {"desc": "High Value Uncertain", "prob": 0.35, "amount": 150000.0, "behavior": 0.0, "history": "LIMITED", "expected_model": "APPROVE", "expected_context": "VERIFY"},
        {"desc": "Behavioral Anomaly", "prob": 0.45, "amount": 5000.0, "behavior": 0.9, "history": "SUFFICIENT", "expected_model": "VERIFY", "expected_context": "BLOCK"},
        {"desc": "High Risk Fraud", "prob": 0.92, "amount": 5000.0, "behavior": 0.0, "history": "NONE", "expected_model": "BLOCK", "expected_context": "BLOCK"},
    ]
    
    model_only_blocks = 0
    model_only_verif = 0
    context_blocks = 0
    context_verif = 0
    
    for case in test_cases:
        # Model Only (Pre-Step 4 logic: >=0.85 block, >=0.40 verify)
        mo_action = "BLOCK" if case["prob"] >= 0.85 else ("VERIFY" if case["prob"] >= 0.40 else "APPROVE")
        
        # Context Aware
        res = decision_engine.assess_risk(case["prob"], case["amount"], case["behavior"], case["history"])
        ca_action = res["recommended_action"]
        
        print(f"CASE: {case['desc']}")
        print(f"  Model Only: {mo_action}")
        print(f"  Context Aware: {ca_action} ({res['decision_policy']})")
        print("-" * 40)
        
        if mo_action == "BLOCK": model_only_blocks += 1
        if mo_action == "VERIFY": model_only_verif += 1
        
        if ca_action == "BLOCK": context_blocks += 1
        if ca_action == "VERIFY": context_verif += 1
        
    print(f"RESULTS:")
    print(f"Model Only -> Blocks: {model_only_blocks}, Verify: {model_only_verif}")
    print(f"Context Aware -> Blocks: {context_blocks}, Verify: {context_verif}")
    
    # We write the research report based on this structural difference
    
if __name__ == "__main__":
    evaluate()
