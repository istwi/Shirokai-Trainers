Correção da batalha que abria com apenas “Go …”, sem enviar o Pokémon adversário e sem avançar.

O ator adversário agora implementa `EntityBackedBattleActor`, necessário para o primeiro `SwitchInstruction` no Cobblemon 1.8.3. Quando o desafio parte de um NPC próximo, ele fornece a origem do envio; o comando também funciona sem NPC, usando uma origem invisível temporária, independente por batalha e sem persistência no mundo.

- Pokémon e IA continuam independentes por sessão; a equipe configurada do jogador/NPC não é substituída.
- A origem temporária e os Pokémon adversários são limpos ao encerrar ou falhar a batalha.
- Se a inicialização não concluir em 30 segundos, a batalha é abortada com erro registrado, sem recompensas ou novo cooldown.
- Logs distinguem solicitação de batalha de inicialização real dos dois lados.

Validação: compilação e suíte automatizada do núcleo, além de regressão no servidor dedicado com o motor real do Cobblemon. O teste reproduziu a ausência do adversário com o ator antigo e confirmou envio dos dois Pokémon e conclusão com vencedor usando o ator corrigido. O teste é um módulo separado, não incluído no JAR distribuído; a interface com cliente continua dependendo do reteste no servidor do usuário.

## Atualizar

Pare o servidor, remova apenas o JAR Shirokai Trainers 0.2.0 e coloque `shirokai-trainers-0.2.1.jar` em `mods/`. Mantenha `config/shirokai_trainers/` e o mundo; não é necessário recriar treinadores ou equipes. Reinicie e teste `/trainer brock`. Não deixe as duas versões do Shirokai instaladas juntas.

Compatibilidade mantida: Minecraft 1.21.1, Java 21, Fabric, Cobblemon **1.8.3+1.21.1**, Fabric API e Fabric Language Kotlin nas versões documentadas. Shirokai Trainers é instalado apenas no servidor e não depende de Cobblemon Trainer Battle.

[Comandos e permissões](https://github.com/istwi/Shirokai-Trainers/blob/main/docs/comandos-e-permissoes.md) · [Guia de testes](https://github.com/istwi/Shirokai-Trainers/blob/main/docs/guia-testes.md)
