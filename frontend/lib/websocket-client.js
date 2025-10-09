/**
 * Multimodal Agent WebSocket Client
 * Handles real-time communication with the backend
 */

export class MultimodalAgentClient {
    constructor(wsUrl = 'ws://localhost:8000/ws') {
        this.wsUrl = wsUrl;
        this.ws = null;
        this.sessionId = null;
        this.chatId = null; // Current chat ID
        this.isAuthenticated = false;
        this.isConnecting = false;
        this.messageHandlers = new Map();
        // Log handlers removed; logs not used
        this.eventHandlers = new Map();
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.heartbeatInterval = null;
        this._tokenSent = false; // guard to avoid duplicate token sends
        this.nanoMessageHandlers = new Map(); // For handling nano messages
        this._nextSignature = null; // optional agent signature for next outbound message
    }

    connect(token) {
        if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
            return Promise.resolve();
        }

        this.isConnecting = true;
        
        return new Promise((resolve, reject) => {
            try {
                console.log('Connecting to WebSocket with token:', token ? `${token.substring(0, 20)}...` : 'NO TOKEN');
                this.ws = new WebSocket(this.wsUrl);
                
                this.ws.onopen = () => {
                    console.log('WebSocket onopen', new Date().toISOString());
                    this.isConnecting = false;
                    this.reconnectAttempts = 0;
                
                    // send token only once
                    if (token) {
                        if (!this._tokenSent) {
                            console.log('Sending auth token (one-time)');
                            this.ws.send(JSON.stringify({ token }));
                            this._tokenSent = true;
                        } else {
                            console.warn('Token already sent, skipping duplicate send');
                        }
                    } else {
                        console.error('No token provided for WebSocket authentication');
                        this.ws.close(1000, 'No authentication token');
                        reject(new Error('No authentication token provided'));
                        return;
                    }
                
                    resolve();
                };
                

                this.ws.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        this.handleMessage(data);
                    } catch (error) {
                        console.error('Failed to parse WebSocket message:', error, 'raw=', event.data);
                    }
                };
                

                this.ws.onclose = (event) => {
                    console.log('WebSocket disconnected:', event.code, event.reason);
                    this._tokenSent = false; // allow re-send on reconnect
                    this.isAuthenticated = false;
                    this.sessionId = null;
                    this.isConnecting = false;
                    this.stopHeartbeat();
                    
                    // Attempt reconnection if not a clean close
                    if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
                        this.scheduleReconnect(token);
                    }
                    
                    this.emit('disconnected', { code: event.code, reason: event.reason });
                };

