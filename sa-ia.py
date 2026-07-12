#!/usr/bin/env python3
"""
SA-IA — Sistema Âncora para Inteligência Artificial
CLI principal do framework.

Uso:
  python sa-ia.py setup [--perfil solo|empresa]  — configura estrutura e hooks
  python sa-ia.py add-company                    — adiciona empresa (perfil empresa)
  python sa-ia.py create                         — cria novo projeto
  python sa-ia.py status                         — exibe contexto atual
  python sa-ia.py destilar                       — atualiza active-context.md
"""

import sys
import os
import json
import shutil
import re
import subprocess
from datetime import datetime
from pathlib import Path

# ── Paths base ────────────────────────────────────────────────────────────────

ROOT        = Path(__file__).parent
ANCHOR_DIR  = ROOT / "00-anchor"
DEPT_DIR    = ROOT / "01-departments"
PROJ_DIR    = ROOT / "02-projects"
CTX_DIR     = ROOT / "04-context"
CLAUDE_DIR  = ROOT / ".claude"
HOOKS_DIR   = CLAUDE_DIR / "hooks"
SETTINGS    = CLAUDE_DIR / "settings.json"
OWNER_FILE  = ANCHOR_DIR / "owner.md"

# ── Templates ─────────────────────────────────────────────────────────────────

OWNER_TEMPLATE = """\
# Âncora — Owner
> Preencha este arquivo no setup. É sua identidade permanente no sistema.
> O Claude injeta este contexto automaticamente no início de cada sessão.

---

## Identidade

**Nome:** [Seu Nome]
**Posicionamento:** [Como você se descreve profissionalmente em uma linha]
**Localização:** [Cidade, Estado]

---

## Objetivo Central

[O objetivo de mais alto nível que governa tudo que você faz. Uma frase.]

---

## Pilares

1. [Pilar 1] — [descrição em uma linha]
2. [Pilar 2] — [descrição em uma linha]
3. [Pilar 3] — [descrição em uma linha]

---

## Regras

- [Regra 1]
- [Regra 2]

---

## Restrições ativas

- [Restrição 1]
- [Restrição 2]

---

## Contexto atual

**Foco desta semana:** [o que mais importa agora]
**Projetos quentes:** [quais merecem atenção prioritária]
**Situação geral:** [ex: expansão / estável / apertado]

---

*Última atualização: {data}*
"""

EMPRESA_TEMPLATE = """\
# Âncora — {nome}
> Âncora da empresa. Edite quando missão ou objetivos mudarem.

---

## Missão

[O que a empresa faz e para quem. Duas ou três frases.]

---

## Objetivo atual

[O objetivo estratégico desta empresa agora. Uma frase.]

---

## Departamentos

{departamentos}

---

## Regras da empresa

- [Regra 1]
- [Regra 2]

---

*Última atualização: {data}*
"""

DEPT_TEMPLATE = """\
# Âncora — {empresa} / {nome}
> Âncora do departamento. Edite quando foco ou responsável mudar.

---

## Responsável

[Nome do responsável pelo departamento]

---

## Objetivo do departamento

[O que este departamento entrega. Uma frase.]

---

## Projetos ativos

[Lista dos projetos ativos deste departamento]

---

*Última atualização: {data}*
"""

PROJ_README_TEMPLATE = """\
# {nome}

> Índice do projeto. Gerado automaticamente — edite com cuidado.

| Campo | Valor |
|-------|-------|
| **Âncora** | {anchor} |
| **Status** | ativo |
| **Criado** | {data} |

## Arquivos

- [`ancora.md`](ancora.md) — objetivo, escopo e stakeholders
- [`tasks.md`](tasks.md) — tarefas abertas e concluídas
- [`changelog.md`](changelog.md) — contexto destilado (não edite)
- [`raw/`](raw/) — registros brutos: reuniões, decisões, transcrições

## Como registrar algo

Crie um arquivo em `raw/` com o que aconteceu:

```
raw/reuniao-{data}.md
raw/decisao-{data}.md
raw/entrega-{data}.md
```

Formato livre — escreva como quiser. O hook destila automaticamente ao encerrar a sessão.
"""

