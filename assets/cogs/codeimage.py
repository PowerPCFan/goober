import html
import io
import logging
import re
from enum import Enum
from typing import TYPE_CHECKING

import discord
from discord.ext import commands
from playwright.async_api import async_playwright

if TYPE_CHECKING:
    from collections.abc import Mapping

logger = logging.getLogger("goober")


# Both discord and this cog use highlight.js,
# so the compatibility should be 100%
# but we're starting with this subset
# which will probably be the most used anyways
class HighlightJSLanguage(Enum):
    PYTHON = "language-python"
    JAVASCRIPT = "language-javascript"
    CPLUSPLUS = "language-cpp"
    C = "language-c"
    JAVA = "language-java"
    RUST = "language-rust"
    GOLANG = "language-go"
    HTML = "language-html"
    CSS = "language-css"
    TYPESCRIPT = "language-typescript"
    JSON = "language-json"
    BASH = "language-bash"
    PWSH = "language-powershell"
    RUBY = "language-ruby"
    PHP = "language-php"
    SWIFT = "language-swift"
    KOTLIN = "language-kotlin"


class CodeImage(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.description = "🖼️|Code to image converter"
        self.pattern = re.compile(r"```([^\n]*)\n(.*?)```", re.DOTALL | re.UNICODE | re.IGNORECASE)
        # fmt: off
        self.lang_map: Mapping[HighlightJSLanguage, tuple[str, ...]] = {
            HighlightJSLanguage.PYTHON: ("py", "python", "gyp"),
            HighlightJSLanguage.JAVASCRIPT: ("javascript", "js", "jsx"),
            HighlightJSLanguage.CPLUSPLUS: ("cpp", "hpp", "cc", "hh", "c++", "h++", "cxx", "hxx"),
            HighlightJSLanguage.C: ("c", "h"),
            HighlightJSLanguage.JAVA: ("java", "jsp"),
            HighlightJSLanguage.RUST: ("rust", "rs"),
            HighlightJSLanguage.GOLANG: ("go", "golang"),
            HighlightJSLanguage.HTML: ("xml", "html", "xhtml", "rss", "atom", "xjb", "xsd", "xsl", "plist", "svg"),  # noqa: E501
            HighlightJSLanguage.CSS: ("css", "scss"),  # highlight.js has a scss highlighter but consolidate for now  # noqa: E501
            HighlightJSLanguage.TYPESCRIPT: ("typescript", "ts", "tsx", "mts", "cts"),
            HighlightJSLanguage.JSON: ("json", "jsonc"),
            HighlightJSLanguage.BASH: ("bash", "sh", "zsh"),
            HighlightJSLanguage.PWSH: ("powershell", "ps", "ps1"),
            HighlightJSLanguage.RUBY: ("ruby", "rb", "gemspec", "podspec", "thor", "irb"),
            HighlightJSLanguage.PHP: ("php",),
            HighlightJSLanguage.SWIFT: ("swift",),
            HighlightJSLanguage.KOTLIN: ("kotlin", "kt"),
        }
        # fmt: on

    def get_language(self, lang: str) -> HighlightJSLanguage | None:
        lang = lang.lower().strip()

        if not lang:
            return None

        for language, aliases in self.lang_map.items():
            if lang in aliases:
                return language

        return None

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            # ignore bots
            return

        logger.debug(f"Checking message {message.id} for codeblocks...")

        matches: list[re.Match[str]] = list(self.pattern.finditer(message.content))

        if not matches:
            logger.debug("No codeblocks found.")
            return

        logger.info(f"Found codeblock in message {message.id}.")

        lang: str | None = matches[0].group(1).strip().lower() if matches[0].group(1) else None
        code: str = matches[0].group(2).strip()

        if not code:
            logger.debug("Codeblock is empty, skipping...")
            return

        language: HighlightJSLanguage | None = self.get_language(lang) if lang else None

        logger.debug(f"Language extracted: {lang} -> {language.name if language else 'unknown/auto-detect'}")  # noqa: E501

        if language:
            codeblock_html = f'<code class="{language.value}">{html.escape(code)}</code>'
        else:
            codeblock_html = f"<code>{html.escape(code)}</code>"  # auto detect lang

        initial_reply = await message.reply(
            embed=discord.Embed(
                title="Image Generating",
                description="Codeblock detected! Generating code image, please wait...",
                color=discord.Color.orange(),
                timestamp=discord.utils.utcnow(),
            ),
        )

        try:
            logger.info(f"Generating code image (language: {language.name if language else 'auto-detect'})")  # noqa: E501
            image_bytes = await self.generate_code_image(codeblock_html)
            file = discord.File(io.BytesIO(image_bytes), filename="code_image.png")

            await initial_reply.edit(attachments=[file], embed=discord.Embed(
                title="Image Generated",
                description="Code image generated successfully!",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow(),
            ))
        except Exception:
            logger.exception("Error generating code image:")
            await initial_reply.edit(embed=discord.Embed(
                title="Error",
                description="An error occurred while generating the code image.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow(),
            ))

    async def generate_code_image(self, codeblock_html: str) -> bytes:
        html_content = self.create_html(codeblock_html)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            await page.set_content(html_content)
            await page.wait_for_function("typeof hljs !== 'undefined'", timeout=5000)

            dimensions = await page.evaluate("""
                () => {
                    const pre = document.querySelector('pre');
                    const rect = pre.getBoundingClientRect();
                    return {
                        width: Math.ceil(rect.width),
                        height: Math.ceil(rect.height)
                    };
                }
            """)

            await page.set_viewport_size({
                "width": dimensions["width"] + 40,
                "height": dimensions["height"] + 40,
            })

            element = await page.query_selector("pre")
            if not element:
                raise ValueError("Could not find code block element for screenshot")  # noqa: EM101, TRY003

            bounding_box = await element.bounding_box()
            if not bounding_box:
                raise ValueError("Could not get bounding box of code block element")  # noqa: EM101, TRY003

            screenshot = await page.screenshot(
                clip={
                    "x": bounding_box["x"],
                    "y": bounding_box["y"],
                    "width": bounding_box["width"],
                    "height": bounding_box["height"],
                },
            )

            await browser.close()

        return screenshot

    def create_html(self, codeblock_html: str) -> str:
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/highlight.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/languages/rust.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/languages/typescript.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/languages/powershell.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/languages/swift.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/languages/kotlin.min.js"></script>
    <style>
        :root {{
            --base00: #282828;
            --base01: #3c3836;
            --base02: #504945;
            --base03: #665c54;
            --base04: #bdae93;
            --base05: #d5c4a1;
            --base06: #ebdbb2;
            --base07: #fbf1c7;
            --base08: #fb4934;
            --base09: #fe8019;
            --base0A: #fabd2f;
            --base0B: #b8bb26;
            --base0C: #8ec07c;
            --base0D: #83a598;
            --base0E: #d3869b;
            --base0F: #d65d0e;
        }}

        *, *::before, *::after {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        html {{
            height: 100%;
            width: 100%;
        }}

        body {{
            margin: 0;
            height: 100%;
            font-family: "Inter", system-ui;
            color: #FFFFFF;
            background-color: #000000;
            padding: 2rem;
            display: flex;
            justify-content: center;
            align-items: center;
        }}

        pre {{
            border-radius: 8px;
            overflow-x: auto;
            background: var(--base00);
            border: 2px solid var(--base03);
            max-width: 1000px;
            width: fit-content;
            padding: 1rem;
        }}

        code {{
            border-radius: 0.25rem;
            padding: 1rem;
            white-space: pre-wrap;
            word-break: break-word;
            display: block;
        }}

        /* highlight.js */
        pre code.hljs {{
          display: block;
          overflow-x: auto;
          padding: 0.5rem;
        }}
        code.hljs {{
          padding: 3px 5px
        }}
        .hljs {{
          color: var(--base05);
          /*background: var(--base00);*/
          background-color: inherit;
        }}

        .hljs::selection,
        .hljs ::selection {{
          background-color: var(--base02);
          color: var(--base05);
        }}

        .hljs-comment {{
          color: var(--base03);
        }}

        .hljs-tag {{
          color: var(--base04);
        }}

        .hljs-subst,
        .hljs-punctuation,
        .hljs-operator {{
          color: var(--base05)
        }}
        .hljs-operator {{
          opacity: 0.7
        }}

        .hljs-bullet,
        .hljs-variable,
        .hljs-template-variable,
        .hljs-selector-tag,
        .hljs-name,
        .hljs-deletion {{
          color: var(--base08);
        }}

        .hljs-symbol,
        .hljs-number,
        .hljs-link,
        .hljs-attr,
        .hljs-variable.constant_,
        .hljs-literal {{
          color: var(--base09)
        }}

        .hljs-title,
        .hljs-class .hljs-title,
        .hljs-title.class_ {{
          color: var(--base0A)
        }}
        .hljs-strong {{
          font-weight: bold;
          color: var(--base0A)
        }}

        .hljs-code,
        .hljs-addition,
        .hljs-title.class_.inherited__,
        .hljs-string {{
          color: var(--base0B)
        }}

        .hljs-built_in,
        .hljs-doctag,
        .hljs-quote,
        .hljs-keyword.hljs-atrule,
        .hljs-regexp {{
          color: var(--base0C)
        }}

        .hljs-function .hljs-title,
        .hljs-attribute,
        .ruby .hljs-property,
        .hljs-title.function_,
        .hljs-section {{
          color: var(--base0D)
        }}

        .hljs-type,
        .hljs-template-tag,
        .diff .hljs-meta,
        .hljs-keyword {{
          color: var(--base0E)
        }}
        .hljs-emphasis {{
          color: var(--base0E);
          font-style: italic
        }}

        .hljs-meta,
        .hljs-meta .hljs-keyword,
        .hljs-meta .hljs-string {{
          color: var(--base0F)
        }}

        .hljs-meta .hljs-keyword,
        .hljs-meta-keyword {{
          font-weight: bold
        }}
    </style>
</head>
<body>
    <pre>{codeblock_html}</pre>
    <script>hljs.highlightAll();</script>
</body>
</html>""".strip()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CodeImage(bot))
