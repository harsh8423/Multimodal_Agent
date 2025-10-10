import asyncio
import base64
import os
from datetime import datetime
import json
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn

# Import social media manager and registry functions
from agents.social_media_manager import social_media_manager
from utils.agent_registry import init_updated_registry
from database import connect_to_mongo, close_mongo_connection
from routes.auth import router as auth_router
from routes.chats import router as chats_router
from services.auth import auth_service

# Import session management
from utils.session_memory import SESSION_MANAGER, create_session, remove_session
from utils.mongo_store import (create_chat, save_chat_message, append_chat_log, update_chat_title, get_store)
from utils.title_generator import generate_chat_title

# Legacy websocket communication utilities removed; SessionContext stores websocket reference

app = FastAPI()

# Allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://accounts.google.com",
        "https://www.googleapis.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# Include authentication routes
app.include_router(auth_router)

# Include chat management routes
app.include_router(chats_router)

# Include social media management routes
from routes import brands, templates, competitors, scraped_posts, scraping, todos
app.include_router(brands.router)
app.include_router(templates.router)
app.include_router(competitors.router)
app.include_router(scraped_posts.router)
app.include_router(scraping.router)
app.include_router(todos.router)

# Import asset agent for HTTP endpoint
from agents.asset_agent import asset_agent

