import discord
from discord.ext import commands
import os
import sqlite3
import random
import asyncio
from datetime import datetime
from threading import Thread
from flask import Flask
from gtts import gTTS 
import tempfile
import time

# --- CẤU HÌNH DỮ LIỆU LỚN VÀ LOGIC GAME ---

# 1. Cấp bậc (Rarity) và Tỷ lệ random (Phần trăm)
RARITY_CONFIG = {
    "Hư Hại": 35, "Bình Thường": 30, "Hiếm Có": 20, "Sử Thi": 10, 
    "Bán Thần Thoại": 4, "Thần Thoại": 0.9, "Đấng Cứu Thế": 0.1,
}
RARITY_NAMES = list(RARITY_CONFIG.keys())
RARITY_WEIGHTS = list(RARITY_CONFIG.values())

# 2. DỮ LIỆU VŨ KHÍ (30 Loại)
WEAPON_TYPES = [
    "Kiếm Lưỡi Hái", "Kiếm Nhật Katana", "Kiếm Thiên Thần", "Song Kiếm", "Kiếm Lửa Địa Ngục", 
    "Trượng Bão Tuyết", "Trượng Sấm Sét", "Trượng Hồi Sinh", "Trượng Cổ Đại", "Trượng Lửa",
    "Súng Laser", "Súng Pháo Đài", "Súng Bắn Tỉa", "Súng Máy Mini", "Súng Lục",
    "Giáp Rồng", "Giáp Thép Titan", "Giáp Pha Lê", "Giáp Hộ Mệnh", "Giáp Bóng Đêm",
    "Cung Thần Gió", "Cung Băng Giá", "Cung Tinh Linh", "Nỏ Lớn", "Cung Ngắn",
    "Khiên Kim Cương", "Khiên Titan", "Khiên Phù Thủy", "Khiên Rồng", "Khiên Gỗ Cứng",
]

# 3. DỮ LIỆU KỸ NĂNG (50 Skill)
SKILLS = [
    "Cú Đấm Sấm Sét", "Hơi Thở Rồng", "Lá Chắn Ánh Sáng", "Hồi Máu Diện Rộng", "Tăng Tốc Độ",
    "Chém Xuyên Giáp", "Bắn Tỉa Chí Mạng", "Triệu Hồi Thần", "Khóa Kỹ Năng", "Hút Hồn",
    "Độc Tố Lan Truyền", "Phục Kích", "Đỡ Đòn Hoàn Hảo", "Nộ Long", "Ám Ảnh",
    "Băng Giá Vĩnh Cửu", "Hỏa Diệm Sơn", "Tia Chớp Phẫn Nộ", "Kháng Ma Thuật", "Phá Vỡ Khiên",
    "Thao Túng Thời Gian", "Dịch Chuyển Tức Thời", "Hóa Đá Kẻ Thù", "Mưa Mũi Tên", "Bẫy Ngầm",
    "Gió Lốc Cuồng Nộ", "Tiếng Thét Hủy Diệt", "Lưỡi Cắt Không Gian", "Nguyền Rủa Sức Mạnh", "Gây Mù",
    "Tạo Vòng Bảo Vệ", "Lôi Đài Chiến Đấu", "Sức Mạnh Bất Diệt", "Cú Đấm Ngàn Cân", "Hào Quang Phép Thuật",
    "Phục Hồi Nhanh", "Tấn Công Liên Hoàn", "Hóa Giải Độc", "Tăng Sức Chịu Đựng", "Nước Mắt Thiên Thần",
    "Gia Tăng Tầm Đánh", "Cảm Tử", "Bóng Ma", "Khiên Phản Chiếu", "Tăng Tỷ Lệ Rớt Đồ",
    "Thu Phục Quái Vật", "Biến Hình", "Áp Chế", "Khóa Mục Tiêu", "Cơ Động Thần Tốc",
]

