import os
import json
from skills.soil_optimizer import optimize_fertilizer
from skills.irrigation_scheduler import calculate_irrigation
from security.validator_signer import check_ecological_compliance, generate_signed_advisory
from security.anonymizer import anonymize_user_input

class AgriGuardOrchestrator:
    def __init__(self, mcp_server):
        self.mcp = mcp_server
        # Load API keys or use local offline simulation
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.is_offline = not bool(self.api_key)
        
    def run_workflow(self, raw_input, crop_name, current_n, current_p, current_k, current_ph, region_id):
        """
        Runs the full secure multi-agent coordination pipeline.
        
        1. Anonymize user input (Security Input Gate).
        2. Query MCP database.
        3. Solve mathematical optimization models (Skills).
        4. Coordinate agents (Agronomist, Market, Compliance).
        5. Verify results (Security Output Gate).
        6. Apply HMAC signature.
        """
        # Step 1: Input Anonymizer Gate
        anon_input, redacted_logs, resolved_region = anonymize_user_input(raw_input)
        if not region_id:
            region_id = resolved_region or "ZONE_VALLEY"
            
        print(f"[Security] Input anonymized. Region resolved to: {region_id}")
        
        # Step 2: Query MCP Database
        soil_needs = self.mcp.get_soil_requirements(crop_name)
        if "error" in soil_needs:
            return {"success": False, "error": soil_needs["error"]}
            
        weather = self.mcp.get_weather_data(region_id, "2026-07-01") # Sample date
        prices = self.mcp.get_market_prices(crop_name, region_id)
        eco_rules = self.mcp.get_ecological_restrictions()
        suitability = self.mcp.get_crop_suitability(region_id, crop_name)
        
        # Step 3: Run Mathematics Skills
        target_npk = [soil_needs['ideal_n'], soil_needs['ideal_p'], soil_needs['ideal_k']]
        current_npk = [current_n, current_p, current_k]
        
        fertilizer_rec = optimize_fertilizer(current_npk, target_npk)
        
        irrigation_rec = calculate_irrigation(
            temp_c=weather.get('temp_c', 25.0),
            humidity=weather.get('humidity', 60.0),
            precip_mm=weather.get('precip_mm', 0.0),
            solar_radiation=weather.get('solar_radiation', 18.0),
            kc=soil_needs.get('kc_coefficient', 1.15)
        )
        
        # Step 4: Multi-Agent Synthesis (with Infinite Loop Protection)
        agent_iterations = 0
        max_iterations = 5
        proposed_chemicals = [
            {'chemical_id': 'UREA', 'dosage_kg_ha': fertilizer_rec['urea_kg']},
            {'chemical_id': 'DAP', 'dosage_kg_ha': fertilizer_rec['dap_kg']},
            {'chemical_id': 'MOP', 'dosage_kg_ha': fertilizer_rec['mop_kg']}
        ]
        
        advisory_text = ""
        compliance_passed = False
        compliance_message = ""
        
        while agent_iterations < max_iterations:
            agent_iterations += 1
            print(f"[Agent Loop] Iteration {agent_iterations} checking compliance...")
            
            # Compliance Guardian (Security Agent Check)
            is_valid, msg = check_ecological_compliance(proposed_chemicals, eco_rules)
            
            if is_valid:
                compliance_passed = True
                compliance_message = msg
                print(f"[Agent Loop] Compliance check passed.")
                break
            else:
                # If violation found, rewrite the proposed chemicals to adjust dosage
                # (Simulates Agronomist rewriting advice after being corrected by Guardian)
                print(f"[Agent Loop] Violation detected: {msg}. Adjusting chemicals to safety thresholds.")
                adjusted = []
                for chem in proposed_chemicals:
                    c_id = chem['chemical_id']
                    c_dosage = chem['dosage_kg_ha']
                    if c_id in eco_rules:
                        limit = eco_rules[c_id]['max_limit']
                        if c_dosage > limit:
                            # Trim to safety limit
                            c_dosage = limit
                    adjusted.append({'chemical_id': c_id, 'dosage_kg_ha': c_dosage})
                proposed_chemicals = adjusted
                
        # Synthesize advisory report (Agent-style narrative)
        ph_status = "ideal" if soil_needs['min_ph'] <= current_ph <= soil_needs['max_ph'] else "outside bounds"
        
        advisory_text = (
            f"--- AGRIGUARD OFFICIAL ADVISORY ---\n"
            f"Target Crop: {crop_name} (Suitability Index: {suitability:.2f})\n"
            f"Region: {region_id}\n\n"
            f"[SOIL DIAGNOSTIC]\n"
            f"Current pH: {current_ph} (Ideal: {soil_needs['min_ph']} - {soil_needs['max_ph']}) - Soil condition is {ph_status}.\n"
            f"NPK deficiency corrected via fertilizer optimizer.\n\n"
            f"[RECOMMENDED APPLICATION PATHWAY]\n"
            f"- Urea (N source): {proposed_chemicals[0]['dosage_kg_ha']} kg/hectare\n"
            f"- DAP (P source): {proposed_chemicals[1]['dosage_kg_ha']} kg/hectare\n"
            f"- MOP (K source): {proposed_chemicals[2]['dosage_kg_ha']} kg/hectare\n"
            f"Total estimated fertilizer cost: ${fertilizer_rec['total_cost']:.2f} per hectare\n\n"
            f"[IRRIGATION & WATER MANAGEMENT]\n"
            f"Calculated daily reference evapotranspiration (ET0): {irrigation_rec['et0_mm_day']} mm/day\n"
            f"Net daily irrigation required: {irrigation_rec['net_irrigation_depth_mm']} mm depth\n"
            f"Total watering volume required: {irrigation_rec['irrigation_volume_liters']:.2f} Liters/hectare/day\n\n"
            f"[REGULATORY & COMPLIANCE FOOTPRINT]\n"
            f"{compliance_message}\n"
        )
        
        # Step 5: Generate HMAC Signature (Security Output Gate)
        signature = generate_signed_advisory(anon_input, advisory_text)
        
        return {
            "success": True,
            "anonymized_query": anon_input,
            "resolved_region": region_id,
            "redacted_pii": redacted_logs,
            "suitability_score": suitability,
            "fertilizer_plan": {
                "urea_kg": proposed_chemicals[0]['dosage_kg_ha'],
                "dap_kg": proposed_chemicals[1]['dosage_kg_ha'],
                "mop_kg": proposed_chemicals[2]['dosage_kg_ha'],
                "total_cost": fertilizer_rec['total_cost'],
                "status": fertilizer_rec['status']
            },
            "irrigation_plan": irrigation_rec,
            "compliance": {
                "passed": compliance_passed,
                "message": compliance_message,
                "iterations_required": agent_iterations
            },
            "advisory_report": advisory_text,
            "digital_signature": signature
        }
