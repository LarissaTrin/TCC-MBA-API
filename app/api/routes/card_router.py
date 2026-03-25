from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound

from app.core.deps import get_current_user, get_session
from app.rules.card import CardRules
from app.schemas.card_schema import (
    CardDependenciesResponse,
    CardDependencyAdd,
    CardHistorySchema,
    CardReorderRequest,
    CardSchema,
    CardSchemaBase,
    CardSchemaUp,
    CardSearchResult,
)
from app.schemas.user_schema import UserSchema

router = APIRouter()


@router.post("/{list_id}", response_model=int, status_code=status.HTTP_201_CREATED)
async def create_card(
    card_data: CardSchemaBase,
    list_id: int = Path(
        ..., title="List ID", description="ID of the list where the card will be created"
    ),
    current_user: UserSchema = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_session),
):
    """
    Creates a new card in a specific list.
    """
    rules = CardRules(db_session)

    try:
        new_card_id = await rules.add_card(list_id, card_data, user_id=current_user.id)
        return new_card_id
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/search", response_model=list[CardSearchResult])
async def search_cards(
    q: str = Query(..., description="Search by card title or number"),
    project_id: int = Query(None, description="Filter by project (optional)"),
    current_user: UserSchema = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_session),
):
    """
    Searches cards by title or number, returning up to 10 results.
    """
    rules = CardRules(db_session)
    return await rules.search_cards(q, project_id)


@router.get("/{card_id}", response_model=CardSchema)
async def get_card_by_id(
    card_id: int,
    current_user: UserSchema = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_session),
):
    """
    Returns a card by ID with its relationships.
    """
    rules = CardRules(db_session)

    try:
        card = await rules.get_card_by_id(card_id)
        return card
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail=f"Card id={card_id} not found."
        )


@router.put("/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_cards(
    body: CardReorderRequest,
    current_user: UserSchema = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_session),
):
    """
    Bulk-updates sort_order for multiple cards at once (table view reorder).
    """
    rules = CardRules(db_session)
    await rules.bulk_reorder(body.items)


@router.put("/{card_id}", response_model=CardSchema)
async def update_card(
    card_id: int,
    card_data: CardSchemaUp,
    current_user: UserSchema = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_session),
):
    """
    Updates a card and its relationships.
    """
    rules = CardRules(db_session)

    try:
        updated_card = await rules.update_card(card_id, card_data, user_id=current_user.id)
        return updated_card
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail=f"Card id={card_id} not found."
        )


@router.get("/{card_id}/history", response_model=list[CardHistorySchema])
async def get_card_history(
    card_id: int,
    current_user: UserSchema = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_session),
):
    """
    Returns the event history of a card (moves, assignments, priority changes, etc.).
    """
    rules = CardRules(db_session)
    return await rules.get_card_history(card_id)


@router.get("/{card_id}/dependencies", response_model=CardDependenciesResponse)
async def get_card_dependencies(
    card_id: int,
    current_user: UserSchema = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_session),
):
    """Returns related cards (dependencies) for this card."""
    rules = CardRules(db_session)
    return await rules.get_dependencies(card_id)


@router.post("/{card_id}/dependencies", status_code=status.HTTP_201_CREATED)
async def add_card_dependency(
    card_id: int,
    body: CardDependencyAdd,
    current_user: UserSchema = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_session),
):
    """Adds a card as a dependency."""
    rules = CardRules(db_session)
    await rules.add_dependency(card_id, body.related_card_id, user_id=current_user.id)


@router.delete(
    "/{card_id}/dependencies/{related_card_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_card_dependency(
    card_id: int,
    related_card_id: int,
    current_user: UserSchema = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_session),
):
    """Removes a dependency from the card."""
    rules = CardRules(db_session)
    await rules.remove_dependency(card_id, related_card_id, user_id=current_user.id)


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_card(
    card_id: int,
    current_user: UserSchema = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_session),
):
    """
    Deletes a card and its relationships. Only SuperAdmin or Admin can delete cards.
    """
    rules = CardRules(db_session)

    try:
        await rules.delete_card(card_id, user_id=current_user.id)
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail=f"Card id={card_id} not found."
        )
