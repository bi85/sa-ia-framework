# 01-departments

Âncoras de departamentos. Opcional — só crie se sua operação tiver áreas distintas.

## O que fica aqui

- Um arquivo `.md` por departamento, organizado por empresa
- Cada arquivo define o responsável, objetivo e projetos ativos do departamento

## Regras

- Toda pasta aqui deve corresponder a uma empresa em `00-anchor/[empresa]/`
- Departamentos sem empresa não existem — vincule sempre
- Edite quando o responsável ou foco do departamento mudar

## Estrutura esperada

```
01-departments/
├── empresa-a/
│   ├── comercial.md
│   ├── operacoes.md
│   └── produto.md
└── empresa-b/
    ├── educacao.md
    └── consultoria.md
```

## Como criar

```bash
python sa-ia.py add-company
```
