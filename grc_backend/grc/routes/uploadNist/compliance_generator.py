"""
Compliance and Risk Records Generator

This module generates compliance and risk records from Excel files containing subpolicy data.
It uses OpenAI's language models via LangChain to create detailed compliance and risk records.

Usage:
    1. As a standalone script:
        python text_generate.py
    
    2. As an imported module in other scripts:
        from text_generate import generate_compliance_and_risk
        
        compliance, risk, comp_file, risk_file = generate_compliance_and_risk(
            excel_file_path="input.xlsx",
            output_prefix="output",
            output_dir="output_folder"
        )

Functions:
    - generate_compliance_and_risk(): Main function to generate records (can be called from other scripts)
    - process_excel_data(): Process Excel data and generate records
    - setup_llm_chain(): Setup LangChain with OpenAI
    - load_excel_data(): Load data from Excel file
    - save_results(): Save results to Excel files
    - main(): CLI entry point for standalone usage

Requirements:
    - OPENAI_API_KEY must be set in environment variables or .env file
    - Input Excel file must contain: SubPolicyId, SubPolicyName, Description, Control columns
"""

import os
import pandas as pd
from dotenv import load_dotenv
import json
import time
from datetime import datetime
 
# Use Django settings for OpenAI API key
from django.conf import settings
from ...debug_utils import debug_print

# Shared AI config
from ...ai.config import (
    AI_PROVIDER,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL_DEFAULT,
    OLLAMA_TIMEOUT,
    OLLAMA_TEMPERATURE
)
import requests
import re
from ...ai.service import get_ai_service
from ...ai.tasks import policy as policy_tasks

def _normalize_compliance_fields(compliance: dict, fallback_title: str = "", fallback_risk: dict | None = None) -> dict:
    """
    Ensure key fields like ComplianceItemDescription and PossibleDamage are always present.
    This is important so the UI Compliance Description and Possible Damage fields are populated.
    """
    if not isinstance(compliance, dict):
        return compliance

    # Normalize description
    desc = (
        compliance.get("ComplianceItemDescription")
        or compliance.get("Description")
        or compliance.get("description")
        or compliance.get("ComplianceDescription")
        or compliance.get("details")
    )
    if not desc and fallback_title:
        desc = f"Compliance requirement for: {fallback_title}"
    compliance["ComplianceItemDescription"] = desc or ""

    # Normalize possible damage (from compliance or linked risk)
    dmg = (
        compliance.get("PossibleDamage")
        or compliance.get("Possible_Damage")
        or compliance.get("Damage")
        or (fallback_risk or {}).get("PossibleDamage")
        or (fallback_risk or {}).get("Possible_Damage")
        or (fallback_risk or {}).get("Damage")
    )
    # If still empty, synthesize a generic but useful sentence so UI is never blank
    if not dmg:
        crit = (compliance.get("Criticality") or "").strip().lower()
        if crit == "high" or crit == "critical":
            dmg = f"Failure to comply with '{fallback_title or 'this requirement'}' may lead to severe security breaches, regulatory fines, and significant business disruption."
        elif crit == "medium":
            dmg = f"Failure to comply with '{fallback_title or 'this requirement'}' may increase exposure to security incidents, audit findings, and operational inefficiencies."
        else:
            dmg = f"Failure to comply with '{fallback_title or 'this requirement'}' may introduce avoidable risk and weaken overall control effectiveness."

    compliance["PossibleDamage"] = dmg

    return compliance

def get_api_key():
    """Get OpenAI API key from Django settings"""
    api_key = getattr(settings, 'OPENAI_API_KEY', None)
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found in Django settings. "
            "Please set it in .env file and restart Django server."
        )
    return api_key
 
def load_excel_data(file_path):
    """Load data from Excel file"""
    try:
        df = pd.read_excel(file_path)
        return df
    except Exception as e:
        debug_print(f"Error loading Excel file: {e}")
        return None
 
