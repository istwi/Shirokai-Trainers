# JAR de teste com NPCs independentes

Substitua o JAR anterior com o servidor parado. Esta compilação reúne a branch `feat/independent-command-npcs` até `66d1b48` com as melhorias da main: cooldown em horas/minutos/segundos e cores/estilos nos nomes dos NPCs. Preserva skins por nick/URL, notificações de recompensas e revisão de permissões antes de aplicar skins.

O arquivo `.sha256` permite verificar a integridade do JAR. Teste dentro do jogo ainda pendente.

```text
/traineradmin npc create-command portal
/traineradmin npc name portal &5&lPortal
/traineradmin npc skin portal player Notch
/traineradmin npc command portal console tp %player% 100 70 200
```

O mesmo JAR está disponível em `downloads/` e `releases/`.
