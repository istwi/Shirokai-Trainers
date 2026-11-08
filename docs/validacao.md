# Validação e critérios de aceitação

## Evidências automatizadas

- `./gradlew test :fabric:build`: compilação e JAR remapeado.
- 19 testes do núcleo: valores de Pokémon, chances extremas, distribuição por peso, primeira vitória, cooldowns/permissões/limites, sessões independentes, bloqueio de simultaneidade, repetição de resultado, entrega interrompida, reset individual, recuperação de JSON, JSON estrito, execução segura de templates e três verificações de intercâmbio Showdown.
- JSON estrito rejeita chaves duplicadas, comentários, documentos adicionais e NaN.

O ambiente de desenvolvimento usa ICU4J 71.1 no runtime porque o POM de desenvolvimento do Cobblemon 1.8.3 não inclui esse pré-requisito de seu GraalJS. O artefato de produção do Cobblemon fornece seu próprio runtime; não empacotar uma segunda cópia dele no Shirokai Trainers.

## Verificações no servidor dedicado desta tarefa

- Inicialização completada com Cobblemon 1.8.3, Shirokai Trainers e dependências declaradas, sem EasyNPC e sem Cobblemon Trainer Battle; motor Showdown carregado.
- Pelo console: treinador `smoke` criado; equipe editada para Geodude nível 15; espécie inexistente rejeitada; configuração recarregada e exportada em Showdown. Após reiniciar, treinador e equipe foram carregados novamente.
- Configuração contendo recompensa de comando `give %player% minecraft:diamond 1` validada pelo dispatcher e salva. A concessão a jogador real ainda não foi exercitada.
- Os comandos vanilla de entidade do console exigiram `execute in minecraft:overworld run ...` para fornecer o contexto de dimensão nesse runtime.
- A consulta de chaves públicas Mojang falhou por DNS na biblioteca de autenticação. Isso não impediu carregamento nem os testes administrativos locais; autenticação de clientes online não foi validada.

Os fixtures de teste permanecem apenas em `fabric/run/`, ignorado pelo Git.

**Compilação e testes unitários não comprovam os 12 critérios de conclusão do TXT.** O mod permanece em validação até executar o roteiro abaixo com clientes compatíveis.

## Roteiro com servidor e clientes

Use um mundo de teste, Cobblemon 1.8.3 e clientes Minecraft 1.21.1 compatíveis. Registre versão exata do EasyNPC e LuckPerms, UUIDs dos jogadores, IDs de batalhas e resultado observado. Cobblemon Trainer Battle deve permanecer completamente ausente em todas as etapas.

1. Administrador: criar treinador pelo jogo; adicionar e editar os seis Pokémon; validar rejeição de espécie, forma, Ability e movimento desconhecidos, EVs totais >510 e IVs >31; testar import/export e modelos.
2. Instalar EasyNPC compatível; criar NPC e configurar sua ação de clique para executar como console/servidor `traineradmin <jogador> battle <id_da_luta>`. Verificar que o mod não altera os diálogos, ferramentas, aparência ou persistência do EasyNPC.
3. Jogador sem OP: confirmar que `/trainer` não existe. Acionar `/traineradmin <jogador> battle <id_da_luta>` pelo console/EasyNPC e confirmar motor Cobblemon, seis Pokémon adversários configurados, IA, movimentos e ausência de mudança de nível/equipe própria.
4. Concluir vitória, derrota e fuga; desconectar durante batalha. Confirmar que só vitória/derrota confirmadas concedem os respectivos grupos; verificar uma única gravação por ID de batalha.
5. Testar recompensa fixa de item, Pokémon no time e overflow no PC, comandos de servidor, inventário/PC cheio e recuperação manual. Simular interrupção entre IN_FLIGHT e DELIVERED; não repetir automaticamente.
6. Configurar chance 0/100, pesos 1/3, grupo fixo+aleatório, primeira vitória, permissão, scoreboard, requisito de vitória anterior, cooldown e limite de claims; verificar elegibilidade e logs.
7. Dois jogadores: desafiar o mesmo treinador simultaneamente, confirmar UUIDs independentes de Pokémon/atores, vencer uma batalha e perder outra. Repetir com `simultaneous: false` e confirmar bloqueio.
8. Testar seleção manual e automática de dificuldades; verificar requisitos faltantes, objetivos e ginásios.
9. Encerrar e reiniciar servidor; conferir vitórias, derrotas, cooldowns e entregas. Resetar um jogador e comparar os dados do outro antes/depois.
10. Recarregar configuração válida durante uma batalha; depois introduzir JSON inválido e confirmar preservação/recuperação com log, sem alteração parcial da configuração ativa. Testar negação de edição de comandos e cliques administrativos após revogação de permissão.
11. Remover EasyNPC e repetir criação, desafios e batalhas por comando. Confirmar que Shirokai Trainers não precisa ser instalado no cliente.

## Limitações conhecidas a validar

- EasyNPC não é integrado pelo mod. A configuração do NPC e o placeholder de jogador pertencem à instalação do operador; a ação deve executar o comando de batalha como console/servidor.
- Intercâmbio Showdown cobre os campos do editor. Campos adicionais são rejeitados explicitamente.
- Ao reiniciar abruptamente, o motor Cobblemon perde batalhas em andamento; elas não são retomadas. Não inferir vitória de uma sessão desaparecida.
- Não há promessa de execução exatamente uma vez para comandos arbitrários; existe revisão explícita de entregas incertas.

## Versão 0.2.0

Cinco testes adicionais cobrem: recuperação do sorteio original após interrupção, encerramento ABORTED de sessão sem resultado, repetição de journal já aplicada, entrega adiada por falta de espaço e elegibilidade de recompensas garantidas. O build compila os seletores de Pokémon no inventário e os comandos de configuração parcial.

A aceitação final dentro do Minecraft continua pendente e será executada com o usuário ao final, conforme solicitado. Os testes automatizados não substituem o teste de dois clientes, EasyNPC/LuckPerms, menus, interação e entrega real. Não declarar essas verificações como aprovadas antes da execução.

## Regressão de início de batalha — 0.2.1

O teste dedicado reproduziu o problema: `TrainerBattleActor` sem `EntityBackedBattleActor` não recebe Pokémon ativo no primeiro `SwitchInstruction` do Cobblemon 1.8.3. Com `EntityTrainerBattleActor`, os dois Pokémon foram enviados e a batalha real por IA terminou com vencedor. Resultado observado: `success=true`, `legacyMissingOpponent=true`, `fixedSpawnedBoth=true`. O harness adia as escolhas dos dois bots até o fim do tick para simular o tempo de escolha do jogador e evitar despacho prematuro em AI-versus-AI.

A primeira tentativa do harness confirmou o envio mas não avançou por causa desse agendamento dos bots; foi corrigido apenas no módulo de teste e a regressão foi repetida com sucesso. Não foi declarado teste de interface com um cliente humano. A correção também inclui timeout de inicialização e ausência de novo cooldown em ABORTED.
