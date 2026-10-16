from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin, get_db
from app.models.partner import Partner
from app.models.user import User
from app.schemas.partner import PartnerCreate, PartnerResponse, PartnerUpdate
from app.services.geo_service import geo_service

router = APIRouter()


@router.get("", response_model=list[PartnerResponse])
async def list_partners(
    db: Annotated[AsyncSession, Depends(get_db)],
    user_lat: float | None = Query(default=None),
    user_lon: float | None = Query(default=None),
    category: str | None = Query(default=None),
    radius_km: float | None = Query(default=None),
    limit: int = 50,
):
    query = select(Partner).where(Partner.is_active.is_(True))
    result = await db.execute(query)
    partners = result.scalars().all()

    response_list: list[PartnerResponse] = []
    for partner in partners:
        if category and category.upper() not in [c.strip().upper() for c in partner.accepted_categories.split(",")]:
            continue

        distance_km = None
        if user_lat is not None and user_lon is not None:
            distance_km = geo_service.calculate_haversine_distance(
                user_lat, user_lon, partner.latitude, partner.longitude
            )
            if radius_km is not None and distance_km > radius_km:
                continue

        p_dict = {
            "id": partner.id,
            "name": partner.name,
            "address": partner.address,
            "latitude": partner.latitude,
            "longitude": partner.longitude,
            "accepted_categories": partner.accepted_categories,
            "phone_number": partner.phone_number,
            "operational_hours": partner.operational_hours,
            "capacity_info": partner.capacity_info,
            "requirements": partner.requirements,
            "is_active": partner.is_active,
            "created_at": partner.created_at,
            "distance_km": distance_km,
        }
        response_list.append(PartnerResponse(**p_dict))

    if user_lat is not None and user_lon is not None:
        response_list.sort(key=lambda x: x.distance_km if x.distance_km is not None else float("inf"))

    return response_list[:limit]


@router.get("/{partner_id}", response_model=PartnerResponse)
async def get_partner(
    partner_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_lat: float | None = Query(default=None),
    user_lon: float | None = Query(default=None),
):
    result = await db.execute(select(Partner).where(Partner.id == partner_id))
    partner = result.scalars().first()
    if not partner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Partner not found")

    distance_km = None
    if user_lat is not None and user_lon is not None:
        distance_km = geo_service.calculate_haversine_distance(user_lat, user_lon, partner.latitude, partner.longitude)

    partner_dict = {
        "id": partner.id,
        "name": partner.name,
        "address": partner.address,
        "latitude": partner.latitude,
        "longitude": partner.longitude,
        "accepted_categories": partner.accepted_categories,
        "phone_number": partner.phone_number,
        "operational_hours": partner.operational_hours,
        "capacity_info": partner.capacity_info,
        "requirements": partner.requirements,
        "is_active": partner.is_active,
        "created_at": partner.created_at,
        "distance_km": distance_km,
    }
    return PartnerResponse(**partner_dict)


@router.post("", response_model=PartnerResponse, status_code=status.HTTP_201_CREATED)
async def create_partner(
    partner_in: PartnerCreate,
    current_admin: Annotated[User, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    partner = Partner(**partner_in.model_dump())
    db.add(partner)
    await db.commit()
    await db.refresh(partner)
    return partner


@router.put("/{partner_id}", response_model=PartnerResponse)
async def update_partner(
    partner_id: int,
    partner_in: PartnerUpdate,
    current_admin: Annotated[User, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Partner).where(Partner.id == partner_id))
    partner = result.scalars().first()
    if not partner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Partner not found")

    update_data = partner_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(partner, field, val)

    db.add(partner)
    await db.commit()
    await db.refresh(partner)
    return partner


@router.delete("/{partner_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_partner(
    partner_id: int,
    current_admin: Annotated[User, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Partner).where(Partner.id == partner_id))
    partner = result.scalars().first()
    if not partner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Partner not found")

    await db.delete(partner)
    await db.commit()
    return None
