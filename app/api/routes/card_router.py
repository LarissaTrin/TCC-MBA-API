from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound

from app.core.deps import get_current_user, get_session
from app.rules.card import CardRules
from app.schemas.card_schema import CardSchema, CardSchemaBase, CardSchemaUp
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


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_card(
    card_id: int,
    current_user: UserSchema = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_session),
):
    """
    Deleta um card e seus relacionamentos.
    """
    rules = CardRules(db_session)

    try:
        await rules.delete_card(card_id)
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail=f"Card com id={card_id} não encontrado."
        )