PROJ_ANCORA_TEMPLATE = """\
---
title: {nome}
sa-ia-type: ancora-projeto
slug: {slug}
anchor: {anchor}
status: ativo
criado: {data}
---

# {nome}

## Objetivo

{objetivo}

## Escopo

[O que este projeto inclui — seja específico]

## Fora do escopo

[O que explicitamente não faz parte deste projeto]

## Stakeholders

| Nome | Papel |
|------|-------|
| — | — |

## Critério de sucesso

[Como você sabe que o projeto foi concluído com sucesso]
"""

PERFIL_TEMPLATE = """\
# Perfil de Destilação — {nome}

## O que SEMPRE deve entrar no changelog

- Decisões que alteram escopo, prazo ou orçamento
- Marcos: contratos assinados, entregas aceitas, metas atingidas
- Bloqueios que dependem de terceiros
- Mudanças de responsabilidade
- Próximos passos com data e responsável

## O que NUNCA deve entrar

- Detalhes operacionais já resolvidos
- Repetição do que já está registrado
- Perguntas sem resposta

## Limite

- Máximo 10 bullets por atualização
- Se changelog ultrapassar 2000 tokens: comprimir entrada mais antiga em 1 parágrafo
"""

TASKS_TEMPLATE = """\
---
sa-ia-type: tasks
projeto: {slug}
atualizado: {data}
---

# Tarefas — {nome}

## Em andamento

- [ ] #task-001 [Primeira tarefa]

## A fazer

- [ ] #task-002 [Próxima tarefa]

## Concluídas

## Bloqueadas
"""

CHANGELOG_TEMPLATE = """\
---
sa-ia-type: changelog
projeto: {slug}
ultima-atualizacao: {data}
---

# Changelog — {nome}

> Contexto destilado automaticamente. Não edite manualmente.

## {data} — Início do projeto

**Marcos alcançados**
- Projeto criado com estrutura SA-IA

**Próximos passos**
- Preencher escopo em `ancora.md`
- Adicionar primeiras tarefas em `tasks.md`
- Criar primeiro registro em `raw/` após próxima reunião
"""

ACTIVE_CTX_TEMPLATE = """\
---
sa-ia-type: active-context
gerado: {data}
---

# Contexto Ativo — {data}

> Gerado automaticamente pelo SA-IA. Não edite manualmente.

## Owner

{owner_resumo}

## Projeto ativo

{projeto_resumo}

## Próximos passos

{proximos_passos}
"""

HOOK_SESSION_START = """\
#!/usr/bin/env bash
# SA-IA — session-start
# Injeta contexto no início de cada sessão.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo ""
echo "━━━ SA-IA ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. Owner
if [ -f "$ROOT/00-anchor/owner.md" ]; then
  echo ""
  cat "$ROOT/00-anchor/owner.md"
fi

# 2. Projeto ativo
PROJ_ATIVO=""
for f in "$ROOT/02-projects/"*.md; do
  [ -f "$f" ] || continue
  if grep -q "status: ativo" "$f"; then
    PROJ_ATIVO="$f"
    break
  fi
done

if [ -n "$PROJ_ATIVO" ]; then
  # Lê empresa e departamento do frontmatter
  ANCHOR=$(grep "^anchor:" "$PROJ_ATIVO" | sed 's/anchor: //')

  # Empresa (se anchor aponta para empresa/dept)
  EMPRESA=$(echo "$ANCHOR" | cut -d'/' -f1)
  DEPT=$(echo "$ANCHOR" | cut -d'/' -f2)

  if [ -f "$ROOT/00-anchor/$EMPRESA/empresa.md" ]; then
    echo ""
    echo "━━━ EMPRESA ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    cat "$ROOT/00-anchor/$EMPRESA/empresa.md"
  fi

  if [ -n "$DEPT" ] && [ -f "$ROOT/01-departments/$EMPRESA/$DEPT.md" ]; then
    echo ""
    echo "━━━ DEPARTAMENTO ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    cat "$ROOT/01-departments/$EMPRESA/$DEPT.md"
  fi

  echo ""
  echo "━━━ PROJETO ATIVO ━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  cat "$PROJ_ATIVO"
else
  echo ""
  echo "Nenhum projeto ativo. Use: python sa-ia.py create"
fi

# 3. Contexto atual
if [ -f "$ROOT/04-context/active-context.md" ]; then
  echo ""
  echo "━━━ CONTEXTO ATIVO ━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  head -60 "$ROOT/04-context/active-context.md"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
"""

