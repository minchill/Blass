import discord
from discord.ext import commands
import os
import sqlite3
import random
from flask import Flask
from threading import Thread

# --- CẤU HÌNH BOT VÀ DATABASE ---

# Lấy Token từ Biến Môi trường (Environment Variables) của Railway/GitHub
# Đảm bảo bạn đã lưu Token Bot với tên biến là 'DISCORD_TOKEN'
TOKEN = os.getenv('DISCORD_TOKEN') 

# ID kênh bạn muốn bot gửi tin nhắn chào mừng
# <<< BẮT BUỘC THAY BẰNG ID KÊNH THỰC TẾ CỦA SERVER BẠN >>>
WELCOME_CHANNEL_ID = 123456789012345678 

# Cấu hình Discord Bot
intents = discord.Intents.default()
# Cần bật các Intents này trên Discord Developer Portal
intents.members = True 
intents.message_content = True 

bot = commands.Bot(command_prefix='!', intents=intents)

# --- DATABASE SETUP (Sử dụng SQLite) ---

# Tên file database để lưu trữ tiền
DB_NAME = 'economy.db'
conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

# Tạo bảng người dùng nếu chưa tồn tại
c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        balance INTEGER DEFAULT 0
    )
''')
conn.commit()

# Hàm lấy số dư của người dùng
def get_balance(user_id):
    c.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    if result:
        return result[0]
    # Nếu chưa có trong DB, thêm người dùng mới với số dư 0
    c.execute('INSERT INTO users (user_id, balance) VALUES (?, ?)', (user_id, 0))
    conn.commit()
    return 0

# Hàm thêm/trừ tiền của người dùng
def update_balance(user_id, amount):
    balance = get_balance(user_id)
    new_balance = balance + amount
    c.execute('UPDATE users SET balance = ? WHERE user_id = ?', (new_balance, user_id))
    conn.commit()
    return new_balance

# --- SỰ KIỆN BOT ---

@bot.event
async def on_ready():
    print(f'✅ Bot đã online và đăng nhập với tên: {bot.user}')
    # In ra URL để biết địa chỉ Flask đang chạy (dùng cho UptimeRobot nếu cần)
    print(f"Flask Webserver Running on port: {os.getenv('PORT')}") 

@bot.event
async def on_member_join(member):
    """Tự động chào 'member' khi vào room, vào server"""
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        # Tặng 100 xu khởi nghiệp
        update_balance(member.id, 100) 
        await channel.send(f"🎉 Chào mừng **{member.mention}** đã gia nhập máy chủ! Chúc bạn có những phút giây vui vẻ. Bạn được tặng **100** xu khởi nghiệp!")
    else:
        print(f"LỖI: Không tìm thấy kênh có ID: {WELCOME_CHANNEL_ID}")


# --- LỆNH BOT: Lệnh BS (Đọc tin nhắn trong chat) ---

@bot.command(name="bs")
async def broadcast_message(ctx, *, message: str):
    """Đọc tin nhắn trong chat = LỆNH \"bs+ tin nhắn\" (Dùng !bs <tin nhắn>)"""
    # Xóa tin nhắn lệnh nếu bot có quyền
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass 
        
    await ctx.send(f"📣 **Thông báo từ {ctx.author.display_name}:** {message}")

# --- LỆNH BOT: HỆ THỐNG TIỀN TỆ ---

@bot.command(name="balance", aliases=["bal", "tien"])
async def balance_command(ctx, member: discord.Member = None):
    """Kiểm tra số tiền."""
    member = member or ctx.author
    balance = get_balance(member.id)
    await ctx.send(f"💰 Số dư hiện tại của **{member.display_name}** là: **{balance}** xu.")

@bot.command(name="give")
@commands.has_permissions(administrator=True) # Lệnh dành cho Admin
async def give_money(ctx, member: discord.Member, amount: int):
    """Lệnh !give @user <số tiền> (Chỉ Admin)"""
    if amount <= 0:
        await ctx.send("Số tiền phải lớn hơn 0.")
        return
    
    update_balance(member.id, amount)
    await ctx.send(f"✅ Đã chuyển **{amount}** xu cho **{member.display_name}**. Số dư mới: **{get_balance(member.id)}** xu.")

# --- LỆNH BOT: TẠO TRÒ CHƠI (Giống owo) ---

@bot.command(name="hunt", aliases=["h"])
@commands.cooldown(1, 60, commands.BucketType.user) # Cooldown 60 giây
async def hunt_command(ctx):
    """Trò chơi tìm kiếm và kiếm tiền (Cooldown 60s)."""
    user_id = ctx.author.id
    
    # Các tình huống khi săn (Tỷ lệ %, Số tiền)
    outcomes = {
        "thành công": (50, 200),  
        "bình thường": (30, 100), 
        "thất bại": (20, 0)       
    }
    
    choice = random.choices(
        list(outcomes.keys()), 
        weights=[outcomes[k][0] for k in outcomes]
    )[0]
    
    if choice == "thành công":
        amount = outcomes[choice][1]
        update_balance(user_id, amount)
        await ctx.send(f"🌟 **{ctx.author.display_name}** đi săn thành công! Bạn bắt được một con thú hiếm và kiếm được **{amount}** xu.")
    elif choice == "bình thường":
        amount = outcomes[choice][1]
        update_balance(user_id, amount)
        await ctx.send(f"🌲 **{ctx.author.display_name}** đi săn và tìm được **{amount}** xu.")
    else:
        await ctx.send(f"💔 **{ctx.author.display_name}** đi săn nhưng không tìm thấy gì cả. Thử lại sau nhé!")

    # Hiển thị số dư mới
    await balance_command(ctx)

@hunt_command.error
async def hunt_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏰ **{ctx.author.display_name}** ơi, bạn phải chờ **{int(error.retry_after)}** giây nữa mới có thể đi săn tiếp.")

# --- THIẾT LẬP KEEP-ALIVE BẰNG FLASK (Rất quan trọng cho Hosting) ---

# Flask sẽ tạo ra một máy chủ web nhỏ mà Railway (hoặc UptimeRobot) sẽ ping
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot đang chạy ổn định 24/7 trên Railway."

def run():
  # Railway sẽ tự động cung cấp một cổng (port)
  port = int(os.environ.get("PORT", 5000))
  app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- KHỞI ĐỘNG BOT VÀ KEEP-ALIVE ---

if __name__ == '__main__':
    keep_alive() # Khởi động máy chủ web Flask
    bot.run(TOKEN) # Khởi động bot Discord

