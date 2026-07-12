# 04-context

Contexto gerado automaticamente pelos hooks. Nunca edite manualmente.

## O que fica aqui

- `active-context.md` — resumo destilado do projeto ativo, atualizado a cada sessão encerrada
- `drift-report.md` — relatório de deriva: projetos e tarefas sem vínculo com a âncora

## Como é gerado

- `active-context.md` → pelo hook `stop.sh` ao encerrar sessão, ou manualmente com `python sa-ia.py destilar`
- `drift-report.md` → pelo hook `validate-anchor.sh` ao detectar projetos sem âncora definida

## Regras

- Não edite nenhum arquivo desta pasta
- Se o conteúdo estiver errado, corrija os arquivos em `02-projects/raw/` e rode novamente:
  ```bash
  python sa-ia.py destilar
  ```
