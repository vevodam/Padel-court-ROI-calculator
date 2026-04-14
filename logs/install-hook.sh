#!/bin/bash
# Tento skript nainstaluje post-commit hook do lokálního git repozitáře.
# Spusť jej jednou z kořenové složky projektu: bash logs/install-hook.sh

HOOK_PATH=".git/hooks/post-commit"

cat > "$HOOK_PATH" << 'HOOK'
#!/bin/bash
# Post-commit hook: automaticky zaznamená každý commit do logs/CHANGELOG.md

LOG_FILE="logs/CHANGELOG.md"

# Prevence nekonečné smyčky – changelog commity se nelogují
COMMIT_MSG=$(git log -1 --pretty=%s)
if [[ "$COMMIT_MSG" == "chore: aktualizace logu" ]]; then
    exit 0
fi

mkdir -p logs

HASH=$(git log -1 --pretty=%h)
DATUM=$(date "+%Y-%m-%d %H:%M")
SOUBORY=$(git diff-tree --no-commit-id -r --name-only HEAD | sed 's/^/  - /')

if [ ! -f "$LOG_FILE" ]; then
    echo "# Changelog – Padel Business Model" > "$LOG_FILE"
    echo "" >> "$LOG_FILE"
    echo "---" >> "$LOG_FILE"
fi

# Nový záznam se vloží NA ZAČÁTEK souboru (nejaktuálnější nahoře)
TEMP=$(mktemp)
{
    head -4 "$LOG_FILE"               # zachová hlavičku souboru
    echo ""
    echo "## $DATUM  (\`$HASH\`)"
    echo "**Popis:** $COMMIT_MSG"
    echo ""
    echo "**Změněné soubory:**"
    echo "$SOUBORY"
    echo ""
    echo "---"
    tail -n +5 "$LOG_FILE"            # zbytek starých záznamů
} > "$TEMP"
mv "$TEMP" "$LOG_FILE"

git add "$LOG_FILE"
git commit -m "chore: aktualizace logu" --no-verify --quiet
HOOK

chmod +x "$HOOK_PATH"
echo "✅ Hook nainstalován: $HOOK_PATH"
