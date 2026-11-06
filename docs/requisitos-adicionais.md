# SHIROKAI TRAINERS — Requisitos adicionais obrigatórios

Adicione os requisitos abaixo ao projeto Shirokai Trainers.

Eles complementam o prompt principal e devem ser considerados antes da implementação.

## 1. Editor de Pokémon

Criar um editor completo dentro do jogo, permitindo:

- Adicionar e remover Pokémon da equipe.
- Alterar espécies, formas e níveis.
- Configurar IVs e EVs individualmente.
- Configurar Nature, Ability e movimentos.
- Configurar itens equipados.
- Definir Shiny.
- Copiar Pokémon entre equipes.
- Salvar equipes como modelos reutilizáveis.
- Importar e exportar equipes Pokémon Showdown.

Validar os dados antes de salvar, impedindo espécies, habilidades ou movimentos inválidos.

## 2. Diálogos personalizados

Cada treinador deve possuir mensagens configuráveis para:

- Primeira interação.
- Início da batalha.
- Vitória do jogador.
- Derrota do jogador.
- Tentativa durante cooldown.
- Revanche.
- Requisitos não cumpridos.

Permitir cores e formatação compatíveis com Minecraft.

Suportar múltiplas linhas de diálogo.

## 3. Integração com EasyNPC

Implementar um modo administrativo de vinculação:

1. Executar `/traineradmin bind <id>`.
2. Clicar no NPC desejado.
3. Confirmar a vinculação.
4. Salvar a associação de forma persistente.

Investigar como interceptar interações com EasyNPC sem quebrar suas funcionalidades.

Não depender de comandos executados pelo jogador com OP.

Se a API do EasyNPC não permitir essa integração diretamente, implementar uma alternativa segura e documentar a limitação.

O sistema principal de batalhas deve funcionar mesmo sem EasyNPC, por comandos administrativos ou por uma entidade própria, caso seja necessário.

## 4. Sistema avançado de recompensas

Cada recompensa deve possuir configurações individuais:

- `enabled`
- `chance`
- `first_win_only`
- `repeatable`
- `cooldown_seconds`
- `max_claims_per_player`
- `required_permission`
- `required_scoreboard`
- `required_previous_victories`

Permitir recompensas fixas e aleatórias separadas para vitória e derrota.

Permitir grupos de recompensas:

- INDEPENDENT: cada recompensa possui seu próprio sorteio.
- WEIGHTED_ONE: apenas uma recompensa é sorteada conforme os pesos.
- GUARANTEED_PLUS_RANDOM: recompensas fixas mais sorteios adicionais.

Documentar claramente a diferença entre chance percentual e peso relativo.

Registrar as recompensas concedidas para evitar duplicações.

## 5. Histórico e progressão

Registrar por UUID:

- Treinadores derrotados.
- Quantidade de vitórias.
- Quantidade de derrotas.
- Primeira vitória.
- Última batalha.
- Recompensas já recebidas.
- Cooldowns.
- Recompensas pendentes.

Criar comandos administrativos para consultar e redefinir dados individuais.

Não apagar o progresso de outros jogadores ao redefinir um jogador.

## 6. Batalhas simultâneas

Permitir que jogadores diferentes desafiem o mesmo treinador ao mesmo tempo, quando configurado.

Cada batalha deve possuir:

- Identificador único.
- Jogador participante.
- Treinador associado.
- Equipe NPC independente.
- Estado da batalha.
- Resultado confirmado.

Impedir que uma batalha altere a equipe ou o resultado de outra.

Adicionar opção de bloquear batalhas simultâneas por treinador.

## 7. Dificuldades e equipes alternativas

Permitir múltiplas equipes para um mesmo treinador.

Exemplo:

- Normal.
- Difícil.
- Elite.

Cada dificuldade pode possuir:

- Equipe própria.
- Níveis próprios.
- Requisitos.
- Cooldown.
- Recompensas.
- Regras de batalha.

Permitir seleção manual de dificuldade ou seleção automática conforme condições configuradas.

Não alterar silenciosamente as equipes do jogador.

## 8. Condições de desbloqueio

Permitir exigir:

- Permissão LuckPerms.
- Scoreboard mínimo.
- Vitória contra outro treinador.
- Quantidade de ginásios derrotados.
- Objetivo de progressão personalizado.

Exibir uma mensagem explicando qual requisito falta.

## 9. Execução segura de comandos