HOOK_POST_WRITE = """\
#!/usr/bin/env bash
# SA-IA — post-write
# Atualiza active-context.md após qualquer escrita em 02-projects/.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Só dispara se o arquivo escrito for um projeto
if [[ "$CLAUDE_TOOL_RESULT" == *"02-projects"* ]]; then
  python "$ROOT/sa-ia.py" destilar --silencioso
fi
"""

HOOK_VALIDATE = """\
#!/usr/bin/env bash
# SA-IA — validate-anchor
# Bloqueia commit se projeto não tiver anchor definido.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

for f in "$ROOT/02-projects/"*.md; do
  [ -f "$f" ] || continue
  if ! grep -q "^anchor:" "$f"; then
    echo "SA-IA: projeto sem âncora — $(basename $f)"
    echo "Adicione 'anchor: owner' ou 'anchor: empresa/departamento' no frontmatter."
    exit 1
  fi
done

exit 0
"""

# ── Helpers ───────────────────────────────────────────────────────────────────

def slugify(text):
    text = text.lower().strip()
    for src, dst in [('àáâãä','a'),('èéêë','e'),('ìíîï','i'),('òóôõö','o'),('ùúûü','u'),('ç','c')]:
        for c in src:
            text = text.replace(c, dst)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'\s+', '-', text)
    return text

def hoje():
    return datetime.now().strftime("%Y-%m-%d")

def atomic_write(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)

def projeto_ativo():
    """Retorna o Path da pasta do projeto ativo, ou None."""
    if not PROJ_DIR.exists():
        return None
    for proj_dir in sorted(p for p in PROJ_DIR.iterdir() if p.is_dir()):
        ancora = proj_dir / "ancora.md"
        if ancora.exists() and "status: ativo" in ancora.read_text(encoding="utf-8"):
            return proj_dir
    return None

def listar_empresas():
    if not ANCHOR_DIR.exists():
        return []
    return [d for d in ANCHOR_DIR.iterdir() if d.is_dir()]

def criar_hooks():
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    for nome, conteudo in [
        ("session-start.sh", HOOK_SESSION_START),
        ("post-write.sh",    HOOK_POST_WRITE),
        ("validate-anchor.sh", HOOK_VALIDATE),
    ]:
        path = HOOKS_DIR / nome
        atomic_write(path, conteudo)
        path.chmod(0o755)
        print(f"  ✓ {nome}")

def registrar_settings():
    CLAUDE_DIR.mkdir(exist_ok=True)
    settings = {}
    if SETTINGS.exists():
        try:
            settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass

    hook_cmd = lambda nome: {"type": "command", "command": f"bash \"{HOOKS_DIR / nome}\""}

    settings["hooks"] = {
        "UserPromptSubmit": [{"matcher": "", "hooks": [hook_cmd("session-start.sh")]}],
        "PostToolUse":      [{"matcher": "Write|Edit", "hooks": [hook_cmd("post-write.sh")]}],
        "Stop":             [{"matcher": "", "hooks": [hook_cmd("validate-anchor.sh")]}],
    }

    atomic_write(SETTINGS, json.dumps(settings, indent=2, ensure_ascii=False))
    print(f"  ✓ .claude/settings.json")

# ── Comandos ──────────────────────────────────────────────────────────────────

