# Third-party licenses and attribution

[Project license](LICENSE) · [Project notice](NOTICE)

PGS contributions and the inherited MIT-licensed source are covered by the project license, with both copyright notices retained. This index is not a substitute for the actual component license texts and does not grant rights to proprietary game content.

## Included materials

See the [detailed component licenses and pinned provenance](THIRD_PARTY.md) for additional terms, including the website map attribution, PvPoke and build-time DEX tools.

| Component | Recorded terms or exclusion | License / provenance |
|---|---|---|
| Original upstream source | MIT; original copyright retained | [LICENSE](LICENSE), [NOTICE](NOTICE) |
| Frida Java bridge / diagnostic derivative | LGPL-2.0 WITH WxWindows-exception-3.1 as declared at the pinned upstream commit; bundled distribution notice retained | [NOTICE](pgs/vendor/NOTICE.txt), [COPYING.LIB](pgs/vendor/COPYING.LIB), [COPYING.frida-tools](pgs/vendor/COPYING.frida-tools), [provenance](pgs/vendor/bridge-provenance.json) |
| Time zone lookup | See included original license | [LICENSE](pgs/vendor/tz-lookup/LICENSE) |
| React and React DOM | MIT, original notice | [React license](website/public/licenses/react.md), [locked website dependencies](website/package-lock.json) |
| Feed icons | Artwork excluded from project MIT license | [NOTICE](pgs/assets/feed-icons/NOTICE.txt), [provenance](pgs/assets/feed-icons/provenance.json) |
| Map icons and game names | Artwork/text excluded from project MIT license; separately identified supplied icon | [NOTICE](pgs/assets/map-icons/NOTICE.txt), [provenance](pgs/assets/map-icons/provenance.json) |

## Build-time dependencies

The native build prepares pinned third-party sources. Their exact upstream license texts, rather than a new project license, govern those components. The native and ART packaging code retains Dobby LICENSE, LSPlant LICENSE, DexBuilder LICENSE, parallel-hashmap LICENSE and XZ-Embedded COPYING in the native/art notices. See [dependency preparation](tools/prepare_native.py), [native build](pgs/native_build.py) and [ART build](pgs/art_build.py). Diagnostic runtime and website development dependencies retain their own terms; consult the locked versions and the respective upstream notices. This index identifies the known included materials and native license-copy contract; it is not a complete legal inventory of every transitive build dependency.

## Proprietary content

The project license does not cover Pokemon GO software, game data, images, trademarks or other third-party property. It grants no right to distribute a game APK. PGS is independent and is not affiliated with the game publisher.

## Português (Brasil)

A licença MIT do projeto cobre o código e as contribuições correspondentes, preservando os avisos originais. As dependências mantêm suas próprias licenças, vinculadas acima. Imagens, dados e software proprietário de Pokémon GO não passam a ser licenciados pelo PGS. Consulte os avisos originais e os registros de procedência; este índice não substitui os respectivos textos legais nem comprova autorização de distribuição.