Criar placeholders:

- `%player%`
- `%player_uuid%`
- `%trainer_id%`
- `%trainer_name%`
- `%battle_id%`

Validar comandos administrativos antes de salvar.

Executar comandos no contexto correto, sem conceder OP aos jogadores.

Não permitir que texto fornecido por jogadores seja inserido diretamente em comandos privilegiados.

Registrar erros de execução.

Restringir a edição de comandos aos administradores autorizados.

## 10. Persistência e backups

Armazenar configurações e dados de jogadores de forma segura.

Implementar:

- Salvamento atômico quando aplicável.
- Backup automático antes de migrações.
- Validação de JSON.
- Recuperação de configurações inválidas.
- Registro de erros.
- Recarregamento sem reiniciar, quando tecnicamente seguro.

Nunca apagar configurações antigas automaticamente.

## 11. Logs e ferramentas administrativas

Registrar:

- Início e encerramento de batalhas.
- Vitória, derrota, fuga e desconexão.
- Recompensas concedidas.
- Falhas na entrega.
- Comandos executados.
- Alterações administrativas.

Criar um modo de depuração que possa ser ativado e desativado.

Evitar logs excessivos durante funcionamento normal.

## 12. Compatibilidade e testes

Antes de implementar, investigar as APIs reais do Cobblemon 1.8.3 e EasyNPC.

Não inventar métodos, eventos ou classes.

Confirmar especialmente:

- Inicialização de batalhas contra equipes NPC.
- Controle da equipe adversária.
- Comportamento da IA.
- Identificação do resultado.
- Tratamento de batalhas simultâneas.
- Integração com entidades EasyNPC.
- Entrega de Pokémon.
- Funcionamento em servidor dedicado.

Não utilizar Cobblemon Trainer Battle como dependência.

Validar o projeto com esse mod completamente ausente.

## 13. Interface server-side

Priorizar menus de inventário que funcionem com clientes Minecraft compatíveis sem exigir instalação do Shirokai Trainers.

Para configurações que exigem texto livre, como comandos, nomes e equipes Showdown, utilizar entrada por comandos administrativos ou outro mecanismo realmente compatível.

Não presumir que uma GUI de inventário vanilla oferece campos de texto arbitrários.

## 14. Critérios de conclusão

O mod só poderá ser considerado concluído quando:

1. Um administrador conseguir criar um treinador dentro do Minecraft.
2. Conseguir configurar uma equipe Pokémon.
3. Conseguir vincular um NPC.
4. Um jogador sem OP conseguir iniciar a batalha.
5. A batalha utilizar o motor real do Cobblemon.
6. Vitória e derrota forem identificadas corretamente.
7. Recompensas fixas funcionarem.
8. Recompensas aleatórias funcionarem.
9. Cooldowns e limites funcionarem.
10. O progresso permanecer salvo após reiniciar o servidor.
11. Dois jogadores conseguirem batalhar simultaneamente sem conflito.
12. O servidor funcionar sem Cobblemon Trainer Battle.

Implementar por etapas, compilando e testando cada módulo antes de avançar.

Priorizar estabilidade, segurança e compatibilidade com servidor público.

## 15. Salvamento da configuração e localização dos NPCs

O servidor deve salvar de forma persistente a configuração e a localização dos NPCs vinculados aos treinadores.

- Registrar UUID do NPC, tipo de entidade, treinador vinculado e dimensão/mundo.
- Preservar coordenadas X, Y e Z, direção e rotação.
- Preservar a configuração própria do NPC, incluindo nome, aparência e demais dados suportados pelo mod que fornece a entidade.
- Manter os dados após salvar o mundo, encerrar e reiniciar o servidor.
- Atualizar o registro quando o administrador alterar a configuração ou mover o NPC.
- Disponibilizar salvamento e recuperação administrativos com permissões, validação e logs.
- Criar backups antes de substituir registros e durante migrações, sem apagar automaticamente configurações antigas.
- Não recriar automaticamente um NPC só porque seu chunk está descarregado ou sua entidade ainda não foi localizada; impedir duplicações.
- Documentar os limites da recuperação de entidades EasyNPC e preservar suas funcionalidades.

Validar reinício do servidor com NPCs em dimensões diferentes, NPC movido, configuração alterada e chunks descarregados. Confirmar posição, aparência/configuração e associação ao treinador após recarregar o mundo, sem duplicar entidades.
