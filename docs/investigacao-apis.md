# APIs verificadas

Base: Minecraft 1.21.1, Java 21, Fabric, Cobblemon 1.8.3. O TXT é a especificação principal completa; não existe outro prompt necessário para iniciar.

## Cobblemon

Fonte oficial: https://gitlab.com/cable-mc/cobblemon/-/tree/1.8.3

Commit da tag consultada: `ffe005511dd0d3ba68377fa3f95906b3837d9a0e`.
Artefato: `com.cobblemon:fabric:1.8.3+1.21.1`, no Maven https://artefacts.cobblemon.com/releases.

Arquivos consultados em `common/src/main/kotlin/com/cobblemon/mod/common/`:

| Necessidade | API existente e observações |
| --- | --- |
| Oponente sem entidade | `battles/actor/TrainerBattleActor.kt`: recebe nome, UUID, lista de `BattlePokemon` e `BattleAI`; tipo NPC. |
| IA | `battles/ai/StrongBattleAI.kt`: skill 0–5; possui estado mutável interno. Criar uma instância por batalha. |
| Inicialização | `battles/BattleRegistry.kt`: `startBattle(BattleFormat, BattleSide, BattleSide, canPreempt)`. **Não valida as equipes**; o chamador precisa validar Pokémon disponíveis, jogador ocupado e formato antes de chamar. |
| Referência de validação | `battles/BattleBuilder.kt`: `pvn` utiliza uma `NPCEntity` do Cobblemon, não uma entidade EasyNPC. Não passar EasyNPC como NPCEntity. |
| Equipe do jogador | `api/storage/party/PartyStore.kt`: `toBattleTeam(clone, healPokemon, leadingPokemon)`. Não ajustar nível, curar ou substituir silenciosamente a equipe do jogador. |
| Equipe adversária | `battles/pokemon/BattlePokemon.kt`: `safeCopyOf`, `playerOwned`; gerar Pokémon novos por sessão. |
| Resultado | `api/events/battles/BattleVictoryEvent.kt`: `battle`, `winners`, `losers`, `wasWildCapture`. Relacionar UUID do ator do jogador e ID da batalha, nunca inferir pelo desaparecimento da entidade. |
| Fuga | `CobblemonEvents.BATTLE_FLED`; encerramento sem vitória não concede recompensas de vitória/derrota. |
| Encerramento | `PokemonBattle.onEndHandlers` e `BattleRegistry.closeBattle`; precisam de proteção idempotente com os eventos de resultado. |
| Dados Pokémon | `PokemonSpecies.getByIdentifier`, `Moves.getByName`, `Abilities.get`, `Natures.getNature`. Validar antes de `PokemonProperties.create`, pois o parser aceita defaults e faz coerções. |
| Entrega | `Cobblemon.storage.getParty(player)` e `getPC(player)`; verificar sucesso e espaço antes de marcar a entrega. |

Esta inspeção confirma assinaturas, não demonstra funcionamento de uma batalha no servidor. A integração ainda deve ser compilada e exercitada com cliente Cobblemon, incluindo dois jogadores simultâneos.

## EasyNPC

Fonte oficial: https://github.com/MarkusBordihn/BOs-Easy-NPC/tree/1.21.1

Commit consultado: `536b212` (branch móvel; a versão binária deverá ser fixada na validação de integração).

Arquivos consultados:

- `core/Common/src/main/java/de/markusbordihn/easynpc/api/npc/raw/NPCRawTemplate.java`: `mobInteract` delega ao `InteractionHandler`.
- `core/Common/src/main/java/de/markusbordihn/easynpc/entity/easynpc/handlers/InteractionHandler.java`: usa mão principal, preserva ferramentas administrativas e executa ações `ON_INTERACTION`.
- `core/Common/src/main/java/de/markusbordihn/easynpc/api/event/EasyNPCEventRegistry.java`: listeners de diálogo, ação, estado etc. Não foi identificado nessa classe um callback universal de interação prévia cancelável.
- `core/Fabric/src/main/resources/fabric.mod.json`: a revisão consultada exige loader >=0.18.3 e Fabric API >=0.116.7+1.21.1. A base inicial do Cobblemon usa versões anteriores; alinhar antes de testar essa revisão do EasyNPC.

Alternativa de integração: callback Fabric de uso de entidade, associação por UUID e interação explícita (por exemplo, agachar e clicar com mão vazia) para iniciar batalha; interações normais retornam PASS e continuam no EasyNPC. O modo administrativo captura somente o clique de vinculação e exige confirmação. Não substituir ações existentes ou executar comandos como jogador OP. Validar a ordem dos callbacks na versão binária selecionada.

EasyNPC e Cobblemon Trainer Battle não são dependências do núcleo. Cobblemon Trainer Battle não deve estar presente na validação.
