# invAIriant demo — a REAL recording of the live CLI.
#   Make it:  vhs demo.tape           (brew install vhs)
#   Needs:    pip install invairiant  ·  run from this repo (refundpilot/)
Output invairiant-demo.gif

Set Shell "bash"
Set FontSize 24
Set Width 1320
Set Height 470
Set Padding 26
Set Margin 14
Set BorderRadius 10
Set TypingSpeed 8ms
Set Theme { "background": "#0b1210", "foreground": "#e4ebe6", "cursor": "#4fc79a", "selection": "#22302a", "black": "#0b1210", "red": "#e0603a", "green": "#4fc79a", "yellow": "#e8a250", "blue": "#8fb3ff", "magenta": "#b08fff", "cyan": "#54c7b0", "white": "#e4ebe6", "brightBlack": "#5f6f66", "brightRed": "#e0603a", "brightGreen": "#4fc79a", "brightYellow": "#e8a250", "brightBlue": "#8fb3ff", "brightMagenta": "#b08fff", "brightCyan": "#54c7b0", "brightWhite": "#ffffff" }

# ── hidden setup: git repo (adr scope), clean prompt, blank screen ──
Hide
Type "PS1='$ '; [ -e .git ] || { git init -q -b main . && git add -A; }; clear" Enter
Sleep 300ms
Show

Sleep 500ms
Type "# report.json was produced by /invairiant audit-adr" Enter
Sleep 850ms
Type "invairiant collect --scope adr --path docs/adr/0007-refund-caps.md --out b.json" Enter
Sleep 1700ms
Type "invairiant validate-report report.json" Enter
Sleep 1700ms
Type "invairiant ci-gate report.json" Enter
Sleep 4800ms
