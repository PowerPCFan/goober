from typing import TypedDict, overload

import discord
from discord.ext import commands


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
    fields: list[DiscordEmbedField] | None = None,
    footer_text: str | None = None,
) -> discord.Message:
    ...


@overload
async def send_info(
    ctx_or_interaction: discord.Interaction,
    *,
    title: str,
    description: str,
    fields: list[DiscordEmbedField] | None = None,
    footer_text: str | None = None,
) -> discord.InteractionCallbackResponse[discord.Client]:
    ...


async def send_info(
    ctx_or_interaction: commands.Context | discord.Interaction,
    *,
    title: str,
    description: str,
    fields: list[DiscordEmbedField] | None = None,
    footer_text: str | None = None,
):
    if isinstance(ctx_or_interaction, commands.Context):
        send = ctx_or_interaction.send
    else:
        send = ctx_or_interaction.response.send_message

    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.blue()
    )

    if fields:
        for field in fields:
            embed.add_field(**field)

    if footer_text:
        embed.set_footer(text=footer_text)

    return await send(embed=embed)


@overload
async def send_success(
    ctx_or_interaction: commands.Context,
    *,
    description: str,
    fields: list[DiscordEmbedField] | None = None,
    title: str = "Success"
) -> discord.Message:
    ...


@overload
async def send_success(
    ctx_or_interaction: discord.Interaction,
    *,
    description: str,
    fields: list[DiscordEmbedField] | None = None,
    title: str = "Success"
) -> discord.InteractionCallbackResponse[discord.Client]:
    ...


async def send_success(
    ctx_or_interaction: commands.Context | discord.Interaction,
    *,
    description: str,
    fields: list[DiscordEmbedField] | None = None,
    title: str = "Success",
):
    if isinstance(ctx_or_interaction, commands.Context):
        send = ctx_or_interaction.send
    else:
        send = ctx_or_interaction.response.send_message

    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.green()
    )

    if fields:
        for field in fields:
            embed.add_field(**field)

    return await send(embed=embed)


@overload
async def send_warning(
    ctx_or_interaction: commands.Context,
    *,
    description: str,
    fields: list[DiscordEmbedField] | None = None,
    title: str = "Warning"
) -> discord.Message:
    ...


@overload
async def send_warning(
    ctx_or_interaction: discord.Interaction,
    *,
    description: str,
    fields: list[DiscordEmbedField] | None = None,
    title: str = "Warning"
) -> discord.InteractionCallbackResponse[discord.Client]:
    ...


async def send_warning(
    ctx_or_interaction: commands.Context | discord.Interaction,
    *,
    description: str,
    fields: list[DiscordEmbedField] | None = None,
    title: str = "Warning"
):
    if isinstance(ctx_or_interaction, commands.Context):
        send = ctx_or_interaction.send
    else:
        send = ctx_or_interaction.response.send_message

    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.orange()
    )

    if fields:
        for field in fields:
            embed.add_field(**field)

    return await send(embed=embed)


@overload
async def send_error(
    ctx_or_interaction: commands.Context,
    *,
    description: str,
    fields: list[DiscordEmbedField] | None = None,
    title: str = "Error"
) -> discord.Message:
    ...


@overload
async def send_error(
    ctx_or_interaction: discord.Interaction,
    *,
    description: str,
    fields: list[DiscordEmbedField] | None = None,
    title: str = "Error",
) -> discord.InteractionCallbackResponse[discord.Client]:
    ...


async def send_error(
    ctx_or_interaction: commands.Context | discord.Interaction,
    *,
    description: str,
    fields: list[DiscordEmbedField] | None = None,
    title: str = "Error"
):
    if isinstance(ctx_or_interaction, commands.Context):
        send = ctx_or_interaction.send
    else:
        send = ctx_or_interaction.response.send_message

    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.red()
    )

    if fields:
        for field in fields:
            embed.add_field(**field)

    return await send(embed=embed)
