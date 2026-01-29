/**
 * Script to update specific requests in Postman collection
 * Run with: node update_postman_collection.js
 */

const fs = require('fs');
const path = require('path');

// Configuration
const COLLECTION_FILE = 'GRC_TPRM_Complete_Postman_Collection 2.json';
const BACKUP_FILE = 'GRC_TPRM_Complete_Postman_Collection 2.backup.json';

function updateCollection() {
    try {
        // Read the updated collection
        const collectionPath = path.join(__dirname, COLLECTION_FILE);
        const collection = JSON.parse(fs.readFileSync(collectionPath, 'utf8'));
        
        // Find specific requests to update
        const requestsToUpdate = [
            'Create Framework Version',
            'Export Framework Policies',
            'Export All Frameworks',
            'Activate/Deactivate Framework Version',
            'Get Rejected Framework Versions',
            'Resubmit Rejected Framework',
            'Resubmit Framework Approval',
            'Set Selected Framework'
        ];
        
        // Function to find and update a request
        function updateRequest(items, requestName, updates) {
            for (let item of items) {
                if (item.name === requestName) {
                    // Update the request
                    if (updates.method) item.request.method = updates.method;
                    if (updates.url) item.request.url = updates.url;
                    if (updates.body) item.request.body = updates.body;
                    return true;
                }
                if (item.item && updateRequest(item.item, requestName, updates)) {
                    return true;
                }
            }
            return false;
        }
        
        // Update specific requests
        const updates = {
            'Create Framework Version': {
                method: 'POST',
                body: {
                    mode: 'raw',
                    raw: JSON.stringify({
                        FrameworkName: 'Updated Framework Name',
                        CreatedByName: 'Your Name',
                        version_type: 'minor'
                    }, null, 2),
                    options: { raw: { language: 'json' } }
                }
            }
            // Add more updates as needed
        };
        
        // Apply updates
        if (collection.item) {
            for (const [requestName, update] of Object.entries(updates)) {
                updateRequest(collection.item, requestName, update);
            }
        }
        
        // Save updated collection
        fs.writeFileSync(collectionPath, JSON.stringify(collection, null, 2));
        console.log('✅ Collection updated successfully!');
        
    } catch (error) {
        console.error('❌ Error updating collection:', error);
    }
}

updateCollection();
