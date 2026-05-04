/**
 * Normalize and filter framework rows to approved + active only.
 * Aligns with HomeView / homepage approved-frameworks behavior.
 */
export function normalizeApprovedActiveFrameworks(items) {
  if (!Array.isArray(items)) return []

  const normalized = items
    .map((framework) => {
      const frameworkId =
        framework.FrameworkId ?? framework.id ?? framework.frameworkId ?? framework.framework_id
      const frameworkName =
        framework.FrameworkName ?? framework.name ?? framework.frameworkName ?? framework.framework_name
      if (frameworkId === undefined || frameworkId === null || !frameworkName) return null

      return {
        ...framework,
        FrameworkId: frameworkId,
        FrameworkName: frameworkName,
      }
    })
    .filter(Boolean)
    .filter((framework) => {
      const statusValue = String(
        framework.Status ??
          framework.status ??
          framework.FrameworkStatus ??
          framework.frameworkStatus ??
          ''
      ).toLowerCase()
      const approvalValue = String(
        framework.ApprovalStatus ?? framework.approvalStatus ?? ''
      ).toLowerCase()

      const activeFlag = framework.IsActive ?? framework.isActive ?? framework.Active ?? framework.active
      const isActive =
        activeFlag === undefined || activeFlag === null
          ? !statusValue || statusValue.includes('active')
          : activeFlag === true ||
            activeFlag === 1 ||
            String(activeFlag).toLowerCase() === 'true'

      const isApproved = !approvalValue || approvalValue.includes('approved')
      return isActive && isApproved
    })

  return normalized.filter(
    (framework, index, arr) =>
      index === arr.findIndex((f) => String(f.FrameworkId) === String(framework.FrameworkId))
  )
}