def cmd_setup():
    perfil = "solo"
    if "--perfil" in sys.argv:
        idx = sys.argv.index("--perfil")
        if idx + 1 < len(sys.argv):
            perfil = sys.argv[idx + 1]

    if perfil not in ("solo", "empresa"):
        print("Perfil inválido. Use: --perfil solo  ou  --perfil empresa")
        sys.exit(1)

    print(f"\nSA-IA — Setup ({perfil})\n")

    # Estrutura base
    ANCHOR_DIR.mkdir(exist_ok=True)
    PROJ_DIR.mkdir(exist_ok=True)
    CTX_DIR.mkdir(exist_ok=True)

    # owner.md
    if not OWNER_FILE.exists():
        atomic_write(OWNER_FILE, OWNER_TEMPLATE.format(data=hoje()))
        print(f"  ✓ 00-anchor/owner.md")
    else:
        print(f"  · 00-anchor/owner.md (já existe)")

    # Estrutura empresa
    if perfil == "empresa":
        DEPT_DIR.mkdir(exist_ok=True)
        print(f"  ✓ 01-departments/")
        print(f"\n  Próximo passo: python sa-ia.py add-company")

    # Hooks
    print(f"\nRegistrando hooks:")
    criar_hooks()
    registrar_settings()

    # .gitignore
    gitignore = ROOT / ".gitignore"
    if not gitignore.exists():
        atomic_write(gitignore, "*.tmp\n__pycache__/\n.claude/settings.json\n")
        print(f"  ✓ .gitignore")

    print(f"""
Setup concluído.

Próximos passos:
  1. Preencha 00-anchor/owner.md com sua identidade
  2. python sa-ia.py create  (criar primeiro projeto)
  3. claude  (abrir Claude Code — contexto já injetado)
""")


def cmd_add_company():
    print("\nSA-IA — Adicionar Empresa\n")

    nome = input("Nome da empresa: ").strip()
    if not nome:
        print("Nome obrigatório.")
        sys.exit(1)

    slug = slugify(nome)
    empresa_dir = ANCHOR_DIR / slug
    dept_empresa = DEPT_DIR / slug

    empresa_dir.mkdir(parents=True, exist_ok=True)
    dept_empresa.mkdir(parents=True, exist_ok=True)

    empresa_file = empresa_dir / "empresa.md"
    if not empresa_file.exists():
        atomic_write(empresa_file, EMPRESA_TEMPLATE.format(
            nome=nome, departamentos="[liste os departamentos aqui]", data=hoje()
        ))

    # Departamentos opcionais
    print(f"\nEmpresa '{nome}' criada.")
    adicionar = input("Deseja adicionar departamentos agora? [s/N]: ").strip().lower()

    while adicionar == "s":
        dept_nome = input("  Nome do departamento: ").strip()
        if dept_nome:
            dept_slug = slugify(dept_nome)
            dept_file = dept_empresa / f"{dept_slug}.md"
            if not dept_file.exists():
                atomic_write(dept_file, DEPT_TEMPLATE.format(
                    empresa=nome, nome=dept_nome, data=hoje()
                ))
            print(f"  ✓ 01-departments/{slug}/{dept_slug}.md")
        adicionar = input("Adicionar outro departamento? [s/N]: ").strip().lower()

    print(f"\n✓ Estrutura criada em:")
    print(f"  00-anchor/{slug}/empresa.md")
    if any(dept_empresa.iterdir()):
        for f in dept_empresa.iterdir():
            print(f"  01-departments/{slug}/{f.name}")


