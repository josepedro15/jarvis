4.  **Integração Contínua**: Posso ajudar a configurar workflows de CI/CD.

## Próximos Passos

Definir o objetivo do projeto no `task.md`.

## Funcionalidades do Agente

- **Listar Repositórios**: Ao solicitar "listar meus repositórios", o agente deve enviar uma requisição para o **Jules**. O Jules listará os repositórios que ele tem acesso.
- **Executar Alterações**: Ao solicitar uma alteração de código, o agente informará qual repositório Git deve ser editado. O agente deve então enviar uma requisição com os detalhes da alteração para o **Jules** executar. O agente (eu) não deve editar os arquivos diretamente, mas sim delegar a execução ao Jules.
