"""Context-aware initial prompts for Whisper — improves accuracy based on active application."""

from __future__ import annotations

# Maps process executable names to vocabulary hints for Whisper's initial_prompt.
# These prime the model to prefer domain-specific terms.
CONTEXT_PROMPTS: dict[str, str] = {
    # Code editors / IDEs
    "code.exe": (
        "Software development, programming, Python, JavaScript, TypeScript, "
        "function, class, variable, API, git, commit, merge, deploy, debug, "
        "refactor, import, export, async, await, const, let, return"
    ),
    "devenv.exe": (
        "Visual Studio, C#, .NET, NuGet, solution, project, build, debug, "
        "namespace, class, interface, async, Task, LINQ"
    ),
    "idea64.exe": (
        "IntelliJ, Java, Kotlin, Spring, Maven, Gradle, "
        "class, interface, annotation, dependency injection"
    ),
    "cursor.exe": (
        "Software development, AI coding, Python, JavaScript, TypeScript, "
        "function, class, variable, API, git, refactor"
    ),

    # Design tools
    "figma.exe": (
        "UI design, UX, components, frames, auto-layout, layers, "
        "padding, margin, typography, color, prototype, Figma"
    ),

    # Browsers
    "vivaldi.exe": "Web browsing, search, URL, website, link, tab, bookmark",
    "chrome.exe": "Web browsing, search, URL, website, link, tab, bookmark",
    "firefox.exe": "Web browsing, search, URL, website, link, tab, bookmark",
    "msedge.exe": "Web browsing, search, URL, website, link, tab, bookmark",
    "brave.exe": "Web browsing, search, URL, website, link, tab, bookmark",

    # Communication
    "discord.exe": "Chat, message, server, channel, voice call, gaming, Discord",
    "slack.exe": "Chat, message, channel, thread, Slack, workspace, DM",
    "teams.exe": "Microsoft Teams, meeting, chat, call, channel, presentation",
    "telegram.exe": "Chat, message, Telegram, group, channel",
    "whatsapp.exe": "Chat, message, WhatsApp, group, media, audio",

    # Productivity
    "obsidian.exe": (
        "Notes, markdown, knowledge base, links, tags, Obsidian, vault, "
        "backlinks, graph, template"
    ),
    "notion.exe": "Notes, pages, databases, Notion, workspace, blocks, templates",
    "winword.exe": "Microsoft Word, document, paragraph, formatting, table, header",
    "excel.exe": "Microsoft Excel, spreadsheet, cell, formula, chart, pivot table",
    "powerpnt.exe": "Microsoft PowerPoint, slides, presentation, bullet points",

    # Terminal
    "windowsterminal.exe": (
        "Command line, terminal, shell, bash, PowerShell, git, npm, pip, "
        "docker, kubectl, ssh, cd, ls, mkdir"
    ),
    "cmd.exe": "Command prompt, batch, dir, cd, copy, del, mkdir",
    "powershell.exe": "PowerShell, cmdlet, Get-Item, Set-Item, pipeline, module",
}


def get_prompt_for_process(process_name: str | None) -> str:
    """Return a context-appropriate initial prompt for Whisper.

    Args:
        process_name: The executable name of the active window (e.g. "code.exe").

    Returns:
        A vocabulary hint string, or empty string if no match.
    """
    if not process_name:
        return ""
    name = process_name.lower().strip()
    return CONTEXT_PROMPTS.get(name, "")
