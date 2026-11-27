# Configurações do repositório PGS — verificações administrativas

Este documento acompanha a limpeza da identidade pública do PGS. O código e os APKs são gerenciados pelo GitHub Actions; as configurações administrativas exigem acesso do proprietário do repositório.

## Descrição pública (About)

No momento da auditoria, a descrição pública do repositório ainda continha uma referência ao nome de outro projeto. Ela é um **campo da configuração do GitHub**, não um trecho do README. Por isso, atualizar arquivos de código não modifica esse texto automaticamente.

1. Abra https://github.com/LucianoToscano/PGS
2. No painel **About**, clique no ícone **engrenagem** ou **Editar** (no navegador, use a opção "Site para computador" se necessário).
3. Substitua a descrição por:

> PGS — Pokémon GO Spoofers. Projeto independente para Android, com controles de localização, joystick, mapas e ferramentas auxiliares para Pokémon GO.

4. Se desejar, preencha **Website** com `https://lucianotoscano.github.io/PGS/`, mas só depois de ativar o Pages.
5. Salve a alteração. Isso não reescreve commits, código, histórico nem o certificado do APK.

## Por que a main mostra um X vermelho?

Na build `45984656628`, a compilação do site passou, mas o job `deploy` retornou **HTTP 404** ao criar uma implantação do GitHub Pages. Isso indica que o Pages ainda não estava habilitado/configurado corretamente. O X vermelho sinaliza a falha dessa verificação, **não** uma perda de código da branch `main` e **não** uma falha de assinatura do APK.

Para resolver:

1. Abra https://github.com/LucianoToscano/PGS/settings/pages
2. Em **Build and deployment → Source**, escolha **GitHub Actions**.
3. Salve a configuração, caso a interface ofereça botão de salvar.
4. Reexecute o workflow **Website** a partir de https://github.com/LucianoToscano/PGS/actions
5. Aguarde a conclusão de `build` e `deploy`, ambos com resultado **success**. Até então, não afirme que o site está publicado.

A instalação GitHub conectada para edição de código não possui permissão administrativa para habilitar o Pages ou alterar o campo About. Essa etapa é feita diretamente pelo proprietário do repositório.

## Capturas de tela

A captura antiga `website/public/images/main-menu.png` foi retirada do site porque mostrava o cabeçalho e a numeração de uma versão anterior. A interface atual usa a identidade **PGS**, mas uma imagem só deve ser publicada como captura de uma build quando houver evidências da versão, sem dados pessoais, tokens, e-mails ou coordenadas privadas.

As imagens de pesquisa e documentação que forem mantidas em arquivos históricos não são evidência de funcionamento no celular do proprietário.

## Continuidade técnica

O Android continua instalando o PGS como **Pokémon GO**, com package `com.nianticlabs.pokemongo`, `versionCode` crescente e chave de assinatura definitiva. Não remover, renomear ou recriar esses identificadores em um processo de limpeza visual.

Interfaces JNI, nomes de bibliotecas, chaves de backup, pastas de código e histórico Git preservam compatibilidade técnica ou procedência e não devem ser apagados indiscriminadamente. Alterações neles exigem planejamento de migração e testes físicos, em PR separada.

O release `v0.0.2` permanece em rascunho até confirmação de instalação, abertura, login e atualização por cima sem perda de dados.
