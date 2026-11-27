# PGS AUTO DEV — etapa inicial

O workflow `PGS AUTO DEV — Review` é acionado por pull requests destinadas à main. Com permissões somente de leitura, classifica caminhos alterados por categoria e registra contagens e áreas que requerem revisão especializada no resumo do GitHub Actions. Renomeações contam os caminhos antigos e novos. A ferramenta não envia conteúdo para provedores externos, não usa modelos de IA e não modifica, integra ou publica código.

As categorias são indicativas e não provam segurança, funcionalidade ou compatibilidade. A revisão humana e os testes existentes continuam necessários. Mudanças em licença, automação, código nativo, Android, build/runtime e arquivos não classificados são sinalizadas. Não se deve considerar ausência de alertas uma autorização de merge.

Nenhuma API externa paga ou credencial adicional é necessária. A execução está sujeita às cotas do GitHub Actions. Futuras integrações com IA devem ser avaliadas separadamente e começar sem acesso a segredos e sem permissão de escrita automática.
