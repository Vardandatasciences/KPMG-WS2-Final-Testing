# Step 7: Similarity Integration Guide

Add "Suggest" button to any creation form to check for similar records before creating.

## Quick Integration

### 1. Framework Creation Form

```vue
<template>
  <form @submit.prevent="createFramework">
    <!-- Form fields -->
    <input v-model="form.FrameworkName" placeholder="Framework Name" />
    <textarea v-model="form.FrameworkDescription" placeholder="Description" />
    
    <!-- Buttons -->
    <div class="form-actions">
      <button type="submit" class="btn-primary">Create</button>
      
      <!-- ADD THIS: Suggest Button -->
      <SimilaritySuggestButton
        item-type="Framework"
        :item-data="form"
        :tenant-id="currentTenantId"
        @similarity-checked="onSimilarityChecked"
        @create-anyway="createFramework"
        @use-existing="navigateToExisting"
      />
    </div>
  </form>
</template>

<script setup>
import { ref } from 'vue';
import SimilaritySuggestButton from '@/components/SimilaritySuggestButton.vue';

const form = ref({
  FrameworkName: '',
  FrameworkDescription: '',
  Category: '',
  Type: ''
});

const currentTenantId = ref(1);

const onSimilarityChecked = (results) => {
  console.log('Similarity results:', results);
  // Optionally show custom UI
};

const navigateToExisting = (candidate) => {
  // Navigate to the existing record
  router.push(`/framework/${candidate.id}`);
};

const createFramework = async () => {
  // Your existing create logic
  await api.createFramework(form.value);
};
</script>
```

### 2. Policy Creation Form

```vue
<template>
  <form @submit.prevent="createPolicy">
    <input v-model="form.PolicyName" />
    <textarea v-model="form.PolicyDescription" />
    
    <div class="form-actions">
      <button type="submit">Create</button>
      
      <!-- ADD THIS -->
      <SimilaritySuggestButton
        item-type="Policy"
        :item-data="form"
        :tenant-id="tenantId"
        :parent-framework-id="selectedFrameworkId"
        @create-anyway="createPolicy"
        @use-existing="useExistingPolicy"
      />
    </div>
  </form>
</template>
```

### 3. SubPolicy Creation Form

```vue
<SimilaritySuggestButton
  item-type="SubPolicy"
  :item-data="form"
  :tenant-id="tenantId"
  :parent-framework-id="frameworkId"
  :parent-policy-id="policyId"
  @create-anyway="createSubPolicy"
  @use-existing="useExisting"
/>
```

### 4. Compliance Creation Form

```vue
<SimilaritySuggestButton
  item-type="Compliance"
  :item-data="form"
  :tenant-id="tenantId"
  :parent-framework-id="frameworkId"
  :parent-policy-id="policyId"
  :parent-subpolicy-id="subpolicyId"
  @create-anyway="createCompliance"
  @use-existing="useExisting"
/>
```

## Component Props

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `itemType` | String | ✅ | 'Framework', 'Policy', 'SubPolicy', 'Compliance' |
| `itemData` | Object | ✅ | Form data object |
| `tenantId` | Number | ✅ | Current tenant ID |
| `parentFrameworkId` | Number | - | For Policy/SubPolicy/Compliance |
| `parentPolicyId` | Number | - | For SubPolicy/Compliance |
| `parentSubpolicyId` | Number | - | For Compliance |
| `disabled` | Boolean | - | Disable button |
| `hint` | String | - | Tooltip text |

## Events

| Event | Payload | Description |
|-------|---------|-------------|
| `similarity-checked` | `{check_id, candidates, risk_level}` | Check completed |
| `create-anyway` | - | User chose to create despite similarity |
| `use-existing` | `{id, name, view_url}` | User selected existing record |

## Modal Display

The modal automatically shows when:
- Similar records found (candidates > 0)
- Risk level is MEDIUM or HIGH

Modal shows:
- Risk badge (color-coded)
- List of similar records with scores
- ChromaDB score (vector similarity)
- Reranker score (deep comparison)
- LLM reasoning
- Action buttons

## Backend Flow (Steps 1-6)

When user clicks "Suggest":

```
1. POST /api/similarity/check/
   → Runs Steps 1-6
   
2. Step 1: Text Cleaning
   → Form data → Structured JSON
   
3. Step 2: Domain Classification
   → AI categorizes (Food/Banking/IT)
   
4. Step 3: Embedding (BGE-M3)
   → Creates 1024-dim vector
   
5. Step 4: Vector Search (ChromaDB)
   → Finds top 20 similar
   
6. Step 5: Reranker (BGE-Reranker)
   → Re-ranks top 5 accurately
   
7. Step 6: LLM Decision
   → Analyzes and classifies
   
8. Response with results
   → Show modal with findings
```

## User Decisions (Step 8)

When user clicks in modal:
- **Create Anyway** → `POST /api/similarity/check/{id}/decision/` with `CREATE_ANYWAY`
- **Use Selected** → Same endpoint with `USE_EXISTING` + candidate ID
- **Cancel** → Same endpoint with `CANCEL`

## Styling

The components use scoped CSS. Override by:

```css
/* Global override */
.suggest-btn {
  background: your-color !important;
}

/* Modal customization */
.similarity-modal {
  max-width: 800px;
}
```

## Testing

Test with backend running:
```bash
# Backend
python manage.py runserver

# Frontend
npm run dev

# Test similarity
curl -X POST http://localhost:8000/api/similarity/check/ \
  -H "Authorization: Bearer TOKEN" \
  -d '{"item_type":"Framework","item_data":{...}}'
```
