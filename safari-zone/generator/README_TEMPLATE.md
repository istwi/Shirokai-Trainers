# Shirokai Safari Zone V5 — Minecraft Java 1.21.1

Mapa procedural real de 1.500 × 1.500 blocos para uso com Fabric/Cobblemon 1.8.3. Entrega de teste: arquivos gerados e verificados em disco, ainda sem homologação dentro do servidor do operador.

## Revisão V5 — sem hub construído e sem trilhas pintadas nas cavernas

O centro é uma clareira plana de grama entre X/Z=-60 e 60, com piso em Y=76 e entrada em `(0,77,0)`. Não contém portal, prédios, praça, placas ou decorações de spawn. O relevo se integra ao entorno por uma faixa de transição gradual. Essa é a área disponível para as construções do operador.

As cavernas mantêm passagens naturais, iluminação e biomas reais; não recebem as faixas artificiais de musgo/dripstone que marcavam os antigos trajetos. Só os acessos externos têm adaptação de desnível para manter entrada caminhável; o piso usa o mesmo material do habitat ao redor. As entradas recebem tratamento sobre a rocha existente, sem pórticos ou paredes artificiais.

Fundos de lagos e rios recebem pedra, cascalho, argila e areia por profundidade e habitat; a grama submersa é substituída em toda a área tratada. As bordas de solo são misturadas em faixas irregulares e não alteram os IDs reais dos biomas. A água pode mudar de cor entre biomas porque essa coloração é nativa do Minecraft, mesmo com os materiais do leito misturados.

Mantém as pontes detalhadas, vegetação e as 12 câmaras; acrescenta agrupamentos de samambaias e formações minerais fora dos corredores livres. Os arquivos e a navegação são testados, mas o aspecto desta revisão ainda não foi inspecionado em um cliente Minecraft neste ambiente.

## Conteúdo

- `world/safari/`: mundo Anvil, `level.dat`, 8.836 chunks e todos os 26 biomas nativos. Spawn `(0,77,0)`.
- `schematics/`: 36 regiões contínuas de 250 × 320 × 250 blocos, mais a clareira de 120 × 48 × 120. Os limites verticais dos terrenos exportados são Y=-64 a 255; nenhum bloco construído ultrapassa esse volume.
- `schematics/manifest.json`: posição exata do canto mínimo de cada parte e dimensões.
- `biomes/biome_coordinates.json`: pontos de visita e áreas aproximadas dos biomas superficiais; consulte também as entradas de caverna em `routes.json`.
- `biomes/biome_restore/`: matriz real dos biomas por células 4³ e restaurador offline com backup.
- `maps/safari_layout.png`: mapa de relevo e biomas, norte no topo. Não é captura de tela dentro do Minecraft.
- `validation/`: relatórios dos arquivos e da navegação.
- `generator/`: código completo, dependências fixadas e testes; não exige a mod Shirokai Trainers.

O retângulo autoral é X/Z=-750..749. Chunks inteiros incluem margem adicional até -752..751. Fora disso, o gerador do mundo standalone produz oceano plano. É preferível conservar esse gerador ao importar o mundo completo, evitando emendas com outro terreno. O hub construído foi removido por solicitação do operador. O centro contém somente terreno disponível para construir. Nenhum NPC ou teleporte é configurado automaticamente.

## Atualizar a Safari já instalada no seu Multiworld

O JAR fornecido pelo operador foi identificado como **Multiworld de Isaiah, bundle 1.14.2**, incluindo a implementação para 1.21.1. A V1 já foi carregada no servidor do operador; para atualizar os chunks:

1. Saia da dimensão Safari e pare completamente o servidor.
2. Faça uma cópia de segurança de `world/dimensions/multiworld/safari/`. Se `level-name` do `server.properties` tiver outro valor, use esse nome no lugar de `world`.
3. Renomeie a pasta `region` existente para `region-v1-backup`, sem apagá-la.
4. Copie **somente** a pasta `world/safari/region` deste pacote V5 para `world/dimensions/multiworld/safari/region`. Não misture arquivos region de versões diferentes e não substitua o `level.dat` do mundo principal.
5. Inicie o servidor e, dentro do jogo como administrador, use `/mw tp safari`, `/tp @s 0 77 0` e, se necessário, `/mw setspawn`.

Isso substitui o terreno e construções existentes na dimensão Safari. NPCs/entidades colocados pelo operador não integram este mapa e podem continuar salvos nas pastas `entities` e em índices de outras mods; verifique suas posições. Não copie nem apague dados de jogadores ou de outras dimensões. Se a dimensão ainda não estiver registrada, crie-a primeiro com `/mw create safari normal`, depois pare o servidor e siga a troca da pasta region.

