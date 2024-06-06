import discord
import os
from discord.ext import commands
from keep_alive import keep_alive
from collections import defaultdict
import asyncio
from datetime import datetime, timedelta
import re

# Bot token is in .env
TOKEN = os.getenv('TOKEN')
if not TOKEN:
    raise ValueError("Token not found. Ensure that the environment variable 'TOKEN' is set.")

# Keeps the bot online 24/7
keep_alive()

# Bot prefix and required intents (Administrator)
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)
bot.remove_command('help')

# Owner ID
OWNER_ID = 706855632333963367  # Replace this with your own user ID

# Almacena las invitaciones actuales
invitations = {}

async def update_invitations():
    for guild in bot.guilds:
        try:
            invitations[guild.id] = await guild.invites()
        except Exception as e:
            print(f"Error al actualizar invitaciones para {guild.name}: {e}")

    @bot.event
    async def on_ready():
        await update_invitations()
        activity = discord.Activity(type=discord.ActivityType.watching, name="👑 Created by edu__579 👑 y 𝐏𝐇𝐈𝐁𝐁𝐘")
        await bot.change_presence(status=discord.Status.dnd, activity=activity)
        print("El status del bot está activo..")

@bot.command()
async def invites(ctx):
    try:
        # Obtener todas las invitaciones del servidor
        invites = await ctx.guild.invites()

        # Crear un diccionario para mapear usuarios a la cantidad de invitaciones
        user_invites = defaultdict(int)

        # Contar la cantidad de invitaciones por usuario
        for invite in invites:
            user_invites[invite.inviter] += invite.uses

        # Verificar cuántas personas se unieron gracias al usuario que invoca el comando
        user = ctx.author
        invites_from_user = user_invites[user]

        await ctx.send(f"¡Has invitado a {invites_from_user} personas al servidor!")
    except Exception as e:
        await ctx.send(f"Ocurrió un error al obtener las invitaciones: {e}")

# Anti-spam and link removal setup
message_logs = defaultdict(list)
SPAM_THRESHOLD = 5  # Number of messages considered as spam
SPAM_TIMEFRAME = 10  # Time frame in seconds to check for spam
MUTE_DURATION = 60  # Duration to mute in seconds

anti_raid_enabled = False  # Variable to control anti-raid/spam/links mode

async def mute_user(guild, user, reason):
    try:
        role = discord.utils.get(guild.roles, name="Muted")
        if not role:
            role = await guild.create_role(name="Muted")
            for channel in guild.channels:
                await channel.set_permissions(role, send_messages=False, speak=False)

        await user.add_roles(role)
        await user.send(f"{user.mention}, has sido silenciado por {reason}.")
        await asyncio.sleep(MUTE_DURATION)
        await user.remove_roles(role)
        await user.send(f"{user.mention}, has sido des-silenciado.")
    except discord.Forbidden:
        print(f"No se pudo silenciar a {user} debido a permisos insuficientes.")
    except Exception as e:
        print(f"Error al silenciar a {user}: {e}")

