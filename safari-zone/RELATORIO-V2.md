# Safari V2 — revisão natural

- 6909 árvores, com 8 espécies, troncos inclinados e galhos. Posições por sorteio; entropia dos resíduos módulo 7: {'x': 2.8067383315374776, 'z': 2.8069124098977496}, próxima do máximo de 2,807 bits (sem o padrão de grade da V1).
- Cerejeiras: alturas [4, 5, 6, 7] e raios-base de copa [4, 5, 6]; copas são montadas com vários lobos e ramos.
- 27 lagos com margens irregulares; água/gelo confirmado em todos, mínimo de 464 blocos na janela central de inspeção.
- Arbustos, vegetação por habitat, pétalas, samambaias/grama alta e solos variados. Caminhos seguem custos de inclinação e têm bordas/materiais variados.
- 12 câmaras subterrâneas com passagens 3D e entradas abertas; os biomas foram confirmados nos pontos reais de entrada e chegada.
- Busca de navegação: 49 destinos alcançados, incluindo todas as 12 câmaras, com dois blocos livres de altura e degrau máximo de um bloco nos corredores avaliados.
- 8836 chunks / 176720 seções lidas de volta. 136 estados de bloco conferidos com vanilla 1.21.1.
- 37 schematics Sponge v3; 720691200 blocos e a mesma quantidade de biomas comparados integralmente com o mundo fonte.
- Restauração offline testada: uma região deliberadamente alterada foi recuperada byte por byte, com backup. Três testes unitários de codificação e segurança passaram.

## Entradas das cavernas

- `lush_caves`: entrada **[-290, 97, 130]**; primeira câmara **[-150, 27, 185]**.
- `dripstone_caves`: entrada **[110, 121, -340]**; primeira câmara **[280, 27, -340]**.

## Instalar no Multiworld fornecido

Pare o servidor. Faça backup e renomeie `world/dimensions/multiworld/safari/region` para `region-v1-backup`. Copie `world/safari/region` deste pacote V2 para o local da pasta antiga. Substitua `world` pelo `level-name` real, se diferente. Não substitua o `level.dat` do mundo principal. Entre com `/mw tp safari` e `/tp @s 0 77 0`.

## Limites da validação

A V1 foi carregada pelo operador. Esta V2 foi verificada em arquivos e por navegação em voxels; ainda não foi avaliada visualmente num cliente Minecraft neste ambiente nem medida com os datapacks e jogadores do servidor. As imagens de prévia são projeções dos blocos e não capturas em jogo. O hub central foi conservado; esta revisão se concentra em paisagem, vegetação, caminhos e cavernas.

## Coordenadas dos biomas

| Bioma | X | Y | Z |
|---|---:|---:|---:|
| `minecraft:flower_forest` | -390 | 81 | -70 |
| `minecraft:dark_forest` | -580 | 96 | -260 |
| `minecraft:bamboo_jungle` | 400 | 92 | 30 |
| `minecraft:taiga` | -320 | 111 | -430 |
| `minecraft:forest` | -180 | 100 | -180 |
| `minecraft:jungle` | 540 | 82 | 230 |
| `minecraft:cherry_grove` | 80 | 105 | -250 |
| `minecraft:snowy_taiga` | -170 | 91 | -600 |
| `minecraft:plains` | 0 | 77 | 0 |
| `minecraft:meadow` | -60 | 115 | -370 |
| `minecraft:savanna` | -70 | 67 | 390 |
| `minecraft:snowy_plains` | 220 | 111 | -500 |
| `minecraft:ice_spikes` | 460 | 79 | -540 |
| `minecraft:stony_peaks` | -530 | 183 | -580 |
| `minecraft:jagged_peaks` | 70 | 169 | -690 |
| `minecraft:desert` | -300 | 86 | 580 |
| `minecraft:badlands` | -590 | 106 | 440 |
| `minecraft:swamp` | 160 | 69 | 231 |
| `minecraft:mangrove_swamp` | 330 | 70 | 450 |
| `minecraft:deep_ocean` | 575 | 68 | 640 |
| `minecraft:warm_ocean` | 630 | 65 | 410 |
| `minecraft:river` | -160 | 65 | -38 |
| `minecraft:beach` | 428 | 65 | 419 |
| `minecraft:mushroom_fields` | 580 | 71 | 623 |
| `minecraft:dripstone_caves` | 280 | 29 | -340 |
| `minecraft:lush_caves` | -150 | 29 | 185 |