## Instalar o mundo e usar Multiworld

1. Use Minecraft Java **1.21.1**, Fabric e Cobblemon **1.8.3**, com suas dependências habituais. Não abra em versão anterior.
2. Pare o servidor e faça backup do mundo/dimensões existentes.
3. Extraia o pacote. A pasta que representa o mundo é **`world/safari`**, aquela que contém `level.dat` e `region/`.
4. Há implementações diferentes de Multiworld no Fabric. A instalação do operador usa Isaiah Multiworld 1.14.2; o procedimento acima foi conferido no bytecode do JAR fornecido. Para outra implementação, não presuma o mesmo comando ou diretório. Use o comando de ajuda/documentação do seu Multiworld para **importar um mundo existente** com nome `safari` e tipo Overworld. Aponte para a pasta `safari`, no diretório de mundos exigido por esse mod. Não use um comando de criação que substitua os arquivos existentes.
5. Se o seu Multiworld só suporta dimensões dentro de um único save: crie primeiro uma dimensão Overworld vazia `safari`; pare o servidor; copie o conteúdo de `world/safari/region/` para a subpasta `region/` da dimensão que ele criou. Não substitua o `level.dat` do mundo principal. Nesse modo o gerador externo e as regras são os da dimensão criada, não os de `level.dat` entregue. Configure a área de exploração dentro do retângulo autoral.
6. Inicie o servidor, entre no mundo/dimensão `safari` pelo comando documentado no mod e teleporte para `(0,77,0)` nesse mundo. Configure a recepção/retorno com seu sistema de NPCs/menus, se desejar.
7. Confirme os IDs no debug F3 e faça o roteiro de aceitação abaixo. A importação Multiworld não foi executada neste ambiente.

Não instale Multiverse de Bukkit em Fabric. Não copie a pasta do mapa sobre o mundo principal. Para ensaio independente, é possível usar `safari` como mundo principal (`level-name=safari`) em um servidor de testes isolado, após aceitar pessoalmente a EULA do Minecraft; o pacote não aceita termos nem inclui servidor proprietário.

## Importar com WorldEdit

Use uma build Fabric do WorldEdit compatível com Minecraft 1.21.1 que **leia Sponge Schematic v3 e cole biomas 3D**. Os `.schem` contêm `Biomes/Palette` e `Biomes/Data` por bloco, além de blocos e textos das placas. A estrutura foi conferida com a especificação Sponge v3; uma colagem real pelo WorldEdit ainda precisa ser feita.

1. Pare para backup, depois use um mundo de teste vazio. Coloque os `.schem` na pasta de schematics da sua instalação do WorldEdit (normalmente `config/worldedit/schematics/`).
2. Para cada arquivo, leia `paste_at` no `schematics/manifest.json`. Teleporte-se exatamente para essas coordenadas **na dimensão de destino**.
3. Carregue a parte por autodetecção e cole **incluindo biomas**:

   ```text
   //schem load safari_00_00
   //paste -b
   ```

   Exemplo: `safari_00_00` usa canto mínimo `(-750,-64,-750)`. `safari_00_01` usa `(-500,-64,-750)`. Todos usam Offset `[0,0,0]`, portanto o ponto de colagem é esse canto, sem depender de uma origem oculta.
4. Repita por arquivo. O schematic da clareira é opcional; já está incorporado nas 36 partes e no mundo completo. Seu canto é `(-60,64,-60)`.
5. Cada parte completa tem **20 milhões de blocos**. Faça uma de cada vez, sem jogadores no mundo; se o limite de operações impedir, prefira importar o mundo pronto. Não aumente limites de memória às cegas. Não use `-a` para reconstrução completa: o ar é necessário para abrir as cavernas e limpar espaço das construções.
6. A opção de biomas deve ser efetivamente suportada pela versão instalada. Se `-b` não existir ou os biomas não forem preservados, não presuma sucesso: importe o mundo entregue ou use o restaurador offline.

## Restaurar biomas reais

O mundo completo já contém os biomas. Este procedimento é para uma cópia com biomas perdidos, por exemplo após uma ferramenta que só cole blocos.

Requer Python 3.11+ e dependências do gerador. **Pare o servidor primeiro.** O script cria um backup dos arquivos region antes de substituí-los. Mantém blocos e dados dos chunks; restaura apenas o campo de biomas no volume original, em chunks existentes. Não reconstrói terreno e não cria chunks ausentes. Por isso, a colagem precisa estar nas coordenadas originais.