async def notify_owner(user_id, action, details):
    try:
        owner = await bot.fetch_user(OWNER_ID)
        if owner:
            await owner.send(f'Usuario {user_id} intentó {action}. Detalles: {details}')
    except Exception as e:
        print(f"No se pudo notificar al propietario: {e}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    try:
        # Detect and delete messages containing links and mute the user if anti-raid is enabled
        url_regex = re.compile(r'https?://\S+|www\.\S+')
        if (url_regex.search(message.content)):
            if anti_raid_enabled:
                await message.delete()
                await mute_user(message.guild, message.author, "enviar enlaces no permitidos")
                await notify_owner(message.author.id, "enviar enlaces no permitidos", message.content)
            return

        now = datetime.now()
        message_logs[message.author.id].append((now, message))

        # Remove messages that are outside the spam timeframe
        message_logs[message.author.id] = [(msg_time, msg) for msg_time, msg in message_logs[message.author.id] if now - msg_time < timedelta(seconds=SPAM_TIMEFRAME)]

        # Check for spam
        if len(message_logs[message.author.id]) > SPAM_THRESHOLD:
            if anti_raid_enabled:
                await mute_user(message.guild, message.author, "spam")
                await notify_owner(message.author.id, "spam", f"Envió más de {SPAM_THRESHOLD} mensajes en {SPAM_TIMEFRAME} segundos")

                # Delete recent messages within the timeframe
                for msg_time, msg in message_logs[message.author.id]:
                    await msg.delete()

                message_logs[message.author.id] = []
    except Exception as e:
        print(f"Error en el manejo de mensaje: {e}")

    await bot.process_commands(message)

# Detect and expel unverified bots
@bot.event
async def on_member_join(member):
    if (member.bot):
        if anti_raid_enabled:  # Solo expulsa bots si el modo anti-raid está activado
            try:
                await member.kick(reason="Bot no verificado")
                await notify_owner(member.id, "añadir un bot no verificado", f"Bot {member} ha sido expulsado.")
                print(f"Bot no verificado {member} ha sido expulsado.")
            except Exception as e:
                print(f"Error al expulsar bot no verificado: {e}")
    else:
        # Determine who invited the new member
        guild = member.guild
        current_invitations = await guild.invites()
        old_invitations = invitations.get(guild.id, [])
        inviter = None

        for current_invite in current_invitations:
            for old_invite in old_invitations:
                if current_invite.code == old_invite.code:
                    if current_invite.uses > old_invite.uses:
                        inviter = current_invite.inviter
                        break
            if inviter:
                break

        invitations[guild.id] = current_invitations

        # Send a welcome message to a specific channel
        welcome_channel_id = 1246090846387048520  # Replace with your channel ID
        channel = bot.get_channel(welcome_channel_id)
        if inviter:
            if channel:
                await channel.send(f"¡Bienvenido al servidor, {member.mention}! 🎉 Has sido invitado por {inviter.mention}.")
            # Optionally, send a DM to the new member
            try:
                await member.send(f"¡Hola {member.name}! Bienvenido al servidor. Has sido invitado por {inviter.name}. 😊")
            except discord.Forbidden:
                print(f"No se pudo enviar un mensaje directo a {member} has sido invitado por {inviter.name}.")
        else:
            if channel:
                await channel.send(f"¡Bienvenido al servidor, {member.mention}! 🎉")
            try:
                await member.send(f"¡Hola {member.name}! Bienvenido al servidor. 😊")
            except discord.Forbidden:
                print(f"No se pudo enviar un mensaje directo a {member}.")

# !kick command
@bot.command(name='kick')
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    try:
        await member.kick(reason=reason)
        if reason:
            await ctx.send(f"{member} ha sido expulsado por {reason}.")
        else:
            await ctx.send(f"{member} ha sido expulsado.")
        print("El comando de kick ha sido utilizado contra ") 
    except discord.Forbidden:
        await ctx.send(f"No pude expulsar a {member} porque tiene un rol más alto que el mío.")
    except Exception as e:
        await ctx.send(f"Ocurrió un error: {e}")

# !mute command
@bot.command(name='mute')
@commands.has_permissions(manage_roles=True, manage_channels=True)
async def mute(ctx, member: discord.Member, *, reason=None):
    try:
        await mute_user(ctx.guild, member, reason or "comportamiento inapropiado")
        if reason:
            await ctx.send(f"{member} ha sido silenciado por {reason}.")
        else:
            await ctx.send(f"{member} ha sido silenciado.")
        print("El comando de mute está activado.")
    except discord.Forbidden:
        await ctx.send(f"¡UH oh! no pude silenciar a {member}.")
    except Exception as e:
        await ctx.send(f"Ocurrió un error: {e}")

# !ban command
@bot.command(name='ban')
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    try:
        await member.ban(reason=reason)
        if reason:
            await ctx.send(f"{member} ha sido baneado por {reason}.")
        else:
            await ctx.send(f"{member} ha sido baneado.")
        print("El comando de ban está activado.") 
    except discord.Forbidden:
        await ctx.send(f"No pude banear a {member} porque tiene un rol más alto que el mío.")
    except Exception as e:
        await ctx.send(f"Ocurrió un error: {e}")

# !unban command
@bot.command(name='unban')
@commands.has_role('admin')
async def unban(ctx, *, member):
    try:
        banned_users = await ctx.guild.bans()
        member_name, member_discriminator = member.split('#')
        for ban_entry in banned_users:
            user = ban_entry.user
            if (user.name, user.discriminator) == (member_name, member_discriminator):
                await ctx.guild.unban(user)
                await ctx.send(f"{user.mention} ha sido desbaneado.")
                return
        await ctx.send(f"No se encontró un usuario con el nombre y discriminador: {member}")
    except Exception as e:
        await ctx.send(f'Ocurrió un error al desbanear: {e}')

# !unmute command
@bot.command(name='unmute')
@commands.has_role('admin')
async def unmute(ctx, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name="Muted")
    if role in member.roles:
        await member.remove_roles(role)
        await ctx.send(f"{member.mention} ha sido des-silenciado.")
    else:
        await ctx.send(f"{member.mention} no está silenciado.")

# !clear command
@bot.command(name='clear')
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    try:
        if amount < 1:
            await ctx.send("Por favor, especifica una cantidad válida de mensajes para eliminar.")
            return
        deleted = await ctx.channel.purge(limit=amount + 1)  # +1 para incluir el comando clear
        await ctx.send(f'Se han eliminado {len(deleted) - 1} mensajes.', delete_after=5)
    except Exception as e:
        await ctx.send(f'Ocurrió un error al intentar eliminar mensajes: {e}')

# !nuke command
@bot.command(name='nuke')
@commands.has_permissions(administrator=True)
async def nuke(ctx):
    try:
        await ctx.channel.purge()
        await ctx.send(f'Nuke by {ctx.author.mention}')
    except Exception as e:
        await ctx.send(f'Ocurrió un error al intentar limpiar el canal: {e}')

# !cmds command
@bot.command(name='cmds')
async def cmds(ctx):
    try:
        color_code = int('446be5', 16)  # converts the hex code to an integer
        embed = discord.Embed(title='Commands', description='Enumera todos los comandos disponibles', color=color_code)
        embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/1226150520079646760/1243931697976967169/SPOILER_standard.gif?ex=6653452b&is=6651f3ab&hm=575d5c39bb2c16145b60a5b8396b5c580bf3aff4ebf006ec514840ef25bfc683&')

        # Lista de comandos que pueden ser utilizados por miembros normales
        normal_commands = [
            ('!invites', 'Muestra la cantidad de invitaciones que ha generado cada usuario.'),
            ('!dev', 'Consigue un enlace para convertirte de developper de discord.'),
            ('!estado', 'Muestra el estado del servidor: modo anti-raid, total de usuarios, cantidad de bots y cantidad de miembros no bots.')
        ]

        # Agrega los comandos que pueden ser utilizados por miembros normales al embed
        for name, value in normal_commands:
            embed.add_field(name=name, value=value)

        await ctx.send(embed=embed)
    except discord.Forbidden:
        await ctx.send('No tengo permiso para enviar mensajes en este canal.')
    except Exception as e:
        await ctx.send(f'Ha ocurrido un error: {e}')

# !adminc command
@bot.command(name='adminc')
@commands.has_permissions(administrator=True)
async def adminc(ctx):
    try:
        color_code = int('ff0000', 16)  # converts the hex code to an integer
        embed = discord.Embed(title='Admin Commands', description='Enumera todos los comandos de administrador disponibles', color=color_code)
        embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/1226150520079646760/1243931697976967169/SPOILER_standard.gif?ex=6653452b&is=6651f3ab&hm=575d5c39bb2c16145b60a5b8396b5c580bf3aff4ebf006ec514840ef25bfc683&')

        # Lista de comandos de administrador
        admin_commands = [
            ('!ban @user', 'Banea a un usuario específico del servidor'),
            ('!kick @user', 'Expulsa a un usuario específico del servidor'),
            ('!mute @user', 'Silencia a un usuario específico para que no pueda chatear ni hablar en canales de voz.'),
            ('!dev', 'Consigue un enlace para convertirte de developper de discord.'),
            ('!unban @user', 'Desbanea a un usuario específico'),
            ('!unmute @user', 'Des-silencia a un usuario específico'),
            ('!clear [cantidad]', 'Elimina una cantidad especificada de mensajes del canal.'),
            ('!invites', 'Muestra la cantidad de invitaciones que ha generado cada usuario.'),
            ('!nuke', 'Limpia todos los mensajes del canal actual.'),
            ('!estado', 'Muestra el estado del servidor: modo anti-raid, total de usuarios, cantidad de bots y cantidad de miembros no bots.')
        ]

        # Agrega los comandos de administrador al embed
        for name, value in admin_commands:
            embed.add_field(name=name, value=value)

        await ctx.send(embed=embed)
    except discord.Forbidden:
        await ctx.send('No tengo permiso para enviar mensajes en este canal.')
    except Exception as e:
        await ctx.send(f'Ha ocurrido un error: {e}')
# !estado command
@bot.command(name='estado')
async def estado(ctx):
    try:
        total_users = ctx.guild.member_count
        bots = sum(1 for member in ctx.guild.members if member.bot)
        non_bots = total_users - bots
        mode_status = "activado" if anti_raid_enabled else "desactivado"

        embed = discord.Embed(title=f"Estado del servidor: {ctx.guild.name}", color=discord.Color.blue())
        embed.add_field(name="Modo anti-raid", value=mode_status, inline=False)
        embed.add_field(name="Total de usuarios", value=total_users, inline=False)
        embed.add_field(name="Cantidad de bots", value=bots, inline=False)
        embed.add_field(name="Cantidad de miembros (no bots)", value=non_bots, inline=False)

        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f'Ocurrió un error al obtener el estado del servidor: {e}')

