# Comandos e permissões — Shirokai Trainers 0.2.1

## Instalar e começar

Baixe o JAR na [Release v0.2.1](https://github.com/istwi/Shirokai-Trainers/releases/tag/v0.2.1) e coloque-o em `mods/` **do servidor**. Use Minecraft 1.21.1, Java 21, Fabric Loader >=0.17.2, Fabric API >=0.116.6+1.21.1, Fabric Language Kotlin >=1.13.6+kotlin.2.2.20 e Cobblemon **1.8.3+1.21.1**. Clientes precisam do Cobblemon compatível; não precisam do Shirokai Trainers.

EasyNPC e LuckPerms são opcionais. Verifique os requisitos próprios da versão EasyNPC escolhida; a revisão investigada requer Loader >=0.18.3 e Fabric API >=0.116.7+1.21.1. Não é necessário instalar Cobblemon Trainer Battle. Esta é uma pré-release para os [testes finais no jogo](guia-testes.md).

No jogo, os comandos começam com `/`. No console, retire a `/`. Comandos que abrem menus, usam buffer pessoal ou clicam em NPC precisam de um jogador conectado.

## Permissões implementadas

| Acesso | Regra efetiva |
| --- | --- |
| `/trainer`, `/trainerstatus`, `/trainerclaim` | Disponíveis a jogadores comuns, sem OP. Não há nós próprios como `shirokai.use` nessa versão. |
| `/traineradmin` e todos os subcomandos | `shirokai.admin`, consultada pela Fabric Permissions API. Sem decisão do provedor de permissões, usa fallback de nível de permissão Minecraft **2**. |
| Requisito de dificuldade `permission` | Nó escolhido pelo administrador; sem concessão do provedor, o padrão é **negar**. |
| Recompensa `required_permission` | Nó escolhido pelo administrador; sem concessão do provedor, o padrão é **negar**. |

`shirokai.admin` concede administração completa: equipes, comandos de recompensa, vínculos, snapshots e dados de jogadores. Não existem permissões administrativas separadas por subcomando nessa versão. Os comandos de recompensa são executados pelo servidor com nível 4; o participante não recebe OP.

### Exemplo com LuckPerms

Com LuckPerms instalado e a integração Fabric ativa, execute como operador autorizado:

```text
/lp user SeuNick permission set shirokai.admin true
```

Para conceder a um grupo já existente:

```text
/lp group administradores permission set shirokai.admin true
```

Para remover a concessão individual explícita:

```text
/lp user SeuNick permission unset shirokai.admin
```

Remover um nó explícito não remove concessões herdadas de grupos nem o fallback OP quando aplicável. Para negar explicitamente pelo LuckPerms:

```text
/lp user SeuNick permission set shirokai.admin false
```

Para um requisito personalizado de dificuldade:

```text
/traineradmin requirements brock elite {"permission":"shirokai.desafio.elite"}
/lp user NomeDoJogador permission set shirokai.desafio.elite true
```

Esse nó personalizado só será exigido porque foi configurado naquela dificuldade; não é uma permissão global automática do mod. Sem LuckPerms ou outro provedor compatível, mantenha esses requisitos de permissão ausentes para os desafios públicos e use o fallback OP apenas para administrar.

## Comandos dos jogadores

| Comando | O que faz |
| --- | --- |
| `/trainer` | Abre o menu de treinadores. |
| `/trainer <id> [dificuldade]` | Inicia o desafio, respeitando requisitos, cooldown e disponibilidade. Sem dificuldade explícita, usa a primeira ou a seleção automática configurada. |
| `/trainerstatus` | Mostra suas vitórias, derrotas e quantidade de recompensas pendentes/em revisão. |
| `/trainerclaim` | Tenta entregar suas recompensas PENDING. Falta de espaço continua pendente; entregas incertas não são repetidas automaticamente. |

Para desafiar por NPC vinculado: **agache e clique com a mão principal vazia**. O clique normal fica disponível para as funções originais do EasyNPC. Cada participante precisa de Pokémon aptos na equipe.

## Comandos administrativos

Todos exigem `shirokai.admin` ou o fallback descrito acima. `<id>` identifica o treinador, `<dif>` a dificuldade, `<slot>` vai de 1 a 6, e `<uuid>` é o UUID completo. IDs de treinador/dificuldade/modelo/grupo/recompensa usam letras minúsculas, números, `_` e `-`, com no máximo 64 caracteres.

| Comando | O que faz |
| --- | --- |
| `/traineradmin` | Abre o menu administrativo. |
| `/traineradmin help` | Mostra a ajuda dentro do jogo. |
| `/traineradmin create <id>` | Cria um treinador, inicialmente sem equipe. |
| `/traineradmin edit <id>` | Abre o editor de inventário. |
| `/traineradmin name <id> <nome>` | Altera o nome exibido; aceita espaços. |
| `/traineradmin show <id>` | Exibe a configuração completa em JSON. |
| `/traineradmin config <id> <JSON ou buffer>` | Substitui a configuração completa, validando antes de salvar; o ID precisa permanecer igual. |
| `/traineradmin team <id> <dif> add` | Adiciona um Pokémon padrão para edição. |
| `/traineradmin team <id> <dif> clear` | Esvazia aquela equipe. |
| `/traineradmin pokemon <id> <dif> <slot> <JSON ou buffer>` | Substitui o Pokémon do slot; campos omitidos usam os defaults de Pokémon. |
| `/traineradmin remove <id> <dif> <slot>` | Remove o Pokémon do slot. |
| `/traineradmin copy <origem> <dif_origem> <slot> <destino> <dif_destino>` | Copia o Pokémon para o final de outra equipe, sem remover o original. |
| `/traineradmin difficulty <id> <nova_dif>` | Adiciona uma dificuldade, inicialmente sem equipe. |
| `/traineradmin settings <id> <dif> <JSON parcial ou buffer>` | Atualiza campos da dificuldade, como cooldown, IA e regras. |
| `/traineradmin requirements <id> <dif> <JSON parcial ou buffer>` | Atualiza condições de desbloqueio. |
| `/traineradmin dialogue <id> <evento> <texto ou buffer>` | Define mensagens; `|` separa linhas quando não usa buffer. |
| `/traineradmin input begin` | Inicia/esvazia seu buffer de texto. |
| `/traineradmin input append <linha>` | Acrescenta uma linha; `<blank>` insere uma linha em branco. Limite total de 24.000 caracteres, expiração de 10 minutos. |
| `/traineradmin input clear` | Remove seu buffer. |
| `/traineradmin import <id> <dif>` | Importa a equipe Showdown do seu buffer. |
| `/traineradmin export <id> <dif>` | Exibe a equipe em formato Showdown. |
| `/traineradmin template save <modelo> <id> <dif>` | Salva a equipe como modelo reutilizável. |
| `/traineradmin template load <modelo> <id> <dif>` | Substitui aquela equipe pelo modelo salvo. |
| `/traineradmin rewardgroup <id> <dif> win ou loss <grupo> <modo>` | Cria um grupo ou altera seu modo de seleção. Use `win` ou `loss`, sem a palavra `ou`. |
| `/traineradmin reward <id> <dif> win ou loss <grupo> <recompensa> <JSON parcial ou buffer>` | Cria/edita uma recompensa no grupo existente. |
| `/traineradmin rewardremove <id> <dif> win ou loss <grupo> <recompensa>` | Remove a recompensa da configuração, preservando o histórico de claims. |
| `/traineradmin bind <id>` | Inicia vinculação por clique em NPC, com prazo de 60 segundos. |
| `/traineradmin bindconfirm` | Confirma o NPC selecionado, perto do administrador e na mesma dimensão, dentro do prazo. |
| `/traineradmin unbind <uuid_npc>` | Remove a vinculação. Não remove a entidade. |
| `/traineradmin npcsave [uuid_npc]` | Salva configuração/localização do NPC carregado; sem UUID, tenta todos os vinculados. |
| `/traineradmin npcrestore <uuid_npc> confirm` | Restaura um snapshot no NPC existente e carregado, com backup do estado anterior. |
| `/traineradmin data <uuid_jogador>` | Consulta progresso, cooldowns, claims e entregas daquele jogador. |
| `/traineradmin reset <uuid_jogador> confirm` | Zera apenas aquele jogador, com backup; recusa se houver sessão ativa dele. |
| `/traineradmin objective <uuid_jogador> <objetivo> grant` | Concede um objetivo personalizado. |
| `/traineradmin objective <uuid_jogador> <objetivo> revoke` | Remove um objetivo personalizado. |
| `/traineradmin delivery <uuid_jogador> <id_entrega> delivered_confirm` | Após conferência, marca uma entrega incerta como já concedida. |
| `/traineradmin delivery <uuid_jogador> <id_entrega> retry_confirm` | Após comprovar que não foi concedida, libera nova tentativa de entrega incerta. |
| `/traineradmin claim` | Tenta entregar suas próprias pendências; alias administrativo de `/trainerclaim`. |
| `/traineradmin reload` | Valida e recarrega configurações; batalhas existentes mantêm sua configuração original. |
| `/traineradmin retryresults` | Reprocessa resultados de sessões retidas que já não estão no motor, por exemplo após corrigir uma falha de disco. Não inventa vitória para sessão sem resultado confirmado. |
| `/traineradmin debug on` | Ativa detalhes de depuração. |
| `/traineradmin debug off` | Desativa detalhes de depuração. |

## Exemplo completo: criar um treinador

```text
/traineradmin create brock
/traineradmin name brock Brock
/traineradmin team brock normal add
/traineradmin pokemon brock normal 1 {"species":"geodude","level":15,"nature":"adamant","moves":["tackle","rockthrow"]}
/traineradmin settings brock normal {"cooldownSeconds":60,"skill":3}
/traineradmin dialogue brock start &eVamos batalhar!
/traineradmin dialogue brock win &aVocê venceu!|&eParabéns!
/traineradmin edit brock
```

O editor permite selecionar espécie, forma, Nature, Ability, movimentos e item, ajustar níveis, IVs, EVs e Shiny e copiar para outra equipe. Clique direito reduz valores numéricos. Validações impedem dados inválidos e EVs acima do total permitido.

Crie seu NPC pelo EasyNPC ou pelos recursos nativos do Cobblemon. Em seguida:

```text
/traineradmin bind brock
```

Clique no NPC e depois execute:

```text
/traineradmin bindconfirm
/traineradmin npcsave
```

Jogador sem OP pode usar `/trainer brock` ou o gesto de agachar/clicar no NPC. Vinculação e snapshot são gravados por UUID; se o NPC for removido e recriado com outro UUID, vincule novamente.

## Recompensas: fixa e sorteio

```text
/traineradmin rewardgroup brock normal win fixas INDEPENDENT
/traineradmin reward brock normal win fixas diamante {"kind":"ITEM","value":"minecraft:diamond","chance":100,"amount":1}
/traineradmin rewardgroup brock normal win sorteio WEIGHTED_ONE
/traineradmin reward brock normal win sorteio ouro {"kind":"ITEM","value":"minecraft:gold_ingot","weight":3}
/traineradmin reward brock normal win sorteio esmeralda {"kind":"ITEM","value":"minecraft:emerald","weight":1}
```

Assim, uma vitória elegível concede diamante e um item do sorteio. `INDEPENDENT` usa `chance` percentual, de 0 a 100; `WEIGHTED_ONE` usa pesos relativos e ignora `chance`. Nesse exemplo, pesos 3 e 1 significam 75% e 25% se ambas forem elegíveis. `GUARANTEED_PLUS_RANDOM` concede as recompensas com `guaranteed:true` e sorteia as demais por chance, respeitando os requisitos individuais.

Exemplo de comando executado **pelo servidor**, sem tornar o jogador OP:

```text
/traineradmin reward brock normal win fixas mensagem {"kind":"COMMAND","value":"tell %player% Parabens pela vitoria!","amount":1,"chance":100}
```

Placeholders: `%player%`, `%player_uuid%`, `%trainer_id%`, `%trainer_name%`, `%battle_id%`. Devem ocupar argumentos completos. `%trainer_name%` só funciona em comandos se o nome não contiver espaços ou caracteres especiais; use `%trainer_id%` para nomes decorados.

Recompensas podem exigir `enabled`, `first_win_only`, `repeatable`, `cooldown_seconds`, `max_claims_per_player`, `required_permission`, `required_scoreboard` e `required_previous_victories`. Consulte [o README](../README.md#recompensas-dificuldades-e-requisitos) para os tipos e regras. IDs de recompensa e grupo fazem parte da identidade dos limites: editar o mesmo ID preserva seus claims; criar outro ID representa outra recompensa.

## Requisitos, dificuldades e modelos

```text
/traineradmin difficulty brock elite
/traineradmin copy brock normal 1 brock elite
/traineradmin settings brock elite {"skill":5,"cooldownSeconds":300}
/traineradmin requirements brock elite {"previousVictories":{"brock":1}}
/traineradmin template save equipe_rocha brock normal
/traineradmin template load equipe_rocha brock elite
```

`requirements` aceita `permission`, `scoreboard`, `previousVictories`, `gyms` e `objectives`. Campos de mapa/lista informados substituem o mapa/lista anterior. Por exemplo, `{"scoreboard":{}}` remove os requisitos de scoreboard; `{"permission":null}` remove o requisito de permissão. Campos omitidos são preservados nesses comandos de atualização parcial.

Eventos de diálogo: `first`, `start`, `win`, `loss`, `cooldown`, `rematch`, `requirements`. Cores/formatação legadas usam `&`, como `&a`, `&c`, `&l` e `&r`.

## Importar Showdown pelo chat

```text
/traineradmin input begin
/traineradmin input append Geodude
/traineradmin input append Ability: Rock Head
/traineradmin input append Level: 15
/traineradmin input append Adamant Nature
/traineradmin input append - Tackle
/traineradmin input append - Rock Throw
/traineradmin import brock normal
/traineradmin export brock normal
```

Para inserir outro Pokémon, use `input append <blank>` antes do cabeçalho dele. O buffer também pode fornecer JSON a `pokemon`, `config`, `settings`, `requirements` e `reward`, ou múltiplas linhas a `dialogue`. A importação cobre os campos do editor e rejeita campos adicionais não suportados.

## Dados e recuperação

Arquivos ficam em `config/shirokai_trainers/`. Dados de jogador usam UUID. Backups preservam versões anteriores e não são apagados automaticamente. Faça backup do mundo junto com as configurações para preservar as entidades e seus dados próprios.

Snapshot não recria NPC desaparecido: carregue o chunk da entidade existente antes de `npcrestore`. Antes de restaurar, o mod arquiva o estado atual. Para entregas em `IN_FLIGHT` ou `NEEDS_REVIEW`, confira logs/inventário antes de `retry_confirm`; repetir um comando externo não idempotente pode duplicar efeitos. Entregas sem espaço que continuam PENDING usam `/trainerclaim` normalmente.
