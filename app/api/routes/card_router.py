from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound

from app.core.deps import get_current_user, get_session
from app.rules.card import CardRules
from app.schemas.card_schema import (
    CardDependenciesResponse,
    CardDependencyAdd,
    CardHistorySchema,
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
        ..., title="ID da lista", description="ID da lista onde o card será criado"
    ),
    current_user: UserSchema = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_session),
):
    """
    Cria um novo card em uma lista específica.
    """
    rules = CardRules(db_session)

    try:
        new_card_id = await rules.add_card(list_id, card_data)
        return new_card_id
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/search", response_model=list[CardSearchResult])
async def search_cards(
    q: str = Query(..., description="Busca por título ou número do card"),
    project_id: int = Query(None, description="Filtra por projeto (opcional)"),
    current_user: UserSchema = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_session),
):
    """
    Busca cards por título ou número, retornando até 10 resultados.
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
    Retorna um card por ID com seus relacionamentos.
    """
    rules = CardRules(db_session)

    try:
        card = await rules.get_card_by_id(card_id)
        return card
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail=f"Card com id={card_id} não encontrado."
        )


@router.put("/{card_id}", response_model=CardSchema)
async def update_card(
    card_id: int,
    card_data: CardSchemaUp,
    current_user: UserSchema = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_session),
):
    """
    Atualiza um card e seus relacionamentos.
    """
    rules = CardRules(db_session)

    try:
        updated_card = await rules.update_card(card_id, card_data)
        return updated_card
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail=f"Card com id={card_id} não encontrado."
        )


@router.get("/{card_id}/history", response_model=list[CardHistorySchema])
async def get_card_history(
    card_id: int,
    current_user: UserSchema = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_session),
):
    """
    Retorna o histórico de eventos de um card (movimentações, atribuições, etc.).
    """
    rules = CardRules(db_session)
    return await rules.get_card_history(card_id)


@router.get("/{card_id}/dependencies", response_model=CardDependenciesResponse)
async def get_card_dependencies(
    card_id: int,
    current_user: UserSchema = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_session),
):
    """Retorna os cards relacionados (dependências) deste card."""
    rules = CardRules(db_session)
    return await rules.get_dependencies(card_id)


@router.post("/{card_id}/dependencies", status_code=status.HTTP_201_CREATED)
async def add_card_dependency(
    card_id: int,
    body: CardDependencyAdd,
    current_user: UserSchema = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_session),
):
    """Adiciona um card como dependência."""
    rules = CardRules(db_session)
    await rules.add_dependency(card_id, body.related_card_id)


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
    """Remove uma dependência do card."""
    rules = CardRules(db_session)
    await rules.remove_dependency(card_id, related_card_id)


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_card(
    card_id: int,
    current_user: UserSchema = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_session),
):
    """
    Deleta um card e seus relacionamentos. Apenas SuperAdmin do projeto pode deletar.
    """
    rules = CardRules(db_session)

    try:
        await rules.delete_card(card_id, user_id=current_user.id)
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail=f"Card com id={card_id} não encontrado."
        )
