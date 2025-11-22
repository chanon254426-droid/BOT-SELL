import os 
import discord
from discord.ext import commands
from discord import app_commands
import random 
import time
from myserver import server_on

# =================================================================
# 🛠️ --- CONFIGURATION: ส่วนตั้งค่าที่ต้องแก้ไข/ใส่ค่า ID และลิงก์ --- 🛠️
# * กรุณาตรวจสอบ ID ทั้ง 3 ตัว และลิงก์ QR Code อีกครั้ง *
# =================================================================

# 🔑 Bot Token
DISCORD_BOT_TOKEN = 'DISCORD_BOT_TOKEN' 

# 🛒 Channel IDs
SHOP_CHANNEL_ID = 1416797606180552714      # แชนเนลที่ใช้แสดงเมนูร้านค้า
SLIP_SUBMIT_CHANNEL_ID = 1416797464350167090 # แชนเนลที่ลูกค้าส่งสลิป
ADMIN_LOG_CHANNEL_ID = 1437395517545123860 # แชนเนล Log สำหรับแอดมินเท่านั้น

# 📣 ข้อมูลยศทั้งหมดที่คุณต้องการขาย (SALE_ITEMS)
SALE_ITEMS = [
    {
        "role_id": 1419373724653588540,
        "name": "SETTING PREMIUM", 
        "price": "169 บาท", 
        "qr_url": 'https://ik.imagekit.io/ex9p4t2gi/IMG_6124.jpg'
    },
    {
        "role_id": 1432064283767738571,
        "name": "ᴍᴏᴅ ᴅᴇᴠᴏᴜʀ 👻", 
        "price": "120 บาท", 
        "qr_url": 'https://ik.imagekit.io/ex9p4t2gi/IMG_6124.jpg'
    },
    {
        "role_id": 1431279741440364625,
        "name": "𝙳𝙾𝙽𝙰𝚃𝙴⭐", 
        "price": "89 บาท", 
        "qr_url": 'https://ik.imagekit.io/ex9p4t2gi/IMG_6124.jpg'
    },
    {
        "role_id": 1431204938373140513,
        "name": "𝚁𝚎𝚊𝚕𝚕𝚒𝚟𝚎✿", 
        "price": "25 บาท", 
        "qr_url": 'https://ik.imagekit.io/ex9p4t2gi/IMG_6124.jpg'
    },
    {
        "role_id": 1431278653760737340,
        "name": "𝚜𝚞𝚗𝚔𝚒𝚜𝚜𝚎𝚍🎧", 
        "price": "25 บาท", 
        "qr_url": 'https://ik.imagekit.io/ex9p4t2gi/IMG_6124.jpg'
    },
    {
        "role_id": 1431231640058990652,
        "name": "𝚖𝚊𝚐𝚒𝚌𝚎𝚢𝚎🌃", 
        "price": "25 บาท", 
        "qr_url": 'https://ik.imagekit.io/ex9p4t2gi/IMG_6124.jpg' 
    },
    {
        "role_id": 1431250097135419505,
        "name": "𝚛𝚎𝚊𝚕𝚒𝚜𝚝𝚒𝚌𝚅𝟷💎", 
        "price": "25 บาท", 
        "qr_url": 'https://ik.imagekit.io/ex9p4t2gi/IMG_6124.jpg'
    },
    {
        "role_id": 1431234346202959973,
        "name": "𝚛𝚎𝚊𝚕𝚒𝚜𝚝𝚒𝚌𝚅𝟸🌈", 
        "price": "25 บาท", 
        "qr_url": 'https://ik.imagekit.io/ex9p4t2gi/IMG_6124.jpg'
    },
    {
        "role_id": 1431249584054734929,
        "name": "𝚛𝚎𝚊𝚕𝚒𝚜𝚝𝚒𝚌𝚅𝟹🔥", 
        "price": "25 บาท", 
        "qr_url": 'https://ik.imagekit.io/ex9p4t2gi/IMG_6124.jpg'
    },
    {
        "role_id": 1432010188340199504,
        "name": "𝙱𝙾𝙾𝚂𝚃𝙵𝙿𝚂🎮", 
        "price": "99 บาท", 
        "qr_url": 'https://ik.imagekit.io/ex9p4t2gi/IMG_6124.jpg'
    },
]

# ----------------- GLOBAL STATE (Order Tracking) -----------------
# ตัวแปรนี้จะเก็บข้อมูล Order ชั่วคราว: {user_id: {"role_id": int, "order_id": str, "timestamp": float}}
USER_ORDERS = {} 
ORDER_COUNTER = 0 # ตัวนับ Order

