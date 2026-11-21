# Diálogos nativos dos NPCs — Zorykai Trainers 0.3.3

Minecraft 1.21.1, Fabric, Java 21 e Cobblemon 1.8.3. Usa a tela de diálogo já existente no Cobblemon: nome, retrato, texto e botões. Nenhum mod cliente adicional ou pacote de recursos novo é necessário. A renderização e o formato da caixa continuam sendo os nativos do Cobblemon.

## Instalação

Com o servidor parado e backup das configurações/mundo, substituir o JAR anterior do Trainers por `shirokai-trainers-0.3.3.jar`. Manter somente uma cópia do mod. Os IDs técnicos, caminho `config/shirokai_trainers`, dados de batalha, recompensas, cooldowns, entidades, skins e vínculos existentes são preservados. Os NPCs anteriores mantêm o clique direto ou a confirmação de batalha até receberem um diálogo.

O Zorykai-menu é opcional para os diálogos. Para o botão de loja deste exemplo, manter o ZorykaiMenus instalado; a integração foi testada com sua versão 1.1.0. O Trainers não substitui o sistema de compras, vendas, saldo, permissões, descontos ou recuperação financeira do Zorykai-menu.

## Exemplo rápido de vendedor

Na primeira execução são criados `vendedor.json` e `treinador.json` em:

```text
config/shirokai_trainers/dialogues/
```

Arquivos existentes não são sobrescritos. Se o diretório já existir sem os modelos, use `dialogue-create` para criá-los com outro ID.

No jogo, como administrador:

```mcfunction
/traineradmin npc create-command vendedor
/traineradmin npc name vendedor &aMercador
/traineradmin npc dialogue vendedor vendedor
```

Clique direito no NPC como jogador comum. Ele apresenta texto e os botões Comprar, Informações e Sair. Comprar executa `zmenu` **como o jogador**, abrindo o menu principal configurado no Zorykai-menu. Os botões da loja continuam seguindo as regras desse mod.

Um NPC já existente pode receber o diálogo sem ser recriado:

```mcfunction
/traineradmin npc dialogue meu_npc vendedor
```

Também é possível escolher um diálogo no menu administrativo: `/traineradmin` → **NPCs Cobblemon** → NPC → **Diálogo Cobblemon**. Há opções de teste e desativação na mesma tela. O teste exige estar próximo do NPC e respeita as permissões reais do jogador.

## Configurar por JSON

Cada diálogo usa um arquivo próprio. Exemplo completo:

```json
{
  "schemaVersion": 1,
  "id": "vendedor",
  "title": "&aMercador",
  "startPage": "inicio",
  "timeoutSeconds": 120,
  "pages": [
    {
      "id": "inicio",
      "speaker": "npc",
      "text": "Olá, %player%! Como posso ajudar?",
      "vertical": false,
      "buttons": [
        {
          "id": "pokebolas",
          "label": "Pokébolas",
          "action": "command",
          "executor": "player",
          "command": "zmenu shop loja_pokebolas"
        },
        {
          "id": "informacoes",
          "label": "Informações",
          "action": "page",
          "page": "sobre"
        },
        {
          "id": "sair",
          "label": "Sair",
          "action": "close"
        }
      ]
    },
    {
      "id": "sobre",
      "speaker": "npc",
      "text": "Escolha os produtos no menu da loja.\nBoas compras!",
      "buttons": [
        {
          "id": "voltar",
          "label": "Voltar",
          "action": "page",
          "page": "inicio"
        },
        {
          "id": "sair",
          "label": "Sair",
          "action": "close"
        }
      ]
    }
  ]
}
```

O nome do arquivo deve acompanhar o ID: `vendedor.json` para `"id": "vendedor"`. IDs usam letras minúsculas, números, `_` e `-`, com até 64 caracteres.

- `title`: nome no cabeçalho. Vazio usa o nome atual do NPC, incluindo sua formatação.
- `startPage`: ID da primeira página.
- `timeoutSeconds`: de 15 a 3600; padrão 120, renovado ao trocar de página.
- `text`: texto da página, com `\n` para separar linhas.
- `speaker`: `npc` mostra nome/retrato do NPC à direita; `player` mostra nome/retrato do jogador à esquerda.
- `vertical`: mostra as opções em coluna. Com mais de três botões, a coluna é usada automaticamente.
- `label`: texto do botão.
- `permission`: permissão opcional do botão, por exemplo `zorykai.loja.vip`. Sem ela, a opção fica indisponível. É conferida novamente no servidor ao clicar.

Título, texto e rótulos aceitam cores/estilos Minecraft como `&a`, `&e` e `&l`. Essa formatação é independente do MiniMessage dos JSONs do Zorykai-menu. Variáveis de exibição: `%player%`, `%player_uuid%` e `%npc%`.

