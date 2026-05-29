/**
 * User-facing copy for similarity update flows (no technical jargon).
 */

const ENTITY = {
  Framework: {
    noun: 'framework',
    nounPlural: 'frameworks',
    reviewTitle: 'Similar frameworks ready to review',
    category: 'framework',
  },
  Policy: {
    noun: 'policy',
    nounPlural: 'policies',
    reviewTitle: 'Similar policies ready to review',
    category: 'policy',
  },
  SubPolicy: {
    noun: 'sub-policy',
    nounPlural: 'sub-policies',
    reviewTitle: 'Similar sub-policies ready to review',
    category: 'policy',
  },
  Compliance: {
    noun: 'compliance item',
    nounPlural: 'compliance items',
    reviewTitle: 'Similar compliance items ready to review',
    category: 'compliance',
  },
};

const OP_PHRASE = {
  framework_version: 'framework version',
  policy_version: 'policy version',
  compliance_update: 'compliance version',
  tt_create_framework: 'new tailored framework',
  tt_create_policy: 'new tailored policy',
};

export function resolveSimilarityEntity(operation, itemTypes = []) {
  const types = [...new Set((itemTypes || []).filter(Boolean))];
  if (operation === 'compliance_update') return 'Compliance';
  if (operation === 'framework_version' || operation === 'tt_create_framework') return 'Framework';
  if (operation === 'policy_version' || operation === 'tt_create_policy') {
    if (types.length === 1 && types[0] === 'SubPolicy') return 'SubPolicy';
    if (types.includes('SubPolicy') && !types.includes('Policy') && !types.includes('Framework')) {
      return 'SubPolicy';
    }
    return 'Policy';
  }
  if (types.length === 1) return types[0];
  if (types.includes('Compliance')) return 'Compliance';
  if (types.includes('SubPolicy')) return 'SubPolicy';
  if (types.includes('Policy')) return 'Policy';
  if (types.includes('Framework')) return 'Framework';
  return 'Policy';
}

export function getSimilarityStartMessage(operation, itemTypes = []) {
  const entity = resolveSimilarityEntity(operation, itemTypes);
  const meta = ENTITY[entity] || ENTITY.Policy;
  return {
    heading: `Checking similar ${meta.nounPlural}`,
    message:
      `We are comparing your ${meta.noun} changes with existing records. `
      + 'You will receive a notification when the review is ready. '
      + 'Nothing is saved until you open the review and confirm.',
  };
}

export function getSimilarityBannerMessage(entityKey, checkCount = 1) {
  const meta = ENTITY[entityKey] || ENTITY.Policy;
  const { heading } = getSimilarityStartMessage(
    entityKey === 'Compliance' ? 'compliance_update' : 'policy_version',
    [entityKey]
  );
  const countPart = checkCount > 1
    ? `${checkCount} ${meta.nounPlural} you changed are being reviewed. `
    : `Your ${meta.noun} changes are being reviewed. `;
  return (
    `${heading}. ${countPart}`
    + 'You will receive a notification when matches are ready. '
    + 'Nothing is saved until you review and confirm.'
  );
}

export function getSimilarityReadyPopup(entityKey) {
  const meta = ENTITY[entityKey] || ENTITY.Policy;
  return {
    heading: meta.reviewTitle,
    message: 'Open Notifications or click Open review, then confirm save to apply your changes.',
  };
}

export function getSimilarityReadyNotification(operation, itemTypes, label) {
  const entityKey = resolveSimilarityEntity(operation, itemTypes);
  const meta = ENTITY[entityKey] || ENTITY.Policy;
  const opPhrase = (operation && OP_PHRASE[operation]) ? OP_PHRASE[operation] : meta.noun;
  const namePart = label && String(label).trim() ? ` "${String(label).trim().slice(0, 120)}"` : '';
  return {
    title: meta.reviewTitle,
    message:
      `Possible matches are ready for your ${opPhrase}${namePart}. `
      + 'Open the review, then confirm save to apply your changes.',
    category: meta.category,
    entity_type: entityKey,
  };
}
