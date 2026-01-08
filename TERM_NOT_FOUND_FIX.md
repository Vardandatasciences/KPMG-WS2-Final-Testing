# Term Not Found Error - Fix Summary

## Problem
When trying to edit questionnaires for a contract term after loading questions from a template, users were getting an error:
```❌ Term not found for editing questionnaires: {termTitle: '', termId: null}
```

### Symptoms
- User clicks to view template questions
- Template questions load successfully ("✅ Loaded 1 questions from template 85")
- Modal shows "Unknown Term" as the term name
- When clicking "Edit Questionnaires" button, error occurs
- Navigation to QuestionnaireTemplates page fails

## Root Cause

### Issue 1: Term Lookup Failure
In `viewTemplateQuestions()` function (line 5659), the term lookup was failing:
```javascript
const term = contractTerms.value.find(t => String(t.term_id) === String(termId))
```

When the term was not found, the code defaulted to "Unknown Term" instead of showing an error:
```javascript
selectedTermTitle.value = term?.term_title || 'Unknown Term'  // ❌ Bad fallback
```

This caused a cascading failure when trying to edit questionnaires.

### Issue 2: Poor Error Handling
The error message didn't provide enough information to debug the issue:
- No logging of available terms
- No comparison of term IDs to understand mismatch
- Silent fallback to "Unknown Term" masked the real problem

### Issue 3: Potential Race Condition
The modal was being closed before the edit function completed, potentially clearing state variables.

## Fixes Applied

### 1. Enhanced Term Lookup with Validation
**File**: `grc_frontend/tprm_frontend/src/pages/contract/CreateContract.vue`

**In `viewTemplateQuestions()` function**:
- Added debug logging to show all available terms
- Return early with error popup if term is not found
- Use the actual found term values instead of fallback values

```javascript
// Try to find term with better logging
console.log('🔍 Looking for term:', termIdStr)
console.log('🔍 Available terms:', contractTerms.value.map(t => ({ id: t.term_id, title: t.term_title })))

const term = contractTerms.value.find(t => String(t.term_id) === String(termId))

if (!term) {
  console.error('❌ Term not found in contractTerms:', { 
    termId: termIdStr, 
    availableTerms: contractTerms.value.length,
    termIds: contractTerms.value.map(t => t.term_id)
  })
  PopupService.error(`Term not found. Please ensure the term exists before viewing questions.`, 'Error')
  return  // ✅ Exit early instead of using fallback
}

// Use actual term values
selectedTermTitle.value = term.term_title  // ✅ No fallback
selectedTermId.value = term.term_id        // ✅ Use actual term_id from found term
```

### 2. Improved Error Logging in editQuestionnaires()
**In `editQuestionnaires()` function**:
- Added debug logging to show input parameters
- Added logging of all available terms for comparison
- Better error message for users

```javascript
console.log('🔍 editQuestionnaires called with:', { termTitle, termId, questionsCount: existingQuestionnaires?.length })
console.log('🔍 Available contractTerms:', contractTerms.value.map(t => ({ id: t.term_id, title: t.term_title })))

if (!term) {
  console.error('❌ Term not found for editing questionnaires:', { 
    termTitle, 
    termId, 
    availableTerms: contractTerms.value.length,
    allTermIds: contractTerms.value.map(t => t.term_id),
    allTermTitles: contractTerms.value.map(t => t.term_title)
  })
  PopupService.error(`Term not found. The contract term may have been deleted or the page needs to be refreshed.`, 'Error')
  return
}
```

### 3. Added Click Event Logging
**In the Edit Questionnaires button**:
- Added logging to track button click events
- Shows exact values being passed to the function

```javascript
<Button @click="() => {
  console.log('🖱️ Edit button clicked with:', { title: selectedTermTitle, id: selectedTermId, questions: selectedQuestionnaires?.length })
  editQuestionnaires(selectedTermTitle, selectedTermId, selectedQuestionnaires)
}">
```

### 4. Prevented Race Condition
**In `editQuestionnaires()` function**:
- Removed premature modal closing
- Let the modal close after navigation is initiated

```javascript
// Close the modal AFTER navigation is initiated to prevent race conditions
// Don't close the modal yet - let it close after navigation
```

## Testing Instructions

### 1. Test With Valid Term
1. Open Create Contract page
2. Add a contract term with a title
3. Select a template for that term
4. Click the eye icon to view template questions
5. **Expected**: Modal opens showing term name (not "Unknown Term")
6. Click "Edit Questionnaires" button
7. **Expected**: Successfully navigates to QuestionnaireTemplates page with questions loaded

### 2. Test With Invalid Term
1. Open browser console to see logs
2. Manually try to view template questions for a non-existent term
3. **Expected**: Error popup shows "Term not found. Please ensure the term exists before viewing questions."
4. Console shows detailed debug info about available terms vs requested term

### 3. Check Console Logs
When testing, you should see these logs in console:

**When viewing template questions**:
```
🔍 Looking for term: term_1767849083981_0_m7um4svnk
🔍 Available terms: [{id: 'term_...', title: 'Payment'}, ...]
📋 Loading questions for template: {templateId: 85, termId: '...', termCategory: 'Payment', termTitle: 'Payment'}
✅ Loaded 1 questions from template 85
✅ Modal opened with term: {title: 'Payment', id: 'term_...'}
```

**When clicking Edit button**:
```
🖱️ Edit button clicked with: {title: 'Payment', id: 'term_...', questions: 1}
🔍 editQuestionnaires called with: {termTitle: 'Payment', termId: 'term_...', questionsCount: 1}
🔍 Available contractTerms: [{id: 'term_...', title: 'Payment'}, ...]
📋 Editing questionnaires for term: {term_id: '...', term_title: 'Payment', ...}
```

## Common Issues and Solutions

### Issue: "Term not found" error still occurs
**Possible Causes**:
1. The `contractTerms` array is empty - verify terms were added to the contract
2. The term_id format doesn't match - check console logs to compare IDs
3. Page needs refresh after adding terms

**Solution**:
- Check console logs to see available terms vs requested term
- Ensure terms are properly saved before viewing template questions
- Refresh the page if terms were recently added

### Issue: Modal shows "Unknown Term"
**This should no longer happen** with the fix. If it does:
1. Check browser console for error messages
2. Verify the term_id format in contractTerms array
3. Ensure contractTerms is properly restored from sessionStorage

### Issue: Nothing happens when clicking Edit button
**Possible Causes**:
- Browser console may show errors
- Term lookup is failing silently

**Solution**:
- Open browser console and look for error messages
- Check that selectedTermTitle and selectedTermId are set (use Vue DevTools)
- Verify the Edit button click event is logging the values

## Rollback Instructions
If this fix causes issues, revert these changes in `CreateContract.vue`:
1. `viewTemplateQuestions()` function (lines ~5656-5690)
2. `editQuestionnaires()` function (lines ~5805-5816)
3. Edit Questionnaires button click handler (lines ~2562-2569)

## Related Files
- `grc_frontend/tprm_frontend/src/pages/contract/CreateContract.vue` - Main fix location
- `grc_frontend/tprm_frontend/src/pages/QuestionnaireTemplates.vue` - Loads questions for editing
- `grc_frontend/tprm_frontend/src/services/api.js` - API calls for template questions

## Next Steps
If the term lookup continues to fail:
1. Check the term_id format being stored in the database vs what's in the frontend
2. Verify the contractTerms restoration logic from sessionStorage
3. Add more detailed logging in the term creation/saving process
4. Consider normalizing term_id format (remove prefixes, standardize case, etc.)