Até 32 páginas, de 1 a 6 botões por página e 2.000 caracteres de texto por página. Use textos curtos para uma apresentação legível. O layout de pixels, fonte e dimensões da janela seguem o renderizador nativo; os JSONs controlam conteúdo, orientação, retratos e ações.

### Ações de botão

| `action` | Campos adicionais | Comportamento |
|---|---|---|
| `command` | `command`, `executor` | Fecha o diálogo e executa o comando configurado |
| `page` | `page` | Abre outra página do mesmo diálogo |
| `battle` | `trainer` opcional | Inicia desafio pelo serviço existente do Trainers |
| `close` | nenhum | Encerra a conversa |

`executor` pode ser `player` ou `console`; o padrão é `player`. Para abrir menus e lojas do Zorykai-menu, use **player**. A opção console destina-se aos comandos administrativos explicitamente definidos pelo administrador e não concede OP ao jogador. Comandos são escritos sem `/` e aceitam apenas `%player%` e `%player_uuid%` como argumentos completos.

Para batalha, `trainer` pode indicar um ID específico. Sem esse campo, usa o treinador já vinculado ao NPC. As verificações existentes de equipe, cooldown, requisitos, simultaneidade e recompensas continuam no serviço do Trainers. Um alvo ausente/desativado deixa a opção indisponível.

Um comando ausente ou sem permissão de execução também deixa o botão indisponível. O servidor usa somente ações da configuração; texto enviado pelo cliente não vira comando. Ações terminais consomem a sessão antes de executar, evitando repetição por reenvio de clique.

## Zorykai-menu

Exemplos reais do repositório informado:

```text
zmenu                         → menu principal configurado
zmenu open main               → menu com ID main
zmenu shop loja_pokebolas      → loja migrada de Pokébolas
zmenu shop loja_breeding       → loja migrada de breeding
```

Usar os IDs que existem no seu servidor. Os arquivos migrados dessas lojas estão no repositório do Zorykai-menu; `loja_pokebolas` não é criada pelo Trainers. Em uma instalação nova do Zorykai-menu, a loja de demonstração tem ID `example`.

Preços, produtos, descontos VIP e confirmação ficam nos JSONs do Zorykai-menu. O NPC apenas abre o destino escolhido com a identidade e permissões do jogador. O diálogo é encerrado antes da abertura do inventário, sem fechar a loja em seguida.

## Recarregar e vincular

```mcfunction
/traineradmin npc dialogue-list
/traineradmin npc dialogue-create recepcao merchant
/traineradmin npc dialogue-create desafio battle
/traineradmin npc dialogue vendedor vendedor
/traineradmin npc dialogue-preview vendedor
/traineradmin npc dialogue-reload
/traineradmin npc reload
/traineradmin reload
```

- `dialogue-reload`: recarrega os arquivos de diálogo.
- `npc reload`: recarrega também os vínculos de `npcs.json`, sem recriar entidades.
- `traineradmin reload`: recarrega treinadores, vínculos e diálogos.

Para configurar o vínculo por arquivo, preservar os demais dados do NPC existente em `config/shirokai_trainers/npcs.json` e adicionar `"dialogue": "vendedor"` dentro do objeto desse NPC. Não substituir UUIDs ou o registro completo por um exemplo.

Para voltar ao clique anterior:

```mcfunction
/traineradmin npc dialogue vendedor off
```

O comando direto e o treinador anteriores não são apagados quando um diálogo é vinculado. Sem diálogo, voltam a valer. Uma recarga bem-sucedida encerra as conversas abertas para descartar botões antigos. Erros de configuração são reportados sem sobrescrever o arquivo; a configuração válida em memória é preservada quando a recarga falha. O mecanismo já existente de backups JSON permanece.

Conversas terminam ao sair do servidor, morrer, se afastar mais de oito blocos, alterar/remover o NPC ou atingir o tempo limite. O encerramento de uma sessão antiga não fecha outra conversa que a substituiu.

## Validação e limites

Compilação/remapeamento e 37 testes do núcleo aprovados. Integração local com o JAR de produção, Cobblemon 1.8.3, ZorykaiMenus 1.1.0, Fabric, LuckPerms e Impactor: 17 cenários por cliente TCP aprovados, incluindo interação com NPC, pacotes nativos, páginas, retrato, placeholders, permissões, comandos player/console, reenvio, distância, timeout, recarga JSON, compatibilidade do clique anterior, inventário real do Zorykai-menu e criação de batalha Cobblemon.

O teste lê o estado nativo do diálogo em uma fixture de console; entradas de diálogo e interação com NPC são enviadas pelo protocolo de rede. O decodificador vanilla consome os pacotes de apresentação de itens/metadados/receitas como bytes. Não houve renderização em cliente humano, teste visual do retrato/pixels ou batalha completa até a vitória. O teste de loja verificou abertura/permanência do inventário, sem ensaiar novas compras/pagamentos. Não foi alterado o servidor de produção. A fixture é separada e não está no JAR instalável.