def _generate_compliance_with_ai(subpolicy_name, description, control, current_date):
    """
    Generate compliance records using the centralized policy.generate_subpolicy_compliances AI task.
    This delegates to the shared task implementation in grc.ai.tasks.policy so that the
    prompt shape and JSON contract stay consistent across the platform.
    """
    print(f"[ROUTE-COMPLIANCE] _generate_compliance_with_ai: subpolicy={str(subpolicy_name)[:50] if subpolicy_name else 'N/A'}...")
    service = get_ai_service()

    payload = {
        "subpolicy_title": subpolicy_name or "Policy requirement",
        "subpolicy_description": description or "(no description)",
        "control": control or description or subpolicy_name or "",
        "current_date": current_date,
    }

    # Use centralized task helper (this already calls generate_json with the correct task_name)
    try:
        compliances = policy_tasks.generate_subpolicy_compliances(
            service,
            payload,
            metadata=None,
            options=None,
        )
        # For backward compatibility with the rest of this module, wrap into the older
        # {"compliances": [...]} envelope expected by process_excel_data.
        result = {"compliances": compliances}
    except Exception as e:
        debug_print(f"Error in centralized generate_subpolicy_compliances: {e}")
        result = {"compliances": []}

    _n = len(result.get("compliances", [])) if isinstance(result, dict) and result else 0
    print(f"[ROUTE-COMPLIANCE] policy.generate_subpolicy_compliances DONE: compliances={_n}")
    return result

def setup_llm_chain(api_key=None):
    """
    DEPRECATED: This function is kept for backward compatibility.
    Use _generate_compliance_with_ai() directly for Phase 1, 2, 3 optimizations.
    """
    # Return a mock chain object that can be invoked
    class MockChain:
        def invoke(self, inputs):
            subpolicy_name = inputs.get("SubPolicyName", "")
            description = inputs.get("Description", "")
            control = inputs.get("Control", "")
            current_date = inputs.get("current_date", datetime.now().strftime("%Y-%m-%d"))
            
            # Use simple AI generation
            result = _generate_compliance_with_ai(
                subpolicy_name, description, control, current_date
            )
            
            # Return in LangChain-compatible format
            class MockResponse:
                def __init__(self, content):
                    self.content = json.dumps(content) if isinstance(content, dict) else content
            
            return MockResponse(result)
    
    return MockChain()
 
