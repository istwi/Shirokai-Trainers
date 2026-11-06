# Shirokai Trainers

Mod **server-side** para **Minecraft 1.21.1 / Fabric / Cobblemon 1.8.3**, implementado a partir de [requisitos-adicionais.md](docs/requisitos-adicionais.md), que é o prompt completo do projeto.

**Em validação. Não é uma versão concluída para servidor público.** Os testes automatizados do núcleo e a compilação passaram; o roteiro de aceitação com clientes, batalhas completas e EasyNPC ainda precisa ser executado. Consulte [a investigação das APIs](docs/investigacao-apis.md) e [o roteiro de validação](docs/validacao.md).

## Compilar

Necessário **JDK 21** (incluindo `javac`).

```sh
./gradlew -PcoreOnly :core:test  # núcleo sem preparar Minecraft
./gradlew test :fabric:build
```

O JAR instalável fica em `fabric/build/libs/shirokai-trainers-0.1.0.jar`. Requisitos de servidor: Fabric Loader >=0.17.2, Fabric API >=0.116.6+1.21.1, Fabric Language Kotlin >=1.13.6+kotlin.2.2.20 e Cobblemon **1.8.3+1.21.1**. A API de permissões e o núcleo são incluídos no JAR. Não instale Cobblemon Trainer Battle; ele não é uma dependência.

Clientes precisam do Minecraft e Cobblemon compatíveis, **sem instalar Shirokai Trainers**. EasyNPC e LuckPerms são opcionais. A versão EasyNPC consultada exige loader/API mais recentes; confira a compatibilidade antes de adicioná-la.

Use o checkout existente da tarefa em nuvem; não crie worktrees adicionais. Em redes gerenciadas, mantenha o proxy e configure as propriedades Java de proxy/CA conforme o ambiente; não desabilite TLS. O wrapper verifica o SHA-256 da distribuição Gradle.

## Desenvolvimento e servidor

```sh
./gradlew :fabric:runServer
```

O diretório de desenvolvimento é `fabric/run/`, ignorado pelo Git. O servidor solicita a aceitação da EULA do Minecraft no primeiro uso. Configure `eula.txt` e `server.properties` nesse diretório conforme os termos aceitos pelo operador. Processos precisam ser reiniciados entre tarefas; não suponha que um servidor em execução sobreviva a snapshots.

## Administração dentro do Minecraft

`/traineradmin` abre o menu administrativo. Requer `shirokai.admin`, com fallback para nível de permissão 2. LuckPerms pode fornecer essa permissão pela Fabric Permissions API. Jogadores comuns usam `/trainer` ou `/trainer <id> [dificuldade]`, sem OP.

```text
/traineradmin create brock
/traineradmin name brock Brock
/traineradmin edit brock
/traineradmin team brock normal add
/traineradmin pokemon brock normal 1 {"species":"geodude","level":15,"nature":"adamant","moves":["tackle","rockthrow"]}
/traineradmin dialogue brock win &aMuito bem!|&eVolte para uma revanche.
/traineradmin bind brock
```

Depois de `bind`, clique em uma entidade EasyNPC ou NPC do Cobblemon e confirme com `/traineradmin bindconfirm` em até 60 segundos. A associação é salva por UUID. Para desafiar um NPC associado, **agache e clique com a mão principal vazia**. O clique normal continua disponível para diálogos, ferramentas e ações do EasyNPC. O comando `/trainer brock` também funciona sem EasyNPC. UUIDs deixam de representar o mesmo NPC se ele for removido e recriado: vincule novamente.

O menu permite adicionar/remover Pokémon, ajustar nível, Shiny, IVs e EVs, alternar dificuldades e configurar cooldown, IA, ginásio e simultaneidade. Espécie, forma, Nature, Ability, movimentos e item são editáveis pelo comando `pokemon`, com JSON, inteiramente dentro do jogo. Texto livre usa comandos, e não campos fictícios de inventário.

