/**
 * Helpers for automatic similarity checks on Submit / Save.
 */
function parseOptionalInt(value) {
  if (value == null || value === '') return null;
  const n = parseInt(value, 10);
  return Number.isNaN(n) ? null : n;
}

/**
 * Build API payload for /similarity/check/
 * @param {Object} opts
 */
export function buildSimilarityCheckPayload(opts) {
  const tenantId = opts.tenant_id ?? opts.tenantId
    ?? parseInt(localStorage.getItem('tenant_id'), 10)
    ?? parseInt(localStorage.getItem('tenantId'), 10)
    ?? null;

  const params = {
    item_type: opts.item_type || opts.itemType,
    item_data: opts.item_data || opts.itemData || {},
    tenant_id: tenantId
  };

  const fw = parseOptionalInt(opts.parent_framework_id ?? opts.parentFrameworkId);
  const pol = parseOptionalInt(opts.parent_policy_id ?? opts.parentPolicyId);
  const sub = parseOptionalInt(opts.parent_subpolicy_id ?? opts.parentSubpolicyId);
  const exclude = parseOptionalInt(opts.exclude_entity_id ?? opts.excludeEntityId);

  if (fw != null) params.parent_framework_id = fw;
  if (pol != null) params.parent_policy_id = pol;
  if (sub != null) params.parent_subpolicy_id = sub;
  if (exclude != null) params.exclude_entity_id = exclude;
  if (opts.framework_context) params.framework_context = opts.framework_context;
  if (opts.policy_context) params.policy_context = opts.policy_context;

  return params;
}

/**
 * @param {import('vue').Ref|Object} gateRef - SimilaritySubmitGate ref
 * @param {Object} [overrides] - optional check params (item_type, item_data, parent ids, exclude)
 * @returns {Promise<{action: string, candidate?: object}>}
 */
export async function runSimilarityBeforeSubmit(gateRef, overrides = null) {
  const gate = gateRef?.value ?? gateRef;
  if (!gate?.runCheck) {
    console.warn('[similarity] Submit gate not ready');
    return overrides ? { action: 'cancel' } : { action: 'proceed' };
  }
  return gate.runCheck(overrides);
}

/**
 * Run multiple checks in sequence (framework → policies → subpolicies).
 * @param {Array<{gate: object, params: object, skip?: () => boolean}>} checks
 */
export async function runSimilarityCheckSequence(checks, { PopupService } = {}) {
  const queue = (checks || []).filter((c) => c?.params);
  const total = queue.length;

  for (let i = 0; i < queue.length; i += 1) {
    const check = queue[i];
    if (check.skip?.()) continue;
    if (!check.params?.item_type && !check.params?.itemType) continue;
    const name = check.params.item_data?.name || check.params.itemData?.name;
    if (!name || !String(name).trim()) continue;

    const itemType = check.params.item_type || check.params.itemType;
    const gate = check.gate?.value ?? check.gate;
    if (gate?.setProgressLabel) {
      gate.setProgressLabel(
        `Checking ${itemType} (${i + 1} of ${total}): ${String(name).trim().slice(0, 60)}…`
      );
    }

    const result = await runSimilarityBeforeSubmit(check.gate, {
      ...check.params,
      alwaysShowReview: check.alwaysShowReview === true
    });

    if (!handleSimilarityGateResult(result, { PopupService })) {
      if (gate?.clearProgressLabel) gate.clearProgressLabel();
      return false;
    }
  }

  const gate = queue[0]?.gate?.value ?? queue[0]?.gate;
  if (gate?.clearProgressLabel) gate.clearProgressLabel();
  return true;
}

/**
 * Build check list from Create Policy form state.
 */
export function buildNewFrameworkSimilarityParams(frameworkFormData) {
  if (!frameworkFormData?.FrameworkName?.trim()) return null;
  return {
    item_type: 'Framework',
    item_data: {
      name: frameworkFormData.FrameworkName,
      description: frameworkFormData.FrameworkDescription || frameworkFormData.FrameworkName,
      category: frameworkFormData.Category || '',
      identifier: frameworkFormData.Identifier || '',
      type: frameworkFormData.InternalExternal || ''
    }
  };
}

