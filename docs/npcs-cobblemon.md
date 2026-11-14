# NPCs nativos do Cobblemon

Alvo: Minecraft 1.21.1, Fabric, Cobblemon **1.8.3+1.21.1**. Sem EasyNPC.

## API consultada

Fonte oficial, tag `1.8.3`, commit `ffe005511dd0d3ba68377fa3f95906b3837d9a0e`:

- [NPCEntity.kt](https://gitlab.com/cable-mc/cobblemon/-/blob/1.8.3/common/src/main/kotlin/com/cobblemon/mod/common/entity/npc/NPCEntity.kt): construtor `NPCEntity(Level)`, propriedades `npc`, `forcedResourceIdentifier`, `appliedAspects`, `isMovable`, `initialize(1)` e `updateAspects()`.
- [SpawnNPCCommand.kt](https://gitlab.com/cable-mc/cobblemon/-/blob/1.8.3/common/src/main/kotlin/com/cobblemon/mod/common/command/SpawnNPCCommand.kt): sequência oficial de criação, inicialização e `addFreshEntity`.
- [NPCClasses.kt](https://gitlab.com/cable-mc/cobblemon/-/blob/1.8.3/common/src/main/kotlin/com/cobblemon/mod/common/api/npc/NPCClasses.kt): `classes` e `getByIdentifier` consultam classes realmente carregadas de datapacks.
- [NPCPlayerTexture.kt](https://gitlab.com/cable-mc/cobblemon/-/blob/1.8.3/common/src/main/kotlin/com/cobblemon/mod/common/entity/npc/NPCPlayerTexture.kt): bytes da textura e modelos `DEFAULT`, `SLIM`, `NONE`.

`NPCEntity.mobInteract` chama a interação configurada na entidade/classe na mão principal. O callback Fabric `UseEntityCallback` consome a interação dos NPCs indexados antes desse método, inclusive mão secundária e editor nativo. NPCs não indexados continuam com seu comportamento original. Nenhum evento fictício do Cobblemon foi adicionado.

`NPCEntity.saveWithoutId/load` grava e recupera classe, recurso forçado, aspectos, textura de jogador e demais propriedades no NBT. Flags vanilla de AI, gravidade, nome e UUID também pertencem ao salvamento da entidade.

## Administração

Tudo requer `shirokai.admin` (fallback OP nível 2), inclusive cada ação de menu e o clique de seleção. `/traineradmin` → **NPCs Cobblemon** abre a lista paginada e o painel de cada NPC. Ações com texto livre mostram o comando correspondente; ações de mover, parar, vincular a um treinador da lista, desvincular e remover têm botões. Remover pelo menu solicita confirmação.

| Comando após `/traineradmin npc` | Ação |
| --- | --- |
| `menu`, `help`, `list`, `classes` | Menu, ajuda, índice (inclui removidos), classes disponíveis |
| `create <npc> <treinador>` | Cria entidade nativa na posição/dimensão/rotação do administrador, parada |
| `show <npc>` | UUID, propriedade da entidade, vínculo, dimensão, posição, mensagens e aparência atual |
| `select <novo_id_npc> <treinador>` | Próximo clique direito em NPC Cobblemon existente o vincula (60s) |
| `unselect` | Próximo clique desvincula (60s), sem apagar entidade |
| `cancel` | Cancela seleção pendente |
| `link <npc> <treinador>` | Altera vínculo de um NPC indexado; treinador deve existir |
| `unlink <npc>` | Externo: retira índice, preserva entidade. Próprio: mantém entidade/índice sem treinador |
| `remove <npc>` | Remove somente entidade criada pelo Trainers, preservando treinador e progresso |
| `name <npc> <nome com espaços>` | Nome exibido |
| `class <npc> <namespace:classe>` | Classe carregada pelo Cobblemon; preserva nome |
| `resource <npc> <namespace:recurso\|default>` | Recurso de aparência ou retorno ao recurso da classe |
| `aspects <npc> <aspecto1,aspecto2\|clear>` | Substitui aspectos aplicados; variações da classe continuam presentes |
| `skin <npc> <arquivo.png> default\|slim` | Textura local de jogador via dados sincronizados nativos |
| `skin <npc> player <nick>` | Busca skin oficial Java pela Mojang, detectando braços automaticamente (`nick` também é aceito no lugar de `player`) |
| `skin <npc> url <https://imagem.png> [default\|slim]` | Baixa PNG direto por HTTPS; modelo padrão `default` |
| `skin <npc> clear` | Remove textura personalizada e cancela download pendente |
| `stationary <npc> true\|false` | Desativa/ativa AI, movimento e gravidade; não implementa rotas |
| `move <npc>` | Move para posição e dimensão atuais do administrador, inclusive MultiWorld |
| `rotate <npc> <yaw> [pitch]` | Rotação; pitch entre -90 e 90 |
| `message <npc> <texto>` | Mensagem ao clicar |
| `confirmation <npc> <texto>` | Título e botão da confirmação |
| `confirm <npc> true\|false` | Confirmação em inventário ou desafio direto pelo clique |

Nome do NPC e ID do treinador são independentes. `blue_npc` pode exibir `Blue` e apontar para `blue`. Não existe cópia de treinador dentro do NPC.

### Aparência e skins

`class` valida a classe no registro real. `resource` identifica um recurso de renderização do Cobblemon, **não uma URL, caminho de PNG ou ID de textura isolado**. A presença de um recurso/modelo e a utilidade de cada aspecto dependem dos recursos instalados nos clientes. O servidor não consegue validar registros de renderização exclusivos do cliente. Use `classes` e recursos conhecidos; datapacks/resource packs adicionais precisam ser distribuídos pelo operador.

Skins personalizadas são suportadas nativamente na API 1.8.3. Coloque, no servidor, `config/shirokai_trainers/npc-skins/blue.png`, PNG 64×64 ou 64×32, até 1 MiB. O comando envia os bytes no campo nativo `NPC_PLAYER_TEXTURE` e configura `model-default`/`model-slim`. Cobblemon salva os bytes no NBT e os sincroniza com clientes; Shirokai Trainers continua server-side. A partir da 0.3.2 também há download por URL e consulta de nick oficial, sem dependência de outro mod de NPC. O administrador deve fornecer um arquivo apropriado; o resultado visual precisa de teste com cliente Cobblemon.

### Skin por nick ou URL (0.3.2)

```text
/traineradmin npc skin blue_npc player Notch
/traineradmin npc skin blue_npc nick Notch
/traineradmin npc skin blue_npc url https://seu-site.com/blue.png default
/traineradmin npc skin blue_npc url https://seu-site.com/blue.png slim
```

Nick consulta perfil **oficial Java na Mojang** e detecta `default`/`slim`; nomes locais/offline e skins definidas por SkinRestorer não são consultados. Se o perfil não tiver skin personalizada ou não existir, o comando informa o erro e preserva a aparência atual. URL precisa retornar os bytes de uma imagem PNG 64×64 ou 64×32, até 1 MiB; páginas de sites de skins não são imagens diretas. Use HTTPS na porta padrão, sem credenciais. Downloads aceitam até três redirecionamentos, verificam destinos públicos e têm timeout de conexão/leitura de 10 segundos. Não desativam TLS.

O comando confirma o início do download e depois anuncia sucesso/erro. Dois workers com fila limitada fazem rede e validação fora da thread principal. Apenas o resultado validado é aplicado na thread Minecraft, rechecando permissão, conexão do administrador e identidade do NPC. Uma solicitação de skin mais recente ou `clear` invalida downloads anteriores. Se o NPC for removido, desvinculado externamente ou descarregado durante o download, o resultado não cria/recarrega uma entidade; o administrador deve tentar novamente com o NPC carregado.

A skin aplicada é uma cópia persistida em NBT pelo Cobblemon: reinícios e reloads não precisam fazer downloads novamente, e mudanças posteriores na skin do jogador não atualizam o NPC automaticamente. Reexecute o comando para atualizar. O servidor precisa acessar `api.mojang.com`, `sessionserver.mojang.com` e `textures.minecraft.net` para nick, ou o host HTTPS informado para URL.

Testes automatizados usam respostas simuladas das APIs oficiais: perfil/base64, ambos os modelos de braços, upgrade do host de textura para HTTPS, PNG e dimensões/tamanho, nick/URL inválidos, perfil sem skin e exclusão de endereços privados. Acesso real às APIs e renderização/persistência com clientes ainda precisam de teste dentro do jogo. Verifique também duas solicitações consecutivas, `clear` durante download, desconexão/revogação de permissão, NPC removido/descarregado e falhas HTTP.

## Fluxo de batalha

Jogador comum clica com botão direito, lê a mensagem e confirma (ou desafia diretamente se `confirm false`). Confirmar exige NPC vivo, no mesmo mundo e a até oito blocos. Um vínculo alterado/removido é consultado novamente; não se mantém uma cópia obsoleta do treinador no menu.

O clique chama exatamente `ShirokaiTrainers.challenge(player, trainerId, null)`, usado pelos comandos administrativos existentes. Continua usando dificuldades atuais, requisitos, permissões, cooldown, simultaneidade e validação da equipe. A sessão conserva seu snapshot original. Vitórias/derrotas e entregas continuam em `finish`/`BattleLedger`/`RewardEngine`, inclusive chances, pesos, comandos e limites. Não há outro executor de recompensas.

Cliques na mão secundária são consumidos, cliques principais têm debounce de 750 ms por jogador e a reserva existente rejeita batalha/sessão ativa do mesmo jogador. A flag `Trainer.simultaneous` continua decidindo se outro jogador pode desafiar o mesmo treinador. NPC já em batalha nativa não pode ser selecionado para vínculo ou usado para desafio Trainers.

## Persistência, remoção e recuperação

Estratégia única: **Minecraft/Cobblemon salva entidades; Trainers nunca restaura/spawna entidades a partir do índice**. Criar é a única operação que instancia um NPC. Nome, aparência, AI e localização ficam no NBT. `config/shirokai_trainers/npcs.json` guarda UUID, ID administrativo, ID do treinador, propriedade, mensagens e última dimensão/posição observadas. Escrita usa `JsonStore`, com arquivo temporário, fsync, substituição atômica e backups existentes.

O índice é carregado em `SERVER_STARTING`, antes dos chunks. Eventos de carga/descarga atualizam a localização observada; dimensões usam `ResourceKey` real, sem nomes de mundo presumidos. Consultar/editar tenta localizar UUID carregado e carregar o último chunk conhecido, sem criar substitutos. Se entidades ainda estão carregando, carregue o local e repita a operação. Não há tickets permanentes de chunk.

NPC desaparecido ou dimensão ausente produz erro e mantém o registro. Treinador ausente mantém o vínculo e informa o erro; use `link` para corrigir. `remove` mantém uma marca persistente de exclusão: se a entidade estiver descarregada, ela é descartada ao carregar, inclusive após reinício. O ID removido fica reservado para impedir reuso acidental da identidade. `list` inclui essas marcas. Nenhuma remoção apaga treinador, histórico ou recompensas. NPC externo só aceita `unlink`; sua entidade e propriedades são preservadas e a interação nativa volta a funcionar. Mudanças administrativas feitas em sua aparência/posição não são revertidas ao desvincular.

`reload` continua recarregando treinadores; não reaplica ou recria NPCs. Arquivos anteriores de treinadores, progresso e sessões não mudam de formato; o índice novo é aditivo, `schemaVersion: 1`. Uma queda antes de o Minecraft salvar uma entidade recém-criada pode deixar registro sem entidade; ele fica visível para diagnóstico, sem respawn automático que arriscaria duplicação.

## Exemplo completo

Como administrador:

```text
/traineradmin create blue
/traineradmin name blue Blue
/traineradmin team blue normal add
/traineradmin pokemon blue normal 1 {"species":"squirtle","level":5,"moves":["tackle"]}
/traineradmin settings blue normal {"cooldownSeconds":60}
/traineradmin rewardgroup blue normal win fixas INDEPENDENT
/traineradmin reward blue normal win fixas diamante {"kind":"ITEM","value":"minecraft:diamond","chance":100}
/traineradmin rewardgroup blue normal win sorteio INDEPENDENT
/traineradmin reward blue normal win sorteio ouro {"kind":"ITEM","value":"minecraft:gold_ingot","chance":25}
/traineradmin reward blue normal win fixas aviso {"kind":"COMMAND","value":"tellraw %player% {\"text\":\"Vitória contra Blue!\"}","chance":100}
/traineradmin npc create blue_npc blue
/traineradmin npc name blue_npc Blue
/traineradmin npc class blue_npc cobblemon:standard
/traineradmin npc skin blue_npc blue.png default
/traineradmin npc message blue_npc Sou Blue. Quer me desafiar?
/traineradmin npc confirmation blue_npc Desafiar Blue?
/traineradmin npc stationary blue_npc true
```

O comando `skin` pressupõe o PNG local instalado. Pode omiti-lo e usar a aparência da classe. Um jogador sem OP, com Pokémon apto, clica direito e confirma. Ao vencer, o sistema existente concede um diamante, executa o comando de aviso e sorteia o ouro por chance de 25%; `/trainerstatus` e `/trainerclaim` mantêm suas funções. Para mover, vá a outra posição/mundo e use `/traineradmin npc move blue_npc`. Para vincular entidade externa, `/traineradmin npc select blue_externo blue` e clique nela; `/traineradmin npc unlink blue_externo` preserva a entidade.

## Verificações e roteiro dentro do jogo

Testes automatizados novos cobrem round trip de UUID/dimensão/mensagens, unicidade de IDs e UUIDs, tombstones próprios, rejeição de exclusão externa, esquema inválido e preservação byte a byte dos arquivos de treinador/jogador durante desvínculo. A suíte existente cobre sorteios/chances, limites, requisitos de recompensas, sessões exclusivas/simultâneas, snapshots de resultados e comandos seguros.

A validação Fabric exige `./gradlew test :fabric:build`; o harness existente de batalhas é `./gradlew :fabric:runBattleSmoke`, após o operador aceitar EULA em seu mundo isolado. Nenhum desses comandos substitui aceitação com cliente.

Ainda é necessário testar em jogo:

1. Criar, consultar, alterar nome/classe/aspectos/skin, parar, mover entre dimensões e girar. Conferir aparência em dois clientes.
2. Vincular NPC externo, cancelar/expirar seleção, revogar permissão durante seleção/menu, desvincular e confirmar que a entidade continua com interação nativa. Usuário comum não administra.
3. Jogador sem OP desafia; repetir clique e botão de confirmação sem criar sessão duplicada. Verificar requisito negado, cooldown, dois jogadores com `simultaneous` true/false e NPC em batalha nativa.
4. Vencer/perder, verificar itens, comando, sorteio por chance (zero/100 e amostra intermediária), limites e histórico. Editar treinador durante batalha: sessão atual usa snapshot, próxima usa configuração nova.
5. Salvar e reiniciar; descarregar/carregar chunk; `reload`; confirmar UUID e contagem de entidades sem duplicação e aparência persistida. Repetir em dimensão MultiWorld.
6. Remover NPC próprio carregado/descarregado, reiniciar antes de recarregar o chunk e conferir tombstone. Treinador e progresso permanecem. Mundo ausente, entidade apagada externamente e treinador ausente informam erro sem apagar índice.

### Resultado desta execução na nuvem

- Consultados os fontes oficiais da tag 1.8.3 acima, inclusive criação, interação e leitura/escrita NBT.
- Instalados Temurin JDK 21.0.9+10 e Gradle 8.14.3 com SHA-256 verificado; wrapper executado com proxy e CA do sistema, sem desabilitar TLS.
- **23 testes do core aprovados**, zero falhas e zero ignorados: `CoreTest` 16, `ShowdownTest` 3, `NpcRegistryTest` 4. Executados com build auxiliar em `/workspace/core-check` que aponta para o mesmo módulo `core`, sem alterar os manifests/dependências do repositório. Esse desvio foi necessário porque até `-PcoreOnly` resolve Fabric Loom declarado na raiz.
- `git diff --check` passou.
- `./gradlew test :fabric:build` **falhou antes da compilação Fabric**, na resolução de `fabric-loom:1.11.8`; o proxy retornou 403 para `maven.fabricmc.net` e `artefacts.cobblemon.com`. Não foi produzido JAR validado da nova integração.
- Servidor, harness de batalhas e cenários com cliente **não executados**. Os testes do core não demonstram spawn/renderização, clique real, teleporte, unload/restart de entidades, nem entrega de comandos dentro do Minecraft.
- Salvos no rascunho do ambiente `install_script` (JDK, ativação, proxy/CA e wrapper), `start_skill` (ativação, comandos e bloqueios) e concessões de rede para Fabric/Cobblemon/Minecraft. Salvar o rascunho não aplica nem publica. Após revisar/salvar nas configurações e publicar o ambiente, retomar a compilação Fabric e corrigir qualquer incompatibilidade que ela revelar antes de distribuir o mod.