def process_excel_data(df, chain=None):
    """
    Process each row of Excel data and generate separate compliance and risk records.
    Uses simple direct AI calls - no optimizations.
    """
    compliance_results = []
    risk_results = []
   
    # Check if required columns exist
    required_columns = ["SubPolicyId", "SubPolicyName", "Description", "Control"]
    missing_columns = [col for col in required_columns if col not in df.columns]
   
    if missing_columns:
        debug_print(f"Error: Missing required columns: {', '.join(missing_columns)}")
        debug_print(f"Available columns: {', '.join(df.columns)}")
        return None, None
   
    total_rows = len(df)
    print(f"[ROUTE-COMPLIANCE] process_excel_data: total_rows={total_rows}")
    current_date = datetime.now().strftime("%Y-%m-%d")
    compliance_id_counter = 1  # Track compliance IDs for risk linking
    risk_id_counter = 1  # Track risk IDs
    
    # No caching - simple processing
   
    for index, row in df.iterrows():
        # Plain progress print so you can see it easily in the terminal
        current_row = index + 1
        print(f"[ROUTE-COMPLIANCE] Processing row {current_row}/{total_rows} ({(current_row/total_rows)*100:.1f}% complete)")
        debug_print(f"Processing row {current_row}/{total_rows}...")
       
        try:
            # Extract data from row
            SubPolicyId = int(row["SubPolicyId"])  # Use existing SubPolicyId from Excel
            SubPolicyName = row["SubPolicyName"]
            Description = row["Description"]
            Control = row["Control"]
           
            # Generate compliance records using simple direct AI call
            if chain:
                # Backward compatibility with LangChain chain
                result = chain.invoke({
                    "SubPolicyName": SubPolicyName,
                    "Description": Description,
                    "Control": Control,
                    "current_date": current_date
                })
                try:
                    compliance_data = json.loads(result.content.strip())
                except:
                    compliance_data = result if isinstance(result, dict) else {}
            else:
                # Use simple direct AI call
                compliance_data = _generate_compliance_with_ai(
                    SubPolicyName, Description, Control, current_date
                )
           
            # Parse the JSON response
            try:
                if isinstance(compliance_data, str):
                    compliance_data = json.loads(compliance_data)
                compliances = compliance_data.get("compliances", [])
               
                # Process each compliance and its associated risk
                for compliance in compliances:
                    # Extract risk data if present
                    risk_data = compliance.pop("risk", None)

                    # Normalize key fields so UI always has description and possible damage
                    compliance = _normalize_compliance_fields(
                        compliance,
                        fallback_title=compliance.get("ComplianceTitle", SubPolicyName),
                        fallback_risk=risk_data,
                    )
                   
                    # Create compliance record
                    compliance_record = {
                        "ComplianceId": compliance_id_counter,
                        "SubPolicyId": SubPolicyId,
                        "PreviousComplianceVersionId": None,
                        "Identifier": compliance.get("Identifier", f"COMP-{compliance_id_counter:04d}"),
                        "ComplianceTitle": compliance.get("ComplianceTitle", ""),
                        "ComplianceItemDescription": compliance.get("ComplianceItemDescription", ""),
                        "ComplianceType": compliance.get("ComplianceType", ""),
                        "Scope": compliance.get("Scope", ""),
                        "Objective": compliance.get("Objective", ""),
                        "BusinessUnitsCovered": compliance.get("BusinessUnitsCovered", ""),
                        "IsRisk": compliance.get("IsRisk", 1),
                        "PossibleDamage": compliance.get("PossibleDamage", ""),
                        "mitigation": json.dumps(compliance.get("mitigation", {})),
                        "Criticality": compliance.get("Criticality", ""),
                        "MandatoryOptional": compliance.get("MandatoryOptional", ""),
                        "ManualAutomatic": compliance.get("ManualAutomatic", ""),
                        "Impact": float(compliance.get("Impact", 0)),
                        "Probability": float(compliance.get("Probability", 0)),
                        "MaturityLevel": compliance.get("MaturityLevel", ""),
                        "ActiveInactive": compliance.get("ActiveInactive", "Active"),
                        "PermanentTemporary": compliance.get("PermanentTemporary", "Permanent"),
                        "CreatedByName": compliance.get("CreatedByName", "radha.sharma"),
                        "CreatedByDate": compliance.get("CreatedByDate", current_date),
                        "ComplianceVersion": compliance.get("ComplianceVersion", "1.0"),
                        "Status": compliance.get("Status", ""),
                        "Applicability": compliance.get("Applicability", ""),
                        "PotentialRiskScenarios": compliance.get("PotentialRiskScenarios", ""),
                        "RiskType": compliance.get("RiskType", ""),
                        "RiskCategory": compliance.get("RiskCategory", ""),
                        "RiskBusinessImpact": compliance.get("RiskBusinessImpact", ""),
                        "FrameworkId": None
                    }
                    compliance_results.append(compliance_record)
                   
                    # Create risk record if risk data exists
                    if risk_data:
                        risk_record = {
                            "RiskId": risk_id_counter,
                            "ComplianceId": compliance_id_counter,
                            "RiskTitle": risk_data.get("RiskTitle", ""),
                            "Criticality": risk_data.get("Criticality", compliance.get("Criticality", "")),
                            "PossibleDamage": risk_data.get("PossibleDamage", compliance.get("PossibleDamage", "")),
                            "Category": risk_data.get("Category", compliance.get("RiskCategory", "")),
                            "RiskType": risk_data.get("RiskType", compliance.get("RiskType", "")),
                            "BusinessImpact": risk_data.get("BusinessImpact", compliance.get("RiskBusinessImpact", "")),
                            "RiskDescription": risk_data.get("RiskDescription", ""),
                            "RiskLikelihood": int(risk_data.get("RiskLikelihood", 0)),
                            "RiskImpact": int(risk_data.get("RiskImpact", compliance.get("Impact", 0))),
                            "RiskExposureRating": float(risk_data.get("RiskExposureRating", 0)),
                            "RiskPriority": risk_data.get("RiskPriority", ""),
                            "RiskMitigation": json.dumps(risk_data.get("RiskMitigation", compliance.get("mitigation", {}))),
                            "CreatedAt": risk_data.get("CreatedAt", current_date),
                            "FrameworkId": None,
                            "RiskMultiplierX": float(risk_data.get("RiskMultiplierX", 0.1)),
                            "RiskMultiplierY": float(risk_data.get("RiskMultiplierY", 0.1))
                        }
                        risk_results.append(risk_record)
                        risk_id_counter += 1
                   
                    compliance_id_counter += 1
                   
                debug_print(f"Generated {len(compliances)} compliance and risk records for: {SubPolicyName}")
               
            except json.JSONDecodeError as e:
                debug_print(f"Error parsing JSON response for row {index+1}: {e}")
                debug_print(f"Raw response: {result.content}")
               
        except Exception as e:
            debug_print(f"Error processing row {index+1}: {e}")
   
    return compliance_results, risk_results
 