# 4. DỮ LIỆU PET (50 Loại)
PET_NAMES = [
    "Lân Sư Rồng (Tết)", "Chim Lạc (Giỗ Tổ)", "Cóc Thần (Mưa)", "Thiên Cẩu (Trung Thu)", "Rồng Vàng (Mùng 1)",
    "Hùng Vương Thần Lực", "Thánh Gióng", "Âu Cơ", "Lạc Long Quân", "Phù Đổng Thiên Vương",
    "Hổ Đông Dương", "Voi Rừng Tây Nguyên", "Sơn Tinh", "Thủy Tinh", "Sếu Đầu Đỏ",
    "Tinh Linh Ánh Sáng", "Bóng Ma Cổ", "Thần Tài Mini", "Tiên Nữ Hoa", "Quỷ Lửa",
    *[f"Pet Chiến Đấu {i}" for i in range(1, 31)]
]

# 5. Pet Ẩn Cực Kì Quan Trọng (Ngày Bác Hồ Sinh - 19/5)
HIDDEN_PET_NAME = "Hồ Chí Minh Bất Tử"
HIDDEN_PET_RARITY = "Đấng Cứu Thế"
HIDDEN_PET_DATE = (5, 19) # (Tháng, Ngày)

# 6. CẤU HÌNH CHÀO/TẠM BIỆT NGẪU NHIÊN (6 PHONG CÁCH)
WELCOME_MESSAGES = [
    "🎉 Chào mừng **{name}** đến với bến đỗ mới! Đã tặng **100** xu khởi nghiệp.", 
    "🥳 Woa! **{name}** đã xuất hiện! Sẵn sàng quẩy chưa? (100 xu đã vào ví)", 
    "👋 Huhu, mừng **{name}** ghé thăm! Mau vào tìm đồng đội nào. (100 xu)", 
    "👾 Thành viên mới **{name}** vừa hạ cánh. Cẩn thận, code bot tôi đã bị thay đổi! (100 xu)", 
    "🔔 Thông báo: **{name}** đã gia nhập. Xin hãy giữ trật tự! (100 xu)", 
    "😎 Một huyền thoại mới: **{name}**! Chào mừng! (100 xu khởi nghiệp)" 
]

GOODBYE_MESSAGES = [
    "💔 **{name}** đã rời đi. Tạm biệt và hẹn gặp lại!", 
    "👋 Cảm ơn **{name}** đã dành thời gian ở đây! Chúc may mắn.", 
    "😭 Một chiến binh **{name}** đã ngã xuống. Thế giới game cần bạn trở lại!", 
    "🚪 **{name}** thoát server. Chắc là đi ngủ sớm rồi! Bye!", 
    "🚨 **{name}** đã bị hệ thống phát hiện và rời đi.", 
    "✨ Chuyến đi bình an, **{name}**!" 
]

# --- CẤU HÌNH BOT VÀ DATABASE ---

TOKEN = os.getenv('DISCORD_TOKEN') 
WELCOME_CHANNEL_ID = 123456789012345678 # <<< THAY ID KÊNH CỦA BẠN >>>

intents = discord.Intents.default()
intents.members = True 
intents.message_content = True 

bot = commands.Bot(command_prefix='!', intents=intents)

# --- DATABASE SETUP ---

DB_NAME = 'economy.db'
conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        balance INTEGER DEFAULT 0
    )
