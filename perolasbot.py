from math import floor
from random import randint
from os import getenv
import discord
from discord.ext import commands
from discord.ext.commands import has_permissions, MissingPermissions
from openai import OpenAI
from db_manager import Database

BOT_KEY, OPENAI_KEY, OWNER_ID = getenv('BOT_KEY'), getenv('OPENAI_API_KEY'), getenv('OWNER_ID')

db = Database('pearls.db')

intents = discord.Intents.all()

client = OpenAI(api_key=OPENAI_KEY)
bot = commands.Bot(command_prefix='a!', intents=intents, activity=discord.Game('/ajuda na sua cara'), owner_id=OWNER_ID)

@bot.event
async def on_ready():
    print(f'Logado como {bot.user.name}.')

@bot.event
async def on_command_error(ctx:commands.Context, error):
    print(error)
    print(error.__traceback__)
    await ctx.reply('Amigo, acho que esse comando não existe.')


@bot.command()
@commands.is_owner()
async def sync(ctx:commands.Context):
    await ctx.send('Initiating Sync...')
    await bot.tree.sync()
    await ctx.send('Sync Sucessfully.')


@bot.tree.command(name='ajuda', description='mostra o menu de ajuda, e seus comandos')
async def slash_command(interactions:discord.Interaction):
    embed = discord.Embed(title='Ajuda', color=discord.Colour.pink(), description='Lista de Comandos e seus usos')
    embed.add_field(name='a!addperola "<conteúdo>"',
                     value="""Use para adicionar uma pérola, sempre deixe o conteúdo entre aspas duplas, se precisar de aspas dentro do conteúdo, utilize aspas simples. 
                     \nExemplo.: a!addperola "Raimundo, o 'Melhor' Rato" """, inline=False)
    embed.add_field(name='a!altperola <número da pérola> "<nova pérola>"', value="""Use para alterar uma pérola já existente, utilize sempre aspas duplas para a nova pérola.
                    Uso somente para moderadores ou administradores.
                    \nExemplo.: a!altperola 2 "Raimundo jogando cartas com o R" """, inline=False)
    embed.add_field(name='a!perola <número da pérola>', value="""Use para ver somente uma pérola específica. 
                    \nExemplo.: a!perola 8""", inline=False)
    embed.add_field(name='a!verperolas <página>', value='Use para ver todas as pérolas presentes no servidor.', inline=False)
    embed.add_field(name='a!perolas', value="Use para ver uma pérola aleatória.", inline=False)
    embed.add_field(name='a!c', value='Use para conversar com o próprio bot.')
    embed.add_field(name='a!contagem', value='Que tal contribuir para nossa contagem?', inline=False)
    embed.add_field(name='Duvidas ou Sugestões', value='Incomode o ardonitos, ele vai te atender melhor que eu.', inline=False)

    await interactions.response.send_message(embed=embed)


@bot.command()
async def c(ctx: commands.Context, *, args):
    try:
        completion = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[
            {"role": "system", "content": f"Você é um ratinho engraçado chamado Raimundo, habilidoso em contar piadas, sendo seu ouvinte o {ctx.author}"},
            {"role": "user", "content": f"""{args}"""}
            ],
            temperature=0.7
        )
        await ctx.reply(completion.choices[0].message.content)
    except Exception as error:
        print(error)
        await ctx.reply("Serviço Indisponível")


@bot.command()
async def addperola(ctx, *, args):
    try:
        server_id = ctx.guild.id
        db.create_table(f'sv{server_id}', 'id INTEGER PRIMARY KEY, phrase TEXT') # Cria a Tabela do Servidor caso ela não exista.

        if len(db.read_data('id', f'sv{server_id}')) == 0: # Primeira Pérola adicionada na Tabela
            db.insert_data(f'sv{server_id}', f'1, {args}')
            await ctx.reply('Pérola Anotada.')
            return

        # Insere as pérolas normalmente no servidor em questão
        rows = db.read_data('id', f'sv{server_id}')
        db.insert_data(f'sv{server_id}', f"{rows[-1][0]+1}, {args}")
        await ctx.reply('Pérola Anotada.')

    except Exception as error:
        print(error)
        await ctx.reply('Ih rapaz, não foi a pérola. Talvez tu esqueceu as aspas ("")?')


