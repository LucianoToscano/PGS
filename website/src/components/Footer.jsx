import { links } from '../content.js';
import { asset } from '../assets.js';
import { homeHref, indexHref } from './guideData.js';
import { ui } from '../uiText.js';

export default function Footer({ onGuide = false }) {
  return (
    <footer className="site-footer">
      <div className="site-footer__inner">
        <div className="site-footer__top">
          <a className="brand" href={onGuide ? homeHref : '#top'}>
            <img className="brand__mark" src={asset('pgs-shield.png')} alt="" width="26" height="26" />
            <span className="brand__name">PGS</span>
          </a>
          <nav className="site-footer__links" aria-label={ui.footer.nav}>
            <a href={indexHref}>{ui.footer.guides}</a>
            <a href={links.github}>GitHub</a>
            <a href={links.releasesLatest}>{ui.footer.releases}</a>
            <a href={links.discord}>Discord</a>
            <a href={`${links.github}/blob/main/THIRD_PARTY.md`}>{ui.footer.credits}</a>
          </nav>
        </div>
        <p className="site-footer__legal">
          {ui.footer.legal}
        </p>
        <p className="site-footer__legal">{ui.footer.map} <a href="https://www.openstreetmap.org/copyright">{ui.footer.contributors}</a>.</p>
      </div>
    </footer>
  );
}