                this.ws.onerror = (error) => {
                    console.error('WebSocket error:', error);
                    this.isConnecting = false;
                    this.emit('error', error);
                    reject(error);
                };

            } catch (error) {
                this.isConnecting = false;
                reject(error);
            }
        });
    }

    scheduleReconnect(token) {
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
        
        console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        
        setTimeout(() => {
            this.connect(token);
        }, delay);
    }

    startHeartbeat() {
        // clear any existing to be safe
        this.stopHeartbeat();
    
        this.heartbeatInterval = setInterval(() => {
            if (!this.isAuthenticated || !this.ws || this.ws.readyState !== WebSocket.OPEN) {
                // don't send if not authenticated or socket closed
                return;
            }
    
            // send explicit application-level ping; include session_id for traceability (optional)
            const payload = { type: 'ping' };
            if (this.sessionId) payload.session_id = this.sessionId;
    
            try {
                this.ws.send(JSON.stringify(payload));
            } catch (err) {
                console.warn('Failed to send heartbeat:', err);
            }
        }, 30000); // 30s
    }
    

    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }

    handleMessage(data) {
        const eventType = data.type || data.event;
        
        // Filter out empty messages from backend
        if (data.text && data.text.trim() === '') {
            console.warn('Received empty message from backend, ignoring');
            return;
        }
        
        switch (eventType) {
            case 'auth_success':
                this.handleAuthSuccess(data);
                break;
            case 'auth_error':
                this.handleAuthError(data);
                break;
            case 'auth_required':
                this.handleAuthRequired(data);
                break;
            case 'session_started':
                this.handleSessionStarted(data);
                break;
            case 'chat_created':
                this.handleChatCreated(data);
                break;
            case 'chat_switched':
                this.handleChatSwitched(data);
                break;
            case 'title_updated':
                this.handleTitleUpdated(data);
                break;
            case 'nano_message':
                this.handleNanoMessage(data);
                break;
            case 'agent_direct_message':
                this.handleAgentDirectMessage(data);
                break;
            case 'agent_notification':
                this.handleAgentNotification(data);
                break;
            // 'log' event disabled; no persistence/UI for logs
            case 'message':
                this.handleMessageEvent(data);
                break;
            case 'pong':
                // Heartbeat response
                break;
            default:
                // Handle regular chat messages
                if (data.text !== undefined && data.text.trim() !== '') {
                    this.handleChatMessage(data);
                } else {
                    console.warn('Received message without valid text content:', data);
                }
        }
    }

    handleAuthSuccess(data) {
        this.isAuthenticated = true;
        this.sessionId = data.session_id;
        this.chatId = data.chat_id; // Set current chat ID
        console.log('Authenticated:', data.user);
        console.log('Session ID:', this.sessionId);
        console.log('Chat ID:', this.chatId);
        
        // start heartbeat only after successful authentication
        this.startHeartbeat();
    
        this.emit('auth_success', data);
    }
    

    handleAuthError(data) {
        this.isAuthenticated = false;
        this.sessionId = null;
        console.error('Authentication error:', data.message);
        console.error('Full error data:', data);
        
        this.emit('auth_error', data);
    }

    handleAuthRequired(data) {
        this.isAuthenticated = false;
        this.sessionId = null;
        console.log('Authentication required');
        
        this.emit('auth_required', data);
    }

    handleSessionStarted(data) {
        console.log('Session started:', data.session_id);
        this.sessionId = data.session_id;
        this.chatId = data.chat_id; // Set chat ID from session start
        
        this.emit('session_started', data);
    }

    handleChatCreated(data) {
        this.chatId = data.chat_id;
        console.log('Chat created:', this.chatId);
        
        this.emit('chat_created', data);
    }

    handleChatSwitched(data) {
        this.chatId = data.chat_id;
        console.log('Chat switched to:', this.chatId);
        
        this.emit('chat_switched', data);
    }

    handleTitleUpdated(data) {
        console.log('Title updated for chat:', data.chat_id, 'New title:', data.title);
        
        this.emit('title_updated', data);
    }

    handleNanoMessage(data) {
        console.log(`[${data.agent}] ${data.message}`);
        
        // Call registered nano message handlers
        const handlers = this.nanoMessageHandlers.get(data.agent) || [];
        handlers.forEach(handler => handler(data));
        
        // Call general nano message handlers
        const generalHandlers = this.nanoMessageHandlers.get('*') || [];
        generalHandlers.forEach(handler => handler(data));
        
        this.emit('nano_message', data);
    }

    handleAgentDirectMessage(data) {
        console.log(`[${data.agent_name}] Direct message: ${data.message}`);
        this.emit('agent_direct_message', data);
    }


    handleAgentNotification(data) {
        console.log(`[${data.agent_name}] Notification (${data.notification_type}): ${data.message}`);
        this.emit('agent_notification', data);
    }

    // handleLog removed

    handleMessageEvent(data) {
        this.emit('message', data);
    }

    handleChatMessage(data) {
        this.emit('chat_message', data);
    }

    // Public API methods
    sendMessage(message, image = null, chatId = null, metadata = null) {
        if (!this.isAuthenticated || !this.ws || this.ws.readyState !== WebSocket.OPEN) {
            throw new Error('Not connected or authenticated');
        }
        
        // Prevent sending empty messages
        if (!message || message.trim().length === 0) {
            console.warn('Attempted to send empty message, ignoring');
            return;
        }
        
        const payload = { 
            text: message.trim(),
            chat_id: chatId || this.chatId // Include chat_id
        };
        if (this._nextSignature) {
            payload.signature = this._nextSignature;
            console.log(`[WebSocket] Adding signature to payload: ${this._nextSignature}`);
        }
        if (image) {
            payload.image = image;
        }
        if (metadata && typeof metadata === 'object') {
            payload.metadata = metadata;
        }
        
        console.log('Sending message:', { text: message.trim(), hasImage: !!image, hasMetadata: !!metadata, chatId: payload.chat_id, signature: payload.signature });
        this.ws.send(JSON.stringify(payload));
        // Clear signature after sending one message
        this._nextSignature = null;
    }

    // Chat management methods
    createNewChat(title = "New chat") {
        if (!this.isAuthenticated || !this.ws || this.ws.readyState !== WebSocket.OPEN) {
            throw new Error('Not connected or authenticated');
        }

        const payload = { 
            chat_id: null, // Signal to create new chat
            title: title
        };

        console.log('Creating new chat:', title);
        this.ws.send(JSON.stringify(payload));
    }

    switchToChat(chatId) {
        if (!this.isAuthenticated || !this.ws || this.ws.readyState !== WebSocket.OPEN) {
            throw new Error('Not connected or authenticated');
        }

        if (chatId === this.chatId) {
            console.log('Already in chat:', chatId);
            return;
        }

        const payload = { chat_id: chatId };

        console.log('Switching to chat:', chatId);
        this.ws.send(JSON.stringify(payload));
    }

    getCurrentChatId() {
        return this.chatId;
    }

    sendImage(imageData) {
        if (!this.isAuthenticated || !this.ws || this.ws.readyState !== WebSocket.OPEN) {
            throw new Error('Not connected or authenticated');
        }

        this.ws.send(JSON.stringify({ image: imageData }));
    }

    // Event handling
    on(event, handler) {
        if (!this.eventHandlers.has(event)) {
            this.eventHandlers.set(event, []);
        }
        this.eventHandlers.get(event).push(handler);
    }

    off(event, handler) {
        if (this.eventHandlers.has(event)) {
            const handlers = this.eventHandlers.get(event);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }

    emit(event, data) {
        if (this.eventHandlers.has(event)) {
            this.eventHandlers.get(event).forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`Error in event handler for ${event}:`, error);
                }
            });
        }
    }

    // Log handling removed

    // Nano message handling
    onNanoMessage(agent, handler) {
        if (!this.nanoMessageHandlers.has(agent)) {
            this.nanoMessageHandlers.set(agent, []);
        }
        this.nanoMessageHandlers.get(agent).push(handler);
    }

    offNanoMessage(agent, handler) {
        if (this.nanoMessageHandlers.has(agent)) {
            const handlers = this.nanoMessageHandlers.get(agent);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }

    // Note: Follow-up responses are now sent as normal messages
    // The sendMessage method handles all user responses including follow-ups

    // Utility methods
    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }

    getConnectionState() {
        if (!this.ws) return 'CLOSED';
        
        switch (this.ws.readyState) {
            case WebSocket.CONNECTING:
                return 'CONNECTING';
            case WebSocket.OPEN:
                return 'OPEN';
            case WebSocket.CLOSING:
                return 'CLOSING';
            case WebSocket.CLOSED:
                return 'CLOSED';
            default:
                return 'UNKNOWN';
        }
    }

    disconnect() {
        this.stopHeartbeat();
        
        if (this.ws) {
            this.ws.close(1000, 'Client disconnect');
            this.ws = null;
        }
        
        this.isAuthenticated = false;
        this.sessionId = null;
        this.chatId = null;
        this.reconnectAttempts = 0;
    }

    // Session management
    async getSessionHistory(token) {
        try {
            const response = await fetch(`/api/sessions/history?token=${token}`);
            if (!response.ok) throw new Error('Failed to fetch session history');
            return await response.json();
        } catch (error) {
            console.error('Failed to fetch session history:', error);
            throw error;
        }
    }

    async getSessionMessages(sessionId, token) {
        try {
            const response = await fetch(`/api/sessions/${sessionId}/messages?token=${token}`);
            if (!response.ok) throw new Error('Failed to fetch session messages');
            return await response.json();
        } catch (error) {
            console.error('Failed to fetch session messages:', error);
            throw error;
        }
    }

    // getSessionLogs removed: logs are not persisted
}