def cmd_create():
    print("\nSA-IA — Novo Projeto\n")

    nome = input("Nome do projeto: ").strip()
    if not nome:
        print("Nome obrigatório.")
        sys.exit(1)

    slug = slugify(nome)
    proj_file = PROJ_DIR / f"{slug}.md"

    if proj_file.exists():
        print(f"Projeto '{slug}' já existe.")
        sys.exit(1)

    objetivo = input("Objetivo em uma frase: ").strip() or "A definir"

    # Determina anchor
    empresas = listar_empresas()
    anchor = "owner"

    if empresas:
        print(f"\nEsta é uma âncora de:")
        print(f"  0. Owner (pessoal / sem empresa)")
        for i, e in enumerate(empresas, 1):
            print(f"  {i}. {e.name}")
        escolha = input("Escolha [0]: ").strip()

        if escolha.isdigit() and 1 <= int(escolha) <= len(empresas):
            empresa = empresas[int(escolha) - 1]
            anchor = empresa.name

            # Departamento opcional
            depts = list((DEPT_DIR / empresa.name).glob("*.md")) if (DEPT_DIR / empresa.name).exists() else []
            if depts:
                print(f"\nDepartamento (opcional):")
                print(f"  0. Nenhum")
                for i, d in enumerate(depts, 1):
                    print(f"  {i}. {d.stem}")
                dept_escolha = input("Escolha [0]: ").strip()
                if dept_escolha.isdigit() and 1 <= int(dept_escolha) <= len(depts):
                    anchor = f"{empresa.name}/{depts[int(dept_escolha)-1].stem}"

    # Pausa projetos ativos
    for proj_pasta in PROJ_DIR.iterdir():
        if not proj_pasta.is_dir():
            continue
        ancora_file = proj_pasta / "ancora.md"
        if ancora_file.exists():
            conteudo = ancora_file.read_text(encoding="utf-8")
            if "status: ativo" in conteudo:
                atomic_write(ancora_file, conteudo.replace("status: ativo", "status: pausado"))

    # Cria estrutura de pasta do projeto
    proj_dir = PROJ_DIR / slug
    proj_dir.mkdir(parents=True, exist_ok=True)
    (proj_dir / "raw").mkdir(exist_ok=True)

    ctx = dict(nome=nome, slug=slug, anchor=anchor, objetivo=objetivo, data=hoje())

    atomic_write(proj_dir / "README.md",
                 PROJ_README_TEMPLATE.format(**ctx))
    atomic_write(proj_dir / "ancora.md",
                 PROJ_ANCORA_TEMPLATE.format(**ctx))
    atomic_write(proj_dir / "perfil-destilacao.md",
                 PERFIL_TEMPLATE.format(**ctx))
    atomic_write(proj_dir / "tasks.md",
                 TASKS_TEMPLATE.format(**ctx))
    atomic_write(proj_dir / "changelog.md",
                 CHANGELOG_TEMPLATE.format(**ctx))

    print(f"\n✓ Projeto criado: 02-projects/{slug}/")
    print(f"  ├── README.md")
    print(f"  ├── ancora.md       (âncora: {anchor})")
    print(f"  ├── perfil-destilacao.md")
    print(f"  ├── tasks.md")
    print(f"  ├── changelog.md")
    print(f"  └── raw/")


