import hmac
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()

# Fallback static key if secret key is not set in environment
SECRET_KEY = os.getenv("SECRET_SIGNING_KEY", "agri_guard_super_secure_key_10283").encode('utf-8')

def check_ecological_compliance(proposed_chemicals, ecological_db_rules):
    """
    Validates recommended chemical dosages against environmental safety rules.
    
    proposed_chemicals: list of dicts [{'chemical_id': 'UREA', 'dosage_kg_ha': 150}]
    ecological_db_rules: dict mapping chemical_id -> {'max_limit': float, 'is_restricted': int}
    
    Returns:
    tuple (is_compliant, reason_string)
    """
    for chem in proposed_chemicals:
        chem_id = chem['chemical_id']
        dosage = chem['dosage_kg_ha']
        
        if chem_id in ecological_db_rules:
            rule = ecological_db_rules[chem_id]
            
            # Check restricted chemicals
            if rule['is_restricted'] == 1:
                return False, f"Warning: Recommended chemical '{chem_id}' is a restricted substance and requires municipal approval."
                
            # Check dosage limit
            if dosage > rule['max_limit']:
                return False, f"Violation: Proposed dosage for {chem_id} ({dosage} kg/ha) exceeds the ecological safety limit of {rule['max_limit']} kg/ha."
                
    return True, "Eco-compliance check passed. Recommendations within safe environmental thresholds."

def generate_signed_advisory(farmer_query, recommendation_details):
    """
    Generates a secure HMAC advisory signature to guarantee recommendation integrity.
    
    farmer_query: str
    recommendation_details: str
    
    Returns:
    str (hex representation of signature)
    """
    message = f"{farmer_query}||{recommendation_details}".encode('utf-8')
    signature = hmac.new(SECRET_KEY, message, hashlib.sha256).hexdigest()
    return signature

def verify_advisory_signature(farmer_query, recommendation_details, signature):
    """
    Verifies the integrity of a signed recommendation.
    """
    message = f"{farmer_query}||{recommendation_details}".encode('utf-8')
    expected_sig = hmac.new(SECRET_KEY, message, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected_sig, signature)

if __name__ == "__main__":
    # Test Compliance & Signing
    rules = {
        'UREA': {'max_limit': 300.0, 'is_restricted': 0},
        'GLYPHOSATE': {'max_limit': 2.5, 'is_restricted': 1}
    }
    
    p1 = [{'chemical_id': 'UREA', 'dosage_kg_ha': 180}]
    p2 = [{'chemical_id': 'UREA', 'dosage_kg_ha': 320}]
    p3 = [{'chemical_id': 'GLYPHOSATE', 'dosage_kg_ha': 1.0}]
    
    print("Test 1 (Urea 180):", check_ecological_compliance(p1, rules))
    print("Test 2 (Urea 320):", check_ecological_compliance(p2, rules))
    print("Test 3 (Glyphosate):", check_ecological_compliance(p3, rules))
    
    sig = generate_signed_advisory("Query details", "Recommendation content here")
    print("HMAC Signature:", sig)
    print("Verify True:", verify_advisory_signature("Query details", "Recommendation content here", sig))
    print("Verify False:", verify_advisory_signature("Query details", "Altered content here", sig))
