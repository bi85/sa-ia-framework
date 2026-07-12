#!/usr/bin/env python3
"""
SA-IA — Sistema Âncora para Inteligência Artificial
CLI principal do framework.

Uso:
  python sa-ia.py setup      — registra hooks no Claude Code (rode uma vez por máquina)
  python sa-ia.py create     — cria novo projeto interativamente
  python sa-ia.py status     — exibe contexto atual do projeto ativo
  python sa-ia.py destilar   — destila raw/ e atualiza changelog.md do projeto ativo
"""

import sys
import os
import json
import shutil
import re
from datetime import datetime
from pathlib import Path

# ── Paths base ────────────────────────────────────────────────────────────────

ROOT = Path(__file__).parent
PROJETOS = ROOT / "projetos"
ANCORA_GLOBAL = ROOT / "ANCORA.md"
CLAUDE_DIR = ROOT / ".claude"
HOOKS_DIR = CLAUDE_DIR / "hooks"
SETTINGS = CLAUDE_DIR / "settings.json"

TEMPLATES = {
    "ancora_projeto": """\
---
title: {nome}
sa-ia-type: ancora-projeto
projeto: {slug}
cliente: {cliente}
criado: {data}
status: ativo
---

# {nome}

## Objetivo

{objetivo}

## Escopo

[O que este projeto inclui — seja específico]

## Fora do escopo

[O que explicitamente não faz parte deste projeto]

## Stakeholders

| Nome | Papel | Contato |
|------|-------|---------|
| {cliente} | Cliente | — |

## Critério de sucesso

[Como você sabe que o projeto foi concluído com sucesso]
""",

    "perfil_destilacao": """\
---
title: Perfil de Destilação — {nome}
sa-ia-type: perfil-destilacao
projeto: {slug}
---

# Perfil de Destilação — {nome}

## O que SEMPRE deve entrar no changelog

- Decisões que alteram escopo, prazo ou orçamento
- Marcos comerciais: contratos, metas, entregas aceitas
- Bloqueios que dependem de terceiros
- Mudanças de responsabilidade ou equipe
- Próximos passos com data e responsável

## O que NUNCA deve entrar no changelog

- Detalhes operacionais já resolvidos
- Repetição de contexto já registrado
- Perguntas em aberto sem resposta
- Problemas técnicos menores sem impacto estratégico

## Limite por ciclo

- Máximo 10 bullets por atualização
- Máximo 2000 tokens no arquivo completo
- Se ultrapassar: comprimir entrada mais antiga em 1 parágrafo
""",

    "tasks": """\
---
title: Tarefas — {nome}
sa-ia-type: tasks
projeto: {slug}
atualizado: {data}
---

# Tarefas — {nome}

## Em andamento

- [ ] #task-001 [Primeira tarefa do projeto]

## A fazer

- [ ] #task-002 [Próxima tarefa]

## Concluídas

<!-- tarefas concluídas aparecem aqui -->

## Bloqueadas

<!-- tarefas bloqueadas por terceiros aparecem aqui -->
""",

    "changelog": """\
---
title: Changelog — {nome}
sa-ia-type: changelog
projeto: {slug}
ultima-atualizacao: {data}
---

# Changelog — {nome}

> Contexto destilado automaticamente. Leia antes de cada sessão.
> Não edite manualmente — gerado pelo hook sa-ia stop.

## {data} — Início do projeto

**Marcos alcançados**
- Projeto criado e estrutura inicializada

**Próximos passos**
- Preencher escopo em ANCORA_PROJETO.md
- Adicionar primeiras tarefas em tasks.md
- Criar primeiro arquivo em raw/ após reunião inicial
""",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[àáâãä]', 'a', text)
    text = re.sub(r'[èéêë]', 'e', text)
    text = re.sub(r'[ìíîï]', 'i', text)
    text = re.sub(r'[òóôõö]', 'o', text)
    text = re.sub(r'[ùúûü]', 'u', text)
    text = re.sub(r'[ç]', 'c', text)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s]+', '-', text)
    return text

def hoje() -> str:
    return datetime.now().strftime("%Y-%m-%d")

