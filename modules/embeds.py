import discord
from discord.ext import commands
from typing import TypedDict, overload


class DiscordEmbedField(TypedDict):
    name: str
    value: str
    inline: bool


@overload
async def send_info(
    ctx_or_interaction: commands.Context,
    *,
    title: str,
    description: str,
    fields: list[DiscordEmbedField] = [],
    reply: bool = False
) -> discord.Message:
    ...


@overload
async def send_info(
    ctx_or_interaction: discord.Interaction,
    *,
    title: str,
    description: str,
    fields: list[DiscordEmbedField] = [],
) -> discord.InteractionCallbackResponse[discord.Client]:
    ...


async def send_info(
    ctx_or_interaction: commands.Context | discord.Interaction,
    *,
    title: str,
    description: str,
    fields: list[DiscordEmbedField] = [],
    reply: bool = False,
):
    if isinstance(ctx_or_interaction, commands.Context):
        if reply:
            send = ctx_or_interaction.message.reply
        else:
            send = ctx_or_interaction.send
    else:
        send = ctx_or_interaction.response.send_message

    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.blue()
    )

    for field in fields:
        embed.add_field(**field)

    return await send(embed=embed)


@overload
async def send_success(
    ctx_or_interaction: commands.Context,
    *,
    description: str,
    fields: list[DiscordEmbedField] = [],
    title: str = "Success",
    reply: bool = False
) -> discord.Message:
    ...


@overload
async def send_success(
    ctx_or_interaction: discord.Interaction,
    *,
    description: str,
    fields: list[DiscordEmbedField] = [],
    title: str = "Success"
) -> discord.InteractionCallbackResponse[discord.Client]:
    ...


async def send_success(
    ctx_or_interaction: commands.Context | discord.Interaction,
    *,
    description: str,
    fields: list[DiscordEmbedField] = [],
    title: str = "Success",
    reply: bool = False
):
    if isinstance(ctx_or_interaction, commands.Context):
        if reply:
            send = ctx_or_interaction.message.reply
        else:
            send = ctx_or_interaction.send
    else:
        send = ctx_or_interaction.response.send_message

    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.green()
    )

    for field in fields:
        embed.add_field(**field)

    return await send(embed=embed)


@overload
async def send_warning(
    ctx_or_interaction: commands.Context,
    *,
    description: str,
    fields: list[DiscordEmbedField] = [],
    title: str = "Warning",
    reply: bool = False
) -> discord.Message:
    ...


@overload
async def send_warning(
    ctx_or_interaction: discord.Interaction,
    *,
    description: str,
    fields: list[DiscordEmbedField] = [],
    title: str = "Warning",
) -> discord.InteractionCallbackResponse[discord.Client]:
    ...


async def send_warning(
    ctx_or_interaction: commands.Context | discord.Interaction,
    *,
    description: str,
    fields: list[DiscordEmbedField] = [],
    title: str = "Warning",
    reply: bool = False,
):
    if isinstance(ctx_or_interaction, commands.Context):
        if reply:
            send = ctx_or_interaction.message.reply
        else:
            send = ctx_or_interaction.send
    else:
        send = ctx_or_interaction.response.send_message

    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.orange()
    )

    for field in fields:
        embed.add_field(**field)

    return await send(embed=embed)


@overload
async def send_error(
    ctx_or_interaction: commands.Context,
    *,
    description: str,
    fields: list[DiscordEmbedField] = [],
    title: str = "Error",
    reply: bool = False
) -> discord.Message:
    ...


@overload
async def send_error(
    ctx_or_interaction: discord.Interaction,
    *,
    description: str,
    fields: list[DiscordEmbedField] = [],
    title: str = "Error",
) -> discord.InteractionCallbackResponse[discord.Client]:
    ...


async def send_error(
    ctx_or_interaction: commands.Context | discord.Interaction,
    *,
    description: str,
    fields: list[DiscordEmbedField] = [],
    title: str = "Error",
    reply: bool = False,
):
    if isinstance(ctx_or_interaction, commands.Context):
        if reply:
            send = ctx_or_interaction.message.reply
        else:
            send = ctx_or_interaction.send
    else:
        send = ctx_or_interaction.response.send_message

    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.red()
    )

    for field in fields:
        embed.add_field(**field)

    return await send(embed=embed)