`pokemon` recebe um objeto Pokémon completo, aplicando defaults aos campos omitidos. `config` recebe uma configuração de treinador completa, obtida com `show`. Mudanças são validadas antes de salvar, incluindo consulta aos registros reais do Cobblemon, e criação de um Pokémon de validação. Equipes de jogadores não são substituídas ou niveladas pelo mod.

```text
/traineradmin show brock
/traineradmin config brock <JSON completo ou buffer>
/traineradmin difficulty brock elite
/traineradmin copy brock normal 1 brock elite
/traineradmin template save equipe_rocha brock normal
/traineradmin template load equipe_rocha brock elite
/traineradmin export brock normal
```

Importação Showdown e textos longos usam um buffer por administrador, com limite de 24.000 caracteres e expiração de 10 minutos:

```text
/traineradmin input begin
/traineradmin input append Geodude
/traineradmin input append Ability: Rock Head
/traineradmin input append Level: 15
/traineradmin input append Adamant Nature
/traineradmin input append - Tackle
/traineradmin input append - Rock Throw
/traineradmin import brock normal
```

Para separar Pokémon, adicione `/traineradmin input append <blank>`. O mesmo buffer aceita JSON em linhas, para `pokemon ... buffer` ou `config ... buffer`, e diálogos com `dialogue ... buffer`. Campos Showdown não suportados são rejeitados explicitamente; a implementação cobre os campos do editor e não afirma preservar metadados fora dessa especificação.

## Recompensas, dificuldades e requisitos

O modelo completo está em `core/src/main/kotlin/dev/shirokai/core/Model.kt`. Cada dificuldade contém `team`, `requirements`, `cooldownSeconds`, `skill`, `battleRules`, `winRewards` e `lossRewards`. Cada grupo de recompensa tem `id`, `mode` e `rewards`. IDs de grupo devem ser únicos dentro da dificuldade, inclusive entre vitória e derrota.

- `INDEPENDENT`: cada recompensa elegível usa `chance`, percentual absoluto de 0 a 100. Zero nunca concede, 100 sempre concede.
- `WEIGHTED_ONE`: seleciona exatamente uma recompensa elegível, proporcionalmente a `weight` positivo. `chance` não participa desse modo. Pesos 1 e 3 significam probabilidades 25% e 75% se ambas forem elegíveis.
- `GUARANTEED_PLUS_RANDOM`: concede recompensas com `guaranteed: true` e sorteia as demais por `chance`. Todas continuam sujeitas aos próprios requisitos e limites.

Uma recompensa usa `kind: ITEM | POKEMON | COMMAND`, `value` e `amount`. Para ITEM, `value` é um ID como `minecraft:diamond`. Para POKEMON, é uma string contendo o JSON de `PokemonSpec` e `amount` deve ser 1. Para COMMAND, é o comando sem `/`, executado pelo servidor, e `amount` deve ser 1. Os campos individuais exigidos no TXT estão presentes com seus nomes originais: `enabled`, `chance`, `first_win_only`, `repeatable`, `cooldown_seconds`, `max_claims_per_player`, `required_permission`, `required_scoreboard` e `required_previous_victories`.

`required_scoreboard` e `required_previous_victories` são mapas de objetivo/treinador para mínimo exigido. Limite de claims zero significa ilimitado. Claims são reservados e persistidos antes da entrega e contam recompensas pendentes, para impedir contornar limites por desconexão. A identidade do limite inclui treinador, dificuldade, grupo e recompensa: mantenha esses IDs para preservar limites existentes.

Os requisitos de dificuldade usam `permission`, `scoreboard`, `previousVictories`, `gyms` e `objectives`. Um treinador marcado `gym` conta uma vez após a primeira vitória. Objetivos personalizados são administrados com `objective`. Na seleção automática, vence a **última dificuldade elegível na ordem configurada**; a seleção manual continua disponível. Nenhuma dificuldade ignora seus requisitos.

## Comandos privilegiados e entregas

