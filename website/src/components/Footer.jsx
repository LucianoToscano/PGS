import { links } from '../content.js';
import { asset } from '../assets.js';
import { homeHref, indexHref } from './guideData.js';

export default function Footer({ onGuide = false }) {
  return (
    <footer className="site-footer">
      <div className="site-footer__inner">
        <div className="site-footer__top">
          <a className="brand" href={onGuide ? homeHref : '#top'}>
            <img className="brand__mark" src={asset('pgs-shield.png')} alt="" width="26" height="26" />
            <span className="brand__name">PGS</span>
          </a>
          <nav className="site-footer__links" aria-label="Footer">
            <a href={indexHref}>Feature guides</a>
            <a href={links.github}>GitHub</a>
            <a href={links.releasesLatest}>Releases</a>
            <a href={links.discord}>Discord</a>
            <a href={`${links.github}/blob/main/THIRD_PARTY.md`}>Credits</a>
          </nav>
        </div>
        <p className="site-footer__legal">
          PGS — Pokémon GO Spoofers. Consulte a licença e os avisos de terceiros no repositório.
          O projeto não é afiliado à editora do jogo.
        </p>
        <p className="site-footer__legal">Map screenshot © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>.</p>
      </div>
    </footer>
  );
}
