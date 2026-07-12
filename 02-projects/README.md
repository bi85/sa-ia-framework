# 02-projects

Um projeto por pasta. Cada pasta é autossuficiente — contém tudo sobre aquele projeto.

## O que fica aqui

- `[slug-do-projeto]/` — uma pasta por projeto, criada pelo `sa-ia.py create`

## Estrutura de cada projeto

```
02-projects/
└── nome-do-projeto/
    ├── README.md              ← índice do projeto (este arquivo, gerado automaticamente)
    ├── ancora.md              ← âncora do projeto: objetivo, escopo, stakeholders
    ├── perfil-destilacao.md   ← critérios do que entra no changelog
    ├── tasks.md               ← tarefas abertas, em andamento e concluídas
    ├── changelog.md           ← contexto destilado automaticamente (não edite)
    └── raw/                   ← registros brutos: reuniões, decisões, transcrições
        └── reuniao-YYYY-MM-DD.md
```

## Regras

- Nunca edite `changelog.md` manualmente — é gerado pelo hook
- Arquivos em `raw/` são de entrada: escreva livremente, sem formato obrigatório
- O frontmatter de `ancora.md` deve ter `anchor:` vinculando a `owner`, empresa ou departamento
- Só um projeto pode ter `status: ativo` por vez

## Como criar

```bash
python sa-ia.py create
```