Placeholders aceitos: `%player%`, `%player_uuid%`, `%trainer_id%`, `%trainer_name%`, `%battle_id%`. Devem ocupar argumentos completos. O nome de jogador é validado e não é texto de chat. `%trainer_name%` exige nome administrativo sem espaços ou caracteres especiais; prefira `%trainer_id%` para nomes decorados. O comando é validado sintaticamente no dispatcher Minecraft antes de salvar. Somente administradores autorizados editam comandos. O jogador nunca recebe OP.

Recompensas são persistidas antes de efeitos externos, com ID derivado da batalha e da recompensa. Eventos repetidos não geram novas entregas. Uma operação externa e a escrita em disco não podem constituir uma única transação: entregas interrompidas em `IN_FLIGHT` e erros em `NEEDS_REVIEW` **não são repetidos automaticamente**. O administrador deve consultar os registros e o inventário antes de decidir:

```text
/traineradmin data <uuid>
/traineradmin delivery <uuid> <id_entrega> delivered_confirm
/traineradmin delivery <uuid> <id_entrega> retry_confirm
```

Use `retry_confirm` apenas após comprovar que a entrega não ocorreu; repetir comandos não idempotentes pode duplicar efeitos. Não se promete exactly-once para comandos externos arbitrários. Inventário/PC sem espaço gera registro para revisão, sem descartar itens no chão.

## Dados, recuperação e logs

Configurações e progresso ficam em `config/shirokai_trainers/`: `trainers/`, `players/`, `templates/` e `bindings.json`. Escritas usam arquivo temporário, fsync e substituição atômica. Versões anteriores são preservadas em `backups/` antes da substituição, sem exclusão automática. Isso requer uma política de arquivamento do operador para não ocupar o disco indefinidamente.

JSON inválido é preservado e pode ser recuperado do `.bak`, com erro registrado. Se um arquivo não tiver backup válido, o carregamento falha em vez de apagar dados. `schemaVersion: 1` é a versão inicial; versões desconhecidas são rejeitadas. Não existe ainda migração de um formato anterior.

```text
/traineradmin reload
/traineradmin data <uuid>
/traineradmin reset <uuid> confirm
/traineradmin objective <uuid> <id> grant
/traineradmin debug on
/traineradmin debug off
```

O reload valida todo o conjunto antes de trocar a configuração ativa. Batalhas em andamento usam sua configuração original. Reset é exclusivo do UUID informado, preserva backup e é recusado durante batalha ativa desse jogador. Logs normais cobrem batalhas, resultados, desconexões, entregas, comandos de recompensa e alterações administrativas; debug adiciona detalhes de falhas.

## Configuração e localização dos NPCs

Além da persistência nativa das entidades no mundo Minecraft, o mod registra um snapshot dos NPCs vinculados em `npcs/<uuid>.json`: tipo de entidade, treinador, dimensão, coordenadas, rotação e NBT completo disponível pela API de salvamento da entidade. Esse NBT contém os dados que o próprio Cobblemon/EasyNPC expõe para salvamento, incluindo nome e aparência quando suportados pelo fornecedor.

NPCs carregados são registrados ao vincular, a cada 1.200 ticks (aproximadamente um minuto) e no encerramento normal. Entidades Mob são marcadas persistentes. Para salvar imediatamente após editar/mover:

```text
/traineradmin npcsave
/traineradmin npcsave <uuid_npc>
/traineradmin npcrestore <uuid_npc> confirm
```

A restauração exige o mesmo NPC **já carregado**, mesmo UUID/tipo/vínculo, dimensão existente e nenhuma batalha do treinador em andamento. Antes de aplicar, o estado atual é arquivado em `npc-restore-backups/`. NPCs com passageiros/montarias não são restaurados até desmontar. A restauração pode mover o NPC para sua dimensão/posição salva, mas não cria entidades novas: chunk descarregado não é evidência de exclusão. Dados externos ao NBT, mantidos por outro mod em arquivos próprios, também precisam dos backups nativos desse mod. Faça backup do mundo junto com `config/`.
