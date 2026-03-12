# utils/watermarker.py
import asyncio
from pathlib import Path
from PIL import Image
from core.logging import logger
from core.config import settings

class Watermarker:
    def __init__(self, watermark_path: str):
        self.watermark_path = Path(watermark_path)
        self._logger = logger.bind(module="Watermarker")

    def _apply_sync(self, image_path: str, output_path: str, opacity: int = 128) -> bool:
        """
        Синхронный процесс Pillow (запускается в отдельном потоке).
        """
        try:
            with Image.open(image_path).convert("RGBA") as base:
                with Image.open(self.watermark_path).convert("RGBA") as wm:
                    # Ресайз вотермарка до 15% от ширины картинки
                    wm_width = int(base.width * 0.15)
                    w_percent = (wm_width / float(wm.size[0]))
                    wm_height = int((float(wm.size[1]) * float(w_percent)))
                    wm = wm.resize((wm_width, wm_height), Image.Resampling.LANCZOS)

                    # Установка прозрачности
                    mask = wm.split()[3].point(lambda i: i * (opacity / 255))
                    
                    # Позиция: правый нижний угол (отступ 20px)
                    position = (base.width - wm.width - 20, base.height - wm.height - 20)
                    
                    base.paste(wm, position, mask)
                    
                    # Сохранение в RGB (для JPEG)
                    base.convert("RGB").save(output_path, "JPEG", quality=90)
                    return True
        except Exception as e:
            self._logger.error("watermark_failed", error=str(e), file=image_path)
            return False

    async def apply_watermark(self, image_path: str, output_path: str) -> bool:
        """
        Асинхронная обертка для тяжелой работы с изображениями.
        """
        if not self.watermark_path.exists():
            return False
        
        # Запуск в пуле потоков (не блокирует event loop)
        return await asyncio.to_thread(self._apply_sync, image_path, output_path)

# Инициализация
watermarker = Watermarker(settings.WATERMARK_PATH)
