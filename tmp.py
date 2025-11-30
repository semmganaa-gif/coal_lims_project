from pathlib import Path
text=Path('app/templates/ahlah_dashboard.html').read_text(encoding='utf-8')
start=text.index('<p class="text-muted">')
end=text.index('</p>', start)+4
print(repr(text[start:end]))