def cmd_status():
    print(f"\n━━━ SA-IA STATUS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    ativo = projeto_ativo()
    if not ativo:
        print("Nenhum projeto ativo. Use: python sa-ia.py create\n")
        return

    print(f"Projeto ativo: {ativo.name}\n")

    # Tarefas abertas
    tasks = ativo / "tasks.md"
    if tasks.exists():
        abertas = [l for l in tasks.read_text(encoding="utf-8").splitlines()
                   if l.startswith("- [ ]")]
        if abertas:
            print(f"Tarefas abertas ({len(abertas)}):")
            for t in abertas:
                print(f"  {t}")

    # Raw pendente
    raw_dir = ativo / "raw"
    if raw_dir.exists():
        raw = sorted(raw_dir.glob("*.md"))
        if raw:
            print(f"\nRegistros em raw/ ({len(raw)}):")
            for f in raw[-5:]:
                print(f"  {f.name}")

    print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")


def cmd_destilar():
    silencioso = "--silencioso" in sys.argv

    ativo = projeto_ativo()
    if not ativo:
        if not silencioso:
            print("SA-IA: nenhum projeto ativo.")
        return

    raw_dir = ativo / "raw"
    if not raw_dir.exists() or not any(raw_dir.glob("*.md")):
        if not silencioso:
            print(f"SA-IA: nenhum registro em raw/ para {ativo.name}.")
        return

    # Monta contexto
    owner = OWNER_FILE.read_text(encoding="utf-8") if OWNER_FILE.exists() else ""
    proj = (ativo / "ancora.md").read_text(encoding="utf-8") if (ativo / "ancora.md").exists() else ""
    perfil = (ativo / "perfil-destilacao.md").read_text(encoding="utf-8") if (ativo / "perfil-destilacao.md").exists() else ""

    raw_conteudo = ""
    for f in sorted(raw_dir.glob("*.md")):
        raw_conteudo += f"\n\n### {f.name}\n{f.read_text(encoding='utf-8')}"

    prompt = f"""Você é um assistente de contexto para projetos.

OWNER (quem usa o sistema):
{owner[:1000]}

PROJETO ATIVO:
{proj[:1000]}

CRITÉRIOS DE DESTILAÇÃO:
{perfil[:500]}

REGISTROS NOVOS:
{raw_conteudo[:3000]}

INSTRUÇÃO:
Extraia os pontos mais relevantes dos registros novos e atualize o contexto ativo.
Formate como markdown com estas seções (omita as que não tiverem conteúdo):

## Resumo do projeto
[2-3 frases sobre o estado atual]

## Próximos passos
- [ ] [ação concreta com responsável se souber]

## Decisões tomadas
- [bullet por decisão relevante]

## Bloqueios
- [bullet por bloqueio identificado]

Máximo 10 bullets no total. Seja direto e específico."""

    if not silencioso:
        print(f"SA-IA: destilando {ativo.stem}...")

    result = subprocess.run(
        ["claude", "-p", "--output-format", "text"],
        input=prompt, capture_output=True, text=True, encoding="utf-8"
    )

    if result.returncode != 0:
        if not silencioso:
            print(f"SA-IA: erro ao chamar claude CLI.\n{result.stderr}")
        return

    conteudo_novo = result.stdout.strip()
    if not conteudo_novo:
        return

    # Prepend no changelog do projeto
    changelog_path = ativo / "changelog.md"
    changelog_existente = changelog_path.read_text(encoding="utf-8") if changelog_path.exists() else ""

    if changelog_existente.startswith("---"):
        partes = changelog_existente.split("---", 2)
        frontmatter = f"---{partes[1]}---"
        corpo = partes[2].strip() if len(partes) > 2 else ""
    else:
        frontmatter = ""
        corpo = changelog_existente.strip()

    frontmatter = re.sub(r"ultima-atualizacao: .+", f"ultima-atualizacao: {hoje()}", frontmatter)
    novo_changelog = f"{frontmatter}\n\n{conteudo_novo}\n\n---\n\n{corpo}".strip()

    if len(novo_changelog) > 8000:
        novo_changelog = "\n".join(novo_changelog.splitlines()[:200])
        novo_changelog += "\n\n---\n*Entradas antigas comprimidas automaticamente.*"

    atomic_write(changelog_path, novo_changelog)

    # Atualiza active-context.md
    owner_linha = next((l for l in owner.splitlines() if l.startswith("**Nome")), "—")
    novo_ctx = ACTIVE_CTX_TEMPLATE.format(
        data=hoje(),
        owner_resumo=owner_linha,
        projeto_resumo=f"{ativo.name} — {conteudo_novo[:200]}",
        proximos_passos=conteudo_novo
    )
    atomic_write(CTX_DIR / "active-context.md", novo_ctx)

    # Git commit automático
    if (ROOT / ".git").exists():
        subprocess.run(["git", "add", str(changelog_path), str(CTX_DIR / "active-context.md")],
                       cwd=ROOT, capture_output=True)
        subprocess.run(["git", "commit", "-m",
                        f"chore(sa-ia): destila {ativo.name} {hoje()}"],
                       cwd=ROOT, capture_output=True)

    if not silencioso:
        print(f"SA-IA: changelog.md e active-context.md atualizados.")


# ── Entry point ───────────────────────────────────────────────────────────────

COMANDOS = {
    "setup":       cmd_setup,
    "add-company": cmd_add_company,
    "create":      cmd_create,
    "status":      cmd_status,
    "destilar":    cmd_destilar,
}

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMANDOS:
        print(__doc__)
        sys.exit(0)
    COMANDOS[sys.argv[1]]()

if __name__ == "__main__":
    main()