def save_results(compliance_results, risk_results, output_prefix, output_dir="excel_output_nist"):
    """Save compliance and risk results to separate Excel files"""
   
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
   
    compliance_file = None
    risk_file = None
    
    # Save compliance results
    if compliance_results:
        compliance_file = os.path.join(output_dir, f"{output_prefix}_Compliance.xlsx")
        df_compliance = pd.DataFrame(compliance_results)
        df_compliance.to_excel(compliance_file, index=False)
        debug_print(f"\nCompliance results saved to {compliance_file}")
        debug_print(f"Total compliance records generated: {len(compliance_results)}")
    else:
        debug_print("\nNo compliance records to save.")
   
    # Save risk results
    if risk_results:
        risk_file = os.path.join(output_dir, f"{output_prefix}_Risk.xlsx")
        df_risk = pd.DataFrame(risk_results)
        df_risk.to_excel(risk_file, index=False)
        debug_print(f"Risk results saved to {risk_file}")
        debug_print(f"Total risk records generated: {len(risk_results)}")
    else:
        debug_print("No risk records to save.")
    
    return compliance_file, risk_file
 
def generate_compliance_for_single_subpolicy(
    subpolicy_id,
    subpolicy_name,
    description,
    control,
    api_key=None,
    framework_id=None,
    amendment_date=None,
):
    """
    Generate compliance and risk records for a single subpolicy using simple AI call.
    
    Args:
        subpolicy_id (int): ID of the subpolicy
        subpolicy_name (str): Name of the subpolicy
        description (str): Description of the subpolicy
        control (str): Control information
        api_key (str): OpenAI API key (optional, will use Django settings if not provided)
    
    Returns:
        list: List of compliance records with associated risks
    """
    try:
        current_date = datetime.now().strftime("%Y-%m-%d")
        debug_print(f"\n[AMENDMENT][COMPLIANCE] ▶️ Generating compliances for SubPolicyId={subpolicy_id} | {subpolicy_name}")

        # Cancellation check (best-effort)
        if framework_id:
            try:
                from grc.models import Framework
                fw = Framework.objects.get(FrameworkId=int(framework_id))
                amendments = fw.Amendment if fw.Amendment else []
                if isinstance(amendments, list) and amendments:
                    for a in reversed(amendments):
                        if not isinstance(a, dict):
                            continue
                        if amendment_date and a.get('amendment_date') != amendment_date:
                            continue
                        if a.get('cancel_requested'):
                            debug_print(f"[AMENDMENT][COMPLIANCE] 🛑 Cancel requested - skipping SubPolicyId={subpolicy_id}")
                            return []
                        break
            except Exception:
                pass
        
        # Generate compliance records using simple AI call
        result = _generate_compliance_with_ai(
            subpolicy_name, description, control, current_date
        )
        
        # Handle both dict and string responses
        if isinstance(result, str):
            compliance_data = json.loads(result)
        else:
            compliance_data = result
        
        compliances = compliance_data.get("compliances", [])
        debug_print(f"[AMENDMENT][COMPLIANCE]   ✅ AI returned compliances={len(compliances)}")
        
        # Process each compliance and add subpolicy reference
        processed_compliances = []
        for compliance in compliances:
            # Extract risk data if present
            risk_data = compliance.pop("risk", None)
            
            # Normalize key fields so UI always has description and possible damage
            compliance = _normalize_compliance_fields(
                compliance,
                fallback_title=compliance.get("ComplianceTitle", subpolicy_name),
                fallback_risk=risk_data,
            )

            # Add subpolicy reference
            compliance["SubPolicyId"] = subpolicy_id
            compliance["SubPolicyName"] = subpolicy_name
            
            # Include risk data in compliance record
            if risk_data:
                compliance["risk_details"] = risk_data
            
            processed_compliances.append(compliance)

        # ---- Live printing of what was generated ----
        try:
            for c_idx, c in enumerate(processed_compliances, 1):
                title = (c.get("ComplianceTitle") or c.get("compliance_title") or "").strip()
                ctype = (c.get("ComplianceType") or c.get("compliance_type") or "").strip()
                crit = (c.get("Criticality") or c.get("criticality") or "").strip()
                mand = (c.get("MandatoryOptional") or c.get("mandatory") or "").strip()
                manauto = (c.get("ManualAutomatic") or c.get("manual_automatic") or "").strip()
                debug_print(f"[AMENDMENT][COMPLIANCE]      C{c_idx}: {title} | type={ctype} | criticality={crit} | {mand}/{manauto}")
        except Exception as e:
            debug_print(f"[AMENDMENT][COMPLIANCE]   ⚠️ Could not print generated compliances: {e}")
        
        return processed_compliances
        
    except Exception as e:
        debug_print(f"Error generating compliance for subpolicy {subpolicy_id}: {e}")
        import traceback
        traceback.print_exc()
        return []


