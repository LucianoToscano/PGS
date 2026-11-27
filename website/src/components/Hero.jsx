import { links, heroFacts } from '../content.js';
import { asset } from '../assets.js';
import { ArrowIcon } from './Icons.jsx';
import RouteMotif from './RouteMotif.jsx';
import { ui } from '../uiText.js';

export default function Hero() {
  return (
    <section className="hero" id="top">
      <RouteMotif className="hero__motif" />
      <div className="hero__inner">
        <div className="hero__copy">
          <p className="eyebrow">
            <span className="eyebrow__dot" aria-hidden="true" />
            {ui.hero.eyebrow}
          </p>
          <img
            className="hero__wordmark"
            src={asset('pgs-wordmark.png')}
            alt="PGS — Pokémon GO Spoofers"
            width="4096"
            height="1704"
            loading="eager"
            decoding="async"
          />
          <h1 className="hero__title">
            {ui.hero.title1}{' '}
            <span className="accent-text">{ui.hero.title2}</span>
          </h1>
          <p className="hero__lead">
            {ui.hero.lead}
          </p>
          <div className="hero__actions">
            <a className="btn btn--primary" href={links.releasesLatest}>
              {ui.hero.download}
              <ArrowIcon />
            </a>
            <a className="btn btn--ghost" href={links.github}>
              {ui.hero.source}
            </a>
          </div>
          <dl className="hero__facts">
            {heroFacts.map((fact) => (
              <div className="hero__fact" key={fact.term}>
                <dt>{fact.term}</dt>
                <dd>{fact.detail}</dd>
              </div>
            ))}
          </dl>
        </div>

        <figure className="hero__shot">
          <img
            src={asset('images/encounter.png')}
            alt={ui.hero.shotAlt}
            width="1080"
            height="2404"
            loading="eager"
            fetchPriority="high"
            decoding="async"
          />
          <figcaption className="shot-tag">
            <span className="shot-tag__num" aria-hidden="true">01</span>
            {ui.hero.shotCaption}
          </figcaption>
        </figure>
      </div>
    </section>
  );
}
