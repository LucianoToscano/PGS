import { steps, faqs, links } from '../content.js';
import { ArrowIcon } from './Icons.jsx';

export default function GetStarted() {
  return (
    <section className="section" id="get-started" aria-labelledby="get-started-heading">
      <div className="section__head">
        <p className="section__num">03 / Get started</p>
        <h2 id="get-started-heading" className="section__title">
          Upstream installation reference
        </h2>
        <p className="section__lead">
          These steps describe the upstream PGRazor release. PGS is still in development and has no validated APK.
        </p>
      </div>

      <ol className="steps">
        {steps.map((step) => (
          <li className="step" key={step.n}>
            <span className="step__num" aria-hidden="true">{step.n}</span>
            <h3 className="step__title">{step.title}</h3>
            <p className="step__body">{step.body}</p>
          </li>
        ))}
      </ol>

      <div className="cta">
        <a className="btn btn--primary" href={links.releasesLatest}>
          View PGS release status
          <ArrowIcon />
        </a>
        <a className="btn btn--ghost" href={links.discord}>
          Upstream Discord
        </a>
      </div>

      <p className="cta__release">
        <span className="cta__badge">Upstream reference</span>
        The upstream{' '}
        <a href={links.releasesCurrent}>v0.3.0 release</a> adds Auto Throw with catch on map,
        Auto-Raid and the experimental PGRazor Root installer.
      </p>

      <div className="faq">
        <h3 className="faq__heading">Good to know</h3>
        {faqs.map((item) => (
          <details className="faq__item" key={item.q}>
            <summary>
              <span>{item.q}</span>
              <span className="faq__mark" aria-hidden="true" />
            </summary>
            <p>{item.a}</p>
          </details>
        ))}
      </div>
    </section>
  );
}