export function buildCreatePolicySimilarityChecks({
  gate,
  isNewFramework,
  frameworkFormData,
  policiesForm,
  frameworkId,
  skipFrameworkCheck = false
}) {
  const checks = [];
  const fwId = isNewFramework ? null : frameworkId;
  const inMemoryFrameworkContext =
    isNewFramework && frameworkFormData?.FrameworkName
      ? {
          domain: frameworkFormData.Category || 'Unknown',
          industry_vertical: null,
          name: frameworkFormData.FrameworkName
        }
      : null;

  if (isNewFramework && !skipFrameworkCheck) {
    const fwParams = buildNewFrameworkSimilarityParams(frameworkFormData);
    if (fwParams) {
      checks.push({ gate, params: fwParams });
    }
  }

  for (const pol of policiesForm || []) {
    if (!pol?.PolicyName?.trim()) continue;

    const policyParams = {
      item_type: 'Policy',
      item_data: {
        name: pol.PolicyName,
        description: pol.PolicyDescription || pol.description || '',
        policy_type: pol.PolicyType || pol.internalExternal || '',
        category: pol.PolicyCategory || pol.category || '',
        identifier: pol.Identifier || ''
      }
    };
    if (fwId != null) {
      policyParams.parent_framework_id = fwId;
    }
    if (inMemoryFrameworkContext) {
      policyParams.framework_context = inMemoryFrameworkContext;
    }
    checks.push({ gate, params: policyParams });

    const policyContext = {
      business_function: pol.PolicyCategory || pol.category || '',
      compliance_area: pol.PolicySubCategory || pol.subCategory || '',
      name: pol.PolicyName
    };

    const subpolicies = pol.subpolicies || pol.subPolicies || [];
    for (const sp of subpolicies) {
      const subName = (sp?.SubPolicyName || sp?.name || '').trim();
      if (!subName) continue;
      const subParams = {
        item_type: 'SubPolicy',
        item_data: {
          name: subName,
          description: sp.Description || sp.description || '',
          control: sp.Control || sp.control || '',
          identifier: sp.Identifier || sp.identifier || ''
        },
        policy_context: policyContext
      };
      if (fwId != null) {
        subParams.parent_framework_id = fwId;
      }
      const existingPolicyId = pol.PolicyId || pol.policyId || pol.originalPolicyId;
      if (existingPolicyId != null && existingPolicyId !== '') {
        const pid = parseInt(existingPolicyId, 10);
        if (!Number.isNaN(pid)) {
          subParams.parent_policy_id = pid;
        }
      }
      if (inMemoryFrameworkContext) {
        subParams.framework_context = inMemoryFrameworkContext;
      }
      // Always show review step so subpolicy is not silently skipped after policy modal
      checks.push({ gate, params: subParams, alwaysShowReview: true });
    }
  }

  return checks;
}

/**
 * Build checks from Upload Framework edited sections.
 */
export function buildUploadFrameworkSimilarityChecks({ gate, frameworkForm, sections }) {
  const checks = [];

  if (frameworkForm?.FrameworkName?.trim()) {
    checks.push({
      gate,
      params: {
        item_type: 'Framework',
        item_data: {
          name: frameworkForm.FrameworkName,
          description: frameworkForm.FrameworkDescription || '',
          category: frameworkForm.Category || '',
          identifier: frameworkForm.Identifier || ''
        }
      }
    });
  }

  for (const section of sections || []) {
    for (const policy of section.policies || []) {
      if (policy.exclude) continue;
      const polName = policy.policy_title || policy.policy_name || policy.PolicyName || policy.name;
      if (!polName?.trim()) continue;

      checks.push({
        gate,
        params: {
          item_type: 'Policy',
          item_data: {
            name: polName,
            description: policy.policy_description || policy.description || '',
            identifier: policy.policy_id || policy.identifier || ''
          }
        }
      });

      for (const sp of policy.subpolicies || []) {
        if (sp.exclude) continue;
        const spName = sp.subpolicy_title || sp.subpolicy_name || sp.SubPolicyName || sp.name;
        if (!spName?.trim()) continue;
        checks.push({
          gate,
          params: {
            item_type: 'SubPolicy',
            item_data: {
              name: spName,
              description: sp.subpolicy_description || sp.description || sp.Description || '',
              control: sp.control || sp.Control || '',
              identifier: sp.subpolicy_id || sp.identifier || ''
            }
          }
        });
      }
    }
  }

  return checks;
}

const _norm = (v) => String(v ?? '').trim();

function _frameworkFieldsChanged(form, previous) {
  if (!previous) return true;
  return (
    _norm(form?.name) !== _norm(previous.FrameworkName)
    || _norm(form?.description) !== _norm(previous.FrameworkDescription)
    || _norm(form?.category) !== _norm(previous.Category)
    || _norm(form?.identifier) !== _norm(previous.Identifier)
    || _norm(form?.internalExternal) !== _norm(previous.InternalExternal)
    || _norm(form?.startDate) !== _norm(previous.StartDate)
    || _norm(form?.endDate) !== _norm(previous.EndDate)
  );
}

