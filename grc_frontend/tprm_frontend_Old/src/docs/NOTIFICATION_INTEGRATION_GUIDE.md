# Notification System Integration Guide

## Overview

The notification system has been enhanced to provide comprehensive success, error, warning, and info notifications across all SLA pages. This guide explains how to use the notification system in your components.

## Components

### 1. Enhanced Notification Service (`src/services/notificationService.js`)

The notification service now includes:

- **Generic notification methods:**
  - `createSuccessNotification(title, message, data)`
  - `createErrorNotification(title, message, data)`
  - `createWarningNotification(title, message, data)`
  - `createInfoNotification(title, message, data)`

- **SLA-specific notification methods:**
  - `createSLASuccessNotification(action, slaData)`
  - `createSLAErrorNotification(action, error, slaData)`
  - `createSLAWarningNotification(action, slaData)`

### 2. Notification Composable (`src/composables/useNotifications.js`)

A Vue composable that provides easy access to notification methods:

```javascript
import { useNotifications } from '@/composables/useNotifications'

const { 
  showSuccess, 
  showError, 
  showWarning, 
  showInfo,
  showSLASuccess,
  showSLAError,
  showSLAWarning 
} = useNotifications()
```

## Usage Examples

### Basic Notifications

```javascript
// Success notification
await showSuccess('Operation Successful', 'Your action completed successfully')

// Error notification
await showError('Operation Failed', 'Something went wrong')

// Warning notification
await showWarning('Attention Required', 'Please review this item')

// Info notification
await showInfo('Information', 'Here is some useful information')
```

### SLA-Specific Notifications

```javascript
// SLA success notifications
await showSLASuccess('created', {
  sla_id: 'sla-123',
  sla_name: 'My SLA'
})

await showSLASuccess('renewed', {
  sla_id: 'sla-123',
  sla_name: 'My SLA',
  new_expiry_date: '2024-12-31'
})

// SLA error notifications
await showSLAError('create_failed', 'Database connection error', {
  sla_id: 'sla-123',
  sla_name: 'My SLA'
})

// SLA warning notifications
await showSLAWarning('expiring_soon', {
  sla_id: 'sla-123',
  sla_name: 'My SLA',
  days_until_expiry: 5
})
```

## Integration in SLA Pages

### SLACreateEdit.vue

The SLA creation page now includes notifications for:

- **Draft saved successfully** - Info notification
- **SLA submitted for approval** - Success notification
- **Submission errors** - Error notification
- **Creation errors** - Error notification

### SLARenew.vue

The SLA renewal page includes notifications for:

- **SLA extended successfully** - Success notification
- **Extension errors** - Error notification
- **SLA terminated** - Warning notification
- **Termination errors** - Error notification

### SLAExpiring.vue

The expiring SLAs page includes notifications for:

- **Renewal process initiated** - Info notification
- **Notification cleared** - Info notification
- **Process errors** - Error notification

## Notification Types and Priorities

| Type | Priority | Use Case |
|------|----------|----------|
| Success | Low | Successful operations |
| Error | High | Failed operations, system errors |
| Warning | Medium | Attention required, expiring items |
| Info | Low | General information, process updates |

## Notification Metadata

All notifications include metadata for better tracking:

```javascript
{
  sla_id: 'string',
  sla_name: 'string',
  action: 'string',
  error_message: 'string', // for errors
  new_expiry_date: 'string', // for renewals
  days_until_expiry: 'number', // for warnings
  reason: 'string' // for terminations
}
```

## Testing

The notification system includes a test function in `Notifications.vue` that creates random notifications of different types to verify the system is working correctly.

## Best Practices

1. **Always use try-catch blocks** when calling notification methods
2. **Provide meaningful titles and messages** that help users understand what happened
3. **Include relevant metadata** for better tracking and debugging
4. **Use appropriate notification types** based on the situation
5. **Handle errors gracefully** and provide fallback notifications if needed

## Error Handling

```javascript
try {
  await showSLASuccess('created', slaData)
} catch (error) {
  console.error('Failed to create success notification:', error)
  // Fallback: show a basic error notification
  await showError('Notification Error', 'Could not create notification')
}
```

## Integration Checklist

- [ ] Import the `useNotifications` composable
- [ ] Initialize the composable in your component
- [ ] Add notifications to success operations
- [ ] Add notifications to error handling
- [ ] Add notifications to warning conditions
- [ ] Test all notification scenarios
- [ ] Verify notifications appear in the notification center

## Troubleshooting

### Common Issues

1. **Notifications not appearing**: Check that the notification service is properly imported and initialized
2. **Wrong notification type**: Verify you're using the correct method for the situation
3. **Missing metadata**: Ensure all required data is passed to the notification methods
4. **API errors**: Check that the backend notification API is working correctly

### Debug Tips

- Use browser console to check for notification creation errors
- Verify notification data in the notification center
- Check network requests to ensure API calls are successful
- Test with different notification types to ensure all work correctly