def projeto_ativo() -> Path | None:
    """Retorna o path do primeiro projeto com status: ativo."""
    if not PROJETOS.exists():
        return None
    for proj_dir in sorted(PROJETOS.iterdir()):
        ancora = proj_dir / "ANCORA_PROJETO.md"
        if ancora.exists() and "status: ativo" in ancora.read_text(encoding="utf-8"):
            return proj_dir
    return None

def ler_arquivo(path: Path, max_linhas: int = 0) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    if max_linhas:
        linhas = text.splitlines()
        return "\n".join(linhas[:max_linhas])
    return text

def atomic_write(path: Path, content: str):
    """Escreve via temp + rename para evitar conflito com Claude Code."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)

# ── Comandos ──────────────────────────────────────────────────────────────────

def cmd_setup():
    """Registra hooks no .claude/settings.json do projeto."""
    print("SA-IA — Setup\n")

    # Garante que os diretórios existem
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    PROJETOS.mkdir(exist_ok=True)

    # Copia hooks se existirem na pasta hooks/ do repo
    repo_hooks = ROOT / "hooks"
    if repo_hooks.exists():
        for hook in repo_hooks.iterdir():
            dest = HOOKS_DIR / hook.name
            shutil.copy2(hook, dest)
            dest.chmod(0o755)
            print(f"  ✓ Hook copiado: {hook.name}")
    else:
        # Cria hooks inline se pasta hooks/ não existir
        _criar_hooks_inline()

    # Registra em settings.json
    settings = {}
    if SETTINGS.exists():
        try:
            settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass

    settings.setdefault("hooks", {})
    settings["hooks"]["PreToolUse"] = []
    settings["hooks"]["Stop"] = [
        {
            "matcher": "",
            "hooks": [
                {
                    "type": "command",
                    "command": f"bash \"{HOOKS_DIR / 'stop.sh'}\""
                }
            ]
        }
    ]
    settings["hooks"]["UserPromptSubmit"] = [
        {
            "matcher": "",
            "hooks": [
                {
                    "type": "command",
                    "command": f"bash \"{HOOKS_DIR / 'session-start.sh'}\""
                }
            ]
        }
    ]

    atomic_write(SETTINGS, json.dumps(settings, indent=2, ensure_ascii=False))
    print(f"  ✓ Hooks registrados em .claude/settings.json")
    print(f"\nSetup concluído. Abra o Claude Code para começar.")
    print(f"Próximo passo: preencha ANCORA.md com sua identidade.")


def _criar_hooks_inline():
    """Cria os hooks diretamente se a pasta hooks/ não existir no repo."""

    session_start = """\
#!/usr/bin/env bash
# SA-IA — session-start hook
# Injeta contexto do projeto ativo no início da sessão.

SAAIA_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ANCORA_GLOBAL="$SAAIA_ROOT/ANCORA.md"
PROJETOS="$SAAIA_ROOT/projetos"

echo ""
echo "━━━ SA-IA ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Âncora global
if [ -f "$ANCORA_GLOBAL" ]; then
  echo ""
  cat "$ANCORA_GLOBAL"
fi