function _policyFieldsChanged(policy, baseline) {
  if (!baseline) return true;
  return (
    _norm(policy?.name) !== _norm(baseline.name)
    || _norm(policy?.description) !== _norm(baseline.description)
    || _norm(policy?.identifier) !== _norm(baseline.identifier)
    || _norm(policy?.department) !== _norm(baseline.department)
    || _norm(policy?.scope) !== _norm(baseline.scope)
    || _norm(policy?.objective) !== _norm(baseline.objective)
    || _norm(policy?.type) !== _norm(baseline.type)
    || _norm(policy?.category) !== _norm(baseline.category)
    || _norm(policy?.subCategory) !== _norm(baseline.subCategory)
  );
}

function _subPolicyFieldsChanged(sp, baseline) {
  if (!baseline) return true;
  return (
    _norm(sp?.name) !== _norm(baseline.name)
    || _norm(sp?.description) !== _norm(baseline.description)
    || _norm(sp?.control) !== _norm(baseline.control)
    || _norm(sp?.identifier) !== _norm(baseline.identifier)
  );
}

/**
 * VV versioning: only check entities the user actually changed (vs loaded baseline).
 */
export function buildVersioningSimilarityChecks({
  gate,
  frameworkForm,
  previousFramework,
  policyTabs,
  frameworkId,
  excludeFrameworkId,
  policyOnly = false,
}) {
  const checks = [];
  const fwId = frameworkId;

  if (!policyOnly && frameworkForm?.name?.trim() && _frameworkFieldsChanged(frameworkForm, previousFramework)) {
    checks.push({
      gate,
      params: {
        item_type: 'Framework',
        item_data: {
          name: frameworkForm.name,
          description: frameworkForm.description || '',
          category: frameworkForm.category || '',
          identifier: frameworkForm.identifier || '',
          type: frameworkForm.internalExternal || '',
        },
        exclude_entity_id: excludeFrameworkId,
      },
    });
  }

  const tabs = policyOnly && policyTabs?.length ? [policyTabs[0]] : (policyTabs || []);

  for (const policy of tabs) {
    if (policy.exclude) continue;
    const baseline = policy._similarityBaseline;
    const policyChanged = _policyFieldsChanged(policy, baseline);

    if (policy.name?.trim() && policyChanged) {
      checks.push({
        gate,
        params: {
          item_type: 'Policy',
          item_data: {
            name: policy.name,
            description: policy.description || '',
            identifier: policy.identifier || '',
            policy_type: policy.internalExternal || policy.policyType || '',
          },
          parent_framework_id: fwId,
          exclude_entity_id: policy.originalPolicyId || policy.policyId || policy.id,
        },
      });
    }

    for (const sp of policy.subPolicies || []) {
      if (sp.exclude) continue;
      const spBaseline = baseline?.subPolicies?.find(
        (b) => String(b.id) === String(sp.id)
      );
      if (!sp.name?.trim()) continue;
      if (!_subPolicyFieldsChanged(sp, spBaseline)) continue;

      const subParams = {
        item_type: 'SubPolicy',
        item_data: {
          name: sp.name,
          description: sp.description || '',
          control: sp.control || '',
          identifier: sp.identifier || '',
        },
        parent_framework_id: fwId,
        exclude_entity_id: sp.originalSubPolicyId || sp.subPolicyId || sp.id,
      };
      const existingPolicyId = policy.originalPolicyId || policy.policyId || policy.id;
      if (existingPolicyId != null && existingPolicyId !== '') {
        const pid = parseInt(existingPolicyId, 10);
        if (!Number.isNaN(pid)) {
          subParams.parent_policy_id = pid;
        }
      }
      checks.push({ gate, params: subParams, alwaysShowReview: true });
    }
  }

  return checks;
}

/**
 * TT / VV tailoring & versioning forms (framework + all policy tabs + subpolicies).
 */
export function buildTailoringSimilarityChecks({ gate, frameworkForm, policyTabs, frameworkId, excludeFrameworkId }) {
  const checks = [];

  if (frameworkForm?.name?.trim()) {
    checks.push({
      gate,
      params: {
        item_type: 'Framework',
        item_data: {
          name: frameworkForm.name,
          description: frameworkForm.description || '',
          category: frameworkForm.category || '',
          identifier: frameworkForm.identifier || '',
          type: frameworkForm.internalExternal || ''
        },
        exclude_entity_id: excludeFrameworkId
      }
    });
  }

  for (const policy of policyTabs || []) {
    if (policy.exclude) continue;
    if (policy.name?.trim()) {
      checks.push({
        gate,
        params: {
          item_type: 'Policy',
          item_data: {
            name: policy.name,
            description: policy.description || '',
            identifier: policy.identifier || '',
            policy_type: policy.internalExternal || policy.policyType || ''
          },
          parent_framework_id: frameworkId,
          exclude_entity_id: policy.originalPolicyId || policy.policyId
        }
      });
    }

    for (const sp of policy.subPolicies || []) {
      if (sp.exclude) continue;
      if (sp.name?.trim()) {
        checks.push({
          gate,
          params: {
            item_type: 'SubPolicy',
            item_data: {
              name: sp.name,
              description: sp.description || '',
              control: sp.control || '',
              identifier: sp.identifier || ''
            },
            parent_framework_id: frameworkId,
            exclude_entity_id: sp.originalSubPolicyId || sp.subPolicyId
          },
          alwaysShowReview: true,
        });
      }
    }
  }

  return checks;
}

