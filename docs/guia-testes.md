# Teste da pré-release 0.2.1

Este roteiro é para a aceitação final no jogo. Os passos abaixo ainda não foram marcados como aprovados.

## Instalação

Servidor Minecraft 1.21.1, JDK 21, Fabric Loader >=0.17.2, Fabric API >=0.116.6+1.21.1, Fabric Language Kotlin >=1.13.6+kotlin.2.2.20 e Cobblemon **1.8.3+1.21.1**. Adicionar `shirokai-trainers-0.2.1.jar` ao diretório `mods/` do servidor. O Shirokai Trainers não precisa ser instalado nos clientes; eles precisam do Cobblemon compatível.

Para EasyNPC, conferir as dependências da versão escolhida. A branch 1.21.1 investigada exige Loader >=0.18.3 e Fabric API >=0.116.7+1.21.1. Não instalar Cobblemon Trainer Battle. Usar mundo e dados de teste; as versões anteriores estão preservadas nos backups de configuração.

## 1. Criar e configurar

Como administrador com `shirokai.admin` ou OP nível 2:

```text
/traineradmin create rocha
/traineradmin name rocha Mestre Rocha
/traineradmin team rocha normal add
/traineradmin pokemon rocha normal 1 {"species":"geodude","level":15,"nature":"adamant","moves":["tackle","rockthrow"]}
/traineradmin settings rocha normal {"cooldownSeconds":60,"skill":3}
/traineradmin dialogue rocha win &aVocê venceu!|&eParabéns!
/traineradmin edit rocha
```

No menu, trocar espécie/forma/Nature/Ability/movimentos/item, nível, Shiny, IVs e EVs. Clicar com botão direito reduz valores. Verificar rejeição de EVs totais >510 e de movimentos repetidos. Shift-click, arrastar, teclas numéricas e clicar no inventário inferior não podem retirar os itens de decoração do menu. Revogar permissão com menu aberto deve impedir edição.

## 2. Recompensas

```text
/traineradmin rewardgroup rocha normal win fixas INDEPENDENT
/traineradmin reward rocha normal win fixas diamante {"kind":"ITEM","value":"minecraft:diamond","chance":100,"max_claims_per_player":2}
/traineradmin rewardgroup rocha normal win sorteio WEIGHTED_ONE
/traineradmin reward rocha normal win sorteio ouro {"kind":"ITEM","value":"minecraft:gold_ingot","weight":3}
/traineradmin reward rocha normal win sorteio esmeralda {"kind":"ITEM","value":"minecraft:emerald","weight":1}
/traineradmin rewardgroup rocha normal loss derrota INDEPENDENT
/traineradmin reward rocha normal loss derrota pedra {"kind":"ITEM","value":"minecraft:stone","chance":100}
```

Vitória deve conceder diamante e apenas um item do sorteio; derrota deve conceder apenas pedra. Testar chance 0/100, limite de duas concessões e cooldown. Para item sem espaço, preencher o inventário: a entrega deve continuar PENDING, depois liberar espaço e usar `/trainerclaim`. `/trainerstatus` deve mostrar o progresso do próprio jogador.

Testar também recompensas POKEMON e COMMAND, com `value` contendo respectivamente JSON Pokémon e comando sem `/`. Conferir que comandos não concedem OP ao jogador e que placeholders são validados. Erros posteriores ao início de um efeito exigem revisão com `/traineradmin delivery`, e não uma repetição automática.

## 3. Batalha e simultaneidade

Com Pokémon aptos na equipe, um jogador **sem OP** executa `/trainer rocha`. Confirmar interface de batalha Cobblemon, equipe adversária definida, IA e resultado. Testar vitória, derrota, fuga e desconexão, relacionando os IDs nos logs.

Dois jogadores executam `/trainer rocha` simultaneamente. Cada um deve ter adversário independente; vencer uma batalha não deve encerrar a outra ou conceder recompensa ao participante errado. Em `/traineradmin edit rocha`, desativar simultaneidade e verificar bloqueio do segundo desafio. A equipe/níveis do jogador não podem mudar silenciosamente.

## 4. NPC e persistência

Criar NPC pelo EasyNPC ou pelos comandos nativos do Cobblemon. Executar `/traineradmin bind rocha`, clicar e `/traineradmin bindconfirm`. O jogador deve agachar e clicar com a mão principal vazia para desafiar; clique normal e ferramentas do EasyNPC continuam suas próprias funções.

```text
/traineradmin npcsave
/traineradmin npcrestore <uuid_npc> confirm
```

Salvar snapshot, mudar nome/aparência e mover a entidade; restaurar e conferir. Repetir em outra dimensão. Descarregar seu chunk não pode criar outra entidade nem apagar o registro. A restauração só trabalha sobre a entidade existente e carregada.

Encerrar e reiniciar servidor. Conferir NPC, posição, nome/aparência, vinculação, equipes, vitórias, derrotas, cooldown e entregas. Resetar apenas um jogador com `/traineradmin reset <uuid> confirm`; os dados do segundo devem permanecer intactos. Os comandos de inspeção de dados e revisão são administrativos.

## 5. Dificuldades, requisitos e intercâmbio

Criar `elite` com `/traineradmin difficulty rocha elite`, copiar um Pokémon com `/traineradmin copy rocha normal 1 rocha elite` e editar o nível da nova equipe. Usar `settings` e `requirements` para cooldowns e condições independentes. Validar permissão LuckPerms, mínimo de scoreboard, vitória anterior, número de ginásios e objetivo personalizado, com mensagem do requisito faltante.

Salvar/carregar modelo, exportar Showdown e importar pelo buffer documentado no README. Conferir IVs, EVs, Nature, Ability, movimentos, forma, Shiny e item. O formato intercambiado cobre os campos do editor; campos adicionais são rejeitados explicitamente.

## Relatar falha

Registrar versão do JAR e dos mods, comando/ação, resultado esperado, resultado observado, ID de batalha/treinador e trecho correspondente do log. Não marcar o mod como concluído enquanto os critérios do TXT não forem exercitados. Downloads ficam na Release correspondente do GitHub.
