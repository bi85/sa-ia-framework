# SA-IA — Sistema Âncora para Inteligência Artificial

> Um LLM não tem memória entre sessões. O SA-IA resolve isso.

---

## O problema

Toda vez que você abre uma nova sessão com um agente de IA, precisa reexplicar quem você é, o que está construindo, e onde parou. Isso quebra o fluxo, desperdiça tokens, e força você a ser o gerenciador de contexto da própria IA.

## A solução

O SA-IA mantém **âncoras** — arquivos de contexto vivos, atualizados automaticamente com base no que acontece nas sessões de trabalho. Quando você abre uma nova sessão, o agente já sabe onde parou.

```
Princípio: A IA não tem estado. O contexto é o estado.
           Gerenciar a IA = gerenciar o que entra no contexto.
```

---

## Quickstart

```bash
git clone https://github.com/bi85/sa-ia
cd sa-ia
python sa-ia.py setup --perfil solo
```

Preencha `00-anchor/owner.md` com sua identidade (5 minutos, feito uma vez), crie um projeto:

```bash
python sa-ia.py create
```

Abra seu agente. O contexto já estará injetado.

---

## Como funciona

```
00-anchor/owner.md          ← quem você é, seus objetivos, suas restrições
02-projects/[slug]/         ← objetivo, escopo, stakeholders do projeto
04-context/active-context.md ← destilado automático das últimas sessões
```

A cada encerramento de sessão, diga **"encerra sessão"**. O agente atualiza o contexto ativo com o que aconteceu. Na próxima sessão, ele já sabe onde parou — sem reexplicação.

---

## Compatibilidade

| Ferramenta | Hooks automáticos | Arquivo de contexto |
|---|---|---|
| Claude Code | ✅ | `CLAUDE.md` |
| OpenAI Codex | ✅ | `AGENTS.md` |
| Cursor | ❌ manual | `.cursorrules` |
| Windsurf | ❌ manual | `.windsurfrules` |
| Gemini CLI | ❌ manual | `GEMINI.md` |
| Qualquer LLM | ❌ manual | `AGENT-CONTEXT.md` |

Para ferramentas sem hooks, rode manualmente ao encerrar:
```bash
python sa-ia.py destilar
```

---

## Estrutura

```
sa-ia/
├── AGENT-CONTEXT.md     ← fonte universal (edite aqui)
├── CLAUDE.md            ← Claude Code
├── AGENTS.md            ← OpenAI Codex
├── .cursorrules         ← Cursor / Windsurf
├── sa-ia.py             ← CLI do framework
├── 00-anchor/
│   └── owner.md         ← SUA âncora (preencha no setup)
├── 02-projects/
│   └── [slug]/          ← um projeto por pasta
└── 04-context/
    └── active-context.md
```

---

## Comandos

```bash
python sa-ia.py setup [--perfil solo|empresa] [--ferramenta claude|codex|cursor|windsurf|gemini|manual]
python sa-ia.py create          # cria novo projeto
python sa-ia.py status          # exibe contexto atual
python sa-ia.py destilar        # atualiza active-context.md
python sa-ia.py add-company     # adiciona empresa (perfil empresa)
python sa-ia.py sync-context    # propaga AGENT-CONTEXT.md para todos os arquivos de ferramenta
```

---

## Perfis

**Solo** — profissional individual, sem separação por empresa:
```bash
python sa-ia.py setup --perfil solo
```

**Empresa** — quando você trabalha com uma ou mais empresas e quer separar contexto por organização:
```bash
python sa-ia.py setup --perfil empresa
```

---

## Derivação — o problema que o SA-IA resolve por baixo

Além do contexto perdido entre sessões, o SA-IA resolve um segundo problema: **deriva de intenção**.

Quando você trabalha com IA de forma intensa, tarefas surgem no meio de tarefas, projetos se multiplicam, e o agente começa a executar sem saber se aquilo é prioridade real ou distração.

A âncora (`owner.md`) funciona como constituição: toda tarefa nova é cruzada contra seus objetivos e restrições. Se não houver vínculo, o agente pergunta antes de executar.

---

## Licença

MIT — use livremente, contribuições bem-vindas.

---

*SA-IA — github.com/bi85/sa-ia*
