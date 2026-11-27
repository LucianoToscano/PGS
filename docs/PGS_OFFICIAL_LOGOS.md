# Logos oficiais — PGS · Pokémon GO Spoofers

Estas são as **três imagens originais** fornecidas pelo projeto, copiadas **sem redesenho, sem vetorização, sem compressão com perdas e sem alteração de pixels**. Cada cópia é verificada por SHA-256 no CI por `tools/pgs_branding_audit.py`.

| Uso | Arquivo no repositório | Resolução | SHA-256 original |
|---|---|---|---|
| Escudo / favicon / navegação | `website/public/pgs-shield.png` | 4096 × 4096 | `30f51e26c20ea0aba1687e4c1e22adce093b238c3879492342163f818b438300` |
| Logo completa do README | `website/public/pgs-full.png` | 4096 × 4096 | `15716009d2d1c0e11d75ace39783c3237c1d9db2272ca7f2fad8ac2d6e20ab2e` |
| Texto/wordmark horizontal do site | `website/public/pgs-wordmark.png` | 4096 × 1704 | `8ad6e5d80075145154ebfc343d91469da970fa7cfa729b9f6e31479307d4b29e` |

## Arquivos originais do Google Drive

- Escudo **Logo PGS.png**: https://drive.google.com/file/d/1Lh7Y9tN2C1sdqm-ZvPGDP52nlyfjNtna/view?usp=drivesdk
- Logo completa **Logo PGS - Pokémon GO Spoofers.png**: https://drive.google.com/file/d/1yoQQgK1dhgYGE2d1IOLCqeL08EG84OV6/view?usp=drivesdk
- Texto **Logo PGS - Pokémon GO Spoofers Texto.png**: https://drive.google.com/file/d/1SU2eAty59TMR8DZyNdNHnU_ccHPUUhZT/view?usp=drivesdk

## Como usar

- As imagens da pasta `website/public/` são usadas diretamente pelo GitHub Pages e pelo README.
- As três cópias byte a byte iguais em `pgs/branding/` servem como arquivos de marca do PGS dentro da árvore principal. O Git deduplica blobs idênticos.
- Como os arquivos são brancos com **transparência**, o site usa um fundo escuro para exibi-los em ambos os temas.
- A primeira migração preservou a logo dentro do jogo e o joystick. A rodada de identidade de 27/11/2026 substitui o launcher pela cópia oficial do escudo, empacotada sem alterar os pixels; o joystick continua intacto. O launcher mantém o indicador de estado e usa sombra discreta, sem fundo sólido.
- A numeração do PGS, o package Android e o certificado de assinatura não dependem destas imagens.

Substituições futuras só devem ser feitas após comparar os bytes com uma versão autorizada pelo responsável do projeto e atualizar os testes de integridade.
