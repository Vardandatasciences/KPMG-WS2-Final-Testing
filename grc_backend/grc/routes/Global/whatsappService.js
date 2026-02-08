import { getWhatsAppConfig } from './sysParamsService.js';

const API_VERSION = 'v20.0';
const BASE_URL = `https://graph.facebook.com/${API_VERSION}`;

/**
 * Send a text message via WhatsApp Cloud API
 */
export async function sendTextMessage(to, message) {
  const config = await getWhatsAppConfig();
  const url = `${BASE_URL}/${config.phoneNumberId}/messages`;
  
  // Validate access token
  if (!config.accessToken || config.accessToken.length < 50) {
    throw new Error('Invalid access token: Token is missing or too short. Please check sys_params table.');
  }

  // Debug: Log token info (first/last 10 chars only for security)
  const tokenPreview = config.accessToken.length > 20 
    ? `${config.accessToken.substring(0, 10)}...${config.accessToken.substring(config.accessToken.length - 10)}`
    : 'TOO_SHORT';
  console.log(`🔑 Using Access Token: ${tokenPreview} (length: ${config.accessToken.length})`);
  console.log(`📱 Phone Number ID: ${config.phoneNumberId}`);

  const payload = {
    messaging_product: 'whatsapp',
    recipient_type: 'individual',
    to: to,
    type: 'text',
    text: {
      body: message,
    },
  };

  console.log(`📤 Sending message to ${to} via Phone Number ID: ${config.phoneNumberId}`);

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${config.accessToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorText = await response.text();
    let errorMessage = `WhatsApp API error: ${errorText}`;
    
    try {
      const errorJson = JSON.parse(errorText);
      if (errorJson.error) {
        errorMessage = `WhatsApp API error (${errorJson.error.code}): ${errorJson.error.message}`;
        console.error('❌ Full error response:', JSON.stringify(errorJson, null, 2));
        
        // Specific handling for token errors
        if (errorJson.error.code === 190) {
          console.error('🔴 Access Token Error Details:');
          console.error('   - Error Code: 190 (OAuthException)');
          console.error('   - This usually means:');
          console.error('     1. Token is expired or invalid');
          console.error('     2. Token is corrupted (truncated or has extra characters)');
          console.error('     3. Token is for wrong app/environment');
          console.error('   - Solution: Generate a new permanent token from Meta Developer Console');
          console.error(`   - Current token length: ${config.accessToken.length} characters`);
          console.error(`   - Current token preview: ${tokenPreview}`);
        }
      }
    } catch (e) {
      // Not JSON, use text as is
      console.error('❌ Error response (non-JSON):', errorText);
    }
    
    throw new Error(errorMessage);
  }

  const data = await response.json();
  console.log('✅ Message sent successfully:', data.messages?.[0]?.id);
  return data;
}

/**
 * Send an image via WhatsApp Cloud API
 */
export async function sendImageMessage(to, imageUrl, caption = '') {
  const config = await getWhatsAppConfig();
  const url = `${BASE_URL}/${config.phoneNumberId}/messages`;
  
  const payload = {
    messaging_product: 'whatsapp',
    recipient_type: 'individual',
    to: to,
    type: 'image',
    image: {
      link: imageUrl,
      caption: caption,
    },
  };

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${config.accessToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`WhatsApp API error: ${error}`);
  }

  const data = await response.json();
  return data;
}

/**
 * Send a document via WhatsApp Cloud API
 */
export async function sendDocumentMessage(to, documentUrl, caption = '', fileName = '') {
  const config = await getWhatsAppConfig();
  const url = `${BASE_URL}/${config.phoneNumberId}/messages`;
  
  const payload = {
    messaging_product: 'whatsapp',
    recipient_type: 'individual',
    to: to,
    type: 'document',
    document: {
      link: documentUrl,
      caption: caption,
      filename: fileName,
    },
  };

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${config.accessToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`WhatsApp API error: ${error}`);
  }

  const data = await response.json();
  return data;
}

/**
 * Send a video via WhatsApp Cloud API
 */
export async function sendVideoMessage(to, videoUrl, caption = '') {
  const config = await getWhatsAppConfig();
  const url = `${BASE_URL}/${config.phoneNumberId}/messages`;
  
  const payload = {
    messaging_product: 'whatsapp',
    recipient_type: 'individual',
    to: to,
    type: 'video',
    video: {
      link: videoUrl,
      caption: caption,
    },
  };

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${config.accessToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`WhatsApp API error: ${error}`);
  }

  const data = await response.json();
  return data;
}

/**
 * Send an audio via WhatsApp Cloud API
 */
export async function sendAudioMessage(to, audioUrl) {
  const config = await getWhatsAppConfig();
  const url = `${BASE_URL}/${config.phoneNumberId}/messages`;
  
  const payload = {
    messaging_product: 'whatsapp',
    recipient_type: 'individual',
    to: to,
    type: 'audio',
    audio: {
      link: audioUrl,
    },
  };

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${config.accessToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`WhatsApp API error: ${error}`);
  }

  const data = await response.json();
  return data;
}

