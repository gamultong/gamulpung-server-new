from core.broker import EventBroker
from core.lifecycle import HLife, LifeCycle

from data.board import Point, abs_to_sec, SectionFlag
from data.board.emitter import TileEmitter
from data.bomb import InstalledBomb, BombEmitter
from handler.board.storage import _get_db, get_section
from handler.board.internal.section_handling.upgrade_section import upgrade_interaction_section
from loguru import logger
import asyncio
from datetime import datetime, timedelta
from config import BombConfig
from handler.stats import StatsHandler


class BombHandler:
    @classmethod
    async def install_bomb(cls, cur_id: str, point: Point):
        from .bomb_scheduler import enqueue_installed_bomb

        delay_seconds = BombConfig.DEFAULT_DELAY_SECONDS
        loop = asyncio.get_running_loop()
        active_at = datetime.now() + timedelta(seconds=delay_seconds)
        active_at_mono = loop.time() + delay_seconds
        installed_bomb = InstalledBomb(
            cur_id=cur_id,
            position=point,
            explosion_range=BombConfig.EXPLOSION_RANGE,
            active_at=active_at,
            active_at_mono=active_at_mono,
        )
        await enqueue_installed_bomb(installed_bomb)

        installed_events = BombEmitter.get_installed_events(installed_bomb)
        for event in installed_events:
            await EventBroker.publish(event=event)

    @classmethod
    @LifeCycle.with_async_lifecycle(
        factory=HLife.create_factory("BombHandler", "explode_bomb")
    )
    async def explode_bomb(cls, installed_bomb: InstalledBomb):
        hlife = HLife.get_lifecycle()
        point = installed_bomb.position

        sec_p = abs_to_sec(point)

        async with _get_db() as db:
            section = await get_section(db, sec_p)
            assert section

            if section.flag == SectionFlag.NUMBERING:
                await upgrade_interaction_section(db, sec_p)

            old_tile = section.at_map_tile_by_abs_point(point)

        draw_events = BombEmitter.get_draw_events(installed_bomb)
        for event in draw_events:
            await EventBroker.publish(event=event)

        explosion_events = TileEmitter.get_explosion_events(
            point,
            old_tile,
            explosion_range=installed_bomb.explosion_range,
        )
        logger.debug(explosion_events)

        hlife.add_events(draw_events + explosion_events)
        for event in explosion_events:
            await EventBroker.publish(event=event)
        await StatsHandler.record(
            "EXPLOSION",
            actor_id=installed_bomb.cur_id,
            point=point,
            value=installed_bomb.explosion_range,
            payload={
                "explosion_range": installed_bomb.explosion_range,
                "active_at": installed_bomb.active_at.isoformat(),
            },
        )