''')

c.execute('''
    CREATE TABLE IF NOT EXISTS user_inventory (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        item_name TEXT,
        rarity TEXT,
        skin_percent INTEGER,
        skill_main TEXT,
        skill_sub1 TEXT, skill_sub2 TEXT, skill_sub3 TEXT, skill_sub4 TEXT,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
''')

c.execute('''
    CREATE TABLE IF NOT EXISTS user_pets (
        pet_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        pet_name TEXT,
        rarity TEXT,
        pet_skill TEXT,
        is_hidden BOOLEAN,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
''')
conn.commit()

# --- HÀM HỖ TRỢ DATABASE VÀ ITEM ---

def get_balance(user_id):
    c.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    if result: return result[0]
    c.execute('INSERT INTO users (user_id, balance) VALUES (?, ?)', (user_id, 0))
    conn.commit()
    return 0

def update_balance(user_id, amount):
    balance = get_balance(user_id)
    new_balance = balance + amount
    c.execute('UPDATE users SET balance = ? WHERE user_id = ?', (new_balance, user_id))
    conn.commit()
    return new_balance

def random_roll_rarity():
    return random.choices(RARITY_NAMES, weights=RARITY_WEIGHTS, k=1)[0]

def random_roll_skills(num_skills):
    return random.sample(SKILLS, k=min(num_skills, len(SKILLS)))

def random_roll_weapon():
    rarity = random_roll_rarity()
    weapon_type = random.choice(WEAPON_TYPES)
    skin_percent = random.randint(0, 100)
    skills = random_roll_skills(5)
    
    return {
        "name": f"[{rarity}] {weapon_type}",
        "rarity": rarity,
        "skin_percent": skin_percent,
        "skill_main": skills[0],
        "skill_sub1": skills[1],
        "skill_sub2": skills[2],
        "skill_sub3": skills[3],
        "skill_sub4": skills[4],
    }

def add_item_to_inventory(user_id, item):
    c.execute(
        '''INSERT INTO user_inventory (user_id, item_name, rarity, skin_percent, skill_main, skill_sub1, skill_sub2, skill_sub3, skill_sub4) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (user_id, item['name'], item['rarity'], item['skin_percent'], item['skill_main'], item['skill_sub1'], item['skill_sub2'], item['skill_sub3'], item['skill_sub4'])
    )
    conn.commit()


# --- LỆNH MỚI: TRÌNH ĐỌC TIN NHẮN (TTS) ---

@bot.command(name="speak", aliases=["tts"])
async def speak_command(ctx, *, text: str):
    """Lệnh !speak <tin nhắn> để bot đọc tin nhắn trong kênh thoại."""
    
    if not ctx.message.author.voice:
        await ctx.send("❌ Bạn phải ở trong một kênh thoại để sử dụng lệnh này.")
        return
        
    voice_channel = ctx.message.author.voice.channel
    
    # Giới hạn độ dài tin nhắn
    if len(text) > 100:
        text = text[:100] + "..."

    # Tạo file âm thanh TTS
    mp3_filepath = None
    try:
        # Lang='vi' (Tiếng Việt), slow=False (Tốc độ thường)
        tts = gTTS(text=text, lang='vi', slow=False) 
        
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
            tts.write_to_fp(tmp_file)
            mp3_filepath = tmp_file.name
            
    except Exception as e:
        await ctx.send(f"❌ Lỗi tạo file âm thanh (TTS): {e}")
        return

    # Kết nối và phát âm thanh
    try:
        # Kết nối/Chuyển kênh
        if ctx.voice_client:
            if ctx.voice_client.channel != voice_channel:
                await ctx.voice_client.move_to(voice_channel)
        else:
            await voice_channel.connect()
            
        # Phát file .mp3 đã tạo (Yêu cầu FFmpeg hoạt động)
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
        
        ctx.voice_client.play(discord.FFmpegPCMAudio(mp3_filepath), after=lambda e: print(f'Player error: {e}') if e else None)
        await ctx.send(f"🔊 Đã phát: **{text}**")
        
        # Chờ phát xong rồi ngắt kết nối
        while ctx.voice_client.is_playing():
             await asyncio.sleep(1)
        
        await ctx.voice_client.disconnect()

    except discord.ClientException:
        await ctx.send("❌ Bot đang bận hoặc có lỗi kết nối. Hãy thử lại sau.")
    except Exception as e:
        await ctx.send(f"❌ Lỗi phát âm thanh: Lỗi chi tiết: {e}")
    finally:
        # Dọn dẹp file tạm
        if mp3_filepath and os.path.exists(mp3_filepath):
            os.remove(mp3_filepath)

# --- SỰ KIỆN CHÀO MỪNG & TẠM BIỆT (6 PHONG CÁCH) ---

@bot.event
async def on_member_join(member):
    """Chào mừng thành viên với 6 phong cách ngẫu nhiên."""
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        message_template = random.choice(WELCOME_MESSAGES)
        
        try:
             get_balance(member.id) 
             update_balance(member.id, 100) 
        except:
             pass 
             
        final_message = message_template.format(name=member.mention)
        await channel.send(final_message)

@bot.event
async def on_member_remove(member):
    """Tạm biệt thành viên với 6 phong cách ngẫu nhiên."""
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        message_template = random.choice(GOODBYE_MESSAGES)
        final_message = message_template.format(name=member.display_name)
        await channel.send(final_message)


# --- CÁC LỆNH KHÁC (Đã Tối Ưu) ---

@commands.cooldown(1, 86400, commands.BucketType.user) 
async def daily_command(ctx):
    user_id = ctx.author.id
    DAILY_REWARD = 500
    item = random_roll_weapon()
    add_item_to_inventory(user_id, item)
    update_balance(user_id, DAILY_REWARD)
    await ctx.send(f"🎁 **{ctx.author.display_name}** hoàn thành **Nhiệm Vụ Ngày**! Nhận **{DAILY_REWARD}** xu và 1 Hòm Gacha Vũ khí: **{item['name']}**!")
    await balance_command(ctx)

@daily_command.error
async def daily_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        remaining_seconds = int(error.retry_after)
        hours = remaining_seconds // 3600
        minutes = (remaining_seconds % 3600) // 60
        seconds = remaining_seconds % 60
        await ctx.send(f"⏰ **{ctx.author.display_name}** ơi, Nhiệm Vụ Ngày sẽ tái tạo sau **{hours} giờ, {minutes} phút, {seconds} giây** nữa.")

@commands.cooldown(1, 60, commands.BucketType.user) 
async def hunt_command(ctx):
    user_id = ctx.author.id
    if random.random() < 0.30: 
        today = datetime.now() 
        rarity = random_roll_rarity()
        is_hidden = False
        if today.month == HIDDEN_PET_DATE[0] and today.day == HIDDEN_PET_DATE[1] and random.random() < 0.01:
            pet_name = HIDDEN_PET_NAME
            rarity = HIDDEN_PET_RARITY
            is_hidden = True
            message = f"🌟🌟 **Kỳ Tích!** Bạn đã tìm thấy {pet_name} - Pet **{rarity}** cực phẩm!"
        else:
            pet_name = random.choice(PET_NAMES)
            message = f"🎉 **Chúc mừng!** Bạn đã bắt được Pet: **{pet_name}** ({rarity})!"
        pet_skill = random.choice(SKILLS)
        c.execute('INSERT INTO user_pets (user_id, pet_name, rarity, pet_skill, is_hidden) VALUES (?, ?, ?, ?, ?)',
                  (user_id, pet_name, rarity, pet_skill, is_hidden))
        conn.commit()
        await ctx.send(f"{message}\nKỹ năng Pet: **{pet_skill}**")
    else:
        update_balance(user_id, 50)
        await ctx.send("💔 Bạn đi săn nhưng không thấy Pet nào. Nhận **50** xu an ủi.")
    await balance_command(ctx)

@hunt_command.error
async def hunt_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏰ **{ctx.author.display_name}** ơi, bạn phải chờ **{int(error.retry_after)}** giây nữa mới có thể đi săn tiếp.")

async def bgive_money(ctx, member: discord.Member, amount: int):
    user_id = ctx.author.id; sender_balance = get_balance(user_id)
    if member.id == user_id or amount <= 0 or sender_balance < amount:
        if member.id == user_id: await ctx.send("❌ Bạn không thể tự chuyển tiền cho chính mình.")
        elif amount <= 0: await ctx.send("❌ Số tiền chuyển phải lớn hơn 0.")
        else: await ctx.send(f"❌ Bạn không đủ **{amount}** xu. Số dư hiện tại của bạn là: **{sender_balance}** xu.")
        return
    update_balance(user_id, -amount); update_balance(member.id, amount)
    await ctx.send(f"✅ **{ctx.author.display_name}** đã chuyển **{amount}** xu cho **{member.display_name}** thành công!")
    await balance_command(ctx) 

@bot.command(name="balance", aliases=["bal", "tien"])
async def balance_command(ctx, member: discord.Member = None):
    member = member or ctx.author; balance = get_balance(member.id)
    await ctx.send(f"💰 Số dư hiện tại của **{member.display_name}** là: **{balance}** xu.")

@bot.command(name="admingive")
@commands.has_permissions(administrator=True) 
async def admin_give_money(ctx, member: discord.Member, amount: int):
    if amount <= 0: await ctx.send("Số tiền phải lớn hơn 0."); return
    update_balance(member.id, amount)
    await ctx.send(f"✅ Đã chuyển **{amount}** xu cho **{member.display_name}**.")
    await balance_command(ctx, member=member)

@bot.command(name="ping", aliases=["lat"])
async def ping_command(ctx):
    latency = round(ctx.bot.latency * 1000)
    await ctx.send(f"🏓 Pong! Độ trễ hiện tại là: **{latency}ms**")

@bot.command(name="gacha", aliases=["mohòm"])
async def open_gacha_box(ctx):
    COST = 500; user_id = ctx.author.id
    if get_balance(user_id) < COST: await ctx.send(f"❌ Bạn cần **{COST}** xu để mở hòm Gacha vũ khí."); return
    update_balance(user_id, -COST); item = random_roll_weapon(); add_item_to_inventory(user_id, item)
    await ctx.send(f"📦 **{ctx.author.display_name}** mở hòm và nhận được: **{item['name']}**!\n"
                   f"✨ Phẩm chất: **{item['rarity']}**\n"
                   f"🎨 Tỷ lệ Skin: **{item['skin_percent']}%**\n"
                   f"🗡️ Kỹ năng Chính: **{item['skill_main']}**\n"
                   f"🔮 4 Kỹ năng Phụ: {item['skill_sub1']}, {item['skill_sub2']}, {item['skill_sub3']}, {item['skill_sub4']}")
    await balance_command(ctx)

@bot.command(name="gioithieu", aliases=["gtvk"])
async def introduce_weapon(ctx):
    embed = discord.Embed(title="⚔️ Hệ Thống Vũ Khí, Pet & Kỹ Năng", description="Thông tin chi tiết về cấp bậc và hệ thống kỹ năng:", color=discord.Color.gold())
    rarity_list = "\n".join([f"**{name}**: Tỷ lệ {prob}%" for name, prob in RARITY_CONFIG.items()])
    skill_preview = ", ".join(SKILLS[:10]) + ", ..."
    embed.add_field(name="✨ Cấp Bậc Phẩm Chất (Rarity)", value=rarity_list, inline=False)
    embed.add_field(name="🗡️ Tổng Số Vũ Khí", value=f"Hiện có **{len(WEAPON_TYPES)}** loại vũ khí.\n\n**Vũ khí được gán 1 Kỹ năng Chính và 4 Kỹ năng Phụ.**", inline=True)
    embed.add_field(name="🐾 Tổng Số Pet", value=f"Hiện có **{len(PET_NAMES)}** loại Pet.\n\n**Pet được gán 1 Kỹ năng riêng biệt.**", inline=True)
    embed.set_footer(text=f"Mô phỏng 50+ Kỹ năng (Ví dụ: {skill_preview})")
    await ctx.send(embed=embed)

async def handle_game_wager(ctx, game_name, wager_amount, is_win, win_multiplier=2):
    user_id = ctx.author.id; current_balance = get_balance(user_id)
    if wager_amount <= 0: await ctx.send(f"❌ Số tiền cược cho {game_name} phải lớn hơn 0."); return None, None
    if current_balance < wager_amount: await ctx.send(f"❌ Bạn không đủ tiền cược **{wager_amount}** xu. Số dư hiện tại: **{current_balance}** xu."); return None, None
    if is_win: win_amount = wager_amount * win_multiplier - wager_amount; update_balance(user_id, win_amount); return True, win_amount
    else: update_balance(user_id, -wager_amount); return False, wager_amount
    return None, None

async def bcf_game(ctx, choice, wager):
    result = random.choice(["heads", "tails"]); is_win = choice.lower().strip() == result
    game_outcome, amount = await handle_game_wager(ctx, "Tung Xu (BCF)", wager, is_win)
    if game_outcome is not None:
        emoji = "🥇" if game_outcome else "💔"; win_loss_text = "THẮNG" if game_outcome else "THUA"; sign = "+" if game_outcome else "-"
        await ctx.send(f"{emoji} **Tung Xu (BCF)**: Bot chọn **{result.upper()}**! Bạn **{win_loss_text}** {sign}**{amount}** xu.")
        await balance_command(ctx)

async def bbj_game(ctx, wager):
    player_hand = random.randint(14, 21); dealer_hand = random.randint(14, 21); is_win = None
    if player_hand > 21: is_win = False
    elif dealer_hand > 21: is_win = True
    elif player_hand == dealer_hand: pass
    elif player_hand > dealer_hand: is_win = True
    else: is_win = False
    message = f"Của bạn: {player_hand}, Của Bot: {dealer_hand}. "
    if is_win is False: message += "Bạn **THUA**."
    elif is_win is True: message += "Bạn **THẮNG**."
    else: message += "Kết quả **HÒA**, tiền cược được hoàn lại."
    if is_win is None: await ctx.send(f"♣️ **Blackjack (BBJ)**: {message}"); return
    game_outcome, amount = await handle_game_wager(ctx, "Blackjack (BBJ)", wager, is_win, win_multiplier=1.5)
    if game_outcome is not None:
        emoji = "👑" if game_outcome else "⚔️"; sign = "+" if game_outcome else "-"
        await ctx.send(f"{emoji} **Blackjack (BBJ)**: {message} Bạn {sign}**{amount}** xu.")
        await balance_command(ctx)

@bot.event
async def on_message(message):
    if message.author == bot.user: return
    content = message.content.strip(); content_lower = content.lower()
    ctx = await bot.get_context(message)
    
    if not ctx.valid: 
        parts = content.split()
        if content_lower == "bdaily": await daily_command(ctx); return
        if content_lower == "bhunt": await hunt_command(ctx); return
        if content_lower.startswith("bs "):
            broadcast_text = content[3:].strip()
            if broadcast_text:
                try: await message.delete() 
                except discord.Forbidden: pass
                await message.channel.send(f"📣 **Thông báo từ {message.author.display_name}:** {broadcast_text}")
            return 
        if content_lower.startswith("bgive ") and len(parts) == 3:
            try:
                member_id = message.mentions[0].id; member = message.guild.get_member(member_id); amount = int(parts[2])
                await bgive_money(ctx, member, amount)
            except (IndexError, ValueError): await message.channel.send("❌ Cú pháp `bgive` không hợp lệ. Dùng: `bgive @tên_người <số tiền>`")
            return
        if content_lower.startswith("bcf ") and len(parts) == 3:
            try:
                choice = parts[1].lower(); wager = int(parts[2])
                if choice not in ["heads", "tails"]: await message.channel.send("❌ Cú pháp `bcf` không hợp lệ. Chọn `heads` hoặc `tails`."); return
                await bcf_game(ctx, choice, wager)
            except ValueError: await message.channel.send("❌ Số tiền cược không hợp lệ.")
            return
        if content_lower.startswith("bbj ") and len(parts) == 2:
            try:
                wager = int(parts[1])
                await bbj_game(ctx, wager)
            except ValueError: await message.channel.send("❌ Số tiền cược không hợp lệ.")
            return

    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f'✅ Bot đã online và đăng nhập với tên: {bot.user}')

# --- THIẾT LẬP KEEP-ALIVE BẰNG FLASK (Cho 24/7) ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot đang chạy ổn định 24/7 trên Railway."
def run():
  port = int(os.environ.get("PORT", 5000))
  app.run(host='0.0.0.0', port=port)
def keep_alive():
    t = Thread(target=run); t.start()
if __name__ == '__main__':
    keep_alive(); bot.run(TOKEN)