export function complianceItemDataFromRecord(c) {
  return {
    name: c?.ComplianceTitle || c?.name || '',
    description: c?.ComplianceItemDescription || c?.description || '',
    compliance_type: c?.ComplianceType || c?.compliance_type || '',
    identifier: c?.Identifier || c?.identifier || '',
  };
}

function _complianceFieldsChanged(c, baseline) {
  if (!baseline) return true;
  const cur = complianceItemDataFromRecord(c);
  return (
    _norm(cur.name) !== _norm(baseline.name)
    || _norm(cur.description) !== _norm(baseline.description)
    || _norm(cur.compliance_type) !== _norm(baseline.compliance_type)
    || _norm(cur.identifier) !== _norm(baseline.identifier)
  );
}

/**
 * Create Compliance: one check per tab/item (blocking sequence, like Create Policy subpolicies).
 */
export function buildComplianceCreateSimilarityChecks({
  gate,
  complianceList,
  frameworkId,
  policyId,
  subPolicyId,
}) {
  const checks = [];
  const withTitle = (complianceList || []).filter((c) => c?.ComplianceTitle?.trim());
  const multi = withTitle.length > 1;

  for (const c of withTitle) {
    const params = {
      item_type: 'Compliance',
      item_data: complianceItemDataFromRecord(c),
    };
    const fw = parseOptionalInt(frameworkId);
    const pol = parseOptionalInt(policyId);
    const sub = parseOptionalInt(subPolicyId);
    if (fw != null) params.parent_framework_id = fw;
    if (pol != null) params.parent_policy_id = pol;
    if (sub != null) params.parent_subpolicy_id = sub;
    checks.push({ gate, params, alwaysShowReview: multi });
  }

  return checks;
}

/**
 * Edit / version Compliance: only when similarity-relevant fields changed vs loaded baseline.
 */
export function buildComplianceVersioningSimilarityChecks({
  gate,
  compliance,
  baseline,
  excludeEntityId,
  frameworkId,
  policyId,
  subPolicyId,
}) {
  if (!compliance?.ComplianceTitle?.trim()) return [];
  if (!_complianceFieldsChanged(compliance, baseline)) return [];

  const params = {
    item_type: 'Compliance',
    item_data: complianceItemDataFromRecord(compliance),
    exclude_entity_id: excludeEntityId,
  };
  const fw = parseOptionalInt(frameworkId);
  const pol = parseOptionalInt(policyId);
  const sub = parseOptionalInt(subPolicyId);
  if (fw != null) params.parent_framework_id = fw;
  if (pol != null) params.parent_policy_id = pol;
  if (sub != null) params.parent_subpolicy_id = sub;

  return [{ gate, params, alwaysShowReview: true }];
}

/**
 * Option A: queue background checks for update flows (no save until review page).
 */
export async function startAsyncUpdateFromChecks(checks, pendingSave, { PopupService } = {}) {
  const { startAsyncUpdateSimilarity } = await import('@/services/similarityAsyncUpdateService');
  const filtered = (checks || []).filter((c) => {
    const name = c.params?.item_data?.name || c.params?.itemData?.name;
    return name && String(name).trim();
  }).map((c) => c.params || c);

  if (!filtered.length) {
    return { started: false, masterCheckId: null };
  }

  const result = await startAsyncUpdateSimilarity({
    checks: filtered,
    pendingSave,
  });

  const count = filtered.length;
  const itemTypes = filtered.map((c) => c.item_type || c.itemType).filter(Boolean);
  const { getSimilarityStartMessage } = await import('@/utils/similarityNotificationText');
  const startCopy = getSimilarityStartMessage(pendingSave?.operation, itemTypes);
  const msg =
    count === 1
      ? (result.message || startCopy.message)
      : `${result.message || startCopy.message} (${count} items you changed.)`;

  if (PopupService?.info) {
    PopupService.info(msg, startCopy.heading);
  }
  return {
    started: true,
    masterCheckId: result.master_check_id,
    message: msg,
    checkCount: count,
  };
}

export function handleSimilarityGateResult(result) {
  if (!result || result.action === 'proceed') {
    return true;
  }
  if (result.action === 'cancel') {
    return false;
  }
  if (result.action === 'use_existing') {
    // User acknowledged a similar record but chose to continue submit (same as create anyway).
    // USE_EXISTING is already logged on the similarity audit via SimilaritySubmitGate.
    return true;
  }
  return false;
}
