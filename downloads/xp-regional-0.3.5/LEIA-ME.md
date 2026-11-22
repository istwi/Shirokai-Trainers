# Zorykai Trainers 0.3.5 — XP dos Pokémon por região do Guard

Minecraft 1.21.1 / Fabric / Java 21 / Cobblemon 1.8.3. Mantém os diálogos e a correção de cliques rápidos da 0.3.4, a identidade Zorykai e os IDs técnicos/configurações existentes.

## Instalar

Com o servidor parado e backup dos dados, substitua somente o JAR antigo do Trainers por `shirokai-trainers-0.3.5.jar`; mantenha apenas uma versão. Não precisa trocar o Guard: a integração consulta os limites da região pela API de núcleo já existente. Sem Guard ou com integração indisponível, as batalhas continuam funcionando com XP normal. Não cria `/warp xp`; o comando de warp pertence ao mod de warps que você utiliza.

## 1. Demarcar a área

Como administrador, na dimensão da área, marque os dois cantos opostos:

```mcfunction
/sg pos1
/sg pos2
/sg define farm_xp
```

Cada `pos` usa o bloco onde você está. Também aceita coordenadas, por exemplo `/sg pos1 100 60 100` e `/sg pos2 140 90 140`. Inclua a altura onde ficam jogadores e NPCs. Se a região já existe, use o ID atual no JSON; não precisa recriá-la. `/sg info farm_xp` mostra os limites.

O bônus consulta somente a geometria da região: não altera owners, members, flags, bypass, comandos, autenticação ou permissões. As proteções continuam independentes. Se a região bloqueia interação/batalha, libere explicitamente os recursos necessários nela, por exemplo:

```mcfunction
/sg flag farm_xp entity-interact allow
/sg flag farm_xp pokemon-interact allow
/sg flag farm_xp pokemon-battle allow
```

Quebra e construção podem continuar bloqueadas. Confira também regiões sobrepostas e suas prioridades. Não é preciso liberar comandos gerais para o bônus funcionar.

## 2. Configurar o multiplicador

Na primeira carga é criado `config/shirokai_trainers/xp-regions.json` com a lista vazia, sem bônus ativo em lugar algum. Edite-o:

```json
{
  "schemaVersion": 1,
  "enabled": true,
  "regions": [
    {
      "region": "farm_xp",
      "dimension": "minecraft:overworld",
      "multiplier": 2.0,
      "enabled": true,
      "trainers": []
    }
  ]
}
```

Depois:

```mcfunction
/traineradmin reload
```

`multiplier: 2.0` dobra o XP calculado pelo Cobblemon; `3.0` triplica. Valores aceitos: 1.0 a 10.0. O multiplicador é aplicado ao XP de batalha existente, respeitando seus outros ajustes; não substitui a fórmula de XP do Cobblemon nem entrega uma segunda recompensa.

`trainers: []` aceita todos os treinadores do Shirokai-Trainers enfrentados por um NPC dentro da região. Para restringir à fazenda, use os IDs dos treinadores, por exemplo `"trainers": ["xp_facil", "xp_medio"]`. São IDs dos arquivos de treinador, não o nome visual ou o ID da entidade NPC. Você pode ter mais de uma região/dimensão na lista; o mesmo ID em dimensões diferentes é permitido. Duplicar o par dimensão/região é rejeitado.

`enabled: false` no início desliga a função; dentro de uma regra desliga somente aquela região. Uma lista vazia não aplica bônus. `__global__` é proibida: a região precisa ter limites físicos. Região inexistente/removida ou dimensão diferente não dá bônus.

## 3. Colocar os NPCs

Use seus treinadores já configurados e crie/vincule os NPCs dentro dos limites. Exemplo, se o treinador `xp_facil` já existir com equipe válida:

```mcfunction
/traineradmin npc create npc_xp xp_facil
```

O clique direto, a confirmação de batalha e o botão de batalha dos diálogos nativos passam pelo mesmo controle. Não é preciso recriar NPCs existentes. O NPC pode ser independente ou um NPC externo vinculado ao Trainers.

## Regras de funcionamento

- O jogador e o NPC real precisam estar vivos, na mesma dimensão e dentro da mesma região configurada ao iniciar a batalha pelo NPC.
- Conferência por bloco, incluindo X/Y/Z; coordenadas negativas usam arredondamento para baixo, como o Guard.
- O multiplicador fica associado àquela batalha e ao dono dos Pokémon. Entrar na área depois de começar uma luta fora não ativa bônus. Sair da área depois de iniciar uma luta válida não recalcula o bônus dessa luta.
- Recarregar/editar o JSON ou remover uma região afeta as próximas batalhas; a luta em andamento mantém o valor inicial. Isso permite que o último KO receba o bônus mesmo se o callback de vitória já encerrou o registro de resultado.
- Regiões sobrepostas usam o maior multiplicador elegível, sem somar nem multiplicar entre si. A prioridade de proteção do Guard continua funcionando separadamente.
- Só afeta XP dos Pokémon em batalhas iniciadas pelo sistema de NPCs do Trainers. Não aumenta XP Minecraft, doces, comandos, ovos, dinheiro, itens, EVs ou batalhas selvagens/PvP/de outros mods. Desafios remotos por comando/menu sem origem NPC não recebem o bônus.
- XP é inteiro: arredonda para baixo e limita ao máximo do tipo inteiro, sem converter zero em ganho positivo. Limites de nível e comportamento nativo continuam no Cobblemon.
- Inventário, times dos jogadores, recompensas/cooldowns e arquivos antigos não são migrados ou resetados.

Erros de JSON seguem a política existente: um backup válido pode ser recuperado com registro no log; sem backup válido, a recarga falha e preserva a configuração em memória. O bônus não depende de OP/LuckPerms e não concede permissão ou bypass.

## Validação

Os arquivos `test-results-guard.json`, `test-results-without-guard.json`, `dialogue-test-results.json` e `verification.json` acompanham esta entrega com os resultados efetivamente executados. O teste de XP usa um jogador TCP real, regiões reais do Guard e o caminho nativo de experiência do Cobblemon; também executa batalha Showdown até o KO final. O teste não valida renderização em cliente gráfico nem substitui a homologação da sua configuração específica em servidor. Nenhum servidor de produção foi alterado.