@app.get("/")
async def root():
    return {
        "message": "Multimodal Agent API is running", 
        "status": "ok",
        "endpoints": {
            "auth": "/api/auth",
            "brands": "/api/brands",
            "templates": "/api/templates",
            "competitors": "/api/competitors",
            "scraped_posts": "/api/scraped-posts",
            "scraping": "/api/scraping",
            "todos": "/api/todos",
            "asset_manager_chat": "/api/asset-manager/chat"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Initialize the agent registry on startup
REGISTRY_PATH = Path(__file__).parent / "system_prompts.json"
init_updated_registry(str(REGISTRY_PATH))

# Database connection events
@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    """Get current user from WebSocket token"""
    user_id = auth_service.verify_token(credentials.credentials)
    if not user_id:
        return None
    return await auth_service.get_user_by_id(user_id)


async def generate_and_update_title(chat_id: str, user_message: str, websocket=None):
    """Generate and update chat title asynchronously"""
    try:
        print(f"[title-generation] Starting title generation for chat {chat_id} with message: '{user_message[:100]}...'")
        title = await generate_chat_title(user_message)
        print(f"[title-generation] Generated title: '{title}'")
        
        # Update the chat title in the database
        print(f"[title-generation] Updating database with title: '{title}'")
        success = await update_chat_title(chat_id, title)
        if success:
            print(f"[title-generation] Successfully updated chat title to: '{title}'")
            
            # Notify frontend about title update
            if websocket:
                try:
                    notification = {
                        "event": "title_updated",
                        "chat_id": chat_id,
                        "title": title
                    }
                    print(f"[title-generation] Sending notification to frontend: {notification}")
                    await websocket.send_text(json.dumps(notification))
                    print(f"[title-generation] Notification sent successfully")
                except Exception as e:
                    print(f"[title-generation] Failed to notify frontend: {e}")
            else:
                print(f"[title-generation] No websocket available for notification")
        else:
            print(f"[title-generation] Failed to update chat title in database")
            
    except Exception as e:
        print(f"[title-generation] Error generating/updating title: {e}")
        import traceback
        traceback.print_exc()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    async def send_json(payload):
        try:
            txt = json.dumps(payload)
        except Exception as e:
            # Only websocket-related prints are allowed – keep minimal
            txt = str(payload)
        # Only print websocket-related messages (no full payload)
        print(f"[ws-send] len={len(txt)} time={datetime.utcnow().isoformat()}")
        await websocket.send_text(txt)


    current_user = None
    session_context = None
    current_chat_id = None
    is_first_message = True  # Track if this is the first message in a new chat

    # diagnostic counters
    empty_frame_count = 0
    recv_count = 0

    
    try:
        while True:
            data = await websocket.receive_text()
            recv_count += 1
            # Log ALL received data to debug missing user responses
            print(f"[ws-recv #{recv_count}] RAW DATA: {data}")
            print(f"[ws-recv #{recv_count}] Length={len(data)} time={datetime.utcnow().isoformat()}")
            
            # Log current session if available
            if session_context:
                print(f"[ws-recv #{recv_count}] current_session: {session_context.session_id}")
            else:
                print(f"[ws-recv #{recv_count}] NO SESSION CONTEXT")

            # Ignore truly empty frames quickly
            if not data or data.strip() == "":
                empty_frame_count += 1
                print(f"[ws-recv] empty or whitespace frame received (count={empty_frame_count}), ignoring")
                continue

            # Expect JSON string
            try:
                message = json.loads(data)
                print(f"[ws-recv] PARSED MESSAGE: {message}")
                # Normalize message type for routing
                msg_type = None
                if isinstance(message, dict):
                    msg_type = message.get("type") or message.get("event")
                if msg_type == "user_response_to_agent":
                    print(f"[ws-recv] 🎯 USER RESPONSE MESSAGE DETECTED!")
            except json.JSONDecodeError as e:
                print(f"[ws-recv] JSON decode error: {e}, data: {data}")
                message = {"text": str(data)}

            # Ignore empty frames quickly
            if isinstance(data, str) and data.strip() == "":
                continue

            # If heartbeat ping, respond or ignore immediately
            if isinstance(message, dict) and message.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
                continue
            print(f"[main.py] message: {message}")

            # Note: Follow-up responses are handled as normal messages with optional agent signature


            # Handle authentication on first message
            if not current_user and isinstance(message, dict) and "token" in message:
                token = message.get("token")
                if token:
                    user_id = auth_service.verify_token(token)
                    if user_id:
                        current_user = await auth_service.get_user_by_id(user_id)
                        if current_user:
                            # Create session after successful authentication
                            session_context = await create_session(
                                user_id=current_user.id,
                                agent_names=["research_agent", "asset_agent", "social_media_manager", "media_analyst", "social_media_search_agent", "media_activist", "copy_writer"],
                                websocket=websocket,
                                chat_id=current_chat_id
                            ) 
                            
                            # Associate websocket with session (held inside SessionContext)
                            print(f"[main.py] WebSocket associated with session: {session_context.session_id}")
                            
                            # Hydrate memories if we have a chat_id
                            if current_chat_id:
                                await session_context.hydrate_memories_from_db(current_chat_id)
                            
                        
                            # Send authentication success
                            await send_json({
                                "type": "auth_success",
                                "session_id": session_context.session_id,
                                "chat_id": current_chat_id,
                                "user": {
                                    "id": current_user.id,
                                    "name": current_user.name,
                                    "email": current_user.email,
                                    "picture": current_user.picture
                                }
                            })
                            # IMPORTANT: handled the auth packet — don't treat it as a user message
                            continue

                        else:
                            await websocket.send_text(json.dumps({
                                "type": "auth_error",
                                "message": "User not found"
                            }))
                            continue
                    else:
                        await websocket.send_text(json.dumps({
                            "type": "auth_error",
                            "message": "Invalid token"
                        }))
                        continue
                else:
                    await websocket.send_text(json.dumps({
                        "type": "auth_error",
                        "message": "No token provided"
                    }))
                    continue

            # If not authenticated, require authentication
            if not current_user or not session_context:
                await websocket.send_text(json.dumps({
                    "type": "auth_required",
                    "message": "Authentication required"
                }))
                continue

            # Normalize control frames: if text contains JSON with only chat_id, treat as control not user content
            if isinstance(message, dict) and isinstance(message.get("text"), str):
                txt = message.get("text", "").strip()
                if txt.startswith("{") and "chat_id" in txt:
                    try:
                        parsed = json.loads(txt)
                        if isinstance(parsed, dict) and set(parsed.keys()) <= {"chat_id", "type"}:
                            # Promote to control field if not already present or different
                            if not message.get("chat_id") and parsed.get("chat_id"):
                                message["chat_id"] = parsed.get("chat_id")
                            # Remove text so it won't be treated as user content
                            message["text"] = ""
                    except Exception:
                        pass

            # Handle chat creation/continuation (only if user is authenticated). Process BEFORE filtering non-user messages
            if isinstance(message, dict) and "chat_id" in message:
                chat_id = message.get("chat_id")

                if chat_id and chat_id != current_chat_id:
                    # Chat switch requested
                    if current_chat_id:
                        # Persist current memories before switching
                        await session_context.persist_memories_to_db()
                # log persistence removed

                    # Load new chat
                    current_chat_id = chat_id
                    session_context.chat_id = current_chat_id
                    
                    # Check if this is a newly created chat (no messages yet)
                    store = await get_store()
                    existing_messages = await store.get_chat_messages(chat_id, limit=1)
                    is_first_message = len(existing_messages) == 0  # First message if no existing messages
                    print(f"[chat-switch] Chat {chat_id}: existing_messages={len(existing_messages)}, is_first_message={is_first_message}")
                    
                    await session_context.hydrate_memories_from_db(chat_id)

                    # Suppress verbose history printing; only websocket/system/agent prints allowed

                    await send_json({"event": "chat_switched", "chat_id": chat_id})
                    # If this frame contains only control info, stop here
                    if not message.get("text") and not message.get("image") and not message.get("image_path"):
                        continue
                elif chat_id is None and not current_chat_id:
                    # Create new chat (only if no current chat and chat_id is explicitly null)
                    current_chat_id = await create_chat(
                        user_id=current_user.id,
                        title=message.get("title", "New chat")
                    )
                    # Update session context with new chat_id
                    session_context.chat_id = current_chat_id
                    is_first_message = True  # Mark this as the first message
                    await send_json({"event": "chat_created", "chat_id": current_chat_id})
                    # If this frame contains only control info, stop here
                    if not message.get("text") and not message.get("image") and not message.get("image_path"):
                        continue

            # Skip non-user-control frames (e.g., the initial token message, other control messages)
            if isinstance(message, dict):
                # Consider fields that make a message a "user message"
                has_user_content = False
                if message.get("text") and str(message.get("text")).strip() != "":
                    has_user_content = True
                if message.get("image") or message.get("image_path"):
                    has_user_content = True
                # Follow-up responses are now handled as normal messages

                if not has_user_content:
                    # Skip processing silently; restrict prints to websocket/system/agent only
                    continue

            # Add user info and session info to message
            if isinstance(message, dict):
                message["user_id"] = current_user.id
                message["user_name"] = current_user.name
                message["session_id"] = session_context.session_id

            # Save image if present
            saved_path = None
            if isinstance(message, dict) and "image" in message and message["image"]:
                image = message["image"]
                try:
                    b64 = image.get("data", "")
                    raw = base64.b64decode(b64)
                    name = image.get("name") or f"image_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
                    safe_name = name.replace("/", "_").replace("\\", "_")
                    _, ext = os.path.splitext(safe_name)
                    if not ext:
                        ext = ".bin"
                    filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}{ext}"
                    path = UPLOAD_DIR / filename
                    with open(path, "wb") as f:
                        f.write(raw)
                    saved_path = str(path)
                except Exception as e:
                    await session_context.add_log("error", f"Failed to save image: {e}", level="error")

            # attach image path to the message dict so social media manager can see it
            if saved_path:
                if isinstance(message, dict):
                    message["image_path"] = saved_path
                else:
                    message = {"text": str(message), "image_path": saved_path, "user_id": current_user.id, "session_id": session_context.session_id}

            # Save user message to MongoDB (chat-scoped only)
            user_message_content = message.get("text", str(message)) if isinstance(message, dict) else str(message)
            
            # Prepare metadata for storage
            meta = {}
            if saved_path:
                meta["image_path"] = saved_path
            if isinstance(message, dict) and "metadata" in message and message["metadata"]:
                # Include media metadata from Cloudinary upload
                media_meta = message["metadata"]
                if "media_url" in media_meta:
                    meta["media_url"] = media_meta["media_url"]
                if "media_type" in media_meta:
                    meta["media_type"] = media_meta["media_type"]
                if "public_id" in media_meta:
                    meta["public_id"] = media_meta["public_id"]
                if "resource_type" in media_meta:
                    meta["resource_type"] = media_meta["resource_type"]
                if "bytes" in media_meta:
                    meta["bytes"] = media_meta["bytes"]
                if "width" in media_meta:
                    meta["width"] = media_meta["width"]
                if "height" in media_meta:
                    meta["height"] = media_meta["height"]
                if "duration" in media_meta:
                    meta["duration"] = media_meta["duration"]
            
            # Save to chat-scoped storage only
            if current_chat_id:
                await save_chat_message(
                    chat_id=current_chat_id,
                    role="user",
                    content=user_message_content,
                    message_type="final_message",
                    meta=meta
                )
                
                # Generate and update chat title if this is the first message
                print(f"[title-generation] Debug: is_first_message={is_first_message}, user_message_content='{user_message_content[:50]}...'")
                if is_first_message and user_message_content.strip():
                    print(f"[title-generation] Starting title generation for chat {current_chat_id}")
                    try:
                        # Generate title asynchronously without blocking the main flow
                        asyncio.create_task(generate_and_update_title(current_chat_id, user_message_content, websocket))
                    except Exception as e:
                        print(f"[title-generation] Failed to start title generation: {e}")
                    
                    is_first_message = False  # Mark that we've processed the first message
                else:
                    print(f"[title-generation] Skipping title generation: is_first_message={is_first_message}, has_content={bool(user_message_content.strip())}")
        
            # Route based on optional agent signature; default to social media manager
            try:
                target_signature = None
                if isinstance(message, dict):
                    target_signature = (message.get("signature") or "").strip()
                
                print(f"[main.py] Message signature: '{target_signature}'")
                print(f"[main.py] Message content: {message.get('text', '')[:100]}...")

                if target_signature in ("research_agent", "asset_agent", "media_analyst", "social_media_search_agent", "media_activist", "copy_writer", "todo_planner"):
                    from utils.router import call_agent
                    user_text = message.get("text", "") if isinstance(message, dict) else str(message)
                    result = await call_agent(
                        target_signature,
                        user_text,
                        "gpt-4o-mini",
                        str(REGISTRY_PATH),
                        session_context,
                        message.get("metadata") if isinstance(message, dict) else None,
                        message.get("image_path") if isinstance(message, dict) else None,
                    )
                    
                    
                    try:
                        agent_text = result.get("text", "") if isinstance(result, dict) else str(result)
                        agent_metadata = result.get("metadata") if isinstance(result, dict) else None
                    except Exception:
                        agent_text = str(result)
                        agent_metadata = None
                    
                    # Only send response if there's actual content
                    if agent_text and agent_text.strip():
                        response_payload = {
                            "text": agent_text,
                            "agent_name": target_signature
                        }
                        
                        # Include metadata if present (for todo data, etc.)
                        if agent_metadata:
                            response_payload["metadata"] = agent_metadata
                        
                        await websocket.send_json(response_payload)
                else:
                    # Default social media manager flow
                    await social_media_manager(message, websocket, session_context=session_context, model_name="gpt-5-mini", debug=False)
            except Exception as route_err:
                await websocket.send_json({"text": f"Routing error: {route_err}"})
            continue

    except WebSocketDisconnect:
        # Clean up session on disconnect
        if session_context:
            # No global registry to unregister
            
            # Persist memories before cleanup
            if current_chat_id:
                await session_context.persist_memories_to_db()
                # log persistence removed
            
            await session_context.add_log("session_ended", "WebSocket disconnected", level="info")
            await remove_session(session_context.session_id)
    except Exception as e:
        # Handle unexpected errors
        if session_context:
            # No global registry to unregister
            
            # Persist memories before cleanup
            if current_chat_id:
                await session_context.persist_memories_to_db()
                # log persistence removed
            
            await session_context.add_log("error", f"Unexpected error: {str(e)}", level="error")
            await remove_session(session_context.session_id)
        raise


# HTTP endpoint for asset manager AI assistant
@app.post("/api/asset-manager/chat")
async def asset_manager_chat(
    request: dict,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
):
    """
    HTTP endpoint for asset manager AI assistant
    Accepts chat messages and returns AI responses using asset_agent
    """
    try:
        # Verify authentication
        user_id = auth_service.verify_token(credentials.credentials)
        if not user_id:
            return {"error": "Invalid authentication token"}, 401
        
        # Extract request data
        message = request.get("message", "")
        chat_history = request.get("chat_history", [])
        selected_brand = request.get("selected_brand", None)
        
        if not message.strip():
            return {"error": "Message cannot be empty"}, 400
        
        # Build enhanced query with chat history context
        enhanced_query = message
        
        # Add chat history context to the query
        if chat_history:
            history_context = "Previous conversation:\n"
            for msg in chat_history[-10:]:  # Last 10 messages
                role = msg.get("sender", "unknown")
                content = msg.get("text", "")
                if role == "user":
                    history_context += f"User: {content}\n"
                elif role == "agent":
                    history_context += f"Assistant: {content}\n"
            
            enhanced_query = f"{history_context}\nCurrent message: {message}"
        
        # Add selected brand context if available
        if selected_brand:
            brand_context = f"\n\nCurrent selected brand: {selected_brand.get('name', 'Unknown')} (ID: {selected_brand.get('id', 'Unknown')})"
            enhanced_query += brand_context
        
        # Call asset agent with enhanced query
        result = await asset_agent(
            query=enhanced_query,
            model_name="gpt-4o-mini",
            user_id=user_id,
            user_metadata={"selected_brand": selected_brand} if selected_brand else None
        )
        
        # Extract response text
        if isinstance(result, dict):
            response_text = result.get("text", str(result))
        else:
            response_text = str(result)
        
        return {
            "success": True,
            "response": response_text,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"Asset manager chat error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": f"Internal server error: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }, 500


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