# Comando para decir developper
@bot.command(name='dev')
async def dev(ctx):
    await ctx.send('¡Hola! ¡Aquí tienes un link para convertirte en developper de disocrd! https://discord.com/developers/active-developer.')

# Unknown command
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Comando desconocido, usa !cmds para ver todos los comandos disponibles")
    else:
        await ctx.send(f"Ocurrió un error: {error}")

# Anti-channel deletion setup
channel_delete_logs = defaultdict(list)
CHANNEL_DELETE_THRESHOLD = 5  # Number of channels deleted
CHANNEL_DELETE_TIMEFRAME = 5  # Time frame in seconds

@bot.event
async def on_guild_channel_delete(channel):
    if channel.guild.me.guild_permissions.manage_guild:
        now = datetime.now()
        channel_delete_logs[channel.guild.id].append(now)

        # Remove logs outside the timeframe
        channel_delete_logs[channel.guild.id] = [log_time for log_time in channel_delete_logs[channel.guild.id] if now - log_time < timedelta(seconds=CHANNEL_DELETE_TIMEFRAME)]

        if len(channel_delete_logs[channel.guild.id]) >= CHANNEL_DELETE_THRESHOLD:
            async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
                if entry.target.id == channel.id:
                    if entry.user.bot:
                        try:
                            await entry.user.kick(reason="Eliminación masiva de canales")
                            await notify_owner(entry.user.id, "eliminar masivamente canales", f"{entry.user} ha sido expulsado.")

                            # Recreate deleted channels
                            for _ in range(CHANNEL_DELETE_THRESHOLD):
                                new_channel = await channel.guild.create_text_channel(name=channel.name, category=channel.category)
                                await new_channel.send(f"{entry.user} eliminó este canal y ha sido recreado.")

                            channel_delete_logs[channel.guild.id] = []
                            break
                        except Exception as e:
                            print(f"Error al manejar eliminación masiva de canales: {e}")

# Comando !on
@bot.command(name='on')
@commands.has_permissions(administrator=True)
async def enable_anti_raid(ctx):
    global anti_raid_enabled
    anti_raid_enabled = True
    await ctx.send("¡El modo anti-raid ha sido activado. 🛡️!")

# Comando !off
@bot.command(name='off')
@commands.has_permissions(administrator=True)
async def disable_anti_raid(ctx):
    global anti_raid_enabled
    anti_raid_enabled = False
    await ctx.send("¡El modo anti-raid ha sido desactivado. 🚫!")

# Inicia el bot
bot.run(TOKEN)