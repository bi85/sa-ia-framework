# SA-IA — Sistema Âncora para Inteligência Artificial
*Framework de contexto vivo para projetos de consultoria com IA*

---

## O que é o SA-IA

Um LLM não tem memória entre sessões. O que parece "memória" é sempre a mesma coisa: texto colocado no contexto antes da conversa começar.

O SA-IA resolve isso. Ele mantém um arquivo de contexto vivo por projeto, atualizado automaticamente com base no que acontece nas sessões de trabalho. Quando você abre uma nova sessão, o contexto já está injetado — sem repetição, sem reexplicação.

```
Princípio: A IA não tem estado. O contexto é o estado.
           Gerenciar a IA = gerenciar o que entra no contexto.
```

---

## Setup — Faça isso primeiro

> O Claude Code lê este arquivo automaticamente ao abrir uma sessão.
> Se for a primeira vez neste repositório, execute os passos abaixo antes de qualquer outra coisa.

### Detectar se é primeira vez

Verifique se existe o arquivo `ANCORA.md` preenchido com seu nome e objetivo:

```bash
cat ANCORA.md
```

Se estiver com os valores de exemplo (`[Seu Nome]`, `[Seu objetivo]`), é primeira vez. Siga os passos abaixo.

### Passo 1 — Instalar dependência

```bash
pip install anthropic pyyaml
```

### Passo 2 — Preencher sua âncora global

Abra `ANCORA.md` e substitua os campos marcados com `[...]`. Esta é sua identidade permanente no sistema — leva 5 minutos.

### Passo 3 — Registrar os hooks no Claude Code

```bash
python sa-ia.py setup
```

Este comando copia os hooks para `.claude/hooks/` e registra em `.claude/settings.json`. Só precisa rodar uma vez por máquina.

### Passo 4 — Criar seu primeiro projeto

```bash
python sa-ia.py create
```

O comando pergunta nome, cliente e objetivo do projeto e cria a estrutura de arquivos em `projetos/`.

### Passo 5 — Trabalhar

Abra o Claude Code normalmente. O contexto do projeto ativo já estará injetado no início de cada sessão.

---

## Como usar no dia a dia

### Registrar algo que aconteceu

Salve um arquivo em `projetos/[slug]/raw/` com o que aconteceu — reunião, decisão, entrega, problema. Formato livre, sem regras.

```
projetos/apollo-advisory/raw/reuniao-2026-07-12.md
```

O hook de encerramento destila automaticamente o que estiver em `raw/` e atualiza o `changelog.md`.

### Encerrar uma sessão

Diga ao Claude: **"encerra sessão"** ou **"fecha sessão"**.

O hook `stop` dispara, destila tudo que aconteceu e atualiza o `changelog.md` do projeto ativo.

### Criar um novo projeto

```bash
python sa-ia.py create
```

### Ver o contexto atual de um projeto

```bash
python sa-ia.py status
```

---

## Estrutura de arquivos

```
sa-ia/
├── CLAUDE.md                  ← este arquivo
├── ANCORA.md                  ← sua identidade global (você preenche)
├── sa-ia.py                   ← CLI do framework
├── .claude/
│   ├── settings.json          ← hooks registrados
│   └── hooks/
│       ├── session-start.sh   ← injeta contexto no início da sessão
│       └── stop.sh            ← destila e atualiza changelog ao encerrar
└── projetos/
    └── [slug-do-projeto]/
        ├── ANCORA_PROJETO.md  ← âncora do projeto (gerada pelo create)
        ├── perfil-destilacao.md ← critérios do que entra no changelog
        ├── tasks.md           ← tarefas do projeto
        ├── changelog.md       ← contexto comprimido (atualizado pelo hook)
        └── raw/               ← registros brutos (você escreve aqui)
```

---

## Regras que o Claude deve seguir neste repositório

1. **Nunca sobrescrever um arquivo sem ler o estado atual primeiro** — especialmente `changelog.md` e `tasks.md`.

2. **Ao encerrar sessão**, sempre executar o hook `stop.sh` ou chamar `python sa-ia.py destilar` antes de fechar.

3. **Arquivos em `raw/` são de entrada** — o Claude pode criar arquivos lá para registrar o que aconteceu na sessão, mas nunca editar arquivos existentes em `raw/`.

4. **`ANCORA.md` e `ANCORA_PROJETO.md` são permanentes** — só editar se o usuário pedir explicitamente. São a bússola do sistema.

5. **`changelog.md` é gerado automaticamente** — nunca editar manualmente. Se precisar corrigir algo, registre em `raw/` e rode a destilação novamente.

6. **Projeto ativo** = o projeto cujo `ANCORA_PROJETO.md` tem `status: ativo`. Se houver mais de um ativo, perguntar qual usar antes de começar.

---

## Contexto injetado automaticamente

O hook `session-start.sh` injeta no início de cada sessão:

- Conteúdo de `ANCORA.md` (sua identidade global)
- Conteúdo de `ANCORA_PROJETO.md` do projeto ativo
- Últimas 3 entradas do `changelog.md` do projeto ativo
- Lista de tarefas abertas do `tasks.md`

Você não precisa reexplicar nada. O contexto já está lá.

---

## Compatibilidade

Funciona com qualquer ferramenta que leia `CLAUDE.md`:

- **Claude Code** (CLI) — suporte completo com hooks automáticos
- **Codex** — lê o `CLAUDE.md` como contexto de projeto
- **VS Code + extensão Claude** — lê o `CLAUDE.md` como instruções do workspace
- **Cursor, Windsurf** — compatível via `CLAUDE.md` ou `.cursorrules`

Os hooks automáticos (`session-start`, `stop`) funcionam apenas no Claude Code CLI. Nos outros ambientes, rode manualmente:

```bash
python sa-ia.py status    # ver contexto atual
python sa-ia.py destilar  # atualizar changelog manualmente
```

---

*SA-IA — Sistema Âncora para Inteligência Artificial*
*Desenvolvido por Márcio Santos — ODDATA / Trium Mind Advisory*
