from os import remove
from json import load
from io import BytesIO
from aiosqlite import connect
from asyncio import sleep, run
from freeGPT import AsyncClient
from discord.ui import Button, View
from discord.ext.commands import Bot
from aiohttp import ClientSession, ClientError
from discord import Intents, Embed, File, Status, Activity, ActivityType, Colour
from discord.app_commands import (
    describe,
    checks,
    BotMissingPermissions,
    MissingPermissions,
    CommandOnCooldown,
)

intents = Intents.default()
intents.message_content = True
bot = Bot(command_prefix="/", intents=intents, help_command=None)
db = None
textCompModels = ["gpt3", "gpt4", "alpaca_7b", "falcon_40b"]
imageGenModels = ["prodia", "pollinations"]


@bot.event
async def on_ready():
    print(f"\033[1;94m INFO \033[0m| {bot.user} đã kết nối Discord.")
    global db
    db = await connect("database.db")
    async with db.cursor() as cursor:
        await cursor.execute(
            "CREATE TABLE IF NOT EXISTS database(guilds INTEGER, channels INTEGER, models TEXT)"
        )
    print("\033[1;94m INFO \033[0m| Database kết nối thành công.")
    sync_commands = await bot.tree.sync()
    print(f"\033[1;94m INFO \033[0m| Đã đồng bộ {len(sync_commands)} lệnh.")
    while True:
        await bot.change_presence(
            status=Status.online,
            activity=Activity(
                type=ActivityType.playing,
                name=f"{len(bot.guilds)} máy chủ | /help",
            ),
        )
        await sleep(300)


@bot.event
async def on_guild_remove(guild):
    await db.execute("DELETE FROM database WHERE guilds = ?", (guild.id,))
    await db.commit()


