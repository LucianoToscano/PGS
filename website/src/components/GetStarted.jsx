import { steps, faqs, links } from '../content.js';
import { ArrowIcon } from './Icons.jsx';
import { ui } from '../uiText.js';

export default function GetStarted() {
  return (
    <section className="section" id="get-started" aria-labelledby="get-started-heading">
      <div className="section__head">
        <p className="section__num">{ui.getStarted.number}</p>
        <h2 id="get-started-heading" className="section__title">
          {ui.getStarted.title}
        </h2>
        <p className="section__lead">
          {ui.getStarted.lead}
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
          {ui.getStarted.download}
          <ArrowIcon />
        </a>
        <a className="btn btn--ghost" href={links.discord}>
          {ui.getStarted.discord}
        </a>
      </div>

      <p className="cta__release">
        <span className="cta__badge">{ui.getStarted.badge}</span>
        <a href={links.releasesCurrent}>{ui.getStarted.build}</a> {ui.getStarted.afterBuild}
      </p>

      <div className="faq">
        <h3 className="faq__heading">{ui.getStarted.faqTitle}</h3>
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