# =================================================================
# ⚙️ --- CORE BOT SETUP --- ⚙️
# =================================================================

intents = discord.Intents.default()
intents.members = True 
intents.message_content = True 
bot = commands.Bot(command_prefix='!', intents=intents)

# ----------------- View สำหรับการอนุมัติของแอดมิน (Admin Approval View) -----------------

class ApprovalView(discord.ui.View):
    """View ที่มีปุ่ม 'ยืนยัน' และ 'ปฏิเสธ' สำหรับแอดมินเพื่อจัดการสลิป"""
    def __init__(self, user_id: int, role_id: int, original_message: discord.Message, order_id: str):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.role_id = role_id
        self.original_message = original_message
        self.order_id = order_id
        self.item_info = next((item for item in SALE_ITEMS if item["role_id"] == role_id), None)
        self.role_name = self.item_info['name'] if self.item_info else f"Role ID: {role_id}"

    async def on_timeout(self):
        # ล้าง Order ออกเมื่อหมดเวลา
        if self.user_id in USER_ORDERS and USER_ORDERS[self.user_id]['order_id'] == self.order_id:
            del USER_ORDERS[self.user_id]
        
        try:
            await self.original_message.edit(
                content=f"⚠️ หมดเวลาอนุมัติสำหรับ Order **{self.order_id}** (<@{self.user_id}>) แล้ว", 
                view=None
            )
        except:
            pass
            
    async def send_user_feedback(self, member: discord.Member, is_approved: bool):
        """ส่งข้อความแจ้งเตือนกลับไปยังแชนเนลส่งสลิป"""
        slip_channel = bot.get_channel(SLIP_SUBMIT_CHANNEL_ID)
        if not slip_channel:
            return
            
        role_mention = f"<@&{self.role_id}>"
        if is_approved:
            await slip_channel.send(f"✅ <@{member.id}>: **Order {self.order_id}** ได้รับการยืนยันแล้ว! ยศ {role_mention} ถูกมอบให้แล้ว", delete_after=30)
        else:
            await slip_channel.send(f"❌ <@{member.id}>: **Order {self.order_id}** ถูกปฏิเสธ! สลิปไม่ถูกต้อง/ไม่ชัดเจน กรุณาตรวจสอบและส่งใหม่", delete_after=30)

    @discord.ui.button(label="✅ อนุมัติ", style=discord.ButtonStyle.success, custom_id="approve_button")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("คุณไม่มีสิทธิ์ในการอนุมัติ!", ephemeral=True)
            return

        guild = interaction.guild
        member = guild.get_member(self.user_id)
        role = guild.get_role(self.role_id)

        # ล้าง Order ออกจากระบบทันทีที่อนุมัติ
        if self.user_id in USER_ORDERS and USER_ORDERS[self.user_id]['order_id'] == self.order_id:
            del USER_ORDERS[self.user_id]

        if member and role:
            try:
                await member.add_roles(role)
                await interaction.response.edit_message(
                    content=f"✅ **อนุมัติโดย {interaction.user.display_name}** | มอบยศ **{self.role_name}** (<@&{self.role_id}>) ให้กับ <@{self.user_id}> (Order **{self.order_id}**) แล้ว", 
                    view=None
                )
                await self.send_user_feedback(member, True)
            except discord.Forbidden:
                await interaction.response.send_message("❌ บอทไม่มีสิทธิ์ในการมอบยศ! กรุณาตรวจสอบ Permission", ephemeral=True)
                
        else:
            await interaction.response.edit_message(
                content=f"❌ เกิดข้อผิดพลาด: ไม่พบสมาชิก (<@{self.user_id}>) หรือยศ (<@&{self.role_id}>) | Order **{self.order_id}**", 
                view=None
            )

    @discord.ui.button(label="❌ ปฏิเสธ", style=discord.ButtonStyle.danger, custom_id="reject_button")
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("คุณไม่มีสิทธิ์ในการดำเนินการ!", ephemeral=True)
            return
        
        member = interaction.guild.get_member(self.user_id)
        
        # ล้าง Order ออกจากระบบ
        if self.user_id in USER_ORDERS and USER_ORDERS[self.user_id]['order_id'] == self.order_id:
            del USER_ORDERS[self.user_id]
        
        await interaction.response.edit_message(
            content=f"❌ **ปฏิเสธโดย {interaction.user.display_name}** | ปฏิเสธการให้ยศ **{self.role_name}** กับ <@{self.user_id}> (Order **{self.order_id}**)",
            view=None
        )
        await self.send_user_feedback(member, False)
        
