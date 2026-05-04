/**
 * Maps Pinia / dashboard framework rows into Framework Explorer list/card shape
 * for instant paint + background sync with FRAMEWORK_EXPLORER API.
 */
export function mapPiniaFrameworksToExplorerRows(raw) {
  const list = Array.isArray(raw) ? raw : []
  return list.map((fw) => {
    const statusRaw = fw.ActiveInactive ?? fw.status ?? fw.Status ?? ''
    const status =
      String(statusRaw).toLowerCase() === 'active' ? 'Active' : String(statusRaw || 'Inactive')
    return {
      id: fw.FrameworkId ?? fw.id,
      name: fw.FrameworkName ?? fw.name ?? '',
      category: fw.Category ?? fw.category ?? '',
      description: fw.FrameworkDescription ?? fw.description ?? '',
      status,
      internalExternal: fw.InternalExternal ?? fw.internalExternal ?? 'Internal',
      versions: Array.isArray(fw.versions) ? fw.versions : [],
    }
  })
}

/** Minimal hierarchy row for All Policies until POLICY_ALL_POLICIES_FRAMEWORKS returns */
export function mapPiniaFrameworksForAllPoliciesList(raw) {
  const base = mapPiniaFrameworksToExplorerRows(raw)
  return base.map((fw) => ({
    ...fw,
    FrameworkId: fw.id,
    FrameworkName: fw.name,
    versions: Array.isArray(fw.versions) ? fw.versions : [],
  }))
}

export function summarizeExplorerFromFrameworkRows(frameworks) {
  let active = 0
  let inactive = 0
  for (const fw of frameworks) {
    if (String(fw.status).toLowerCase() === 'active') active++
    else inactive++
  }
  if (inactive === 0 && frameworks.length && active < frameworks.length) {
    inactive = frameworks.length - active
  }
  return {
    active_frameworks: active,
    inactive_frameworks: inactive,
    active_policies: 0,
    inactive_policies: 0,
  }
}
