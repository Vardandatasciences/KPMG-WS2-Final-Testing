#!/usr/bin/env python3
"""
Script to update only specific requests in Postman collection
Usage: python update_specific_requests.py
"""

import json
import sys
from datetime import datetime

COLLECTION_FILE = "GRC_TPRM_Complete_Postman_Collection 2.json"
BACKUP_FILE = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

def find_and_update_request(items, request_name, updates):
    """Recursively find and update a request in the collection"""
    for item in items:
        if item.get("name") == request_name:
            print(f"✅ Found: {request_name}")
            
            # Update request method
            if "method" in updates:
                item["request"]["method"] = updates["method"]
                print(f"   Updated method to: {updates['method']}")
            
            # Update URL
            if "url" in updates:
                if isinstance(updates["url"], str):
                    item["request"]["url"]["raw"] = updates["url"]
                    # Parse path from URL
                    path_parts = updates["url"].replace("{{base_url}}/api/", "").split("/")
                    item["request"]["url"]["path"] = ["api"] + [p for p in path_parts if p and not p.startswith("{{")]
                else:
                    item["request"]["url"] = updates["url"]
                print(f"   Updated URL")
            
            # Update body
            if "body" in updates:
                item["request"]["body"] = updates["body"]
                print(f"   Updated body")
            
            return True
        
        # Recursively search in sub-items
        if "item" in item:
            if find_and_update_request(item["item"], request_name, updates):
                return True
    
    return False

def update_collection():
    """Main function to update the collection"""
    try:
        # Read collection
        print(f"📖 Reading collection: {COLLECTION_FILE}")
        with open(COLLECTION_FILE, 'r', encoding='utf-8') as f:
            collection = json.load(f)
        
        # Create backup
        print(f"💾 Creating backup: {BACKUP_FILE}")
        with open(BACKUP_FILE, 'w', encoding='utf-8') as f:
            json.dump(collection, f, indent=2, ensure_ascii=False)
        
        # Define updates for specific requests
        updates_map = {
            "Create Framework Version": {
                "method": "POST",
                "url": "{{base_url}}/api/frameworks/{{framework_id}}/create-version",
                "body": {
                    "mode": "raw",
                    "raw": json.dumps({
                        "FrameworkName": "Updated Framework Name",
                        "CreatedByName": "Your Name",
                        "version_type": "minor"
                    }, indent=2),
                    "options": {
                        "raw": {
                            "language": "json"
                        }
                    }
                }
            },
            "Export Framework Policies": {
                "method": "POST",
                "url": "{{base_url}}/api/frameworks/{{framework_id}}/export",
                "body": {
                    "mode": "raw",
                    "raw": json.dumps({"format": "xlsx"}, indent=2),
                    "options": {
                        "raw": {
                            "language": "json"
                        }
                    }
                }
            },
            "Export All Frameworks": {
                "method": "POST",
                "url": "{{base_url}}/api/frameworks/export-all",
                "body": {
                    "mode": "raw",
                    "raw": json.dumps({"format": "xlsx"}, indent=2),
                    "options": {
                        "raw": {
                            "language": "json"
                        }
                    }
                }
            },
            "Activate/Deactivate Framework Version": {
                "method": "PUT",
                "url": "{{base_url}}/api/frameworks/{{framework_id}}/toggle-active"
            },
            "Resubmit Framework Approval": {
                "method": "PUT",
                "url": "{{base_url}}/api/frameworks/{{framework_id}}/resubmit-approval"
            }
        }
        
        # Apply updates
        print("\n🔄 Applying updates...")
        if "item" in collection:
            for request_name, updates in updates_map.items():
                if find_and_update_request(collection["item"], request_name, updates):
                    print(f"   ✅ Updated: {request_name}\n")
                else:
                    print(f"   ⚠️  Not found: {request_name}\n")
        
        # Save updated collection
        print(f"💾 Saving updated collection...")
        with open(COLLECTION_FILE, 'w', encoding='utf-8') as f:
            json.dump(collection, f, indent=2, ensure_ascii=False)
        
        print("✅ Collection updated successfully!")
        print(f"📦 Backup saved as: {BACKUP_FILE}")
        print("\n💡 Next steps:")
        print("   1. In Postman: Right-click collection → Import → File")
        print("   2. Select: 'GRC_TPRM_Complete_Postman_Collection 2.json'")
        print("   3. Choose 'Merge' option (not Replace)")
        print("   4. Only changed requests will be updated!")
        
    except FileNotFoundError:
        print(f"❌ Error: {COLLECTION_FILE} not found!")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    update_collection()
