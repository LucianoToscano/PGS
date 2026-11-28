import { featureGuides, guideHref, homeHref, indexHref } from './guideData.js';
import { ui } from '../uiText.js';
import Gallery from './Gallery.jsx';
import { guideScreenshots } from '../guideScreenshots.i18n.js';

// One feature's how-to page. An unknown id (renamed, removed, or mistyped in a
// shared link) renders a useful not-found view with a route back to the index
// rather than a blank page.
export default function GuideDetail({ id }) {
  const guide = featureGuides.find((item) => item.id === id);

  if (!guide) {
    return (
      <section className="section guide-detail" aria-labelledby="guide-notfound-heading">
        <div className="section__head">
          <p className="section__num">{ui.guide.number}</p>
          <h1 id="guide-notfound-heading" className="section__title">
            {ui.guide.missingTitle}
          </h1>
          <p className="section__lead">
            {ui.guide.missing(id)}
          </p>
        </div>
        <p className="guide-back">
          <a className="btn btn--primary" href={indexHref}>
            {ui.guide.browse}
          </a>
          <a className="btn btn--ghost" href={homeHref}>
            {ui.guide.back}
          </a>
        </p>
      </section>
    );
  }

  const steps = Array.isArray(guide.steps) ? guide.steps : [];
  const notes = Array.isArray(guide.notes) ? guide.notes : [];
  const related = featureGuides.filter(
    (item) => item.category === guide.category && item.id !== guide.id,
  );

  return (
    <article className="section guide-detail" aria-labelledby="guide-detail-heading">
      <nav className="guide-detail__crumbs" aria-label={ui.guide.breadcrumb}>
        <a href={homeHref}>{ui.guide.home}</a>
        <span aria-hidden="true">/</span>
        <a href={indexHref}>{ui.guide.title}</a>
        <span aria-hidden="true">/</span>
        <span aria-current="page">{guide.title}</span>
      </nav>

      <div className="section__head">
        {guide.category && <p className="section__num">{guide.category}</p>}
        <h1 id="guide-detail-heading" className="section__title">
          {guide.title}
        </h1>
        {guide.summary && <p className="section__lead">{guide.summary}</p>}
      </div>


      {guide.where && (
        <section className="guide-detail__block" aria-labelledby="guide-where-heading">
          <h2 id="guide-where-heading">{ui.guide.where}</h2>
          <p>{guide.where}</p>
        </section>
      )}

      {steps.length > 0 && (
        <section className="guide-detail__block" aria-labelledby="guide-steps-heading">
          <h2 id="guide-steps-heading">{ui.guide.steps}</h2>
          <ol className="guide-steps">
            {steps.map((step, index) => (
              <li key={index}>{step}</li>
            ))}
          </ol>
        </section>
      )}

      {guideScreenshots[id]?.length > 0 && (
        <section className="guide-detail__block guide-screenshots" aria-labelledby="guide-screenshots-heading">
          <h2 id="guide-screenshots-heading">{ui.guide.screenshots}</h2>
          <p>{ui.guide.screenshotNote}</p>
          <Gallery shots={guideScreenshots[id]} />
        </section>
      )}

      {notes.length > 0 && (
        <section className="guide-detail__block" aria-labelledby="guide-notes-heading">
          <h2 id="guide-notes-heading">{ui.guide.notes}</h2>
          <ul className="guide-notes">
            {notes.map((note, index) => (
              <li key={index}>{note}</li>
            ))}
          </ul>
        </section>
      )}

      <nav className="guide-detail__related" aria-label={ui.guide.moreNav}>
        <h2>{ui.guide.more}</h2>
        {related.length > 0 && (
          <ul className="guide-related">
            {related.map((item) => (
              <li key={item.id}>
                <a href={guideHref(item.id)}>{item.title}</a>
              </li>
            ))}
          </ul>
        )}
        <p className="guide-back">
          <a className="btn btn--ghost" href={indexHref}>
            {ui.guide.all}
          </a>
          <a className="btn btn--ghost" href={homeHref}>
            {ui.guide.back}
          </a>
        </p>
      </nav>
    </article>
  );
}
