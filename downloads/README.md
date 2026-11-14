# JAR de teste com NPCs independentes

Substitua o JAR anterior com o servidor parado. Esta compilação reúne a main até `713bc4d` (skins por nick/URL, notificações de recompensas e revisão de permissões antes de aplicar skins) com os NPCs independentes de comandos da PR #1.

31 testes passaram e a compilação Fabric concluiu com sucesso. Teste dentro do jogo ainda pendente.

```text
/traineradmin npc create-command portal
/traineradmin npc skin portal player Notch
/traineradmin npc command portal console tp %player% 100 70 200
```

O JAR 0.3.0 anterior foi substituído, pois não incluía as alterações recentes da main.
