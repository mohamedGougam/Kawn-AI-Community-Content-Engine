"""AI settings API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import AIProviderSetting
from app.schemas import AIProviderSettingResponse, AIProviderSettingUpdate
from app.services.ai.provider import provider_has_key, PROVIDERS

router = APIRouter(prefix="/api/settings/ai", tags=["ai-settings"])


@router.get("", response_model=list[AIProviderSettingResponse])
async def list_ai_settings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AIProviderSetting).order_by(AIProviderSetting.provider))
    settings = result.scalars().all()

    if not settings:
        for name in PROVIDERS:
            setting = AIProviderSetting(
                provider=name,
                is_active=name == "mock",
                is_default=name == "mock",
                model=getattr(PROVIDERS[name](), "model", None),
            )
            db.add(setting)
        await db.flush()
        result = await db.execute(select(AIProviderSetting).order_by(AIProviderSetting.provider))
        settings = result.scalars().all()

    return [
        AIProviderSettingResponse(
            id=s.id,
            provider=s.provider,
            is_active=s.is_active,
            is_default=s.is_default,
            model=s.model,
            temperature=s.temperature,
            max_tokens=s.max_tokens,
            api_key_env=s.api_key_env,
            settings=s.settings or {},
            has_api_key=provider_has_key(s.provider),
        )
        for s in settings
    ]


@router.post("/{provider}", response_model=AIProviderSettingResponse)
async def update_ai_setting(
    provider: str, data: AIProviderSettingUpdate, db: AsyncSession = Depends(get_db)
):
    if provider not in PROVIDERS:
        raise HTTPException(status_code=404, detail=f"Unknown provider: {provider}")

    result = await db.execute(select(AIProviderSetting).where(AIProviderSetting.provider == provider))
    setting = result.scalar_one_or_none()

    if not setting:
        setting = AIProviderSetting(provider=provider)
        db.add(setting)

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(setting, key, value)

    if data.is_default:
        await db.execute(update(AIProviderSetting).values(is_default=False))
        setting.is_default = True

    await db.flush()
    await db.refresh(setting)

    return AIProviderSettingResponse(
        id=setting.id,
        provider=setting.provider,
        is_active=setting.is_active,
        is_default=setting.is_default,
        model=setting.model,
        temperature=setting.temperature,
        max_tokens=setting.max_tokens,
        api_key_env=setting.api_key_env,
        settings=setting.settings or {},
        has_api_key=provider_has_key(setting.provider),
    )