/**
 * Download media from WhatsApp Cloud API
 */
export async function downloadMedia(mediaId) {
  const config = await getWhatsAppConfig();
  const url = `${BASE_URL}/${mediaId}`;
  
  const response = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${config.accessToken}`,
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to get media info: ${response.statusText}`);
  }

  const data = await response.json();
  
  // Download the actual media file
  const mediaFileResponse = await fetch(data.url, {
    headers: {
      'Authorization': `Bearer ${config.accessToken}`,
    },
  });

  if (!mediaFileResponse.ok) {
    throw new Error(`Failed to download media file: ${mediaFileResponse.statusText}`);
  }

  return {
    url: data.url,
    mimeType: data.mime_type,
    sha256: data.sha256,
    fileSize: data.file_size,
    buffer: await mediaFileResponse.arrayBuffer(),
  };
}

/**
 * Send a template message via WhatsApp Cloud API
 * Supports authentication templates and other template types
 */
export async function sendTemplateMessage(to, templateName, languageCode = 'en', components = []) {
  const config = await getWhatsAppConfig();
  const url = `${BASE_URL}/${config.phoneNumberId}/messages`;

  // WhatsApp template parameter restrictions:
  // - text params cannot contain newline/tab characters
  // - text params cannot contain more than 4 consecutive spaces
  const sanitizeTemplateParamText = (value) => {
    if (value == null) return value;
    const s = String(value);
    // Replace newlines/tabs with single spaces, then collapse whitespace runs.
    // Keep up to 4 consecutive spaces (WhatsApp limit).
    return s
      .replace(/[\r\n\t]+/g, ' ')
      .replace(/ {5,}/g, '    ')
      .replace(/\s{2,}/g, (m) => (m.startsWith(' ') ? m.slice(0, Math.min(4, m.length)) : ' '))
      .trim();
  };

  const sanitizeComponents = (comps) => {
    if (!Array.isArray(comps)) return comps;
    return comps.map((c) => {
      if (!c || typeof c !== 'object') return c;
      const next = { ...c };
      if (Array.isArray(next.parameters)) {
        next.parameters = next.parameters.map((p) => {
          if (!p || typeof p !== 'object') return p;
          if (p.type === 'text' && typeof p.text !== 'undefined') {
            return { ...p, text: sanitizeTemplateParamText(p.text) };
          }
          return p;
        });
      }
      return next;
    });
  };
  
  // Validate access token
  if (!config.accessToken || config.accessToken.length < 50) {
    throw new Error('Invalid access token: Token is missing or too short. Please check sys_params table.');
  }

  // Debug: Log token info (first/last 10 chars only for security)
  const tokenPreview = config.accessToken.length > 20 
    ? `${config.accessToken.substring(0, 10)}...${config.accessToken.substring(config.accessToken.length - 10)}`
    : 'TOO_SHORT';
  console.log(`🔑 Using Access Token: ${tokenPreview} (length: ${config.accessToken.length})`);
  console.log(`📱 Phone Number ID: ${config.phoneNumberId}`);

  // Build template payload according to WhatsApp Cloud API format
  const payload = {
    messaging_product: 'whatsapp',
    recipient_type: 'individual',
    to: to,
    type: 'template',
    template: {
      name: templateName,
      language: {
        code: languageCode
      }
    }
  };

  // Add components if provided (for authentication templates with OTP codes)
  if (components && components.length > 0) {
    payload.template.components = sanitizeComponents(components);
  }

  console.log(`📤 Sending template "${templateName}" to ${to} via Phone Number ID: ${config.phoneNumberId}`);
  console.log(`📋 Template payload:`, JSON.stringify(payload, null, 2));

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${config.accessToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorText = await response.text();
    let errorMessage = `WhatsApp API error: ${errorText}`;
    
    try {
      const errorJson = JSON.parse(errorText);
      if (errorJson.error) {
        errorMessage = `WhatsApp API error (${errorJson.error.code}): ${errorJson.error.message}`;
        console.error('❌ Full error response:', JSON.stringify(errorJson, null, 2));
        
        // Specific handling for token errors
        if (errorJson.error.code === 190) {
          console.error('🔴 Access Token Error Details:');
          console.error('   - Error Code: 190 (OAuthException)');
          console.error('   - This usually means:');
          console.error('     1. Token is expired or invalid');
          console.error('     2. Token is corrupted (truncated or has extra characters)');
          console.error('     3. Token is for wrong app/environment');
          console.error('   - Solution: Generate a new permanent token from Meta Developer Console');
          console.error(`   - Current token length: ${config.accessToken.length} characters`);
          console.error(`   - Current token preview: ${tokenPreview}`);
        }
        
        // Specific handling for missing button parameters
        if (errorJson.error.code === 131008) {
          console.error('🔴 Button Parameter Error Details:');
          console.error('   - Error Code: 131008 (Required parameter is missing)');
          console.error('   - This means your template has a button (likely URL button) that requires a parameter');
          console.error('   - Solution options:');
          console.error('     1. Update your template in Meta Business Manager to use "Copy code" button instead of URL button');
          console.error('     2. Or provide button components in the template request with WHATSAPP_OTP_BUTTON_URL env var');
          console.error('   - For authentication templates, "Copy code" buttons are automatic and don\'t need parameters');
        }
        
        // Specific handling for parameter length limit
        if (errorJson.error.code === 100 && errorJson.error.error_data?.details?.includes('parameter length limit')) {
          console.error('🔴 Parameter Length Error Details:');
          console.error('   - Error Code: 100 (Invalid parameter)');
          console.error('   - This means a button URL parameter exceeds the 15-character limit');
          console.error('   - WhatsApp has a strict 15-character limit for URL button parameters');
          console.error('   - Solution options:');
          console.error('     1. Set WHATSAPP_OTP_BUTTON_URL to a URL with 15 characters or less');
          console.error('     2. Use a short URL service (bit.ly, tinyurl, etc.)');
          console.error('     3. Use just the domain name (e.g., "prosync.app" instead of "https://prosync.app")');
          console.error('     4. Update your template to use "Copy code" button instead (recommended)');
        }
        
        // Specific handling for button parameter containing URL error
        if (errorJson.error.code === 100 && errorJson.error.error_data?.details?.includes('contains url')) {
          console.error('🔴 Button Parameter URL Error Details:');
          console.error('   - Error Code: 100 (Invalid parameter)');
          console.error('   - This means your template button parameter structure is incorrect');
          console.error('   - Your template likely uses a "copy_code" button, not a URL button');
          console.error('   - Solution: Set WHATSAPP_OTP_INCLUDE_BUTTON=false (or don\'t set it)');
          console.error('   - "Copy code" buttons are automatic and don\'t need button components');
          console.error('   - Only set WHATSAPP_OTP_INCLUDE_BUTTON=true if your template has a URL button');
        }
      }
    } catch (e) {
      // Not JSON, use text as is
      console.error('❌ Error response (non-JSON):', errorText);
    }
    
    throw new Error(errorMessage);
  }

  const data = await response.json();
  console.log('✅ Template sent successfully:', data.messages?.[0]?.id);
  return data;
}

