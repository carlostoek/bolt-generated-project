from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import LorePiece

class LorePieceService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def code_exists(self, code_name: str) -> bool:
        stmt = select(LorePiece).where(LorePiece.code_name == code_name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create_lore_piece(
        self,
        code_name: str,
        title: str,
        content_type: str,
        content: str,
        *,
        description: str | None = None,
        category: str | None = None,
        is_main_story: bool = False,
    ) -> LorePiece:
        piece = LorePiece(
            code_name=code_name,
            title=title,
            description=description,
            content_type=content_type,
            content=content,
            category=category,
            is_main_story=is_main_story,
        )
        self.session.add(piece)
        await self.session.commit()
        await self.session.refresh(piece)
        return piece

    async def get_lore_piece_by_code(self, code_name: str) -> LorePiece | None:
        stmt = select(LorePiece).where(LorePiece.code_name == code_name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_lore_piece(
        self,
        code_name: str,
        *,
        title: str | None = None,
        description: str | None = None,
        category: str | None = None,
        is_main_story: bool | None = None,
        content_type: str | None = None,
        content: str | None = None,
    ) -> bool:
        piece = await self.get_lore_piece_by_code(code_name)
        if not piece:
            return False
        if title is not None:
            piece.title = title
        if description is not None:
            piece.description = description
        if category is not None:
            piece.category = category
        if is_main_story is not None:
            piece.is_main_story = is_main_story
        if content_type is not None:
            piece.content_type = content_type
        if content is not None:
            piece.content = content
        await self.session.commit()
        return True

    async def delete_lore_piece(self, code_name: str) -> bool:
        piece = await self.get_lore_piece_by_code(code_name)
        if not piece:
            return False
        await self.session.delete(piece)
        await self.session.commit()
        return True

    async def toggle_piece_status(self, code_name: str, status: bool) -> bool:
        piece = await self.get_lore_piece_by_code(code_name)
        if piece:
            piece.is_active = status
            await self.session.commit()
            return True
        return False
