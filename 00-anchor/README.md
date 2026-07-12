# 00-anchor

Âncoras permanentes do sistema. São a bússola que governa tudo.

## O que fica aqui

- `owner.md` — âncora raiz de quem usa o sistema (identidade, objetivo central, pilares, regras)
- `[empresa]/empresa.md` — âncora de cada empresa (uma pasta por empresa)

## Regras

- Só edite quando algo mudar estruturalmente (novo objetivo, nova empresa, nova restrição)
- Não crie arquivos aqui fora dos padrões acima
- O hook `session-start.sh` injeta estes arquivos automaticamente no contexto

## Estrutura esperada

```
00-anchor/
├── owner.md
├── empresa-a/
│   └── empresa.md
└── empresa-b/
    └── empresa.md
```
