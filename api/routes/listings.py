from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from models.base import get_db
from schemas.listings import ListingRequest, ListingResponse
from services.listings_service import ListingsService
from api.dependencies import get_current_active_user

listings_router = APIRouter(prefix="/listings", tags=["Listings"])
listings_service = ListingsService()


@listings_router.post("", response_model=ListingResponse)
async def create_listing(listing_data: ListingRequest, current_user=Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    return await listings_service.create_listing(db, current_user.id, listing_data)


@listings_router.get("", response_model=List[ListingResponse])
async def get_listings(db: AsyncSession = Depends(get_db)):
    return await listings_service.get_all_listings(db)
