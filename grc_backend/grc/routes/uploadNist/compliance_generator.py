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

# Phase 1, 2, 3 Optimizations - Import shared AI utilities
from ...routes.Risk.risk_ai_doc import (
    AI_PROVIDER,
    call_ollama_json,
    call_openai_json,
    _select_ollama_model_by_complexity,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL_DEFAULT,
    OLLAMA_MODEL_FAST,
    OLLAMA_MODEL_COMPLEX,
    OPENAI_API_KEY,
    OPENAI_API_URL,
    OPENAI_MODEL,
)

# Phase 2 Optimizations
from ...utils.document_preprocessor import calculate_document_hash
from ...utils.few_shot_prompts import (
    get_field_extraction_prompt,
    get_compliance_generation_prompt
)

# Phase 3 Optimizations
from ...utils.rag_system import (
    add_document_to_rag,
    retrieve_relevant_context,
    build_rag_prompt,
    is_rag_available,
    get_rag_stats
)
from ...utils.model_router import (
    route_model,
    track_system_load,
    get_current_system_load
)
from ...utils.request_queue import (
    process_with_queue,
    get_queue_status
)

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
        print(f"Error loading Excel file: {e}")
        return None
 
def _generate_compliance_with_ai(subpolicy_name, description, control, current_date, document_hash=None):
    """
    Generate compliance records using optimized AI (Phase 1, 2, 3).
    Replaces LangChain with direct AI calls for better performance.
    """
    # Phase 3: Try to retrieve relevant context from RAG
    rag_context = None
    if is_rag_available():
        try:
            query = f"Compliance requirements for subpolicy: {subpolicy_name}. Control: {control}"
            retrieved = retrieve_relevant_context(query, n_results=3)
            if retrieved:
                rag_context = retrieved
                print(f"   📚 Phase 3 RAG: Retrieved {len(retrieved)} relevant chunks for compliance generation")
        except Exception as e:
            print(f"   ⚠️  RAG retrieval failed: {e}")
    
    # Phase 2: Build prompt with few-shot examples
    base_prompt = get_compliance_generation_prompt(
        subpolicy_name=subpolicy_name,
        description=description,
        control=control,
        current_date=current_date
    )
    
    # Remove the old prompt building code - now using few-shot template
    # The get_compliance_generation_prompt already includes the full prompt with examples
    
    # Phase 3: Enhance prompt with RAG context if available
    if rag_context:
        prompt = build_rag_prompt(
            user_query=base_prompt,
            retrieved_context=rag_context,
            base_prompt=None
        )
    else:
        prompt = base_prompt
    
    # Phase 3: Use intelligent model routing
    selected_model = route_model(
        task_type="compliance_generation",
        text_length=len(prompt),
        accuracy_required="high",
        system_load=get_current_system_load(),
        provider=AI_PROVIDER,
    )
    print(f"   🧠 Phase 3 Model Routing: Selected model '{selected_model}' for compliance generation")
    
    # Call AI with selected model and caching (Phase 1 & 2)
    start_time = time.time()
    if AI_PROVIDER == 'ollama':
        result = call_ollama_json(prompt, model=selected_model, document_hash=document_hash)
    else:
        result = call_openai_json(prompt, document_hash=document_hash)
    
    processing_time = time.time() - start_time
    track_system_load(processing_time, len(prompt))
    
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
            
            # Calculate document hash for caching
            document_text = f"{subpolicy_name}\n{description}\n{control}"
            document_hash = calculate_document_hash(document_text)
            
            # Use optimized AI generation
            result = _generate_compliance_with_ai(
                subpolicy_name, description, control, current_date, document_hash
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
    Phase 1, 2, 3 optimized - uses direct AI calls instead of LangChain.
    """
    compliance_results = []
    risk_results = []
   
    # Check if required columns exist
    required_columns = ["SubPolicyId", "SubPolicyName", "Description", "Control"]
    missing_columns = [col for col in required_columns if col not in df.columns]
   
    if missing_columns:
        print(f"Error: Missing required columns: {', '.join(missing_columns)}")
        print(f"Available columns: {', '.join(df.columns)}")
        return None, None
   
    total_rows = len(df)
    current_date = datetime.now().strftime("%Y-%m-%d")
    compliance_id_counter = 1  # Track compliance IDs for risk linking
    risk_id_counter = 1  # Track risk IDs
    
    # Phase 2: Calculate hash for entire dataset for caching
    dataset_text = "\n".join([
        f"{row['SubPolicyName']}\n{row['Description']}\n{row['Control']}"
        for _, row in df.iterrows()
    ])
    dataset_hash = calculate_document_hash(dataset_text)
   
    for index, row in df.iterrows():
        print(f"Processing row {index+1}/{total_rows}...")
       
        try:
            # Extract data from row
            SubPolicyId = int(row["SubPolicyId"])  # Use existing SubPolicyId from Excel
            SubPolicyName = row["SubPolicyName"]
            Description = row["Description"]
            Control = row["Control"]
           
            # Phase 1, 2, 3: Generate compliance records using optimized AI
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
                # Use optimized direct AI call
                document_text = f"{SubPolicyName}\n{Description}\n{Control}"
                document_hash = calculate_document_hash(document_text)
                compliance_data = _generate_compliance_with_ai(
                    SubPolicyName, Description, Control, current_date, document_hash
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
                   
                print(f"Generated {len(compliances)} compliance and risk records for: {SubPolicyName}")
               
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON response for row {index+1}: {e}")
                print(f"Raw response: {result.content}")
               
        except Exception as e:
            print(f"Error processing row {index+1}: {e}")
   
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
        print(f"\nCompliance results saved to {compliance_file}")
        print(f"Total compliance records generated: {len(compliance_results)}")
    else:
        print("\nNo compliance records to save.")
   
    # Save risk results
    if risk_results:
        risk_file = os.path.join(output_dir, f"{output_prefix}_Risk.xlsx")
        df_risk = pd.DataFrame(risk_results)
        df_risk.to_excel(risk_file, index=False)
        print(f"Risk results saved to {risk_file}")
        print(f"Total risk records generated: {len(risk_results)}")
    else:
        print("No risk records to save.")
    
    return compliance_file, risk_file
 
def generate_compliance_for_single_subpolicy(
    subpolicy_id,
    subpolicy_name,
    description,
    control,
    api_key=None
):
    """
    Generate compliance and risk records for a single subpolicy (Phase 1, 2, 3 optimized).
    
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
        
        # Phase 2: Calculate document hash for caching
        document_text = f"{subpolicy_name}\n{description}\n{control}"
        document_hash = calculate_document_hash(document_text)
        
        # Phase 3: Use queuing for large documents
        def _do_generation():
            # Generate compliance records using optimized AI (Phase 1, 2, 3)
            result = _generate_compliance_with_ai(
                subpolicy_name, description, control, current_date, document_hash
            )
            
            # Handle both dict and string responses
            if isinstance(result, str):
                compliance_data = json.loads(result)
            else:
                compliance_data = result
            
            compliances = compliance_data.get("compliances", [])
            
            # Process each compliance and add subpolicy reference
            processed_compliances = []
            for compliance in compliances:
                # Extract risk data if present
                risk_data = compliance.pop("risk", None)
                
                # Add subpolicy reference
                compliance["SubPolicyId"] = subpolicy_id
                compliance["SubPolicyName"] = subpolicy_name
                
                # Include risk data in compliance record
                if risk_data:
                    compliance["risk_details"] = risk_data
                
                processed_compliances.append(compliance)
            
            # Phase 3: Store generated compliance in RAG
            if is_rag_available() and processed_compliances:
                try:
                    compliance_text = json.dumps(processed_compliances, indent=2)
                    add_document_to_rag(
                        document_text=compliance_text,
                        document_id=f"compliance_{subpolicy_id}_{document_hash[:16]}",
                        metadata={
                            "type": "compliance_generation",
                            "subpolicy_id": subpolicy_id,
                            "subpolicy_name": subpolicy_name,
                            "generated_at": current_date,
                            "num_compliances": len(processed_compliances)
                        }
                    )
                    print(f"   ✅ Phase 3 RAG: Stored compliance generation in knowledge base")
                except Exception as e:
                    print(f"   ⚠️  Phase 3 RAG: Failed to store compliance: {e}")
            
            return processed_compliances
        
        # Use queuing for large inputs
        if len(document_text) > 5000:
            request_id = f"compliance_gen_{subpolicy_id}_{hash(document_text)}"
            return process_with_queue(request_id, _do_generation)
        else:
            return _do_generation()
        
    except Exception as e:
        print(f"Error generating compliance for subpolicy {subpolicy_id}: {e}")
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
    print("Setting up AI model...")
    chain = setup_llm_chain(api_key)
   
    # Process data
    print("Processing data and generating records...")
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
            print("\n✓ Generation complete!")
        else:
            print("\n✓ Data processing complete! (Results not saved to file)")
    else:
        print("\nNo results generated. Please check the input file format.")
    
    return compliance_results, risk_results, compliance_file, risk_file


def main():
    """CLI entry point for standalone usage"""
    print("Compliance and Risk Records Generator")
    print("--------------------------------------")
   
    # Get Excel file path
    excel_file = input("Enter the path to your Excel file: ")
   
    # Call the main function
    compliance_results, risk_results, compliance_file, risk_file = generate_compliance_and_risk(
        excel_file_path=excel_file,
        output_prefix="compliance_risk_output",
        output_dir="excel_output_nist"
    )
    
    if compliance_results or risk_results:
        print("\n✓ Process completed successfully!")
    else:
        print("\n✗ Process failed. Please check the input file.")


if __name__ == "__main__":
    main()
 
 