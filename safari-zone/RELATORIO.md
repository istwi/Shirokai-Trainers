# Relatório de validação — Shirokai Safari

- Minecraft alvo: 1.21.1 / DataVersion 3955.
- 8,836 chunks Anvil e 176,720 seções lidas de volta.
- 85 estados de bloco conferidos com o relatório vanilla oficial.
- Todos os 26 IDs de bioma encontrados nas paletas reais dos chunks e conferidos nos recursos vanilla do servidor 1.21.1.
- 530,160 amostras de blocos de todas as seções comparadas com a matriz de geração.
- 37 arquivos Sponge v3: 720,691,200 blocos e igual quantidade de entradas de bioma comparados integralmente com a fonte.
- Os 26 pontos de visita foram conferidos nas células reais de bioma do volume armazenado.
- Rotas: 37 destinos alcançados, 144,666 nós caminháveis alcançados nos corredores. Dois blocos de altura livre; degrau máximo um bloco.
- Restaurador: 20.480 seções de uma cópia de região tiveram biomas trocados deliberadamente; o restaurador recuperou o arquivo inteiro byte por byte. O backup também foi verificado.
- Três testes unitários de codificação/segurança passaram.

## Pendências de homologação

Não foi iniciado um servidor com este mundo: a EULA não foi aceita em nome do operador. Não houve cliente, importação no Multiworld, colagem real no WorldEdit, benchmark multiplayer ou teste dos datapacks/spawns Cobblemon. Os arquivos foram efetivamente gerados; isso não substitui homologação em jogo. O nome/versão exatos do Multiworld ainda são necessários para um comando de importação específico.

As cavernas possuem escadas e galerias. O teste de navegação cobre os corredores das rotas e escadas; não prova a acessibilidade de cada câmara natural, de cada bloco do terreno ou de todos os trechos de água.

## Coordenadas aproximadas de visita

| Bioma real | X | Y | Z | Área superficial aproximada |
|---|---:|---:|---:|---:|
| `minecraft:flower_forest` | -390 | 76 | -70 | 148736 |
| `minecraft:dark_forest` | -580 | 83 | -260 | 122064 |
| `minecraft:bamboo_jungle` | 400 | 81 | 30 | 162080 |
| `minecraft:taiga` | -320 | 88 | -430 | 64512 |
| `minecraft:forest` | -180 | 85 | -180 | 52512 |
| `minecraft:jungle` | 540 | 83 | 230 | 97072 |
| `minecraft:cherry_grove` | 80 | 95 | -250 | 80032 |
| `minecraft:snowy_taiga` | -170 | 92 | -600 | 68192 |
| `minecraft:plains` | 0 | 77 | 0 | 92272 |
| `minecraft:meadow` | -60 | 105 | -370 | 43856 |
| `minecraft:savanna` | -70 | 77 | 390 | 126976 |
| `minecraft:snowy_plains` | 220 | 85 | -500 | 76880 |
| `minecraft:ice_spikes` | 460 | 92 | -540 | 207520 |
| `minecraft:stony_peaks` | -530 | 160 | -580 | 101216 |
| `minecraft:jagged_peaks` | 70 | 176 | -690 | 39744 |
| `minecraft:desert` | -300 | 80 | 580 | 104896 |
| `minecraft:badlands` | -590 | 102 | 440 | 196896 |
| `minecraft:swamp` | 150 | 71 | 260 | 44960 |
| `minecraft:mangrove_swamp` | 313 | 69 | 450 | 23840 |
| `minecraft:deep_ocean` | 574 | 65 | 642 | 169040 |
| `minecraft:warm_ocean` | 630 | 65 | 410 | 58192 |
| `minecraft:river` | -145 | 65 | -39 | 25024 |
| `minecraft:beach` | 304 | 67 | 469 | 142400 |
| `minecraft:mushroom_fields` | 656 | 70 | 621 | 13104 |
| `minecraft:dripstone_caves` | 189 | 24 | -340 | subterrâneo |
| `minecraft:lush_caves` | -233 | 24 | 130 | subterrâneo |