@bot.tree.error
async def on_app_command_error(interaction, error):
    if isinstance(error, CommandOnCooldown):
        embed = Embed(
            description=f"Dùng lệnh Bot quá nhanh, thử lại sau {error.retry_after:.2f} giây!",
            colour=Colour.red(),
        )
        await interaction.response.send_message(embed=embed)
    elif isinstance(error, MissingPermissions):
        embed = Embed(
            description=f"Thiếu quyền `{error.missing_permissions[0]}` để sử dụng lệnh này!",
            colour=Colour.red(),
        )
    elif isinstance(error, BotMissingPermissions):
        embed = Embed(
            description=f"Bot đang thiếu quyền `{error.missing_permissions[0]}` để thực thi lệnh này!",
            colour=Colour.red(),
        )
        await interaction.response.send_message(embed=embed)
    else:
        embed = Embed(
            title="Đã xảy ra lỗi với code:",
            description=error,
            color=Colour.red(),
        )
        view = View()
        view.add_item(
            Button(
                label="Báo cáo",
                url="https://discord.com/invite/v6vhRtNU9v",
            )
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


@bot.tree.command(name="image", description="Tạo ảnh theo miêu tả của bạn!")
@describe(model=f"Hãy chọn 1 model: {', '.join(imageGenModels)}")
@describe(prompt="Hãy miêu tả ảnh mà bạn muốn Bot tạo...")
async def imagine(interaction, model: str, prompt: str):
    if model.lower() not in imageGenModels:
        await interaction.response.send_message(
            f"Sai cú pháp: Bạn buộc phải chọn 1 model: `{', '.join(imageGenModels)}`."
        )
        return
    try:
        await interaction.response.defer()
        resp = await AsyncClient.create_generation(model, prompt)
        file = File(fp=BytesIO(resp), filename="image.png", spoiler=True)
        # Giải mã Unicode và chuyển đổi thành UTF-8
        await interaction.followup.send(
            "**Note: Có thể hình ảnh do A.I. tạo là ảnh NSFW (18+) nên hình ảnh này sẽ bị đánh dấu là nội dung ẩn!**",
            file=file,
        )

    except Exception as e:
        await interaction.followup.send(str(e))


@bot.tree.command(name="ask", description="Hỏi Bot câu gì đó ???")
@describe(model=f"Hãy chọn 1 model: {', '.join(textCompModels)}")
@describe(prompt="Hãy ghi câu hỏi của bạn!")
async def ask(interaction, model: str, prompt: str):
    if model.lower() not in textCompModels:
        await interaction.response.send_message(
            f"Sai cú pháp: Bạn buộc phải chọn 1 model: `{', '.join(textCompModels)}`."
        )
        return
    try:
        await interaction.response.defer()
        resp = await AsyncClient.create_completion(model, prompt)
        if len(resp) <= 8196:
            # Giải mã Unicode và chuyển đổi thành UTF-8
            resp = resp.encode('utf-8').decode('unicode_escape')
            await interaction.followup.send(resp)
        else:
            # Tạo file UTF-8 từ chuỗi Unicode
            with open("message.txt", "w", encoding="utf-8") as file:
                file.write(resp)
            file = File("message.txt")
            await interaction.followup.send(file=file)

    except Exception as e:
        await interaction.followup.send(str(e))


@bot.tree.command(name="add", description="Tạo 1 kênh Bot tại máy chủ: Chế độ tự động trả lời tin nhắn BẬT!")
@checks.has_permissions(manage_channels=True)
@checks.bot_has_permissions(manage_channels=True)
@describe(model=f"Hãy chọn 1 model: {', '.join(textCompModels)}")
async def setup_chatbot(interaction, model: str):
    if model.lower() not in textCompModels:
        await interaction.response.send_message(
            f"Sai cú pháp: Bạn buộc phải chọn 1 model: `{', '.join(textCompModels)}`."
        )
        return

    cursor = await db.execute(
        "SELECT channels, models FROM database WHERE guilds = ?",
        (interaction.guild.id,),
    )
    data = await cursor.fetchone()
    if data:
        await interaction.response.send_message(
            "Lỗi: Bot đã tạo kênh rồi. Dùng lệnh `/reset` để xóa kênh cũ!"
        )
        return

    if model.lower() in textCompModels:
        # Tạo chủ đề mới trong thư mục hiện tại của kênh
        category = interaction.channel.category
        if category:
            channel = await category.create_text_channel(
                "freegpt-chat", slowmode_delay=15
            )
        else:
            channel = await interaction.guild.create_text_channel(
                "freegpt-chat", slowmode_delay=15
            )

        await db.execute(
            "INSERT OR REPLACE INTO database (guilds, channels, models) VALUES (?, ?, ?)",
            (
                interaction.guild.id,
                channel.id,
                model,
            ),
        )
        await db.commit()
        await interaction.response.send_message(
            f"Đã tạo kênh Bot mới: {channel.mention}."
        )
    else:
        await interaction.response.send_message(
            f"Sai cú pháp: Bạn buộc phải chọn 1 model: `{', '.join(textCompModels)}`."
        )

    # Giải mã Unicode và chuyển đổi thành UTF-8
    await interaction.response.send_message(embed=embed, view=view)


@bot.tree.command(name="reset", description="Xóa kênh Bot đã tạo!")
@checks.has_permissions(manage_channels=True)
@checks.bot_has_permissions(manage_channels=True)
async def reset_chatbot(interaction):
    cursor = await db.execute(
        "SELECT channels, models FROM database WHERE guilds = ?",
        (interaction.guild.id,),
    )
    data = await cursor.fetchone()
    if data:
        channel = await bot.fetch_channel(data[0])
        await channel.delete()
        await db.execute(
            "DELETE FROM database WHERE guilds = ?", (interaction.guild.id,)
        )
        await db.commit()
        await interaction.response.send_message(
            "Đã xóa kênh thành công!"
        )

    else:
        await interaction.response.send_message(
            "Không thể dùng lệnh này khi Bot chưa tạo kênh. Dùng `/add` để tạo kênh mới!"
        )


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if db:
        cursor = await db.execute(
            "SELECT channels, models FROM database WHERE guilds = ?",
            (message.guild.id,),
        )

        data = await cursor.fetchone()
        if data:
            channel_id, model = data
            if message.channel.id == channel_id:
                await message.channel.edit(slowmode_delay=15)
                async with message.channel.typing():
                    if message.attachments and message.attachments[0].url.endswith(
                        ".png"
                    ):
                        temp_image = "temp_image.jpg"
                        async with ClientSession() as session:
                            async with session.get(message.attachments[0].url) as image:
                                image_content = await image.read()
                                with open(temp_image, "wb") as file:
                                    file.write(image_content)
                                try:
                                    with open(temp_image, "rb") as file:
                                        data = file.read()
                                finally:
                                    remove(temp_image)
                                async with session.post(
                                    "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large",
                                    data=data,
                                    headers={"Authorization": f"Bearer {HF_TOKEN}"},
                                    timeout=20,
                                ) as resp:
                                    resp_json = await resp.json()
                                    if resp.status != 200:
                                        raise ClientError(
                                            "Unable to fetch the response."
                                        )
                                    resp = await AsyncClient.create_completion(
                                        model,
                                        f"Đã phát hiện hình ảnh: {resp_json[0]['generated_text']}. Yêu cầu của bạn: {message.content}",
                                    )
                    else:
                        resp = await AsyncClient.create_completion(
                            model, message.content
                        )
                        if (
                            "@everyone" in resp
                            or "@here" in resp
                            or "<@" in resp
                            and ">" in resp
                        ):
                            resp = (
                                resp.replace("@everyone", "@|everyone")
                                .replace("@here", "@|here")
                                .replace("<@", "<@|")
                            )
                        # Giải mã Unicode và chuyển đổi thành UTF-8
                        resp = resp.encode('utf-8').decode('unicode_escape')
                        if len(resp) <= 2000:
                            await message.reply(resp, mention_author=False)
                        else:
                            await message.reply(
                                file=File(
                                    fp=BytesIO(resp.encode("utf-8")),
                                    filename="message.txt",
                                ),
                                mention_author=False,
                            )


if __name__ == "__main__":
    with open("config.json", "r") as file:
        data = load(file)
    HF_TOKEN = data["HF_TOKEN"]
    run(bot.run(data["BOT_TOKEN"]))