# Projeto ativo
ATIVO=""
for dir in "$PROJETOS"/*/; do
  ainda="$dir/ANCORA_PROJETO.md"
  if [ -f "$ainda" ] && grep -q "status: ativo" "$ainda"; then
    ATIVO="$dir"
    break
  fi
done

if [ -n "$ATIVO" ]; then
  echo ""
  echo "━━━ PROJETO ATIVO ━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  cat "$ATIVO/ANCORA_PROJETO.md"

  echo ""
  echo "━━━ CHANGELOG (últimas entradas) ━━━━━━━━━━━━"
  if [ -f "$ATIVO/changelog.md" ]; then
    head -80 "$ATIVO/changelog.md"
  else
    echo "(sem changelog ainda)"
  fi

  echo ""
  echo "━━━ TAREFAS ABERTAS ━━━━━━━━━━━━━━━━━━━━━━━━"
  if [ -f "$ATIVO/tasks.md" ]; then
    grep -E "^- \\[ \\]" "$ATIVO/tasks.md" || echo "(nenhuma tarefa aberta)"
  fi
else
  echo ""
  echo "Nenhum projeto ativo. Use: python sa-ia.py create"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
"""

    stop = """\
#!/usr/bin/env bash
# SA-IA — stop hook
# Destila raw/ e atualiza changelog.md ao encerrar sessão.

SAAIA_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

python "$SAAIA_ROOT/sa-ia.py" destilar
"""

    for nome, conteudo in [("session-start.sh", session_start), ("stop.sh", stop)]:
        path = HOOKS_DIR / nome
        atomic_write(path, conteudo)
        path.chmod(0o755)
        print(f"  ✓ Hook criado: {nome}")


def cmd_create():
    """Cria novo projeto interativamente."""
    print("SA-IA — Novo Projeto\n")

    nome = input("Nome do projeto: ").strip()
    if not nome:
        print("Nome obrigatório.")
        sys.exit(1)

    cliente = input("Cliente (ou deixe vazio): ").strip() or "—"
    objetivo = input("Objetivo em uma frase: ").strip() or "A definir"

    slug = slugify(nome)
    proj_dir = PROJETOS / slug

    if proj_dir.exists():
        print(f"Projeto '{slug}' já existe em projetos/{slug}/")
        sys.exit(1)

    # Cria estrutura
    (proj_dir / "raw").mkdir(parents=True)

    ctx = {"nome": nome, "slug": slug, "cliente": cliente,
           "objetivo": objetivo, "data": hoje()}

    for arquivo, template in [
        ("ANCORA_PROJETO.md", TEMPLATES["ancora_projeto"]),
        ("perfil-destilacao.md", TEMPLATES["perfil_destilacao"]),
        ("tasks.md", TEMPLATES["tasks"]),
        ("changelog.md", TEMPLATES["changelog"]),
    ]:
        atomic_write(proj_dir / arquivo, template.format(**ctx))

    # Pausa outros projetos ativos
    if PROJETOS.exists():
        for outro in PROJETOS.iterdir():
            if outro == proj_dir:
                continue
            ainda = outro / "ANCORA_PROJETO.md"
            if ainda.exists():
                conteudo = ainda.read_text(encoding="utf-8")
                if "status: ativo" in conteudo:
                    atomic_write(ainda, conteudo.replace("status: ativo", "status: pausado"))

    print(f"\n✓ Projeto criado em projetos/{slug}/")
    print(f"  Próximo passo: edite projetos/{slug}/ANCORA_PROJETO.md com o escopo completo.")


def cmd_status():
    """Exibe contexto atual do projeto ativo."""
    ativo = projeto_ativo()
    if not ativo:
        print("Nenhum projeto ativo. Use: python sa-ia.py create")
        sys.exit(0)

    print(f"\n━━━ SA-IA STATUS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    print(f"Projeto ativo: {ativo.name}\n")

    # Tarefas abertas
    tasks = ativo / "tasks.md"
    if tasks.exists():
        abertas = [l for l in tasks.read_text(encoding="utf-8").splitlines()
                   if l.startswith("- [ ]")]
        print(f"Tarefas abertas ({len(abertas)}):")
        for t in abertas:
            print(f"  {t}")

    # Raw pendentes
    raw_dir = ativo / "raw"
    if raw_dir.exists():
        raw_files = sorted(raw_dir.iterdir())
        print(f"\nArquivos em raw/ ({len(raw_files)}):")
        for f in raw_files[-5:]:  # últimos 5
            print(f"  {f.name}")

    # Última entrada do changelog
    changelog = ativo / "changelog.md"
    if changelog.exists():
        linhas = changelog.read_text(encoding="utf-8").splitlines()
        print(f"\nÚltima entrada do changelog:")
        em_entrada = False
        for linha in linhas:
            if linha.startswith("## "):
                if em_entrada:
                    break
                em_entrada = True
            if em_entrada:
                print(f"  {linha}")

    print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")


def cmd_destilar():
    """Destila raw/ e atualiza changelog.md via claude CLI."""
    ativo = projeto_ativo()
    if not ativo:
        print("SA-IA: nenhum projeto ativo para destilar.")
        sys.exit(0)

    raw_dir = ativo / "raw"
    if not raw_dir.exists() or not any(raw_dir.iterdir()):
        print(f"SA-IA: nenhum arquivo em raw/ para destilar em {ativo.name}.")
        sys.exit(0)

    # Monta contexto
    ancora_proj = ler_arquivo(ativo / "ANCORA_PROJETO.md")
    perfil = ler_arquivo(ativo / "perfil-destilacao.md")
    changelog_atual = ler_arquivo(ativo / "changelog.md", max_linhas=60)

    raw_conteudo = ""
    for f in sorted(raw_dir.iterdir()):
        if f.suffix == ".md":
            raw_conteudo += f"\n\n### {f.name}\n{f.read_text(encoding='utf-8')}"

    if not raw_conteudo.strip():
        print("SA-IA: sem conteúdo em raw/ para destilar.")
        sys.exit(0)

    prompt = f"""Você é um assistente de contexto para projetos de consultoria.

PERFIL DO PROJETO:
{ancora_proj}

CRITÉRIOS DE DESTILAÇÃO:
{perfil}

CHANGELOG ATUAL (últimas entradas):
{changelog_atual}

NOVOS REGISTROS EM raw/:
{raw_conteudo}

INSTRUÇÃO:
Com base nos critérios do perfil, extraia APENAS os pontos novos relevantes que ainda não estão no changelog.
Não repita o que já está registrado.

Formate a saída como uma nova seção do changelog:

## {hoje()} — [título curto descrevendo o que aconteceu]

**Decisões tomadas**
- [máximo 3 bullets, apenas se houver]

**Marcos alcançados**
- [máximo 3 bullets, apenas se houver]

**Bloqueios identificados**
- [máximo 3 bullets, apenas se houver]

**Próximos passos**
- [máximo 3 bullets com data e responsável, apenas se houver]

Se não há conteúdo relevante para uma seção, omita a seção.
Total máximo: 10 bullets.
Retorne APENAS o bloco markdown da nova seção, sem explicações."""

    # Salva prompt em arquivo temporário e chama claude -p
    prompt_file = ativo / "raw" / ".prompt-destilacao.tmp"
    atomic_write(prompt_file, prompt)

    print(f"SA-IA: destilando {ativo.name}...")

    import subprocess
    result = subprocess.run(
        ["claude", "-p", "--output-format", "text"],
        input=prompt,
        capture_output=True,
        text=True,
        encoding="utf-8"
    )

    # Remove arquivo temporário
    if prompt_file.exists():
        prompt_file.unlink()

    if result.returncode != 0:
        print(f"SA-IA: erro ao chamar claude CLI.")
        print(result.stderr)
        sys.exit(1)

    nova_entrada = result.stdout.strip()
    if not nova_entrada:
        print("SA-IA: destilação retornou vazia.")
        sys.exit(0)

    # Prepend no changelog (entrada mais recente no topo)
    changelog_path = ativo / "changelog.md"
    changelog_existente = ler_arquivo(changelog_path)

    # Separa o frontmatter do conteúdo
    if changelog_existente.startswith("---"):
        partes = changelog_existente.split("---", 2)
        frontmatter = f"---{partes[1]}---"
        corpo = partes[2].strip() if len(partes) > 2 else ""
    else:
        frontmatter = ""
        corpo = changelog_existente.strip()

    # Atualiza data no frontmatter
    frontmatter = re.sub(
        r"ultima-atualizacao: .+",
        f"ultima-atualizacao: {hoje()}",
        frontmatter
    )

    novo_changelog = f"{frontmatter}\n\n{nova_entrada}\n\n---\n\n{corpo}".strip()

    # Compressão se ultrapassar ~2000 tokens (~8000 chars)
    if len(novo_changelog) > 8000:
        linhas = novo_changelog.splitlines()
        novo_changelog = "\n".join(linhas[:200])
        novo_changelog += "\n\n---\n*Entradas mais antigas comprimidas automaticamente.*"

    atomic_write(changelog_path, novo_changelog)
    print(f"SA-IA: changelog.md atualizado em projetos/{ativo.name}/")

    # Faz git commit automático se estiver num repo git
    if (ROOT / ".git").exists():
        subprocess.run(
            ["git", "add", str(changelog_path)],
            cwd=ROOT, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m",
             f"chore(sa-ia): destila {ativo.name} {hoje()}"],
            cwd=ROOT, capture_output=True
        )


# ── Entry point ───────────────────────────────────────────────────────────────

COMANDOS = {
    "setup": cmd_setup,
    "create": cmd_create,
    "status": cmd_status,
    "destilar": cmd_destilar,
}

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMANDOS:
        print(__doc__)
        sys.exit(0)
    COMANDOS[sys.argv[1]]()

if __name__ == "__main__":
    main()
