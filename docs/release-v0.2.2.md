# Shirokai Trainers 0.2.2

As lutas agora são acionadas por comando administrativo. O mod não integra, cria, vincula ou salva NPCs: EasyNPC e outros mods continuam responsáveis por cliques, diálogos, aparência e persistência.

Configure a ação do NPC para executar como console/servidor:

```text
traineradmin <jogador> battle <id_da_luta>
```

Também é aceita a ordem `traineradmin battle <jogador> <id_da_luta>`. Substitua `<jogador>` pelo placeholder disponibilizado pelo mod de NPC.

- Removidos o comando público `/trainer`, o vínculo por clique e os snapshots de NPC.
- Cada jogador recebe uma batalha Cobblemon independente, com equipe adversária, recompensas, progresso e cooldown próprios.
- A opção `Simultâneas` fica ativada por padrão para permitir vários jogadores na mesma configuração de luta.

## Atualizar

Pare o servidor, remova o JAR anterior e coloque `shirokai-trainers-0.2.2.jar` em `mods/`. Reinicie o servidor e configure a ação do NPC com o novo comando. Configurações de lutas e dados de jogadores existentes são preservados; arquivos antigos de vínculo/snapshot de NPC deixam de ser usados.

Validação: `./gradlew test :fabric:build` passou.