/**
 * Parse WhatsApp webhook payload
 */
export function parseWebhookPayload(body) {
  const events = [];
  
  try {
    if (!body.entry || !Array.isArray(body.entry)) {
      return events;
    }

    for (const entry of body.entry) {
      if (!entry.changes || !Array.isArray(entry.changes)) {
        continue;
      }

      for (const change of entry.changes) {
        const value = change.value;

        // Handle messages
        if (value.messages && Array.isArray(value.messages)) {
          for (const message of value.messages) {
            const event = {
              type: 'message',
              wmid: message.id,
              phoneNumber: message.from,
              timestamp: message.timestamp,
              messageType: message.type,
              message: null,
              mediaId: null,
            };

            // Extract text message
            if (message.type === 'text' && message.text) {
              event.message = message.text.body;
            }
            // Extract image
            else if (message.type === 'image' && message.image) {
              event.mediaId = message.image.id;
              event.mediaType = 'image';
              event.mimeType = message.image.mime_type;
              event.message = message.image.caption || '[Image]';
            }
            // Extract video
            else if (message.type === 'video' && message.video) {
              event.mediaId = message.video.id;
              event.mediaType = 'video';
              event.mimeType = message.video.mime_type;
              event.message = message.video.caption || '[Video]';
            }
            // Extract audio
            else if (message.type === 'audio' && message.audio) {
              event.mediaId = message.audio.id;
              event.mediaType = 'audio';
              event.mimeType = message.audio.mime_type;
              event.message = '[Audio]';
            }
            // Extract document
            else if (message.type === 'document' && message.document) {
              event.mediaId = message.document.id;
              event.mediaType = 'document';
              event.mimeType = message.document.mime_type;
              event.fileName = message.document.filename;
              event.message = message.document.caption || message.document.filename || '[Document]';
            }

            // Get profile name if available
            if (value.profiles && value.profiles[message.from]) {
              event.name = value.profiles[message.from].name;
            }

            events.push(event);
          }
        }

        // Handle status updates
        if (value.statuses && Array.isArray(value.statuses)) {
          for (const status of value.statuses) {
            const statusEvent = {
              type: 'status',
              wmid: status.id,
              phoneNumber: status.recipient_id,
              status: status.status,
              timestamp: status.timestamp,
            };
            
            // Include error information if status is failed
            if (status.status === 'failed' && status.errors) {
              statusEvent.error = status.errors[0] || status.errors; // Get first error or all errors
            }
            
            events.push(statusEvent);
          }
        }
      }
    }
  } catch (error) {
    console.error('Error parsing webhook payload:', error);
  }

  return events;
}

