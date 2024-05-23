from math import floor
from random import randint
from os import getenv
import discord
from discord.ext import commands
from discord.ext.commands import has_permissions, MissingPermissions
from openai import OpenAI
from db_manager import Database

BOT_KEY, OPENAI_KEY = getenv('BOT_KEY'), getenv('OPENAI_API_KEY')

db = Database('pearls.db')

intents = discord.Intents.default()
intents.message_content = True

client = OpenAI(api_key=OPENAI_KEY)
bot = commands.Bot(command_prefix='a!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logado como {bot.user.name}.')
    await bot.change_presence(activity=discord.Game('a!ajuda na sua cara.'))


@bot.command()
async def ajuda(ctx):
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
    embed.add_field(name='Duvidas ou Sugestões', value='Incomode o ardonitos, ele vai te atender melhor que eu.', inline=False)

    await ctx.send(embed=embed)


@bot.command()
async def c(ctx, *, args):
    completion = client.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=[
        {"role": "system", "content": "Você é um ratinho engraçado chamado Raimundo, sendo sua maior habilidade ser fazer piadas e rir usando KKKKKK!"},
        {"role": "user", "content": f"""{args}"""}
        ]
    )
    await ctx.reply(completion.choices[0].message.content)


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
    page_ = int(page)

    def loader(first, last):
        loader_ = db.read_data(table_name=f'sv{server.id}', otherstmt=f'WHERE id BETWEEN {first} AND {last}')
        return loader_
    
    def embed_content(loader):
        counter = 0
        for i in loader:
            embed.add_field(name=f'Pérola #{i[0]}', value=f'"{i[1]}"', inline=False)
            counter = i[0]
        embed.set_footer(text=f'Página {page_}/{total_pages} - Vendo {counter}-{total_pearl} Pérolas.')
        

    try:
        embed = discord.Embed(color=discord.Colour.pink(), title=f'Vendo as pérolas de {server.name}.')
        embed.set_thumbnail(url=server.icon.url)

        total_pearl: int = db.read_data('id', f'sv{server.id}')[-1][0]
        pages_var = total_pearl/8
        total_pages = pages_var if pages_var.is_integer() else floor(pages_var)+1 

        if page_ < 1 or page_ > total_pages:
            raise IndexError
        else:
            first_var = 8*(page_-1)+1
            last_var = 8*page_

            if page_ == 1:
                embed_content(loader(1, 8))
                await ctx.send(embed=embed)
            elif page_ == total_pages:
                embed_content(loader(first_var, last_var))
                await ctx.send(embed=embed)
            else:
                embed_content(loader(first_var, last_var))
                await ctx.send(embed=embed)


    except IndexError as ie:
        print(ie)
        await ctx.reply('Calma lá, eu ainda não anotei tanta pérola assim.')
    except Exception as e:
        print(e)
        return

bot.run(BOT_KEY)