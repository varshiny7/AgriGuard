import re

# Regex patterns for PII scrubbing
PHONE_REGEX = re.compile(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b')
EMAIL_REGEX = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
GPS_REGEX = re.compile(r'\b(-?\d{1,3}\.\d+)\s*[NnSs]?\s*,\s*(-?\d{1,3}\.\d+)\s*[EeWw]?\b')

def anonymize_user_input(text, region_lookup_fn=None):
    """
    Scrubs PII (phone numbers, email addresses, exact GPS coordinates) from user inputs.
    
    If GPS coordinates are found, maps them to a regional zone ID (e.g. ZONE_NORTH)
    using region_lookup_fn.
    
    Returns:
    tuple (anonymized_text, redacted_pii_log, resolved_region_id)
    """
    redacted_pii = []
    resolved_region_id = None
    
    # 1. Scrub Phone Numbers
    phones = PHONE_REGEX.findall(text)
    if phones:
        redacted_pii.extend([("phone", phone) for phone in phones])
        text = PHONE_REGEX.sub("[REDACTED_PHONE]", text)
        
    # 2. Scrub Emails
    emails = EMAIL_REGEX.findall(text)
    if emails:
        redacted_pii.extend([("email", email) for email in emails])
        text = EMAIL_REGEX.sub("[REDACTED_EMAIL]", text)
        
    # 3. Handle GPS Coordinates
    gps_matches = GPS_REGEX.findall(text)
    if gps_matches:
        for match in gps_matches:
            lat, lon = float(match[0]), float(match[1])
            redacted_pii.append(("gps", f"{lat}, {lon}"))
            
            # Simple quadrant mapping to resolve regions if lookup function isn't provided
            if region_lookup_fn:
                try:
                    resolved_region_id = region_lookup_fn(lat, lon)
                except Exception as e:
                    print(f"Error in coordinate lookup: {e}")
            
            if not resolved_region_id:
                # Default mapping logic
                if lat > 25.0:
                    resolved_region_id = "ZONE_NORTH"
                elif lat < 15.0:
                    resolved_region_id = "ZONE_SOUTH"
                else:
                    resolved_region_id = "ZONE_VALLEY"
                    
        text = GPS_REGEX.sub(f"[REDACTED_COORDINATES - resolved to {resolved_region_id}]", text)
        
    return text, redacted_pii, resolved_region_id

if __name__ == "__main__":
    # Test Scrubbing
    raw_input = "Farmer John Doe (Phone: +1-555-019-2834, email: john@farm.com) reported crop issue at location 28.6139, 77.2090. Need fertilizer suggestions."
    anon, logs, region = anonymize_user_input(raw_input)
    print("Anonymized:", anon)
    print("PII Logs:", logs)
    print("Region:", region)