# ----------------- View สำหรับการซื้อของลูกค้า (Customer Shop View: ใช้ Dropdown) -----------------

class RoleSelect(discord.ui.Select):
    """Dropdown Menu สำหรับให้ลูกค้าเลือกยศที่ต้องการ"""
    def __init__(self, items: list):
        options = []
        item_emojis = ["👑", "👻", "⭐", "🌷", "🎧", "🌃", "💎", "🌈", "🔥", "🎮"]
        
        for i, item in enumerate(items):
            emoji = item_emojis[i % len(item_emojis)]
            options.append(
                discord.SelectOption(
                    label=f"{emoji} {item['name']} | {item['price']}",
                    value=str(item['role_id']), 
                    description=f"ราคา {item['price']}",
                    emoji=emoji
                )
            )
        super().__init__(
            placeholder="🛒 เลือกยศที่คุณต้องการสั่งซื้อ...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="role_select_menu"
        )
        self.sale_items = items

    async def callback(self, interaction: discord.Interaction):
        global ORDER_COUNTER 
        ORDER_COUNTER += 1 # เพิ่ม Order ID
        
        selected_role_id = int(self.values[0])
        item = next(i for i in self.sale_items if i['role_id'] == selected_role_id)
        user_id = interaction.user.id
        
        # สร้าง Order ID ที่ไม่ซ้ำกัน: O-000001 (เพื่อความเป็นมืออาชีพ)
        order_id = f"O-{ORDER_COUNTER:06d}"
        
        # 🎯 บันทึก Order State ของผู้ใช้คนนี้
        USER_ORDERS[user_id] = {
            "role_id": selected_role_id,
            "order_id": order_id,
            "timestamp": time.time(),
            "role_name": item['name']
        }

        # สร้าง Embed สำหรับการชำระเงิน (แสดงใน DM/Ephemeral)
        embed = discord.Embed(
            title=f"🛒 คำสั่งซื้อ #{order_id} : ขั้นตอนการชำระเงิน",
            description=(
                f"**รายการที่สั่งซื้อ:** <@&{item['role_id']}> ({item['name']}) **ราคา {item['price']}**\n\n"
                "1. **ชำระเงิน** ตาม QR Code ด้านล่าง\n"
                f"2. **ส่งสลิป** ในแชนเนล **<#{SLIP_SUBMIT_CHANNEL_ID}>**\n"
                f"3. **⚠️ สำคัญ:** กรุณาพิมพ์ **หมายเลข Order ID** (`{order_id}`) **แนบมากับสลิป** เพื่อให้แอดมินอนุมัติได้ง่ายขึ้น"
            ),
            color=discord.Color.gold()
        )
        embed.set_image(url=item['qr_url']) 
        
        await interaction.response.send_message(
            content=f"✅ **Order {order_id} ถูกสร้างแล้ว!** กรุณาดูรายละเอียดการชำระเงินและส่งสลิปในข้อความนี้ (เห็นแค่คุณคนเดียว)", 
            embed=embed, 
            ephemeral=True
        )

class ShopSelectView(discord.ui.View):
    """View ที่มี Select Menu สำหรับเลือกยศ"""
    def __init__(self, sale_items: list):
        super().__init__(timeout=None)
        self.add_item(RoleSelect(sale_items))

# ----------------- BOT EVENTS & COMMANDS -----------------

@bot.event
async def on_ready():
    print('----------------------------------------------------')
    print('🚀 Discord Bot Online!')
    
    # Sync Slash Commands
    try:
        synced = await bot.tree.sync()
        print(f"[{len(synced)}] Application Command(s) Synced successfully.")
    except Exception as e:
        print(f"Error syncing commands: {e}")
        
    print(f'🤖 Logged in as {bot.user} (ID: {bot.user.id})')
    print('----------------------------------------------------')
    
    # เพิ่ม View ถาวรเพื่อให้ปุ่มทำงานได้แม้บอทรีสตาร์ท (ใช้ ShopSelectView ใหม่)
    bot.add_view(ShopSelectView(SALE_ITEMS)) 

