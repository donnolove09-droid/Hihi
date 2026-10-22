
import os
import json
import logging
import aiohttp

from urllib.parse import quote
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

API_BASE = "https://flash-player-info-v1.vercel.app"
API_UID = os.environ["API_UID"]
API_PASSWORD = os.environ["API_PASSWORD"]
BOT_TOKEN = os.environ["BOT_TOKEN"]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 FREE FIRE PLAYER INFO\n\n"
        "Dùng lệnh:\n"
        "/info UID\n\n"
        "Ví dụ:\n"
        "/info 3419823759"
    )


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "⚠️ Vui lòng nhập UID.\nVí dụ: /info 3419823759"
        )
        return

    uid = context.args[0].strip()

    if not uid.isdigit() or not 1 <= len(uid) <= 20:
        await update.message.reply_text("❌ UID không hợp lệ.")
        return

    url = (
        f"{API_BASE}/{quote(API_UID, safe='')}/"
        f"{quote(API_PASSWORD, safe='')}/player-info"
    )

    await update.message.reply_text("🔎 Đang tra cứu người chơi...")

    timeout = aiohttp.ClientTimeout(total=20)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, params={"uid": uid}) as response:
                if response.status != 200:
                    await update.message.reply_text(
                        f"⚠️ API trả về lỗi HTTP {response.status}."
                    )
                    return

                data = await response.json(content_type=None)

        if isinstance(data, (dict, list)):
            result = json.dumps(
                data, ensure_ascii=False, indent=2
            )
        else:
            result = str(data)

        if not result or result == "{}" or result == "[]":
            await update.message.reply_text(
                "Không tìm thấy dữ liệu người chơi."
            )
            return

        # Telegram giới hạn độ dài tin nhắn.
        chunks = [result[i:i + 3500] for i in range(0, len(result), 3500)]

        for chunk in chunks:
            await update.message.reply_text(
                f"🎮 KẾT QUẢ TRA CỨU\n\n{chunk}"
            )

    except aiohttp.ClientError:
        await update.message.reply_text(
            "❌ Không thể kết nối API. Hãy thử lại sau."
        )
    except (TimeoutError, json.JSONDecodeError):
        await update.message.reply_text(
            "⚠️ API phản hồi chậm hoặc dữ liệu không hợp lệ."
        )
    except Exception:
        logging.exception("Player lookup failed")
        await update.message.reply_text(
            "❌ Có lỗi xảy ra khi tra cứu."
        )


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("info", info))
    app.run_polling()


if __name__ == "__main__":
    main()
