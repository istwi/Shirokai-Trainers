# Pokécentros Safari — coleção de 26 biomas

26 construções independentes para Minecraft Java 1.21.1, seguindo a referência aprovada: dois andares, base de pedra, estrutura de troncos, janelas altas, telhado assimétrico, varanda frontal, escada externa na direita e emblema de Pokébola. Cada versão varia madeiras, alvenaria, telhado, plantas e detalhes do habitat. Inclui balcão de recepção, espaços de cura e sala superior mobiliada. Não é um hub e não substitui o mapa V6.

## Conteúdo

Cada pasta de bioma contém o schematic Sponge v3, prévia técnica, relatório de acesso, paleta e matriz dos blocos. O catálogo mostra seis exemplos reais da coleção. Todos os 26 schematics estão prontos para colocar separadamente pelo mapa; nenhum foi instalado automaticamente na dimensão.

Os espaços de cura e as camas são mobiliário visual de blocos vanilla. Máquinas funcionais do Cobblemon, NPCs, diálogos, comércio e teleporte precisam ser configurados com os mods/sistemas do seu servidor. Não existem NPCs ou serviços funcionais embutidos. As marcações de recepcionista/pesquisador no manifest indicam posições livres para configuração.

## Colocar com WorldEdit Fabric

1. Faça backup da dimensão. Use WorldEdit Fabric compatível com 1.21.1 e Sponge v3.
2. Copie o arquivo pokecentro_BIOMA.schem escolhido para a pasta de schematics do WorldEdit.
3. Escolha uma área do bioma com terreno adequado. Cada construção usa volume de 33 blocos no eixo X, 30 no Z e 30 de altura. A fachada aponta para sul (+Z) e a escada fica a leste (+X).
4. Posicione o ponto de colagem no canto noroeste do volume, na altura desejada do piso térreo. O schematic possui Offset [0,-4,0]: a fundação começa quatro blocos abaixo desse ponto. Por exemplo, ponto de colagem Y=76 produz piso em Y=76, fundação em Y=72 e volume até Y=101.
5. Para a floresta, use:

```
//schem load pokecentro_forest
//paste
```

Cole sem -b para conservar os biomas existentes. O ar faz parte do arquivo e limpa os interiores; -a pode deixar árvores e terreno dentro da casa. A colagem substitui blocos em todo o volume indicado, então escolha o local antes. Faça uma construção por vez.

A porta térrea fica no deslocamento (18,+1,23), com área de chegada em (18,+1,25). Some esses valores ao ponto de colagem. As demais posições de NPCs e acesso estão em manifest.json. As portas são utilizáveis e permanecem fechadas no schematic.

Use as versões oceânicas em margem, ilha ou plataforma adequada; não são bases submersas. Nos modelos de palafitas, prolongue os pilares até o leito se ele estiver mais de quatro blocos abaixo do piso. Em encostas e cavernas, ajuste os apoios ao terreno e reserve altura livre de 26 blocos acima do piso; evite soterrar entradas ou suspender fundações. A seleção do local e a integração final com o terreno não foram automatizadas.

## Verificação

Os 26 arquivos foram relidos e seus 772.200 blocos comparados integralmente à fonte. Os estados foram conferidos contra o registro oficial vanilla 1.21.1. A navegação em voxels verificou chegada, recepção, duas áreas de cura, varanda, sala superior, espaço do pesquisador e início/fim da escada. Portas são tratadas como abríveis e a busca admite degrau de um bloco; não é simulação da física exata de escadas, cercas ou jogadores. As lanternas têm blocos de apoio.

As prévias são projeções técnicas dos blocos realmente gerados, com texturas e formas simplificadas. Não representam screenshots do jogo ou garantem o aspecto exato com shaders. Ainda não houve carregamento destes schematics no cliente Minecraft nem colagem real pelo WorldEdit.

## Reproduzir

Instale requirements.txt e rode:

```
python build_centers.py pasta-destino /caminho/para/blocks.json
```

O segundo argumento é opcional e habilita conferência de estados com seu registro oficial de blocos 1.21.1. O gerador executa os testes e salva os resultados por bioma. render_centers.py usa a pasta de uma variante e o JAR oficial de cliente 1.21.1 para ler texturas; esse JAR não é redistribuído. Para gerar uma prévia, crie a subpasta maps na variante e execute `python render_centers.py pasta-da-variante cliente-1.21.1.jar`.

## Versões incluídas

- plains
- forest
- flower_forest
- dark_forest
- bamboo_jungle
- jungle
- taiga
- cherry_grove
- snowy_taiga
- meadow
- savanna
- snowy_plains
- ice_spikes
- stony_peaks
- jagged_peaks
- desert
- badlands
- swamp
- mangrove_swamp
- deep_ocean
- warm_ocean
- river
- beach
- mushroom_fields
- dripstone_caves
- lush_caves