@bot.tree.command(name="setup_shop", description="[ADMIN] แสดงหน้าต่างร้านค้าพร้อมเมนูสำหรับซื้อ")
@app_commands.default_permissions(administrator=True)
async def setup_shop_slash(interaction: discord.Interaction):
    """Slash Command สำหรับแอดมิน เพื่อแสดงหน้าต่างร้านค้า"""
    channel = bot.get_channel(SHOP_CHANNEL_ID)
    if not channel:
        await interaction.response.send_message(f"❌ ไม่พบแชนเนลร้านค้า ID: {SHOP_CHANNEL_ID}", ephemeral=True)
        return
        
    description_lines = []
    item_emojis = ["👑", "👻", "⭐", "🌷", "🎧", "🌃", "💎", "🌈", "🔥", "🎮"]
    
    for i, item in enumerate(SALE_ITEMS):
        emoji = item_emojis[i % len(item_emojis)]
        description_lines.append(f"\n{emoji} **{item['name']}** (<@&{item['role_id']}>)\n> ราคา **{item['price']}**")

    embed = discord.Embed(
        title="🛒 ร้านค้าจำหน่ายยศ Premium",
        description='**เลือกยศที่คุณต้องการสั่งซื้อจากเมนูด้านล่าง**:\n' + '\n'.join(description_lines),
        color=discord.Color.blue()
    )
    
    await channel.send(embed=embed, view=ShopSelectView(SALE_ITEMS))
    await interaction.response.send_message("✅ ตั้งค่าร้านค้าเสร็จสมบูรณ์! กรุณาตรวจสอบ Channel", ephemeral=True)


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
        
    await bot.process_commands(message)
    
    # ตรวจสอบว่าเป็นข้อความที่ส่งในแชนเนลส่งสลิปและมีไฟล์แนบหรือไม่
    if message.channel.id == SLIP_SUBMIT_CHANNEL_ID and message.attachments:
        
        user_id = message.author.id
        log_channel = bot.get_channel(ADMIN_LOG_CHANNEL_ID) 
        
        # 1. 🎯 ตรวจสอบ Order State
        if user_id in USER_ORDERS:
            user_order = USER_ORDERS[user_id]
            role_id = user_order['role_id']
            order_id = user_order['order_id']
            item_info = next(item for item in SALE_ITEMS if item["role_id"] == role_id)
            role_name = item_info['name']
            
            status_text = f"✅ **Order State Found:** ลูกค้าเลือกซื้อยศ **{role_name}** (Order **{order_id}**)"
        else:
            # ❌ ไม่พบ Order State: ใช้ Default และ Order ID ชั่วคราว
            default_item = SALE_ITEMS[0] 
            role_id = default_item['role_id']
            role_name = default_item['name']
            order_id = "N/A"
            status_text = f"❌ **Order State Not Found:** บอทไม่พบ Order ID ที่บันทึกไว้สำหรับ <@{user_id}>\n> **ยศที่ถูกเสนอ (Default):** <@&{role_id}> | **โปรดตรวจสอบข้อความสลิปด้วยตนเอง**"


        if not log_channel:
            print(f"⚠️ ADMIN_LOG_CHANNEL_ID ({ADMIN_LOG_CHANNEL_ID}) ไม่ถูกต้อง/ไม่พบ")
            return
            
        # สร้าง Embed สำหรับแอดมิน
        log_embed = discord.Embed(
            title=f"🚨 สลิปใหม่รออนุมัติ! (Order: {order_id})",
            description=(
                f"**ผู้ซื้อ:** {message.author.mention} (`{message.author.id}`)\n"
                f"**ข้อความผู้ใช้:** `{message.content or 'ไม่มีข้อความ'}`\n\n"
                f"{status_text}\n"
                f"**ลิงก์สลิปต้นทาง:** {message.jump_url}"
            ),
            color=discord.Color.red()
        )
        log_embed.set_image(url=message.attachments[0].url) 
        log_embed.set_footer(text=f"อนุมัติ: RoleID {role_id} สำหรับ Order {order_id}")
        
        # 2. 🎯 ส่ง Log พร้อม Role ID ที่ถูกต้อง
        log_message = await log_channel.send(
            content=f"**สลิปใหม่จาก:** {message.author.mention}", 
            embed=log_embed, 
            # ส่ง Order ID และ Role ID ที่ถูกบันทึกไว้ไปยัง ApprovalView
            view=ApprovalView(user_id, role_id, message, order_id) 
        )
        
        # 3. แจ้งเตือนผู้ใช้
        await message.channel.send(
            f"🤖 <@{user_id}>: ได้รับสลิปของคุณแล้ว! Order **{order_id}** กำลังรอตรวจสอบ กรุณารอแอดมินสักครู่", 
            delete_after=10
        )
        
# 🚀 รันบอท
try:
    server_on()
    bot.run(os.getenv('TOKEN')) 
except Exception as e:
    print(f"❌ เกิดข้อผิดพลาดในการรันบอท: {e}")
    print("กรุณาตรวจสอบ Token และสิทธิ์ 'Privileged Gateway Intents' ใน Discord Developer Portal")