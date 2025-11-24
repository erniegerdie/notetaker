from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID
from loguru import logger

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models import Collection
from pydantic import BaseModel

router = APIRouter(prefix="/api/collections", tags=["collections"])


class CollectionCreate(BaseModel):
    name: str
    description: str | None = None


class CollectionResponse(BaseModel):
    id: UUID
    name: str
    description: str | None = None

    class Config:
        from_attributes = True


@router.get("", response_model=List[CollectionResponse])
async def list_collections(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    """Get all collections for the current user."""
    result = await db.execute(
        select(Collection)
        .filter(Collection.user_id == user_id)
        .order_by(Collection.name)
    )
    collections = result.scalars().all()
    return collections


@router.post("", response_model=CollectionResponse, status_code=201)
async def create_collection(
    collection: CollectionCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    """Create a new collection."""
    # Check if collection with same name already exists for this user
    result = await db.execute(
        select(Collection).filter(
            Collection.name == collection.name,
            Collection.user_id == user_id
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Collection '{collection.name}' already exists"
        )

    # Create new collection with user_id
    new_collection = Collection(
        name=collection.name,
        description=collection.description,
        user_id=user_id
    )
    db.add(new_collection)
    await db.commit()
    await db.refresh(new_collection)

    logger.info(f"Created collection: {new_collection.name} ({new_collection.id})")
    return new_collection


@router.delete("/{collection_id}", status_code=204)
async def delete_collection(
    collection_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    """Delete a collection."""
    result = await db.execute(
        select(Collection).filter(
            Collection.id == collection_id,
            Collection.user_id == user_id
        )
    )
    collection = result.scalar_one_or_none()

    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    await db.delete(collection)
    await db.commit()

    logger.info(f"Deleted collection: {collection.name} ({collection_id})")
