"""API routes for the multi-agent system."""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import logging
import asyncio

from ..core import ConductorManager, StateManager, EventBus
from ..agents import (
    RequirementsMainAgent, RequirementsReviewAgent,
    DesignMainAgent, DesignReviewAgent,
    ImplementationMainAgent, ImplementationReviewAgent,
    TestMainAgent, TestReviewAgent
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["projects"])

# Global instances (in production, use dependency injection)
state_manager = StateManager()
event_bus = EventBus()
conductor = ConductorManager(state_manager, event_bus)

# WebSocket connections
websocket_connections: Dict[str, List[WebSocket]] = {}


# Request/Response models
class ProjectCreateRequest(BaseModel):
    """Request to create a new project."""
    name: Optional[str] = None
    requirements: str
    metadata: Optional[Dict[str, Any]] = None


class ProjectResponse(BaseModel):
    """Project response."""
    project_id: str
    name: str
    status: str
    current_phase: Optional[str]
    created_at: str


class ProjectStatusResponse(BaseModel):
    """Project status response."""
    project_id: str
    name: str
    status: str
    current_phase: Optional[str]
    phases: Dict[str, Any]
    created_at: str
    updated_at: str


class DirectionRequest(BaseModel):
    """Request to provide new direction."""
    direction: Dict[str, Any]


# Initialize system on startup
async def initialize_system():
    """Initialize the multi-agent system."""
    # Connect to Redis
    await state_manager.connect()
    
    # Create agent instances with streaming callbacks
    def create_streaming_callback(agent_id: str):
        async def callback(content: str):
            await broadcast_agent_output(agent_id, content)
        return callback
    
    # Register all agents
    agents = [
        RequirementsMainAgent(create_streaming_callback("requirements_main")),
        RequirementsReviewAgent(create_streaming_callback("requirements_reviewer")),
        DesignMainAgent(create_streaming_callback("design_main")),
        DesignReviewAgent(create_streaming_callback("design_reviewer")),
        ImplementationMainAgent(create_streaming_callback("implementation_main")),
        ImplementationReviewAgent(create_streaming_callback("implementation_reviewer")),
        TestMainAgent(create_streaming_callback("test_main")),
        TestReviewAgent(create_streaming_callback("test_reviewer"))
    ]
    
    for agent in agents:
        conductor.register_agent(agent)
    
    # Subscribe to events
    event_bus.subscribe("*", handle_system_event)
    
    logger.info("Multi-agent system initialized")


async def handle_system_event(event_type: str, data: Dict[str, Any]):
    """Handle system events and broadcast to WebSocket clients."""
    project_id = data.get("project_id")
    if project_id:
        await broadcast_message(project_id, {
            "type": event_type,
            "data": data
        })


async def broadcast_agent_output(agent_id: str, content: str):
    """Broadcast agent output to all connected clients."""
    # For now, broadcast to all connections
    # In production, we'd track which project each agent is working on
    for project_id, connections in websocket_connections.items():
        await broadcast_message(project_id, {
            "type": "agent_output",
            "agent_id": agent_id,
            "content": content
        })


async def broadcast_message(project_id: str, message: Dict[str, Any]):
    """Broadcast message to WebSocket connections for a project."""
    if project_id in websocket_connections:
        dead_connections = []
        for websocket in websocket_connections[project_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending WebSocket message: {e}")
                dead_connections.append(websocket)
        
        # Remove dead connections
        for conn in dead_connections:
            websocket_connections[project_id].remove(conn)


# API Endpoints
@router.post("/projects", response_model=ProjectResponse)
async def create_project(request: ProjectCreateRequest):
    """Create a new project and start the workflow."""
    try:
        project_id = await conductor.start_project(
            requirements=request.requirements,
            name=request.name,
            metadata=request.metadata
        )
        
        # Get project status
        status = await conductor.get_status(project_id)
        if not status:
            raise HTTPException(status_code=500, detail="Failed to get project status")
        
        return ProjectResponse(
            project_id=project_id,
            name=status["name"],
            status=status["status"],
            current_phase=status["current_phase"],
            created_at=status["created_at"]
        )
        
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects", response_model=List[ProjectResponse])
async def list_projects():
    """List all projects."""
    try:
        projects = await conductor.list_projects()
        return [
            ProjectResponse(
                project_id=p["project_id"],
                name=p["name"],
                status=p["status"],
                current_phase=p["current_phase"],
                created_at=p["created_at"]
            )
            for p in projects
        ]
    except Exception as e:
        logger.error(f"Error listing projects: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}", response_model=ProjectStatusResponse)
async def get_project_status(project_id: str):
    """Get detailed project status."""
    try:
        status = await conductor.get_status(project_id)
        if not status:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return ProjectStatusResponse(**status)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/pause")
async def pause_project(project_id: str):
    """Pause project workflow."""
    try:
        result = await conductor.pause_workflow(project_id)
        if not result:
            raise HTTPException(status_code=400, detail="Failed to pause project")
        
        return {"message": "Project paused successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/resume")
async def resume_project(project_id: str, request: Optional[DirectionRequest] = None):
    """Resume project workflow with optional new direction."""
    try:
        direction = request.direction if request else None
        result = await conductor.resume_workflow(project_id, direction)
        if not result:
            raise HTTPException(status_code=400, detail="Failed to resume project")
        
        return {"message": "Project resumed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents")
async def list_agents():
    """List all registered agents."""
    try:
        agents = conductor.list_agents()
        return {"agents": agents}
    except Exception as e:
        logger.error(f"Error listing agents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket endpoint (moved from main.py)
@router.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    
    # Add to connections
    if project_id not in websocket_connections:
        websocket_connections[project_id] = []
    websocket_connections[project_id].append(websocket)
    
    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connection",
            "message": f"Connected to project {project_id}"
        })
        
        # Keep connection alive
        while True:
            # Wait for messages from client
            data = await websocket.receive_json()
            
            # Handle client messages
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif data.get("type") == "start_workflow":
                # Start workflow if not already started
                status = await conductor.get_status(project_id)
                if status and status["status"] == "initialized":
                    # This would trigger the workflow
                    pass
                    
    except WebSocketDisconnect:
        # Remove from connections
        if project_id in websocket_connections:
            websocket_connections[project_id].remove(websocket)
            if not websocket_connections[project_id]:
                del websocket_connections[project_id]
                
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        if project_id in websocket_connections:
            try:
                websocket_connections[project_id].remove(websocket)
            except ValueError:
                pass