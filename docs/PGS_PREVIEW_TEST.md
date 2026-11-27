# PGS — prévia Android

A prévia standalone `pgs-preview.apk` (ID `dev.pgs.preview`) é uma interface de desenvolvimento, não o Pokémon GO. A compilação da prévia foi confirmada no CI 45929853563. O instalador e a execução do jogo não fazem parte desta entrega.

O CI verifica assinatura, ID de pacote e SHA-256 da prévia. O artefato de teste só será enviado por execução manual na main e com a variável de repositório `PGS_PREVIEW_ARTIFACT_ENABLED=true`. A retenção é de três dias. Não usa as chaves de release; utiliza assinatura de desenvolvimento temporária. Não publique o arquivo como versão jogável, nem substitua um aplicativo instalado com certificado diferente.

Após a integração e validação, o responsável pode habilitar a variável e executar **Source checks** manualmente em Actions. Se o CI passar, o artefato `PGS-preview-test` incluirá a prévia, o SHA-256 e o commit. Desative a variável após o teste. Teste físico continua necessário.
