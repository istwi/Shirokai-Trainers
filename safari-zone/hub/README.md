# Hub Floresta para Safari V6

Hub independente, 112 × 112 blocos, quatro casas com interiores, duas barracas, oito espaços para NPCs, spawn central, dois lagos, ponte, jardins e iluminação. Madeira, pedra com musgo e cerejeiras combinam com a clareira central da V6. Os NPCs e serviços são configurados pelo operador; este schematic contém a construção e os espaços reservados.

## Colocar na clareira

Faça backup da dimensão. Em Minecraft Java 1.21.1, use WorldEdit Fabric com leitura Sponge v3. Copie safari_hub_floresta.schem para a pasta de schematics. Entre na dimensão Safari e execute:

```
/tp @s -56 70 -56
//schem load safari_hub_floresta
//paste
/tp @s 0 77 0
```

A origem do schematic é o canto mínimo (-56,70,-56); a base caminhável fica em Y76. Não use -a: o ar limpa os interiores. Cole sem -b para manter os biomas da dimensão. O volume substituído vai de X/Z -56 a55 e Y70 a117. O hub não altera os arquivos do mundo V6 distribuído separadamente. Para definir o spawn no Isaiah Multiworld, posicione-se em (0,77,0) na dimensão Safari e use /mw setspawn.

As posições sugeridas para NPCs constam em hub_layout.json. Todos os oito pontos, as quatro casas e quatro acessos foram verificados por navegação em blocos. Os 602.112 blocos do schematic foram relidos e comparados com a fonte; estados verificados contra registros oficiais 1.21.1. Não houve teste desta construção no cliente Minecraft ou colagem real pelo WorldEdit.

hub_planta.png é a planta dos blocos; maps/preview_hub_floresta.png é uma projeção técnica com texturas e formas simplificadas, não uma captura do jogo. Para reproduzir, instale numpy, nbtlib==2.0.4 e pillow e execute python build_hub.py pasta-destino. render_hub.py aceita a pasta gerada e o caminho do JAR oficial de cliente 1.21.1 para ler texturas (JAR não incluído).

## Espaços para NPCs

- Recepcao / guia Safari: [-29, 77, -32]
- Centro de cuidado: [26, 77, -33]
- Pesquisador / missoes: [-32, 77, 30]
- Loja / trocas: [28, 77, 37]
- Mercador / servico opcional: [-19, 77, -15]
- Mercador / servico opcional: [-15, 77, -15]
- Mercador / servico opcional: [-20, 77, 11]
- Mercador / servico opcional: [-16, 77, 11]