@bot.command()
@has_permissions(manage_messages=True)
async def altperola(ctx, number_arg, pearl_arg):
    try:
        print(number_arg, pearl_arg)
        db.update_data(f'sv{ctx.guild.id}', f'phrase = "{pearl_arg}"', f'id={number_arg}')
        await ctx.reply('Pérola Alterada')
    except Exception as error:
        print(error)
        await ctx.reply('Houve uma falha ao executar este comando.')

@altperola.error
async def altperola_err(ctx, error):
    if isinstance(error, MissingPermissions):
        await ctx.reply(f"F {ctx.message.author}, tu não tem permissão para usar este comando.")


@bot.command()
async def perola(ctx, number_arg):
    try:
        var = db.read_data('phrase', f'sv{ctx.guild.id}', f'WHERE id={number_arg}')
        if var == []:
            raise IndexError

        await ctx.reply(f'Pérola #{number_arg} "{var[0][0]}"')
    except Exception as error:
        print(error)
        await ctx.reply('Das duas, uma: ou essa pérola não existe, ou tá fora da ordem.')


@bot.command()
async def perolas(ctx):
    try:
        rows = db.read_data('*', f'sv{ctx.guild.id}')
        exp = randint(1, len(rows))-1
        await ctx.reply(f'Pérola #{rows[exp][0]} "{rows[exp][1]}"')
    except Exception as error:
        print(error)
        await ctx.reply('Eu ainda não anotei nenhuma pérola por aqui.')


@bot.command()
async def verperolas(ctx: commands.Context, page='1'):
    server = ctx.guild
    actual_page = int(page)

    def loader(first, last):
        loader_ = db.read_data(table_name=f'sv{server.id}', otherstmt=f'WHERE id BETWEEN {first} AND {last}')
        return loader_
    
    def embed_content(loader):
        pearls_per_page_counter = 0
        for i in loader:
            embed.add_field(name=f'Pérola #{i[0]}', value=f'"{i[1]}"', inline=False)
            pearls_per_page_counter = i[0]
        embed.set_footer(text=f'Página {actual_page}/{total_pages} - Vendo {pearls_per_page_counter}-{total_of_pearls} Pérolas.')
        

    try:
        embed = discord.Embed(color=discord.Colour.pink(), title=f'Vendo as pérolas de {server.name}.')
        embed.set_thumbnail(url=server.icon.url)

        total_of_pearls: int = db.read_data('id', f'sv{server.id}')[-1][0]
        number_of_pages = total_of_pearls/8
        total_pages = number_of_pages if number_of_pages.is_integer() else floor(number_of_pages)+1 

        if actual_page < 1 or actual_page > total_pages:
            raise IndexError
        else:
            first_var = 8*(actual_page-1)+1
            last_var = 8*actual_page

            if actual_page == 1:
                embed_content(loader(1, 8))
                await ctx.send(embed=embed)
            elif actual_page == total_pages:
                embed_content(loader(first_var, last_var))
                await ctx.send(embed=embed)
            else:
                embed_content(loader(first_var, last_var))
                await ctx.send(embed=embed)


    except IndexError as ie:
        print(ie)
        await ctx.reply('Calma lá, eu ainda não anotei tanta pérola assim.')
    except Exception as error:
        print(error)
    

@bot.command()
async def contagem(ctx:commands.Context):
    try:
        db.create_table('contagem', 'numbers INTEGER')
        if len(db.read_data('*', 'contagem')) == 0:
            db.insert_data('contagem', '1')
            await ctx.send(f'{ctx.author} comecou a contagem em 1.')
            return

        rows = db.read_data('*', 'contagem')
        actual_number = rows[-1][0] +1
        db.update_data('contagem', f'numbers={actual_number}', f'numbers={actual_number-1}')
        await ctx.send(f'{ctx.author} continuou em {actual_number}.')
    except Exception as error:
        print(error)


bot.run(BOT_KEY)