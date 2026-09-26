[//]: # (Gerado pelo SA-IA a partir de AGENT-CONTEXT.md — para Claude Code)
[//]: # (Para editar o framework, edite AGENT-CONTEXT.md e rode: python sa-ia.py sync-context)

# SA-IA — Sistema Âncora para Inteligência Artificial
*Fonte de contexto universal — válida para qualquer agente de IA*

---

## O que é o SA-IA

Um LLM não tem memória entre sessões. O que parece "memória" é sempre a mesma coisa: texto colocado no contexto antes da conversa começar.

O SA-IA resolve isso. Ele mantém arquivos de contexto vivos, atualizados automaticamente com base no que acontece nas sessões de trabalho. Quando você abre uma nova sessão, o contexto já está injetado — sem repetição, sem reexplicação.

```
Princípio: A IA não tem estado. O contexto é o estado.
           Gerenciar a IA = gerenciar o que entra no contexto.
```

---

## Setup — Faça isso primeiro

> Se for a primeira vez neste repositório, siga os passos abaixo antes de qualquer outra coisa.

### Passo 1 — Definir seu perfil

Responda: **você é um profissional solo ou representa uma empresa (ou mais de uma)?**

**Profissional solo:**
```bash
python sa-ia.py setup --perfil solo
```
Cria: `00-anchor/owner.md` · `02-projects/` · `04-context/`

**Empresa ou múltiplas empresas:**
```bash
python sa-ia.py setup --perfil empresa
```
Cria: `00-anchor/owner.md` · `00-anchor/[empresa]/` · `01-departments/[empresa]/` · `02-projects/` · `04-context/`

Se não souber ainda, use `--perfil solo` — você pode adicionar empresas e departamentos depois com `python sa-ia.py add-company`.

### Passo 2 — Preencher sua âncora

Abra `00-anchor/owner.md` e preencha os campos marcados com `[...]`. Leva 5 minutos e é feito uma única vez.

### Passo 3 — Criar o primeiro projeto

```bash
python sa-ia.py create
```

### Passo 4 — Trabalhar

Abra o Claude Code normalmente. O contexto já estará injetado no início de cada sessão.

---

## Estrutura de arquivos

### Perfil solo

```
sa-ia/
├── AGENT-CONTEXT.md         ← fonte universal (edite aqui)
├── CLAUDE.md                ← gerado — Claude Code
├── AGENTS.md                ← gerado — OpenAI Codex
├── .cursorrules             ← gerado — Cursor / Windsurf
├── sa-ia.py
├── .claude/
│   ├── settings.json
│   └── hooks/
│       ├── session-start.sh     ← injeta contexto no início da sessão
│       ├── post-write.sh        ← atualiza active-context.md após escrita
│       └── validate-anchor.sh   ← bloqueia projeto sem vínculo com âncora
├── 00-anchor/
│   └── owner.md                 ← sua identidade e objetivos (você preenche)
├── 02-projects/
│   └── [slug]/                  ← uma pasta por projeto
└── 04-context/
    ├── active-context.md        ← gerado automaticamente
    └── drift-report.md          ← gerado automaticamente
```

### Perfil empresa

```
sa-ia/
├── 00-anchor/
│   ├── owner.md                 ← âncora raiz (quem usa o sistema)
│   └── [empresa]/
│       └── empresa.md           ← missão e objetivos da empresa
├── 01-departments/
│   └── [empresa]/
│       └── [departamento].md    ← um arquivo por departamento
├── 02-projects/
│   └── [slug]/                  ← vinculado a empresa + departamento no frontmatter
└── 04-context/
    ├── active-context.md
    └── drift-report.md
```

---

## Como usar no dia a dia

### Registrar o que aconteceu

Salve um arquivo em `02-projects/[slug]/raw/` com o que aconteceu — reunião, decisão, entrega. Formato livre.

```
02-projects/apollo-advisory/raw/reuniao-2026-07-12.md
```

### Encerrar uma sessão

Diga: **"encerra sessão"** ou **"fecha sessão"**.

O hook `stop` destila tudo em `raw/` e atualiza o `active-context.md`.

### Criar projeto

```bash
python sa-ia.py create
```

### Adicionar empresa (perfil empresa)

```bash
python sa-ia.py add-company
```

### Ver contexto atual

```bash
python sa-ia.py status
```

---

## Regras para o agente

1. **Nunca sobrescrever arquivo sem ler o estado atual primeiro** — especialmente `active-context.md` e arquivos de projeto.

2. **Ao encerrar sessão**, sempre executar o hook stop ou `python sa-ia.py destilar` antes de fechar.

3. **`04-context/` é gerado automaticamente** — nunca editar manualmente.

4. **`00-anchor/` é permanente** — só editar se o usuário pedir explicitamente.

5. **Todo projeto deve ter `anchor` no frontmatter** — vinculado a `owner`, a uma empresa ou a um departamento. Se não tiver, o hook `validate-anchor.sh` bloqueia e pede correção.

6. **Projeto ativo** = pasta em `02-projects/` com `status: ativo` no frontmatter de `ancora.md`. Se houver mais de um, perguntar qual usar antes de começar a sessão.

---

## Contexto injetado automaticamente

O hook `session-start.sh` injeta no início de cada sessão, nesta ordem:

1. `00-anchor/owner.md`
2. `00-anchor/[empresa]/empresa.md` (se existir empresa ativa)
3. `01-departments/[empresa]/[dept].md` (se existir departamento do projeto ativo)
4. `02-projects/[slug]/ancora.md` do projeto ativo
5. Últimas entradas do `04-context/active-context.md`

---

## Compatibilidade

| Ferramenta | Hooks automáticos | Arquivo de contexto |
|---|---|---|
| Claude Code | ✅ completo | `CLAUDE.md` |
| OpenAI Codex | ✅ completo | `AGENTS.md` |
| Cursor | ❌ manual | `.cursorrules` |
| Windsurf | ❌ manual | `.windsurfrules` |
| Gemini CLI | ❌ manual | `GEMINI.md` |
| Qualquer LLM | ❌ manual | `AGENT-CONTEXT.md` |

Nos ambientes sem hooks, rode manualmente ao encerrar a sessão:
```bash
python sa-ia.py destilar
```

---

*SA-IA — Sistema Âncora para Inteligência Artificial*
*github.com/bi85/sa-ia*
