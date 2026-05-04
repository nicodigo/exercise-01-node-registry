from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from src.database import engine, get_db, Base
from src.models import Node
from src.schemas import NodeCreate, NodeUpdate, NodeResponse

app = FastAPI()

# Create tables on startup (for development)
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

# Health endpoint
@app.get("/health")
def health(db: Session = Depends(get_db)):
    # TODO: implement proper health check
    nodes_count = db.query(Node).filter(Node.status == "active").count()
    return {"status": "ok", "db": "connected", "nodes_count": nodes_count}

# Endpoints (placeholders with TODO logic)
@app.post("/api/nodes", status_code=status.HTTP_201_CREATED)
def create_node(payload: NodeCreate, db: Session = Depends(get_db)):
    # TODO: implement node creation with duplicate detection
    # Placeholder: raise not implemented
    raise NotImplementedError("TODO: implement create_node")

@app.get("/api/nodes")
def list_nodes(db: Session = Depends(get_db)):
    # TODO: implement list all nodes (including inactive)
    raise NotImplementedError("TODO: implement list_nodes")

@app.get("/api/nodes/{name}")
def get_node(name: str, db: Session = Depends(get_db)):
    # TODO: implement get node by name
    raise NotImplementedError("TODO: implement get_node")

@app.put("/api/nodes/{name}")
def update_node(name: str, payload: NodeUpdate, db: Session = Depends(get_db)):
    # TODO: implement partial update of node host/port
    raise NotImplementedError("TODO: implement update_node")

@app.delete("/api/nodes/{name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_node(name: str, db: Session = Depends(get_db)):
    # TODO: implement soft delete (set status to inactive)
    raise NotImplementedError("TODO: implement delete_node")
    # Return None for 204
