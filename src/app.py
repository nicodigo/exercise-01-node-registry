from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from src.database import engine, get_db, Base
from src.models import Node
from src.schemas import NodeCreate, NodeUpdate, NodeResponse
from sqlalchemy import text

app = FastAPI()

# Create tables on startup (for development)
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

# Health endpoint
@app.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        # Execute simple checkhealth
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
        raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"status": "unhealthy", "db": db_status}
        )
    nodes_count = db.query(Node).filter(Node.status == "active").count()
    return {"status": "ok", "db": "connected", "nodes_count": nodes_count}

# Endpoints (placeholders with TODO logic)
@app.post("/api/nodes", status_code=status.HTTP_201_CREATED)
def create_node(payload: NodeCreate, db: Session = Depends(get_db)):
    # Check if node with the same name already exists
    existing: bool = db.query(Node).filter(Node.name == payload.name).first()
    if existing:
        raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Node with name '{payload.name}' already exists"
        )

    # Create new node
    # Pydantic validates that payload doesnt have null values
    node = Node(
        name=payload.name,
        host=payload.host,
        port=payload.port,
        status="active", # Default
        )
    db.add(node)
    db.commit()
    db.refresh(node)

    return NodeResponse.model_validate(node)


@app.get("/api/nodes")
def list_nodes(db: Session = Depends(get_db)):
    nodes = db.query(Node).all()
    return [NodeResponse.model_validate(node) for node in nodes]

@app.get("/api/nodes/{name}")
def get_node(name: str, db: Session = Depends(get_db)):
    node: Node = db.query(Node).filter(Node.name == name).first()
    if not(node):
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Node not found",
        )
    return NodeResponse.model_validate(node)

@app.put("/api/nodes/{name}")
def update_node(name: str, payload: NodeUpdate, db: Session = Depends(get_db)):
    node = db.query(Node).filter(Node.name == name).first()
    if not(node):
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Node not found",
        )

    if payload.host is not None:
        node.host = payload.host # type: ignore
    if payload.port is not None:
        node.port = payload.port # type: ignore

    db.commit()
    db.refresh(node)

    return NodeResponse.model_validate(node)

@app.delete("/api/nodes/{name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_node(name: str, db: Session = Depends(get_db)):
    node = db.query(Node).filter(Node.name == name).first()
    if not(node):
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Node not found",
        )

    node.status = "inactive" # type: ignore

    db.commit()
    db.refresh(node)
    # No return statement needed - FastAPI will respond with 204 and no body
