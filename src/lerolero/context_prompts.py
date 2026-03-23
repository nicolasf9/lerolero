"""Context-aware initial prompts for Whisper — improves accuracy based on active application."""

from __future__ import annotations

# Maps normalized process names (no .exe, lowercase) to vocabulary hints.
# Works cross-platform: "code" matches code.exe (Windows), Code (macOS), code (Linux).
CONTEXT_PROMPTS: dict[str, str] = {
    # Code editors / IDEs
    "code": (
        "Software development, programming, Python, JavaScript, TypeScript, "
        "function, class, variable, API, git, commit, merge, deploy, debug, "
        "refactor, import, export, async, await, const, let, return"
    ),
    "devenv": (
        "Visual Studio, C#, .NET, NuGet, solution, project, build, debug, "
        "namespace, class, interface, async, Task, LINQ"
    ),
    "idea64": (
        "IntelliJ, Java, Kotlin, Spring, Maven, Gradle, "
        "class, interface, annotation, dependency injection"
    ),
    "idea": (
        "IntelliJ, Java, Kotlin, Spring, Maven, Gradle, "
        "class, interface, annotation, dependency injection"
    ),
    "cursor": (
        "Software development, AI coding, Python, JavaScript, TypeScript, "
        "function, class, variable, API, git, refactor"
    ),

    # Design tools
    "figma": (
        "UI design, UX, components, frames, auto-layout, layers, "
        "padding, margin, typography, color, prototype, Figma"
    ),

    # Browsers
    "vivaldi": "Web browsing, search, URL, website, link, tab, bookmark",
    "chrome": "Web browsing, search, URL, website, link, tab, bookmark",
    "google chrome": "Web browsing, search, URL, website, link, tab, bookmark",
    "firefox": "Web browsing, search, URL, website, link, tab, bookmark",
    "msedge": "Web browsing, search, URL, website, link, tab, bookmark",
    "microsoft edge": "Web browsing, search, URL, website, link, tab, bookmark",
    "brave": "Web browsing, search, URL, website, link, tab, bookmark",
    "safari": "Web browsing, search, URL, website, link, tab, bookmark",

    # Communication
    "discord": "Chat, message, server, channel, voice call, gaming, Discord",
    "slack": "Chat, message, channel, thread, Slack, workspace, DM",
    "teams": "Microsoft Teams, meeting, chat, call, channel, presentation",
    "telegram": "Chat, message, Telegram, group, channel",
    "whatsapp": "Chat, message, WhatsApp, group, media, audio",

    # Productivity
    "obsidian": (
        "Notes, markdown, knowledge base, links, tags, Obsidian, vault, "
        "backlinks, graph, template"
    ),
    "notion": "Notes, pages, databases, Notion, workspace, blocks, templates",
    "winword": "Microsoft Word, document, paragraph, formatting, table, header",
    "word": "Microsoft Word, document, paragraph, formatting, table, header",
    "excel": "Microsoft Excel, spreadsheet, cell, formula, chart, pivot table",
    "powerpnt": "Microsoft PowerPoint, slides, presentation, bullet points",
    "keynote": "Keynote, slides, presentation, animation, Apple",
    "pages": "Pages, document, Apple, formatting, paragraph",
    "numbers": "Numbers, spreadsheet, Apple, cell, formula",

    # Terminal
    "windowsterminal": (
        "Command line, terminal, shell, bash, PowerShell, git, npm, pip, "
        "docker, kubectl, ssh, cd, ls, mkdir"
    ),
    "cmd": "Command prompt, batch, dir, cd, copy, del, mkdir",
    "powershell": "PowerShell, cmdlet, Get-Item, Set-Item, pipeline, module",
    "terminal": "Command line, terminal, shell, bash, git, npm, pip, ssh, cd, ls",
    "iterm2": "Command line, terminal, shell, bash, git, npm, pip, ssh, cd, ls",
    "gnome-terminal": "Command line, terminal, shell, bash, git, npm, pip, ssh",
    "konsole": "Command line, terminal, shell, bash, git, npm, pip, ssh",
}


def get_prompt_for_process(process_name: str | None) -> str:
    """Return a context-appropriate initial prompt for Whisper.

    Args:
        process_name: Normalized process name (no .exe, lowercase).

    Returns:
        A vocabulary hint string, or empty string if no match.
    """
    if not process_name:
        return ""
    # Normalize: strip .exe, lowercase
    name = process_name.lower().strip()
    if name.endswith(".exe"):
        name = name[:-4]
    return CONTEXT_PROMPTS.get(name, "")
