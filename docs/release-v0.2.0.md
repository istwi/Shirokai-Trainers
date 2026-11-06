Pré-release para a rodada final de testes dentro do Minecraft.

## Download e instalação

Baixe **shirokai-trainers-0.2.0.jar** nos anexos e coloque em `mods/` do servidor. O checksum SHA-256, o guia de comandos/permissões e o guia de testes também estão anexados.

Requisitos: Minecraft 1.21.1, Java 21, Fabric Loader >=0.17.2, Fabric API >=0.116.6+1.21.1, Fabric Language Kotlin >=1.13.6+kotlin.2.2.20 e **Cobblemon 1.8.3+1.21.1**. Clientes precisam de Cobblemon compatível, sem instalar Shirokai Trainers. EasyNPC e LuckPerms são opcionais; confira suas dependências. Não precisa de Cobblemon Trainer Battle.

## Comandos e permissões

- Jogadores sem OP: `/trainer`, `/trainer <id> [dificuldade]`, `/trainerstatus`, `/trainerclaim`.
- Administração: `/traineradmin`, com a permissão **shirokai.admin** ou fallback Minecraft nível 2 quando o provedor não define uma decisão.
- LuckPerms: `/lp user SeuNick permission set shirokai.admin true`.
- [Guia completo de comandos, permissões e exemplos](https://github.com/istwi/Shirokai-Trainers/blob/main/docs/comandos-e-permissoes.md).
- [Roteiro dos testes finais](https://github.com/istwi/Shirokai-Trainers/blob/main/docs/guia-testes.md).

## Incluído

Editor por inventário de espécies, formas, Nature, Ability, movimentos, itens, níveis, Shiny, IVs/EVs e cópia entre equipes; importação/exportação Showdown e modelos; dificuldades e diálogos; requisitos e recompensas fixas/aleatórias; cooldowns e limites; sessões isoladas com equipe/IA própria; progresso por UUID e journal para recuperação; recompensas pendentes quando falta espaço; vínculo opcional com NPCs e snapshots de configuração/localização com backups.

## Validação

Compilação e 19 testes automatizados aprovados na preparação da versão. O workflow de publicação também exige `./gradlew test :fabric:build` antes de anexar os arquivos. Os testes finais com clientes, batalhas completas, dois jogadores simultâneos e EasyNPC/LuckPerms ainda precisam ser executados; esta pré-release não é uma declaração de validação para servidor público.