def generate_compliance_and_risk(
    excel_file_path, 
    output_prefix="compliance_risk_output", 
    output_dir="excel_output_nist",
    api_key=None,
    save_to_file=True
):
    """
    Main function to generate compliance and risk records from Excel file.
    Can be called from other scripts.
    
    Args:
        excel_file_path (str): Path to the input Excel file
        output_prefix (str): Prefix for output files (default: "compliance_risk_output")
        output_dir (str): Directory to save output files (default: "excel_output_nist")
        api_key (str): OpenAI API key (optional, will use environment variable if not provided)
        save_to_file (bool): Whether to save results to Excel files (default: True)
    
    Returns:
        tuple: (compliance_results, risk_results, compliance_file_path, risk_file_path)
               If save_to_file=False, file paths will be None
    """
    # Load data
    df = load_excel_data(excel_file_path)
    if df is None:
        return None, None, None, None
   
    # Setup LangChain
    debug_print("Setting up AI model...")
    chain = setup_llm_chain(api_key)
   
    # Process data
    debug_print("Processing data and generating records...")
    compliance_results, risk_results = process_excel_data(df, chain)
   
    compliance_file = None
    risk_file = None
    
    if compliance_results is not None or risk_results is not None:
        if save_to_file:
            # Save results to separate files
            compliance_file, risk_file = save_results(
                compliance_results, 
                risk_results, 
                output_prefix,
                output_dir
            )
            debug_print("\n✓ Generation complete!")
        else:
            debug_print("\n✓ Data processing complete! (Results not saved to file)")
    else:
        debug_print("\nNo results generated. Please check the input file format.")
    
    return compliance_results, risk_results, compliance_file, risk_file


def main():
    """CLI entry point for standalone usage"""
    debug_print("Compliance and Risk Records Generator")
    debug_print("--------------------------------------")
   
    # Get Excel file path
    excel_file = input("Enter the path to your Excel file: ")
   
    # Call the main function
    compliance_results, risk_results, compliance_file, risk_file = generate_compliance_and_risk(
        excel_file_path=excel_file,
        output_prefix="compliance_risk_output",
        output_dir="excel_output_nist"
    )
    
    if compliance_results or risk_results:
        debug_print("\n✓ Process completed successfully!")
    else:
        debug_print("\n✗ Process failed. Please check the input file.")


if __name__ == "__main__":
    main()
 
 