```sh
python -m venv .venv
.venv/bin/python -m pip install -r generator/requirements.txt
.venv/bin/python generator/restore_biomes.py \
  --world /caminho/do/servidor/safari \
  --data biomes/biome_restore/biomes_4x4x4.npz \
  --server-stopped
```

No Windows, use `.venv\Scripts\python.exe`. Se a região for uma dimensão que não possui `level.dat`, acrescente `--level-dat /caminho/do/save-principal/level.dat`. Só é aceito DataVersion 3955 (1.21.1). O restaurador suporta chunks zlib, como os entregues; ele recusa outros métodos em vez de sobrescrever dados que não entende. A matriz usa as coordenadas originais; mover ou rotacionar schematics exige transformar a matriz também.

## Prévia técnica opcional

`maps/preview_cerejeiras.png`, quando presente, é uma projeção dos blocos reais do arquivo gerado. Não é screenshot de um cliente Minecraft. O script opcional `generator/voxel_preview.py` requer o JAR oficial do **cliente** 1.21.1 para ler as texturas; esse JAR não é redistribuído. Renderizadores e shaders do servidor/cliente podem apresentar cores e transparências diferentes.

## Reproduzir a geração

O gerador é executável, não pseudocódigo. Usa apenas blocos vanilla, não cria entidades decorativas nem altera arquivos de spawn do Cobblemon. Reserve 4 GB de RAM livre, 2 GB de disco livre para intermediários e dependências, além de Python 3.11+. No ambiente desta entrega a geração demorou aproximadamente dois minutos; o tempo varia por máquina.

```sh
cd generator
bash run.sh ../Safari-regenerada
```

Para execução manual, instale `requirements.txt`, rode os testes, `generate.py --output DESTINO`, `validate.py DESTINO` , `check_routes.py DESTINO` e `check_natural.py DESTINO`. Para validar IDs/estados contra registros oficiais de sua própria cópia do Minecraft, `validate.py` aceita `--official-biomes JSON` (lista de nomes) e `--official-blocks JSON` (relatório `blocks.json` do datagen). Os relatórios desta entrega foram gerados com os dados vanilla oficiais do 1.21.1. O JAR proprietário usado para a verificação não é redistribuído.

## Validação e limites reais

Consulte `validation/validation.json`, `validation/routes.json`, `validation/build.json` e `validation/RELATORIO.md`.

Verificado: 26 IDs reais em todos os chunks; paletas compatíveis com vanilla 1.21.1; leitura dos arquivos Anvil; comparação dos dados de bioma de todas as seções com a matriz fonte; amostras de blocos de todas as seções; comparação integral dos blocos e biomas de todos os 37 schematics com a fonte; testes de variação das árvores, ausência da grade anterior e água/gelo nos 27 lagos; conectividade das rotas por busca tridimensional com dois blocos livres de altura e degrau máximo de um bloco, incluindo os pontos de visita das 12 câmaras. Essa busca cobre os corredores das rotas e escadas, não navegação livre em toda a área, natação nem voo. Não equivale a teste com cliente.

**Ainda não executado:** abrir o mundo num servidor Minecraft/Cobblemon, importar pelo Multiworld, colar pelo WorldEdit e medir performance/spawns com os datapacks reais. Portanto esta entrega é para homologação, não uma promessa de funcionamento já observado em jogo. Não foram aceitos termos da EULA em nome do operador. Iluminação está marcada para recálculo pelo Minecraft ao carregar os chunks; verifique-a durante a homologação.

### Roteiro do operador

- Carregar o mundo em servidor de testes e verificar o log, sem erros de chunk/registro.
- Ir à clareira e a cada ponto de `biome_coordinates.json`; conferir F3 e as condições reais dos biomas de caverna.
- Percorrer as rotas, pontes, montanhas, acessos subterrâneos e ilha; verificar luz e estabilidade do terreno após atualizações de água/folhagens.
- Colar uma parte em dimensão descartável com `-b` e comparar blocos, placas e biomas; testar restauração offline nessa cópia.
- Confirmar que os datapacks do servidor permitem spawns na dimensão `safari`. Bioma sozinho não garante espécie alguma. O mapa oferece superfícies naturais variadas, lagos e águas rasas/profundas, trechos escuros e cavernas, mas não altera regras de spawn.
- Fazer ensaio com jogadores simultâneos, monitorando TPS, memória e tempo de carregamento. Ajustar distâncias de simulação/renderização conforme o servidor. Não há benchmark de multiplayer nesta entrega.

Conserve uma cópia intacta do ZIP para recuperação. Não instale arquivos do gerador como mod e não substitua o JAR de treinadores por este mapa.
